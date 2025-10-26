"""Pydantic schemas for LLM agentic loop planning"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import date


class Slots(BaseModel):
    """Extracted parameters from user message"""

    # Dates
    check_in: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Check-in date in YYYY-MM-DD format"
    )
    check_out: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Check-out date in YYYY-MM-DD format"
    )
    date_hint: Optional[str] = Field(
        default=None,
        description="Fuzzy date reference like 'next weekend', 'this Friday'"
    )

    # Party composition
    adults: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Number of adult guests"
    )
    children: List[int] = Field(
        default_factory=list,
        description="Ages of children (0-17 years old)"
    )

    # Preferences
    board_preference: Optional[str] = Field(
        default=None,
        description="Meal plan preference (breakfast, half board, etc.)"
    )
    bed_preference: Optional[str] = Field(
        default=None,
        description="Bed configuration preference"
    )

    # Comparison
    compare_criteria: List[str] = Field(
        default_factory=list,
        description="What aspects user wants to compare (price, size, amenities)"
    )

    # Room selection
    selected_room_code: Optional[str] = Field(
        default=None,
        description="Specific room type code user selected"
    )

    # Guest information
    guest_name: Optional[str] = Field(
        default=None,
        description="Guest's full name for booking"
    )
    guest_phone: Optional[str] = Field(
        default=None,
        description="Guest's phone number"
    )
    guest_email: Optional[str] = Field(
        default=None,
        description="Guest's email address"
    )


class ToolCall(BaseModel):
    """
    Single tool call with optional dependencies.

    Tools are organized into waves based on 'needs' dependencies.
    Tools in the same wave run in parallel.
    """

    id: str = Field(
        description="Unique identifier for this tool call (e.g., 'get_rooms', 'check_availability')"
    )

    tool: str = Field(
        description="Tool name from registry (e.g., 'faq.get_rooms_and_pricing', 'pms.get_availability')"
    )

    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the tool"
    )

    needs: List[str] = Field(
        default_factory=list,
        description="List of tool IDs this tool depends on. Leave empty if no dependencies."
    )


class PlanningResult(BaseModel):
    """
    Complete LLM planning output using OpenAI Structured Outputs.

    SINGLE-PLANNING MODE:
    - LLM plans ALL tools upfront in one shot
    - Tools are organized into waves based on dependencies
    - Each tool can depend on previous tools via 'needs' field
    """

    action: str = Field(
        description="Natural language description of what you're helping the user with (e.g., 'Checking availability for Hanukkah', 'Finding room information')"
    )

    slots: Slots = Field(
        description="Extracted booking parameters and preferences"
    )

    tools: List[ToolCall] = Field(
        description="ALL tools to execute for this request. Use 'needs' field to specify dependencies between tools."
    )

    reasoning: str = Field(
        description="Brief explanation of your plan (1-2 sentences)"
    )

