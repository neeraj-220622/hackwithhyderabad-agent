"""
backend/tools/registry.py
-------------------------
Tool Registry for managing available tools.
"""
from typing import Dict, List, Any
from backend.tools.base import Tool

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        
    def register(self, tool: Tool) -> None:
        if not isinstance(tool, Tool):
            raise TypeError("Only Tool instances can be registered.")
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered.")
        self._tools[tool.name] = tool
        
    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry.")
        return self._tools[name]
        
    def has_tool(self, name: str) -> bool:
        return name in self._tools
        
    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self._tools.values()
        ]
