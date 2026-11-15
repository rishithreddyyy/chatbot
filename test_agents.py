"""
Comprehensive test script for Multi-Agent Coding Assistant tools & orchestrator.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import AssistantConfig
from tools.search_agent import WebSearchTool, FetchWebpageTool, SearchDocumentationTool
from tools.finance_agent import GetStockQuoteTool, GetHistoricalDataTool, GetCompanyOverviewTool, CompareTickersTool
from tools.terminal_agent import RunTerminalCommandTool, ExecutePythonCodeTool, ListWorkspaceFilesTool, is_safe_command
from core.orchestrator import AgentOrchestrator


class TestTerminalAgent(unittest.TestCase):
    def setUp(self):
        self.cmd_tool = RunTerminalCommandTool()
        self.py_tool = ExecutePythonCodeTool()
        self.list_tool = ListWorkspaceFilesTool()

    def test_safe_command_filter(self):
        self.assertTrue(is_safe_command("python --version"))
        self.assertTrue(is_safe_command("git status"))
        self.assertFalse(is_safe_command("rmdir /s /q C:\\"))
        self.assertFalse(is_safe_command("format c:"))

    def test_terminal_command_execution(self):
        res = self.cmd_tool.execute(command="python --version")
        self.assertTrue(res.success)
        self.assertIn("Python", res.output)

    def test_python_code_execution(self):
        code = "a = 21\nb = 2\nprint('Computed Result:', a * b)"
        res = self.py_tool.execute(code=code)
        self.assertTrue(res.success)
        self.assertIn("Computed Result: 42", res.output)

    def test_list_workspace_files(self):
        res = self.list_tool.execute(subfolder=".")
        self.assertTrue(res.success)
        self.assertIn("app.py", res.output)


class TestSearchAgent(unittest.TestCase):
    def setUp(self):
        self.search_tool = WebSearchTool()
        self.doc_tool = SearchDocumentationTool()

    def test_web_search_tool_structure(self):
        self.assertEqual(self.search_tool.name, "web_search")
        self.assertEqual(self.search_tool.agent_name, "Google Search Agent")
        schema = self.search_tool.parameters
        self.assertIn("query", schema["properties"])

    def test_search_doc_tool(self):
        self.assertEqual(self.doc_tool.name, "search_documentation")
        schema = self.doc_tool.parameters
        self.assertIn("library", schema["properties"])


class TestFinanceAgent(unittest.TestCase):
    def setUp(self):
        self.quote_tool = GetStockQuoteTool()
        self.hist_tool = GetHistoricalDataTool()
        self.compare_tool = CompareTickersTool()

    def test_tools_schema(self):
        self.assertEqual(self.quote_tool.name, "get_stock_quote")
        self.assertEqual(self.quote_tool.agent_name, "Finance Agent")
        self.assertIn("symbol", self.quote_tool.parameters["properties"])
        self.assertIn("symbols", self.compare_tool.parameters["properties"])

    def test_ticker_quote_offline_resilience(self):
        # Test quote execution structure
        res = self.quote_tool.execute(symbol="AAPL")
        self.assertIsInstance(res.success, bool)


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        config = AssistantConfig(provider="smart_engine")
        self.orchestrator = AgentOrchestrator(config)

    def test_orchestrator_initialization(self):
        tools = self.orchestrator.get_active_tools()
        tool_names = [t.name for t in tools]
        self.assertIn("web_search", tool_names)
        self.assertIn("get_stock_quote", tool_names)
        self.assertIn("run_terminal_command", tool_names)
        self.assertIn("execute_python_code", tool_names)

    def test_smart_terminal_dispatch(self):
        res = self.orchestrator.process_message("run: python --version")
        self.assertIn("Python", res["response"])
        self.assertTrue(len(res["traces"]) > 0)
        self.assertEqual(res["traces"][0].tool_name, "run_terminal_command")

    def test_smart_code_exec_dispatch(self):
        res = self.orchestrator.process_message("run python: print('Test Passed!')")
        self.assertIn("Test Passed!", res["response"])
        self.assertTrue(len(res["traces"]) > 0)
        self.assertEqual(res["traces"][0].tool_name, "execute_python_code")


if __name__ == "__main__":
    unittest.main(verbosity=2)

