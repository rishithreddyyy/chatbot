"""
Tools package exporter.
"""

from tools.base import BaseTool, ToolResult
from tools.search_agent import (
    WebSearchTool,
    FetchWebpageTool,
    SearchDocumentationTool,
    SearchAgent
)
from tools.finance_agent import (
    GetStockQuoteTool,
    GetHistoricalDataTool,
    GetCompanyOverviewTool,
    CompareTickersTool,
    FinanceAgent,
    build_plotly_candlestick
)
from tools.terminal_agent import (
    RunTerminalCommandTool,
    ExecutePythonCodeTool,
    ListWorkspaceFilesTool,
    ReadWorkspaceFileTool,
    WriteWorkspaceFileTool,
    TerminalAgent
)

def get_all_tools() -> list[BaseTool]:
    """Returns a list of all instantiated tools across agents."""
    return [
        # Search Agent Tools
        WebSearchTool(),
        FetchWebpageTool(),
        SearchDocumentationTool(),
        # Finance Agent Tools
        GetStockQuoteTool(),
        GetHistoricalDataTool(),
        GetCompanyOverviewTool(),
        CompareTickersTool(),
        # Terminal Agent Tools
        RunTerminalCommandTool(),
        ExecutePythonCodeTool(),
        ListWorkspaceFilesTool(),
        ReadWorkspaceFileTool(),
        WriteWorkspaceFileTool()
    ]

