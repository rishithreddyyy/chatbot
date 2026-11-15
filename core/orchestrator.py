"""
Multi-Agent Orchestrator.
Coordinates between the Coding Assistant, Google Search Agent, Finance Agent,
and Terminal Agent in an autonomous ReAct loop.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json

from config import AssistantConfig, SYSTEM_PROMPT
from core.memory import ConversationMemory, ChatMessage
from core.llm_client import LLMClient
from tools.base import BaseTool, ToolResult
from tools.search_agent import WebSearchTool, FetchWebpageTool, SearchDocumentationTool
from tools.finance_agent import (
    GetStockQuoteTool,
    GetHistoricalDataTool,
    GetCompanyOverviewTool,
    CompareTickersTool,
    build_plotly_candlestick
)
from tools.terminal_agent import (
    RunTerminalCommandTool,
    ExecutePythonCodeTool,
    ListWorkspaceFilesTool,
    ReadWorkspaceFileTool,
    WriteWorkspaceFileTool
)


@dataclass
class ToolExecutionTrace:
    tool_name: str
    agent_name: str
    args: Dict[str, Any]
    output: str
    success: bool
    data: Optional[Any] = None


class AgentOrchestrator:
    """Coordinates specialized agent tools and LLM reasoning."""
    def __init__(self, config: Optional[AssistantConfig] = None):
        self.config = config or AssistantConfig()
        self.memory = ConversationMemory(system_prompt=SYSTEM_PROMPT)
        self.llm_client = LLMClient(self.config)
        self.tool_registry: Dict[str, BaseTool] = {}
        self._init_tools()

    def _init_tools(self):
        """Initializes and registers tools based on config flags."""
        self.tool_registry.clear()

        # Google Search Agent Tools
        if self.config.enable_search:
            for t in [WebSearchTool(), FetchWebpageTool(), SearchDocumentationTool()]:
                self.tool_registry[t.name] = t

        # Finance Agent Tools
        if self.config.enable_finance:
            for t in [GetStockQuoteTool(), GetHistoricalDataTool(), GetCompanyOverviewTool(), CompareTickersTool()]:
                self.tool_registry[t.name] = t

        # Terminal Agent Tools
        if self.config.enable_terminal:
            for t in [
                RunTerminalCommandTool(),
                ExecutePythonCodeTool(),
                ListWorkspaceFilesTool(),
                ReadWorkspaceFileTool(),
                WriteWorkspaceFileTool()
            ]:
                self.tool_registry[t.name] = t

    def get_active_tools(self) -> List[BaseTool]:
        return list(self.tool_registry.values())

    def update_config(self, **kwargs):
        """Update configuration parameters dynamically."""
        for k, v in kwargs.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)
        self._init_tools()
        self.llm_client = LLMClient(self.config)

    def process_message(self, user_prompt: str, max_iterations: int = 4) -> Dict[str, Any]:
        """
        Executes an agent loop turn for a given user query.
        Returns:
            {
                "response": str,
                "traces": List[ToolExecutionTrace],
                "chart_fig": Optional[Plotly Figure],
                "data": Optional[Any]
            }
        """
        self.memory.add_user_message(user_prompt)
        traces: List[ToolExecutionTrace] = []
        final_response = ""
        chart_fig = None
        extra_data = None

        current_messages = [
            {"role": m.role, "content": m.content}
            for m in self.memory.get_messages()
        ]

        active_tools = self.get_active_tools()

        for step in range(max_iterations):
            # Query LLM with active tools
            llm_result = self.llm_client.generate_with_tools(
                messages=current_messages,
                tools=active_tools,
                system_instruction=SYSTEM_PROMPT
            )

            text_response = llm_result.get("text", "")
            tool_calls = llm_result.get("tool_calls", [])

            # If no tools were called, we have our final synthesized answer
            if not tool_calls:
                final_response = text_response
                self.memory.add_assistant_message(content=final_response)
                break

            # Process each tool call
            for tc in tool_calls:
                tool_name = tc.get("name")
                tool_args = tc.get("args", {})

                if tool_name in self.tool_registry:
                    tool = self.tool_registry[tool_name]
                    result: ToolResult = tool.execute(**tool_args)

                    trace = ToolExecutionTrace(
                        tool_name=tool_name,
                        agent_name=tool.agent_name,
                        args=tool_args,
                        output=result.output,
                        success=result.success,
                        data=result.data
                    )
                    traces.append(trace)

                    # Check for chart or dataframe to visualize
                    if tool_name == "get_historical_data" and result.data and "df" in result.data:
                        try:
                            chart_fig = build_plotly_candlestick(result.data["df"], tool_args.get("symbol", "Asset"))
                            extra_data = result.data
                        except Exception:
                            pass

                    # Format observation for model reasoning
                    obs_content = f"[Observation from {tool.agent_name} ({tool_name})]:\n{result.output}"
                    current_messages.append({"role": "user", "content": obs_content})
                    self.memory.add_tool_message(
                        content=result.output,
                        tool_name=tool_name,
                        agent_name=tool.agent_name
                    )
                else:
                    err_msg = f"Tool '{tool_name}' is not recognized or is disabled."
                    current_messages.append({"role": "user", "content": f"[Error]: {err_msg}"})

            # Check if this was the smart fallback or if key is not active
            key = (self.config.api_key or "").strip()
            is_fallback = (
                self.config.provider in ["smart_engine"]
                or not key
                or (self.config.provider == "gemini" and not key.startswith("AIza"))
                or (self.config.provider == "openai" and not key.startswith("sk-"))
            )
            if is_fallback:
                # Combine reasoning text with tool outputs for clean presentation
                summaries = [t.output for t in traces]
                joined_tools_output = "\n\n".join(summaries)
                final_response = f"{text_response}\n\n{joined_tools_output}".strip()
                self.memory.add_assistant_message(content=final_response)
                break

        if not final_response and traces:
            # Fallback if loop completed without final text
            final_response = "\n\n".join([t.output for t in traces])

        return {
            "response": final_response,
            "traces": traces,
            "chart_fig": chart_fig,
            "data": extra_data
        }

