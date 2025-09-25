from typing import Optional, Tuple

# Minimal city alias mapping used only for DB filtering, not for response labels
ALIASES = {
    "bengaluru": "Bangalore",
}


def normalize_city(city: Optional[str]) -> Tuple[Optional[str], bool]:
    """
    Normalize incoming city/location to DB value using alias mapping.

    Returns a tuple of (normalized_city_or_none, aliased_flag).
    - If input is None/empty -> (None, False)
    - Trims whitespace and applies case-insensitive alias lookup
    """
    if not city:
        return None, False

    city_trimmed = city.strip()
    if city_trimmed == "":
        return None, False

    alias = ALIASES.get(city_trimmed.lower())
    if alias:
        return alias, True
    return city_trimmed, False


