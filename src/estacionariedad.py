# -*- coding: utf-8 -*-
"""
Orden de integracion de cada serie: paso previo a las pruebas de cointegracion.

Se usan dos pruebas con hipotesis nulas opuestas, que es la practica estandar:
  ADF  -> H0: hay raiz unitaria (la serie NO es estacionaria)
  KPSS -> H0: la serie ES estacionaria
Cuando las dos coinciden, la conclusion es firme. Cuando se contradicen, el
resultado es ambiguo y hay que reportarlo asi, no esconderlo.
"""
from __future__ import annotations

import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss

import config
from src import graficos as g


def _adf(s: pd.Series, regresion: str = "c") -> dict:
    try:   # statsmodels >= 0.15 avisa que la tupla cambia de forma en el futuro
        salida = adfuller(s.dropna(), regression=regresion, autolag="AIC",
                          result_object=False)
    except TypeError:
        salida = adfuller(s.dropna(), regression=regresion, autolag="AIC")
    est, p, rez, n, crit = salida[0], salida[1], salida[2], salida[3], salida[4]
    return {"adf_est": est, "adf_p": p, "adf_rezagos": rez, "adf_crit5": crit["5%"]}


def _kpss(s: pd.Series, regresion: str = "c") -> dict:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")           # avisa cuando p sale del rango tabulado
        est, p, rez, crit = kpss(s.dropna(), regression=regresion, nlags="auto")
    return {"kpss_est": est, "kpss_p": p, "kpss_crit5": crit["5%"]}


def _veredicto(adf_p: float, kpss_p: float, alfa: float) -> str:
    adf_estac = adf_p < alfa            # se rechaza raiz unitaria
    kpss_estac = kpss_p > alfa          # no se rechaza estacionariedad
    if adf_estac and kpss_estac:
        return "estacionaria"
    if not adf_estac and not kpss_estac:
        return "no estacionaria"
    return "ambiguo"


def probar(df: pd.DataFrame, nombre_bloque: str, con_tendencia: bool = True,
           alfa: float | None = None) -> pd.DataFrame:
    """Corre ADF y KPSS en niveles y en primeras diferencias para cada columna."""
    alfa = config.NIVEL_SIG if alfa is None else alfa
    reg = "ct" if con_tendencia else "c"
    filas = []
    for c in df.columns:
        nivel = df[c].dropna()
        dif = nivel.diff().dropna()
        for etiqueta, serie, r in (("nivel", nivel, reg), ("1a diferencia", dif, "c")):
            fila = {"variable": c, "transformacion": etiqueta, "n": len(serie),
                    "regresion": r}
            fila.update(_adf(serie, r))
            fila.update(_kpss(serie, r))
            fila["conclusion"] = _veredicto(fila["adf_p"], fila["kpss_p"], alfa)
            filas.append(fila)

    t = pd.DataFrame(filas)
    orden = []
    for c in df.columns:
        sub = t[t.variable == c]
        niv = sub[sub.transformacion == "nivel"]["conclusion"].iloc[0]
        dif = sub[sub.transformacion == "1a diferencia"]["conclusion"].iloc[0]
        orden.append({"variable": c,
                      "orden_integracion": "I(0)" if niv == "estacionaria"
                      else ("I(1)" if dif == "estacionaria" else "revisar")})
    t = t.merge(pd.DataFrame(orden), on="variable")
    t.to_csv(config.TABLAS / f"03_raices_unitarias_{nombre_bloque}.csv", index=False)
    return t


def resumen_orden(t: pd.DataFrame) -> dict[str, str]:
    return dict(t.drop_duplicates("variable")[["variable", "orden_integracion"]].values)


def fig_niveles_vs_diferencias(df: pd.DataFrame, nombre_bloque: str, demo: bool = False):
    """Ver la serie y su diferencia lado a lado hace visible por que hay raiz unitaria."""
    cols = list(df.columns)
    fig, axes = plt.subplots(len(cols), 2, figsize=(9.5, 2.0 * len(cols)), sharex=True)
    if len(cols) == 1:
        axes = np.array([axes])
    for i, c in enumerate(cols):
        axes[i, 0].plot(df.index, df[c], color=g.color(i))
        axes[i, 0].set_title(c + " - nivel", loc="left", fontsize=9)
        d = df[c].diff()
        axes[i, 1].plot(d.index, d, color=g.color(i), lw=1.2)
        axes[i, 1].axhline(0, color=config.TINTA_2, lw=0.8)
        axes[i, 1].set_title(c + " - primera diferencia", loc="left", fontsize=9)
        for ax in axes[i]:
            ax.grid(axis="y")
            ax.set_axisbelow(True)
    rect = g.encabezado(fig, "Niveles frente a primeras diferencias, bloque "
                        + nombre_bloque, alto=0.94)
    fig.tight_layout(rect=rect)
    return g.guardar(fig, "08_niveles_vs_diferencias_" + nombre_bloque, demo)
