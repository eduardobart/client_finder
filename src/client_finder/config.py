from pathlib import Path
import os

APP_DIR = Path(os.environ.get("CLIENT_FINDER_DIR", Path.home() / ".client_finder"))
DB_PATH = APP_DIR / "data.db"
DATA_DIR = APP_DIR / "raw"

NOMINATIM_UA = "ClientFinder/1.0 (opensource)"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
BRASILAPI_BASE = "https://brasilapi.com.br/api"
RF_BASE_URL = "https://dados.rfb.gov.br/CNPJ/dados_abertos_cnpj"

# RF porte codes: '05' = DEMAIS (not ME nor EPP) = médio + grande porte
PORTE_MEDIO_GRANDE = {"05"}
PORTE_MAP = {
    "00": "Não Informado",
    "01": "Micro Empresa",
    "03": "Empresa de Pequeno Porte",
    "05": "Médio/Grande Porte",
}

SITUACAO_ATIVA = "02"
EARTH_RADIUS_KM = 6371.0
DEFAULT_RADIUS_KM = 5.0
DEFAULT_LIMIT = 500

# Estabelecimentos CSV column positions (RF open data, no header)
ESTAB_COLS = {
    "cnpj_basico": 0, "cnpj_ordem": 1, "cnpj_dv": 2,
    "nome_fantasia": 4, "situacao_cadastral": 5,
    "tipo_logradouro": 13, "logradouro": 14, "numero": 15,
    "complemento": 16, "bairro": 17, "cep": 18,
    "uf": 19, "municipio": 20,
    "ddd1": 21, "telefone1": 22,
    "email": 27,
}

# Empresas CSV column positions
EMP_COLS = {
    "cnpj_basico": 0, "razao_social": 1, "porte": 5,
}
