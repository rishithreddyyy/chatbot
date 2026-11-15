"""
Memory and conversation context manager.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json

@dataclass
class ChatMessage:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    agent_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_results:
            d["tool_results"] = self.tool_results
        if self.agent_name:
            d["agent_name"] = self.agent_name
        return d

class ConversationMemory:
    """Manages chat messages and tool call context."""
    def __init__(self, system_prompt: Optional[str] = None, max_history: int = 30):
        self.system_prompt = system_prompt
        self.max_history = max_history
        self.messages: List[ChatMessage] = []

    def add_user_message(self, content: str) -> ChatMessage:
        msg = ChatMessage(role="user", content=content)
        self.messages.append(msg)
        self._trim()
        return msg

    def add_assistant_message(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        agent_name: Optional[str] = "Coding Assistant"
    ) -> ChatMessage:
        msg = ChatMessage(
            role="assistant",
            content=content,
            tool_calls=tool_calls,
            agent_name=agent_name
        )
        self.messages.append(msg)
        self._trim()
        return msg

    def add_tool_message(self, content: str, tool_name: str, agent_name: str = "Tool") -> ChatMessage:
        msg = ChatMessage(
            role="tool",
            content=content,
            agent_name=agent_name
        )
        self.messages.append(msg)
        self._trim()
        return msg

    def clear(self):
        self.messages.clear()

    def _trim(self):
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def get_messages(self) -> List[ChatMessage]:
        return list(self.messages)

