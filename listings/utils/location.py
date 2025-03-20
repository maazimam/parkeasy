import math


def simplify_location(location_string):
    """
    Simplifies a location string before sending to template.
    Example: "Tandon School of Engineering, Johnson Street, Downtown Brooklyn, Brooklyn..."
    becomes "Tandon School of Engineering, Brooklyn"
    """
    if not location_string:
        return ""

    parts = [part.strip() for part in location_string.split(",")]
    if len(parts) < 2:
        return location_string

    building = parts[0]

    # Find the city (Brooklyn, Manhattan, etc.)
    city = next(
        (
            part
            for part in parts
            if part.strip()
            in ["Brooklyn", "Manhattan", "Queens", "Bronx", "Staten Island"]
        ),
        "New York",
    )

    # For educational institutions, keep the full name
    if any(
        term in building.lower()
        for term in ["school", "university", "college", "institute"]
    ):
        return f"{building}, {city}"

    # For other locations, use first two parts
    street = parts[1]
    return f"{building}, {street}, {city}"


def calculate_distance(lat1, lng1, lat2, lng2):
    """
    Calculate the Haversine distance between two points on the earth.

    Args:
        lat1, lng1: Latitude and longitude of first point
        lat2, lng2: Latitude and longitude of second point

    Returns:
        Distance in kilometers, rounded to 1 decimal place
    """
    R = 6371  # Earth's radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (math.sin(dlat/2) * math.sin(dlat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng/2) * math.sin(dlng/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return round(R * c, 1)


def extract_coordinates(location_string):
    """
    Extract latitude and longitude from a location string.

    Args:
        location_string: String containing coordinates in format "name [lat,lng]"

    Returns:
        tuple: (latitude, longitude) as floats

    Raises:
        ValueError: If coordinates cannot be extracted
    """
    try:
        coords = location_string.split('[')[1].strip(']').split(',')
        return float(coords[0]), float(coords[1])
    except (IndexError, ValueError) as e:
        raise ValueError(f"Could not extract coordinates from location string: {e}")
