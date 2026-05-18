import time
import requests
from geopy.geocoders import Nominatim
from .config import NOMINATIM_UA, BRASILAPI_BASE

_geolocator = Nominatim(user_agent=NOMINATIM_UA)


def geocode_address(address: str) -> tuple[float, float]:
    """Convert free-text address to (lat, lng) using Nominatim."""
    location = _geolocator.geocode(address, country_codes="BR", timeout=15)
    if not location:
        # retry without country filter
        location = _geolocator.geocode(f"{address}, Brasil", timeout=15)
    if not location:
        raise ValueError(f"Não foi possível geocodificar: {address!r}")
    return location.latitude, location.longitude


def geocode_cep(cep: str) -> tuple[float, float] | None:
    """Get (lat, lng) for a Brazilian CEP, trying BrasilAPI first then Nominatim."""
    clean = cep.replace("-", "").replace(".", "").strip().zfill(8)
    # BrasilAPI CEP v2 returns coordinates directly
    try:
        r = requests.get(f"{BRASILAPI_BASE}/cep/v2/{clean}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            coords = data.get("location", {}).get("coordinates", {})
            lat = coords.get("latitude")
            lng = coords.get("longitude")
            if lat and lng:
                return float(lat), float(lng)
    except Exception:
        pass

    # Fallback: Nominatim (rate-limited to 1 req/s)
    try:
        time.sleep(1.1)
        location = _geolocator.geocode(f"CEP {clean}, Brasil", timeout=15)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass

    return None
