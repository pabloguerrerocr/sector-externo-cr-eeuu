# -*- coding: utf-8 -*-
"""
Relacion estadistica entre las variables estadounidenses y las del sector
externo costarricense, incluida la relacion de largo plazo.

Dos rutas complementarias:
  Engle-Granger : par por par, facil de leer, una sola relacion posible
  Johansen      : sistema completo, permite mas de un vector de cointegracion
Si Johansen encuentra rango r > 0, el modelo del objetivo 3 es un VECM.
"""
from __future__ import annotations

import itertools

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen, select_coint_rank

import config
from src import graficos as g


# --------------------------------------------------------------------------
# Engle-Granger
# --------------------------------------------------------------------------
def engle_granger(df: pd.DataFrame, nombre_bloque: str,
                  alfa: float | None = None) -> pd.DataFrame:
    alfa = config.NIVEL_SIG if alfa is None else alfa
    filas = []
    for y, x in itertools.permutations(df.columns, 2):
        est, p, crit = coint(df[y], df[x], trend="c", autolag="AIC")
        filas.append({"dependiente": y, "independiente": x, "estadistico": est,
                      "p_valor": p, "critico_5pc": crit[1],
                      "cointegran": "si" if p < alfa else "no"})
    t = pd.DataFrame(filas).sort_values("p_valor")
    t.to_csv(config.TABLAS / f"04_engle_granger_{nombre_bloque}.csv", index=False)
    return t


def residuo_largo_plazo(df: pd.DataFrame, y: str, xs: list[str]) -> pd.Series:
    """Residuo de la regresion de largo plazo. Si es estacionario, hay cointegracion."""
    X = sm.add_constant(df[xs])
    mco = sm.OLS(df[y], X).fit()
    return pd.Series(mco.resid, index=df.index, name="residuo")


# --------------------------------------------------------------------------
# Johansen
# --------------------------------------------------------------------------
def johansen(df: pd.DataFrame, nombre_bloque: str, k_ar_diff: int = 2,
             det_order: int = 0) -> tuple[pd.DataFrame, int]:
    """
    det_order: -1 sin termino determinista, 0 constante, 1 constante y tendencia.
    Devuelve la tabla de la prueba de la traza y del maximo valor propio, y el
    rango de cointegracion al 5 por ciento.
    """
    res = coint_johansen(df.values, det_order, k_ar_diff)
    filas = []
    n = df.shape[1]
    for r in range(n):
        filas.append({
            "hipotesis": f"r <= {r}",
            "traza": res.lr1[r], "traza_crit_5pc": res.cvt[r, 1],
            "traza_rechaza": "si" if res.lr1[r] > res.cvt[r, 1] else "no",
            "max_valor_propio": res.lr2[r], "mvp_crit_5pc": res.cvm[r, 1],
            "mvp_rechaza": "si" if res.lr2[r] > res.cvm[r, 1] else "no",
            "valor_propio": float(np.real(res.eig[r])),
        })
    t = pd.DataFrame(filas)
    t.to_csv(config.TABLAS / f"05_johansen_{nombre_bloque}.csv", index=False)

    rango = int(select_coint_rank(df, det_order, k_ar_diff, method="trace",
                                  signif=0.05).rank)
    return t, rango


def vectores_cointegracion(df: pd.DataFrame, k_ar_diff: int = 2,
                           det_order: int = 0, rango: int = 1) -> pd.DataFrame:
    """Vectores beta normalizados a la primera variable, que es como se interpretan."""
    res = coint_johansen(df.values, det_order, k_ar_diff)
    beta = np.real(res.evec[:, :max(rango, 1)])
    beta = beta / beta[0, :]
    return pd.DataFrame(beta, index=df.columns,
                        columns=[f"vector_{i+1}" for i in range(beta.shape[1])])


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------
def fig_residuo(df: pd.DataFrame, y: str, xs: list[str], nombre_bloque: str, demo: bool = False):
    r = residuo_largo_plazo(df, y, xs)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(r.index, r, color=g.color(0), label="residuo de la relacion de largo plazo")
    ax.axhline(0, color=config.TINTA_2, lw=0.9)
    for s in (r.std() * 2, -r.std() * 2):
        ax.axhline(s, color=config.TINTA_3, lw=0.7, ls=(0, (3, 3)))
    g.eje(ax, "Desviacion respecto al equilibrio de largo plazo",
          y + " explicada por " + ", ".join(xs) +
          ". Que el residuo vuelva a cero es la senal de cointegracion.",
          "residuo")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return g.guardar(fig, "09_residuo_largo_plazo_" + nombre_bloque, demo)


def fig_johansen(t: pd.DataFrame, rango: int, nombre_bloque: str, demo: bool = False):
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    x = np.arange(len(t))
    ancho = 0.38
    ax.bar(x - ancho / 2 - 0.01, t["traza"], ancho, color=g.color(0),
           label="estadistico de la traza", linewidth=0)
    ax.bar(x + ancho / 2 + 0.01, t["traza_crit_5pc"], ancho, color=g.color(3),
           label="valor critico al 5 por ciento", linewidth=0)
    ax.set_xticks(x)
    ax.set_xticklabels(t["hipotesis"])
    g.eje(ax, "Prueba de cointegracion de Johansen (traza)",
          "Se rechaza la hipotesis mientras la barra azul supere a la amarilla. "
          "Rango estimado: r = " + str(rango) + ".", "estadistico")
    ax.xaxis.set_major_locator(plt.FixedLocator(x))
    ax.legend(loc="upper right")
    fig.tight_layout()
    return g.guardar(fig, "10_johansen_" + nombre_bloque, demo)
