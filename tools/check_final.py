import requests, re, json

headers = {"User-Agent": "Mozilla/5.0"}

# 1. Check RF GitHub
print("=== GitHub RF ===")
gh = requests.get("https://api.github.com/orgs/receita-federal/repos", timeout=8, headers=headers)
print("Status:", gh.status_code, "body:", gh.text[:300])

# 2. Try archive.org wayback API to find what URL the RF used before
print("\n=== Wayback Machine last known good ===")
wb = requests.get(
    "https://archive.org/wayback/available?url=dados.rfb.gov.br/CNPJ/dados_abertos_cnpj/",
    timeout=10, headers=headers
)
if wb.status_code == 200:
    d = wb.json()
    print(json.dumps(d, indent=2))

# 3. Try the dados.gov.br API with a different content-type
print("\n=== dados.gov.br API with API key workaround ===")
# Try unauthenticated but with different headers
r = requests.get(
    "https://dados.gov.br/api/3/action/package_show",
    params={"id": "cadastro-nacional-da-pessoa-juridica---cnpj"},
    headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
    timeout=10
)
print("Status:", r.status_code)
if r.status_code == 200:
    d = r.json()
    for res in d.get("result", {}).get("resources", [])[:10]:
        print("  Resource:", res.get("url"), "|", res.get("name"))

# 4. Check RF news for download URL change announcements
print("\n=== RF news for dados abertos ===")
news = requests.get(
    "https://www.gov.br/receitafederal/pt-br/assuntos/noticias/servicos",
    timeout=10, headers=headers
)
text = re.sub(r'<[^>]+>', ' ', news.text)
text = re.sub(r'\s+', ' ', text)
for m in re.finditer(r'.{0,30}(dados.abertos|cnpj.*download|download.*cnpj).{0,150}', text, re.IGNORECASE):
    print(m.group()[:250])
