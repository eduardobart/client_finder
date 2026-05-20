import requests, json, time

headers = {
    "User-Agent": "python-requests/2.28",
    "Accept": "application/json",
}

time.sleep(3)

# Try CNPJA API directly - openapi spec and endpoints
endpoints = [
    "https://api.cnpja.com/openapi.json",
    "https://api.cnpja.com/swagger.json",
    "https://api.cnpja.com/",
    "https://api.cnpja.com/office/33683111000107",  # Petrobras CNPJ - test free endpoint
]

for url in endpoints:
    try:
        r = requests.get(url, timeout=10, headers=headers)
        print(f"{r.status_code}  {url}")
        if r.status_code in (200, 401, 403):
            try:
                print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:1500])
            except:
                print(r.text[:500])
        print()
    except Exception as e:
        print(f"ERR  {url}: {e}\n")
    time.sleep(1)
