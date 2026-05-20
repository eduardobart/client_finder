import requests, re

headers = {"User-Agent": "Mozilla/5.0"}

# Check the RF CNPJ service page for open data links
pages = [
    "https://www.gov.br/receitafederal/pt-br/servicos/cadastro/cnpj",
    "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/consultas/dados-publicos-cnpj",
]

for url in pages:
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        print(f"\n{r.status_code} {r.url[:80]}")
        # Find all external links
        links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
        for l in links:
            if any(x in l.lower() for x in ["cnpj", "rfb", "dados", "zip", "download", "aberto"]):
                if l.startswith("http") or l.startswith("/"):
                    print(f"  {l[:120]}")
    except Exception as e:
        print(f"ERRO: {e}")
