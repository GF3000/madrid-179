import json, csv, urllib.request, urllib.parse, sys
BASE="https://datos.comunidad.madrid/catalogo/api/3/action/package_search"
rows=200; start=0; allp=[]
while True:
    url=f"{BASE}?rows={rows}&start={start}"
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"datathon-cam"}),timeout=120) as r:
        d=json.load(r)["result"]
    allp+=d["results"]; start+=rows
    print(len(allp),d["count"],file=sys.stderr)
    if start>=d["count"]: break
json.dump(allp,open("data/raw/cam_ckan_catalogo_full.json","w",encoding="utf-8"),ensure_ascii=False)
with open("docs/fuentes/cam_ckan_catalogo.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["id","name","title","grupos","organizacion","formatos","n_recursos","modificado","url_portal","urls_recursos","notas"])
    for p in allp:
        res=p.get("resources",[])
        w.writerow([p["id"],p["name"],p["title"],"|".join(g["title"] for g in p.get("groups",[])),
            (p.get("organization") or {}).get("title",""),"|".join(sorted({r.get("format","") for r in res})),len(res),
            p.get("metadata_modified",""),"https://datos.comunidad.madrid/catalogo/dataset/"+p["name"],
            "|".join(r.get("url","") for r in res),(p.get("notes") or "").replace("\n"," ")[:500]])
