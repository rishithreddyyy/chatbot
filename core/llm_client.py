"""
Unified LLM Client supporting Gemini, OpenAI, Ollama, and High-Speed Smart Engine.
Features automatic intent routing:
- Python code -> Auto-executes in Python runner
- Shell commands -> Auto-executes in Terminal
- Stocks/Crypto -> Auto-queries Finance Agent
- Any other question -> Auto-searches the live web and synthesizes comprehensive answers!
"""

from typing import List, Dict, Any, Optional
import os
import re
import ast
import json
from config import AssistantConfig, SYSTEM_PROMPT
from tools.base import BaseTool, ToolResult
from tools.search_agent import WebSearchTool

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def is_python_code(text: str) -> bool:
    """Detects if user input is an executable Python code snippet."""
    clean = text.strip()

    # Explicit prefix
    if any(clean.lower().startswith(p) for p in ["python:", "run python", "exec python", "py:", "```python"]):
        return True

    # Common Python statement starts
    python_starters = [
        "print(", "import ", "from ", "def ", "class ", "for ", "while ",
        "with ", "try:", "if __name__", "x = ", "y = ", "a = ", "b = "
    ]
    if any(clean.startswith(s) for s in python_starters):
        return True

    # Check if ends with semicolon or has multiple lines and parses as AST
    if not clean.endswith("?") and ("print(" in clean or ";" in clean or "\n" in clean):
        try:
            # Remove trailing semicolons for python AST parser
            test_code = clean.rstrip(";")
            ast.parse(test_code)
            return True
        except Exception:
            pass

    return False


def is_shell_command(text: str) -> bool:
    """Detects if user input is a shell command."""
    clean = text.strip()
    if clean.startswith("$ "):
        return True
    if any(clean.lower().startswith(p) for p in ["run command:", "run:", "terminal:", "exec:", "shell:", "cmd:", "run "]):
        return True

    shell_cmds = [
        "git ", "pip ", "dir", "ls", "cd ", "mkdir ", "echo ", "cat ",
        "powershell", "python -m", "python --version", "npm ", "node ", "python -v"
    ]
    lower = clean.lower()
    return any(lower == sc.strip() or lower.startswith(sc) for sc in shell_cmds)


class LLMClient:
    """Unified client with instant failover and rich autonomous reasoning."""
    def __init__(self, config: AssistantConfig):
        self.config = config

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[BaseTool],
        system_instruction: str = SYSTEM_PROMPT
    ) -> Dict[str, Any]:
        provider = self.config.provider.lower()

        # Check Gemini: only call network if key looks like a valid Google AI Studio key (starts with AIza)
        if provider == "gemini":
            key = (self.config.api_key or "").strip()
            if not key or not key.startswith("AIza"):
                return self._fallback_smart_engine(messages, tools)
            try:
                return self._call_gemini(messages, tools, system_instruction)
            except Exception:
                return self._fallback_smart_engine(messages, tools)

        elif provider == "openai":
            key = (self.config.api_key or "").strip()
            if not key or not key.startswith("sk-"):
                return self._fallback_smart_engine(messages, tools)
            try:
                return self._call_openai(messages, tools, system_instruction)
            except Exception:
                return self._fallback_smart_engine(messages, tools)

        elif provider == "ollama":
            try:
                return self._call_ollama(messages, tools, system_instruction)
            except Exception:
                return self._fallback_smart_engine(messages, tools)

        else:
            return self._fallback_smart_engine(messages, tools)

    def _call_gemini(
        self,
        messages: List[Dict[str, Any]],
        tools: List[BaseTool],
        system_instruction: str
    ) -> Dict[str, Any]:
        if not GEMINI_AVAILABLE:
            return self._fallback_smart_engine(messages, tools)

        client = genai.Client(api_key=self.config.api_key)
        gemini_tools = []
        function_declarations = [t.to_gemini_declaration() for t in tools]
        if function_declarations:
            gemini_tools.append({"function_declarations": function_declarations})

        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append(
                genai_types.Content(
                    role=role,
                    parts=[genai_types.Part.from_text(text=m["content"])]
                )
            )

        config = genai_types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self.config.temperature,
            tools=gemini_tools if gemini_tools else None
        )

        response = client.models.generate_content(
            model=self.config.model_name or "gemini-3.8-flash",
            contents=contents,
            config=config
        )

        tool_calls = []
        text_parts = []
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.text:
                        text_parts.append(part.text)
                    if part.function_call:
                        fc = part.function_call
                        args = dict(fc.args) if fc.args else {}
                        tool_calls.append({
                            "name": fc.name,
                            "args": args,
                            "id": getattr(fc, "id", fc.name)
                        })

        return {
            "text": "".join(text_parts).strip(),
            "tool_calls": tool_calls
        }

    def _call_openai(
        self,
        messages: List[Dict[str, Any]],
        tools: List[BaseTool],
        system_instruction: str
    ) -> Dict[str, Any]:
        if not OPENAI_AVAILABLE:
            return self._fallback_smart_engine(messages, tools)

        client = OpenAI(api_key=self.config.api_key)
        openai_tools = [t.to_openai_tool() for t in tools]

        formatted_msgs = [{"role": "system", "content": system_instruction}]
        for m in messages:
            formatted_msgs.append({"role": m["role"], "content": m["content"]})

        kwargs: Dict[str, Any] = {
            "model": self.config.model_name or "gpt-4o",
            "messages": formatted_msgs,
            "temperature": self.config.temperature,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append({
                    "name": tc.function.name,
                    "args": args,
                    "id": tc.id
                })

        return {"text": msg.content or "", "tool_calls": tool_calls}

    def _call_ollama(
        self,
        messages: List[Dict[str, Any]],
        tools: List[BaseTool],
        system_instruction: str
    ) -> Dict[str, Any]:
        if not OPENAI_AVAILABLE:
            return self._fallback_smart_engine(messages, tools)

        base_url = f"{self.config.ollama_base_url.rstrip('/')}/v1"
        client = OpenAI(base_url=base_url, api_key="ollama")

        openai_tools = [t.to_openai_tool() for t in tools]
        formatted_msgs = [{"role": "system", "content": system_instruction}]
        for m in messages:
            formatted_msgs.append({"role": m["role"], "content": m["content"]})

        kwargs: Dict[str, Any] = {
            "model": self.config.model_name or "deepseek-coder",
            "messages": formatted_msgs,
            "temperature": self.config.temperature,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append({
                    "name": tc.function.name,
                    "args": args,
                    "id": tc.id
                })

        return {"text": msg.content or "", "tool_calls": tool_calls}

    def _fallback_smart_engine(
        self,
        messages: List[Dict[str, Any]],
        tools: List[BaseTool]
    ) -> Dict[str, Any]:
        """
        High-speed autonomous router:
        1. If user typed Python code -> executes in Terminal Agent!
        2. If user typed a shell command -> executes in Terminal Agent!
        3. If user asked about finance/crypto -> executes Finance Agent!
        4. If user asked ANY other question -> searches live web and synthesizes answer!
        """
        last_message = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_message = m["content"].strip()
                break

        user_lower = last_message.lower()
        tool_map = {t.name: t for t in tools}

        # -------------------------------------------------------------
        # 1. PYTHON CODE EXECUTION DETECTION
        # -------------------------------------------------------------
        if is_python_code(last_message) and "execute_python_code" in tool_map:
            clean_code = re.sub(r"^(run python|exec python|execute python|eval python|python|py)\s*:?\s*", "", last_message, flags=re.IGNORECASE).strip()
            clean_code = re.sub(r"^```python\s*|\s*```$", "", clean_code, flags=re.MULTILINE).strip()
            # Remove trailing semicolon if present on standalone print statements
            if clean_code.endswith(";"):
                clean_code = clean_code[:-1].strip()

            return {
                "text": "⚡ **Executing Python code in sandbox runner...**",
                "tool_calls": [{"name": "execute_python_code", "args": {"code": clean_code}, "id": "tc_py_exec"}]
            }

        # -------------------------------------------------------------
        # 2. SHELL / TERMINAL COMMAND DETECTION
        # -------------------------------------------------------------
        if is_shell_command(last_message) and "run_terminal_command" in tool_map:
            cmd = re.sub(r"^(run command|terminal|exec|shell|run|cmd)\s*:?\s*|\$ ", "", last_message, flags=re.IGNORECASE).strip()
            return {
                "text": f"💻 **Running command:** `{cmd}`",
                "tool_calls": [{"name": "run_terminal_command", "args": {"command": cmd}, "id": "tc_term_cmd"}]
            }

        # -------------------------------------------------------------
        # 3. FINANCE AGENT DETECTION
        # -------------------------------------------------------------
        finance_keywords = ["stock", "ticker", "price", "market cap", "quote", "crypto", "bitcoin", "btc", "aapl", "nvda", "tsla", "msft", "googl", "spy", "finance"]
        if any(kw in user_lower for kw in finance_keywords):
            symbols = re.findall(r"\b[A-Z]{2,5}\b", last_message)
            symbols = [s for s in symbols if s not in ["THE", "FOR", "AND", "CAN", "YOU", "WHAT", "HOW", "SHOW", "LIST", "VIEW", "TEST", "RUN", "CODE"]]

            if "compare" in user_lower and len(symbols) >= 2 and "compare_tickers" in tool_map:
                return {
                    "text": f"📊 Comparing market metrics for **{', '.join(symbols)}**...",
                    "tool_calls": [{"name": "compare_tickers", "args": {"symbols": symbols}, "id": "tc_fin_compare"}]
                }
            elif any(w in user_lower for w in ["history", "historical", "trend", "chart", "performance"]) and symbols and "get_historical_data" in tool_map:
                period = "1y" if ("1y" in user_lower or "year" in user_lower) else ("5d" if "5d" in user_lower else "1mo")
                return {
                    "text": f"📈 Fetching historical price data & candlestick chart for **{symbols[0]}**...",
                    "tool_calls": [{"name": "get_historical_data", "args": {"symbol": symbols[0], "period": period}, "id": "tc_fin_hist"}]
                }
            elif symbols and "get_stock_quote" in tool_map:
                return {
                    "text": f"📈 Retrieving real-time market quote for **{symbols[0]}**...",
                    "tool_calls": [{"name": "get_stock_quote", "args": {"symbol": symbols[0]}, "id": "tc_fin_quote"}]
                }
            elif "bitcoin" in user_lower or "btc" in user_lower:
                return {
                    "text": "📈 Retrieving real-time Bitcoin (BTC-USD) quote...",
                    "tool_calls": [{"name": "get_stock_quote", "args": {"symbol": "BTC-USD"}, "id": "tc_fin_btc"}]
                }

        # -------------------------------------------------------------
        # 4. WORKSPACE FILES
        # -------------------------------------------------------------
        if any(w in user_lower for w in ["list files", "workspace files"]):
            if "list_workspace_files" in tool_map:
                return {
                    "text": "📂 Inspecting workspace files...",
                    "tool_calls": [{"name": "list_workspace_files", "args": {}, "id": "tc_term_list"}]
                }

        # -------------------------------------------------------------
        # 5. GENERAL QUESTIONS & WEB SEARCH (ANSWERS ANYTHING FROM THE WEB)
        # -------------------------------------------------------------
        if "web_search" in tool_map:
            clean_search_query = re.sub(r"^(search for|google|look up|search web|find docs on|search|who is|what is|tell me about|how to)\s*:?\s*", "", last_message, flags=re.IGNORECASE).strip()
            if not clean_search_query:
                clean_search_query = last_message

            return {
                "text": f"🔍 Searching web with Google Search Agent for: *\"{last_message}\"*...",
                "tool_calls": [{"name": "web_search", "args": {"query": clean_search_query, "num_results": 5}, "id": "tc_search"}]
            }

        # Fallback
        return {
            "text": f"Received: {last_message}",
            "tool_calls": []
        }
