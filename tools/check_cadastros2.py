import requests, re

headers = {"User-Agent": "Mozilla/5.0"}

# Check the cadastros page body text for any file links or mentions of CNPJ data
r = requests.get(
    "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos/cadastros",
    timeout=15, headers=headers
)

# Strip HTML and look for text content
text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', ' ', text)
text = re.sub(r'\s+', ' ', text)

# Print chunk that mentions CNPJ or dados
for m in re.finditer(r'.{0,50}(CNPJ|dados.abertos|estabelecimento|empresa|cadastro).{0,200}', text, re.IGNORECASE):
    print(m.group()[:300])
    print("---")

# Also check the orientacao-tributaria/cadastros page which might have the actual data link
print("\n\n=== orientacao-tributaria/cadastros ===")
r2 = requests.get(
    "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros",
    timeout=15, headers=headers
)
links2 = re.findall(r'href=["\']([^"\']+)["\']', r2.text)
for l in links2:
    if any(x in l.lower() for x in ["cnpj", "dados", "aberto", "zip", "csv", "estabelecimento"]):
        print(f"  {l[:150]}")
