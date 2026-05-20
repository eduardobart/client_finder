import requests, time

headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}

# Try every possible RF / gov.br URL for CNPJ open data
urls = [
    # Official RF data page
    "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/consultas/dados-publicos-cnpj",
    # Direct data URLs with different dates
    "https://dados.rfb.gov.br/CNPJ/dados_abertos_cnpj/2025-04/",
    "https://dados.rfb.gov.br/CNPJ/dados_abertos_cnpj/2025-03/",
    "https://dados.rfb.gov.br/CNPJ/dados_abertos_cnpj/2024-12/",
    # Alternative RF subdomains
    "https://dadosabertos.rfb.gov.br/CNPJ/dados_abertos_cnpj/2025-04/",
    "https://www.rfb.gov.br/CNPJ/dados_abertos_cnpj/2025-04/",
    # Portal dados.gov.br
    "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj",
    # receitafederal.gov.br
    "https://www.receitafederal.gov.br/",
    # Check if gov.br RF page has link to files
    "https://www.gov.br/receitafederal/pt-br",
]

for url in urls:
    try:
        r = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
        print(f"{r.status_code}  {r.url[:80]}")
        if "dados_abertos" in r.url or "cnpj" in r.url.lower():
            # Print links to data files
            import re
            links = re.findall(r'https?://[^\s"\'<>]+\.zip', r.text)
            for l in links[:5]:
                print(f"      ZIP: {l}")
    except Exception as e:
        s = str(e)
        tag = "TO" if "timed" in s else "ERR"
        print(f"{tag}  {url[:80]}")
    time.sleep(0.3)
