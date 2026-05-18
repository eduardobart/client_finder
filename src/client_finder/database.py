import sqlite3
import math
from contextlib import contextmanager
from .config import DB_PATH, EARTH_RADIUS_KM


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS empresas (
                cnpj_basico TEXT PRIMARY KEY,
                razao_social TEXT NOT NULL,
                porte       TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS estabelecimentos (
                cnpj             TEXT PRIMARY KEY,
                cnpj_basico      TEXT NOT NULL,
                nome_fantasia    TEXT,
                situacao         TEXT NOT NULL,
                tipo_logradouro  TEXT,
                logradouro       TEXT,
                numero           TEXT,
                complemento      TEXT,
                bairro           TEXT,
                cep              TEXT,
                uf               TEXT,
                municipio_cod    TEXT,
                ddd              TEXT,
                telefone         TEXT,
                email            TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_estab_basico   ON estabelecimentos(cnpj_basico);
            CREATE INDEX IF NOT EXISTS idx_estab_cep      ON estabelecimentos(cep);
            CREATE INDEX IF NOT EXISTS idx_estab_situacao ON estabelecimentos(situacao);
            CREATE INDEX IF NOT EXISTS idx_estab_uf       ON estabelecimentos(uf);

            CREATE TABLE IF NOT EXISTS cep_coords (
                cep TEXT PRIMARY KEY,
                lat REAL,
                lng REAL
            );
        """)


def count_empresas() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]


def count_estabelecimentos() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM estabelecimentos").fetchone()[0]


def upsert_cep_coords(cep: str, lat: float, lng: float):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cep_coords(cep, lat, lng) VALUES (?,?,?)",
            (cep, lat, lng),
        )


def get_cep_coords(cep: str) -> tuple[float, float] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT lat, lng FROM cep_coords WHERE cep = ?", (cep,)
        ).fetchone()
        return (row["lat"], row["lng"]) if row else None


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def search_rf(
    lat: float,
    lng: float,
    radius_km: float,
    portes: set[str],
    limit: int = 500,
) -> list[dict]:
    """
    Query local RF database for active medium/large establishments near (lat, lng).
    Only returns companies whose CEP has already been geocoded.
    """
    delta_lat = radius_km / 111.0
    delta_lng = radius_km / (111.0 * math.cos(math.radians(lat)))

    porte_placeholders = ",".join("?" * len(portes))

    sql = f"""
        SELECT
            e.cnpj, e.cnpj_basico, e.nome_fantasia,
            e.tipo_logradouro, e.logradouro, e.numero, e.complemento,
            e.bairro, e.cep, e.uf, e.municipio_cod,
            e.ddd, e.telefone, e.email,
            em.razao_social, em.porte,
            c.lat, c.lng
        FROM estabelecimentos e
        JOIN empresas em ON e.cnpj_basico = em.cnpj_basico
        JOIN cep_coords c ON e.cep = c.cep
        WHERE e.situacao = '02'
          AND em.porte IN ({porte_placeholders})
          AND c.lat BETWEEN ? AND ?
          AND c.lng BETWEEN ? AND ?
        LIMIT ?
    """

    params = (
        *portes,
        lat - delta_lat, lat + delta_lat,
        lng - delta_lng, lng + delta_lng,
        limit * 3,
    )

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    results = []
    for row in rows:
        dist = haversine(lat, lng, row["lat"], row["lng"])
        if dist <= radius_km:
            results.append({"dist": dist, **dict(row)})

    results.sort(key=lambda x: x["dist"])
    return results[:limit]


def get_uncached_ceps_in_uf(uf: str, limit: int = 5000) -> list[str]:
    """Return distinct CEPs for a UF that have no cached coordinates yet."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT e.cep
            FROM estabelecimentos e
            LEFT JOIN cep_coords c ON e.cep = c.cep
            WHERE e.uf = ? AND e.situacao = '02' AND c.cep IS NULL
            LIMIT ?
            """,
            (uf, limit),
        ).fetchall()
    return [r["cep"] for r in rows]
