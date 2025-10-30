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
    elif tool_name.startswith("guest."):
        return _compress_guest_output(tool_name, tool_result)
    else:
        # Generic compression for unknown tools
        return _compress_generic(tool_result)


def _compress_faq_output(tool_name: str, result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    FAQ tools are NOT compressed - return full text.

    FAQ content contains important details (capacities, policies, amenities)
    that should not be truncated.
    """
    metadata = {"type": "faq", "tool": tool_name}

    if "rooms" in tool_name:
        metadata["content_type"] = "rooms_info"
    elif "hotel" in tool_name:
        metadata["content_type"] = "hotel_info"
    elif "policies" in tool_name:
        metadata["content_type"] = "policies"

    # Return full result without compression
    if isinstance(result, str):
        return result, metadata
    else:
        return str(result), metadata


def _compress_calendar_output(tool_name: str, result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Calendar tools are NOT compressed - return full result.
    """
    metadata = {"type": "calendar", "tool": tool_name}

    if "resolve_date" in tool_name:
        metadata["resolved"] = True

    # Return full result without compression
    if isinstance(result, str):
        return result, metadata
    elif isinstance(result, dict):
        # Keep structured format
        return str(result), {"type": "calendar", "dates": result}
    else:
        return str(result), metadata


def _compress_guest_output(tool_name: str, result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Guest tools are NOT compressed - return full result.

    Guest information contains important reservation details that should not be truncated.
    """
    metadata = {"type": "guest", "tool": tool_name}

    if "get_guest_info" in tool_name:
        metadata["content_type"] = "guest_info"

    # Return full result without compression
    if isinstance(result, str):
        return result, metadata
    else:
        return str(result), metadata


def _compress_pms_output(tool_name: str, result: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    PMS tools are NOT compressed - return full result.
    """
    metadata = {"type": "pms", "tool": tool_name}

    if "availability" in tool_name:
        metadata["content_type"] = "availability"
    elif "booking_link" in tool_name:
        metadata["content_type"] = "booking_link"

    # Return full result without compression
    return str(result), metadata


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

    # Build detailed room listings for top 3 rooms
    detailed_rooms = []
    for room in top_rooms[:3]:
        room_name = room.get("room_name") or room.get("room_type_name", "Unknown")
        room_desc = room.get("room_desc", "")
        available_count = room.get("available", 0)

        # Get cheapest price for this room
        room_prices = [p.get("price", 0) for p in room.get("prices", [])]
        cheapest = min(room_prices) if room_prices else 0

        # Extract first line of description (has the key features)
        if room_desc:
            # Get first meaningful line (skip room name line)
            lines = [line.strip() for line in room_desc.split('\n') if line.strip()]
            features_line = ""
            for line in lines:
                # Skip the room name line and empty lines
                if line and not line.startswith('סוויטת') and not line.startswith('דירת') and not line.startswith('אוראל'):
                    features_line = line
                    break

            if features_line:
                detailed_rooms.append(
                    f"• {room_name}: {features_line} (Price: {cheapest} {currency}, Available: {available_count})"
                )
            else:
                detailed_rooms.append(
                    f"• {room_name}: {available_count} available, from {cheapest} {currency}"
                )
        else:
            detailed_rooms.append(
                f"• {room_name}: {available_count} available, from {cheapest} {currency}"
            )

    # Build summary with detailed room information
    summary_parts = [
        f"Found {total_available} available room types. Price range: {min_price}-{max_price} {currency}.",
        "\nTop available rooms with details:"
    ]
    summary_parts.extend(detailed_rooms)
    summary = "\n".join(summary_parts)

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
                "description": r.get("room_desc"),
                "available": r.get("available"),
                "min_price": min([p.get("price", 0) for p in r.get("prices", [])]) if r.get("prices") else 0
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
