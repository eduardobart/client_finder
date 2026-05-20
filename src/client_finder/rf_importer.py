"""
Downloads and imports Receita Federal CNPJ open data into local SQLite.

RF data URL pattern:
  https://dados.rfb.gov.br/CNPJ/dados_abertos_cnpj/{YYYY-MM}/Empresas{0-9}.zip
  https://dados.rfb.gov.br/CNPJ/dados_abertos_cnpj/{YYYY-MM}/Estabelecimentos{0-9}.zip

Columns have no header row; encoding is Latin-1; separator is semicolon.
"""

import csv
import io
import zipfile
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm
from rich.console import Console

from .config import (
    RF_BASE_URL, DATA_DIR, DB_PATH,
    EMP_COLS, ESTAB_COLS,
    PORTE_MEDIO_GRANDE, SITUACAO_ATIVA,
)
from .database import init_db, get_conn

console = Console()

_BATCH = 50_000


def _latest_rf_date() -> str:
    """Return the most recent available RF data month string (YYYY-MM)."""
    today = datetime.today()
    for delta in range(0, 6):
        candidate = today - timedelta(days=30 * delta)
        ym = candidate.strftime("%Y-%m")
        url = f"{RF_BASE_URL}/{ym}/Empresas0.zip"
        try:
            r = requests.head(url, timeout=10)
            if r.status_code == 200:
                return ym
        except Exception:
            pass
    # fallback: hardcode a known good date
    return "2025-04"


def _download_file(url: str, dest: Path, desc: str):
    """Stream-download a file with a progress bar."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        console.print(f"  [dim]Já existe: {dest.name}[/dim]")
        return
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    with open(dest, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc=desc, leave=False
    ) as bar:
        for chunk in r.iter_content(chunk_size=1024 * 256):
            f.write(chunk)
            bar.update(len(chunk))


def _import_empresas(zip_path: Path):
    """Import Empresas CSV from a zip file — inserts only médio/grande porte."""
    buf: list[tuple] = []

    with zipfile.ZipFile(zip_path) as zf:
        fname = zf.namelist()[0]
        with zf.open(fname) as raw:
            reader = csv.reader(
                io.TextIOWrapper(raw, encoding="latin-1"),
                delimiter=";",
                quotechar='"',
            )
            with get_conn() as conn:
                for row in reader:
                    if len(row) < 6:
                        continue
                    porte = row[EMP_COLS["porte"]].strip()
                    if porte not in PORTE_MEDIO_GRANDE:
                        continue
                    buf.append((
                        row[EMP_COLS["cnpj_basico"]].strip(),
                        row[EMP_COLS["razao_social"]].strip(),
                        porte,
                    ))
                    if len(buf) >= _BATCH:
                        conn.executemany(
                            "INSERT OR IGNORE INTO empresas(cnpj_basico, razao_social, porte) VALUES (?,?,?)",
                            buf,
                        )
                        buf.clear()
                if buf:
                    conn.executemany(
                        "INSERT OR IGNORE INTO empresas(cnpj_basico, razao_social, porte) VALUES (?,?,?)",
                        buf,
                    )


def _import_estabelecimentos(zip_path: Path):
    """Import Estabelecimentos CSV — only active companies already in empresas table."""
    buf: list[tuple] = []
    c = ESTAB_COLS

    with zipfile.ZipFile(zip_path) as zf:
        fname = zf.namelist()[0]
        with zf.open(fname) as raw:
            reader = csv.reader(
                io.TextIOWrapper(raw, encoding="latin-1"),
                delimiter=";",
                quotechar='"',
            )
            with get_conn() as conn:
                for row in reader:
                    if len(row) < 28:
                        continue
                    if row[c["situacao_cadastral"]].strip() != SITUACAO_ATIVA:
                        continue
                    basico = row[c["cnpj_basico"]].strip()
                    ordem = row[c["cnpj_ordem"]].strip()
                    dv = row[c["cnpj_dv"]].strip()
                    cnpj = basico + ordem + dv

                    ddd = row[c["ddd1"]].strip()
                    tel = row[c["telefone1"]].strip()
                    telefone = f"({ddd}) {tel}" if ddd and tel else tel or ddd

                    buf.append((
                        cnpj,
                        basico,
                        row[c["nome_fantasia"]].strip(),
                        SITUACAO_ATIVA,
                        row[c["tipo_logradouro"]].strip(),
                        row[c["logradouro"]].strip(),
                        row[c["numero"]].strip(),
                        row[c["complemento"]].strip(),
                        row[c["bairro"]].strip(),
                        row[c["cep"]].strip(),
                        row[c["uf"]].strip(),
                        row[c["municipio"]].strip(),
                        ddd,
                        telefone,
                        row[c["email"]].strip(),
                    ))
                    if len(buf) >= _BATCH:
                        conn.executemany(
                            """INSERT OR IGNORE INTO estabelecimentos
                            (cnpj, cnpj_basico, nome_fantasia, situacao,
                             tipo_logradouro, logradouro, numero, complemento,
                             bairro, cep, uf, municipio_cod, ddd, telefone, email)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            buf,
                        )
                        buf.clear()
                if buf:
                    conn.executemany(
                        """INSERT OR IGNORE INTO estabelecimentos
                        (cnpj, cnpj_basico, nome_fantasia, situacao,
                         tipo_logradouro, logradouro, numero, complemento,
                         bairro, cep, uf, municipio_cod, ddd, telefone, email)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        buf,
                    )


def _find_local_zip(source_dir: Path, prefix: str, index: int) -> Path | None:
    """Find a ZIP file matching patterns like Empresas0.zip or Empresas0-2025-04.zip."""
    patterns = [
        f"{prefix}{index}.zip",
        f"{prefix}{index}-*.zip",
    ]
    for pat in patterns:
        matches = sorted(source_dir.glob(pat))
        if matches:
            return matches[0]
    return None


def run_import(
    year: int | None = None,
    month: int | None = None,
    source_dir: Path | None = None,
):
    """Full import pipeline: download RF files -> parse -> populate SQLite.

    If source_dir is given, ZIPs are read from that directory instead of
    being downloaded. Useful when the RF server is unreachable.
    """
    init_db()

    if source_dir:
        source_dir = Path(source_dir)
        console.print(f"[bold]Importando dados RF de pasta local:[/bold] {source_dir}")
        console.print(f"[dim]Banco de dados: {DB_PATH}[/dim]")
        console.print()

        console.print("[bold cyan]Fase 1/2 — Empresas (porte médio/grande)[/bold cyan]")
        for i in range(10):
            zip_path = _find_local_zip(source_dir, "Empresas", i)
            if zip_path is None:
                console.print(f"  [yellow]Empresas{i}.zip não encontrado em {source_dir} — pulando[/yellow]")
                continue
            console.print(f"  Importando {zip_path.name}...")
            try:
                _import_empresas(zip_path)
            except Exception as e:
                console.print(f"  [yellow]Aviso: Empresas{i} — {e}[/yellow]")

        console.print()
        console.print("[bold cyan]Fase 2/2 — Estabelecimentos (ativos)[/bold cyan]")
        for i in range(10):
            zip_path = _find_local_zip(source_dir, "Estabelecimentos", i)
            if zip_path is None:
                console.print(f"  [yellow]Estabelecimentos{i}.zip não encontrado em {source_dir} — pulando[/yellow]")
                continue
            console.print(f"  Importando {zip_path.name}...")
            try:
                _import_estabelecimentos(zip_path)
            except Exception as e:
                console.print(f"  [yellow]Aviso: Estabelecimentos{i} — {e}[/yellow]")

        console.print()
        console.print("[bold green]OK Import concluído.[/bold green]")
        console.print("[dim]Execute 'search' para buscar empresas por endereço.[/dim]")
        return

    if year and month:
        ym = f"{year:04d}-{month:02d}"
    else:
        console.print("[cyan]Detectando mês mais recente dos dados RF...[/cyan]")
        ym = _latest_rf_date()

    console.print(f"[bold]Importando dados RF de {ym}[/bold]")
    console.print(f"[dim]Banco de dados: {DB_PATH}[/dim]")
    console.print()

    # Step 1: download + import Empresas files (10 shards)
    console.print("[bold cyan]Fase 1/2 — Empresas (porte médio/grande)[/bold cyan]")
    download_errors = 0
    for i in range(10):
        url = f"{RF_BASE_URL}/{ym}/Empresas{i}.zip"
        dest = DATA_DIR / f"Empresas{i}-{ym}.zip"
        console.print(f"  Baixando Empresas{i}.zip...")
        try:
            _download_file(url, dest, f"Empresas{i}")
            console.print(f"  Importando Empresas{i}...")
            _import_empresas(dest)
        except Exception as e:
            download_errors += 1
            console.print(f"  [yellow]Aviso: Empresas{i} — {e}[/yellow]")

    # Step 2: download + import Estabelecimentos files (10 shards)
    console.print()
    console.print("[bold cyan]Fase 2/2 — Estabelecimentos (ativos)[/bold cyan]")
    for i in range(10):
        url = f"{RF_BASE_URL}/{ym}/Estabelecimentos{i}.zip"
        dest = DATA_DIR / f"Estabelecimentos{i}-{ym}.zip"
        console.print(f"  Baixando Estabelecimentos{i}.zip...")
        try:
            _download_file(url, dest, f"Estabelecimentos{i}")
            console.print(f"  Importando Estabelecimentos{i}...")
            _import_estabelecimentos(dest)
        except Exception as e:
            download_errors += 1
            console.print(f"  [yellow]Aviso: Estabelecimentos{i} — {e}[/yellow]")

    console.print()
    if download_errors == 20:
        console.print("[bold red]ERRO: Nenhum arquivo foi baixado.[/bold red]")
        console.print()
        console.print("O servidor dados.rfb.gov.br está inacessível nesta rede.")
        console.print("Alternativas:")
        console.print(f"  1. Baixe os arquivos manualmente pelo navegador:")
        console.print(f"     [cyan]https://dados.rfb.gov.br/CNPJ/dados_abertos_cnpj/{ym}/[/cyan]")
        console.print(f"     Baixe Empresas0.zip a Empresas9.zip e Estabelecimentos0.zip a Estabelecimentos9.zip")
        console.print(f"  2. Salve todos os ZIPs numa pasta (ex: C:\\Downloads\\rf_data)")
        console.print(f"  3. Execute:")
        console.print(f'     [bold]python main.py import --source-dir "C:\\Downloads\\rf_data"[/bold]')
    else:
        console.print("[bold green]OK Import concluído.[/bold green]")
        console.print("[dim]Execute 'search' para buscar empresas por endereço.[/dim]")
