import requests, json

headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Try different CKAN API approaches for dados.gov.br
apis = [
    # Package show by slug
    "https://dados.gov.br/api/3/action/package_show?id=cadastro-nacional-da-pessoa-juridica---cnpj",
    # No auth - try with .json suffix
    "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj.json",
    # Try the dataset JSON view
    "https://dados.gov.br/api/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj",
    # Try the CKAN portal data endpoint
    "https://dados.gov.br/api/publico/conjuntos-dados?q=cnpj&qtd=5",
    # Direct resource search
    "https://dados.gov.br/api/3/action/current_package_list_with_resources?limit=5",
]

for url in apis:
    try:
        r = requests.get(url, timeout=10, headers=headers)
        print(f"{r.status_code}  {url[:80]}")
        if r.status_code == 200:
            try:
                d = r.json()
                print(json.dumps(d, indent=2, ensure_ascii=False)[:2000])
            except:
                print(r.text[:500])
        else:
            print(f"  -> {r.text[:200]}")
    except Exception as e:
        print(f"ERR  {url[:60]}: {e}")
    print()
