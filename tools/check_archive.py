import requests, json

headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Search archive.org for RF CNPJ data
r = requests.get(
    "https://archive.org/advancedsearch.php",
    params={
        "q": "receita federal cnpj empresas estabelecimentos",
        "fl[]": ["identifier", "title", "date", "downloads"],
        "output": "json",
        "rows": 10,
        "sort[]": "downloads desc",
    },
    headers=headers,
    timeout=10
)
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    for item in data.get("response", {}).get("docs", []):
        print(f"  {item.get('identifier')} — {item.get('title')} ({item.get('date', '')})")
