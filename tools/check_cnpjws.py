import requests, json

base = "https://publica.cnpj.ws"
headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Check if cnpj.ws has any search endpoints
endpoints = [
    "/cnpj/search?q=paulista+sao+paulo",
    "/municipios",
    "/atividades",
]
for ep in endpoints:
    try:
        r = requests.get(base + ep, headers=headers, timeout=8)
        print(f"{ep}: {r.status_code} — {r.text[:200]}")
    except Exception as e:
        print(f"{ep}: ERRO — {e}")

# Check the full CNPJ response structure from cnpj.ws
print("\n--- cnpj.ws structure for Petrobras ---")
r = requests.get(f"{base}/cnpj/33000167000101", headers=headers, timeout=8)
if r.status_code == 200:
    d = r.json()
    print("Keys:", list(d.keys()))
    # Look for porte, size, address fields
    for key in ["porte", "descricao_porte", "natureza_juridica", "logradouro",
                "municipio", "cep", "situacao_cadastral"]:
        print(f"  {key}:", d.get(key, "N/A"))
    # Check estabelecimento
    estab = d.get("estabelecimento", {})
    if estab:
        print("Estabelecimento keys:", list(estab.keys())[:10])
        for key in ["logradouro", "numero", "bairro", "cep", "municipio", "uf",
                    "situacao_cadastral", "ddd1", "telefone1"]:
            print(f"  estab.{key}:", estab.get(key, "N/A"))
