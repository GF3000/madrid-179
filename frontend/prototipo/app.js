// Prototipo de Madrid 179: solo habla con la API (mismo contrato que usará la app definitiva).
const API = "/api/v1";
const $ = (s) => document.querySelector(s);
const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (x, d = 1) => Number(x).toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
const NOMBRES = {
  Distancia_Madrid: "Distancia a Madrid", Talento: "Talento", Acceso_Ferroviario: "Acceso ferroviario",
  Coste_Inmobiliario: "Coste inmobiliario", Renta: "Renta", Especializacion_Servicios: "Especialización en servicios",
  Dinamismo_Demografico: "Dinamismo demográfico", Viabilidad_Empresarial: "Viabilidad empresarial",
};
const FILTROS = { excluir_madrid_capital: "la capital no es candidata (reequilibrio territorial)", min_uu_oficinas: "no tiene oficinas en el Catastro" };

let meta = null;
let municipios = [];
let seleccionado = null;

async function api(ruta, cuerpo) {
  const r = await fetch(API + ruta, cuerpo === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo),
  });
  const datos = await r.json();
  if (!r.ok) throw new Error(typeof datos.detail === "string" ? datos.detail : JSON.stringify(datos.detail));
  return datos;
}

// ---------------------------------------------------------------- inicio
async function iniciar() {
  try {
    [meta, municipios] = await Promise.all([api("/meta"), api("/municipios")]);
  } catch (e) {
    $("#aviso").hidden = false;
    $("#aviso").innerHTML = `<span class="error">No se pudo conectar con la API: ${esc(e.message)}</span>`;
    return;
  }
  const v = meta.validacion;
  $("#version").textContent = `modelo ${meta.version_modelo}` +
    (v ? ` · acierto ${fmt(v.acierto[0] * 100)} % (azar ${fmt(v.acierto_azar * 100)} %)` : "");
  $("#aviso").hidden = false;
  $("#aviso").textContent = meta.aviso;

  for (const sel of document.querySelectorAll(".importancia"))
    sel.innerHTML = meta.importancias.map((i) => `<option>${esc(i)}</option>`).join("");
  $("#lista-municipios").innerHTML = municipios.map((m) => `<option value="${esc(m.municipio)}">`).join("");

  $("#evidencias").innerHTML = Object.entries(meta.nodos)
    .filter(([n]) => n !== meta.objetivo)
    .map(([n, d]) => `<label>${esc(NOMBRES[n] || n)}<select data-nodo="${esc(n)}">
      <option value="">(sin fijar)</option>${d.estados.map((s) => `<option>${esc(s)}</option>`).join("")}</select></label>`)
    .join("");

  for (const el of document.querySelectorAll("aside select, aside input")) el.addEventListener("change", cargarRanking);
  $("#buscador").addEventListener("change", (e) => {
    const m = municipios.find((x) => x.municipio.toLowerCase() === e.target.value.trim().toLowerCase());
    if (m) abrirFicha(m.ine5);
  });
  for (const b of document.querySelectorAll(".pestanas button")) b.addEventListener("click", () => cambiarPestana(b.dataset.pestana));
  $("#consultar").addEventListener("click", consultar);
  await cargarRanking();
  const enlace = location.hash.match(/^#(\d{5})$/);  // enlace directo a una ficha: …/prototipo/#28149
  if (enlace) abrirFicha(enlace[1]);
}

function cambiarPestana(p) {
  for (const b of document.querySelectorAll(".pestanas button")) b.classList.toggle("activa", b.dataset.pestana === p);
  $("#pestana-ranking").hidden = p !== "ranking";
  $("#pestana-consulta").hidden = p !== "consulta";
}

// --------------------------------------------------------------- ranking
function peticionRanking() {
  return {
    preferencias: { transporte: $("#pref-transporte").value, ayudas: $("#pref-ayudas").value },
    filtros: {
      estacion_max_km: $("#fil-estacion-on").checked ? Number($("#fil-estacion").value) : null,
      solo_con_ayudas: $("#fil-ayudas").checked,
    },
    limite: Number($("#limite").value) || null,
  };
}

async function cargarRanking() {
  const cuerpo = $("#tabla-ranking tbody");
  let r;
  try {
    r = await api("/ranking", peticionRanking());
  } catch (e) {
    $("#resumen-ranking").innerHTML = `<span class="error">${esc(e.message)}</span>`;
    cuerpo.innerHTML = "";
    return;
  }
  const pesos = Object.entries(r.pesos).filter(([, a]) => a > 0).map(([k, a]) => `${k} a = ${fmt(a, 2)}`);
  $("#resumen-ranking").textContent = `${r.candidatos} candidatos tras los filtros` +
    (pesos.length ? ` · pesos de las preferencias: ${pesos.join(", ")}` : " · sin preferencias: solo el modelo");
  if (!r.resultados.length) {
    cuerpo.innerHTML = `<tr><td colspan="6">Ningún municipio cumple los filtros.</td></tr>`;
    return;
  }
  cuerpo.innerHTML = r.resultados.map((f) => {
    const d = f.desglose;
    const pila = ["modelo", "transporte", "ayudas"].filter((k) => k in d)
      .map((k) => `<span class="c-${k}" style="width:${d[k]}%" title="${k}: ${fmt(d[k])}"></span>`).join("");
    return `<tr data-ine5="${f.ine5}" class="${f.ine5 === seleccionado ? "sel" : ""}">
      <td class="num">${f.posicion}</td><td>${esc(f.municipio)}</td>
      <td><div class="barra"><div class="pila">${pila}</div><b>${fmt(f.puntuacion)}</b></div></td>
      <td class="num">${fmt(f.p_alta_red * 100, 0)} %</td><td>${esc(f.nivel_ayudas)}</td>
      <td class="num">${fmt(f.dist_ferro_km)} km</td></tr>`;
  }).join("");
  for (const tr of cuerpo.querySelectorAll("tr[data-ine5]")) tr.addEventListener("click", () => abrirFicha(tr.dataset.ine5));
}

// ----------------------------------------------------------------- ficha
function barrasProb(probs, priori) {
  return `<div class="probs">${Object.entries(probs).map(([s, p]) => `
    <span>${esc(s)}</span>
    <div class="eje"><span style="width:${p * 100}%"></span>${priori ? `<i class="priori" style="left:${priori[s] * 100}%" title="a priori ${fmt(priori[s] * 100)} %"></i>` : ""}</div>
    <span class="v">${fmt(p * 100)} %</span>`).join("")}</div>`;
}

async function abrirFicha(ine5) {
  seleccionado = ine5;
  history.replaceState(null, "", `#${ine5}`);
  for (const tr of document.querySelectorAll("#tabla-ranking tr[data-ine5]")) tr.classList.toggle("sel", tr.dataset.ine5 === ine5);
  const el = $("#ficha");
  el.hidden = false;
  el.innerHTML = "Cargando…";
  let f;
  try {
    f = await api(`/municipios/${ine5}`);
  } catch (e) {
    el.innerHTML = `<span class="error">${esc(e.message)}</span>`;
    return;
  }
  const max = Math.max(...f.ga2m.aportaciones.map((a) => Math.abs(a.aportacion_pp)), 1e-9);
  const aport = f.ga2m.aportaciones.map((a) => {
    const ancho = (Math.abs(a.aportacion_pp) / max) * 50;
    const pos = a.aportacion_pp >= 0;
    const valores = Object.entries(a.valores).map(([c, v]) => `${c} = ${fmt(v, 2)}`).join(", ");
    return `<span title="${esc(valores)}">${esc(a.etiqueta)}</span>
      <div class="eje"><span style="${pos ? "left:50%" : `left:${50 - ancho}%`};width:${ancho}%;background:var(${pos ? "--positivo" : "--negativo"})"></span></div>
      <span class="v">${a.aportacion_pp >= 0 ? "+" : ""}${fmt(a.aportacion_pp, 2)}</span>`;
  }).join("");
  const estados = Object.entries(f.red.estados).map(([n, s]) =>
    `<tr class="${n in f.red.padres ? "padre" : ""}"><td>${esc(NOMBRES[n] || n)}${n === meta.objetivo ? " (observada)" : ""}</td><td>${esc(s)}</td></tr>`).join("");

  el.innerHTML = `
    <button class="cerrar" title="Cerrar">×</button>
    <h2>${esc(f.municipio)}</h2>
    <div class="pie">INE ${f.ine5} · ${f.poblacion.toLocaleString("es-ES")} habitantes</div>
    ${f.candidato ? `<div class="cifras">
        <div><b>${f.posicion}.º</b><span>de ${f.de} candidatos</span></div>
        <div><b>${fmt(f.puntuacion)}</b><span>puntuación (sin preferencias)</span></div>
        <div><b>${fmt(f.red.probabilidades.Alta * 100, 0)} %</b><span>P(Alta) en la red</span></div></div>`
      : `<p class="excluido">No es candidato: ${(f.motivo_exclusion || []).map((m) => esc(FILTROS[m] || m)).join("; ")}. Se muestra su explicación igualmente.</p>`}
    ${f.discrepancia ? `<p class="discrepancia">${esc(f.discrepancia)}</p>` : ""}

    <h3>Por qué: aportaciones del GA²M</h3>
    <p class="pie">Tasa neta anual de unidades productivas predicha: <b>${fmt(f.ga2m.prediccion_pct, 2)} %</b> =
      base ${fmt(f.ga2m.intercepto_pct, 2)} + suma de aportaciones (puntos porcentuales).</p>
    <div class="aport">${aport}</div>

    <h3>Red bayesiana</h3>
    ${barrasProb(f.red.probabilidades)}
    <p class="pie">En negrita, los padres directos de la viabilidad: con evidencia completa solo ellos influyen.</p>
    <table class="estados">${estados}</table>

    <h3>Preferencias</h3>
    <p class="pie">Estación ferroviaria a ${fmt(f.preferencias.transporte.dist_ferro_km)} km (utilidad ${fmt(f.preferencias.transporte.utilidad, 2)}) ·
      ayudas: nivel ${esc(f.preferencias.ayudas.nivel)} (utilidad ${fmt(f.preferencias.ayudas.utilidad, 1)})</p>`;
  el.querySelector(".cerrar").addEventListener("click", () => { el.hidden = true; seleccionado = null; history.replaceState(null, "", location.pathname); });
}

// -------------------------------------------------------------- consulta
async function consultar() {
  const evidencia = {};
  for (const s of document.querySelectorAll("#evidencias select")) if (s.value) evidencia[s.dataset.nodo] = s.value;
  const el = $("#resultado-consulta");
  let r;
  try {
    r = await api("/consulta", { evidencia });
  } catch (e) {
    el.innerHTML = `<p class="error">${esc(e.message)}</p>`;
    return;
  }
  const fijada = Object.keys(evidencia).length
    ? Object.entries(evidencia).map(([n, s]) => `${NOMBRES[n] || n} = ${s}`).join(" · ") : "ninguna (a priori)";
  el.innerHTML = `
    <h3>P(${esc(NOMBRES[meta.objetivo])} | evidencia)</h3>
    <p class="pie">Evidencia: ${esc(fijada)}. La marca vertical es la probabilidad a priori.</p>
    ${barrasProb(r.probabilidades, r.a_priori)}
    <h3>${r.municipios.length} municipios cumplen esa evidencia</h3>
    <div class="chips">${r.municipios.map((m) =>
      `<button data-ine5="${m.ine5}" class="${m.candidato ? "" : "no-candidato"}" title="${m.candidato ? "" : "no candidato"}">${esc(m.municipio)}</button>`).join("")}</div>`;
  for (const b of el.querySelectorAll(".chips button")) b.addEventListener("click", () => abrirFicha(b.dataset.ine5));
}

iniciar();
