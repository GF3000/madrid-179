"""Instrumentos oficiales de apoyo por municipio (PENDIENTES #11): qué programas alcanzan a cada uno, con su fuente.

- LEADER 2023-2027: municipios del anexo I («Ámbito geográfico de actuación», columna LAU_CODE = código INE) de los
  convenios de la Comunidad con los tres Grupos de Acción Local (BOCM de 18-01-2025, núms. 14, 15 y 16).
- Deducciones autonómicas del IRPF por traslado de residencia y por compra de vivienda en municipios de menos de
  2.500 habitantes (Ley 5/2024): la regla usa la población del INE a 1 de enero del año anterior al ejercicio.
- PIR 2022-2026: los municipios de menos de 2.500 habitantes no cofinancian sus actuaciones.

Entrada: data/raw/ayudas/BOCM-20250118-{14,15,16}.PDF (descargar con curl desde bocm.es) y el padrón ya normalizado.
Salida: data/processed/ayudas_oficiales.csv (179 filas, clave ine5).
Ejecutar con `python -I` (solo lee descargas).
"""
import re
from pathlib import Path

import pandas as pd
import pypdfium2 as pdfium

RAW = Path("data/raw/ayudas")
BOCM = "https://www.bocm.es/boletin/CM_Orden_BOCM/2025/01/18/{}.PDF"
CONVENIOS = {  # fichero -> nombre del Grupo de Acción Local
    "BOCM-20250118-14": "ARACOVE (sureste)",
    "BOCM-20250118-15": "GALSINMA (Sierra Norte)",
    "BOCM-20250118-16": "ADI Sierra Oeste (suroeste)",
}
UMBRAL = 2500


def texto(pdf):
    doc = pdfium.PdfDocument(pdf)
    return "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))


def ambito_leader(pdf):
    """Códigos INE del anexo I (entre «ANEXO I» y «ANEXO II»)."""
    t = texto(pdf)
    ini = t.index("ANEXO I\r") if "ANEXO I\r" in t else re.search(r"ANEXO I\s*\n", t).start()
    fin = t.index("ANEXO II", ini)
    return sorted(set(re.findall(r"(?m)^\s*(28\d{3})\b", t[ini:fin])))


maestro = pd.read_csv("data/processed/maestro_municipios.csv", dtype=str, encoding="utf-8-sig").set_index("ine5")
out = pd.DataFrame(index=maestro.index)
out["municipio"] = maestro.nombre_iecm

# --- LEADER ---
out["leader_gal"] = ""
for f, gal in CONVENIOS.items():
    codigos = ambito_leader(RAW / f"{f}.PDF")
    desconocidos = set(codigos) - set(out.index)
    assert not desconocidos, f"{f}: códigos que no están en el maestro: {desconocidos}"
    assert not (out.loc[codigos, "leader_gal"] != "").any(), f"{f}: municipios en dos GAL"
    out.loc[codigos, "leader_gal"] = gal
    print(f"{gal}: {len(codigos)} municipios")
out["leader_fuente"] = out.leader_gal.map(lambda g: "" if not g else BOCM.format(
    next(f for f, n in CONVENIOS.items() if n == g)))

# --- Reglas por población (padrón a 1 de enero) ---
pad = pd.read_csv("data/processed/municipal/padron_por_sexo.csv", sep=";", dtype=str, encoding="utf-8-sig")
pad.columns = ["Anio" if c.startswith("A") and len(c) == 3 else c for c in pad.columns]
pad = pad[(pad["Tipo territorio"] == "Municipios") & (pad.Sexo == "Total") & pad.ine5.notna()]
pad["Valor"] = pd.to_numeric(pad.Valor, errors="coerce")  # «-» = sin dato
anio = pad.Anio.max()
pob = pad[pad.Anio == anio].set_index("ine5").Valor
assert pob.index.is_unique and set(pob.index) == set(out.index)
out["poblacion_1_enero"] = pob.astype(int)
out["anio_padron"] = anio
out["irpf_menos_2500"] = out.poblacion_1_enero < UMBRAL  # aplica al ejercicio siguiente (anio + 1)
out["pir_sin_cofinanciacion"] = out.poblacion_1_enero < UMBRAL
anterior = pad[pad.Anio == str(int(anio) - 1)].set_index("ine5").Valor
print(f"Padrón {anio}: {out.irpf_menos_2500.sum()} municipios < {UMBRAL} hab. "
      f"(con {int(anio) - 1}: {(anterior < UMBRAL).sum()}; la Comunidad cita 73)")
print("En LEADER:", (out.leader_gal != "").sum(), "· LEADER y < 2.500:", ((out.leader_gal != "") & out.irpf_menos_2500).sum())

out.index.name = "ine5"
out.to_csv("data/processed/ayudas_oficiales.csv", sep=";", encoding="utf-8-sig")
print("ok -> data/processed/ayudas_oficiales.csv", len(out))
