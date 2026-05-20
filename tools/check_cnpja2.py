import requests, re, time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

pages = [
    "https://cnpja.com/pricing",
    "https://cnpja.com/docs",
    "https://docs.cnpja.com",
    "https://api.cnpja.com",
]

for url in pages:
    time.sleep(2)
    try:
        r = requests.get(url, timeout=12, headers=headers, allow_redirects=True)
        print(f"\n{r.status_code} {r.url}")
        if r.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text)
            # Print 3000 chars of body
            print(text[:3000])
    except Exception as e:
        print(f"ERRO: {e}")
