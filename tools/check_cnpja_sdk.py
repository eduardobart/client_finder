import requests, re, time

headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json, text/plain"}

# Check CNPJA's official SDK repo
urls = [
    "https://raw.githubusercontent.com/cnpja/sdk-nodejs/main/README.md",
    "https://raw.githubusercontent.com/cnpja/sdk-nodejs/master/README.md",
    "https://raw.githubusercontent.com/rfoel/cnpja/main/README.md",
    # Their npm package might have pricing info
    "https://registry.npmjs.org/cnpja/latest",
]

for url in urls:
    time.sleep(0.5)
    r = requests.get(url, timeout=10, headers=headers)
    print(f"{r.status_code}  {url[:80]}")
    if r.status_code == 200:
        text = r.text
        if "README" in url:
            # Look for pricing/plan/free mentions and endpoint docs
            for m in re.finditer(r".{0,50}(pric|plano|gratu|free|R\$|\$\d|credi|limit|geocod|radius|raio|coordena).{0,200}", text, re.IGNORECASE):
                print("  MATCH:", m.group()[:250])
            # Also print first 1000 chars
            print("  FIRST 800 chars:\n", text[:800])
        elif "npmjs" in url:
            import json
            d = json.loads(text)
            print("  Description:", d.get("description", ""))
            print("  Homepage:", d.get("homepage", ""))
        print()
