import requests, re

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(
    "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos/cadastros",
    timeout=15, headers=headers, allow_redirects=True
)
print(f"Status: {r.status_code}")

# Extract links
links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
seen = set()
for l in links:
    if l in seen:
        continue
    seen.add(l)
    print(f"  {l[:150]}")
