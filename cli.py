"""
Interactive CLI interface for the Multi-Agent Coding Assistant.
Run directly in your terminal: `python cli.py`
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import AssistantConfig, MODELS_CATALOG
from core.orchestrator import AgentOrchestrator
from tools.search_agent import WebSearchTool
from tools.finance_agent import GetStockQuoteTool, GetHistoricalDataTool
from tools.terminal_agent import RunTerminalCommandTool, ExecutePythonCodeTool


# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    banner = f"""
{CYAN}{BOLD}======================================================================
  🤖 MULTI-AGENT CODING ASSISTANT
  Equipped with:
    🔍 Google Search Agent
    📈 Finance & Market Agent
    💻 Terminal & Code Execution Agent
======================================================================{RESET}
Type your coding request, question, or use commands:
  {YELLOW}/search <query>{RESET}     Direct Google / web search
  {GREEN}/quote <symbol>{RESET}     Quick stock/crypto quote (e.g. /quote NVDA)
  {GREEN}/chart <symbol>{RESET}     Historical stock performance summary
  {BLUE}/run <command>{RESET}      Execute shell command in workspace
  {MAGENTA}/py <code>{RESET}          Execute Python code snippet
  {YELLOW}/tools{RESET}              List active agent tools
  {RED}/clear{RESET}              Clear conversation memory
  {RED}/exit{RESET}               Quit assistant
----------------------------------------------------------------------
"""
    print(banner)


def main():
    config = AssistantConfig()

    # Determine provider from environment or fallback
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        config.provider = "gemini"
        config.model_name = "gemini-2.5-flash"
    elif os.environ.get("OPENAI_API_KEY"):
        config.provider = "openai"
        config.model_name = "gpt-4o"
    else:
        config.provider = "smart_engine"

    orchestrator = AgentOrchestrator(config)
    print_banner()

    print(f"[{BOLD}Active Engine{RESET}]: {GREEN}{config.provider}{RESET} ({config.model_name})")
    print(f"[{BOLD}Tools Enabled{RESET}]: Search, Finance, Terminal\n")

    while True:
        try:
            user_input = input(f"{BOLD}{CYAN}You > {RESET}").strip()
            if not user_input:
                continue

            # Command Handlers
            if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                print(f"\n{YELLOW}Goodbye! Happy coding.{RESET}")
                break

            elif user_input.lower() == "/clear":
                orchestrator.memory.clear()
                print(f"{GREEN}✓ Conversation memory cleared.{RESET}\n")
                continue

            elif user_input.lower() == "/tools":
                tools = orchestrator.get_active_tools()
                print(f"\n{BOLD}Active Registered Tools ({len(tools)}):{RESET}")
                for t in tools:
                    print(f"  • {GREEN}{t.name:<24}{RESET} [{MAGENTA}{t.agent_name}{RESET}]: {t.description[:60]}...")
                print()
                continue

            elif user_input.startswith("/search "):
                q = user_input[8:].strip()
                print(f"{YELLOW}Searching web for '{q}'...{RESET}")
                res = WebSearchTool().execute(query=q)
                print(f"\n{res.output}\n")
                continue

            elif user_input.startswith("/quote "):
                sym = user_input[7:].strip()
                print(f"{GREEN}Querying stock quote for '{sym}'...{RESET}")
                res = GetStockQuoteTool().execute(symbol=sym)
                print(f"\n{res.output}\n")
                continue

            elif user_input.startswith("/chart "):
                sym = user_input[7:].strip()
                print(f"{GREEN}Fetching historical data for '{sym}'...{RESET}")
                res = GetHistoricalDataTool().execute(symbol=sym, period="1mo")
                print(f"\n{res.output}\n")
                continue

            elif user_input.startswith("/run "):
                cmd = user_input[5:].strip()
                print(f"{BLUE}Executing command: {cmd}{RESET}")
                res = RunTerminalCommandTool().execute(command=cmd)
                print(f"\n{res.output}\n")
                continue

            elif user_input.startswith("/py "):
                code = user_input[4:].strip()
                print(f"{MAGENTA}Executing Python code...{RESET}")
                res = ExecutePythonCodeTool().execute(code=code)
                print(f"\n{res.output}\n")
                continue

            # Process through Orchestrator
            print(f"{BOLD}{MAGENTA}Assistant is thinking...{RESET}")
            result = orchestrator.process_message(user_input)

            # Display any tool calls made
            if result.get("traces"):
                for t in result["traces"]:
                    status_color = GREEN if t.success else RED
                    print(f"\n{status_color}⚡ [{t.agent_name}] -> {t.tool_name}{RESET}")
                    print(f"{BOLD}Arguments:{RESET} {t.args}")
                    print(f"{BOLD}Result:{RESET}\n{t.output}")
                    print("-" * 50)

            print(f"\n{BOLD}{GREEN}Assistant >{RESET}\n{result['response']}\n")

        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted. Exiting...{RESET}")
            break
        except Exception as e:
            print(f"{RED}Error: {str(e)}{RESET}\n")


if __name__ == "__main__":
    main()

