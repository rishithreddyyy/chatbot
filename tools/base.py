"""
Base tool interfaces and definitions for Multi-Agent tools.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
import json

@dataclass
class ToolResult:
    """Standardized result returned by all tools."""
    success: bool
    output: str
    data: Optional[Any] = None
    error: Optional[str] = None
    agent_name: str = "Assistant"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "agent_name": self.agent_name
        }

    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error ({self.agent_name}): {self.error or self.output}"

class BaseTool:
    """Base class that all agent tools inherit from."""
    name: str = "base_tool"
    description: str = "Base tool description"
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": []
    }
    agent_name: str = "General"

    def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError("Subclasses must implement execute()")

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI compatible tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def to_gemini_declaration(self) -> Dict[str, Any]:
        """Convert to Gemini FunctionDeclaration dictionary schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

