"""
Configuration settings for the Multi-Agent Coding Assistant.
Supports Gemini, OpenAI, Ollama, and built-in local fallback modes.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# Root workspace directory
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR

# Load .env file automatically if present
env_file = BASE_DIR / ".env"
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass

# Available Models
MODELS_CATALOG = {
    "gemini": [
        "gemini-3.8-flash",
        "gemini-3.8-pro",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "o3-mini"
    ],
    "ollama": [
        "deepseek-coder",
        "qwen2.5-coder",
        "llama3.2",
        "mistral"
    ],
    "smart_engine": [
        "smart-autonomous-engine"
    ]
}

SYSTEM_PROMPT = """You are an expert AI Coding Assistant and Senior Software Architect.
You possess deep expertise in software engineering, system architecture, debugging, data science, and quantitative finance.

You have access to specialized autonomous agent tools:
1. Google Search Agent: For querying live web documentation, finding solutions to technical errors, library APIs, and latest news.
2. Finance Agent: For fetching live stock/crypto market data, historical prices, company financials, and generating interactive financial charts.
3. Terminal Agent: For executing shell commands, running Python code scripts, exploring workspace files, reading/writing source code, and validating builds.

Guidelines:
- When writing code, provide clean, idiomatic, fully functional, and well-commented code.
- When a user asks about live external information or technical docs, use the Google Search Agent.
- When a user asks about stocks, market trends, or financial calculations, use the Finance Agent.
- When testing code, validating packages, running scripts, or inspecting the workspace, use the Terminal Agent.
- Explain your reasoning clearly, summarize tool outputs, and recommend best practices.
"""

@dataclass
class AssistantConfig:
    provider: str = "gemini"  # "gemini", "openai", "ollama", "smart_engine"
    model_name: str = "gemini-3.8-flash"
    api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    temperature: float = 0.2
    max_tokens: int = 4096
    workspace_path: Path = WORKSPACE_DIR
    enable_search: bool = True
    enable_finance: bool = True
    enable_terminal: bool = True
    terminal_timeout: int = 30
    auto_execute_code: bool = False

    def __post_init__(self):
        # Auto-detect API key from environment if not explicitly set
        if not self.api_key:
            if self.provider == "gemini":
                self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            elif self.provider == "openai":
                self.api_key = os.environ.get("OPENAI_API_KEY")

