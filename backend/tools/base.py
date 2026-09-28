"""
backend/tools/base.py
---------------------
Base definitions for the Tool Framework.
"""
from typing import Any, Dict
from abc import ABC, abstractmethod

class Tool(ABC):
    """
    Abstract base class for all tools in the framework.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of the tool."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a brief description of what the tool does."""
        pass
        
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """
        Return a JSON-schema-like dictionary describing the expected arguments.
        """
        pass
        
    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool with the provided structured arguments.
        Must return a meaningful result or raise an exception on failure.
        """
        pass
