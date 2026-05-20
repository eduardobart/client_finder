import requests, re

headers = {"User-Agent": "Mozilla/5.0"}

# Try the specific CNPJ dados abertos sub-page
urls = [
    "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos/cadastros/cnpj",
    "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos/cnpj",
]

for url in urls:
    r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
    print(f"\n{r.status_code} {r.url}")

    # Find ALL links including rfb.gov.br, dados, zip
    all_links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
    for l in all_links:
        if any(x in l.lower() for x in ["rfb", "zip", "csv", "dados_abertos", "cnpj/2025", "cnpj/2024"]):
            print(f"  FILE: {l}")

    # Also find URLs in the page text/javascript
    js_urls = re.findall(r'"(https?://[^"]+dados_abertos_cnpj[^"]+)"', r.text)
    for u in js_urls:
        print(f"  JS: {u}")

    # Print the main body text
    text = re.sub(r'<[^>]+>', ' ', r.text)
    text = re.sub(r'\s+', ' ', text)
    # Find 2000 chars around "CNPJ"
    idx = text.find("CNPJ")
    if idx > 0:
        print("TEXT:", text[max(0,idx-100):idx+500])
