# -*- coding: utf-8 -*-
"""
Armado de los paneles de trabajo, todo con datos reales.

Estados Unidos viene de FRED (cacheado en data/raw/cache/).
Costa Rica viene de los Excel del BCCR puestos en data/raw/.

Se arman dos paneles porque las series no comparten frecuencia: casi todo es
mensual, pero la cuenta financiera de la balanza de pagos solo existe
trimestral.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config
from src import bccr_excel as bx, fuentes

ORIGENES: dict[str, str] = {}
TITULOS: dict[str, str] = {}


def etiqueta(clave: str) -> str:
    if clave in config.FRED:
        return config.FRED[clave]["etiqueta"]
    return config.BCCR[clave]["etiqueta"]


def frecuencia(clave: str) -> str:
    if clave in config.FRED:
        return config.FRED[clave]["frec"]
    return config.BCCR[clave]["frec"]


# --------------------------------------------------------------------------
# Series individuales
# --------------------------------------------------------------------------
def serie_bccr(clave: str) -> pd.Series:
    spec = config.BCCR[clave]
    ruta = config.DATA_RAW / spec["archivo"]
    if not ruta.exists():
        raise FileNotFoundError(
            f"Falta {spec['archivo']} en data/raw/. Descargalo del portal del BCCR: "
            f"https://sdd.bccr.fi.cr/es/IndicadoresEconomicos/Inicio/  ({spec['cuadro']})")

    cruda, titulo, _ = bx.leer(ruta, spec["columna"])
    TITULOS[clave] = titulo
    ORIGENES[clave] = f"BCCR - {spec['archivo']}"

    if spec["frec"] == "Q":
        s = cruda.resample("QS").mean()
    elif spec["acumulada"]:
        # El cuadro viene acumulado en el ano: primero a fin de mes, luego el flujo.
        s = bx.desacumular(bx.a_mensual(cruda, "ultimo"))
    else:
        s = bx.a_mensual(cruda, spec["agregacion"])
    return s.rename(clave)


def serie_fred(clave: str, como: str = "M") -> pd.Series:
    spec = config.FRED[clave]
    s = fuentes.estados_unidos(clave)
    ORIGENES[clave] = f"FRED - {spec['id']}"

    if como == "Q":
        return s.resample("QS").mean().dropna().rename(clave)
    if spec["frec"] == "Q":
        return s.resample("MS").ffill().dropna().rename(clave)
    return s.resample("MS").mean().dropna().rename(clave)


# --------------------------------------------------------------------------
# Paneles
# --------------------------------------------------------------------------
def construir() -> tuple[pd.DataFrame, pd.DataFrame]:
    mensuales_cr = [c for c in config.BCCR if config.BCCR[c]["frec"] == "M"]
    trimestrales_cr = [c for c in config.BCCR if config.BCCR[c]["frec"] == "Q"]
    eeuu = [c for c in config.FRED if c != "crec_eeuu"]

    cols_m = {c: serie_fred(c, "M") for c in eeuu}
    cols_m.update({c: serie_bccr(c) for c in mensuales_cr})
    mensual = pd.DataFrame(cols_m).loc[config.INICIO:config.FIN]

    cols_q = {c: serie_fred(c, "Q") for c in eeuu}
    cols_q.update({c: serie_bccr(c) for c in trimestrales_cr})
    trimestral = pd.DataFrame(cols_q).loc[config.INICIO:config.FIN]

    mensual.to_csv(config.DATA_PROC / "panel_mensual.csv")
    trimestral.to_csv(config.DATA_PROC / "panel_trimestral.csv")

    reg = pd.DataFrame({
        "variable": list(ORIGENES),
        "etiqueta": [etiqueta(c) for c in ORIGENES],
        "frecuencia": [frecuencia(c) for c in ORIGENES],
        "origen": [ORIGENES[c] for c in ORIGENES],
        "titulo_original": [TITULOS.get(c, "") for c in ORIGENES],
    })
    reg.to_csv(config.DATA_PROC / "origen_de_los_datos.csv", index=False)
    return mensual, trimestral


def transformar(df: pd.DataFrame, bloque: dict) -> pd.DataFrame:
    """Aplica log a las variables indicadas y devuelve solo las del bloque."""
    out = df[bloque["variables"]].copy()
    for c in bloque["logaritmo"]:
        if c in out:
            if (out[c].dropna() <= 0).any():
                raise ValueError(f"'{c}' tiene valores no positivos: no admite logaritmo")
            out[c] = np.log(out[c])
            out = out.rename(columns={c: f"log_{c}"})
    return out.dropna()


def dummy_covid(idx: pd.DatetimeIndex, rango: tuple[str, str]) -> pd.DataFrame:
    ini, fin = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])
    return pd.DataFrame({"covid": ((idx >= ini) & (idx <= fin)).astype(float)}, index=idx)
