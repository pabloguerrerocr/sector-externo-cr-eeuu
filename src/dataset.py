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
# Diferencia maxima entre la suma anual de los flujos y el acumulado de diciembre.
VERIFICACIONES: dict[str, float] = {}


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
        acumulada = bx.a_mensual(cruda, "ultimo")
        s = bx.desacumular(acumulada)
        VERIFICACIONES[clave] = bx.verificar_desacumulacion(acumulada, s)
    else:
        s = bx.a_mensual(cruda, spec["agregacion"])
    return s.rename(clave)


_INSTANTANEA: dict[str, pd.DataFrame] = {}
AVISOS: list[str] = []


def instantanea_fred(clave: str, como: str) -> pd.Series:
    """
    Serie de FRED tomada del panel versionado en data/procesado/, ya llevada a
    la frecuencia de trabajo. Son los mismos datos con los que se obtuvieron
    los resultados publicados, asi que un clon nuevo los reproduce sin red.
    """
    archivo = "panel_mensual.csv" if como == "M" else "panel_trimestral.csv"
    if archivo not in _INSTANTANEA:
        ruta = config.DATA_PROC / archivo
        if not ruta.exists():
            raise fuentes.FREDNoDisponible(
                f"No hay copia local de FRED ni instantanea en {ruta}. "
                f"Corre: python main.py --descargar-fred")
        _INSTANTANEA[archivo] = pd.read_csv(ruta, index_col="fecha", parse_dates=True,
                                            float_precision="round_trip")
    return _INSTANTANEA[archivo][clave].dropna().rename(clave)


def serie_fred(clave: str, como: str = "M", descargar: bool = False) -> pd.Series:
    spec = config.FRED[clave]
    ORIGENES[clave] = f"FRED - {spec['id']}"
    try:
        s = fuentes.estados_unidos(clave, descargar)
    except fuentes.FREDNoDisponible:
        if descargar:
            raise
        aviso = ("FRED: no hay copia local en data/raw/cache/; se usa la instantanea "
                 "versionada de data/procesado/ (los datos de los resultados publicados). "
                 "Para bajar la version mas reciente: python main.py --descargar-fred")
        if aviso not in AVISOS:
            AVISOS.append(aviso)
        return instantanea_fred(clave, como)

    if como == "Q":
        return s.resample("QS").mean().dropna().rename(clave)
    if spec["frec"] == "Q":
        return s.resample("MS").ffill().dropna().rename(clave)
    return s.resample("MS").mean().dropna().rename(clave)


# --------------------------------------------------------------------------
# Paneles
# --------------------------------------------------------------------------
def construir(descargar_fred: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    mensuales_cr = [c for c in config.BCCR if config.BCCR[c]["frec"] == "M"]
    trimestrales_cr = [c for c in config.BCCR if config.BCCR[c]["frec"] == "Q"]
    eeuu = [c for c in config.FRED if c != "crec_eeuu"]

    cols_m = {c: serie_fred(c, "M", descargar_fred) for c in eeuu}
    cols_m.update({c: serie_bccr(c) for c in mensuales_cr})
    mensual = pd.DataFrame(cols_m).loc[config.INICIO:config.FIN]

    cols_q = {c: serie_fred(c, "Q", descargar_fred) for c in eeuu}
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
