"""Tool Registry with decorator-based registration"""
from typing import Callable, Any, Dict, get_type_hints
from pydantic import BaseModel, create_model, ValidationError
from functools import wraps
import inspect
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for tools with automatic schema generation.

    Tools are registered using the @tool decorator which:
    - Auto-generates Pydantic schema from function signature
    - Validates inputs
    - Redacts sensitive fields in logs
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, type[BaseModel]] = {}
        self._redact_fields: Dict[str, set] = {}
        self._descriptions: Dict[str, str] = {}

    def tool(
        self,
        name: str = None,
        description: str = None,
        redact: list[str] = None
    ):
        """
        Decorator to register a function as a tool.

        Args:
            name: Tool name (defaults to module.function_name)
            description: Human-readable description
            redact: List of parameter names to redact in logs

        Example:
            @registry.tool(
                name="pms.get_availability",
                description="Get room availability",
                redact=["pms_password"]
            )
            async def get_availability(hotel_id: str, pms_password: str):
                ...
        """
        def decorator(func: Callable) -> Callable:
            # Determine tool name
            tool_name = name or f"{func.__module__}.{func.__name__}"

            # Create Pydantic schema from function signature
            schema = self._create_schema_from_function(func)

            # Store metadata
            self._tools[tool_name] = func
            self._schemas[tool_name] = schema
            self._redact_fields[tool_name] = set(redact or [])
            self._descriptions[tool_name] = description or func.__doc__ or ""

            logger.info(f"Registered tool: {tool_name}")

            # Return wrapped function (for direct calls if needed)
            @wraps(func)
            async def wrapper(**kwargs):
                return await self.call(tool_name, **kwargs)

            return wrapper

        return decorator

    def _create_schema_from_function(self, func: Callable) -> type[BaseModel]:
        """
        Auto-generate Pydantic model from function type hints.

        Args:
            func: Function to analyze

        Returns:
            Pydantic model class
        """
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        fields = {}
        for param_name, param in sig.parameters.items():
            if param_name == "return":
                continue

            # Get type hint
            param_type = type_hints.get(param_name, Any)

            # Get default value
            if param.default == inspect.Parameter.empty:
                param_default = ...  # Required field
            else:
                param_default = param.default

            fields[param_name] = (param_type, param_default)

        # Create Pydantic model dynamically
        model_name = f"{func.__name__}_Input"
        return create_model(model_name, **fields)

    async def call(self, tool_name: str, **kwargs) -> Any:
        """
        Call a registered tool with validation.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool

        Returns:
            Tool result

        Raises:
            ValueError: If tool not found or validation fails
        """
        if tool_name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise ValueError(f"Unknown tool: {tool_name}. Available: {available}")

        # Get tool components
        func = self._tools[tool_name]
        schema = self._schemas[tool_name]
        redact_fields = self._redact_fields[tool_name]

        # Validate input
        try:
            validated = schema(**kwargs)
        except ValidationError as e:
            logger.error(f"Validation error for {tool_name}: {e}")
            raise ValueError(f"Invalid arguments for {tool_name}: {e}")

        # Log call with redacted sensitive fields
        log_kwargs = {
            k: "***REDACTED***" if k in redact_fields else v
            for k, v in kwargs.items()
        }
        logger.info(f"Calling tool: {tool_name}")
        logger.debug(f"  Args: {log_kwargs}")

        # Call the tool
        try:
            result = await func(**validated.dict())
            logger.info(f"Tool {tool_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            raise

    def list_tools(self) -> list[str]:
        """List all registered tool names"""
        return list(self._tools.keys())

    def get_tool_info(self, tool_name: str) -> dict:
        """Get information about a tool"""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        schema = self._schemas[tool_name]
        return {
            "name": tool_name,
            "description": self._descriptions[tool_name],
            "parameters": schema.schema()["properties"],
            "required": schema.schema().get("required", [])
        }


# Global registry instance
registry = ToolRegistry()
