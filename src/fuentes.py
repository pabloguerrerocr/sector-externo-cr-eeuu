# -*- coding: utf-8 -*-
"""
Descarga de las series de Estados Unidos desde FRED.

FRED es publico y no pide llave. Cada serie se guarda en data/raw/cache/ para
no repetir la descarga: FRED limita la frecuencia de peticiones y el analisis
tiene que poder correr sin red.

Por defecto no se toca la red: se lee la copia local. Si no existe (por
ejemplo, en un clon recien hecho, porque data/raw/cache/ no se versiona),
dataset.py usa la instantanea versionada en data/procesado/. Para bajar la
version mas reciente de FRED: python main.py --descargar-fred

Las series de Costa Rica no pasan por aqui: vienen de los Excel del BCCR y las
lee src/bccr_excel.py.
"""
from __future__ import annotations

import io

import pandas as pd
import requests

import config

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
CACHE = config.DATA_RAW / "cache"
CACHE.mkdir(parents=True, exist_ok=True)


class FREDNoDisponible(RuntimeError):
    """No hay copia local de la serie, o se pidio descargarla y la descarga fallo."""


def fred(serie_id: str, descargar: bool = False) -> pd.Series:
    destino = CACHE / f"fred_{serie_id}.csv"
    if destino.exists() and not descargar:
        crudo = destino.read_text(encoding="utf-8")
    elif descargar:
        try:
            r = requests.get(FRED_CSV, params={"id": serie_id}, timeout=90,
                             headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
        except requests.RequestException as e:
            raise FREDNoDisponible(
                f"No se pudo descargar {serie_id} de FRED ({type(e).__name__}). "
                f"Revisa la conexion o corre sin --descargar-fred para usar la "
                f"instantanea versionada.") from e
        crudo = r.text
        destino.write_text(crudo, encoding="utf-8")
    else:
        raise FREDNoDisponible(f"No hay copia local de {serie_id} en {CACHE}")

    df = pd.read_csv(io.StringIO(crudo))
    df.columns = ["fecha", "valor"]
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    return df.dropna().set_index("fecha")["valor"].sort_index()


def estados_unidos(clave: str, descargar: bool = False) -> pd.Series:
    serie = fred(config.FRED[clave]["id"], descargar)
    return serie.loc[config.INICIO:config.FIN].rename(clave)
