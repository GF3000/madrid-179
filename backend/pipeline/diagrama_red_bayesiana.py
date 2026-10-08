"""Dibuja con Graphviz el flujo completo de puntuación: filtros duros -> red bayesiana -> puntuación.
Lee NODOS, EDGES y FILTROS de red_bayesiana_viabilidad.py para no desincronizarse del modelo.
Salidas: docs/informe/red_bayesiana.{dot,png,svg}. Requiere `dot` (Graphviz) en el PATH y el venv con pgmpy.
"""
import json
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "backend/pipeline")
from red_bayesiana_viabilidad import EDGES, FILTROS, NODOS  # noqa: E402

d = pd.read_csv("data/processed/dataset_bn_municipios.csv", sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
um = json.load(open("data/processed/bn_umbrales.json", encoding="utf-8"))
TARGET = "Viabilidad_Empresarial"
FONT = "Segoe UI"
PCT = {"crec_pob_5a", "tasa_neta_emp"}
TILDES = {"Especializacion": "Especialización", "Demografico": "Demográfico"}
# Nodos sobre los que el usuario suele expresar preferencias (evidencia blanda)
PREFERENCIAS = ["Distancia_Madrid", "Talento", "Acceso_Ferroviario", "Coste_Inmobiliario"]
# Descripción legible de cada filtro duro activo
DESC_FILTROS = {
    "excluir_madrid_capital": "Excluir Madrid capital<BR/><FONT POINT-SIZE='9.5' COLOR='#52514e'>objetivo de reequilibrio</FONT>",
    "min_uu_oficinas": "Al menos 1 inmueble de oficinas<BR/><FONT POINT-SIZE='9.5' COLOR='#52514e'>Catastro, uu_oficinas ≥ 1</FONT>",
}


def fmt(x):
    if abs(x) >= 1000:
        return f"{x:,.0f}".replace(",", ".")
    return f"{x:.4g}".replace(".", ",")


def titulo(n):
    return " ".join(TILDES.get(w, w) for w in n.split("_"))


def label(n):
    col, estados, metodo = NODOS[n]
    u = um[n]
    if metodo == "terciles":
        pct = col in PCT
        c1, c2 = (fmt(c * 100) + " %" if pct else fmt(c) for c in u["cortes"])
        rng = f"{estados[0]} ≤ {c1} &lt; {estados[1]} ≤ {c2} &lt; {estados[2]}"
    else:
        rng = f"{estados[0]} = 0 · Sí &gt; 0"
    conteo = " / ".join(str(c) for c in u["conteo"])
    return (f'<<TABLE BORDER="0" CELLSPACING="2">'
            f'<TR><TD><FONT POINT-SIZE="14"><B>{titulo(n)}</B></FONT></TD></TR>'
            f'<TR><TD><FONT POINT-SIZE="9.5" FACE="Consolas" COLOR="#52514e">{col}</FONT></TD></TR>'
            f'<TR><TD><FONT POINT-SIZE="10">{rng}</FONT></TD></TR>'
            f'<TR><TD><FONT POINT-SIZE="9" COLOR="#898781">n = {conteo}</FONT></TD></TR></TABLE>>')


def rho(a, b):
    return d[NODOS[a][0]].corr(d[NODOS[b][0]], method="spearman")


# Recuento real de cada filtro, aplicado en cadena
quedan = [len(d)]
mask = np.ones(len(d), bool)
for f in FILTROS.values():
    mask &= np.asarray(f(d))
    quedan.append(int(mask.sum()))
n_cand = quedan[-1]
n_opc = int((mask & (d.poblacion < 20000).to_numpy()).sum())

L = [
    "digraph BN {",
    f'  graph [rankdir=TB, compound=true, newrank=true, bgcolor="#fcfcfb", pad=0.45, nodesep=0.5, ranksep=0.6, fontname="{FONT}", '
    f'label=<<FONT POINT-SIZE="21"><B>Flujo de puntuación · Viabilidad empresarial municipal (CAM)</B></FONT><BR/>'
    f'<FONT POINT-SIZE="11" COLOR="#52514e">1 · filtros duros (descartan)   →   2 · red bayesiana (explica, consultas parciales, simulación)   →   3 · GA²M y preferencias (puntúan)'
    f'   ·   trazo discontinuo = previsto, aún no implementado</FONT><BR/> >, labelloc=t];',
    f'  node [shape=box, style="rounded,filled", fillcolor="#ffffff", color="#c3c2b7", penwidth=1.2, fontname="{FONT}", margin="0.16,0.09"];',
    f'  edge [color="#52514e", penwidth=1.3, arrowsize=0.8, fontname="Consolas", fontsize=9.5, fontcolor="#52514e"];',
]

# ---- 1. Filtros duros ----
L.append(f'  subgraph cluster_filtros {{ label=<<B>1 · FILTROS DUROS</B>  <FONT COLOR="#52514e">preprocesado con pandas, antes de la inferencia</FONT>>; '
         f'fontname="{FONT}"; fontsize=12.5; style="rounded,filled"; fillcolor="#f4f3ef"; color="#898781"; margin=14;')
L.append(f'    entrada [label=<<B>{quedan[0]} municipios</B><BR/><FONT POINT-SIZE="9.5" COLOR="#52514e">dataset_bn_municipios.csv</FONT>>, '
         f'shape=box, style="rounded,filled", fillcolor="#ffffff"];')
prev = "entrada"
for i, k in enumerate(FILTROS, start=1):
    elim = quedan[i - 1] - quedan[i]
    L.append(f'    f{i} [label=<<B>{DESC_FILTROS.get(k, k)}</B>>, shape=box, style="rounded,filled", fillcolor="#ffffff", color="#52514e"];')
    L.append(f'    {prev} -> f{i} [label=" {quedan[i - 1]}"];')
    L.append(f'    descarte{i} [label=<−{elim}<BR/><FONT POINT-SIZE="9">puntuación nula,<BR/>aplanado en el mapa</FONT>>, shape=plaintext, style="", fontcolor="#b8312f"];')
    L.append(f'    f{i} -> descarte{i} [style=dashed, color="#b8312f", arrowsize=0.6, constraint=false];')
    prev = f"f{i}"
L.append(f'    fopc [label=<<B>Opcional · necesito ayudas</B><BR/><FONT POINT-SIZE="9.5" COLOR="#52514e">menos de 20.000 hab.: quedarían {n_opc}</FONT>>, '
         f'style="rounded,dashed,filled", fillcolor="#ffffff", color="#898781", fontcolor="#52514e"];')
L.append(f'    {prev} -> fopc [style=dashed, label=" {n_cand}"];')
L.append(f'    candidatos [label=<<B>{n_cand} municipios candidatos</B>>, shape=box, style="rounded,filled", fillcolor="#e6effb", color="#256abf", penwidth=1.6];')
L.append(f'    fopc -> candidatos [style=dashed];')
L.append("  }")

# ---- 2. Red bayesiana ----
raices = {n for n in NODOS if all(h != n for _, h in EDGES)}
L.append(f'  subgraph cluster_bn {{ label=<<B>2 · RED BAYESIANA</B>  <FONT COLOR="#52514e">8 nodos · máx. 2 padres · CPT BDeu (ESS = 10) · explica cada candidato y sostiene el simulador do()</FONT>>; '
         f'fontname="{FONT}"; fontsize=12.5; style="rounded"; color="#256abf"; penwidth=1.4; margin=16;')
for n in NODOS:
    attrs = ""
    if n == TARGET:
        attrs = ', fillcolor="#fde8e7", color="#b8312f", penwidth=2.4'
    elif n in raices:
        attrs = ', fillcolor="#e6effb", color="#256abf"'
    L.append(f"    {n} [label={label(n)}{attrs}];")
L.append(f"    {{rank=same; {' '.join(sorted(raices))}}}")
for a, b in EDGES:
    et = f" ρ {rho(a, b):+.2f}".replace("-", "−")
    L.append(f'    {a} -> {b} [label="{et}"];')
L.append("  }")
L.append(f'  candidatos -> Talento [lhead=cluster_bn, label="  atributos reales de cada municipio = evidencia", fontname="{FONT}", fontsize=10];')

# Preferencias blandas del usuario
L.append(f'  prefs [label=<<B>Preferencias blandas del usuario</B><BR/><FONT POINT-SIZE="9.5" COLOR="#52514e">chatbot y preguntas inteligentes<BR/>→ pesos en la puntuación · evidencia parcial en la red</FONT>>, '
         f'shape=note, style="filled", fillcolor="#fdf1d8", color="#c98a12"];')
for n in PREFERENCIAS:
    L.append(f'  prefs -> {n} [style=dotted, color="#c98a12", arrowsize=0.6];')
L.append("  {rank=same; prefs; candidatos}")

# ---- 3. Puntuación (decisión #40 b: el GA²M puntúa, la red explica) ----
L.append(f'  subgraph cluster_out {{ label=<<B>3 · PUNTUACIÓN Y RANKING</B>>; fontname="{FONT}"; fontsize=12.5; style="rounded"; color="#b8312f"; margin=14;')
L.append(f'    ga2m [label=<<B>GA²M (EBM)</B><BR/><FONT POINT-SIZE="9.5" COLOR="#52514e">mismas 7 variables, sin discretizar ·<BR/>predice la tasa neta empresarial</FONT>>, fillcolor="#e6effb", color="#256abf"];')
L.append(f'    score [label=<<B>Puntuación = percentil del GA²M entre candidatos (0-100)</B><BR/><FONT POINT-SIZE="9.5" COLOR="#52514e">'
         f'altura y color del municipio en el mapa 3D · bn_ranking_municipios.csv</FONT>>, fillcolor="#fde8e7", color="#b8312f", penwidth=1.6];')
L.append(f'    pesos [label=<<B>Preferencias ponderadas</B><BR/><FONT POINT-SIZE="9.5" COLOR="#52514e">transporte · ayudas · coste (previsto)<BR/>'
         f'(S + Σ a·u) / (1 + Σ a) · preferencias.py</FONT>>, fillcolor="#fdf1d8", color="#c98a12"];')
L.append('    ga2m -> score [penwidth=2, color="#b8312f", label=" S"];')
L.append('    pesos -> score [color="#c98a12", label=" + a·u"];')
L.append("  }")
L.append(f'  candidatos -> ga2m [lhead=cluster_out, label="  variables continuas", fontname="{FONT}", fontsize=10];')
L.append(f'  Viabilidad_Empresarial -> score [style=dashed, color="#256abf", label=<  <FONT FACE="{FONT}">explicación: P(Alta) y causas;<BR/>  aviso si red y GA²M discrepan</FONT>>];')
L.append('  prefs -> pesos [style=dotted, color="#c98a12", arrowsize=0.6];')
L.append("}")

dot = "\n".join(L)
open("docs/informe/red_bayesiana.dot", "w", encoding="utf-8").write(dot)
for fmt_out, extra in (("png", ["-Gdpi=160"]), ("svg", [])):
    subprocess.run(["dot", f"-T{fmt_out}", *extra, "docs/informe/red_bayesiana.dot", "-o", f"docs/informe/red_bayesiana.{fmt_out}"], check=True)
print("ok: docs/informe/red_bayesiana.png / .svg / .dot")
