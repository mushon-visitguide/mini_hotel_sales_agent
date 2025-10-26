"""Room enrichment helper - matches PMS room codes to room details"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


def load_room_mapping(hotel_id: str = "visitguide") -> List[Dict[str, Any]]:
    """
    Load room mapping from JSON file.

    Args:
        hotel_id: Hotel identifier (default: Oreldi71)

    Returns:
        List of room mappings with ids, name, description
    """
    mapping_file = Path(__file__).parent.parent.parent.parent / "rooms-mapping.json"

    if not mapping_file.exists():
        return []

    with open(mapping_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def match_room_code_to_info(room_code: str, room_mappings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Match a PMS room code to room info from mapping.

    Matches using the same logic as ai-server:
    - Check if room_code equals mapping.name
    - Check if room_code is in mapping.ids array

    Args:
        room_code: Room type code from PMS (e.g., "432A", "FAMILY")
        room_mappings: List of room mappings from JSON

    Returns:
        Dict with name and description if found, None otherwise
    """
    for mapping in room_mappings:
        # Match by name
        if mapping.get("name") == room_code:
            return {
                "room_name": mapping.get("name"),
                "room_desc": mapping.get("description")
            }

        # Match by id in ids array
        if room_code in mapping.get("ids", []):
            return {
                "room_name": mapping.get("name"),
                "room_desc": mapping.get("description")
            }

    return None


def enrich_room_types(room_types: List[Dict[str, Any]], hotel_id: str = "visitguide") -> List[Dict[str, Any]]:
    """
    Enrich room types with name and description from mapping file.

    Similar to MiniHotelRoomEnricher.enrich_room_list() in ai-server.

    Args:
        room_types: List of room type dicts from PMS API
        hotel_id: Hotel identifier

    Returns:
        Enriched room types with room_name and room_desc added
    """
    # Load mapping
    room_mappings = load_room_mapping(hotel_id)

    if not room_mappings:
        # No mapping file, return as-is
        return room_types

    enriched_rooms = []

    for room in room_types:
        enriched_room = dict(room)  # Copy
        room_code = room.get("room_type_code")

        if room_code:
            # Try to match and enrich
            match = match_room_code_to_info(room_code, room_mappings)

            if match:
                enriched_room["room_name"] = match["room_name"]
                enriched_room["room_desc"] = match["room_desc"]
            else:
                # No match - use PMS name as fallback
                enriched_room["room_name"] = room.get("room_type_name", room_code)
                enriched_room["room_desc"] = None
        else:
            enriched_room["room_name"] = room.get("room_type_name", "Unknown")
            enriched_room["room_desc"] = None

        enriched_rooms.append(enriched_room)

    return enriched_rooms
