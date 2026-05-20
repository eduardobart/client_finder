import requests, re

headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/html,*/*"}

# The dados.gov.br catalog page for CNPJ dataset
r = requests.get(
    "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj",
    timeout=15, headers=headers, allow_redirects=True
)
print("Status:", r.status_code, "URL:", r.url)

# Extract all download/resource links
text = r.text

# Find all URLs in the page
all_urls = re.findall(r'https?://[^\s"\'<>]+', text)
for u in all_urls:
    if any(x in u.lower() for x in ["cnpj", "rfb", "receita", "zip", "csv", "dados_abertos"]):
        print("  LINK:", u[:120])

# Also look for any text mentioning the data location
snippets = re.findall(r'.{0,80}(dados_abertos_cnpj|rfb\.gov\.br|cnpj.*zip).{0,80}', text, re.IGNORECASE)
for s in snippets[:10]:
    print("  SNIPPET:", s[:200])
