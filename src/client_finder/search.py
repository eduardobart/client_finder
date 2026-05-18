"""
Main search orchestration.

Two modes:
  - 'quick'  : Overpass OSM (no local data needed, less complete)
  - 'full'   : Local RF SQLite database (requires prior import, complete)
"""

import time
import random
from rich.console import Console
from .config import PORTE_MEDIO_GRANDE, PORTE_MAP, DEFAULT_RADIUS_KM, DEFAULT_LIMIT
from .geocoder import geocode_address, geocode_cep
from .database import (
    init_db, search_rf, get_cep_coords, upsert_cep_coords,
    count_empresas, count_estabelecimentos,
)
from .models import Empresa, SearchResult

console = Console()


def _build_empresa_from_row(row: dict) -> Empresa:
    logradouro = " ".join(filter(None, [
        row.get("tipo_logradouro", ""),
        row.get("logradouro", ""),
    ]))
    return Empresa(
        cnpj=row["cnpj"],
        razao_social=row["razao_social"],
        nome_fantasia=row.get("nome_fantasia", ""),
        porte=row["porte"],
        porte_desc=PORTE_MAP.get(row["porte"], "Médio/Grande Porte"),
        logradouro=logradouro,
        numero=row.get("numero", ""),
        complemento=row.get("complemento", ""),
        bairro=row.get("bairro", ""),
        cep=row.get("cep", ""),
        municipio=row.get("municipio_cod", ""),
        uf=row.get("uf", ""),
        telefone=row.get("telefone", ""),
        email=row.get("email", ""),
        distancia_km=round(row["dist"], 3),
        lat=row.get("lat"),
        lng=row.get("lng"),
        fonte="rf",
    )


def _geocode_missing_ceps(rows: list[dict], verbose: bool = False) -> list[dict]:
    """
    For rows that lack cached CEP coordinates, geocode them and cache.
    Returns rows that have valid coordinates after this step.
    """
    from .database import haversine  # avoid circular at module level

    missing_ceps = {
        r["cep"] for r in rows
        if r["cep"] and get_cep_coords(r["cep"]) is None
    }

    if missing_ceps and verbose:
        console.print(f"  [dim]Geocodificando {len(missing_ceps)} CEPs novos...[/dim]")

    for cep in missing_ceps:
        coords = geocode_cep(cep)
        if coords:
            upsert_cep_coords(cep, coords[0], coords[1])
        time.sleep(0.05)  # be kind to BrasilAPI

    return rows


def search_demo(address: str, radius_km: float = 5.0) -> SearchResult:
    """Returns realistic fake data so the UI can be validated without live data."""
    from .geocoder import geocode_address
    lat, lng = geocode_address(address)

    _fake = [
        ("19457844000105", "ITAU UNIBANCO S.A.", "ITAÚ", "05", "Médio/Grande Porte",
         "Praça Alfredo Egydio de Souza Aranha", "100", "Torre Conceição", "Jabaquara", "04344902", "São Paulo", "SP", "(11) 5029-1452", ""),
        ("60746948000112", "BRADESCO S.A.", "BRADESCO", "05", "Médio/Grande Porte",
         "Cidade de Deus", "s/n", "Prédio Novo", "Vila Yara", "06029900", "Osasco", "SP", "(11) 3684-4011", ""),
        ("33000167000101", "PETRÓLEO BRASILEIRO S.A.", "PETROBRAS", "05", "Médio/Grande Porte",
         "Avenida República do Chile", "65", "Edifício Sede", "Centro", "20031912", "Rio de Janeiro", "RJ", "(21) 3224-1510", ""),
        ("00000000000191", "BANCO DO BRASIL S.A.", "BB", "05", "Médio/Grande Porte",
         "Saun Quadra 5 Lote B", "s/n", "Bloco B", "Asa Norte", "70040912", "Brasília", "DF", "(61) 3310-3636", ""),
        ("45543915000181", "MAGAZINE LUIZA S.A.", "MAGALU", "05", "Médio/Grande Porte",
         "Rua Arnaldo Busatto", "1.100", "", "Jardim Nova Franca", "14403270", "Franca", "SP", "(16) 3711-8000", ""),
        ("07526557000100", "LOCALIZA RENT A CAR S.A.", "LOCALIZA", "05", "Médio/Grande Porte",
         "Avenida Abrahão Caram", "1.666", "6º andar", "Pampulha", "31275000", "Belo Horizonte", "MG", "(31) 3247-7000", ""),
        ("11328519000120", "TOTVS S.A.", "TOTVS", "05", "Médio/Grande Porte",
         "Avenida Braz Leme", "1.000", "", "Casa Verde", "02511000", "São Paulo", "SP", "(11) 2099-7000", ""),
        ("02429144000193", "AMBEV S.A.", "AMBEV", "05", "Médio/Grande Porte",
         "Rua Dr. Renato Paes de Barros", "1.017", "4º andar", "Itaim Bibi", "04530001", "São Paulo", "SP", "(11) 2122-1700", ""),
        ("60420390000180", "TELEFONICA BRASIL S.A.", "VIVO", "05", "Médio/Grande Porte",
         "Avenida Engenheiro Luís Carlos Berrini", "1.376", "", "Cidade Monções", "04571936", "São Paulo", "SP", "(11) 3430-3687", ""),
        ("00360305000104", "CAIXA ECONÔMICA FEDERAL", "CAIXA", "05", "Médio/Grande Porte",
         "SBS Quadra 4 Lote 3/4", "s/n", "Bloco A", "Asa Sul", "70092900", "Brasília", "DF", "(61) 3206-9200", ""),
    ]

    empresas = []
    for i, f in enumerate(_fake):
        dist = round(random.uniform(0.3, radius_km * 0.95), 2)
        empresas.append(Empresa(
            cnpj=f[0], razao_social=f[1], nome_fantasia=f[2],
            porte=f[3], porte_desc=f[4],
            logradouro=f[5], numero=f[6], complemento=f[7],
            bairro=f[8], cep=f[9], municipio=f[10], uf=f[11],
            telefone=f[12], email=f[13],
            distancia_km=dist,
            lat=lat + random.uniform(-0.03, 0.03),
            lng=lng + random.uniform(-0.03, 0.03),
            fonte="demo",
        ))

    empresas.sort(key=lambda e: e.distancia_km or 0)
    return SearchResult(
        endereco_buscado=address,
        lat_centro=lat,
        lng_centro=lng,
        raio_km=radius_km,
        total=len(empresas),
        empresas=empresas,
    )


def search(
    address: str,
    radius_km: float = DEFAULT_RADIUS_KM,
    mode: str = "quick",
    limit: int = DEFAULT_LIMIT,
    verbose: bool = True,
) -> SearchResult:
    """
    Find medium/large companies within radius_km of address.

    Args:
        address: Human-readable address (PT-BR).
        radius_km: Search radius in kilometers.
        mode: 'quick' (Overpass) or 'full' (local RF database).
        limit: Max number of results.
        verbose: Print progress messages.
    """
    if verbose:
        console.print(f"\n[bold]Geocodificando endereço:[/bold] {address}")

    lat, lng = geocode_address(address)

    if verbose:
        console.print(f"  [dim]Coordenadas: {lat:.6f}, {lng:.6f}[/dim]")
        console.print(f"  [dim]Modo: {mode} | Raio: {radius_km} km[/dim]\n")

    if mode == "full":
        return _search_full(address, lat, lng, radius_km, limit, verbose)
    else:
        return _search_quick(address, lat, lng, radius_km, limit, verbose)


def _search_quick(
    address: str,
    lat: float,
    lng: float,
    radius_km: float,
    limit: int,
    verbose: bool,
) -> SearchResult:
    from .overpass import search_overpass

    if verbose:
        console.print("[cyan]Consultando OpenStreetMap (Overpass)...[/cyan]")

    try:
        empresas = search_overpass(lat, lng, radius_km, limit=limit)
    except RuntimeError as e:
        console.print(f"  [yellow]! Overpass indisponível:[/yellow] {e}")
        console.print(
            "\n  [bold yellow]Para resultados completos, use o modo full:[/bold yellow]\n"
            "    1. [bold]python main.py import[/bold]  (download único ~5 GB, ~30 min)\n"
            "    2. [bold]python main.py search \"...\" --mode full[/bold]"
        )
        return SearchResult(
            endereco_buscado=address,
            lat_centro=lat,
            lng_centro=lng,
            raio_km=radius_km,
            total=0,
            empresas=[],
        )

    if verbose:
        console.print(f"  [dim]Encontradas {len(empresas)} empresas via OSM.[/dim]")
        if empresas:
            cnpj_count = sum(1 for e in empresas if e.cnpj != "00000000000000")
            console.print(
                f"  [dim]{cnpj_count} com CNPJ identificado, "
                f"{len(empresas) - cnpj_count} sem CNPJ (dados OSM incompletos).[/dim]"
            )
        console.print(
            "  [dim]Nota: modo quick usa OSM (dados incompletos). "
            "Use --mode full para resultados completos.[/dim]"
        )

    return SearchResult(
        endereco_buscado=address,
        lat_centro=lat,
        lng_centro=lng,
        raio_km=radius_km,
        total=len(empresas),
        empresas=empresas,
    )


def _search_full(
    address: str,
    lat: float,
    lng: float,
    radius_km: float,
    limit: int,
    verbose: bool,
) -> SearchResult:
    init_db()

    emp_count = count_empresas()
    if emp_count == 0:
        raise RuntimeError(
            "Banco de dados RF vazio. Execute 'python main.py import' primeiro."
        )

    if verbose:
        console.print(
            f"[cyan]Consultando base RF local "
            f"({emp_count:,} empresas, {count_estabelecimentos():,} estabelecimentos)...[/cyan]"
        )

    rows = search_rf(lat, lng, radius_km, PORTE_MEDIO_GRANDE, limit=limit)

    # geocode CEPs that appeared in results but aren't cached yet
    if rows:
        _geocode_missing_ceps(rows, verbose)
        # re-run after geocoding new CEPs
        rows = search_rf(lat, lng, radius_km, PORTE_MEDIO_GRANDE, limit=limit)

    empresas = [_build_empresa_from_row(r) for r in rows]

    if verbose:
        console.print(f"  [dim]Encontradas {len(empresas)} empresas médio/grande porte.[/dim]")

    return SearchResult(
        endereco_buscado=address,
        lat_centro=lat,
        lng_centro=lng,
        raio_km=radius_km,
        total=len(empresas),
        empresas=empresas,
    )
