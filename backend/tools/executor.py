"""
backend/tools/executor.py
-------------------------
Tool Executor for running tools safely and returning structured results.
"""
import logging
from typing import Any, Dict
from backend.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a tool by name with the given arguments.
        Returns a structured dictionary indicating success or failure.
        """
        if not self.registry.has_tool(tool_name):
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Unknown tool: {tool_name}"
            }
            
        tool = self.registry.get(tool_name)
        
        try:
            # We pass the arguments as kwargs to the tool
            result = tool.execute(**arguments)
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        except TypeError as e:
            logger.error(f"Invalid arguments for tool '{tool_name}': {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Invalid arguments: {e}"
            }
        except Exception as e:
            logger.exception(f"Tool execution failed for '{tool_name}': {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
