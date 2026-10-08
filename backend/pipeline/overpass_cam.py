import json,urllib.request,urllib.parse,time,sys
Q={
"coworking":'nwr["office"="coworking"](area.a);nwr["amenity"="coworking_space"](area.a);',
"guarderias":'nwr["amenity"="kindergarten"](area.a);nwr["amenity"="childcare"](area.a);',
"gimnasios":'nwr["leisure"="fitness_centre"](area.a);nwr["leisure"="sports_centre"](area.a);',
"restauracion":'nwr["amenity"~"^(restaurant|cafe|fast_food|bar)$"](area.a);',
"colegios_univ":'nwr["amenity"~"^(school|college|university)$"](area.a);',
"sanidad":'nwr["amenity"~"^(hospital|clinic|doctors)$"](area.a);nwr["healthcare"="centre"](area.a);',
"transporte":'nwr["railway"~"^(station|halt|subway_entrance)$"](area.a);nwr["highway"="bus_stop"](area.a);nwr["public_transport"="station"](area.a);',
"oficinas":'nwr["office"](area.a);',
"parques":'nwr["leisure"~"^(park|garden)$"](area.a);',
"industrial":'nwr["landuse"="industrial"](area.a);nwr["landuse"="commercial"](area.a);nwr["landuse"="retail"](area.a);',
}
for k,q in Q.items():
    ql=f'[out:json][timeout:600];area["ISO3166-2"="ES-MD"]->.a;({q});out center tags;'
    for i in range(3):
        try:
            d=urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter",data=urllib.parse.urlencode({"data":ql}).encode(),headers={"User-Agent":"datathon-cam"}),timeout=700).read()
            open(f"data/raw/osm/{k}.json","wb").write(d); print("ok",k,len(d),file=sys.stderr); break
        except Exception as e: print("retry",k,e,file=sys.stderr); time.sleep(30)
    time.sleep(5)
