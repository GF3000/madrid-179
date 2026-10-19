// Presentación final del datathon (10 minutos) con la identidad de la app Madrid 179: papel cálido, rojo carmesí de la
// bandera, Fraunces en títulos y Hanken Grotesk en texto, la bandera de siete estrellas como firma.
// Tema propio (colores y fuentes) y layouts con nombre: se puede editar en PowerPoint sin romper el estilo.
//
//   cd infra/presentacion && npm install && node presentacion_final.js [--video ruta.mp4]
//
// Requiere las fuentes Fraunces y Hanken Grotesk instaladas (Google Fonts, OFL) para verse como la app.
// Salida: docs/presentaciones/4_Presentacion_final.pptx, FUERA DE GIT: lleva el vídeo con «Madrid» (Agustín Lara),
// protegida por derechos de autor; solo para proyectar en la sala.
// Cifras verificadas con los datos del proyecto el 2026-10-19 (ver docs/memoria/ESTADO.md); revisarlas si cambia el modelo.
const fs = require("fs");
const os = require("os");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("./apply_theme.js");

const RAIZ = path.resolve(__dirname, "..", "..");
const IMG = path.join(RAIZ, "docs", "presentaciones", "img");
const SALIDA = path.join(RAIZ, "docs", "presentaciones", "4_Presentacion_final.pptx");
const arg = process.argv.indexOf("--video");
const VIDEO = arg > 0 ? process.argv[arg + 1]
  : path.join(os.homedir(), "Downloads", "madrid179-video", "intro", "renders", "boceto_madrid179.mp4");

// Tokens de frontend/app/src/estilos.css
const THEME = {
  name: "Madrid 179",
  headFontFace: "Fraunces",
  bodyFontFace: "Hanken Grotesk",
  colors: {
    dk1: "261C20",      // tinta
    lt1: "FCFAF7",      // papel claro (tarjetas)
    dk2: "8A0A1F",      // rojo hondo
    lt2: "F6F2EC",      // papel (fondo)
    accent1: "C8102E",  // rojo de la bandera
    accent2: "D2847C",  // grupo «Intermedio» del mapa
    accent3: "56677A",  // pizarra («en contra»)
    accent4: "F3C9C4",  // rojo medio
    accent5: "8D8186",  // tinta 3 (rótulos)
    accent6: "FBEAE7",  // rojo suave (chips)
    hlink: "C8102E",
    folHlink: "8A0A1F",
  },
};
const HEX = { tinta2: "5B4F54", linea: "E7DFD5", tinta: "261C20", papelClaro: "FCFAF7", rojo: "C8102E",
  pizarra: "56677A", muyFav: "7A0018", rojoMedio: "F3C9C4", intermedio: "D2847C" };

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 × 5,625 in
pres.author = "Gregorio García Velasco; Guillermo Franco Gimeno";
pres.title = "Madrid 179 · Presentación final";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 10, H = 5.625, X0 = 0.6, AN = 8.8;

// ------------------------------------------------------------------------------------------ piezas de marca
function bandera(slide, x, y, w, nombre = "Bandera") {
  // Carmesí con siete estrellas blancas de cinco puntas (4 + 3), como el logo de la app
  const h = w * 104 / 168, d = w * 0.155;
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: C.accent1 }, line: { type: "none" },
    rectRadius: w * 0.04, objectName: nombre });
  for (let i = 0; i < 7; i++) {
    const fila = i < 4 ? 0 : 1, col = i < 4 ? i : i - 4;
    const cx = x + w * (fila === 0 ? 30 + col * 36 : 48 + col * 36) / 168, cy = y + h * (fila === 0 ? 34 : 70) / 104;
    slide.addShape(pres.ShapeType.star5, { x: cx - d / 2, y: cy - d / 2, w: d, h: d, fill: { color: C.background1 },
      line: { type: "none" }, objectName: `${nombre} estrella ${i + 1}` });
  }
}
const sombra = () => ({ type: "outer", blur: 10, offset: 2, angle: 90, color: "261C20", opacity: 0.14 });
function tarjeta(slide, x, y, w, h, opc = {}) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: opc.fill || C.background1 },
    line: opc.line ? { color: opc.line, width: 1 } : { type: "none" }, rectRadius: opc.radio ?? 0.12,
    shadow: opc.sinSombra ? undefined : sombra(), objectName: opc.nombre || "Tarjeta" });
}
function chip(slide, x, y, txt, opc = {}) {
  const w = opc.w || (0.2 + txt.length * 0.075);
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h: 0.26, fill: { color: opc.fill || C.accent6 },
    line: { type: "none" }, rectRadius: 0.13, objectName: `Etiqueta ${txt}` });
  slide.addText(txt, { x, y, w, h: 0.26, fontSize: 9, bold: true, color: opc.color || C.text2, align: "center",
    valign: "middle", margin: 0, charSpacing: 0.5, isTextBox: true, objectName: `Texto etiqueta ${txt}` });
  return w;
}
function cifra(slide, x, y, w, numero, etiqueta, opc = {}) {
  slide.addText(numero, { x, y, w, h: opc.alto || 0.62, fontFace: THEME.headFontFace, fontSize: opc.size || 34, bold: true,
    color: opc.color || C.accent1, margin: 0, valign: "bottom", isTextBox: true, objectName: `Cifra ${numero}` });
  slide.addText(etiqueta, { x, y: y + (opc.alto || 0.62) + 0.06, w, h: opc.altoEt || 0.5, fontSize: opc.sizeEt || 11.5,
    color: opc.colorEt || HEX.tinta2, margin: 0, valign: "top", isTextBox: true, objectName: `Etiqueta ${numero}` });
}
function numero(slide, x, y, n, opc = {}) {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: 0.34, h: 0.34, fill: { color: opc.fill || C.accent1 },
    line: { type: "none" }, objectName: `Paso ${n}` });
  slide.addText(String(n), { x, y, w: 0.34, h: 0.34, fontSize: 11, bold: true, color: opc.color || C.background1,
    align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `Número ${n}` });
}
function paso(slide, x, y, n, cab, des, w = 3.4, opc = {}) {
  numero(slide, x, y, n, opc);
  slide.addText(cab, { x: x + 0.48, y: y - 0.02, w, h: 0.32, fontFace: THEME.headFontFace, fontSize: 14, bold: true,
    color: opc.colorCab || C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: `Paso ${n} título` });
  slide.addText(des, { x: x + 0.48, y: y + 0.32, w, h: 0.5, fontSize: 11, color: opc.colorDes || HEX.tinta2, margin: 0,
    valign: "top", isTextBox: true, objectName: `Paso ${n} texto` });
}
function captura(slide, ruta, x, y, w, h, nombre) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: C.background1 }, line: { color: HEX.linea, width: 1 },
    rectRadius: 0.08, shadow: sombra(), objectName: `Marco ${nombre}` });
  slide.addImage({ path: ruta, x: x + 0.05, y: y + 0.05, w: w - 0.1, h: h - 0.1, rounding: false, objectName: nombre,
    altText: nombre });
}
// Título con la parte clave en cursiva roja, como «Madrid 179» en la app
const titulo = (normal, cursiva, color = C.accent1) => [
  { text: normal, options: {} }, { text: cursiva, options: { italic: true, color } }];
const pie = (slide, txt) => slide.addText(txt, { x: X0, y: 4.98, w: AN, h: 0.22, fontSize: 8.5, color: C.accent5,
  margin: 0, isTextBox: true, objectName: "Fuente" });

// ------------------------------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "Portada carmesí",
  background: { color: THEME.colors.accent1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: X0, y: 2.05, w: 6.6, h: 1.1, fontFace: THEME.headFontFace,
      fontSize: 54, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: X0, y: 3.3, w: 6.2, h: 1.0, fontSize: 15,
      color: C.background1, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "Carmesí",
  background: { color: THEME.colors.accent1 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: X0, y: 0.45, w: AN, h: 0.28, fontSize: 10, bold: true,
      color: C.accent4, margin: 0, charSpacing: 2 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: X0, y: 0.72, w: AN, h: 0.7, fontFace: THEME.headFontFace,
      fontSize: 30, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.4, h: 0.25, fontFace: THEME.bodyFontFace, fontSize: 9, color: THEME.colors.accent4, align: "right" },
});
pres.defineSlideMaster({
  title: "Contenido",
  background: { color: THEME.colors.lt2 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: X0, y: 0.38, w: AN, h: 0.26, fontSize: 9.5, bold: true,
      color: C.accent5, margin: 0, charSpacing: 2 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: X0, y: 0.62, w: AN, h: 0.62, fontFace: THEME.headFontFace,
      fontSize: 28, bold: true, color: C.text1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Madrid", options: { x: 1.0, y: 5.22, w: 0.6, h: 0.22, fontFace: THEME.headFontFace, fontSize: 10,
      bold: true, color: THEME.colors.dk1, margin: 0 } } },
    { text: { text: "179", options: { x: 1.53, y: 5.22, w: 0.4, h: 0.22, fontFace: THEME.headFontFace, fontSize: 10,
      bold: true, italic: true, color: THEME.colors.accent1, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.4, h: 0.25, fontFace: THEME.bodyFontFace, fontSize: 9, color: THEME.colors.accent5, align: "right" },
});

function contenido(eyebrow, tit, seccion) {
  const s = pres.addSlide({ masterName: "Contenido", sectionTitle: seccion });
  s.addText(eyebrow.toUpperCase(), { placeholder: "eyebrow" });
  s.addText(tit, { placeholder: "title" });
  bandera(s, X0, 5.22, 0.3, "Firma");
  return s;
}
function carmesi(eyebrow, tit, seccion) {
  const s = pres.addSlide({ masterName: "Carmesí", sectionTitle: seccion });
  constelacion(s, THEME.colors.dk2);
  s.addText(eyebrow.toUpperCase(), { placeholder: "eyebrow" });
  s.addText(tit, { placeholder: "title" });
  return s;
}
function constelacion(s, color) {
  for (const [x, y, d] of [[7.6, 0.35, 1.2], [8.75, 1.25, 0.8], [7.85, 2.15, 0.65], [8.95, 2.8, 1.0], [7.3, 3.4, 0.55],
    [8.3, 4.05, 0.7], [9.25, 4.75, 0.45]]) {
    s.addShape(pres.ShapeType.star5, { x, y, w: d, h: d, fill: { color, transparency: 35 }, line: { type: "none" },
      objectName: "Estrella de fondo" });
  }
}

// ============================================================================================== DIAPOSITIVAS
// 1 · Portada
pres.addSection({ title: "Apertura" });
let s = pres.addSlide({ masterName: "Portada carmesí", sectionTitle: "Apertura" });
constelacion(s, THEME.colors.dk2);
bandera(s, X0, 1.0, 1.25, "Logo");
s.addText(titulo("Madrid ", "179", C.accent4), { placeholder: "title" });
s.addText([
  { text: "Dónde abrir una oficina en los 179 municipios de la Comunidad de Madrid", options: { breakLine: true } },
  { text: "Gregorio García Velasco (UC3M) · Guillermo Franco Gimeno (UPM)", options: { fontSize: 11, color: C.accent4 } },
], { placeholder: "body", paraSpaceAfter: 10 });
s.addNotes("[0:00] Somos Gregorio y Guillermo. Madrid 179 ayuda a decidir dónde abrir una oficina en la Comunidad de Madrid "
  + "y, a la vez, a la Administración a ver dónde actuar. Empezamos con un vídeo de un minuto.");

// 2 · Vídeo
s = carmesi("Vídeo · 1 minuto", titulo("Madrid es mucho más ", "que su capital", C.accent4), "Apertura");
{
  const w = 6.1, h = w * 9 / 16, x = X0, y = 1.6;
  if (fs.existsSync(VIDEO)) {
    const portada = "image/png;base64," + fs.readFileSync(path.join(IMG, "final_video_portada.png")).toString("base64");
    s.addMedia({ type: "video", path: VIDEO, x, y, w, h, cover: portada, objectName: "Vídeo" });
  } else {
    s.addImage({ path: path.join(IMG, "final_video_portada.png"), x, y, w, h, objectName: "Portada del vídeo" });
    s.addText("(vídeo no encontrado al generar: insertarlo aquí)", { x, y: y + h + 0.05, w, h: 0.25, fontSize: 9,
      color: C.accent4, isTextBox: true });
  }
}
s.addNotes("[0:20-1:30] Vídeo (60 s): clic para reproducir. Plan B: abrir el MP4 aparte. Lleva la canción de Agustín Lara: "
  + "solo para la sala, no publicar.");

// 3 · El problema
pres.addSection({ title: "Cómo funciona" });
s = contenido("El problema", titulo("La actividad se concentra ", "en la capital"), "Cómo funciona");
{
  const filas = [["Población", 49.1], ["Unidades productivas", 56.3]];
  filas.forEach(([nom, v], i) => {
    const y = 1.55 + i * 1.0, x = X0, w = 5.3;
    s.addText(nom.toUpperCase(), { x, y, w, h: 0.25, fontSize: 9.5, bold: true, color: C.accent5, charSpacing: 1.5,
      margin: 0, isTextBox: true });
    s.addShape(pres.ShapeType.roundRect, { x, y: y + 0.32, w, h: 0.42, fill: { color: C.accent4 }, line: { type: "none" },
      rectRadius: 0.21, objectName: `Barra resto ${nom}` });
    s.addShape(pres.ShapeType.roundRect, { x, y: y + 0.32, w: w * v / 100, h: 0.42, fill: { color: C.accent1 },
      line: { type: "none" }, rectRadius: 0.21, objectName: `Barra capital ${nom}` });
    s.addText(`${String(Math.round(v))} % en la capital`, { x: x + 0.15, y: y + 0.32, w: 2.6, h: 0.42, fontSize: 12,
      bold: true, color: C.background1, valign: "middle", margin: 0, isTextBox: true });
    s.addText(`${String(100 - Math.round(v))} % en los otros 178`, { x: x + w * v / 100 + 0.1, y: y + 0.32,
      w: w * (1 - v / 100) - 0.15, h: 0.42, fontSize: 11, color: C.text2, valign: "middle", align: "right", margin: 0,
      isTextBox: true });
  });
  tarjeta(s, 6.25, 1.5, 3.15, 1.45);
  cifra(s, 6.45, 1.62, 2.8, "142", "municipios de menos de 20.000 hab. suman solo el 8,8 % de la población", { size: 32 });
  tarjeta(s, 6.25, 3.1, 3.15, 1.45, { fill: C.text1 });
  cifra(s, 6.45, 3.22, 2.8, "+9,1 %", "crece la población del resto en 5 años (mediana), frente a +5,2 % en la capital",
    { size: 32, color: C.accent4, colorEt: C.background2 });
  s.addText([{ text: "La oportunidad: ", options: { bold: true, color: C.accent1 } },
    { text: "la periferia crece más rápido, pero la actividad sigue en la capital." }],
  { x: X0, y: 3.85, w: 5.3, h: 0.6, fontSize: 13, color: C.text1, margin: 0, isTextBox: true });
  pie(s, "Fuentes: padrón 2025 (INE) y Colectivo Empresarial 2025 (Comunidad de Madrid), vía el Instituto de Estadística de la Comunidad de Madrid. Cálculo propio.");
}
s.addNotes("[1:30] La mitad de la población vive en la capital y allí está el 56 % de la actividad. 142 municipios tienen "
  + "menos de 20.000 habitantes y apenas suman el 9 % de la población. Pero la periferia crece más rápido: ahí está la "
  + "oportunidad de reequilibrio.");

// 4 · La solución
s = contenido("La solución", titulo("Una herramienta, ", "dos preguntas"), "Cómo funciona");
[["final_asistente.png", "EMPRESAS", "¿Dónde abro mi oficina?", "Describe tu negocio y el mapa 3D ordena los 179 municipios según tus prioridades."],
  ["final_actuar.png", "ADMINISTRACIÓN", "¿Dónde actúo y qué lo frena?", "Necesidad de reequilibrio frente a viabilidad, con los frenos de cada municipio."]]
  .forEach(([img, quien, preg, des], k) => {
    const x = X0 + k * 4.5, w = 4.3;
    captura(s, path.join(IMG, img), x, 1.42, w, w * 9 / 16 - 0.05, `Captura ${quien}`);
    chip(s, x, 3.95, quien, k ? { fill: C.text1, color: C.background1 } : {});
    s.addText(preg, { x, y: 4.26, w, h: 0.34, fontFace: THEME.headFontFace, fontSize: 16, bold: true, color: C.text1,
      margin: 0, isTextBox: true });
    s.addText(des, { x, y: 4.6, w, h: 0.4, fontSize: 11, color: HEX.tinta2, margin: 0, isTextBox: true });
  });
s.addNotes("[2:00] Dos usuarios, mismos datos y mismos modelos. La empresa pregunta dónde ir; la Administración, dónde "
  + "actuar. Está publicada en madrid179.web.app y el código es abierto.");

// 5 · Datos
s = contenido("Los datos", titulo("Datos abiertos ", "de la Comunidad"), "Cómo funciona");
[["11 de 12", "variables de la red, de fuentes de la Comunidad de Madrid"],
  ["621", "tablas municipales del portal de datos abiertos de la Comunidad"],
  ["153.517", "puntos de interés de OpenStreetMap: servicios y coworking"],
  ["569", "convocatorias de ayudas de la BDNS, revisadas"]].forEach(([n, et], k) => {
  const x = X0 + k * 2.2, w = 2.05;
  tarjeta(s, x, 1.5, w, 2.0);
  cifra(s, x + 0.2, 1.68, w - 0.4, n, et, { size: 30, altoEt: 0.75 });
});
s.addText([{ text: "Todo se une por el código INE ", options: { bold: true, color: C.accent1 } },
  { text: "de los 179 municipios: padrón, renta, paro, Catastro, transporte (CRTM), tejido empresarial y ayudas oficiales." }],
{ x: X0, y: 3.85, w: AN, h: 0.6, fontSize: 13, color: C.text1, margin: 0, isTextBox: true });
s.addNotes("[2:30] Partimos de los datos abiertos de la Comunidad: 11 de las 12 variables de la red salen de sus fuentes. "
  + "Descargamos 621 tablas municipales y lo unimos todo por el código INE.");

// 6 · Cómo decide
s = contenido("Cómo decide", titulo("Un modelo ", "para cada tarea"), "Cómo funciona");
{
  const bloques = [ // x, y, w, h, título, texto, relleno, color texto
    [X0, 2.15, 1.75, 1.15, "179 municipios", "14 variables por municipio", C.background1, C.text1],
    [2.85, 1.45, 2.35, 1.15, "GA²M · puntúa", "Ordena. Aditivo: cada factor suma o resta", C.accent1, C.background1],
    [2.85, 2.95, 2.35, 1.15, "Red bayesiana · explica", "Causas y consultas con información parcial", C.accent3, C.background1],
    [5.6, 1.45, 1.75, 1.15, "Tus prioridades", "15 preferencias y 7 requisitos", C.background1, C.text1],
    [7.75, 2.15, 1.65, 1.15, "Resultado", "Ranking, mapa 3D y ficha explicada", C.text1, C.background1],
  ];
  const linea = (x1, y1, x2, y2) => s.addShape(pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2),
    w: Math.abs(x2 - x1) || 0.01, h: Math.abs(y2 - y1) || 0.01, flipV: (y2 < y1) !== (x2 < x1),
    line: { color: HEX.intermedio, width: 1.5, endArrowType: "triangle" }, objectName: "Flecha" });
  linea(2.35, 2.72, 2.85, 2.02); linea(2.35, 2.72, 2.85, 3.52); linea(5.2, 2.02, 5.6, 2.02);
  linea(7.35, 2.02, 7.75, 2.55); linea(5.2, 3.52, 7.75, 2.9);
  for (const [x, y, w, h, t, d, fill, col] of bloques) {
    tarjeta(s, x, y, w, h, { fill });
    s.addText(t, { x: x + 0.15, y: y + 0.12, w: w - 0.3, h: 0.36, fontFace: THEME.headFontFace, fontSize: 13.5, bold: true,
      color: col, margin: 0, isTextBox: true });
    s.addText(d, { x: x + 0.15, y: y + 0.5, w: w - 0.3, h: 0.58, fontSize: 10.5, color: col, margin: 0, isTextBox: true });
  }
  tarjeta(s, X0, 4.35, AN, 0.55, { fill: C.accent6, sinSombra: true });
  s.addText([{ text: "Un LLM solo traduce y redacta: ", options: { bold: true, color: C.text2 } },
    { text: "convierte tu descripción en preferencias y escribe el resumen con los datos de la ficha. Nunca puntúa." }],
  { x: X0 + 0.2, y: 4.35, w: AN - 0.4, h: 0.55, fontSize: 11.5, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
}
s.addNotes("[3:00] Dos modelos con papeles distintos. El GA²M puntúa: es aditivo, cada factor suma o resta y se ve. La red "
  + "bayesiana explica y permite preguntar «¿y si busco talento lejos de Madrid?». Tus preferencias ajustan el orden con un "
  + "peso acotado: el modelo pesa siempre al menos una cuarta parte. El LLM no decide nada.");

// 7 · Validación
s = contenido("Validación", titulo("Señal real, ", "pero moderada"), "Cómo funciona");
s.addChart(pres.ChartType.bar, [{ name: "Acierto en el tercio superior", labels: ["Azar", "Modelo lineal", "GA²M v1", "GA²M v2"],
  values: [0.335, 0.483, 0.517, 0.643] }], {
  x: X0, y: 1.4, w: 5.2, h: 3.5, barDir: "col", barGapWidthPct: 55,
  chartColors: [HEX.linea, HEX.rojoMedio, HEX.intermedio, HEX.rojo], valAxisHidden: true, valAxisMaxVal: 0.8, valAxisMinVal: 0,
  valGridLine: { style: "none" }, catGridLine: { style: "none" }, catAxisLabelColor: HEX.tinta2, catAxisLabelFontSize: 11,
  catAxisLabelFontFace: "+mn-lt", catAxisLineShow: false, showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "0 %", dataLabelFontSize: 13, dataLabelFontBold: true, dataLabelColor: HEX.tinta,
  dataLabelFontFace: "+mj-lt", showTitle: true, title: "Acierto en el tercio superior · validación cruzada 5 × 5",
  titleFontSize: 11, titleColor: HEX.tinta2, titleFontFace: "+mn-lt", showLegend: false, objectName: "Gráfico de validación",
});
cifra(s, 6.2, 1.45, 3.2, "0,53", "correlación de Spearman con la tasa neta real de empresas (GA²M v2)", { size: 32 });
cifra(s, 6.2, 2.62, 3.2, "64 %", "de su tercio superior lo es de verdad, frente al 33 % al azar", { size: 32 });
tarjeta(s, 6.2, 3.85, 3.2, 1.0, { fill: C.text1 });
s.addText([{ text: "Orienta, no predice. ", options: { bold: true, color: C.accent4 } },
  { text: "Son asociaciones de 2020-2024, no efectos causales." }],
{ x: 6.38, y: 3.85, w: 2.85, h: 1.0, fontSize: 11.5, color: C.background1, valign: "middle", margin: 0, isTextBox: true });
pie(s, "Objetivo: tasa neta de unidades productivas 2020-2024 (IECM), con contracción empírico-bayesiana. Predicciones fuera de muestra.");
s.addNotes("[3:45] Validación cruzada repetida: fuera de muestra, el 64 % de lo que el modelo pone en el tercio superior lo "
  + "está de verdad, frente al 33 % del azar. Es una señal real pero moderada, y lo decimos en la propia app: orienta, no "
  + "predice, y no son efectos causales.");

// 8 · Demo
pres.addSection({ title: "Demo" });
s = carmesi("Demo en directo · madrid179.web.app", titulo("Buitrago ", "del Lozoya", C.accent4), "Demo");
captura(s, path.join(IMG, "final_mapa.png"), X0, 1.65, 4.6, 4.6 * 9 / 16 - 0.05, "Mapa de la app");
[["¿Por qué está abajo?", "Puesto 126 de 139: lo que suma y lo que resta"],
  ["Dos lecturas", "El modelo y lo que le conviene a quien se instala"],
  ["La red coincide", "Dinamismo bajo y densidad media: 22 % de viabilidad alta"],
  ["Qué ayudas tiene", "LEADER, IRPF y convocatorias abiertas"]].forEach(([c, d], i) =>
  paso(s, 5.55, 1.7 + i * 0.82, i + 1, c, d, 3.3,
    { fill: C.background1, color: C.accent1, colorCab: C.background1, colorDes: C.accent4 }));
s.addNotes("[5:00-8:00] DEMO EN DIRECTO (plan B: vídeo de la demo). Buscar «Buitrago». Factores: la suma cuadra (0,87 % de "
  + "media regional → 0,40 %); la distancia suma en el modelo pero es un inconveniente para quien se instala; la red "
  + "coincide; ayudas (LEADER GALSINMA, IRPF, desplegable de convocatorias); «En pocas palabras» y su verificador.");

// 9 · Explicable por diseño
s = contenido("Después de la demo", titulo("Explicable ", "por diseño"), "Demo");
{
  const items = [["Crecimiento de población", -0.31], ["Valor de la vivienda", -0.09], ["Densidad", -0.05],
    ["Talento", -0.04], ["Distancia a Madrid", 0.15]];
  const x = X0, y0 = 1.85, alto = 0.46, etW = 2.1, w = 5.1, vmin = -0.5, vmax = 0.25;
  const px = (w - etW) / (vmax - vmin), x0 = x + etW + (0 - vmin) * px;
  s.addText("Buitrago del Lozoya: de la media regional a su predicción", { x, y: 1.42, w: 5, h: 0.3, fontSize: 11,
    color: HEX.tinta2, margin: 0, isTextBox: true });
  items.forEach(([lab, v], i) => {
    const y = y0 + i * alto, bw = Math.abs(v) * px, bx = v < 0 ? x0 - bw : x0;
    s.addText(lab, { x, y, w: etW - 0.15, h: alto - 0.1, fontSize: 11, color: C.text1, align: "right", valign: "middle",
      margin: 0, isTextBox: true });
    s.addShape(pres.ShapeType.roundRect, { x: bx, y: y + 0.06, w: bw, h: alto - 0.22, fill: { color: v < 0 ? C.accent3 : C.accent1 },
      line: { type: "none" }, rectRadius: 0.05, objectName: `Barra ${lab}` });
    s.addText((v > 0 ? "+" : "−") + Math.abs(v).toFixed(2).replace(".", ","), { x: v < 0 ? bx - 0.6 : bx + bw + 0.06, y,
      w: 0.55, h: alto - 0.1, fontSize: 11, bold: true, color: C.text1, align: v < 0 ? "right" : "left", valign: "middle",
      margin: 0, isTextBox: true });
  });
  s.addShape(pres.ShapeType.line, { x: x0, y: y0 - 0.05, w: 0, h: items.length * alto, line: { color: C.accent5, width: 1 },
    objectName: "Eje" });
  chip(s, x, 4.32, "EN CONTRA", { fill: C.accent3, color: C.background1, w: 0.95 });
  chip(s, x + 1.05, 4.32, "A FAVOR", { fill: C.accent1, color: C.background1, w: 0.8 });
  s.addText([{ text: "0,87 % ", options: { bold: true, color: C.accent1 } }, { text: "media regional + aportaciones = " },
    { text: "0,40 %", options: { bold: true, color: C.accent1 } }, { text: ". La suma cuadra exacta." }],
  { x: x + 2.0, y: 4.28, w: 3.3, h: 0.35, fontSize: 11, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
  tarjeta(s, 5.95, 1.42, 3.45, 3.4);
  [["GA²M aditivo", "Cada factor suma o resta en puntos: nada escondido"],
    ["Red auditable", "Cada probabilidad se rehace a mano; un test falla si no cuadra"],
    ["IA verificada", "Cada frase del resumen cita sus datos; si no, se descarta"]].forEach(([c, d], i) =>
    paso(s, 6.15, 1.65 + i * 1.02, i + 1, c, d, 2.65));
}
s.addNotes("[recapitulación tras la demo] Tres garantías: el GA²M es aditivo y la suma cuadra; cada probabilidad de la red se "
  + "puede rehacer a mano (anexo con test automático); y el texto de la IA se comprueba frase a frase.");

// 10 · Ayudas
pres.addSection({ title: "Impacto y cierre" });
s = contenido("Ayudas", titulo("Lo que se puede ", "pedir hoy"), "Impacto y cierre");
captura(s, path.join(IMG, "final_ayudas_panel.png"), X0, 1.4, 2.75, 2.75 * 460 / 375, "Bloque de ayudas de la app");
[["99", "municipios en un grupo LEADER (convenios del BOCM)"],
  ["70", "con deducciones del IRPF por tener menos de 2.500 habitantes"],
  ["23", "convocatorias abiertas para pymes y autónomos (BDNS), revisadas"]].forEach(([n, et], k) =>
  cifra(s, 3.75, 1.38 + k * 0.92, 2.65, n, et, { size: 28, alto: 0.48, sizeEt: 10.5 }));
tarjeta(s, 6.65, 1.45, 2.75, 3.3, { fill: C.text1 });
s.addText("PALANCA DE REEQUILIBRIO", { x: 6.85, y: 1.62, w: 2.4, h: 0.25, fontSize: 9, bold: true, color: C.accent4,
  charSpacing: 1.5, margin: 0, isTextBox: true });
s.addText([{ text: "13 → 20", options: { fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.background1 } }],
  { x: 6.85, y: 1.95, w: 2.4, h: 0.65, margin: 0, isTextBox: true });
s.addText("municipios de menos de 20.000 hab. entre los 20 primeros si la empresa marca las ayudas como muy importantes.",
  { x: 6.85, y: 2.65, w: 2.4, h: 1.3, fontSize: 11, color: C.background2, margin: 0, isTextBox: true });
pie(s, "Las ayudas no entran en el modelo: son información, preferencia o filtro. Convocatorias abiertas a 19-10-2026.");
s.addNotes("[8:00] La pregunta práctica de la empresa: ¿qué puedo pedir? El asistente deduce qué tipo de ayuda le encaja y "
  + "enseña las convocatorias abiertas de la base de datos oficial. Y son una palanca de reequilibrio: con las ayudas como "
  + "muy importantes, los 20 primeros pasan a ser todos municipios de menos de 20.000 habitantes.");

// 11 · Dónde actuar
s = contenido("Para la Administración", titulo("Dónde actuar ", "y qué lo frena"), "Impacto y cierre");
[["33", "Necesita actividad y puede atraerla", "009E73", "FFFFFF"], ["56", "Necesita actividad y le cuesta atraerla", "E69F00", HEX.tinta],
  ["57", "Va por su cuenta", "0072B2", "FFFFFF"], ["32", "Sin urgencia, poca viabilidad", "968AB2", HEX.tinta]]
  .forEach(([n, nom, fill, col], k) => {
    const x = X0 + (k % 2) * 2.45, y = 1.42 + Math.floor(k / 2) * 1.75, w = 2.3, h = 1.6;
    tarjeta(s, x, y, w, h, { fill });
    s.addText(n, { x: x + 0.18, y: y + 0.12, w: w - 0.36, h: 0.6, fontFace: THEME.headFontFace, fontSize: 30, bold: true,
      color: col, margin: 0, isTextBox: true });
    s.addText(nom, { x: x + 0.18, y: y + 0.8, w: w - 0.36, h: 0.7, fontSize: 11.5, color: col, margin: 0, isTextBox: true });
  });
tarjeta(s, 5.65, 1.42, 3.75, 3.35);
cifra(s, 5.88, 1.55, 3.3, "172 de 178", "municipios tienen como freno principal un factor estructural: crecimiento de población, densidad o distancia.",
  { size: 30, altoEt: 0.95 });
s.addText([{ text: "Lectura: ", options: { bold: true, color: C.accent1 } },
  { text: "atraer población y servicios probablemente rinda más que ayudar solo a la empresa." }],
{ x: 5.88, y: 3.35, w: 3.3, h: 1.2, fontSize: 12.5, color: C.text1, margin: 0, isTextBox: true });
pie(s, "178 municipios (la capital es la referencia). Necesidad: crecimiento, juventud, paro y tamaño (definición provisional). Colores de la app.");
s.addNotes("[8:45] Cruzamos necesidad de reequilibrio con viabilidad. 56 municipios necesitan actividad y les cuesta "
  + "atraerla. Y en 172 de 178 el freno principal es estructural: la política que más rinde probablemente sea atraer "
  + "población, no solo subvencionar empresas.");

// 12 · Límites y próximos pasos
s = contenido("Honestidad", titulo("Lo que no hace ", "y lo que viene"), "Impacto y cierre");
[["Límites que decimos", ["Señal moderada: orienta, no predice", "Asociaciones, no efectos causales",
  "La necesidad depende mucho del tamaño", "Las convocatorias caducan: hay que refrescarlas"], C.background1, C.text1, C.accent1],
["Próximos pasos", ["Simulador de políticas con su incertidumbre", "Validación con técnicos de la Comunidad",
  "Más ayudas: Pueblos con Vida y municipales", "Precio real de oficinas y cobertura de fibra"], C.text1, C.background1, C.accent4]]
  .forEach(([cab, items, fill, col, acento], k) => {
    const x = X0 + k * 4.5, w = 4.3;
    tarjeta(s, x, 1.42, w, 3.45, { fill });
    s.addText(cab, { x: x + 0.3, y: 1.6, w: w - 0.6, h: 0.42, fontFace: THEME.headFontFace, fontSize: 18, bold: true,
      color: acento, margin: 0, isTextBox: true });
    s.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < items.length - 1 } })),
      { x: x + 0.3, y: 2.2, w: w - 0.6, h: 2.45, fontSize: 13, color: col, paraSpaceAfter: 10, valign: "top", margin: 0,
        isTextBox: true });
  });
s.addNotes("[9:15] Los límites los decimos, y están escritos en la propia app. Lo siguiente: un simulador de políticas con "
  + "intervalos, validarlo con técnicos de la Comunidad y ampliar las ayudas.");

// 13 · Cierre
s = pres.addSlide({ masterName: "Portada carmesí", sectionTitle: "Impacto y cierre" });
constelacion(s, THEME.colors.dk2);
bandera(s, X0, 0.45, 0.9, "Logo");
s.addText(titulo("Madrid es mucho más ", "que su capital", C.accent4), { placeholder: "title", fontSize: 36 });
s.addText([
  { text: "madrid179.web.app", options: { bold: true, fontSize: 20, breakLine: true } },
  { text: "Gracias · Gregorio García Velasco (UC3M) · Guillermo Franco Gimeno (UPM)", options: { fontSize: 11, color: C.accent4 } },
], { placeholder: "body", paraSpaceAfter: 10 });
s.addNotes("[9:45] Gracias. Madrid es mucho más que su capital: madrid179.web.app.");

(async () => {
  await pres.writeFile({ fileName: SALIDA });
  await applyTheme(SALIDA, THEME);
  console.log(`ok: ${pres.slides.length} diapositivas -> ${SALIDA}${fs.existsSync(VIDEO) ? " (con vídeo)" : " (sin vídeo)"}`);
})();
