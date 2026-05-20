import requests, json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://casadosdados.com.br/",
    "Origin": "https://casadosdados.com.br",
    "Content-Type": "application/json",
}

# Casa dos Dados search API (reverse-engineered from their public search page)
payload = {
    "query": {
        "termo": [],
        "atividade_principal": [],
        "natureza_juridica": [],
        "uf": ["SP"],
        "municipio": ["SAO PAULO"],
        "bairro": [],
        "situacao_cadastral": "ATIVA",
        "cep": [],
        "ddd": []
    },
    "range_query": {
        "data_abertura": {"lte": None, "gte": None},
        "capital_social": {"lte": None, "gte": None}
    },
    "extras": {
        "somente_mei": False,
        "excluir_mei": False,
        "com_email": False,
        "incluir_atividade_secundaria": False,
        "com_contato_telefonico": False,
        "somente_fixo": False,
        "somente_celular": False,
        "somente_matriz": False,
        "somente_filial": False
    },
    "page": 1
}

try:
    r = requests.post(
        "https://api.casadosdados.com.br/v2/public/cnpj/pesquisa",
        json=payload,
        headers=headers,
        timeout=10
    )
    print(f"Casa dos Dados API: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    else:
        print(r.text[:500])
except Exception as e:
    print(f"ERRO: {e}")

# Also test receitaws for structure
print("\n--- ReceitaWS structure ---")
r2 = requests.get("https://receitaws.com.br/v1/cnpj/33683111000107", timeout=10)
if r2.status_code == 200:
    d = r2.json()
    print("Fields:", list(d.keys()))
    print("porte:", d.get("porte"))
    print("logradouro:", d.get("logradouro"))
    print("municipio:", d.get("municipio"))
    print("uf:", d.get("uf"))
