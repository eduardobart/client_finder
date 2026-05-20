import requests, re

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
r = requests.get("https://cnpj.ws/", timeout=10, headers=headers)

text = re.sub(r"<[^>]+>", " ", r.text)
text = re.sub(r"\s+", " ", text)

# Find all price contexts
for m in re.finditer(r"(plano|plan|free|gratuito|starter|basic|premium|pro|\$\d|\bR\$)", text, re.IGNORECASE):
    start = max(0, m.start()-40)
    end = min(len(text), m.end()+200)
    snippet = text[start:end].strip()
    print(snippet)
    print("---")
