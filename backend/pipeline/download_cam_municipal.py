import json,re,os,csv,urllib.request,sys
P=json.load(open("data/raw/cam_ckan_catalogo_full.json",encoding="utf-8"))
pat=re.compile(r"municipi|distrito|secci[oó]n censal|barrio|polígono|suelo|renta|afiliad|paro registrado|transacciones|valor tasado|catastr|empresa|establecimientos|turismo rural|banda ancha|cobertura|licencias|alquiler|vivienda",re.I)
man=[]
for p in P:
    if not pat.search(p["title"]): continue
    csvs=[r for r in p.get("resources",[]) if (r.get("format") or "").upper()=="CSV"]
    if not csvs: continue
    r=csvs[0]; fn=f"data/raw/cam_municipal/{p['name'][:80]}.csv"
    st="ok"
    try:
        if not os.path.exists(fn):
            b=urllib.request.urlopen(urllib.request.Request(r["url"],headers={"User-Agent":"datathon-cam"}),timeout=60).read()
            open(fn,"wb").write(b)
        sz=os.path.getsize(fn)
    except Exception as e: st="ERR "+str(e)[:60]; sz=0
    man.append([p["name"],p["title"][:150],r["url"],sz,st]); print(len(man),st,p["name"],file=sys.stderr)
csv.writer(open("data/raw/cam_municipal/_manifest.csv","w",newline="",encoding="utf-8-sig")).writerows([["name","title","url","bytes","status"]]+man)
