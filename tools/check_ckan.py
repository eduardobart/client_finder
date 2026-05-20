import requests, json, re

headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Try CKAN API on dados.gov.br
apis = [
    "https://dados.gov.br/api/3/action/package_search?q=cnpj+receita+federal&rows=3",
    "https://dados.gov.br/api/3/action/resource_search?query=name:cnpj&limit=5",
]

for url in apis:
    try:
        r = requests.get(url, timeout=10, headers=headers)
        print(f"{url[:60]}: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(json.dumps(d, indent=2, ensure_ascii=False)[:1500])
    except Exception as e:
        print(f"ERRO: {e}")

# Also check the RF gov.br page for any data links
print("\n--- gov.br RF page links ---")
r = requests.get("https://www.gov.br/receitafederal/pt-br", timeout=10, headers={"User-Agent":"Mozilla/5.0"})
urls = re.findall(r'https?://[^\s"\'<>]+', r.text)
for u in urls:
    if any(x in u.lower() for x in ["cnpj", "dados_abertos", "rfb.gov", "zip", "csv"]):
        print(" ", u[:120])
