"""
Tool output compression utilities.

Compresses large tool outputs into compact summaries for efficient context usage.
Different tools have different compression strategies optimized for their output types.
"""
from typing import Any, Dict, Optional, Tuple
from datetime import date


def compress_tool_output(tool_name: str, tool_result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Compress tool output into a summary and metadata.

    Args:
        tool_name: Name of the tool that was executed
        tool_result: The full tool result (can be dict, list, str, etc.)

    Returns:
        Tuple of (summary_text, metadata_dict)
        - summary_text: Human-readable summary of the result
        - metadata_dict: Key structured data for reference (optional)
    """
    if isinstance(tool_result, dict) and 'error' in tool_result:
        return f"Error: {tool_result['error']}", {"error": True}

    # Route to specific compressor based on tool type
    if tool_name.startswith("faq."):
        return _compress_faq_output(tool_name, tool_result)
    elif tool_name.startswith("calendar."):
        return _compress_calendar_output(tool_name, tool_result)
    elif tool_name.startswith("pms."):
        return _compress_pms_output(tool_name, tool_result)
    else:
        # Generic compression for unknown tools
        return _compress_generic(tool_result)


def _compress_faq_output(tool_name: str, result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Compress FAQ tool outputs.

    FAQ tools return text content. We compress by:
    1. Limiting to first ~200 characters
    2. Extracting key facts if structured
    """
    if isinstance(result, str):
        # Simple text response - truncate with ellipsis
        max_length = 200
        if len(result) > max_length:
            summary = result[:max_length].rsplit(' ', 1)[0] + "..."
        else:
            summary = result

        # Extract key metadata based on tool type
        metadata = {"type": "faq", "tool": tool_name}

        if "rooms" in tool_name:
            metadata["content_type"] = "rooms_info"
        elif "hotel" in tool_name:
            metadata["content_type"] = "hotel_info"
        elif "policies" in tool_name:
            metadata["content_type"] = "policies"

        return summary, metadata

    elif isinstance(result, dict):
        # Structured FAQ response
        summary_parts = []
        if "rooms" in result:
            summary_parts.append(f"{len(result['rooms'])} room types available")
        if "facilities" in result:
            summary_parts.append(f"Facilities: {', '.join(result['facilities'][:3])}")

        summary = "; ".join(summary_parts) if summary_parts else str(result)[:200]
        return summary, {"type": "faq", "data_keys": list(result.keys())}

    return str(result)[:200], {"type": "faq"}


def _compress_calendar_output(tool_name: str, result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Compress calendar tool outputs.

    Calendar tools return date information - we extract the key dates.
    """
    if isinstance(result, str):
        # Extract dates from the result string if possible
        # Result typically like: "Monday is October 20th, 2025"
        summary = result
        metadata = {"type": "calendar", "tool": tool_name}

        # Try to extract dates for structured reference
        # This is a simple heuristic - in production might use regex
        if "resolve_date" in tool_name:
            metadata["resolved"] = True

        return summary, metadata

    elif isinstance(result, dict):
        # Structured date response
        summary_parts = []
        if "check_in" in result:
            summary_parts.append(f"Check-in: {result['check_in']}")
        if "check_out" in result:
            summary_parts.append(f"Check-out: {result['check_out']}")
        if "nights" in result:
            summary_parts.append(f"{result['nights']} nights")

        summary = ", ".join(summary_parts)
        return summary, {"type": "calendar", "dates": result}

    return str(result), {"type": "calendar"}


def _compress_pms_output(tool_name: str, result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Compress PMS tool outputs.

    PMS tools return availability data (large) or booking links (small).
    For availability, we compress to key stats + top rooms.
    """
    if "availability" in tool_name:
        return _compress_availability(result)
    elif "booking_link" in tool_name:
        return _compress_booking_link(result)
    else:
        return _compress_generic(result)


def _compress_availability(result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Compress availability results to key statistics.

    Full availability can be 10KB+ with all room details.
    We compress to:
    - Total available rooms
    - Price range
    - Top 3-5 room options with prices
    """
    if not isinstance(result, dict):
        return str(result)[:200], {"type": "availability"}

    room_types = result.get("room_types", [])
    available_rooms = [r for r in room_types if r.get("available", 0) > 0]

    # Extract key statistics
    total_available = len(available_rooms)

    # Get price range
    all_prices = []
    for room in available_rooms:
        for price_option in room.get("prices", []):
            if price_option.get("price"):
                all_prices.append(price_option["price"])

    min_price = min(all_prices) if all_prices else 0
    max_price = max(all_prices) if all_prices else 0
    currency = result.get("currency", "ILS")

    # Get top rooms (by availability or price)
    top_rooms = available_rooms[:5]  # Take first 5
    room_summaries = []
    for room in top_rooms:
        room_name = room.get("room_name") or room.get("room_type_name", "Unknown")
        available_count = room.get("available", 0)

        # Get cheapest price for this room
        room_prices = [p.get("price", 0) for p in room.get("prices", [])]
        cheapest = min(room_prices) if room_prices else 0

        room_summaries.append(f"{room_name} ({available_count} avail, from {cheapest} {currency})")

    # Build summary
    summary_parts = [
        f"Found {total_available} available room types",
        f"Price range: {min_price}-{max_price} {currency}",
        f"Top rooms: {'; '.join(room_summaries[:3])}"
    ]
    summary = ". ".join(summary_parts)

    # Build metadata for reference
    metadata = {
        "type": "availability",
        "total_rooms": total_available,
        "price_range": {"min": min_price, "max": max_price, "currency": currency},
        "check_in": result.get("check_in"),
        "check_out": result.get("check_out"),
        "adults": result.get("adults"),
        "children": result.get("children"),
        "top_rooms": [
            {
                "code": r.get("room_type_code"),
                "name": r.get("room_name") or r.get("room_type_name"),
                "available": r.get("available"),
                "min_price": min([p.get("price", 0) for p in r.get("prices", [])])
            }
            for r in top_rooms[:5]
        ]
    }

    return summary, metadata


def _compress_booking_link(result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Compress booking link results.

    Booking links are already compact - just extract the URL.
    """
    if isinstance(result, str):
        # Extract URL if it's in text like "Here is your booking link: <url>"
        if "http" in result:
            url = result.split("http", 1)[1]
            url = "http" + url.split()[0].rstrip('.,;')
            return f"Booking link generated: {url}", {"type": "booking_link", "url": url}
        return result, {"type": "booking_link"}

    elif isinstance(result, dict) and "url" in result:
        return f"Booking link: {result['url']}", {"type": "booking_link", "url": result["url"]}

    return str(result), {"type": "booking_link"}


def _compress_generic(result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Generic compression for unknown result types.

    Simply truncates to 200 characters.
    """
    result_str = str(result)
    max_length = 200

    if len(result_str) > max_length:
        summary = result_str[:max_length].rsplit(' ', 1)[0] + "..."
    else:
        summary = result_str

    metadata = {"type": "generic"}

    if isinstance(result, dict):
        metadata["data_keys"] = list(result.keys())
    elif isinstance(result, list):
        metadata["item_count"] = len(result)

    return summary, metadata


def get_tool_output_reference(summary: str, metadata: Optional[Dict[str, Any]]) -> str:
    """
    Generate a concise reference string for tool output.

    This is used when building context prompts to reference previous tool calls.

    Args:
        summary: The compressed summary text
        metadata: The metadata dict from compression

    Returns:
        Concise reference string
    """
    if not metadata:
        return summary[:100]

    tool_type = metadata.get("type", "unknown")

    if tool_type == "availability":
        total = metadata.get("total_rooms", 0)
        price_range = metadata.get("price_range", {})
        min_price = price_range.get("min", 0)
        max_price = price_range.get("max", 0)
        currency = price_range.get("currency", "ILS")
        return f"{total} rooms available, {min_price}-{max_price} {currency}"

    elif tool_type == "booking_link":
        url = metadata.get("url", "")
        return f"Booking link: {url}"

    elif tool_type == "calendar":
        if "dates" in metadata:
            dates = metadata["dates"]
            return f"{dates.get('check_in')} to {dates.get('check_out')}"
        return summary[:100]

    else:
        return summary[:100]
