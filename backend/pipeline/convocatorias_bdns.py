"""Convocatorias abiertas para pymes y autónomos con ámbito en la Comunidad de Madrid (BDNS), para «Dónde abrir».

No dependen del municipio (son estatales o de la Comunidad): se muestran según el negocio que describe el usuario,
nunca entran en el modelo.

Pasos:
  1. descargar   Búsqueda en la API pública de la BDNS (sin clave) con el filtro oficial de beneficiario
                 «PYME y personas físicas que desarrollan actividad económica» (tiposBeneficiario=3), regiones España,
                 ES3, ES30 y ES300, desde --desde; se quedan las estatales y las de la Comunidad de Madrid, y se pide el
                 detalle de cada una (plazo, «abierto», finalidad, tipo de convocatoria…).
                 → data/raw/bdns_pymes_detalle_<fecha>.json
  2. candidatas  Abiertas a la fecha (abierto=true o fin de solicitud >= fecha), sin agricultura ni pesca.
                 → lotes para revisar (la etiqueta «concesión directa instrumental» no sirve para saber si se puede
                 pedir y hay plazos sin fecha: cada candidata se revisa una a una).
  3. fusionar    Une la revisión (la de 2026-10-19 está en data/processed/bdns_revision_2026-10-19.json: tres
                 subagentes revisaron un lote cada uno y luego hubo una pasada manual, marcada en «revisor») (JSON con solicitable / abierta / encaja_oficina / perfiles / titulo / para_quien /
                 motivo por «num») y deja las que pasan las tres comprobaciones.
                 → data/processed/convocatorias_abiertas.csv

Uso:
  python -I backend/pipeline/convocatorias_bdns.py descargar [--desde 01/10/2025]
  python -I backend/pipeline/convocatorias_bdns.py candidatas --fecha 2026-10-19 --salida <dir>
  python -I backend/pipeline/convocatorias_bdns.py fusionar --fecha 2026-10-19 --revision <dir>/revision_*.json
"""
import argparse
import glob
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pandas as pd

API = "https://www.infosubvenciones.es/bdnstrans/api"
FICHA = "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias/{}"
REGIONES = [1, 25, 26, 27]  # ES España, ES3 Comunidad de Madrid, ES30 y ES300 Madrid (/api/regiones)
PYME = 3  # /api/beneficiarios: «PYME y personas físicas que desarrollan actividad económica»
RAW = Path("data/raw")
SALIDA = Path("data/processed/convocatorias_abiertas.csv")


def _json(url, intentos=4):
    for k in range(intentos):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))
        except Exception:
            if k == intentos - 1:
                raise
            time.sleep(1.5 * (k + 1))


def descargar(desde):
    todas = {}
    for r in REGIONES:
        p = 0
        while True:
            d = _json(f"{API}/convocatorias/busqueda?vpd=GE&page={p}&pageSize=500&fechaDesde={desde}"
                      f"&tiposBeneficiario={PYME}&regiones={r}")
            for x in d["content"]:
                todas.setdefault(x["numeroConvocatoria"], x)
            if d.get("last", True):
                break
            p += 1
    sel = [x for x in todas.values()
           if x["nivel1"] == "ESTADO" or (x["nivel1"] == "AUTONOMICA" and "MADRID" in x["nivel2"].upper())]
    # la API corta peticiones seguidas: pocas a la vez y con reintentos
    with ThreadPoolExecutor(3) as ex:
        detalles = list(ex.map(lambda x: _json(f"{API}/convocatorias?numConv={x['numeroConvocatoria']}&vpd=GE"), sel))
    salida = RAW / f"bdns_pymes_detalle_{date.today().isoformat()}.json"
    json.dump([x | {"det": d} for x, d in zip(sel, detalles)], salida.open("w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(sel)} convocatorias (estatales y de la Comunidad) -> {salida}")


def _abiertas(fecha):
    datos = json.load(open(RAW / f"bdns_pymes_detalle_{fecha}.json", encoding="utf-8"))
    return [r for r in datos if r["det"]
            and (r["det"].get("abierto") or (r["det"].get("fechaFinSolicitud") or "") >= fecha)
            and "Agricultura" not in (r["det"].get("descripcionFinalidad") or "")]


def fusionar(fecha, patron):
    revision = {x["num"]: x for f in glob.glob(patron) for x in json.load(open(f, encoding="utf-8"))}
    filas = []
    for r in _abiertas(fecha):
        v, d = revision.get(r["numeroConvocatoria"]), r["det"]
        if not v or not (v["solicitable"] == v["abierta"] == v["encaja_oficina"] == "si"):
            continue
        filas.append({"num": r["numeroConvocatoria"], "nivel": "Estado" if r["nivel1"] == "ESTADO" else "Comunidad de Madrid",
                      "organo": r["nivel3"], "titulo": v["titulo"], "para_quien": v["para_quien"],
                      "perfiles": ",".join(v["perfiles"]), "fin_solicitud": d.get("fechaFinSolicitud") or "",
                      "presupuesto": d.get("presupuestoTotal") or "", "finalidad": d.get("descripcionFinalidad") or "",
                      "nota": v.get("nota", ""), "max_habitantes": v.get("max_habitantes") or "", "url": FICHA.format(r["numeroConvocatoria"]), "fecha_consulta": fecha})
    pd.DataFrame(filas).to_csv(SALIDA, sep=";", index=False, encoding="utf-8-sig")
    print(f"{len(filas)} convocatorias abiertas y solicitables -> {SALIDA}")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("paso", choices=["descargar", "candidatas", "fusionar"])
    a.add_argument("--desde", default="01/10/2025")
    a.add_argument("--fecha", default=date.today().isoformat())
    a.add_argument("--salida")
    a.add_argument("--revision")
    args = a.parse_args()
    if args.paso == "descargar":
        descargar(args.desde)
    elif args.paso == "candidatas":
        cand = _abiertas(args.fecha)
        Path(args.salida).mkdir(parents=True, exist_ok=True)
        json.dump(cand, open(Path(args.salida) / "candidatas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{len(cand)} candidatas")
    else:
        fusionar(args.fecha, args.revision)
