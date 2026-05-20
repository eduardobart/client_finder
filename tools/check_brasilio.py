import requests, gzip, csv, io

# Peek at the header of empresas.csv.gz from brasil.io
url = "https://data.brasil.io/dataset/socios-brasil/empresas.csv.gz"
print(f"Fetching header from: {url}")

# Only download first 64KB to read the header
headers = {"User-Agent": "Mozilla/5.0", "Range": "bytes=0-65535"}
r = requests.get(url, headers=headers, timeout=15, stream=True)
print(f"Status: {r.status_code}")
print(f"Content-Range: {r.headers.get('Content-Range', 'n/a')}")
print(f"Content-Type: {r.headers.get('Content-Type', 'n/a')}")

chunk = b""
for c in r.iter_content(65536):
    chunk += c
    if len(chunk) >= 65536:
        break

print(f"Downloaded {len(chunk)} bytes")

try:
    with gzip.open(io.BytesIO(chunk), "rt", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        print("\nColunas:")
        for i, col in enumerate(header):
            print(f"  {i}: {col}")
        # Print first 3 rows
        print("\nPrimeiras linhas:")
        for i, row in enumerate(reader):
            if i >= 3:
                break
            print(row[:10])
except Exception as e:
    print(f"gzip error: {e}")
    # Try without gzip
    try:
        text = chunk.decode("latin-1")
        lines = text.split("\n")[:5]
        for l in lines:
            print(l[:200])
    except Exception as e2:
        print(f"raw error: {e2}")
