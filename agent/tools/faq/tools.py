"""FAQ tools for hotel information retrieval"""
from agent.tools.registry import registry
from src.faq.faq_client import FAQClient


@registry.tool(
    name="faq.get_rooms_and_pricing",
    description="Get comprehensive room types and pricing information from hotel FAQ"
)
async def get_rooms_and_pricing() -> str:
    """
    Get detailed room types and pricing information.

    This provides comprehensive static information about:
    - All room types and categories
    - Room configurations and bed types
    - Amenities included in each room
    - Pricing structure and payment methods
    - Special offers and discounts

    Returns:
        str: Natural language formatted room and pricing information
    """
    faq_client = FAQClient()
    info = faq_client.get_rooms_and_pricing_info()

    return f"Room and Pricing Information:\n\n{info}"


@registry.tool(
    name="faq.get_policies_and_procedures",
    description="Get hotel policies, check-in/out times, cancellation policies, etc."
)
async def get_policies_and_procedures() -> str:
    """
    Get hotel policies and procedures information.

    Returns:
        str: Natural language formatted policies and procedures information
    """
    faq_client = FAQClient()
    info = faq_client.get_policies_and_procedures_info()

    return f"Policies and Procedures:\n\n{info}"


@registry.tool(
    name="faq.get_facilities_and_services",
    description="Get information about hotel facilities, services, location, and activities"
)
async def get_facilities_and_services() -> str:
    """
    Get facilities and services information.

    Returns:
        str: Natural language formatted facilities and services information
    """
    faq_client = FAQClient()
    info = faq_client.get_facilities_and_services_info()

    return f"Facilities and Services:\n\n{info}"


@registry.tool(
    name="faq.get_my_stay_guide",
    description="Get practical information for current guests (WiFi, door codes, troubleshooting, etc.)"
)
async def get_my_stay_guide() -> str:
    """
    Get stay guide information for current guests.

    Returns:
        str: Natural language formatted stay guide information
    """
    faq_client = FAQClient()
    info = faq_client.get_my_stay_guide_info()

    return f"Stay Guide for Current Guests:\n\n{info}"
