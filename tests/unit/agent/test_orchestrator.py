"""Tests for Orchestrator with real PMS integration"""
import pytest
import os
from agent.core.orchestrator import Orchestrator

# Wayinn hotel credentials (from src/tests/test_minihotel.py)
PMS_TYPE = "minihotel"
PMS_USERNAME = "visitguide"
PMS_PASSWORD = "visg#!71R"
HOTEL_ID = "wayinn"
USE_SANDBOX = False

# Skip tests if no API key available
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not available"
)


@pytest.fixture
def orchestrator():
    """Create orchestrator instance"""
    return Orchestrator.create_default()


@pytest.fixture
def wayinn_credentials():
    """Wayinn hotel credentials"""
    return {
        "pms_type": PMS_TYPE,
        "pms_username": PMS_USERNAME,
        "pms_password": PMS_PASSWORD,
        "hotel_id": HOTEL_ID,
        "pms_use_sandbox": USE_SANDBOX
    }


class TestOrchestrator:
    """Test end-to-end orchestrator with real PMS calls"""

    @pytest.mark.asyncio
    async def test_process_availability_message(self, orchestrator, wayinn_credentials):
        """Test full flow for availability check"""
        print("\n" + "="*70)
        print("TEST: Process Availability Message (Real API)")
        print("="*70)

        message = "Looking for a room next weekend"

        result = await orchestrator.process_message(
            message=message,
            **wayinn_credentials
        )

        # Verify result structure
        assert "action" in result
        assert "tools" in result
        assert "results" in result
        assert len(result["tools"]) > 0

        # Should plan availability tool
        assert any("availability" in tool_id for tool_id in result["tools"])

        # Verify we have results
        assert len(result["results"]) > 0

        print(f"\n✓ Availability check completed")
        print(f"  Action: {result['action']}")
        print(f"  Tools executed: {result['tools']}")
        print(f"  Results: {list(result['results'].keys())}")

    @pytest.mark.asyncio
    async def test_process_room_types_message(self, orchestrator, wayinn_credentials):
        """Test full flow for room types"""
        print("\n" + "="*70)
        print("TEST: Process Room Types Message (FAQ)")
        print("="*70)

        message = "Tell me about your rooms"

        result = await orchestrator.process_message(
            message=message,
            **wayinn_credentials
        )

        # Verify result structure
        assert "action" in result
        assert "room" in result["action"].lower()
        assert "tools" in result
        assert len(result["tools"]) > 0
        assert "results" in result
        assert len(result["results"]) > 0

        print(f"\n✓ Room types retrieved")
        print(f"  Action: {result['action']}")
        print(f"  Tools executed: {result['tools']}")
        print(f"  Results: {list(result['results'].keys())}")

    @pytest.mark.asyncio
    async def test_process_booking_link_message(self, orchestrator, wayinn_credentials):
        """Test full flow for booking link generation"""
        print("\n" + "="*70)
        print("TEST: Process Booking Link Message")
        print("="*70)

        message = "Send me a booking link"

        result = await orchestrator.process_message(
            message=message,
            **wayinn_credentials
        )

        # Verify result structure
        assert "action" in result
        assert "booking" in result["action"].lower() or "link" in result["action"].lower()
        assert "tools" in result
        assert len(result["tools"]) > 0
        assert "results" in result
        assert len(result["results"]) > 0

        print(f"\n✓ Booking link generated")
        print(f"  Action: {result['action']}")
        print(f"  Tools executed: {result['tools']}")
        print(f"  Results: {list(result['results'].keys())}")


class TestMultipleMessages:
    """Test processing multiple messages in sequence"""

    @pytest.mark.asyncio
    async def test_conversation_flow(self, orchestrator, wayinn_credentials):
        """Test a simulated conversation flow"""
        print("\n" + "="*70)
        print("TEST: Conversation Flow (Multiple Messages)")
        print("="*70)

        messages = [
            "Tell me about your rooms",
            "Looking for availability next week",
            "Send me a booking link"
        ]

        for i, message in enumerate(messages, 1):
            print(f"\n--- Message {i}: '{message}' ---")
            result = await orchestrator.process_message(
                message=message,
                **wayinn_credentials
            )
            assert "action" in result
            assert "tools" in result
            assert "results" in result
            print(f"✓ Message {i} processed successfully")
            print(f"  Action: {result['action']}")

        print("\n✓ Full conversation flow completed")


class TestErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_invalid_credentials(self, orchestrator):
        """Test handling of invalid credentials"""
        print("\n" + "="*70)
        print("TEST: Invalid Credentials Error Handling")
        print("="*70)

        with pytest.raises(Exception):
            await orchestrator.process_message(
                message="Looking for a room",
                pms_type="minihotel",
                pms_username="invalid",
                pms_password="invalid",
                hotel_id="invalid",
                pms_use_sandbox=False
            )

        print("✓ Correctly raised exception for invalid credentials")


# Convenience function for running tests manually
if __name__ == "__main__":
    print("Orchestrator Test Suite")
    print("=" * 70)
    print("\nTo run all tests:")
    print("  pytest agent/tests/test_orchestrator.py -v -s")
    print("\nTo run specific test class:")
    print("  pytest agent/tests/test_orchestrator.py::TestIntentDetection -v")
    print("  pytest agent/tests/test_orchestrator.py::TestOrchestrator -v -s")
    print("\nTo run a specific test:")
    print("  pytest agent/tests/test_orchestrator.py::TestOrchestrator::test_process_availability_message -v -s")
    print("\n" + "=" * 70)
