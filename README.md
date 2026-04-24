# Multi-Agent News AI (AgenticNews)

🌍 **Multi-Agent World Discussion Platform**

AgenticNews is an interactive, multi-agent AI application for analyzing and discussing world news topics. It leverages advanced LLMs, web search, and persistent memory to simulate a panel of expert agents (News Analyst, Geopolitics Expert, Economist) who debate and analyze current events with analytical depth and reasoning.

## Features

- **Multi-Agent Discussion:** Three specialized AI agents (News Analyst, Geopolitics Expert, Economist) discuss a user-provided topic in a round-robin format.
- **Web Search Integration:** Uses Tavily API to fetch up-to-date news context for the discussion.
- **Persistent Memory:** Stores previous conversations in a SQLite database to inform future discussions.
- **Analytical Confidence Scoring:** Each agent response is scored for analytical depth, relevance, and structure.
- **Streamlit UI:** Clean, interactive web interface for entering topics and viewing progressive discussion results.
- **Customizable Models:** Supports Gemini/OpenAI-compatible models with adjustable temperature and API keys.

## How It Works

1. **User enters a topic** in the Streamlit web app.
2. The app fetches recent news context using Tavily search.
3. Three AI agents (News Analyst, Geopolitics Expert, Economist) take turns discussing the topic, referencing web context and conversation memory.
4. Each response is scored for confidence and stored in a SQLite database.
5. Results are displayed progressively, with moderator feedback on analytical quality.

## Project Structure

- `AgenticNewsApp.py` — Main Streamlit application and agent orchestration logic.
- `memory.db` — SQLite database for storing conversation history (auto-created).
- `README.md` — Project documentation (this file).

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/GitWizard2000/AgenticNewsApplication.git
cd AgenticNews
```

### 2. Install Dependencies

Install Python 3.8+ and run:

```bash
pip install -r requirements.txt
# Or manually:
pip install streamlit python-dotenv tavily autogen-agentchat autogen-ext
```

### 3. Environment Variables

Create a `.env` file in the project root with the following keys:

```
GEMINI_API_KEY1=your_gemini_api_key_1
GEMINI_API_KEY2=your_gemini_api_key_2
TAVILY_API_KEY=your_tavily_api_key
```

### 4. Run the App

```bash
streamlit run AgenticNewsApp.py
```

## Usage

1. Open the app in your browser (Streamlit will provide a local URL).
2. Enter a news topic (e.g., "Global inflation trends").
3. Click **Start Discussion** to generate a multi-agent debate.
4. View results, confidence scores, and progressively reveal more responses.

## Agent Roles

- **NewsAnalyst:** Summarizes current breaking news, prioritizes search results, remains neutral and factual.
- **GeopoliticsExpert:** Analyzes geopolitical tensions, connects current events to historical patterns, provides counterpoints.
- **Economist:** Focuses on markets, inflation, and macroeconomic impacts, highlights risk scenarios.

## Technologies Used

- Python 3.8+
- Streamlit
- SQLite
- Tavily API (web search)
- Gemini/OpenAI-compatible LLMs
- dotenv (for environment variables)

## Customization

- **Model Selection:** Change `MODEL_NAME` or API keys in `AgenticNewsApp.py` or `.env`.
- **Agent Prompts:** Modify agent system messages for different discussion styles.
- **Database:** Uses `memory.db` (SQLite) for persistent memory; can be swapped for other databases.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/), [Tavily](https://tavily.com/), and [Autogen](https://github.com/microsoft/autogen).

---
*For questions or contributions, please open an issue or pull request on GitHub.*
