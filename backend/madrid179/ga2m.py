"""GA²M (EBM de InterpretML): puntuación principal del ranking y aportaciones por término."""
import pandas as pd

from .config import EBM_KW, FEATURES_GA2M, NODOS, OBJETIVO


def ajustar(d):
    """Ajusta el EBM sobre los 179 municipios (objetivo: tasa neta de unidades productivas)."""
    from interpret.glassbox import ExplainableBoostingRegressor  # import local: el resto de módulos no lo necesita
    return ExplainableBoostingRegressor(**EBM_KW).fit(d[FEATURES_GA2M], d[NODOS[OBJETIVO][0]])


def evaluar(ebm, X):
    """Predicción, aportación de cada término (más el intercepto) e importancia media de los términos.
    La predicción es exactamente intercepto + suma de aportaciones."""
    contrib = pd.DataFrame(ebm.eval_terms(X[FEATURES_GA2M]), index=X.index, columns=ebm.term_names_)
    contrib.insert(0, "intercepto", float(ebm.intercept_))
    imp = pd.Series(ebm.term_importances(), index=ebm.term_names_).sort_values(ascending=False)
    return pd.Series(ebm.predict(X[FEATURES_GA2M]), index=X.index), contrib, imp


def ga2m(d, candidatos):
    """Ajusta el GA²M sobre los 179 municipios y devuelve predicción y contribución de cada término
    para los candidatos (base de la explicación por municipio, PENDIENTES #31)."""
    return evaluar(ajustar(d), d.loc[candidatos])
