import requests

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

pages = [
    ("CNPJA",         "https://cnpja.com/pricing"),
    ("CNPJA planos",  "https://cnpja.com/plans"),
    ("Casa dos Dados","https://casadosdados.com.br/planos"),
    ("ReceitaWS",     "https://receitaws.com.br/"),
    ("cnpj.ws",       "https://cnpj.ws/"),
]

for name, url in pages:
    try:
        r = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
        print(f"\n=== {name} ({r.status_code}) ===")
        # Print text content (strip HTML tags roughly)
        import re
        text = re.sub(r"<[^>]+>", " ", r.text)
        text = re.sub(r"\s+", " ", text)
        # Find price mentions
        prices = re.findall(r"R\$[\s\d\.,]+|USD[\s\d\.,]+|\$[\d\.,]+|\d+[,\.]\d{2}\s*/\s*m[eê]s", text, re.IGNORECASE)
        print("Precos encontrados:", prices[:15])
        # Print surrounding context for price mentions
        for p in re.finditer(r"(R\$[\s\d\.,]{2,20}|plano|plan|free|gratuito|credito|credit)", text, re.IGNORECASE):
            start = max(0, p.start()-60)
            end = min(len(text), p.end()+80)
            print(f"  ...{text[start:end]}...")
            break
    except Exception as e:
        print(f"{name}: ERRO — {e}")
