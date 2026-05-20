import requests, re

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(
    "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos",
    timeout=15, headers=headers, allow_redirects=True
)
print(f"Status: {r.status_code} URL: {r.url}")

# Print all links
links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
seen = set()
for l in links:
    if l in seen:
        continue
    seen.add(l)
    low = l.lower()
    if any(x in low for x in ["cnpj", "rfb.gov", "zip", "csv", "download", "aberto", "dados"]):
        print(f"  {l[:150]}")

# Also print raw text around "cnpj" mentions
text = re.sub(r'<[^>]+>', ' ', r.text)
text = re.sub(r'\s+', ' ', text)
for m in re.finditer(r'.{0,100}cnpj.{0,150}', text, re.IGNORECASE):
    print("\nSNIPPET:", m.group()[:250])
