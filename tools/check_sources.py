import requests, re

r = requests.get(
    "https://brasil.io/dataset/socios-brasil/files/",
    timeout=10,
    headers={"User-Agent": "Mozilla/5.0"}
)
print("Status:", r.status_code)
print("URL:", r.url)

# Look for download links in any form
patterns = [
    r'href="([^"]+\.gz)"',
    r'href="([^"]+\.zip)"',
    r'data-[^=]*url[^=]*="([^"]+)"',
    r'"(https?://data\.brasil\.io[^"]*)"',
    r'href="(/dataset/socios-brasil/files/[^"]*)"',
]
found = set()
for pat in patterns:
    for m in re.findall(pat, r.text):
        found.add(m)

for l in sorted(found):
    print("LINK:", l)

# Also dump snippet of page to understand structure
print("\n--- PAGE SNIPPET ---")
print(r.text[:2000])
