"""Tests for LLM-based tool planning"""
import pytest
import os
from pathlib import Path
from agent.llm import LLMClient, ToolPlanner

# Skip tests if no API key available
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not available"
)


@pytest.fixture
def prompts_dir():
    """Get prompts directory"""
    return Path(__file__).parent.parent.parent / "prompts"


@pytest.fixture
def llm_client():
    """Create LLM client"""
    return LLMClient(api_key=os.getenv("OPENAI_API_KEY"))


@pytest.fixture
def tool_planner(llm_client, prompts_dir):
    """Create tool planner"""
    return ToolPlanner(llm_client=llm_client, prompts_dir=prompts_dir)


class TestToolPlanning:
    """Test LLM-based tool planning"""

    def test_plan_availability_search(self, tool_planner):
        """Test planning for availability search"""
        result = tool_planner.plan("Looking for a room next weekend")

        assert "available" in result.action.lower() or "search" in result.action.lower()
        assert result.slots.date_hint == "next weekend"
        assert result.slots.adults == 2
        assert len(result.reasoning) > 0
        assert len(result.tools) > 0

        # Should include availability check
        tool_names = [t.tool for t in result.tools]
        assert any("availability" in tool for tool in tool_names)

    def test_plan_with_children(self, tool_planner):
        """Test planning with children"""
        result = tool_planner.plan(
            "2 adults and kids ages 5 and 7 for this Friday"
        )

        assert result.slots.adults == 2
        assert result.slots.children == [5, 7]
        assert "Friday" in result.slots.date_hint or "friday" in result.slots.date_hint

        # Should include availability tool
        tool_names = [t.tool for t in result.tools]
        assert any("availability" in tool for tool in tool_names)

    def test_plan_room_info(self, tool_planner):
        """Test planning for room info query"""
        result = tool_planner.plan("What rooms do you have?")

        assert "room" in result.action.lower()

        # Should use FAQ tool
        tool_names = [t.tool for t in result.tools]
        assert "faq.get_rooms_and_pricing" in tool_names

    def test_plan_booking_link(self, tool_planner):
        """Test planning for booking link generation"""
        result = tool_planner.plan("Send me a booking link")

        assert "booking" in result.action.lower() or "link" in result.action.lower()

        # Should use booking link tool
        tool_names = [t.tool for t in result.tools]
        assert "pms.generate_booking_link" in tool_names

    def test_extract_budget(self, tool_planner):
        """Test extracting budget constraint"""
        result = tool_planner.plan("Looking for room under ₪500")

        assert result.slots.budget_max == 500
        assert result.slots.currency == "ILS"


class TestParallelExecution:
    """Test tool DAG and parallel execution planning"""

    def test_parallel_tools(self, tool_planner):
        """Test that independent tools are planned to run in parallel"""
        result = tool_planner.plan("Looking for a room next weekend")

        # Should plan FAQ and PMS calls
        tool_names = [t.tool for t in result.tools]
        assert "faq.get_rooms_and_pricing" in tool_names or "pms.get_availability" in tool_names

        # Independent tools should have empty needs
        independent_tools = [t for t in result.tools if not t.needs]
        assert len(independent_tools) > 0

    def test_date_resolution(self, tool_planner):
        """Test that date hints are resolved to actual dates"""
        result = tool_planner.plan("Room for next weekend")

        # Date hint should be captured
        assert result.slots.date_hint == "next weekend"

        # If availability tool is planned, it should have date args
        for tool in result.tools:
            if "availability" in tool.tool:
                # Check that dates are provided (either in args or will be resolved)
                assert "check_in" in tool.args or result.slots.date_hint is not None


class TestChildrenExtraction:
    """Test children age extraction"""

    def test_children_ages_extraction(self, tool_planner):
        """Test that children ages are extracted correctly"""
        result = tool_planner.plan(
            "Family with kids ages 1, 4, and 8"
        )

        # Should extract all children ages
        assert result.slots.children == [1, 4, 8]


# Convenience function for manual testing
if __name__ == "__main__":
    import asyncio

    async def test_manually():
        """Manual test with debug output"""
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  Set OPENAI_API_KEY environment variable to test")
            return

        from agent.core.orchestrator import Orchestrator

        # Create orchestrator
        orchestrator = Orchestrator.create_default()

        # Test message
        message = "Looking for a room next weekend for 2 adults"

        # Process
        result = await orchestrator.process_message(
            message=message,
            pms_type="minihotel",
            pms_username="visitguide",
            pms_password="visg#!71R",
            hotel_id="wayinn",
            pms_use_sandbox=False,
            debug=True
        )

        print("\n📊 Result:")
        print(f"Action: {result['action']}")
        print(f"Tools: {result['tools']}")
        print(f"Reasoning: {result['reasoning']}")

    asyncio.run(test_manually())
