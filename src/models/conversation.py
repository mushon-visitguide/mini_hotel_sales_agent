"""Conversation models - tracks messages and tool executions across conversation"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """
    Represents a single message in the conversation.

    This is a lightweight representation used for context window management.
    Full message content is stored here, but can be summarized later.
    """
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Optional metadata
    turn_number: Optional[int] = None  # Sequential turn number in conversation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "turn_number": self.turn_number
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create Message from dictionary"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            turn_number=data.get("turn_number")
        )

    def __str__(self) -> str:
        """Human-readable representation"""
        return f"[{self.role.value}] {self.content[:50]}..."


@dataclass
class ToolExecutionSummary:
    """
    Compressed summary of a tool execution.

    Instead of storing full tool results (which can be very large),
    we store a compressed summary that captures the key information.
    This allows us to reference previous tool calls without bloating context.
    """
    turn_number: int
    tool_name: str
    tool_id: str  # e.g., "resolve_date_1", "get_availability_1"

    # Input parameters (store original, not compressed)
    inputs: Dict[str, Any]

    # Compressed output summary
    output_summary: str  # Human-readable summary of results
    output_metadata: Optional[Dict[str, Any]] = None  # Key metadata (e.g., room count, price range)

    # Execution metadata
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "turn_number": self.turn_number,
            "tool_name": self.tool_name,
            "tool_id": self.tool_id,
            "inputs": self.inputs,
            "output_summary": self.output_summary,
            "output_metadata": self.output_metadata,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolExecutionSummary":
        """Create ToolExecutionSummary from dictionary"""
        return cls(
            turn_number=data["turn_number"],
            tool_name=data["tool_name"],
            tool_id=data["tool_id"],
            inputs=data["inputs"],
            output_summary=data["output_summary"],
            output_metadata=data.get("output_metadata"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            success=data.get("success", True),
            error_message=data.get("error_message")
        )

    def __str__(self) -> str:
        """Human-readable representation"""
        status = "✓" if self.success else "✗"
        return f"[{status}] {self.tool_id}: {self.output_summary[:60]}..."


@dataclass
class ConversationMetadata:
    """
    Metadata about the conversation session.

    Tracks session identification, timing, and conversation statistics
    for context management and summarization decisions.
    """
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Conversation statistics
    total_turns: int = 0
    total_messages: int = 0
    total_tool_executions: int = 0

    # Summarization tracking
    last_summarized_turn: int = 0  # Last turn that was summarized
    summary_version: int = 0  # Increments with each summarization

    # Hotel/PMS context
    hotel_id: Optional[str] = None
    pms_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "total_turns": self.total_turns,
            "total_messages": self.total_messages,
            "total_tool_executions": self.total_tool_executions,
            "last_summarized_turn": self.last_summarized_turn,
            "summary_version": self.summary_version,
            "hotel_id": self.hotel_id,
            "pms_type": self.pms_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMetadata":
        """Create ConversationMetadata from dictionary"""
        return cls(
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            total_turns=data.get("total_turns", 0),
            total_messages=data.get("total_messages", 0),
            total_tool_executions=data.get("total_tool_executions", 0),
            last_summarized_turn=data.get("last_summarized_turn", 0),
            summary_version=data.get("summary_version", 0),
            hotel_id=data.get("hotel_id"),
            pms_type=data.get("pms_type")
        )

    def increment_turn(self) -> None:
        """Increment turn counter and update timestamp"""
        self.total_turns += 1
        self.last_updated = datetime.now()

    def increment_messages(self, count: int = 1) -> None:
        """Increment message counter"""
        self.total_messages += count
        self.last_updated = datetime.now()

    def increment_tool_executions(self, count: int = 1) -> None:
        """Increment tool execution counter"""
        self.total_tool_executions += count
        self.last_updated = datetime.now()

    def mark_summarized(self, turn_number: int) -> None:
        """Mark that conversation was summarized up to this turn"""
        self.last_summarized_turn = turn_number
        self.summary_version += 1
        self.last_updated = datetime.now()

    def __str__(self) -> str:
        """Human-readable representation"""
        return (
            f"Session {self.session_id}: "
            f"{self.total_turns} turns, "
            f"{self.total_messages} messages, "
            f"{self.total_tool_executions} tools"
        )
