import requests, re, json

headers = {"User-Agent": "Mozilla/5.0"}

# dados.gov.br is a Next.js app - try to fetch __NEXT_DATA__ from the HTML
r = requests.get(
    "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj",
    timeout=15, headers=headers
)
print("Status:", r.status_code)

# Extract __NEXT_DATA__ JSON blob
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
if m:
    try:
        data = json.loads(m.group(1))
        # Flatten and look for rfb.gov or zip URLs
        text = json.dumps(data)
        urls = re.findall(r'https?://[^"]+(?:\.zip|rfb\.gov\.br|dados_abertos)[^"]*', text)
        print("Found URLs:")
        for u in urls[:20]:
            print(" ", u)
        # Also dump the props structure
        props = data.get("props", {}).get("pageProps", {})
        print("\nPageProps keys:", list(props.keys())[:15])
        if "dataset" in props:
            ds = props["dataset"]
            print("Dataset keys:", list(ds.keys())[:15])
            for res in ds.get("resources", [])[:5]:
                print("Resource:", res.get("url"), res.get("name"))
    except Exception as e:
        print("JSON error:", e)
        print(m.group(1)[:500])
else:
    print("No __NEXT_DATA__ found")
    # Look for API calls in script tags
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
    for s in scripts[:3]:
        if "rfb" in s.lower() or "cnpj" in s.lower():
            print("Script with rfb/cnpj:", s[:300])
