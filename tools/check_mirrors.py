import requests, time

headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}

tests = [
    # Internet Archive
    ("archive.org RF empresas",  "https://archive.org/search?query=receita+federal+cnpj+empresas&output=json"),
    # Kaggle (public dataset listing)
    ("kaggle cnpj dataset",      "https://www.kaggle.com/api/v1/datasets/list?search=cnpj+receita+federal&maxResults=3"),
    # Any known S3 mirrors
    ("hubspot RF mirror",        "https://hubdata.s3.amazonaws.com/cnpj/"),
    # Direct RF sub-domains
    ("servicos.rfb.gov.br",      "https://servicos.rfb.gov.br/"),
    ("www.receita.fazenda.gov.br","https://www.receita.fazenda.gov.br/"),
    ("idg.receita.fazenda.gov.br","https://idg.receita.fazenda.gov.br/"),
]

for name, url in tests:
    try:
        r = requests.head(url, timeout=8, headers=headers, allow_redirects=True)
        print(f"OK  {name:40s} {r.status_code}")
    except Exception as e:
        s = str(e)
        tag = "TO" if "timed out" in s or "Timeout" in s else "ERR"
        print(f"{tag}  {name:40s} {s[:70]}")
    time.sleep(0.3)
