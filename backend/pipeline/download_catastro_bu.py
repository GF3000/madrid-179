import csv,os,urllib.request,urllib.parse,sys
for t,u in list(csv.reader(open("data/raw/catastro/atom_BU_madrid.csv",encoding="utf-8-sig")))[1:]:
    fn="data/raw/catastro/BU/"+u.rsplit("/",1)[1]
    if os.path.exists(fn): continue
    try:
        p=urllib.parse.urlsplit(u); u2=p._replace(path=urllib.parse.quote(p.path)).geturl()
        open(fn,"wb").write(urllib.request.urlopen(u2,timeout=180).read()); print("ok",t,file=sys.stderr)
    except Exception as e: print("ERR",t,e,file=sys.stderr)
