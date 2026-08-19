import requests, json, time, sys

HEADERS = {"User-Agent": "njblackpress-research/1.0 (contact: amditisj@montclair.edu)"}

def get(url, params=None, timeout=25):
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r

def ia_search(q):
    url = "https://archive.org/advancedsearch.php"
    params = {"q": q, "fl[]": ["identifier","title","date"], "rows": 10, "output": "json"}
    r = get(url, params)
    return r.json().get("response", {}).get("docs", [])

def ia_metadata(identifier):
    r = get(f"https://archive.org/metadata/{identifier}")
    return r.json()

def ca_titles(name):
    r = get("https://chroniclingamerica.loc.gov/search/titles/results/", {"terms": name, "format": "json"})
    return r.json()

def ca_pages(name):
    r = get("https://chroniclingamerica.loc.gov/search/pages/results/", {"state":"New Jersey", "proxtext": name, "format": "json"})
    return r.json()

if __name__ == "__main__":
    pub_id = sys.argv[1]
    name = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "ia"
    if mode == "ia":
        print(json.dumps(ia_search(name), indent=2)[:3000])
    elif mode == "ca_titles":
        print(json.dumps(ca_titles(name), indent=2)[:3000])
    elif mode == "ca_pages":
        print(json.dumps(ca_pages(name), indent=2)[:3000])
