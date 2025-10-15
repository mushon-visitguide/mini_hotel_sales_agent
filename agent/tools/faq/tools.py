"""FAQ tools for hotel information retrieval"""
from agent.tools.registry import registry
from src.faq.faq_client import FAQClient


@registry.tool(
    name="faq.get_rooms_and_pricing",
    description="Get comprehensive room types and pricing information from hotel FAQ"
)
async def get_rooms_and_pricing() -> dict:
    """
    Get detailed room types and pricing information.

    This provides comprehensive static information about:
    - All room types and categories
    - Room configurations and bed types
    - Amenities included in each room
    - Pricing structure and payment methods
    - Special offers and discounts

    Returns:
        dict: Room and pricing information
    """
    faq_client = FAQClient()
    info = faq_client.get_rooms_and_pricing_info()

    return {
        "info": info,
        "source": "FAQ - Rooms & Pricing"
    }


@registry.tool(
    name="faq.get_policies_and_procedures",
    description="Get hotel policies, check-in/out times, cancellation policies, etc."
)
async def get_policies_and_procedures() -> dict:
    """
    Get hotel policies and procedures information.

    Returns:
        dict: Policies and procedures information
    """
    faq_client = FAQClient()
    info = faq_client.get_policies_and_procedures_info()

    return {
        "info": info,
        "source": "FAQ - Policies & Procedures"
    }


@registry.tool(
    name="faq.get_facilities_and_services",
    description="Get information about hotel facilities, services, location, and activities"
)
async def get_facilities_and_services() -> dict:
    """
    Get facilities and services information.

    Returns:
        dict: Facilities and services information
    """
    faq_client = FAQClient()
    info = faq_client.get_facilities_and_services_info()

    return {
        "info": info,
        "source": "FAQ - Facilities & Services"
    }


@registry.tool(
    name="faq.get_my_stay_guide",
    description="Get practical information for current guests (WiFi, door codes, troubleshooting, etc.)"
)
async def get_my_stay_guide() -> dict:
    """
    Get stay guide information for current guests.

    Returns:
        dict: Stay guide information
    """
    faq_client = FAQClient()
    info = faq_client.get_my_stay_guide_info()

    return {
        "info": info,
        "source": "FAQ - My Stay Guide"
    }
