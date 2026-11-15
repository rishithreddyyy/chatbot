# ⚡ CODE FORGE AI — Advanced AI-Powered All-in-One Platform

> **Search. Think. Code. Explore.**  
> An autonomous multi-agent software engineering, intelligence, and financial analytics workspace.

Developed & Designed by **[Rishith Reddy Serikar](https://github.com/rishithreddyyy)**  
*"Building Intelligent Solutions with AI & Technology."*  
GitHub: [rishithreddyyy](https://github.com/rishithreddyyy) | LinkedIn: [rishith-reddyyy](https://www.linkedin.com/in/rishith-reddyyy/)

---

## 🌟 Overview

**Code Forge AI** is an enterprise-grade, multi-agent AI platform built in Python. It unifies five mission-critical developer modules into a single, cohesive, modern workspace:

1. **📊 Main Dashboard**: Real-time platform metrics, live Indian (NIFTY 50, SENSEX, BANK NIFTY) and Global (S&P 500, NASDAQ, Dow Jones) benchmarks, quick-access action cards, and universal search.
2. **💬 AI Assistant**: Natural language reasoning, multi-language coding (Python, Java, C++, TypeScript, SQL, Go, Rust), syntax highlighting, line-by-line debugging, and conversational context persistence.
3. **🌐 Web Search Explorer**: Real-time internet search powered by autonomous retrieval agents with source citations, AI summarization, and dedicated technical/coding documentation modes.
4. **💻 Code Generator & Isolated Terminal Runner**: Multi-language code generator, language-to-language converter, line-by-line code explainer, and a secure Python execution subprocess sandbox.
5. **📈 Finance & Stock Hub**: Live market data, interactive Plotly candlestick charts (1D, 5D, 1M, 3M, 6M, 1Y, 5Y), company fundamentals, financial news aggregation, and automated AI stock movement explanations.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend / UI** | Streamlit 1.40+, Plotly, Custom Responsive CSS (`Plus Jakarta Sans`, `JetBrains Mono`) |
| **Backend & Orchestration** | Python 3.10+, Autonomous Tool Dispatcher, Multi-Turn Memory Buffer |
| **AI / LLM Providers** | Google Gemini (`gemini-3.8-flash`, `gemini-3.8-pro`), OpenAI (`gpt-4o`, `o3-mini`), Ollama, Built-in Smart Engine |
| **Market Intelligence** | Yahoo Finance (`yfinance`), Interactive Plotly Financial Candlesticks |
| **Search Engine** | DuckDuckGo Search API (`duckduckgo-search`), BeautifulSoup4 |
| **Terminal Sandbox** | Python `subprocess` with execution timeouts and safety command filtering |
| **Persistence** | SQLite 3 (`codeforge.db`) for chat sessions, search history, watchlist, and user settings |

---

## 📁 Project Folder Structure

```
chatbot/
├── .env.example               # Environment variable configuration template
├── .gitignore                 # Comprehensive git exclusion rules
├── app.py                     # Primary Streamlit web application & UI modules
├── cli.py                     # Interactive terminal CLI agent
├── config.py                  # Central configuration, model registry, environment loader
├── main.py                    # Unified application launcher (Web UI or CLI)
├── requirements.txt           # Production dependency specifications
├── test_agents.py             # Unit tests for tools, sandbox, and orchestrator
├── core/                      # Core AI & system architecture
│   ├── __init__.py
│   ├── code_generator.py      # Code generator, language converter, line explainer
│   ├── database.py            # SQLite persistence layer (sessions, watchlist, settings)
│   ├── llm_client.py          # Unified client for Gemini, OpenAI, Ollama, Smart Engine
│   ├── memory.py              # In-memory conversational state buffer
│   └── orchestrator.py        # Autonomous multi-agent routing & tool execution pipeline
└── tools/                     # Autonomous agent tools
    ├── __init__.py
    ├── base.py                # ToolBase & ToolResult abstractions
    ├── finance_agent.py       # Stock quotes, historical data, Plotly charts, market news
    ├── search_agent.py        # Live web search, coding search, AI summarizer
    └── terminal_agent.py      # Subprocess execution sandbox & safe file tools
```

---

## 🚀 Getting Started Locally

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 installed.
- Git installed.

### 2. Clone the Repository
```bash
git clone https://github.com/rishithreddyyy/code-forge-ai.git
cd code-forge-ai
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure API Keys
Copy the example environment file:
```bash
cp .env.example .env
```
Edit `.env` and add your Google Gemini or OpenAI API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Note: Code Forge AI also includes an autonomous built-in Smart Engine that runs out-of-the-box even without an API key!)*

### 6. Run the Application

#### Option A: Web Application (Recommended)
```bash
streamlit run app.py
# or using the main launcher:
python main.py
```
Open **`http://localhost:8501`** in your browser.

#### Option B: Terminal CLI Mode
```bash
python main.py --cli
# or directly:
python cli.py
```

---

## 🧪 Running Automated Tests

Run the automated test suite to verify tool sandboxing, agent routing, and configuration:
```bash
python -m unittest test_agents.py
```

---

## ☁️ Deployment Guide

### Why Not Vercel Serverless?
**Code Forge AI** is built on **Streamlit**, which requires a persistent Python process that maintains active bidirectional **WebSockets**, stateful session memory, and subprocess execution capabilities. 

**Vercel's Serverless Platform** is engineered for static frontend sites (Next.js, React) and stateless HTTP functions with ephemeral execution lifecycles (10–60 second maximum execution timeout, read-only filesystems, and no persistent WebSocket daemons). Deploying a Streamlit application directly to Vercel Serverless results in WebSocket disconnections, read-only database locks, and runtime terminations.

---

### Recommended Production Deployment Platforms

#### 1. Streamlit Community Cloud (1-Click, Free & Official)
The fastest and most reliable free hosting platform for Streamlit applications:
1. Push your repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub account and select your `code-forge-ai` repository.
4. Set the **Main file path** to `app.py`.
5. Under **Advanced Settings > Secrets**, paste your environment variables:
   ```toml
   GEMINI_API_KEY = "your_actual_api_key"
   ```
6. Click **Deploy**. Your live app will be accessible worldwide on a custom `.streamlit.app` URL.

#### 2. Render / Railway / Hugging Face Spaces (Container Service)
For dedicated container environments:
- **Render**: Create a *Web Service*, connect your GitHub repo, and set:
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- **Hugging Face Spaces**: Select the **Streamlit** SDK, connect your repository, and add `GEMINI_API_KEY` under Settings > Secrets.

---

## 🛡️ Security & Privacy
- **API Key Protection**: API keys are loaded via environment variables and never rendered in frontend responses or committed to source control.
- **Subprocess Sandbox**: The Terminal Agent filters dangerous destructive system commands (`rmdir`, `format`, `del /f`) and enforces timeouts.
- **Git Hygiene**: `.gitignore` strictly excludes `.env`, `*.db`, SQLite files, and bytecode.

---

## 📄 License & Attribution
© 2026 Code Forge AI. All Rights Reserved.  
Developed & Designed by **Rishith Reddy Serikar**.
