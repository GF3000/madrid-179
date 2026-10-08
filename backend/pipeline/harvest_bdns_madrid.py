import json,urllib.request,sys,time
B="https://www.infosubvenciones.es/bdnstrans/api"
def get(u):
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"datathon-cam"}),timeout=120))
        except Exception as e: time.sleep(2*(i+1)); err=e
    raise err
def harvest(ep,out,extra=""):
    p=0; rows=[]
    while True:
        d=get(f"{B}/{ep}/busqueda?page={p}&pageSize=1000&regiones=27&vpd=GE{extra}")
        rows+=d["content"]; print(ep,len(rows),d["totalElements"],file=sys.stderr)
        if d["last"] or not d["content"]: break
        p+=1
    json.dump(rows,open(out,"w",encoding="utf-8"),ensure_ascii=False)
harvest("convocatorias","data/raw/bdns_convocatorias_madrid.json")
harvest("concesiones","data/raw/bdns_concesiones_madrid.json","&fechaDesde=01/01/2019")
