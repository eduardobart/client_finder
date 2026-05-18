"""Formats SearchResult for terminal (rich table), JSON, or CSV output."""

import csv
import json
import io
from rich.console import Console
from rich.table import Table
from rich import box
from .models import SearchResult, Empresa

console = Console(width=140, highlight=False)


def _cnpj_fmt(cnpj: str) -> str:
    c = cnpj.zfill(14)
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def print_table(result: SearchResult):
    console.print(
        f"\n[bold green]OK {result.total} empresa(s) encontrada(s)[/bold green] "
        f"em {result.raio_km} km de [italic]{result.endereco_buscado}[/italic]\n"
    )

    if not result.empresas:
        return

    table = Table(box=box.SIMPLE_HEAVY, show_lines=False, expand=False)
    table.add_column("#",            style="dim",    no_wrap=True, width=3)
    table.add_column("CNPJ",         style="cyan",   no_wrap=True, width=20)
    table.add_column("Empresa",      style="bold",   min_width=20, max_width=36, no_wrap=True)
    table.add_column("Município/UF", no_wrap=True,   min_width=16, max_width=22)
    table.add_column("CEP",          no_wrap=True,   width=10)
    table.add_column("Km",           justify="right", style="green", no_wrap=True, width=6)
    table.add_column("Telefone",     no_wrap=True,   width=16)

    for i, e in enumerate(result.empresas, 1):
        cnpj_display = (
            _cnpj_fmt(e.cnpj)
            if e.cnpj and e.cnpj != "00000000000000"
            else "[dim]N/D[/dim]"
        )
        nome = e.nome_fantasia or e.razao_social
        municipio = f"{e.municipio}/{e.uf}" if e.uf else e.municipio

        table.add_row(
            str(i),
            cnpj_display,
            nome[:35],
            municipio[:20],
            e.cep or "",
            f"{e.distancia_km:.2f}" if e.distancia_km is not None else "",
            e.telefone or "",
        )

    console.print(table)

    # detail panel for each result
    console.print()
    for i, e in enumerate(result.empresas, 1):
        logradouro = " ".join(filter(None, [e.logradouro, e.numero, e.complemento]))
        console.print(
            f"  [cyan]{i:>3}.[/cyan] [bold]{e.razao_social}[/bold]"
            + (f" ([italic]{e.nome_fantasia}[/italic])" if e.nome_fantasia and e.nome_fantasia != e.razao_social else "")
        )
        if logradouro:
            console.print(f"       {logradouro}, {e.bairro} — {e.municipio}/{e.uf} — CEP {e.cep}")
        if e.telefone:
            console.print(f"       Tel: {e.telefone}" + (f"  |  {e.email}" if e.email else ""))
        console.print()


def to_json(result: SearchResult, indent: int = 2) -> str:
    def empresa_dict(e: Empresa) -> dict:
        return {
            "cnpj": e.cnpj,
            "cnpj_formatado": _cnpj_fmt(e.cnpj) if e.cnpj != "00000000000000" else None,
            "razao_social": e.razao_social,
            "nome_fantasia": e.nome_fantasia,
            "porte": e.porte,
            "porte_desc": e.porte_desc,
            "endereco": {
                "logradouro": e.logradouro,
                "numero": e.numero,
                "complemento": e.complemento,
                "bairro": e.bairro,
                "municipio": e.municipio,
                "uf": e.uf,
                "cep": e.cep,
            },
            "telefone": e.telefone,
            "email": e.email,
            "distancia_km": e.distancia_km,
            "lat": e.lat,
            "lng": e.lng,
            "fonte": e.fonte,
        }

    payload = {
        "busca": {
            "endereco": result.endereco_buscado,
            "lat": result.lat_centro,
            "lng": result.lng_centro,
            "raio_km": result.raio_km,
        },
        "total": result.total,
        "empresas": [empresa_dict(e) for e in result.empresas],
    }
    return json.dumps(payload, ensure_ascii=False, indent=indent)


def to_csv(result: SearchResult) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "cnpj", "cnpj_formatado", "razao_social", "nome_fantasia",
        "porte", "porte_desc",
        "logradouro", "numero", "complemento", "bairro",
        "municipio", "uf", "cep",
        "telefone", "email",
        "distancia_km", "lat", "lng", "fonte",
    ])
    for e in result.empresas:
        writer.writerow([
            e.cnpj,
            _cnpj_fmt(e.cnpj) if e.cnpj != "00000000000000" else "",
            e.razao_social,
            e.nome_fantasia,
            e.porte,
            e.porte_desc,
            e.logradouro,
            e.numero,
            e.complemento,
            e.bairro,
            e.municipio,
            e.uf,
            e.cep,
            e.telefone,
            e.email,
            e.distancia_km,
            e.lat,
            e.lng,
            e.fonte,
        ])
    return buf.getvalue()
