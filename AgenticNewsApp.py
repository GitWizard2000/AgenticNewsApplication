import os
import sqlite3, re
import asyncio
import streamlit as st
from dotenv import load_dotenv
from tavily import TavilyClient

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

# ==============================
# CONFIG
# ==============================
load_dotenv()

GEMINI_API_KEY1 = os.getenv("GEMINI_API_KEY1")
GEMINI_API_KEY2 = os.getenv("GEMINI_API_KEY2")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

MODEL_NAME = "gemini-2.5-flash"
MAX_WORDS = 100
MAX_TURNS = 9

# ==============================
# DATABASE SETUP
# ==============================
conn = sqlite3.connect("memory.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    agent TEXT,
    response TEXT,
    confidence REAL
)
""")
conn.commit()

# --------- MEMORY RETRIEVAL ----------
def get_memory(limit=6):
    cursor.execute("""
        SELECT topic, agent, response
        FROM conversations
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()

    memory_text = ""
    for row in rows:
        memory_text += f"\nTopic: {row[0]}\n{row[1]} said:\n{row[2]}\n"

    return memory_text

# --------- MODERATOR CHECK ----------
def compute_confidence(text, topic):
    words = len(text.split())
    sentences = len(re.findall(r'[.!?]+', text))
    topic_keywords = topic.lower().split()

    # --- Length Score ---
    if 50 <= words <= 120:
        length_score = 1.0
    elif 30 <= words < 50 or 120 < words <= 150:
        length_score = 0.7
    else:
        length_score = 0.4

    # --- Structure Score ---
    structure_score = min(sentences / 3, 1.0)

    # --- Topic Relevance ---
    matches = sum(1 for word in topic_keywords if word in text.lower())
    relevance_score = min(matches / len(topic_keywords), 1.0) if topic_keywords else 0.5

    # --- Analytical Depth ---
    reasoning_words = ["because", "therefore", "however", "impact", "leads", "results", "affects"]
    reasoning_hits = sum(1 for word in reasoning_words if word in text.lower())
    reasoning_score = min(reasoning_hits / 3, 1.0)

    # --- Final Weighted Score ---
    confidence = round(
        (0.25 * length_score) +
        (0.20 * structure_score) +
        (0.25 * relevance_score) +
        (0.30 * reasoning_score),
        2
    )

    return confidence

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="Multi-Agent News AI", layout="wide")
st.title("🌍 Multi-Agent World Discussion")

topic = st.text_input("Enter Topic:")

if "discussion_messages" not in st.session_state:
    st.session_state.discussion_messages = []
if "display_limit" not in st.session_state:
    st.session_state.display_limit = 0
if "discussion_topic" not in st.session_state:
    st.session_state.discussion_topic = ""

if st.button("Start Discussion") and topic:

    # --------- FETCH MEMORY ----------
    past_memory = get_memory()

    # --------- WEB SEARCH ----------
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    search_result = tavily.search(query=topic, max_results=5)

    web_context = "\n".join(
        [r["content"] for r in search_result["results"]]
    )

    # --------- MODEL CLIENT ----------
    model_client_news = OpenAIChatCompletionClient(
        model=MODEL_NAME,
        api_key=GEMINI_API_KEY1,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        temperature=0.35,
    )

    model_client_geo = OpenAIChatCompletionClient(
        model=MODEL_NAME,
        api_key=GEMINI_API_KEY2,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        temperature=0.55,
    )

    model_client_econ = OpenAIChatCompletionClient(
        model=MODEL_NAME,
        api_key=GEMINI_API_KEY1,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        temperature=0.7,
    )

    COMMON_RULES = """
    RESPONSE GUIDELINES:
    - Maximum 100 words.
    - Maintain analytical depth.
    - Include reasoning (cause-effect, implications).
    - Stay factual and relevant to topic.
    - Avoid repetition and fluff.
    - Do not repeat another agent's wording.
    - Add one disagreement or nuance against the previous agent whenever appropriate.
    """

    # --------- AGENTS ----------
    news_analyst = AssistantAgent(
        name="NewsAnalyst",
        system_message=f"""
        You are a very experienced news analyst.
        Focus on summarizing CURRENT breaking news from search results.
        If search data is available, prioritize it.
        Remain neutral and factual.
        Use web context and conversation history.
        OUTPUT FORMAT (strict):
        - Headline:
        - What happened (2 bullets)
        - Why it matters (1 sentence)
        {COMMON_RULES}
        """,
        model_client=model_client_news,
    )

    geopolitics_expert = AssistantAgent(
        name="GeopoliticsExpert",
        system_message=f"""
        Analyze geopolitical tensions, diplomacy, and international relations.
        Connect current search findings with historical patterns.
        Use web context and past discussion.
        OUTPUT FORMAT (strict):
        - Strategic lens:
        - Regional implications (2 bullets)
        - Counterpoint to previous speaker (1 sentence)
        {COMMON_RULES}
        """,
        model_client=model_client_geo,
    )

    economist = AssistantAgent(
        name="Economist",
        system_message=f"""
        You are a global economist.
        Focus on markets, inflation, global economy impact.
        Use web context and memory.
        OUTPUT FORMAT (strict):
        - Market signal:
        - Macro impact (2 bullets)
        - Risk scenario (1 sentence)
        {COMMON_RULES}
        """,
        model_client=model_client_econ,
    )

    # --------- GROUP CHAT ----------
    team = RoundRobinGroupChat(
        [news_analyst, geopolitics_expert, economist],
        max_turns=MAX_TURNS
    )

    async def run_chat():
        full_prompt = f"""
        Current Topic: {topic}

        Web Context:
        {web_context}

        Previous Conversation Memory:
        {past_memory}

        Discussion protocol:
        1) Each speaker must add at least one new point not already stated.
        2) Each speaker should reference one claim from the immediate previous speaker and either refine or challenge it.
        3) Keep each turn within {MAX_WORDS} words.
        4) Avoid sentence-level repetition across turns.

        Discuss the topic considering historical continuity.
        """
        result = await team.run(task=full_prompt)
        return result

    result = asyncio.run(run_chat())

    # Prepare structured messages once
    prepared_messages = []
    for message in result.messages:
        if message.source != "user":
            confidence = compute_confidence(message.content, topic)
            prepared_messages.append(
                {
                    "source": message.source,
                    "content": message.content,
                    "confidence": confidence,
                }
            )

            # Save to DB once per generated discussion
            cursor.execute(
                "INSERT INTO conversations (topic, agent, response, confidence) VALUES (?, ?, ?, ?)",
                (topic, message.source, message.content, confidence)
            )

    conn.commit()

    # Persist for progressive display
    st.session_state.discussion_messages = prepared_messages
    st.session_state.display_limit = min(3, len(prepared_messages))
    st.session_state.discussion_topic = topic

    st.success("Conversation stored & memory updated.")

# --------- PROGRESSIVE DISPLAY ----------
if st.session_state.discussion_messages:
    st.subheader("Discussion Results")
    st.caption(f"Topic: {st.session_state.discussion_topic}")

    visible_messages = st.session_state.discussion_messages[:st.session_state.display_limit]

    for message in visible_messages:
        st.markdown(f"### 🧠 {message['source']}")
        st.markdown(message["content"])

        if message["confidence"] >= 0.75:
            st.success("🟢 Moderator: High analytical confidence.")
        elif message["confidence"] >= 0.5:
            st.warning("🟡 Moderator: Moderate confidence. Could improve depth or clarity.")
        else:
            st.error("🔴 Moderator: Low confidence. Response lacks depth or relevance.")

        st.write(f"Confidence Score: {message['confidence']}")

    total_messages = len(st.session_state.discussion_messages)
    remaining = total_messages - st.session_state.display_limit

    if remaining > 0:
        st.info(f"{remaining} more responses are ready.")
        if st.button("Show next 3 responses"):
            st.session_state.display_limit = min(st.session_state.display_limit + 3, total_messages)
            st.rerun()

