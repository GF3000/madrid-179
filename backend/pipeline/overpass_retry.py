import json,urllib.request,urllib.parse,time,sys,os
EP=["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter","https://overpass.private.coffee/api/interpreter"]
Q={
"rest_restaurant":'nwr["amenity"="restaurant"](area.a);',
"rest_cafe":'nwr["amenity"="cafe"](area.a);',
"rest_fastfood":'nwr["amenity"="fast_food"](area.a);',
"rest_bar":'nwr["amenity"~"^(bar|pub)$"](area.a);',
"san_hospital":'nwr["amenity"="hospital"](area.a);',
"san_clinic":'nwr["amenity"="clinic"](area.a);',
"san_doctors":'nwr["amenity"="doctors"](area.a);',
"san_pharmacy":'nwr["amenity"="pharmacy"](area.a);',
"viaria_alta_capacidad":'way["highway"~"^(motorway|trunk|motorway_link|trunk_link)$"](area.a);',
"deporte":'nwr["leisure"~"^(sports_centre|pitch|swimming_pool|stadium)$"](area.a);',
}
for k,q in Q.items():
    fn=f"data/raw/osm/{k}.json"
    if os.path.exists(fn): continue
    ql=f'[out:json][timeout:300];area["ISO3166-2"="ES-MD"]->.a;({q});out center tags;'
    done=False
    for rnd in range(3):
        for ep in EP:
            try:
                d=urllib.request.urlopen(urllib.request.Request(ep,data=urllib.parse.urlencode({"data":ql}).encode(),headers={"User-Agent":"datathon-cam"}),timeout=400).read()
                if d[:1]!=b"{": raise Exception("no json")
                open(fn,"wb").write(d); print("ok",k,len(d),ep,file=sys.stderr,flush=True); done=True; break
            except Exception as e: print("fail",k,ep,str(e)[:60],file=sys.stderr,flush=True); time.sleep(10)
        if done: break
        time.sleep(30)
