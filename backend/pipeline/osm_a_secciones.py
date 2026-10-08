"""Asigna POIs OSM (data/raw/osm/*.json) a seccion censal/municipio. Ejecutar con el venv (shapely, pyshp, pyproj)."""
import json,glob,os,csv,collections,shapefile
from shapely.geometry import shape,Point
from shapely.strtree import STRtree
from pyproj import Transformer
r=shapefile.Reader("data/raw/cam_geo/secciones_shp/Seccionado_2019.shp",encoding="latin-1")
geoms=[];meta=[]
for sr in r.shapeRecords():
    g=shape(sr.shape.__geo_interface__)
    if not g.is_valid: g=g.buffer(0)
    geoms.append(g); d=sr.record.as_dict(); meta.append(("28"+d["CDMUNI"],"28"+d["CDSECCION"],d["Area_k2"]))
tree=STRtree(geoms); T=Transformer.from_crs(4326,25830,always_xy=True)
def loc(x):
    s=tree.query(Point(x))
    for i in s:
        if geoms[i].covers(Point(x)): return meta[i]
    return None
out=[];cnt=collections.Counter()
for f in sorted(glob.glob("data/raw/osm/*.json")):
    cat=os.path.basename(f)[:-5]
    for e in json.load(open(f,encoding="utf-8")).get("elements",[]):
        lat=e.get("lat") or (e.get("center") or {}).get("lat"); lon=e.get("lon") or (e.get("center") or {}).get("lon")
        if lat is None: continue
        x,y=T.transform(lon,lat); m=loc((x,y)); t=e.get("tags",{})
        out.append([cat,e["type"],e["id"],lat,lon,round(x),round(y),m[0] if m else "",m[1] if m else "",t.get("name",""),t.get("amenity") or t.get("leisure") or t.get("office") or t.get("landuse") or t.get("highway") or t.get("railway") or ""])
        if m: cnt[(m[0],cat)]+=1
os.makedirs("data/processed",exist_ok=True)
w=csv.writer(open("data/processed/osm_poi_con_seccion.csv","w",newline="",encoding="utf-8-sig"),delimiter=";")
w.writerow(["categoria","osm_tipo","osm_id","lat","lon","x_utm30","y_utm30","ine5","seccion10","nombre","subtipo"]); w.writerows(out)
cats=sorted({c for _,c in cnt}); area=collections.defaultdict(float)
for a,b,c in meta: area[a]+=c
muni=sorted(area)
w=csv.writer(open("data/processed/osm_conteo_por_municipio.csv","w",newline="",encoding="utf-8-sig"),delimiter=";")
w.writerow(["ine5","superficie_km2"]+cats+[c+"_por_km2" for c in cats])
for m in muni: w.writerow([m,round(area[m],2)]+[cnt[(m,c)] for c in cats]+[round(cnt[(m,c)]/area[m],3) for c in cats])
print("POIs",len(out),"sin seccion",sum(1 for o in out if not o[7]),"categorias",cats)
