import requests, sys

r = requests.get(
    "https://raw.githubusercontent.com/cnpja/sdk-nodejs/master/README.md",
    timeout=10,
    headers={"User-Agent": "Mozilla/5.0"}
)
# Write to file to avoid encoding issues
with open("cnpja_readme.txt", "w", encoding="utf-8") as f:
    f.write(r.text)
print("Saved", len(r.text), "chars")
