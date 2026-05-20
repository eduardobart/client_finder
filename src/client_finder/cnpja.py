"""
CNPJA API integration for geographic CNPJ search.

Strategy: search by IBGE municipality code (filters: active status + médio/grande porte),
geocode each result's CEP via BrasilAPI, then filter by Haversine distance.

Free plan: register at https://cnpja.com to get an API key (no credit card needed).
Credit cost: 1 credit per 10 companies returned by the search endpoint.
"""

import time
import requests
from math import radians, cos, sin, asin, sqrt
from geopy.geocoders import Nominatim

from .config import NOMINATIM_UA, BRASILAPI_BASE
from .models import Empresa

CNPJA_BASE = "https://api.cnpja.com"

# CNPJA size id 5 = "DEMAIS" = médio/grande porte (same as RF code '05')
_SIZE_GRANDE = 5
# CNPJA status id 2 = ATIVA
_STATUS_ATIVA = 2

_geolocator = Nominatim(user_agent=NOMINATIM_UA)


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * R * asin(sqrt(a))


def _reverse_geocode_city(lat: float, lng: float) -> tuple[str, str] | None:
    """Return (city_name, uf_code) from coordinates via Nominatim."""
    try:
        time.sleep(1.1)
        loc = _geolocator.reverse(
            (lat, lng), exactly_one=True, language="pt", timeout=15
        )
        if not loc:
            return None
        addr = loc.raw.get("address", {})
        city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("municipality")
            or addr.get("county")
            or ""
        )
        state = addr.get("ISO3166-2-lvl4", "")
        if "-" in state:
            state = state.split("-")[-1]
        return city.strip(), state.upper().strip()
    except Exception:
        return None


def _get_ibge_code(city_name: str, uf: str) -> int | None:
    """Look up IBGE municipality code via BrasilAPI."""
    try:
        r = requests.get(
            f"{BRASILAPI_BASE}/ibge/municipios/v1/{uf}",
            timeout=10,
        )
        if r.status_code != 200:
            return None
        municipios = r.json()
        city_up = city_name.upper()
        # Exact match first
        for m in municipios:
            if m["nome"].upper() == city_up:
                return int(m["codigo_ibge"])
        # Partial match fallback
        for m in municipios:
            if city_up in m["nome"].upper() or m["nome"].upper() in city_up:
                return int(m["codigo_ibge"])
    except Exception:
        pass
    return None


def _cep_to_coords(cep: str) -> tuple[float, float] | None:
    """Get lat/lng for a CEP via BrasilAPI (fast, cached internally by BrasilAPI)."""
    clean = cep.replace("-", "").strip().zfill(8)
    try:
        r = requests.get(f"{BRASILAPI_BASE}/cep/v2/{clean}", timeout=8)
        if r.status_code == 200:
            loc = r.json().get("location", {}).get("coordinates", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")
            if lat and lng:
                return float(lat), float(lng)
    except Exception:
        pass
    return None


def _build_empresa(office: dict, dist: float, lat, lng) -> Empresa:
    company = office.get("company", {}) or {}
    addr = office.get("address", {}) or {}
    size = company.get("size", {}) or {}
    phones = office.get("phones", []) or []
    emails = office.get("emails", []) or []
    mun = addr.get("municipality", {}) or {}
    state = addr.get("state", {}) or {}

    phone = ""
    if phones:
        p = phones[0]
        area = p.get("area", "")
        num = p.get("number", "")
        phone = f"({area}) {num}" if area else num

    raw_cnpj = office.get("taxId", "") or ""
    cnpj = raw_cnpj.replace(".", "").replace("/", "").replace("-", "")

    porte_id = str(size.get("id", "05"))
    porte_desc = size.get("text", "Médio/Grande Porte")

    return Empresa(
        cnpj=cnpj,
        razao_social=company.get("name", ""),
        nome_fantasia=office.get("alias", ""),
        porte=porte_id,
        porte_desc=porte_desc,
        logradouro=addr.get("street", ""),
        numero=str(addr.get("number", "") or ""),
        complemento=addr.get("details", ""),
        bairro=addr.get("district", ""),
        cep=(addr.get("zip", "") or "").replace("-", ""),
        municipio=mun.get("name", ""),
        uf=state.get("code", ""),
        telefone=phone,
        email=emails[0].get("address", "") if emails else "",
        distancia_km=round(dist, 3),
        lat=lat,
        lng=lng,
        fonte="cnpja",
    )


def search_cnpja(
    lat: float,
    lng: float,
    radius_km: float,
    api_key: str,
    limit: int = 500,
) -> list[Empresa]:
    """
    Find active médio/grande porte companies within radius_km of (lat, lng) via CNPJA API.

    Args:
        lat/lng: Center of search area.
        radius_km: Maximum distance from center.
        api_key: CNPJA API key from https://cnpja.com (free registration).
        limit: Maximum number of results to return.

    Raises:
        RuntimeError: On auth/credit errors or if municipality cannot be resolved.
    """
    headers = {"Authorization": api_key, "Accept": "application/json"}

    # Identify municipality from coordinates
    geo = _reverse_geocode_city(lat, lng)
    if not geo or not geo[0]:
        raise RuntimeError(
            "Não foi possível identificar o município pelas coordenadas. "
            "Tente um endereço mais específico."
        )
    city_name, uf = geo

    ibge_code = _get_ibge_code(city_name, uf)
    if not ibge_code:
        raise RuntimeError(
            f"Município '{city_name}/{uf}' não encontrado na base IBGE. "
            "Tente especificar o município no endereço de busca."
        )

    # Paginate CNPJA search
    results: list[Empresa] = []
    token: str | None = None
    pages_fetched = 0
    max_pages = 100  # safety cap: 100 pages × 10 results = 1000 companies max, 100 credits

    while len(results) < limit and pages_fetched < max_pages:
        if token:
            params: dict = {"token": token}
        else:
            params = {
                "limit": 10,
                "status.id.in": _STATUS_ATIVA,
                "company.size.id.in": _SIZE_GRANDE,
                "address.municipality.in": ibge_code,
            }

        resp = requests.get(
            f"{CNPJA_BASE}/office",
            params=params,
            headers=headers,
            timeout=30,
        )

        if resp.status_code == 401:
            raise RuntimeError(
                "Chave de API CNPJA inválida ou expirada. "
                "Verifique sua chave em cnpja.com"
            )
        if resp.status_code == 402:
            raise RuntimeError(
                "Créditos CNPJA esgotados. "
                "Recarregue em cnpja.com ou aguarde renovação do plano gratuito."
            )
        if not resp.ok:
            raise RuntimeError(
                f"CNPJA API retornou erro {resp.status_code}: {resp.text[:300]}"
            )

        payload = resp.json()
        # API may return list directly or wrapped in {"data": [...], "next": "token"}
        if isinstance(payload, list):
            offices = payload
            token = None
        else:
            offices = payload.get("data", [])
            token = payload.get("next")  # pagination token for next page

        if not offices:
            break

        for office in offices:
            if len(results) >= limit:
                break

            addr = office.get("address", {}) or {}
            cep = (addr.get("zip", "") or "").replace("-", "")

            coords = _cep_to_coords(cep) if cep else None
            dist = _haversine(lat, lng, coords[0], coords[1]) if coords else 999.0

            if dist <= radius_km:
                emp = _build_empresa(
                    office, dist,
                    coords[0] if coords else None,
                    coords[1] if coords else None,
                )
                results.append(emp)

            time.sleep(0.03)

        pages_fetched += 1
        if not token:
            break

    results.sort(key=lambda e: e.distancia_km or 0)
    return results
