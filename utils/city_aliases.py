from typing import Optional

# PERF-SAFE: keep minimal, no external deps.
# NOTE: Scope this mapping to Total Technicians metric only (do not import globally elsewhere).
_TECHNICIAN_CITY_ALIAS = {
    # Special case: Treat Bengaluru as Bangalore for technician counts
    "bengaluru": "Bangalore",
}

def normalize_city_for_technician_count(city: Optional[str]) -> Optional[str]:
    """
    Returns the canonical city for Total Technicians metric.
    Only applies a narrow alias for 'Bengaluru' -> 'Bangalore'.
    Leaves other cities unchanged. Preserves None/empty safely.
    """
    if not city:
        return city
    c = city.strip().casefold()
    alias = _TECHNICIAN_CITY_ALIAS.get(c)
    return alias if alias else city.strip()


