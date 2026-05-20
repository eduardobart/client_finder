import requests, time

headers = {"User-Agent": "Mozilla/5.0"}

# Try RF file via alternative domains/paths
urls = [
    "https://www.receita.fazenda.gov.br/pessoajuridica/cnpj/cnpjreva/cnpjreva_solicitacao.asp",
    "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/consultas/dados-publicos-cnpj",
    "https://arquivos.receitafederal.gov.br/CNPJ/dados_abertos_cnpj/2025-04/",
    "https://cdn.rfb.gov.br/CNPJ/dados_abertos_cnpj/2025-04/",
]

for url in urls:
    try:
        r = requests.head(url, timeout=10, headers=headers, allow_redirects=True)
        print(f"{r.status_code}  {url}")
    except Exception as e:
        s = str(e)
        print(f"{'TO' if 'timed' in s else 'ERR'}  {url[:80]}")
    time.sleep(0.5)

# Also check if ReceitaWS has a bulk endpoint
print("\n--- ReceitaWS endpoints ---")
for ep in ["/", "/v1/", "/v1/status"]:
    try:
        r = requests.get("https://receitaws.com.br" + ep, timeout=8, headers=headers)
        print(f"{r.status_code}  receitaws.com.br{ep}  — {r.text[:100]}")
    except Exception as e:
        print(f"ERR  receitaws{ep}")
