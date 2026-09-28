"""
backend/tools/builtins.py
-------------------------
Built-in demonstration tools for the framework.
"""
from typing import Any, Dict
from backend.tools.base import Tool

class CalculatorTool(Tool):
    @property
    def name(self) -> str:
        return "calculator"
        
    @property
    def description(self) -> str:
        return "A simple calculator for basic arithmetic operations."
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The mathematical operation to perform."
                },
                "a": {
                    "type": "number",
                    "description": "The first operand."
                },
                "b": {
                    "type": "number",
                    "description": "The second operand."
                }
            },
            "required": ["operation", "a", "b"]
        }
        
    def execute(self, operation: str, a: float, b: float, **kwargs: Any) -> float:
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero is not allowed.")
            return a / b
        else:
            raise ValueError(f"Unsupported operation: {operation}")
