#!/usr/bin/env python3
"""
client_finder — Encontra CNPJs de empresas de médio/grande porte num raio de endereço.

Comandos:
  search  — Busca por endereço (modo rápido via OSM, ou completo via RF)
  import  — Baixa e importa dados abertos da Receita Federal (necessário para --mode full)
  status  — Mostra estado do banco de dados local
"""

import sys
from pathlib import Path

# allow running from project root without install
sys.path.insert(0, str(Path(__file__).parent / "src"))

import click
from rich.console import Console

console = Console()


@click.group()
def cli():
    """client_finder — CNPJs de empresas médio/grande porte por raio geográfico."""


@cli.command()
@click.argument("endereco")
@click.option("--radius", "-r", default=5.0, show_default=True,
              help="Raio de busca em km.")
@click.option("--mode", "-m",
              type=click.Choice(["quick", "full"], case_sensitive=False),
              default="quick", show_default=True,
              help=(
                  "quick = OpenStreetMap/Overpass (sem setup, menos completo). "
                  "full = base RF local (requer 'import', completo)."
              ))
@click.option("--output", "-o",
              type=click.Choice(["table", "json", "csv"], case_sensitive=False),
              default="table", show_default=True,
              help="Formato de saída.")
@click.option("--limit", "-l", default=500, show_default=True,
              help="Número máximo de resultados.")
@click.option("--save", "-s", type=click.Path(), default=None,
              help="Salvar resultado em arquivo (json ou csv).")
@click.option("--demo", is_flag=True, default=False,
              help="Modo demonstração: mostra dados fictícios sem precisar de rede ou import.")
def search(endereco, radius, mode, output, limit, save, demo):
    """Busca empresas médio/grande porte num raio a partir de ENDEREÇO.

    Exemplos:

      python main.py search "Av. Paulista, 1000, São Paulo, SP"

      python main.py search "Rua XV de Novembro, 100, Curitiba" --radius 3 --mode full

      python main.py search "Praça da Sé, São Paulo" --output json --save resultado.json
    """
    from src.client_finder.search import search as do_search, search_demo
    from src.client_finder.output import print_table, to_json, to_csv

    if demo:
        console.print("[yellow bold]*** MODO DEMO — dados ficticios para validacao da tela ***[/yellow bold]\n")
        result = search_demo(endereco, radius_km=radius)
    else:
        try:
            result = do_search(
                address=endereco,
                radius_km=radius,
                mode=mode.lower(),
                limit=limit,
                verbose=True,
            )
        except ValueError as e:
            console.print(f"[bold red]Erro:[/bold red] {e}")
            sys.exit(1)
        except RuntimeError as e:
            console.print(f"[bold red]Erro:[/bold red] {e}")
            sys.exit(1)

    fmt = output.lower()

    if fmt == "table":
        print_table(result)
    elif fmt == "json":
        text = to_json(result)
        if save:
            Path(save).write_text(text, encoding="utf-8")
            console.print(f"[green]Salvo em {save}[/green]")
        else:
            console.print(text)
    elif fmt == "csv":
        text = to_csv(result)
        if save:
            Path(save).write_text(text, encoding="utf-8")
            console.print(f"[green]Salvo em {save}[/green]")
        else:
            console.print(text)

    if fmt == "table" and save:
        # also save as JSON when table is displayed but --save is set
        ext = Path(save).suffix.lower()
        if ext == ".csv":
            Path(save).write_text(to_csv(result), encoding="utf-8")
        else:
            Path(save).write_text(to_json(result), encoding="utf-8")
        console.print(f"[green]Salvo em {save}[/green]")


@cli.command("import")
@click.option("--year", type=int, default=None, help="Ano dos dados RF (ex: 2025).")
@click.option("--month", type=int, default=None, help="Mês dos dados RF (ex: 4).")
@click.option("--yes", "-y", is_flag=True, default=False,
              help="Pular confirmação interativa.")
@click.option("--source-dir", type=click.Path(exists=True, file_okay=False),
              default=None,
              help=(
                  "Pasta com os ZIPs baixados manualmente (Empresas0.zip … "
                  "Estabelecimentos9.zip). Use quando dados.rfb.gov.br estiver "
                  "inacessível."
              ))
def import_data(year, month, yes, source_dir):
    """Baixa e importa dados abertos da Receita Federal.

    Download de ~5 GB por competência. Necessário apenas uma vez.
    Após o import, use 'search --mode full' para resultados completos.

    Se o servidor estiver inacessível, baixe os ZIPs pelo navegador e use:

      python main.py import --source-dir C:\\Downloads\\rf_data
    """
    from src.client_finder.rf_importer import run_import
    from pathlib import Path

    console.print("[bold]client_finder — Import Receita Federal[/bold]")

    if source_dir:
        console.print(f"[cyan]Usando arquivos locais em:[/cyan] {source_dir}\n")
    else:
        console.print(
            "[yellow]Atencao:[/yellow] o download pode levar 30-60 minutos "
            "e requer ~10 GB de espaco em disco.\n"
        )
        if not yes:
            click.confirm("Deseja continuar?", abort=True)

    run_import(year=year, month=month, source_dir=Path(source_dir) if source_dir else None)


@cli.command()
def status():
    """Mostra estado do banco de dados local."""
    from src.client_finder.config import DB_PATH, DATA_DIR
    from src.client_finder.database import init_db, count_empresas, count_estabelecimentos

    console.print("[bold]client_finder — Status[/bold]\n")
    console.print(f"  Banco de dados : {DB_PATH}")
    console.print(f"  Dados brutos   : {DATA_DIR}")
    console.print()

    if not DB_PATH.exists():
        console.print("  [yellow]Banco de dados não encontrado.[/yellow]")
        console.print("  Execute [bold]python main.py import[/bold] para criar.")
        return

    init_db()
    emp = count_empresas()
    est = count_estabelecimentos()

    console.print(f"  Empresas (médio/grande) : {emp:>12,}")
    console.print(f"  Estabelecimentos ativos  : {est:>12,}")

    if emp == 0:
        console.print(
            "\n  [yellow]Base vazia.[/yellow] Execute [bold]python main.py import[/bold]."
        )
    else:
        console.print(
            "\n  [green]OK Base RF carregada.[/green] Use [bold]--mode full[/bold] para resultados completos."
        )


@cli.command("geocode-ceps")
@click.argument("uf")
@click.option("--batch", default=200, show_default=True,
              help="Número de CEPs a geocodificar por execução.")
def geocode_ceps(uf, batch):
    """Pré-geocodifica CEPs de um estado (acelera buscas no --mode full).

    Executa antes da primeira busca para pré-popular o cache de coordenadas.
    Pode ser chamado várias vezes; retoma de onde parou.

    Exemplo:
      python main.py geocode-ceps SP --batch 500
    """
    from src.client_finder.database import init_db, get_uncached_ceps_in_uf, upsert_cep_coords
    from src.client_finder.geocoder import geocode_cep
    import time

    init_db()
    uf = uf.upper()

    ceps = get_uncached_ceps_in_uf(uf, limit=batch)
    if not ceps:
        console.print(f"[green]OK Todos os CEPs de {uf} já estão geocodificados.[/green]")
        return

    console.print(f"[bold]Geocodificando {len(ceps)} CEPs de {uf}...[/bold]")
    ok, fail = 0, 0
    for cep in ceps:
        coords = geocode_cep(cep)
        if coords:
            upsert_cep_coords(cep, coords[0], coords[1])
            ok += 1
        else:
            fail += 1
        time.sleep(0.05)

    console.print(f"  [green]OK {ok} geocodificados[/green], [yellow]{fail} falhou[/yellow].")
    remaining = get_uncached_ceps_in_uf(uf, limit=1)
    if remaining:
        console.print(f"  Ainda há CEPs pendentes. Execute novamente para continuar.")


if __name__ == "__main__":
    cli()
