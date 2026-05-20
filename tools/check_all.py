import requests, time

# Test all potential sources for CNPJ geographic data

tests = [
    # Overpass mirrors (need for OSM business search)
    ("Overpass official",     "https://overpass-api.de/api/interpreter",     "POST", "data=[out:json];node[name](around:100,-23.55,-46.63);out 1;"),
    ("Overpass lz4",          "https://lz4.overpass-api.de/api/interpreter", "POST", "data=[out:json];node[name](around:100,-23.55,-46.63);out 1;"),
    ("Overpass z",            "https://z.overpass-api.de/api/interpreter",   "POST", "data=[out:json];node[name](around:100,-23.55,-46.63);out 1;"),
    ("Overpass kumi",         "https://overpass.kumi.systems/api/interpreter","POST","data=[out:json];node[name](around:100,-23.55,-46.63);out 1;"),
    ("Overpass openstreetmap","https://maps.mail.ru/osm/tools/overpass/api/interpreter","POST","data=[out:json];node[name](around:100,-23.55,-46.63);out 1;"),
    # RF data
    ("RF HTTP (port 80)",     "http://dados.rfb.gov.br/CNPJ/dados_abertos_cnpj/", "GET", None),
    ("RF HTTPS HEAD",         "https://dados.rfb.gov.br/CNPJ/dados_abertos_cnpj/2025-04/", "HEAD", None),
    # Alternative CNPJ APIs
    ("ReceitaWS",             "https://receitaws.com.br/v1/cnpj/00000000000191", "GET", None),
    ("cnpj.ws",               "https://publica.cnpj.ws/cnpj/00000000000191", "GET", None),
    ("brasilapi cnpj",        "https://brasilapi.com.br/api/cnpj/v1/00000000000191", "GET", None),
]

headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

for name, url, method, body in tests:
    try:
        if method == "POST":
            r = requests.post(url, data=body, timeout=8, headers=headers)
        elif method == "HEAD":
            r = requests.head(url, timeout=8, headers=headers)
        else:
            r = requests.get(url, timeout=8, headers=headers)
        print(f"OK  {name:35s} {r.status_code}  ({len(r.content)} bytes)")
    except Exception as e:
        err = str(e)
        if "timed out" in err or "Timeout" in err:
            print(f"TO  {name:35s} TIMEOUT")
        elif "Connection" in err:
            print(f"CON {name:35s} CONN ERROR")
        else:
            print(f"ERR {name:35s} {err[:60]}")
    time.sleep(0.3)
