import json
from pathlib import Path

pubs = json.loads(Path("data/publications.json").read_text(encoding="utf-8"))["publications"]
web = [p for p in pubs if p.get("websiteUrl")]
print("with_website", len(web))
for p in web:
    print(f"{p['id']}\t{p['name']}\t{p.get('websiteUrl')}\tactive={p.get('isActive')}")
print("http_archive")
for p in pubs:
    u = p.get("archiveUrl") or ""
    if str(u).startswith("http"):
        print(f"{p['id']}\t{p['name']}\t{u}")
