import zipfile,csv,io,collections,shapefile,os
from shapely.geometry import shape,Point
from shapely.strtree import STRtree
from pyproj import Transformer
r=shapefile.Reader("data/raw/cam_geo/secciones_shp/Seccionado_2019.shp",encoding="latin-1")
geoms=[];meta=[]
for sr in r.shapeRecords():
    g=shape(sr.shape.__geo_interface__); g=g if g.is_valid else g.buffer(0)
    geoms.append(g); d=sr.record.as_dict(); meta.append(("28"+d["CDMUNI"],"28"+d["CDSECCION"],d["Area_k2"]))
tree=STRtree(geoms); T=Transformer.from_crs(4326,25830,always_xy=True)
area=collections.defaultdict(float)
for a,b,c in meta: area[a]+=c
cnt=collections.Counter(); rows=[]; seen=set()
for mode in ["metro","metroligero","cercanias","emt","interurbanos"]:  # urbanos.zip trae el mismo stops.txt que interurbanos (md5 igual) -> se cuenta una vez como bus CAM
    z=zipfile.ZipFile(f"data/raw/crtm/{mode}.zip")
    if "stops.txt" not in z.namelist(): print("sin stops",mode); continue
    for s in csv.DictReader(io.TextIOWrapper(z.open("stops.txt"),encoding="utf-8-sig")):
        if s.get("location_type") not in ("","0",None): continue   # solo paradas/estaciones-parada, no entradas ni padres
        try: lat,lon=float(s["stop_lat"]),float(s["stop_lon"])
        except: continue
        k=(mode,s["stop_id"]); 
        if k in seen: continue
        seen.add(k); x,y=T.transform(lon,lat); p=Point(x,y); m=None
        for i in tree.query(p):
            if geoms[i].covers(p): m=meta[i]; break
        rows.append([mode,s["stop_id"],s.get("stop_name",""),lat,lon,m[0] if m else "",m[1] if m else "",s.get("zone_id","")])
        if m: cnt[(m[0],mode)]+=1
w=csv.writer(open("data/processed/gtfs_paradas_con_seccion.csv","w",newline="",encoding="utf-8-sig"),delimiter=";")
w.writerow(["modo","stop_id","nombre","lat","lon","ine5","seccion10","zone_id"]); w.writerows(rows)
modes=sorted({m for _,m in cnt})
w=csv.writer(open("data/processed/gtfs_paradas_por_municipio.csv","w",newline="",encoding="utf-8-sig"),delimiter=";")
w.writerow(["ine5","superficie_km2"]+["paradas_"+m for m in modes]+["paradas_total","paradas_total_por_km2"])
for m in sorted(area):
    t=sum(cnt[(m,x)] for x in modes); w.writerow([m,round(area[m],2)]+[cnt[(m,x)] for x in modes]+[t,round(t/area[m],3)])
print(len(rows),"paradas;",modes,"; municipios sin ninguna parada:",sum(1 for m in area if not any(cnt[(m,x)] for x in modes)))
