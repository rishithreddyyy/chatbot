"""
Terminal Agent and Code Generator tools for Code Forge AI.
Enables command line execution, Python code testing, code conversion,
optimization, line-by-line explanation, and workspace file management.
"""

from typing import List, Dict, Any, Optional
import subprocess
import sys
import os
import time
from pathlib import Path

from tools.base import BaseTool, ToolResult


# Prohibited / Dangerous commands for safety
FORBIDDEN_COMMAND_PATTERNS = [
    "format ",
    "rmdir /s /q c:\\",
    "rmdir /s /q /",
    "remove-item -recurse -force c:\\",
    ":(){ :|:& };:",
    "del /f /s /q c:\\windows",
    "shutdown"
]

def is_safe_command(cmd: str) -> bool:
    """Basic sanity check to prevent destructive system operations."""
    lowered = cmd.lower()
    for pattern in FORBIDDEN_COMMAND_PATTERNS:
        if pattern in lowered:
            return False
    return True


class RunTerminalCommandTool(BaseTool):
    """Executes shell commands in the workspace environment with timeout guardrails."""
    name = "run_terminal_command"
    description = (
        "Executes a shell command (PowerShell on Windows, Bash on Linux/Mac) in the workspace directory. "
        "Returns stdout, stderr, execution time, and exit code."
    )
    agent_name = "Terminal Agent"
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The exact shell command to run (e.g. 'python --version', 'git status', 'pip list')"
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Maximum seconds to wait before terminating the process (default: 30)",
                "default": 30
            }
        },
        "required": ["command"]
    }

    def execute(self, command: str, timeout_seconds: int = 30, **kwargs) -> ToolResult:
        if not is_safe_command(command):
            return ToolResult(
                success=False,
                output=f"Command '{command}' rejected: violates safety constraints.",
                error="Prohibited command",
                agent_name=self.agent_name
            )

        start_time = time.time()
        try:
            is_win = sys.platform.startswith("win")
            shell_cmd = ["powershell", "-Command", command] if is_win else command
            shell_arg = False if is_win else True

            proc = subprocess.run(
                shell_cmd,
                shell=shell_arg,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=os.getcwd()
            )
            elapsed = time.time() - start_time

            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            output_lines = [
                f"$ {command}",
                f"[Exit Code: {proc.returncode} | Time: {elapsed:.2f}s]"
            ]
            if stdout:
                output_lines.append(f"\n--- STDOUT ---\n{stdout}")
            if stderr:
                output_lines.append(f"\n--- STDERR ---\n{stderr}")
            if not stdout and not stderr:
                output_lines.append("(No console output)")

            full_output = "\n".join(output_lines)
            return ToolResult(
                success=(proc.returncode == 0),
                output=full_output,
                data={
                    "command": command,
                    "returncode": proc.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "time": elapsed
                },
                error=stderr if proc.returncode != 0 else None,
                agent_name=self.agent_name
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=f"Command '{command}' timed out after {timeout_seconds} seconds.",
                error="Timeout",
                agent_name=self.agent_name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Error executing command: {str(e)}",
                error=str(e),
                agent_name=self.agent_name
            )


class ExecutePythonCodeTool(BaseTool):
    """Executes arbitrary Python code in an isolated subprocess with timeout and resource limits."""
    name = "execute_python_code"
    description = (
        "Executes arbitrary Python code in an isolated subprocess and returns standard output, "
        "errors, return code, and execution time."
    )
    agent_name = "Terminal Agent"
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python source code to execute"
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Timeout in seconds (default: 20)",
                "default": 20
            }
        },
        "required": ["code"]
    }

    def execute(self, code: str, timeout_seconds: int = 20, **kwargs) -> ToolResult:
        start_time = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=os.getcwd()
            )
            elapsed = time.time() - start_time
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            out_lines = [f"[Python Execution | Exit Code: {proc.returncode} | {elapsed:.2f}s]"]
            if stdout:
                out_lines.append(f"\n--- Output ---\n{stdout}")
            if stderr:
                out_lines.append(f"\n--- Errors / Traceback ---\n{stderr}")
            if not stdout and not stderr:
                out_lines.append("(Executed with no output)")

            return ToolResult(
                success=(proc.returncode == 0),
                output="\n".join(out_lines),
                data={"stdout": stdout, "stderr": stderr, "exit_code": proc.returncode, "elapsed": elapsed},
                error=stderr if proc.returncode != 0 else None,
                agent_name=self.agent_name
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=f"Python execution timed out after {timeout_seconds} seconds.",
                error="Timeout",
                agent_name=self.agent_name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Failed to execute Python code: {str(e)}",
                error=str(e),
                agent_name=self.agent_name
            )


class ListWorkspaceFilesTool(BaseTool):
    """Lists files and folders inside the workspace directory."""
    name = "list_workspace_files"
    description = "Lists files and subdirectories in the current workspace directory."
    agent_name = "Terminal Agent"
    parameters = {
        "type": "object",
        "properties": {
            "subfolder": {
                "type": "string",
                "description": "Optional relative subfolder path (default '.')",
                "default": "."
            }
        }
    }

    def execute(self, subfolder: str = ".", **kwargs) -> ToolResult:
        try:
            target = Path(subfolder).resolve()
            if not target.exists():
                return ToolResult(
                    success=False,
                    output=f"Directory '{subfolder}' does not exist.",
                    error="Not found",
                    agent_name=self.agent_name
                )

            items = []
            for item in sorted(target.iterdir()):
                if item.name.startswith((".", "__pycache__")):
                    continue
                size_str = ""
                if item.is_file():
                    size = item.stat().st_size
                    if size < 1024:
                        size_str = f"({size} B)"
                    else:
                        size_str = f"({size / 1024:.1f} KB)"
                kind = "[DIR] " if item.is_dir() else "[FILE]"
                items.append(f"{kind:<6} {item.name} {size_str}")

            listing = "\n".join(items) if items else "(Empty directory)"
            return ToolResult(
                success=True,
                output=f"Files in {subfolder}:\n{listing}",
                data={"path": str(target), "items": items},
                agent_name=self.agent_name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Error listing files: {str(e)}",
                error=str(e),
                agent_name=self.agent_name
            )


class ReadWorkspaceFileTool(BaseTool):
    """Reads the contents of a source code or config file."""
    name = "read_workspace_file"
    description = "Reads the content of a file in the workspace."
    agent_name = "Terminal Agent"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path of the file to read"
            },
            "max_lines": {
                "type": "integer",
                "description": "Max lines to return (default 200)",
                "default": 200
            }
        },
        "required": ["file_path"]
    }

    def execute(self, file_path: str, max_lines: int = 200, **kwargs) -> ToolResult:
        try:
            p = Path(file_path).resolve()
            if not p.is_file():
                return ToolResult(
                    success=False,
                    output=f"File '{file_path}' does not exist.",
                    error="File not found",
                    agent_name=self.agent_name
                )

            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            truncated = False
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                truncated = True

            numbered_lines = [f"{i+1:3d} | {line}" for i, line in enumerate(lines)]
            content = "".join(numbered_lines)
            if truncated:
                content += f"\n... [Truncated at {max_lines} lines]"

            return ToolResult(
                success=True,
                output=f"File: {file_path}\n\n{content}",
                data={"file_path": file_path, "total_lines": len(lines)},
                agent_name=self.agent_name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Error reading file '{file_path}': {str(e)}",
                error=str(e),
                agent_name=self.agent_name
            )


class WriteWorkspaceFileTool(BaseTool):
    """Creates or overwrites a file in the workspace."""
    name = "write_workspace_file"
    description = "Writes content to a file in the project workspace."
    agent_name = "Terminal Agent"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative file path (e.g., 'src/main.py')"
            },
            "content": {
                "type": "string",
                "description": "Full file content to write"
            }
        },
        "required": ["file_path", "content"]
    }

    def execute(self, file_path: str, content: str, **kwargs) -> ToolResult:
        try:
            p = Path(file_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(
                success=True,
                output=f"Successfully written {len(content)} characters to '{file_path}'.",
                data={"file_path": file_path, "bytes": len(content)},
                agent_name=self.agent_name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Error writing file '{file_path}': {str(e)}",
                error=str(e),
                agent_name=self.agent_name
            )


class TerminalAgent:
    """High-level autonomous terminal agent interface."""
    def __init__(self):
        self.cmd_tool = RunTerminalCommandTool()
        self.py_tool = ExecutePythonCodeTool()
        self.list_tool = ListWorkspaceFilesTool()
        self.read_tool = ReadWorkspaceFileTool()
        self.write_tool = WriteWorkspaceFileTool()

    def get_tools(self) -> List[BaseTool]:
        return [self.cmd_tool, self.py_tool, self.list_tool, self.read_tool, self.write_tool]
