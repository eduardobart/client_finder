import requests, re, time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124",
    "Accept": "text/html,application/json",
}

time.sleep(4)

# API reference and pricing
urls = [
    "https://cnpja.com/api/reference",
    "https://cnpja.com/pricing",
]

for url in urls:
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        print(f"\n{'='*60}")
        print(f"{r.status_code}  {r.url}")
        if r.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text)
            print(text[:4000])
        else:
            print(r.text[:200])
    except Exception as e:
        print(f"ERRO: {e}")
    time.sleep(2)
