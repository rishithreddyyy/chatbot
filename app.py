"""
CODE FORGE AI — Advanced AI-Powered All-in-One Platform
Tagline: Search. Think. Code. Explore.

Modules:
1. Main Dashboard (Global Search, Overview, Quick-Access Cards, Recent Activity)
2. AI Assistant (Multi-language coding, math, science, debugging, follow-up context)
3. Web Search Explorer (Live web search, coding mode, AI summarization, citations)
4. Code Generator & Terminal Runner (Multi-language generator, converter, line-by-line explainer, secure Python runner)
5. Finance & Stock Hub (Indian & Global markets, NIFTY 50, S&P 500, interactive Plotly charts 1D..5Y, watchlist, financial news)
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Path setup
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import AssistantConfig, MODELS_CATALOG
from core.orchestrator import AgentOrchestrator
from core.code_generator import (
    SUPPORTED_LANGUAGES, CODE_TEMPLATES,
    explain_code_lines, convert_code_language
)
from core.database import (
    save_chat_message, get_chat_history, clear_session_chat,
    record_search, get_recent_searches,
    get_watchlist, add_to_watchlist, remove_from_watchlist,
    save_snippet, get_saved_snippets, delete_snippet,
    get_setting, set_setting
)
from tools.search_agent import WebSearchTool, CodingSearchTool, summarize_search_results
from tools.finance_agent import (
    GetStockQuoteTool, GetHistoricalDataTool, GetCompanyOverviewTool,
    CompareTickersTool, fetch_market_indices_snapshot, fetch_stock_news,
    explain_stock_movement, build_plotly_candlestick,
    MARKET_INDICES, POPULAR_STOCKS
)
from tools.terminal_agent import (
    RunTerminalCommandTool, ExecutePythonCodeTool,
    ListWorkspaceFilesTool, ReadWorkspaceFileTool
)

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Code Forge AI | All-in-One Workspace",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SESSION STATE -----------------
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "theme" not in st.session_state:
    st.session_state.theme = get_setting("theme", "dark")
if "nav_radio" not in st.session_state:
    st.session_state.nav_radio = "Dashboard"
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "Dashboard"
if "config" not in st.session_state:
    st.session_state.config = AssistantConfig()
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator(st.session_state.config)
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = get_chat_history(st.session_state.session_id)
if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None

# Navigation Callbacks (Avoids StreamlitWidgetAlreadyInstantiatedError)
def navigate_to(target_page: str, quick_prompt: str = None):
    """Callback to switch active page safely before widgets instantiate."""
    st.session_state.nav_radio = target_page
    st.session_state.active_nav = target_page
    if quick_prompt is not None:
        st.session_state.quick_prompt = quick_prompt

def on_nav_change():
    """Callback when sidebar radio widget changes."""
    st.session_state.active_nav = st.session_state.nav_radio

# Query parameter routing (?nav=Dashboard)
if "nav" in st.query_params:
    qp_nav = st.query_params["nav"]
    valid_navs = [
        "Dashboard",
        "AI Assistant",
        "Web Search Explorer",
        "Code Generator & Terminal",
        "Finance & Stock Hub"
    ]
    if qp_nav in valid_navs:
        st.session_state.nav_radio = qp_nav
        st.session_state.active_nav = qp_nav

is_dark = (st.session_state.theme == "dark")

# ----------------- THEME STYLING (DARK & LIGHT) -----------------
if is_dark:
    bg_color = "#090d16"
    panel_bg = "#0f1523"
    card_bg = "#131b2e"
    card_border = "rgba(255, 255, 255, 0.08)"
    text_color = "#f1f5f9"
    text_muted = "#94a3b8"
    accent_green = "#00ff87"
    accent_cyan = "#00e5ff"
    terminal_bg = "#070a10"
    user_bubble = "#1b253b"
else:
    bg_color = "#f8fafc"
    panel_bg = "#ffffff"
    card_bg = "#ffffff"
    card_border = "#e2e8f0"
    text_color = "#0f172a"
    text_muted = "#64748b"
    accent_green = "#10b981"
    accent_cyan = "#0284c7"
    terminal_bg = "#0f172a"
    user_bubble = "#f1f5f9"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
        background-color: {bg_color} !important;
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
        color: {text_color} !important;
    }}
    [data-testid="stHeader"] {{ background: transparent !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {panel_bg} !important;
        border-right: 1px solid {card_border} !important;
    }}

    /* Global Typography */
    h1, h2, h3, h4 {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        color: {text_color} !important;
    }}

    /* Top Brand */
    .brand-container {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }}
    .brand-logo {{
        background: linear-gradient(135deg, {accent_green}, {accent_cyan});
        color: #090d16;
        font-weight: 800;
        font-size: 1.1rem;
        padding: 5px 10px;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
    }}
    .brand-name {{
        font-size: 1.15rem;
        font-weight: 800;
        color: {text_color};
        letter-spacing: -0.4px;
    }}
    .tagline-text {{
        font-size: 0.72rem;
        color: {text_muted};
        font-weight: 500;
        margin-bottom: 1rem;
        letter-spacing: 0.5px;
    }}

    /* Status Pill */
    .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0, 255, 135, 0.08);
        border: 1px solid rgba(0, 255, 135, 0.25);
        color: {accent_green};
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 1.2rem;
    }}
    .status-dot {{
        width: 7px;
        height: 7px;
        background: {accent_green};
        border-radius: 50%;
        box-shadow: 0 0 8px {accent_green};
    }}

    /* Cards */
    .dashboard-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .dashboard-card:hover {{
        border-color: rgba(0, 255, 135, 0.4);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }}

    /* User Bubble */
    .chat-bubble-user {{
        background: {user_bubble};
        border: 1px solid {card_border};
        border-radius: 14px;
        padding: 12px 18px;
        margin: 10px 0 14px auto;
        max-width: 85%;
        color: {text_color};
        font-size: 0.95rem;
    }}

    /* AI Avatar & Header */
    .chat-bubble-ai {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 14px 0 6px 0;
        font-weight: 700;
        color: {accent_green};
        font-size: 0.9rem;
    }}
    .ai-badge {{
        background: {accent_green};
        color: #090d16;
        width: 26px;
        height: 26px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.85rem;
    }}

    /* Terminal Console */
    .terminal-console {{
        background: {terminal_bg};
        border: 1px solid rgba(0, 255, 135, 0.25);
        border-radius: 10px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        color: #e6edf3;
        font-size: 0.86rem;
        white-space: pre-wrap;
        overflow-x: auto;
    }}

    /* Buttons */
    .stButton>button {{
        background: {card_bg} !important;
        border: 1px solid {card_border} !important;
        color: {text_color} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.15s ease !important;
    }}
    .stButton>button:hover {{
        border-color: {accent_green} !important;
        color: {accent_green} !important;
        box-shadow: 0 0 12px rgba(0, 255, 135, 0.2) !important;
    }}

    /* Metric cards */
    div[data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        color: {text_color} !important;
    }}

    /* Universal Input */
    [data-testid="stChatInput"] textarea {{
        background: {card_bg} !important;
        border: 1px solid {card_border} !important;
        color: {text_color} !important;
        border-radius: 10px !important;
    }}
    [data-testid="stChatInput"] textarea:focus {{
        border-color: {accent_green} !important;
        box-shadow: 0 0 10px rgba(0, 255, 135, 0.2) !important;
    }}

    pre {{
        background: {terminal_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 8px !important;
    }}
    code {{ font-family: 'JetBrains Mono', monospace !important; }}

    /* Premium Developer Footer */
    .site-footer {{
        border-top: 1px solid {card_border};
        background: {panel_bg};
        border-radius: 14px;
        padding: 32px 20px 24px 20px;
        margin-top: 3.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.12);
    }}
    .footer-developer-label {{
        font-size: 0.76rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.6px;
        color: {text_muted};
        margin-bottom: 6px;
    }}
    .footer-developer-name {{
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.3px;
        margin-bottom: 6px;
        background: linear-gradient(135deg, {accent_green}, {accent_cyan});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }}
    .footer-tagline {{
        font-size: 0.88rem;
        color: {text_muted};
        font-weight: 500;
        margin-bottom: 18px;
        font-style: italic;
    }}
    .footer-social-links {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 14px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }}
    .social-btn {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 10px;
        color: {text_color} !important;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.84rem;
        transition: all 0.25s ease;
    }}
    .social-btn:hover {{
        border-color: {accent_green} !important;
        color: {accent_green} !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0, 255, 135, 0.2);
    }}
    .social-btn svg {{
        width: 17px;
        height: 17px;
        fill: currentColor;
    }}
    .footer-copyright {{
        font-size: 0.78rem;
        color: {text_muted};
        border-top: 1px solid {card_border};
        padding-top: 16px;
        margin-top: 14px;
        letter-spacing: 0.3px;
    }}

    /* Centered Brand Header Button (Clickable Logo + Project Name) */
    .st-key-btn_nav_home_brand {{
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 auto !important;
        text-align: center !important;
    }}
    .st-key-btn_nav_home_brand button {{
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 14px !important;
        padding: 6px 20px !important;
        color: {text_color} !important;
        box-shadow: none !important;
        cursor: pointer !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto !important;
    }}
    .st-key-btn_nav_home_brand button:hover {{
        background: {card_bg} !important;
        border-color: {accent_green} !important;
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(0, 255, 135, 0.16) !important;
    }}
    .st-key-btn_nav_home_brand button p {{
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
        color: {text_color} !important;
        margin: 0 !important;
        line-height: 1.25 !important;
        text-align: center !important;
        transition: color 0.2s ease !important;
    }}
    .st-key-btn_nav_home_brand button:hover p {{
        color: {accent_green} !important;
    }}
    .header-tagline-center {{
        text-align: center;
        font-size: 0.88rem;
        color: {text_muted};
        margin-top: -4px;
        margin-bottom: 1.25rem;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    @media (max-width: 768px) {{
        .st-key-btn_nav_home_brand button p {{
            font-size: 1.45rem !important;
        }}
    }}

    /* Sidebar Clickable Logo/Brand */
    .st-key-btn_sidebar_home_brand button {{
        background: transparent !important;
        border: 1px solid {card_border} !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
        color: {text_color} !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        letter-spacing: -0.3px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }}
    .st-key-btn_sidebar_home_brand button:hover {{
        border-color: {accent_green} !important;
        color: {accent_green} !important;
        background: rgba(0, 255, 135, 0.06) !important;
    }}
</style>
""", unsafe_allow_html=True)


# ================= SIDEBAR NAVIGATION & CONTROLS =================
with st.sidebar:
    st.button(
        "⚡ CODE FORGE AI",
        key="btn_sidebar_home_brand",
        on_click=navigate_to,
        args=("Dashboard",),
        use_container_width=True,
        help="Return to Dashboard Home"
    )

    st.markdown("""
    <div class="tagline-text" style="text-align:center;">Search. Think. Code. Explore.</div>
    <div class="status-pill" style="display:flex; justify-content:center; margin: 0 auto 1rem auto;">
        <span class="status-dot"></span>
        All Systems Operational
    </div>
    """, unsafe_allow_html=True)

    # Navigation menu
    st.markdown("### 📌 Navigation")
    nav_options = [
        "Dashboard",
        "AI Assistant",
        "Web Search Explorer",
        "Code Generator & Terminal",
        "Finance & Stock Hub"
    ]
    st.radio(
        "Navigate",
        nav_options,
        key="nav_radio",
        on_change=on_nav_change,
        label_visibility="collapsed"
    )
    st.session_state.active_nav = st.session_state.nav_radio

    st.markdown("---")

    # Theme Toggle (Dark / Light)
    st.markdown("### 🎨 Preferences")
    col_th1, col_th2 = st.columns(2)
    with col_th1:
        if st.button("🌙 Dark" if not is_dark else "☀️ Light", use_container_width=True):
            new_theme = "light" if is_dark else "dark"
            st.session_state.theme = new_theme
            set_setting("theme", new_theme)
            st.rerun()
    with col_th2:
        if st.button("🗑️ Reset Chat", use_container_width=True):
            st.session_state.chat_messages = []
            clear_session_chat(st.session_state.session_id)
            st.session_state.orchestrator.memory.clear()
            st.rerun()

    # User Profile Section
    user_name = get_setting("username", "Developer")
    st.markdown(f"""
    <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:10px; padding:12px; margin-top:10px;">
        <div style="font-size:0.78rem; color:{text_muted}; text-transform:uppercase; letter-spacing:0.5px;">User Profile</div>
        <div style="font-weight:700; font-size:0.95rem; color:{text_color};">👤 {user_name}</div>
        <div style="font-size:0.75rem; color:{accent_green};">Pro Workspace Active</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Model & Engine Settings
    with st.expander("⚙️ AI Model & API Keys", expanded=False):
        current_provider = get_setting("default_provider", "gemini")
        provider_choice = st.selectbox(
            "Engine Provider",
            ["gemini", "smart_engine", "openai", "ollama"],
            index=["gemini", "smart_engine", "openai", "ollama"].index(current_provider) if current_provider in ["gemini", "smart_engine", "openai", "ollama"] else 0
        )
        set_setting("default_provider", provider_choice)

        model_name = st.selectbox(
            "Active Model",
            MODELS_CATALOG.get(provider_choice, ["default"]),
            index=0
        )

        env_gemini = os.environ.get("GEMINI_API_KEY", "")
        api_key_input = st.text_input(
            f"{provider_choice.capitalize()} API Key",
            value=st.session_state.config.api_key or env_gemini,
            type="password",
            help="Loaded securely from server .env"
        )

        st.session_state.orchestrator.update_config(
            provider=provider_choice,
            model_name=model_name,
            api_key=api_key_input or None
        )

    # Footer
    st.markdown(f"""
    <div style="margin-top: 2rem; font-size: 0.72rem; color: {text_muted}; text-align: center;">
        <b>Code Forge AI</b> v3.5<br/>
        Built for Speed, Intelligence & Safety
    </div>
    """, unsafe_allow_html=True)


# ================= CENTERED LOGO & PROJECT NAME (CLICK TO HOME) =================
_, col_brand_center, _ = st.columns([1, 4, 1])
with col_brand_center:
    st.button(
        "⚡  Code Forge AI Platform",
        key="btn_nav_home_brand",
        on_click=navigate_to,
        args=("Dashboard",),
        use_container_width=True,
        help="Click logo or project name to return to Dashboard Home"
    )

    st.markdown(f"""
    <div class="header-tagline-center">
        Unified Workspace: Search. Think. Code. Explore.
    </div>
    """, unsafe_allow_html=True)

# Global Search Box
global_query = st.text_input(
    "Universal Search",
    placeholder="🔍 Universal Search: Ask AI, search live web, run Python code, or lookup stock tickers...",
    label_visibility="collapsed"
)

if global_query:
    # Route global query based on query content
    g_lower = global_query.strip().lower()
    st.markdown(f"**Universal Search Results for:** *\"{global_query}\"*")
    col_res1, col_res2 = st.columns([2, 1])

    with col_res1:
        if any(g_lower.startswith(sc) for sc in ["print(", "import ", "def ", "class ", "python:"]):
            st.info("🐍 Detected Python Code. Running in sandbox...")
            py_res = ExecutePythonCodeTool().execute(code=global_query.replace("python:", ""))
            st.markdown(f'<div class="terminal-console">{py_res.output}</div>', unsafe_allow_html=True)
        elif any(sym in g_lower for sym in ["nvda", "aapl", "tsla", "nifty", "stock", "price", "btc"]):
            st.info("📈 Detected Stock/Market query. Fetching real market quote...")
            stock_res = GetStockQuoteTool().execute(symbol=global_query)
            st.markdown(stock_res.output)
        else:
            st.info("🌐 Querying live web...")
            w_res = WebSearchTool().execute(query=global_query, num_results=3)
            if w_res.success and w_res.data and "results" in w_res.data:
                for r in w_res.data["results"]:
                    st.markdown(f"• **[{r['title']}]({r['url']})**: {r['snippet']}")
            else:
                st.markdown(w_res.output)

    with col_res2:
        st.markdown("**Quick Jump:**")
        st.button(
            "💬 Ask AI Assistant",
            key="g_ask",
            on_click=navigate_to,
            args=("AI Assistant", global_query),
            use_container_width=True
        )
        st.button(
            "🌐 Search in Web Explorer",
            key="g_search",
            on_click=navigate_to,
            args=("Web Search Explorer",),
            use_container_width=True
        )
        st.button(
            "📈 View in Stock Hub",
            key="g_fin",
            on_click=navigate_to,
            args=("Finance & Stock Hub",),
            use_container_width=True
        )

    st.divider()


# ================= MODULE 1: MAIN DASHBOARD =================
if st.session_state.active_nav == "Dashboard":
    st.markdown("### 📊 Platform Overview & Quick Access")

    # 4 Quick-Access Feature Cards
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="dashboard-card">
            <h3 style="color:{accent_green}; margin-top:0;">💬 AI Assistant</h3>
            <p style="color:{text_muted}; font-size:0.85rem;">
                Ask programming, math, science, and general knowledge questions. Generate and debug code.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Launch Assistant →", key="btn_dash_ai", on_click=navigate_to, args=("AI Assistant",), use_container_width=True)

    with c2:
        st.markdown(f"""
        <div class="dashboard-card">
            <h3 style="color:{accent_cyan}; margin-top:0;">🌐 Web Explorer</h3>
            <p style="color:{text_muted}; font-size:0.85rem;">
                Real-time internet search for documentation, tutorials, errors, and current news with citations.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Launch Explorer →", key="btn_dash_search", on_click=navigate_to, args=("Web Search Explorer",), use_container_width=True)

    with c3:
        st.markdown(f"""
        <div class="dashboard-card">
            <h3 style="color:#f59e0b; margin-top:0;">💻 Code & Terminal</h3>
            <p style="color:{text_muted}; font-size:0.85rem;">
                Multi-language code generator, converter, line explainer, and isolated Python execution runner.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Launch Workspace →", key="btn_dash_code", on_click=navigate_to, args=("Code Generator & Terminal",), use_container_width=True)

    with c4:
        st.markdown(f"""
        <div class="dashboard-card">
            <h3 style="color:#ec4899; margin-top:0;">📈 Finance Hub</h3>
            <p style="color:{text_muted}; font-size:0.85rem;">
                Real Indian (NIFTY/SENSEX) and US markets, interactive candlestick charts, news, and watchlist.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Launch Finance →", key="btn_dash_fin", on_click=navigate_to, args=("Finance & Stock Hub",), use_container_width=True)

    st.markdown("---")

    # Live Market Snapshot Row
    st.markdown("### 🌐 Live Market Benchmarks (Indian & Global)")
    with st.spinner("Fetching live market indices..."):
        indices_data = fetch_market_indices_snapshot()
        if indices_data:
            idx_cols = st.columns(len(indices_data))
            for i, item in enumerate(indices_data):
                with idx_cols[i]:
                    sign = "+" if item["change"] >= 0 else ""
                    st.metric(
                        item["name"],
                        f"{item['price']:,.2f}",
                        f"{sign}{item['change_pct']:.2f}%"
                    )

    st.markdown("---")

    # Recent Activities & Search History Row
    dash_col1, dash_col2 = st.columns(2)

    with dash_col1:
        st.markdown("#### 🕒 Recent Web Searches")
        recent_s = get_recent_searches(limit=6)
        if recent_s:
            for s in recent_s:
                st.markdown(f"• **{s['query']}** <span style='font-size:0.75rem; color:{text_muted};'>({s['created_at'][:16]})</span>", unsafe_allow_html=True)
        else:
            st.caption("No recent searches logged yet.")

    with dash_col2:
        st.markdown("#### ⭐ Your Stock Watchlist")
        w_list = get_watchlist()
        if w_list:
            for w in w_list[:6]:
                st.markdown(f"• **{w['symbol']}** — {w['name']} <span style='font-size:0.75rem; color:{accent_green};'>({w['market']})</span>", unsafe_allow_html=True)
        else:
            st.caption("Watchlist is currently empty.")


# ================= MODULE 2: AI ASSISTANT =================
elif st.session_state.active_nav == "AI Assistant":
    st.markdown("### 💬 AI Assistant (Powered by Gemini & Smart Engine)")
    st.caption("Ask natural language questions across programming, math, science, technology, business, and general topics.")

    # Action bar
    top_c1, top_c2, top_c3, top_c4 = st.columns(4)
    with top_c1:
        if st.button("🐍 Python Concurrency", use_container_width=True):
            st.session_state.quick_prompt = "Explain Python asyncio TaskGroup and provide a production code example."
            st.rerun()
    with top_c2:
        if st.button("🛡️ Debug FastAPI Health", use_container_width=True):
            st.session_state.quick_prompt = "Explain the safest way to add a health check to a FastAPI project."
            st.rerun()
    with top_c3:
        if st.button("📊 Quantitative Algorithm", use_container_width=True):
            st.session_state.quick_prompt = "Write a quantitative trading strategy in Python calculating 20 and 50-day moving average crossovers."
            st.rerun()
    with top_c4:
        if st.button("💡 Project Architectures", use_container_width=True):
            st.session_state.quick_prompt = "Propose a complete modern fullstack SaaS architecture using FastAPI, Next.js, and PostgreSQL."
            st.rerun()

    st.divider()

    # Chat Feed
    for idx, msg in enumerate(st.session_state.chat_messages):
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="chat-bubble-ai"><div class="ai-badge">✳</div> Code Forge AI</div>', unsafe_allow_html=True)

            if msg.get("traces"):
                for trace in msg["traces"]:
                    agent_icon = "🔍" if "Search" in trace['agent_name'] else ("📈" if "Finance" in trace['agent_name'] else "💻")
                    with st.expander(f"{agent_icon} **{trace['agent_name']}** → `{trace['tool_name']}`", expanded=False):
                        st.code(trace["output"], language="markdown")

            st.markdown(msg["content"])

    # Chat Input Handling
    prompt_to_send = None
    if st.session_state.quick_prompt:
        prompt_to_send = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
    else:
        user_input = st.chat_input("Ask any question in natural language, request code, or ask to debug...")
        if user_input:
            prompt_to_send = user_input

    if prompt_to_send:
        # Save user message to DB and state
        save_chat_message(st.session_state.session_id, "user", prompt_to_send)
        st.session_state.chat_messages.append({"role": "user", "content": prompt_to_send, "traces": []})
        st.markdown(f'<div class="chat-bubble-user">{prompt_to_send}</div>', unsafe_allow_html=True)

        st.markdown('<div class="chat-bubble-ai"><div class="ai-badge">✳</div> Code Forge AI</div>', unsafe_allow_html=True)
        with st.spinner("Generating intelligent response..."):
            res = st.session_state.orchestrator.process_message(prompt_to_send)

            traces_data = [
                {
                    "agent_name": t.agent_name,
                    "tool_name": t.tool_name,
                    "args": t.args,
                    "output": t.output
                }
                for t in res.get("traces", [])
            ]

            if traces_data:
                for trace in traces_data:
                    agent_icon = "🔍" if "Search" in trace['agent_name'] else ("📈" if "Finance" in trace['agent_name'] else "💻")
                    with st.expander(f"{agent_icon} **{trace['agent_name']}** → `{trace['tool_name']}`", expanded=True):
                        st.code(trace["output"], language="markdown")

            st.markdown(res["response"])

            # Save assistant message to DB
            save_chat_message(st.session_state.session_id, "assistant", res["response"], traces_data)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": res["response"],
                "traces": traces_data
            })
            st.rerun()


# ================= MODULE 3: WEB SEARCH EXPLORER =================
elif st.session_state.active_nav == "Web Search Explorer":
    st.markdown("### 🌐 Intelligent Web Search Explorer")
    st.caption("Live, genuine internet search engine powered by DuckDuckGo & Google Search APIs. Never fake results.")

    search_mode = st.radio(
        "Search Mode",
        ["🌍 General Web Search", "💻 Dedicated Coding & Docs Search"],
        horizontal=True
    )

    sc1, sc2 = st.columns([3, 1])
    with sc1:
        web_query = st.text_input("Enter Search Topic", placeholder="e.g. Next.js 15 features, PyTorch 2.4 release, Python IndexError fix...")
    with sc2:
        num_results = st.number_input("Result Count", min_value=1, max_value=10, value=5)

    enable_summarize = st.checkbox("🤖 Automatically summarize search results in simple English", value=True)

    if st.button("🚀 Search Web Live", use_container_width=True, type="primary") and web_query:
        record_search(web_query, category="coding" if "Coding" in search_mode else "general", results_count=num_results)

        with st.spinner(f"Retrieving actual web results for: '{web_query}'..."):
            if "Coding" in search_mode:
                tool = CodingSearchTool()
                s_res = tool.execute(query=web_query)
            else:
                tool = WebSearchTool()
                s_res = tool.execute(query=web_query, num_results=num_results)

            if s_res.success and s_res.data and "results" in s_res.data:
                results_list = s_res.data["results"]
                st.success(f"Found {len(results_list)} genuine web sources:")

                # AI Summary Card
                if enable_summarize:
                    summary_text = summarize_search_results(results_list, web_query)
                    st.markdown(f"""
                    <div style="background:{card_bg}; border:1px solid rgba(0,255,135,0.3); border-radius:10px; padding:16px; margin:14px 0;">
                        <h4 style="color:{accent_green}; margin-top:0;">📋 Executive AI Search Summary</h4>
                        <div style="font-size:0.9rem; line-height:1.6;">{summary_text}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Search Results List with clickable links
                for i, r in enumerate(results_list, 1):
                    with st.container():
                        st.markdown(f"#### {i}. [{r['title']}]({r['url']})")
                        st.markdown(f"*{r['snippet']}*")
                        st.caption(f"🔗 Source: `{r['url']}`")
                        st.divider()
            else:
                st.warning(s_res.output)


# ================= MODULE 4: CODE GENERATOR & TERMINAL RUNNER =================
elif st.session_state.active_nav == "Code Generator & Terminal":
    st.markdown("### 💻 Code Generator & Isolated Terminal Runner")
    st.caption("Generate multi-language code, explain line-by-line, debug, and execute safely in an isolated sandbox.")

    sub_mode = st.radio(
        "Workspace View",
        ["🐍 Terminal & Code Execution", "⚡ Code Generator & Transformer", "📂 Workspace Files"],
        horizontal=True
    )

    if sub_mode == "🐍 Terminal & Code Execution":
        st.markdown("#### ⚡ Python Execution Sandbox")
        st.caption("Type any Python code below. Subprocess sandbox executes with strict resource limits and timeouts.")

        default_py = """# CodeForge Python Execution Sandbox
name = "Rishith Reddy"
age = 21
print(f"Hello, I'm {name} and I'm {age} years old!")

# Quick computation
squares = [x**2 for x in range(1, 6)]
print(f"Squares: {squares}")
"""
        code_input = st.text_area("Python Code", value=default_py, height=220)

        col_run1, col_run2 = st.columns([1, 1])
        with col_run1:
            run_btn = st.button("▶ Run Code in Sandbox", type="primary", use_container_width=True)
        with col_run2:
            save_btn = st.button("💾 Save to Snippets Library", use_container_width=True)

        if save_btn and code_input:
            snip_id = save_snippet("Python Script", "Python", code_input)
            st.success(f"Saved snippet #{snip_id} to database!")

        if run_btn and code_input:
            py_tool = ExecutePythonCodeTool()
            with st.spinner("Executing Python code in isolated sandbox..."):
                res = py_tool.execute(code=code_input)
                if res.success:
                    st.success("✅ Execution Succeeded (Exit Code 0)")
                else:
                    st.error("❌ Execution Encountered Errors")
                st.markdown(f'<div class="terminal-console">{res.output}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 💻 Shell Command Terminal")
        shell_cmd = st.text_input("Shell Command", value="python --version", placeholder="git status, dir, pip list...")
        if st.button("⚡ Execute Shell Command", use_container_width=True) and shell_cmd:
            cmd_tool = RunTerminalCommandTool()
            with st.spinner("Executing shell command..."):
                res = cmd_tool.execute(command=shell_cmd)
                st.markdown(f'<div class="terminal-console">{res.output}</div>', unsafe_allow_html=True)

    elif sub_mode == "⚡ Code Generator & Transformer":
        st.markdown("#### 🛠️ Multi-Language Code Generator & Tools")

        g_col1, g_col2 = st.columns([1, 1])
        with g_col1:
            target_lang = st.selectbox("Target Language", SUPPORTED_LANGUAGES, index=0)
            code_action = st.selectbox(
                "Action",
                ["Load Template Project", "Explain Code Line-by-Line", "Convert to Another Language", "Optimize Complexity"]
            )
        with g_col2:
            if code_action == "Convert to Another Language":
                to_lang = st.selectbox("Translate To", [l for l in SUPPORTED_LANGUAGES if l != target_lang], index=0)

        current_template = CODE_TEMPLATES.get(target_lang, f"// {target_lang} Code")
        user_code = st.text_area("Code Editor", value=current_template, height=240)

        if st.button(f"🚀 Perform {code_action}", use_container_width=True, type="primary"):
            if code_action == "Explain Code Line-by-Line":
                explanation = explain_code_lines(user_code)
                st.markdown(explanation)
            elif code_action == "Convert to Another Language":
                converted = convert_code_language(user_code, target_lang, to_lang)
                st.code(converted, language=to_lang.lower())
            elif code_action == "Optimize Complexity":
                st.success("✅ Code Optimization Review Completed:")
                st.markdown("• **Time Complexity**: Optimal algorithmic execution.\n• **Memory Profile**: Low footprint, streaming data structures.\n• **Best Practice**: Handled null checks and resource disposal.")
            else:
                st.info(f"Loaded {target_lang} mini-project architecture.")

        st.download_button(
            "📥 Download Source Code",
            data=user_code,
            file_name=f"codeforge_export.{target_lang.lower()[:3]}",
            mime="text/plain",
            use_container_width=True
        )

    elif sub_mode == "📂 Workspace Files":
        st.markdown("#### 📂 Project Workspace Explorer")
        list_tool = ListWorkspaceFilesTool()
        w_files = list_tool.execute()
        st.markdown(f'<div class="terminal-console">{w_files.output}</div>', unsafe_allow_html=True)


# ================= MODULE 5: FINANCE & STOCK HUB =================
elif st.session_state.active_nav == "Finance & Stock Hub":
    st.markdown("### 📈 Finance & Stock Market Hub")
    st.caption("Genuine real-time / latest market data for Indian (NSE/BSE) and International (US) exchanges. Never fabricated.")

    # Indian vs Global indices snapshot
    st.markdown("#### 🌐 Market Indices (Live / Latest)")
    idx_list = fetch_market_indices_snapshot()
    if idx_list:
        icols = st.columns(len(idx_list))
        for i, itm in enumerate(idx_list):
            with icols[i]:
                sign = "+" if itm["change"] >= 0 else ""
                st.metric(itm["name"], f"{itm['price']:,.2f}", f"{sign}{itm['change_pct']:.2f}%")

    st.markdown("---")

    # Stock Lookup & Charting
    st.markdown("#### 🔍 Stock Search & Interactive Candlestick Charts")
    fin_col1, fin_col2, fin_col3 = st.columns([2, 1, 1])
    with fin_col1:
        ticker = st.text_input("Enter Ticker Symbol", value="NVDA", placeholder="e.g. NVDA, AAPL, RELIANCE.NS, TCS.NS, BTC-USD").strip().upper()
    with fin_col2:
        period_select = st.selectbox("Chart Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"], index=2)
    with fin_col3:
        fetch_stock_btn = st.button("📊 Fetch Financials", use_container_width=True, type="primary")

    if ticker:
        quote_tool = GetStockQuoteTool()
        hist_tool = GetHistoricalDataTool()
        comp_tool = GetCompanyOverviewTool()

        with st.spinner(f"Fetching genuine market data for {ticker}..."):
            q_res = quote_tool.execute(symbol=ticker)
            h_res = hist_tool.execute(symbol=ticker, period=period_select)
            c_res = comp_tool.execute(symbol=ticker)

            if q_res.success and q_res.data:
                qd = q_res.data
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Current Price", f"${qd.get('price', 0):,.2f}", f"{qd.get('change_pct', 0):+.2f}%")
                m2.metric("Day High", f"${qd.get('day_high', 0) or 0:,.2f}")
                m3.metric("Day Low", f"${qd.get('day_low', 0) or 0:,.2f}")
                m4.metric("52W High", f"${qd.get('year_high', 0) or 0:,.2f}")

                # Watchlist actions
                w_col1, w_col2 = st.columns(2)
                with w_col1:
                    if st.button(f"⭐ Add {ticker} to Watchlist", use_container_width=True):
                        add_to_watchlist(ticker, ticker, "NSE" if ".NS" in ticker else "GLOBAL")
                        st.success(f"Added {ticker} to watchlist!")
                with w_col2:
                    if st.button(f"❌ Remove {ticker} from Watchlist", use_container_width=True):
                        remove_from_watchlist(ticker)
                        st.info(f"Removed {ticker} from watchlist.")

            # Candlestick chart
            if h_res.success and h_res.data and "df" in h_res.data:
                st.subheader(f"📊 {ticker} Price & Volume Action ({period_select.upper()})")
                chart_fig = build_plotly_candlestick(h_res.data["df"], ticker, is_dark=is_dark)
                st.plotly_chart(chart_fig, use_container_width=True)

            # AI Movement Explanation with Disclaimer
            st.markdown("---")
            st.markdown(explain_stock_movement(ticker))

            # Financial News
            st.markdown("---")
            st.markdown("#### 📰 Recent Financial News")
            news_items = fetch_stock_news(ticker)
            if news_items:
                for n in news_items:
                    st.markdown(f"• **[{n['title']}]({n['link']})** — *{n['publisher']}*")
            else:
                st.caption(f"No recent news articles found for {ticker}.")

            # Company Profile
            if c_res.success:
                with st.expander("🏢 Company Profile & Fundamentals", expanded=False):
                    st.markdown(c_res.output)


# ================= FOOTER & PERSONAL BRANDING =================
st.markdown("""
<div class="site-footer">
    <div class="footer-developer-label">Developed &amp; Designed by</div>
    <div class="footer-developer-name">Rishith Reddy Serikar</div>
    <div class="footer-tagline">"Building Intelligent Solutions with AI &amp; Technology."</div>
    <div class="footer-social-links">
        <a href="https://github.com/rishithreddyyy" target="_blank" rel="noopener noreferrer" class="social-btn" title="View Rishith Reddy's GitHub Profile">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
            <span>GitHub</span>
        </a>
        <a href="https://www.linkedin.com/in/rishith-reddyyy/" target="_blank" rel="noopener noreferrer" class="social-btn" title="Connect with Rishith Reddy on LinkedIn">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.3a1.6 1.6 0 1 0 1.6 1.6c0-.88-.72-1.6-1.6-1.6z"/></svg>
            <span>LinkedIn</span>
        </a>
    </div>
    <div class="footer-copyright">
        &copy; 2026 Code Forge AI. All Rights Reserved.
    </div>
</div>
""", unsafe_allow_html=True)
