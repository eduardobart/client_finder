import requests, json, re, time

headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Check CNPJA on GitHub (they might have docs there)
gh_urls = [
    "https://api.github.com/search/repositories?q=cnpja&sort=stars&order=desc",
    "https://raw.githubusercontent.com/cnpja/sdk-node/main/README.md",
    "https://raw.githubusercontent.com/cnpja/cnpja-node/main/README.md",
]

for url in gh_urls:
    time.sleep(1)
    r = requests.get(url, timeout=10, headers=headers)
    print(f"{r.status_code}  {url[:70]}")
    if r.status_code == 200:
        if url.endswith(".md"):
            # Print README for pricing info
            text = r.text
            for m in re.finditer(r".{0,50}(pric|plano|gratu|free|R\$|\$\d|credi).{0,200}", text, re.IGNORECASE):
                print("  ", m.group()[:280])
        else:
            d = r.json()
            items = d.get("items", [])[:5]
            for item in items:
                print(f"  {item.get('full_name')} — {item.get('description', '')[:80]}")
    print()
