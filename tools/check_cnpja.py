import requests, re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Accept": "text/html",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

r = requests.get("https://cnpja.com", timeout=15, headers=headers, allow_redirects=True)
print("Status:", r.status_code, "URL:", r.url[:80])

text = re.sub(r'<[^>]+>', ' ', r.text)
text = re.sub(r'\s+', ' ', text)

# Find price mentions around R$, USD, plano, free
for m in re.finditer(r'.{0,80}(R\$\s*\d|gratu|free|plano|plan|/m[eê]s|\d+\s*req).{0,150}', text, re.IGNORECASE):
    print(m.group()[:280])
    print("---")
