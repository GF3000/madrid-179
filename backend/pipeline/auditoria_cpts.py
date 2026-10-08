"""Auditoría de transparencia de la red bayesiana.

1. Recalcula cada CPT a mano (conteos de municipios + prior BDeu) con pandas, sin pgmpy.
2. Compara celda a celda con las CPT que estima pgmpy (BayesianEstimator).
3. Reproduce inferencias sumando la distribución conjunta completa y las compara con VariableElimination.

Salidas: data/processed/auditoria_cpts.xlsx (una hoja por nodo + resumen)
         docs/informe/Calculo_CPTs_CAM.pdf (anexo para el jurado)
Uso: python backend/pipeline/auditoria_cpts.py   (venv con pgmpy, pandas, openpyxl, reportlab)
"""
import sys
from itertools import product

import numpy as np
import pandas as pd

sys.path.insert(0, "backend/pipeline")
import red_bayesiana_viabilidad as rb  # noqa: E402
from pgmpy.inference import VariableElimination  # noqa: E402

TOL = 1e-9
d = pd.read_csv(rb.DATA, sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
disc, umbrales = rb.discretizar(d)
model = rb.construir_modelo(disc, "A")
ESS = rb.ESS


# ---------------------------------------------------------------------------
# 1-2. CPT a mano vs pgmpy
# ---------------------------------------------------------------------------
def cpt_manual(nodo):
    cpd = model.get_cpds(nodo)
    padres = cpd.variables[1:]                      # mismo orden de columnas que pgmpy
    estados = cpd.state_names[nodo]
    combos = list(product(*[cpd.state_names[p] for p in padres])) or [()]
    q, r = len(combos), len(estados)
    alpha = ESS / (q * r)                           # pseudo-conteo BDeu por casilla
    pg = cpd.get_values()                           # (r, q)
    filas = []
    for j, combo in enumerate(combos):
        mask = np.ones(len(disc), bool)
        for p, s in zip(padres, combo):
            mask &= (disc[p] == s).to_numpy()
        sub = disc.loc[mask, nodo]
        n = int(mask.sum())
        fila = {**{p: s for p, s in zip(padres, combo)}, "n_municipios": n}
        for i, s in enumerate(estados):
            c = int((sub == s).sum())
            fila[f"conteo_{s}"] = c
        for i, s in enumerate(estados):
            fila[f"P_manual_{s}"] = (fila[f"conteo_{s}"] + alpha) / (n + r * alpha)
        for i, s in enumerate(estados):
            fila[f"P_pgmpy_{s}"] = float(pg[i, j])
        fila["max_dif"] = max(abs(fila[f"P_manual_{s}"] - fila[f"P_pgmpy_{s}"]) for s in estados)
        filas.append(fila)
    return pd.DataFrame(filas), padres, estados, q, r, alpha


audit = {n: cpt_manual(n) for n in rb.NODOS}
resumen = pd.DataFrame([{
    "nodo": n, "padres": ", ".join(p) or "(raíz)", "estados": len(e), "combinaciones_padres": q,
    "pseudo_conteo_BDeu": a, "celdas": q * len(e), "max_dif_manual_vs_pgmpy": df.max_dif.max(),
    "coincide": df.max_dif.max() < TOL} for n, (df, p, e, q, r, a) in audit.items()])


# ---------------------------------------------------------------------------
# 3. Inferencia por enumeración de la conjunta (sin pgmpy) vs VariableElimination
# ---------------------------------------------------------------------------
nodos = list(rb.NODOS)
est = {n: rb.NODOS[n][1] for n in nodos}
tablas = {}
for n in nodos:
    df, padres, estados, *_ = audit[n]
    tablas[n] = (padres, {tuple(row[p] for p in padres): {s: row[f"P_manual_{s}"] for s in estados}
                          for _, row in df.iterrows()})


def conjunta(asig):
    p = 1.0
    for n in nodos:
        padres, t = tablas[n]
        p *= t[tuple(asig[x] for x in padres)][asig[n]]
    return p


def posterior_enumeracion(evid):
    libres = [n for n in nodos if n not in evid]
    acc = {s: 0.0 for s in est["Viabilidad_Empresarial"]}
    for vals in product(*[est[n] for n in libres]):
        a = {**evid, **dict(zip(libres, vals))}
        acc[a["Viabilidad_Empresarial"]] += conjunta(a)
    z = sum(acc.values())
    return {s: v / z for s, v in acc.items()}, len(list(product(*[est[n] for n in libres])))


ve = VariableElimination(model)
fila_cv = disc.loc["28045"]  # Colmenar Viejo
CONSULTAS = [
    ("Sin evidencia (probabilidad a priori)", {}),
    ("Preferencia: Talento = Alto", {"Talento": "Alto"}),
    ("Preferencias: Coste = Bajo y Acceso ferroviario = Sí", {"Coste_Inmobiliario": "Bajo", "Acceso_Ferroviario": "Si"}),
    ("Municipio completo: Colmenar Viejo (28045)", {n: fila_cv[n] for n in nodos if n != "Viabilidad_Empresarial"}),
]
inferencias = []
for nombre, ev in CONSULTAS:
    man, ncomb = posterior_enumeracion(ev)
    q = ve.query(["Viabilidad_Empresarial"], evidence=ev or None, show_progress=False)
    pg = dict(zip(q.state_names["Viabilidad_Empresarial"], q.values))
    inferencias.append({"consulta": nombre, "evidencia": "; ".join(f"{k}={v}" for k, v in ev.items()) or "-",
                        "combinaciones_sumadas": ncomb,
                        **{f"P_enum_{s}": man[s] for s in man}, **{f"P_pgmpy_{s}": float(pg[s]) for s in man},
                        "max_dif": max(abs(man[s] - pg[s]) for s in man)})
inferencias = pd.DataFrame(inferencias)

# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------
print(resumen[["nodo", "combinaciones_padres", "pseudo_conteo_BDeu", "max_dif_manual_vs_pgmpy", "coincide"]].to_string(index=False))
print(inferencias[["consulta", "combinaciones_sumadas", "P_enum_Alta", "P_pgmpy_Alta", "max_dif"]].to_string(index=False))
assert resumen.coincide.all() and (inferencias.max_dif < TOL).all(), "Discrepancia entre cálculo manual y pgmpy"

xl = "data/processed/auditoria_cpts.xlsx"


def escribir_excel():
    with pd.ExcelWriter(xl, engine="openpyxl") as w:
        resumen.to_excel(w, sheet_name="Resumen", index=False)
        inferencias.to_excel(w, sheet_name="Inferencia", index=False)
        disc.join(d[["nombre_iecm"]]).reset_index().to_excel(w, sheet_name="Datos_discretizados", index=False)
        pd.DataFrame([{"nodo": n, **u, "cortes": str(u["cortes"]), "estados": str(u["estados"]), "conteo": str(u["conteo"])}
                      for n, u in umbrales.items()]).to_excel(w, sheet_name="Umbrales", index=False)
        for n, (df, *_) in audit.items():
            df.to_excel(w, sheet_name=n[:31], index=False)
        for ws in w.book.worksheets:
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(42, max(10, max(len(str(c.value or "")) for c in col) + 2))
            for c in ws[1]:
                c.font = c.font.copy(bold=True)



try:
    escribir_excel()
except PermissionError:
    print(f"AVISO: no se pudo escribir {xl} (¿abierto en Excel?). Ciérralo y vuelve a ejecutar; la verificación sí se ha hecho.")

# ---------------------------------------------------------------------------
# PDF (anexo)
# ---------------------------------------------------------------------------
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402

pdfmetrics.registerFont(TTFont("Segoe", "C:/Windows/Fonts/segoeui.ttf"))
pdfmetrics.registerFont(TTFont("SegoeB", "C:/Windows/Fonts/segoeuib.ttf"))
pdfmetrics.registerFont(TTFont("Mono", "C:/Windows/Fonts/consola.ttf"))
pdfmetrics.registerFontFamily("Segoe", normal="Segoe", bold="SegoeB")
INK, INK2, MUTED, RULE = colors.HexColor("#0b0b0b"), colors.HexColor("#52514e"), colors.HexColor("#898781"), colors.HexColor("#d9d8d0")
GREY_BG, BLUE_BG, GOOD = colors.HexColor("#f4f3ef"), colors.HexColor("#e6effb"), colors.HexColor("#006300")
st = {
    "eyebrow": ParagraphStyle("e", fontName="Segoe", fontSize=8.5, textColor=MUTED, leading=11, spaceAfter=2),
    "title": ParagraphStyle("t", fontName="SegoeB", fontSize=19, leading=23, textColor=INK, spaceAfter=9),
    "lede": ParagraphStyle("l", fontName="Segoe", fontSize=10, leading=14.5, textColor=INK2, spaceAfter=4),
    "h2": ParagraphStyle("h2", fontName="SegoeB", fontSize=12.5, leading=16, textColor=INK, spaceBefore=11, spaceAfter=5),
    "h3": ParagraphStyle("h3", fontName="SegoeB", fontSize=10, leading=13, textColor=INK, spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("b", fontName="Segoe", fontSize=9.4, leading=13.4, textColor=INK, spaceAfter=4),
    "cell": ParagraphStyle("c", fontName="Segoe", fontSize=7.9, leading=10, textColor=INK),
    "head": ParagraphStyle("h", fontName="SegoeB", fontSize=7.4, leading=9.5, textColor=INK2),
    "note": ParagraphStyle("n", fontName="Segoe", fontSize=8, leading=11, textColor=MUTED),
    "formula": ParagraphStyle("f", fontName="Mono", fontSize=8.8, leading=12.5, textColor=INK, leftIndent=6),
    "bullet": ParagraphStyle("bu", fontName="Segoe", fontSize=9.3, leading=13.2, textColor=INK, leftIndent=10, bulletIndent=0, spaceAfter=1.5),
}
P = lambda t, s="cell": Paragraph(str(t), st[s])
W = A4[0] - 36 * mm
f3 = lambda x: f"{x:.4f}".replace(".", ",")
TILDES = {"Especializacion": "Especialización", "Demografico": "Demográfico", "Si": "Sí"}
lab = lambda n: " ".join(TILDES.get(w, w) for w in n.replace("_", " ").split())


def tabla(data, anchos, num_desde=None, resalta=None):
    t = Table(data, colWidths=anchos, repeatRows=1)
    sty = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK2),
           ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE), ("TOPPADDING", (0, 0), (-1, -1), 2.6),
           ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if num_desde is not None:
        sty.append(("ALIGN", (num_desde, 0), (-1, -1), "RIGHT"))
    if resalta:
        sty += [("BACKGROUND", c0, c1, BLUE_BG) for c0, c1 in resalta]
    t.setStyle(TableStyle(sty))
    return t


def caja(flow):
    t = Table([[flow]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GREY_BG), ("LEFTPADDING", (0, 0), (-1, -1), 9),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def tabla_nodo(n):
    df, padres, estados, q, r, alpha = audit[n]
    cab = [P(lab(p), "head") for p in padres] + [P("n", "head")] + [P(f"n {s}", "head") for s in estados] + \
          [P(f"P({s})", "head") for s in estados]
    rows = [cab]
    for _, row in df.iterrows():
        rows.append([P(lab(row[p])) for p in padres] + [P(int(row.n_municipios))] + [P(int(row[f"conteo_{s}"])) for s in estados] +
                    [P(f3(row[f"P_manual_{s}"])) for s in estados])
    npad = len(padres)
    wp, wn = 0.15 * W, 0.075 * W
    anchos = [wp] * npad + [wn] + [wn] * r + [(W - wp * npad - wn * (r + 1)) / r] * r
    pcols = npad + 1 + r
    return tabla(rows, anchos, num_desde=npad, resalta=[((pcols, 1), (-1, -1))])


def pie(c, doc):
    c.saveState(); c.setFont("Segoe", 7.5); c.setFillColor(MUTED)
    c.drawString(18 * mm, 10 * mm, "Datathon CAM · Cálculo de las tablas de probabilidad · octubre 2026")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}"); c.restoreState()


ej = audit["Viabilidad_Empresarial"][0]
ej = ej[(ej.Dinamismo_Demografico == "Alto") & (ej.Especializacion_Servicios == "Alta")].iloc[0]
a_v = audit["Viabilidad_Empresarial"][5]
cv = inferencias.iloc[3]
story = [
    P("ANEXO · TRANSPARENCIA DEL MODELO", "eyebrow"),
    P("Cómo se calculan las probabilidades de la red bayesiana", "title"),
    P("Cada probabilidad del modelo sale de contar municipios reales. Este anexo muestra el procedimiento, todas las tablas con sus "
      "conteos y la verificación independiente frente a la librería pgmpy. El fichero <font face='Mono'>auditoria_cpts.xlsx</font> "
      "contiene los mismos cálculos, con la tabla de los 179 municipios discretizados, para reproducirlos en una hoja de cálculo.", "lede"),
    P("1. Procedimiento", "h2"),
    *[Paragraph(t, st["bullet"], bulletText=f"{i}.") for i, t in enumerate([
        "<b>Discretizar.</b> Cada variable continua se divide en tres estados por sus terciles (unos 60 municipios por estado); el "
        "acceso ferroviario es Sí o No. Cada municipio queda descrito por ocho etiquetas.",
        "<b>Contar.</b> Para cada nodo se cuentan los municipios en cada estado, separados por cada combinación de estados de sus padres.",
        "<b>Suavizar (prior BDeu).</b> Se suma a cada casilla un pseudo-conteo igual, para que ninguna probabilidad sea 0 por falta de "
        f"datos. Equivale a añadir {ESS} municipios imaginarios repartidos de forma uniforme en cada tabla.",
        "<b>Combinar.</b> La puntuación de un municipio es P(Viabilidad = Alta | evidencia), que se obtiene multiplicando las tablas "
        "(regla de la cadena) y sumando sobre lo que no se conoce.",
    ], start=1)],
    Spacer(1, 4),
    caja(P(f"pseudo-conteo α = ESS / (combinaciones de padres × estados) <br/>"
           f"P(estado | padres) = (conteo + α) / (municipios con esos padres + estados × α)", "formula")),
    P("2. Ejemplo resuelto", "h2"),
    P(f"Nodo objetivo <b>Viabilidad Empresarial</b>, con padres Dinamismo Demográfico y Especialización en Servicios: "
      f"9 combinaciones × 3 estados, así que α = {ESS} / 27 = {f3(a_v)}. Entre los {ej.n_municipios} municipios con Dinamismo Alto y "
      f"Especialización Alta, {ej.conteo_Alta} tienen viabilidad Alta, {ej.conteo_Media} Media y {ej.conteo_Baja} Baja.", "body"),
    caja(P(f"P(Alta)  = ({ej.conteo_Alta} + {f3(a_v)}) / ({ej.n_municipios} + 3 × {f3(a_v)}) = <b>{f3(ej.P_manual_Alta)}</b><br/>"
           f"P(Media) = ({ej.conteo_Media} + {f3(a_v)}) / ({ej.n_municipios} + 3 × {f3(a_v)}) = {f3(ej.P_manual_Media)}<br/>"
           f"P(Baja)  = ({ej.conteo_Baja} + {f3(a_v)}) / ({ej.n_municipios} + 3 × {f3(a_v)}) = {f3(ej.P_manual_Baja)}", "formula")),
    P(f"Sin suavizar sería {ej.conteo_Alta}/{ej.n_municipios} = {f3(ej.conteo_Alta / ej.n_municipios)}. Con más municipios en una "
      "combinación, el suavizado pesa menos.", "note"),
    P("3. Verificación independiente", "h2"),
    P("Las tablas se recalcularon con pandas, sin pgmpy, y se compararon celda a celda con las que estima pgmpy "
      "(<i>BayesianEstimator</i>, prior BDeu, ESS = 10). Las inferencias se reprodujeron sumando la distribución conjunta completa, "
      "combinación por combinación, y se compararon con el algoritmo de eliminación de variables de pgmpy.", "body"),
]
rs = [[P(h, "head") for h in ["Nodo", "Padres", "Celdas", "α", "Diferencia máxima", "Resultado"]]]
for _, r_ in resumen.iterrows():
    rs.append([P(lab(r_.nodo)), P(", ".join(lab(x) for x in r_.padres.split(", "))), P(r_.celdas), P(f3(r_.pseudo_conteo_BDeu)),
               P(f"{r_.max_dif_manual_vs_pgmpy:.1e}"), P("<font color='#006300'><b>Coincide</b></font>" if r_.coincide else "Difiere")])
story.append(tabla(rs, [0.24 * W, 0.30 * W, 0.08 * W, 0.1 * W, 0.15 * W, 0.13 * W]))
story.append(Spacer(1, 6))
ri = [[P(h, "head") for h in ["Consulta", "Combinaciones sumadas", "P(Alta) a mano", "P(Alta) pgmpy", "Diferencia"]]]
for _, r_ in inferencias.iterrows():
    ri.append([P(r_.consulta), P(f"{r_.combinaciones_sumadas:,}".replace(",", ".")), P(f3(r_.P_enum_Alta)),
               P(f3(r_.P_pgmpy_Alta)), P(f"{r_.max_dif:.1e}")])
story.append(KeepTogether([tabla(ri, [0.44 * W, 0.16 * W, 0.14 * W, 0.14 * W, 0.12 * W], num_desde=1)]))
story.append(P("Diferencias del orden de 10<super>-16</super> son redondeo de coma flotante: los cálculos son idénticos.", "note"))
story.append(P(f"Colmenar Viejo tiene todos sus atributos observados, así que su puntuación es directamente la fila de la tabla "
               f"del objetivo para Dinamismo Alto y Especialización Alta: {cv.P_enum_Alta * 100:.1f} sobre 100.".replace(".", ",", 1), "body"))
story.append(P("4. Todas las tablas de probabilidad", "h2"))
story.append(P("Para cada combinación de padres: municipios que la cumplen (n), cuántos hay en cada estado del nodo y la "
               "probabilidad resultante tras el suavizado (columnas sombreadas).", "body"))
for n in rb.NODOS:
    df, padres, estados, q, r, alpha = audit[n]
    titulo = f"{lab(n)}" + (f" | {', '.join(lab(p) for p in padres)}" if padres else " (nodo raíz)")
    story.append(KeepTogether([P(titulo, "h3"), P(f"α = {ESS} / ({q} × {r}) = {f3(alpha)}", "note"), Spacer(1, 2), tabla_nodo(n)]))
story.append(Spacer(1, 8))
story.append(P("Reproducir: <font face='Mono'>python backend/pipeline/auditoria_cpts.py</font>. El script falla si alguna probabilidad "
               "calculada a mano difiere de pgmpy.", "note"))

SimpleDocTemplate("docs/informe/Calculo_CPTs_CAM.pdf", pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                  bottomMargin=17 * mm, title="Cálculo de las tablas de probabilidad · Red bayesiana CAM",
                  author="Gregorio García Velasco; Guillermo Franco Gimeno").build(story, onFirstPage=pie, onLaterPages=pie)
print("ok: docs/informe/Calculo_CPTs_CAM.pdf")
