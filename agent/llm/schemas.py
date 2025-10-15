"""Pydantic schemas for LLM planning with tools DAG"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import date


class Slots(BaseModel):
    """Extracted parameters from user message"""

    # Dates
    check_in: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Check-in date in YYYY-MM-DD format"
    )
    check_out: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Check-out date in YYYY-MM-DD format"
    )
    date_hint: Optional[str] = Field(
        None,
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
        None,
        description="Meal plan preference (breakfast, half board, etc.)"
    )
    bed_preference: Optional[str] = Field(
        None,
        description="Bed configuration preference"
    )

    # Comparison
    compare_criteria: List[str] = Field(
        default_factory=list,
        description="What aspects user wants to compare (price, size, amenities)"
    )

    # Room selection
    selected_room_code: Optional[str] = Field(
        None,
        description="Specific room type code user selected"
    )


class ToolCall(BaseModel):
    """
    Single tool call in execution plan (DAG node).

    Tools can have dependencies via 'needs' field.
    Tools with no dependencies (needs=[]) can run in parallel.
    """

    id: str = Field(
        description="Unique identifier for this tool call (e.g., 'get_rooms', 'check_availability')"
    )

    tool: str = Field(
        description="Tool name from registry (e.g., 'faq.get_rooms_and_pricing', 'pms.get_availability')"
    )

    args: Optional[Dict[str, Union[str, int, float, bool]]] = Field(
        default=None,
        description="Arguments to pass to the tool"
    )

    needs: List[str] = Field(
        default_factory=list,
        description="List of tool call IDs this depends on (for sequential execution). Empty list means no dependencies."
    )


class PlanningResult(BaseModel):
    """
    Complete LLM planning output using OpenAI Structured Outputs.

    This is the output from the LLM that includes:
    - Natural language action description
    - Extracted parameters (slots)
    - DAG of tools to execute
    - Reasoning
    """

    action: str = Field(
        description="Natural language description of what the user wants to do (e.g., 'Search for available rooms', 'Get information about room types')"
    )

    slots: Slots = Field(
        description="Extracted booking parameters and preferences"
    )

    tools: List[ToolCall] = Field(
        description="DAG of tool calls to execute. Tools with needs=[] can run in parallel. Tools with needs=['id1'] must wait for 'id1' to complete."
    )

    reasoning: str = Field(
        description="Brief explanation of why these tools were chosen and how they relate to the user's request (1-2 sentences)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "action": "Search for available rooms for a family",
                    "slots": {
                        "date_hint": "next weekend",
                        "adults": 2,
                        "children": [5, 8]
                    },
                    "tools": [
                        {
                            "id": "get_room_info",
                            "tool": "faq.get_rooms_and_pricing",
                            "args": {},
                            "needs": []
                        },
                        {
                            "id": "check_availability",
                            "tool": "pms.get_availability",
                            "args": {
                                "check_in": "2024-10-18",
                                "check_out": "2024-10-20",
                                "adults": 2,
                                "children": 2,
                                "babies": 0,
                                "rate_code": "ILS"
                            },
                            "needs": []
                        }
                    ],
                    "reasoning": "User wants to search for rooms, so I'm fetching room information from FAQ and checking real-time availability from PMS. Both can run in parallel since they're independent."
                }
            ]
        }
