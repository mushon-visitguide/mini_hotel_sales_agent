"""Availability summarization tools for multi-room bookings

These are internal functions automatically called by the Runtime when
multiple availability checks are detected. They are NOT exposed as tools.
"""
from typing import List, Dict, Any, Optional


def _try_mixed_room_types(
    room_type_analysis: Dict[str, Any],
    room_requirements: List[dict],
    total_rooms_needed: int
) -> Optional[Dict[str, Any]]:
    """
    Try to fulfill multi-room booking by mixing different room types.

    Example: 2 rooms needed, Room Type A has 1, Room Type B has 1 → Mix them!

    Args:
        room_type_analysis: Analyzed room type data
        room_requirements: List of occupancy requirements
        total_rooms_needed: Total number of rooms

    Returns:
        Mixed allocation option if successful, None otherwise
    """
    # Build compatibility map: which room types can fulfill each requirement
    compatibility = []
    for idx, requirement in enumerate(room_requirements):
        compatible_types = []
        for code, data in room_type_analysis.items():
            # Check if this room type appeared in this query
            for accommodates in data["can_accommodate"]:
                if accommodates["query_index"] == idx:
                    # Get pricing for this occupancy
                    pricing = next(
                        (p for p in data["pricing_per_occupancy"] if p["query_index"] == idx),
                        None
                    )
                    if pricing:
                        compatible_types.append({
                            "code": code,
                            "name": data["name"],
                            "available": data["available_count"],
                            "price": pricing["price"],
                            "board_code": pricing["board_code"],
                            "occupancy": pricing["occupancy"]
                        })
        # Sort by price (greedy: prefer cheaper rooms)
        compatible_types.sort(key=lambda x: x["price"])
        compatibility.append(compatible_types)

    # Try greedy allocation
    inventory = {code: data["available_count"] for code, data in room_type_analysis.items()}
    allocation = []

    for room_idx, compatible_types in enumerate(compatibility):
        # Try to allocate the cheapest available room type
        allocated = False
        for room_type in compatible_types:
            code = room_type["code"]
            if inventory[code] > 0:
                # Allocate this room type
                allocation.append({
                    "room_index": room_idx,
                    "room_type_code": code,
                    "room_type_name": room_type["name"],
                    "price": room_type["price"],
                    "board_code": room_type["board_code"],
                    "occupancy": room_type["occupancy"]
                })
                inventory[code] -= 1
                allocated = True
                break

        if not allocated:
            # Cannot allocate this room - mixed allocation fails
            return None

    # Success! Build the mixed option
    total_price = sum(alloc["price"] for alloc in allocation)

    # Group by room type for summary
    room_type_counts = {}
    for alloc in allocation:
        code = alloc["room_type_code"]
        if code not in room_type_counts:
            room_type_counts[code] = {
                "name": alloc["room_type_name"],
                "count": 0,
                "prices": []
            }
        room_type_counts[code]["count"] += 1
        room_type_counts[code]["prices"].append({
            "occupancy": alloc["occupancy"],
            "price": alloc["price"],
            "board_code": alloc["board_code"]
        })

    return {
        "room_type_code": "MIXED",
        "room_type_name": "Mixed Room Types",
        "is_mixed": True,
        "allocation": allocation,
        "room_type_summary": [
            {
                "code": code,
                "name": data["name"],
                "count": data["count"],
                "prices": data["prices"]
            }
            for code, data in room_type_counts.items()
        ],
        "rooms_needed": total_rooms_needed,
        "pricing_breakdown": [
            {
                "query_index": alloc["room_index"],
                "occupancy": alloc["occupancy"],
                "price": alloc["price"],
                "board_code": alloc["board_code"],
                "room_type": alloc["room_type_name"]
            }
            for alloc in allocation
        ],
        "total_price_per_night": total_price,
        "can_fulfill": True
    }


async def summarize_multi_room_mixed(
    availability_results: List[dict],
    room_requirements: List[dict]
) -> dict:
    """
    Summarizes and analyzes availability for multiple rooms with different occupancies.

    CRITICAL: Handles the case where same room type appears in multiple queries.
    The actual available count is SHARED across all queries.

    Example:
        User needs: 3 rooms (2A, 4A, 3A)
        Room Type 15084 appears in all 3 queries with "available: 1"
        But there's only 1 physical room, not 3!
        This tool correctly validates: 1 < 3 → FAIL

    Args:
        availability_results: List of responses from pms.get_availability calls
            [
                {"room_types": [{"room_type_code": "15084", "available": 1, ...}]},  # 2A query
                {"room_types": [{"room_type_code": "15084", "available": 1, ...}]},  # 4A query
                {"room_types": [{"room_type_code": "15084", "available": 1, ...}]}   # 3A query
            ]

        room_requirements: List of occupancy requirements (one per room)
            [
                {"adults": 2, "children": 0, "babies": 0},
                {"adults": 4, "children": 0, "babies": 0},
                {"adults": 3, "children": 0, "babies": 0}
            ]

    Returns:
        {
            "can_fulfill": bool - Whether booking is possible
            "options": List of viable room type options with pricing breakdown
            "total_rooms_needed": int
            "warnings": List of issues found
        }
    """

    if len(availability_results) != len(room_requirements):
        return {
            "can_fulfill": False,
            "options": [],
            "warnings": ["Mismatch between availability results and room requirements"]
        }

    total_rooms_needed = len(room_requirements)

    # Track room type data across all queries
    room_type_analysis = {}

    # Process each availability result
    for idx, result in enumerate(availability_results):
        requirement = room_requirements[idx]

        for rt in result.get("room_types", []):
            code = rt["room_type_code"]

            # Extract available count from inventory or available field
            inventory = rt.get("inventory")
            available_count = inventory.get("allocation", 0) if inventory else rt.get("available", 0)

            # Initialize room type tracking
            if code not in room_type_analysis:
                room_type_analysis[code] = {
                    "name": rt["room_type_name"],
                    "available_count": available_count,  # Physical rooms available
                    "max_capacity": {
                        "adults": rt.get("max_adults"),
                        "children": rt.get("max_children"),
                        "babies": rt.get("max_babies")
                    },
                    "appears_in_queries": 0,
                    "pricing_per_occupancy": [],
                    "can_accommodate": []
                }

            # Track that this room type can handle this occupancy
            room_type_analysis[code]["appears_in_queries"] += 1
            room_type_analysis[code]["can_accommodate"].append({
                "query_index": idx,
                "adults": requirement.get("adults", 0),
                "children": requirement.get("children", 0),
                "babies": requirement.get("babies", 0)
            })

            # Extract pricing for this specific occupancy
            prices = rt.get("prices", [])
            if prices:
                min_price = min(p["price"] for p in prices)
                board_code = next((p["board_code"] for p in prices if p["price"] == min_price), "RO")

                room_type_analysis[code]["pricing_per_occupancy"].append({
                    "query_index": idx,
                    "occupancy": f"{requirement.get('adults', 0)}A+{requirement.get('children', 0)}C+{requirement.get('babies', 0)}B",
                    "price": min_price,
                    "board_code": board_code
                })

    # Find room types that can fulfill ALL requirements
    suitable_options = []
    insufficient_options = []

    for code, data in room_type_analysis.items():
        # Must appear in ALL queries (can fit all different occupancies)
        can_fit_all = data["appears_in_queries"] == total_rooms_needed

        # Must have enough physical rooms
        has_enough_rooms = data["available_count"] >= total_rooms_needed

        # Calculate total price (sum of all occupancy prices)
        total_price = sum(p["price"] for p in data["pricing_per_occupancy"])

        option = {
            "room_type_code": code,
            "room_type_name": data["name"],
            "available_count": data["available_count"],
            "rooms_needed": total_rooms_needed,
            "max_capacity": data["max_capacity"],
            "pricing_breakdown": data["pricing_per_occupancy"],
            "total_price_per_night": total_price,
            "can_fulfill": can_fit_all and has_enough_rooms
        }

        if can_fit_all and has_enough_rooms:
            suitable_options.append(option)
        else:
            # Add reason why it can't fulfill
            reasons = []
            if not can_fit_all:
                reasons.append(f"Can't fit all occupancies (appears in {data['appears_in_queries']}/{total_rooms_needed} queries)")
            if not has_enough_rooms:
                reasons.append(f"Not enough rooms (has {data['available_count']}, need {total_rooms_needed})")

            option["cannot_fulfill_reason"] = " & ".join(reasons)
            insufficient_options.append(option)

    # Sort suitable options by total price
    suitable_options.sort(key=lambda x: x["total_price_per_night"])

    # If no single room type works, try mixing different room types
    mixed_allocation = None
    if not suitable_options:
        mixed_allocation = _try_mixed_room_types(room_type_analysis, room_requirements, total_rooms_needed)
        if mixed_allocation:
            suitable_options.append(mixed_allocation)

    # Generate warnings
    warnings = []
    if not suitable_options:
        if insufficient_options:
            # Explain why options failed
            for opt in insufficient_options:
                warnings.append(f"{opt['room_type_name']}: {opt['cannot_fulfill_reason']}")
        else:
            warnings.append("No room types can accommodate all the requested occupancies")

    # Build message
    if suitable_options:
        if mixed_allocation:
            message = f"Can fulfill {total_rooms_needed} rooms by mixing different room types"
        else:
            message = f"Found {len(suitable_options)} room type(s) that can fulfill all {total_rooms_needed} rooms"
    else:
        message = f"Cannot fulfill request for {total_rooms_needed} rooms with given requirements"

    return {
        "can_fulfill": len(suitable_options) > 0,
        "options": suitable_options[:3],  # Top 3 options
        "insufficient_options": insufficient_options,
        "total_rooms_needed": total_rooms_needed,
        "requirements": room_requirements,
        "warnings": warnings,
        "message": message
    }


async def summarize_multi_room_simple(
    availability_data: dict,
    rooms_needed: int
) -> dict:
    """
    Summarizes availability for when all rooms have the SAME occupancy requirements.

    Example: "3 rooms for 2 adults each" or "2 family suites"

    Args:
        availability_data: Single response from pms.get_availability
        rooms_needed: How many rooms needed (e.g., 3)

    Returns:
        Options that have enough rooms available
    """

    room_types = availability_data.get("room_types", [])
    suitable = []
    insufficient = []

    for rt in room_types:
        # Extract available count from inventory or available field
        inventory = rt.get("inventory")
        available_count = inventory.get("allocation", 0) if inventory else rt.get("available", 0)
        prices = rt.get("prices", [])

        if not prices:
            continue

        min_price = min(p["price"] for p in prices)
        total_price = min_price * rooms_needed

        option = {
            "room_type_code": rt["room_type_code"],
            "room_type_name": rt["room_type_name"],
            "available_count": available_count,
            "rooms_needed": rooms_needed,
            "max_capacity": {
                "adults": rt.get("max_adults"),
                "children": rt.get("max_children"),
                "babies": rt.get("max_babies")
            },
            "price_per_room": min_price,
            "total_price_per_night": total_price,
            "board_options": [
                {"board_code": p["board_code"], "price": p["price"] * rooms_needed}
                for p in prices
            ]
        }

        if available_count >= rooms_needed:
            suitable.append(option)
        else:
            option["shortage"] = rooms_needed - available_count
            insufficient.append(option)

    # Sort by total price
    suitable.sort(key=lambda x: x["total_price_per_night"])

    warnings = []
    if not suitable:
        if insufficient:
            max_available = max(opt["available_count"] for opt in insufficient)
            warnings.append(f"Maximum {max_available} rooms available, but {rooms_needed} needed")
        else:
            warnings.append("No rooms available for the requested occupancy")

    return {
        "can_fulfill": len(suitable) > 0,
        "options": suitable,
        "insufficient_options": insufficient,
        "rooms_needed": rooms_needed,
        "warnings": warnings,
        "message": (
            f"Found {len(suitable)} room type(s) with {rooms_needed}+ rooms available"
            if suitable
            else f"No room types have {rooms_needed}+ rooms available"
        )
    }
