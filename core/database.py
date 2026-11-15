"""
Database layer for Code Forge AI.
Local SQLite database (codeforge.db) providing persistent storage for:
- User Preferences & Theme
- Chat History & Sessions
- Web Search History
- Stock Watchlist
- Saved Code Snippets
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "codeforge.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if not already present."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. User Preferences
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # 2. Chat Sessions & Messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        traces TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Search History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        results_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. Stock Watchlist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_watchlist (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        market TEXT DEFAULT 'GLOBAL',
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 5. Saved Code Snippets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_snippets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        language TEXT NOT NULL,
        code TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Seed initial default watchlist if empty
    cursor.execute("SELECT COUNT(*) FROM stock_watchlist")
    if cursor.fetchone()[0] == 0:
        default_stocks = [
            ("NVDA", "NVIDIA Corp.", "GLOBAL"),
            ("AAPL", "Apple Inc.", "GLOBAL"),
            ("MSFT", "Microsoft Corp.", "GLOBAL"),
            ("RELIANCE.NS", "Reliance Industries", "NSE"),
            ("TCS.NS", "Tata Consultancy Services", "NSE"),
            ("^NSEI", "NIFTY 50", "INDEX"),
            ("^GSPC", "S&P 500", "INDEX")
        ]
        cursor.executemany("INSERT INTO stock_watchlist (symbol, name, market) VALUES (?, ?, ?)", default_stocks)

    # Seed default settings
    cursor.execute("INSERT OR IGNORE INTO user_settings (key, value) VALUES ('theme', 'dark')")
    cursor.execute("INSERT OR IGNORE INTO user_settings (key, value) VALUES ('username', 'Developer')")
    cursor.execute("INSERT OR IGNORE INTO user_settings (key, value) VALUES ('default_provider', 'gemini')")

    conn.commit()
    conn.close()

# ----------------- CHAT PERSISTENCE -----------------
def save_chat_message(session_id: str, role: str, content: str, traces: Optional[List[Dict[str, Any]]] = None):
    conn = get_connection()
    traces_json = json.dumps(traces) if traces else None
    conn.execute(
        "INSERT INTO chat_messages (session_id, role, content, traces) VALUES (?, ?, ?, ?)",
        (session_id, role, content, traces_json)
    )
    conn.commit()
    conn.close()

def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.execute(
        "SELECT role, content, traces, created_at FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        traces = json.loads(r["traces"]) if r["traces"] else []
        result.append({
            "role": r["role"],
            "content": r["content"],
            "traces": traces,
            "created_at": r["created_at"]
        })
    return result

def clear_session_chat(session_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

# ----------------- SEARCH HISTORY -----------------
def record_search(query: str, category: str = "general", results_count: int = 0):
    conn = get_connection()
    conn.execute(
        "INSERT INTO search_history (query, category, results_count) VALUES (?, ?, ?)",
        (query, category, results_count)
    )
    conn.commit()
    conn.close()

def get_recent_searches(limit: int = 8) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, query, category, created_at FROM search_history ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ----------------- WATCHLIST PERSISTENCE -----------------
def get_watchlist() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.execute("SELECT symbol, name, market, added_at FROM stock_watchlist ORDER BY added_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_to_watchlist(symbol: str, name: str = "", market: str = "GLOBAL") -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO stock_watchlist (symbol, name, market) VALUES (?, ?, ?)",
            (symbol.strip().upper(), name or symbol, market)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def remove_from_watchlist(symbol: str) -> bool:
    try:
        conn = get_connection()
        conn.execute("DELETE FROM stock_watchlist WHERE symbol = ?", (symbol.strip().upper(),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# ----------------- SAVED SNIPPETS -----------------
def save_snippet(title: str, language: str, code: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO saved_snippets (title, language, code) VALUES (?, ?, ?)",
        (title, language, code)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_saved_snippets(limit: int = 15) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, title, language, code, created_at FROM saved_snippets ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_snippet(snippet_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM saved_snippets WHERE id = ?", (snippet_id,))
    conn.commit()
    conn.close()

# ----------------- USER PREFERENCES -----------------
def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    cursor = conn.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# Initialize on import
init_db()
