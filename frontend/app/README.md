# App de Madrid 179

Interfaz de escritorio con mapa 3D de los 179 municipios: React + TypeScript, MapLibre (base) y deck.gl (columnas extruidas). Solo habla con la API (`/api/v1`), igual que el prototipo.

## Arrancar

- **Todo junto:** `powershell -ExecutionPolicy Bypass -File infra/scripts/dev.ps1` compila la app si falta `dist/` y la API la sirve en http://localhost:8000. `-Compilar` fuerza recompilar.
- **Trabajando en la app:** con la API en marcha (`dev.ps1`), `npm run dev` aquí → http://localhost:5173 con recarga en caliente; Vite reenvía `/api` al puerto 8000.
- `npm run build` comprueba los tipos y genera `dist/` (fuera de git). La CI lo ejecuta en cada push.

Requiere Node 20+. La geometría llega de `/api/v1/geometria` (`data/processed/municipios.geojson`, generado por `backend/pipeline/limites_municipales.py`). El mapa base usa las teselas abiertas de OpenFreeMap sin clave; sin conexión, la app sigue funcionando con las formas de los municipios sobre fondo liso.

## Criterios de diseño

- **Clases, no cifras.** La puntuación del modelo es orientativa, así que el usuario ve cinco grupos (quintiles de la posición entre los candidatos: Muy favorable … Poco favorable) más «No cumple tus requisitos» y «Fuera del análisis». Ni posiciones ni porcentajes del modelo; sí datos reales (habitantes, km a la estación).
- **Por qué de cada cosa.** La ficha traduce las aportaciones del GA²M a factores a favor y en contra con tres niveles de fuerza (umbrales en `src/modelo.ts`: p90 ≈ 0,13 pp «mucho», p75 ≈ 0,06 «bastante», p50 ≈ 0,02 «algo»; por debajo no se muestra), la lectura de la red bayesiana como reparto Baja/Media/Alta sin números y el perfil del municipio en terciles.
- **Rótulos.** En la vista general se rotulan Madrid, los 5 primeros del ranking (o de los grupos resaltados en la leyenda) y el municipio seleccionado. Al acercarse (zoom ≥ 9,3) se rotulan todos los visibles; si dos nombres chocan se queda el de mejor posición, y el otro aparece al acercarse más o al pasar el ratón. Los choques se recalculan al terminar cada movimiento del mapa.
- **Asistente.** Si la API tiene clave de DeepSeek (`/meta` → `asistente_disponible`), «Cuéntanos tu negocio» envía la descripción a `/api/v1/interpretar` y enseña «Esto es lo que hemos entendido» (preferencias con su motivo, requisitos, dudas). Mientras lee, el botón rojo se convierte en la bandera con las siete estrellas titilando en orden. Al llegar la respuesta, cada cosa entendida lanza una estrella desde su etiqueta de la tarjeta hasta un municipio que sube de grupo (o, si no sube ninguno, uno de los primeros), y las columnas se mueven cuando aterrizan (`componentes/Viaje.tsx`; sin estrellas con movimiento reducido o si ningún destino se ve en pantalla). Se aplica al mapa en cuanto llega la respuesta (con la animación y «Qué ha cambiado»); la tarjeta muestra lo entendido y permite «Deshacer» (vuelve a lo que estaba marcado), y todo queda en los controles para retocarlo. Sin clave, el cuadro no aparece. Después arranca un **recorrido por el Top 5** (`componentes/Recorrido.tsx`, ~33 s: 5 s por parada y 6 s de resumen final): la cámara vuela de municipio en municipio (solo el de la parada queda en pie) y una tarjeta grande a la derecha, centrada en vertical, enseña su foto (Wikimedia Commons, con crédito) y lo mejor de cada uno en 1-3 líneas, sacadas de su ficha (`modelo.puntosFuertes`: lo que pidió el usuario y cumple de sobra, y los factores del modelo que más suman); termina con la lista de los cinco, que abre su ficha. Se salta con «Saltar», Escape o tocando el mapa; con movimiento reducido no se lanza.
- **15 preferencias** en 5 grupos plegables, construidas desde el catálogo de `/meta` (añadir una en el backend la añade a la app). Una barra muestra cuánto pesa el modelo frente a las preferencias (el modelo, al menos 1 / (1 + tope): hoy una cuarta parte).
- **Foto, resumen y «En pocas palabras».** La ficha abre con la foto del municipio (Wikimedia Commons, con autor y licencia al pie) y el primer párrafo de Wikipedia enlazado. Si hay asistente, «En pocas palabras» pide al LLM lo mejor y lo que conviene vigilar, redactado solo con los hechos de la ficha y firmado como texto con IA; se vuelve a pedir si cambian las preferencias o el grupo. Si falla, la sección no aparece (la ficha ya explica todo).
- **Transiciones que explican.** Al cambiar una preferencia o un requisito, las columnas cambian de altura y color (≈ 1 s) y el panel «Qué ha cambiado» dice qué municipios suben o bajan de grupo y por qué. Al entrar, el mapa se inclina y las columnas crecen. El resto de animaciones de interfaz duran 150-450 ms y respetan `prefers-reduced-motion`.
- **Pantalla de carga (`componentes/Intro.tsx`).** Los 179 municipios aparecen como puntos rojos en su sitio (onda desde Madrid), se juntan en siete estrellas rojas que trazan una constelación, se colocan como en la bandera y el carmesí entra por detrás recortándolas en blanco; al final el carmesí se transforma en el contorno de la Comunidad justo donde lo dibuja el mapa (proyectado con la cámara real, girada o inclinada, y seguido cuadro a cuadro si se mueve), las estrellas vuelan a la bandera de la cabecera y el carmesí se funde en los colores de los municipios. El mapa no se inclina ni levanta columnas hasta que acaba la intro (prop `entrar`); si no carga en 2,5 s, la bandera vuela entera a la cabecera. Espera a los datos reales (si tardan, las estrellas titilan antes del carmesí), va más rápida si los datos ya han llegado o si ya se vio en la sesión, se acelera con un clic y con `prefers-reduced-motion` solo funde la bandera final. Los puntos salen de `src/puntos_carga.ts`, generado por `backend/pipeline/puntos_carga.py`.
- **Navegación (`componentes/Navegacion.tsx`).** Barra vertical a la izquierda para no cargar el panel: arriba los modos («Dónde abrir», «Dónde actuar», «Explorar perfiles»; pulsar el activo pliega el panel y deja el mapa entero), abajo la información («Cómo se decide», «Vídeo» si hay `VIDEO`, «Acerca de»: proyecto, equipo con LinkedIn, transparencia con los PDF y el código, datos y licencias, y aviso). `/#equipo` abre «Acerca de» directamente (enlace para compartir). El aviso «no oficial» queda siempre visible en una línea sobre el mapa, junto a las atribuciones.
- **Identidad.** Rojo carmesí de la bandera de la Comunidad sobre papel cálido, siete estrellas como firma, Fraunces (títulos) y Hanken Grotesk (texto) empaquetadas con la app. Sin librerías de iconos: los pocos símbolos (columna, brújula, flechas, aspa) están dibujados a medida.

## Estructura

| Fichero | Qué hace |
|---|---|
| `src/api.ts` | Tipos del contrato (`backend/api/esquemas.py`) y llamadas |
| `src/modelo.ts` | Clases, nombres de los factores y frases: toda la traducción a lenguaje claro |
| `src/App.tsx` | Estado, peticiones, cálculo de «qué ha cambiado» y resaltados |
| `src/componentes/Mapa.tsx` | MapLibre + deck.gl: estilo base, máscara exterior, columnas, rótulos, cámara |
| `src/componentes/Ficha.tsx` | Ficha del municipio |
| `src/componentes/PanelDecidir.tsx` · `PanelPerfiles.tsx` | Pestañas «Dónde abrir» y «Explorar perfiles» (consultas a la red) |
| `src/componentes/PanelActuar.tsx` | Pestaña «Dónde actuar» (Administración): ámbito, cuatro situaciones (necesidad × viabilidad), diagnóstico del municipio con sus frenos (palanca o estructural) y paso de escenario en desarrollo; datos de `/api/v1/diagnostico`, pedidos al entrar en el modo |
| `src/componentes/Asistente.tsx` | Cuadro del asistente, aplicación inmediata, resumen de lo entendido y «Deshacer» |
| `src/componentes/Navegacion.tsx` | Barra vertical: modos (abren o pliegan el panel) e información; URL del vídeo |
| `src/componentes/Contorno.tsx` | Marca, aviso «no oficial», buscador, leyenda, controles de cámara, etiqueta flotante y diálogos «Cómo se decide», «Acerca de» y vídeo |
| `src/componentes/piezas.tsx` | Selector segmentado, columna en miniatura, marcas de fuerza, escalones, reparto |
