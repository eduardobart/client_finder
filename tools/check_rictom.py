import requests, re

# Check rictom/cnpj-sqlite GitHub releases
url = "https://api.github.com/repos/rictom/cnpj-sqlite/releases"
r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
print("GitHub API status:", r.status_code)

if r.status_code == 200:
    releases = r.json()
    for rel in releases[:3]:
        print(f"\nRelease: {rel.get('name')} ({rel.get('tag_name')}) - {rel.get('published_at')[:10]}")
        for asset in rel.get("assets", []):
            size_mb = asset["size"] / 1024 / 1024
            print(f"  {asset['name']} ({size_mb:.0f} MB) — {asset['browser_download_url']}")
