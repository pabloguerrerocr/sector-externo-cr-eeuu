# -*- coding: utf-8 -*-
"""
Descarga de las series de Estados Unidos desde FRED.

FRED es publico y no pide llave. Se cachea cada serie en data/raw/cache/ para
no repetir la descarga: FRED limita la frecuencia de peticiones y el analisis
tiene que poder correr sin red.

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


def fred(serie_id: str, usar_cache: bool = True) -> pd.Series:
    destino = CACHE / f"fred_{serie_id}.csv"
    if usar_cache and destino.exists():
        crudo = destino.read_text(encoding="utf-8")
    else:
        r = requests.get(FRED_CSV, params={"id": serie_id}, timeout=90,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        crudo = r.text
        destino.write_text(crudo, encoding="utf-8")

    df = pd.read_csv(io.StringIO(crudo))
    df.columns = ["fecha", "valor"]
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    return df.dropna().set_index("fecha")["valor"].sort_index()


def estados_unidos(clave: str) -> pd.Series:
    return fred(config.FRED[clave]["id"]).loc[config.INICIO:config.FIN].rename(clave)
