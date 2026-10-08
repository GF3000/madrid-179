"""Madrid 179: modelo de viabilidad empresarial municipal (red bayesiana + GA²M) y su servicio."""
import warnings

# pgmpy 1.1 avisa de cambios de nombre previstos para la 1.3 (PENDIENTES: migrar antes de actualizar)
warnings.filterwarnings("ignore", message=r".*deprecated and will be removed in v1\.3", category=FutureWarning)

__version__ = "0.1.0"
