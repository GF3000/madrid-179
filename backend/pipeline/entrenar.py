"""Entrena el modelo y guarda el artefacto que sirve la API: data/processed/modelo.joblib.

Contiene la red bayesiana, el GA²M, los umbrales, las predicciones y aportaciones de los 179 municipios
y la validación cruzada (CV-5 × 5 repeticiones). Tarda alrededor de un minuto.

Uso: python backend/pipeline/entrenar.py [--rapido]   (--rapido omite la validación cruzada)
"""
import argparse
import time

from madrid179 import artefactos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true", help="sin validación cruzada (para pruebas)")
    args = ap.parse_args()
    t0 = time.time()
    art = artefactos.entrenar(repeticiones_cv=0 if args.rapido else 5)
    ruta = artefactos.guardar(art)
    v = art["validacion"]
    print(f"Modelo {art['version']} guardado en {ruta} ({time.time() - t0:.0f} s)")
    if v:
        print(f"Validación CV-5 × {v['repeticiones']}: acierto {v['acierto'][0]:.3f} ± {v['acierto'][1]:.3f} "
              f"(azar {v['acierto_azar']:.3f}) · log-loss {v['log_loss'][0]:.3f} ± {v['log_loss'][1]:.3f} "
              f"(uniforme {v['log_loss_uniforme']:.3f})")


if __name__ == "__main__":
    main()
