"""FAQ tools for hotel information retrieval"""
from agent.tools.registry import registry
from src.faq.faq_client import FAQClient


@registry.tool(
    name="faq.get_rooms_info",
    description="Get room types, amenities, configurations, and general pricing information"
)
async def get_rooms_info() -> str:
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

    return f"Room Information:\n\n{info}"


@registry.tool(
    name="faq.get_hotel_all_info",
    description="Get complete hotel/resort information: facilities, services, location, activities, policies, check-in/out times, cancellation, WiFi, and guest guide"
)
async def get_hotel_info() -> str:
    """
    Get comprehensive hotel/resort information.

    This combines:
    - Facilities (spa, pool, gym, etc.)
    - Services available
    - Location and surroundings
    - Activities and attractions
    - Policies and procedures (check-in/out, cancellation, payment, rules)
    - WiFi and technical info for guests
    - Stay guide for current guests

    Returns:
        str: Natural language formatted hotel information
    """
    faq_client = FAQClient()

    # Combine all hotel information
    facilities_info = faq_client.get_facilities_and_services_info()
    policies_info = faq_client.get_policies_and_procedures_info()
    stay_guide_info = faq_client.get_my_stay_guide_info()

    return f"Hotel Information:\n\n{facilities_info}\n\nPolicies & Procedures:\n\n{policies_info}\n\nGuest Guide:\n\n{stay_guide_info}"
