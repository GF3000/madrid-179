"""Normaliza nombres de municipio de los CSV CAM a codigo INE (5 digitos) -> data/processed/"""
import csv,glob,os,re,unicodedata,collections,json,sys
csv.field_size_limit(10**9)
def rd(p):
    b=open(p,"rb").read()
    for e in("utf-8-sig","cp1252"):
        try:return b.decode(e)
        except:pass
def key(s):
    s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower().strip()
    s=re.sub(r"\s+"," ",s)
    m=re.match(r"^(.*?)\s*\((el|la|los|las)\)$",s) or re.match(r"^(.*?),\s*(el|la|los|las)$",s)
    if m: s=m.group(2)+" "+m.group(1)
    return re.sub(r"[^a-z0-9]+"," ",s).strip()
# maestro limpio: nombres IECM (padron) + codigo INE = 28 + 3 primeros digitos del codigo IECM (4to = digito control)
rows=csv.DictReader(rd("data/raw/cam_municipal/padron_por_sexo.csv").splitlines(),delimiter=";")
cod=[k for k in rows.fieldnames if k.startswith("C")][0]; ter="Territorio"; tt="Tipo territorio"
M={}
for r in rows:
    if r[tt]=="Municipios": M["28"+r[cod][:3]]=r[ter]
sec={"28"+r["municipio_codigo"] for r in csv.DictReader(rd("data/raw/cam_geo/secciones_censales.csv").splitlines(),delimiter=";")}
assert len(M)==179 and set(M)==sec,(len(M),set(M)^sec)
K={}
for c,n in M.items(): K[key(n)]=c
ALIAS={"san lorenzo del escorial":"28131","paracuellos del jarama":"28104","san agustin de guadalix":"28129","navarredonda":"28097","horcajo de la sierra":"28070","villavieja de lozoya":"28182","readuena":"28121","municipio de madrid":"28079","madrid capital":"28079","ayuntamiento de madrid":"28079"}
K.update(ALIAS)
os.makedirs("data/processed/municipal",exist_ok=True)
w=csv.writer(open("data/processed/maestro_municipios.csv","w",newline="",encoding="utf-8-sig"))
w.writerow(["ine5","nombre_iecm","clave_normalizada"]); [w.writerow([c,n,key(n)]) for c,n in sorted(M.items())]
unm=collections.Counter(); st=[]
for f in sorted(glob.glob("data/raw/cam_municipal/*.csv")):
    if f.endswith("_manifest.csv"): continue
    t=rd(f)
    if not t or not t.strip(): continue
    lines=t.splitlines(); d=";" if lines[0].count(";")>=lines[0].count(",") else ","
    rows=list(csv.reader(lines,delimiter=d)); h=rows[0]
    tc=[i for i,x in enumerate(h) if x.lower().startswith("territorio")]
    if not tc: st.append((os.path.basename(f),"sin_columna_territorio",len(rows)-1,0,0)); continue
    i=tc[0]; ne=0; nm=0; out=[["ine5"]+h]
    for r in rows[1:]:
        if len(r)<=i: continue
        c=K.get(key(r[i]),"")
        if c: nm+=1
        elif r[i].strip() and r[i].strip() not in ("Comunidad de Madrid","España"): unm[r[i]]+=1
        out.append([c]+r)
    csv.writer(open("data/processed/municipal/"+os.path.basename(f),"w",newline="",encoding="utf-8-sig"),delimiter=";").writerows(out)
    st.append((os.path.basename(f),"ok",len(rows)-1,nm,len({r[0] for r in out[1:] if r[0]})))
csv.writer(open("data/processed/cobertura_normalizacion.csv","w",newline="",encoding="utf-8-sig")).writerows([["fichero","estado","filas","filas_con_ine5","municipios_distintos"]]+st)
ok=[s for s in st if s[1]=="ok"]; conmun=[s for s in ok if s[3]>0]
print("ficheros",len(st),"con territorio",len(ok),"con >=1 fila municipal",len(conmun),"sin territorio",len(st)-len(ok))
print("filas totales",sum(s[2] for s in ok),"casadas",sum(s[3] for s in ok))
print("no casados (agregados, ver):",unm.most_common(25))
