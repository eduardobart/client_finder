"""
Quick-mode search via OpenStreetMap Overpass API.
Falls back gracefully when Overpass is blocked (firewalls, corporate networks).
"""

import re
import time
import requests
from .config import BRASILAPI_BASE, PORTE_MEDIO_GRANDE, PORTE_MAP
from .models import Empresa
from .database import haversine

_OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]

_QUERY_TPL = """
[out:json][timeout:25];
(
  node(around:{radius},{lat},{lng})["office"][name];
  way(around:{radius},{lat},{lng})["office"][name];
  node(around:{radius},{lat},{lng})["company"][name];
  way(around:{radius},{lat},{lng})["company"][name];
  node(around:{radius},{lat},{lng})[amenity=bank][name];
  way(around:{radius},{lat},{lng})[amenity=bank][name];
);
out center tags;
"""


def _clean_cnpj(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    return digits if len(digits) == 14 else None


def _lookup_cnpj_api(cnpj: str) -> dict | None:
    try:
        r = requests.get(f"{BRASILAPI_BASE}/cnpj/v1/{cnpj}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _overpass_query(lat: float, lng: float, radius_m: int) -> list[dict]:
    """Try Overpass mirrors in sequence. Returns OSM elements or raises RuntimeError."""
    query = _QUERY_TPL.format(radius=radius_m, lat=lat, lng=lng)
    last_err = None
    for mirror in _OVERPASS_MIRRORS:
        try:
            resp = requests.post(mirror, data={"data": query}, timeout=35)
            if resp.status_code == 200:
                return resp.json().get("elements", [])
        except Exception as e:
            last_err = e
    raise RuntimeError(
        f"Todos os mirrors Overpass falharam (último erro: {last_err}). "
        "Verifique sua conexão ou use --mode full."
    )


def search_overpass(
    lat: float,
    lng: float,
    radius_km: float,
    limit: int = 200,
) -> list[Empresa]:
    """
    Query Overpass for named businesses within radius.
    Enriches with CNPJ via BrasilAPI when a cnpj OSM tag is present.
    Includes businesses without CNPJ when no data source can confirm their size.
    """
    radius_m = int(radius_km * 1000)
    elements = _overpass_query(lat, lng, radius_m)

    results: list[Empresa] = []

    porte_to_code = {
        "DEMAIS": "05", "ME": "01", "EPP": "03",
        "NAO INFORMADO": "00", "NÃO INFORMADO": "00",
    }

    for el in elements:
        if len(results) >= limit:
            break

        tags = el.get("tags", {})
        name = tags.get("name", "").strip()
        if not name:
            continue

        elat = el.get("lat") or el.get("center", {}).get("lat")
        elng = el.get("lon") or el.get("center", {}).get("lon")
        if not elat or not elng:
            continue

        dist = haversine(lat, lng, elat, elng)

        raw_cnpj = tags.get("cnpj") or tags.get("ref:cnpj") or ""
        cnpj_data = None
        cnpj = ""

        if raw_cnpj:
            clean = _clean_cnpj(raw_cnpj)
            if clean:
                cnpj = clean
                cnpj_data = _lookup_cnpj_api(clean)
                time.sleep(0.2)

        porte_txt = (cnpj_data.get("porte", "") or "") if cnpj_data else ""
        porte_code = porte_to_code.get(porte_txt.upper().strip(), "00")

        # when we have CNPJ data and it's micro or EPP, skip
        if cnpj_data and porte_code in {"01", "03"}:
            continue

        results.append(Empresa(
            cnpj=cnpj or "00000000000000",
            razao_social=(cnpj_data or {}).get("razao_social", name),
            nome_fantasia=name,
            porte=porte_code,
            porte_desc=PORTE_MAP.get(porte_code, "Não Informado"),
            logradouro=(cnpj_data or {}).get("logradouro", tags.get("addr:street", "")),
            numero=(cnpj_data or {}).get("numero", tags.get("addr:housenumber", "")),
            complemento="",
            bairro=(cnpj_data or {}).get("bairro", tags.get("addr:suburb", "")),
            cep=(cnpj_data or {}).get("cep", tags.get("addr:postcode", "")),
            municipio=(cnpj_data or {}).get("municipio", tags.get("addr:city", "")),
            uf=(cnpj_data or {}).get("uf", tags.get("addr:state", "")),
            telefone=(cnpj_data or {}).get("telefone", tags.get("phone", "")),
            email=(cnpj_data or {}).get("email", tags.get("email", "")),
            distancia_km=round(dist, 3),
            lat=elat,
            lng=elng,
            fonte="osm",
        ))

    results.sort(key=lambda e: e.distancia_km or 0)
    return results
