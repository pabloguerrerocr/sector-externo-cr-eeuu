# -*- coding: utf-8 -*-
"""
Modelo econometrico: incidencia relativa del canal real frente al canal
financiero sobre el sector externo de Costa Rica.

Estrategia:
  1. seleccion de rezagos por AIC / BIC / HQIC
  2. si Johansen encuentra rango > 0  -> VECM (relacion de largo plazo y
     velocidad de ajuste); si el rango es 0 -> VAR en primeras diferencias
  3. en los dos casos se estima ademas un VAR en niveles con rezagos
     suficientes, que es consistente aun con cointegracion, y de ahi salen
     las funciones impulso-respuesta y la descomposicion de varianza
  4. causalidad de Granger, diagnosticos y estabilidad

Identificacion (Cholesky): las variables de Estados Unidos van primero. Costa
Rica es una economia pequena y abierta, asi que no se le supone efecto
contemporaneo sobre EE.UU. El orden esta en config.BLOQUE_*["variables"] y es
un supuesto, no un hecho: conviene reportar la version con el orden invertido
entre las dos variables ticas como prueba de robustez.
"""
from __future__ import annotations

import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.vector_ar.vecm import VECM

import config
from src import graficos as g

warnings.filterwarnings("ignore", category=FutureWarning)


# --------------------------------------------------------------------------
# seleccion de rezagos
# --------------------------------------------------------------------------
def seleccionar_rezagos(df: pd.DataFrame, max_lags: int, nombre_bloque: str,
                        exog: pd.DataFrame | None = None) -> tuple[pd.DataFrame, int]:
    modelo = VAR(df, exog=exog)
    max_lags = min(max_lags, max(1, int(len(df) / (df.shape[1] * 3))))
    filas = []
    for p in range(1, max_lags + 1):
        try:
            r = modelo.fit(p)
            filas.append({"rezagos": p, "aic": r.aic, "bic": r.bic,
                          "hqic": r.hqic, "fpe": r.fpe})
        except Exception:
            break
    t = pd.DataFrame(filas)
    t.to_csv(config.TABLAS / f"06_seleccion_rezagos_{nombre_bloque}.csv", index=False)
    # Se prefiere HQIC: AIC sobreparametriza con muestras cortas y BIC se queda corto.
    elegido = int(t.loc[t["hqic"].idxmin(), "rezagos"]) if len(t) else 1
    return t, elegido


# --------------------------------------------------------------------------
# estimacion
# --------------------------------------------------------------------------
def estimar_vecm(df: pd.DataFrame, rango: int, k_ar_diff: int,
                 nombre_bloque: str, exog: pd.DataFrame | None = None):
    res = VECM(df, k_ar_diff=k_ar_diff, coint_rank=rango,
               deterministic="ci", exog=exog).fit()

    beta = pd.DataFrame(res.beta, index=df.columns,
                        columns=[f"vector_{i+1}" for i in range(rango)])
    alfa = pd.DataFrame(res.alpha, index=df.columns,
                        columns=[f"ajuste_{i+1}" for i in range(rango)])
    tabla = beta.join(alfa)
    # Errores estandar y t del termino de correccion de error (velocidad de ajuste)
    tabla["t_ajuste_1"] = res.tvalues_alpha[:, 0]
    tabla["p_ajuste_1"] = res.pvalues_alpha[:, 0]
    tabla.to_csv(config.TABLAS / f"07_vecm_largo_plazo_{nombre_bloque}.csv")
    return res, tabla


def estimar_var(df: pd.DataFrame, rezagos: int, exog: pd.DataFrame | None = None):
    return VAR(df, exog=exog).fit(rezagos)


def diagnosticos(res_var, nombre_bloque: str) -> pd.DataFrame:
    filas = []
    try:
        w = res_var.test_whiteness(nlags=min(12, res_var.k_ar + 8), adjusted=True)
        filas.append({"prueba": "Portmanteau (autocorrelacion)", "H0": "sin autocorrelacion",
                      "estadistico": w.test_statistic, "p_valor": w.pvalue,
                      "conclusion": "se rechaza" if w.pvalue < config.NIVEL_SIG else "no se rechaza"})
    except Exception as e:
        filas.append({"prueba": "Portmanteau", "H0": "sin autocorrelacion",
                      "estadistico": np.nan, "p_valor": np.nan, "conclusion": str(e)[:60]})
    try:
        n = res_var.test_normality()
        filas.append({"prueba": "Jarque-Bera multivariada", "H0": "residuos normales",
                      "estadistico": n.test_statistic, "p_valor": n.pvalue,
                      "conclusion": "se rechaza" if n.pvalue < config.NIVEL_SIG else "no se rechaza"})
    except Exception as e:
        filas.append({"prueba": "Jarque-Bera", "H0": "residuos normales",
                      "estadistico": np.nan, "p_valor": np.nan, "conclusion": str(e)[:60]})

    raices = np.abs(res_var.roots)
    filas.append({"prueba": "Estabilidad (raices del polinomio)",
                  "H0": "todas las raices fuera del circulo unitario",
                  "estadistico": float(np.min(raices)), "p_valor": np.nan,
                  "conclusion": "estable" if np.all(raices > 1) else "INESTABLE"})
    t = pd.DataFrame(filas)
    t.to_csv(config.TABLAS / f"08_diagnosticos_{nombre_bloque}.csv", index=False)
    return t


# --------------------------------------------------------------------------
# causalidad de Granger
# --------------------------------------------------------------------------
def granger(res_var, nombre_bloque: str, alfa: float | None = None) -> pd.DataFrame:
    alfa = config.NIVEL_SIG if alfa is None else alfa
    nombres = list(res_var.names)
    filas = []
    for causa in nombres:
        for efecto in nombres:
            if causa == efecto:
                continue
            try:
                p = res_var.test_causality(efecto, causa, kind="f")
                filas.append({"causa": causa, "efecto": efecto,
                              "estadistico_F": p.test_statistic, "p_valor": p.pvalue,
                              "causa_en_sentido_granger": "si" if p.pvalue < alfa else "no"})
            except Exception:
                continue
    t = pd.DataFrame(filas).sort_values("p_valor")
    t.to_csv(config.TABLAS / f"09_granger_{nombre_bloque}.csv", index=False)
    return t


# --------------------------------------------------------------------------
# impulso-respuesta
# --------------------------------------------------------------------------
def irf_tabla(res_var, periodos: int, nombre_bloque: str) -> pd.DataFrame:
    irf = res_var.irf(periodos)
    nombres = list(res_var.names)
    datos = irf.orth_irfs                      # (periodos+1, respuesta, impulso)
    filas = []
    for h in range(datos.shape[0]):
        for i, resp in enumerate(nombres):
            for j, imp in enumerate(nombres):
                filas.append({"horizonte": h, "impulso": imp, "respuesta": resp,
                              "efecto": datos[h, i, j]})
    t = pd.DataFrame(filas)
    t.to_csv(config.TABLAS / f"10_impulso_respuesta_{nombre_bloque}.csv", index=False)
    return t


def fig_irf(res_var, impulsos: list[str], respuestas: list[str], periodos: int,
            nombre_bloque: str, demo: bool = False, etiquetas: dict[str, str] | None = None):
    """Respuesta acumulada de las variables ticas a los choques estadounidenses."""
    irf = res_var.irf(periodos)
    nombres = list(res_var.names)
    etiquetas = etiquetas or {}
    try:
        bandas = irf.errband_mc(orth=True, repl=500, signif=0.05, seed=7)
    except Exception:
        bandas = None

    fig, axes = plt.subplots(len(respuestas), len(impulsos),
                             figsize=(5.0 * len(impulsos), 3.3 * len(respuestas)),
                             squeeze=False, sharex=True)
    h = np.arange(periodos + 1)
    for fila, resp in enumerate(respuestas):
        i = nombres.index(resp)
        for col, imp in enumerate(impulsos):
            j = nombres.index(imp)
            ax = axes[fila][col]
            y = irf.orth_irfs[:, i, j]
            ax.plot(h, y, color=g.color(col))
            if bandas is not None:
                ax.fill_between(h, bandas[0][:, i, j], bandas[1][:, i, j],
                                color=g.color(col), alpha=0.14, linewidth=0)
            ax.axhline(0, color=config.TINTA_2, lw=0.9)
            ax.grid(axis="y")
            ax.set_axisbelow(True)
            salto = chr(10)
            ax.set_title("choque en " + etiquetas.get(imp, imp) + salto +
                         "respuesta de " + etiquetas.get(resp, resp),
                         loc="left", fontsize=9)
            if fila == len(respuestas) - 1:
                ax.set_xlabel("periodos")
    sub = ("Banda: intervalo de confianza al 95 por ciento por bootstrap."
           if bandas is not None else "Sin banda de confianza: el bootstrap no convergio.")
    rect = g.encabezado(fig, "Funciones impulso-respuesta ortogonalizadas",
                        sub + " Identificacion de Cholesky con EE.UU. primero.",
                        alto=0.91)
    fig.tight_layout(rect=rect)
    return g.guardar(fig, "11_impulso_respuesta_" + nombre_bloque, demo)


# --------------------------------------------------------------------------
# descomposicion de varianza: aqui se responde canal real vs canal financiero
# --------------------------------------------------------------------------
def fevd(res_var, periodos: int, nombre_bloque: str) -> pd.DataFrame:
    d = res_var.fevd(periodos)
    nombres = list(res_var.names)
    filas = []
    for i, resp in enumerate(nombres):
        for h in range(periodos):
            fila = {"variable": resp, "horizonte": h + 1}
            for j, imp in enumerate(nombres):
                fila[imp] = d.decomp[i, h, j] * 100
            filas.append(fila)
    t = pd.DataFrame(filas)
    t.to_csv(config.TABLAS / f"11_descomposicion_varianza_{nombre_bloque}.csv", index=False)
    return t


def comparar_canales(t_fevd: pd.DataFrame, real: str, financiero: str,
                     objetivos: list[str], nombre_bloque: str) -> pd.DataFrame:
    """
    Resumen directo de la pregunta de la boleta: cuanto de la varianza del sector
    externo tico explica cada canal, a 6, 12 y 24 periodos.
    """
    filas = []
    for var in objetivos:
        sub = t_fevd[t_fevd.variable == var].set_index("horizonte")
        for h in [x for x in (6, 12, 24) if x in sub.index]:
            r, f = sub.loc[h, real], sub.loc[h, financiero]
            filas.append({"variable": var, "horizonte": h,
                          "canal_real_pc": r, "canal_financiero_pc": f,
                          "razon_real_sobre_financiero": r / f if f else np.nan,
                          "canal_dominante": "real" if r > f else "financiero"})
    t = pd.DataFrame(filas)
    t.to_csv(config.TABLAS / f"12_canal_real_vs_financiero_{nombre_bloque}.csv", index=False)
    return t


def fig_fevd(t_fevd: pd.DataFrame, objetivos: list[str], nombre_bloque: str,
             demo: bool = False, etiquetas: dict[str, str] | None = None):
    """Areas apiladas: participacion de cada choque en la varianza del error."""
    etiquetas = etiquetas or {}
    impulsos = [c for c in t_fevd.columns if c not in ("variable", "horizonte")]
    fig, axes = plt.subplots(1, len(objetivos), figsize=(5.2 * len(objetivos), 4.0),
                             squeeze=False, sharey=True)
    for k, var in enumerate(objetivos):
        ax = axes[0][k]
        sub = t_fevd[t_fevd.variable == var].set_index("horizonte")[impulsos]
        ax.stackplot(sub.index, [sub[c] for c in impulsos],
                     colors=[g.color(i) for i in range(len(impulsos))],
                     labels=[etiquetas.get(c, c) for c in impulsos],
                     edgecolor=config.SUPERFICIE, linewidth=0.8)
        ax.set_ylim(0, 100)
        ax.set_xlim(sub.index.min(), sub.index.max())
        ax.set_title("varianza de " + etiquetas.get(var, var), loc="left", fontsize=10)
        ax.set_xlabel("horizonte (periodos)")
        ax.grid(axis="y")
        ax.set_axisbelow(True)
    axes[0][0].set_ylabel("porcentaje de la varianza del error de prediccion")
    # La leyenda va fuera del area de datos: dentro taparia las areas apiladas.
    manijas, textos = axes[0][0].get_legend_handles_labels()
    fig.legend(manijas, textos, loc="lower center", ncols=min(4, len(impulsos)),
               bbox_to_anchor=(0.5, -0.06))
    rect = g.encabezado(
        fig, "Descomposicion de la varianza del error de prediccion",
        "Cuanto de la variacion del sector externo tico se atribuye al canal real "
        "y cuanto al canal financiero de EE.UU.", alto=0.88)
    fig.tight_layout(rect=rect)
    return g.guardar(fig, "12_descomposicion_varianza_" + nombre_bloque, demo)


def fig_canales(t_canales: pd.DataFrame, nombre_bloque: str, demo: bool = False,
                etiquetas: dict[str, str] | None = None):
    """Barras agrupadas: canal real frente a canal financiero por horizonte."""
    import textwrap
    etiquetas = etiquetas or {}
    grupos = [(v, h) for v, h in t_canales[["variable", "horizonte"]].values]
    x = np.arange(len(grupos))
    ancho = 0.38

    fig, ax = plt.subplots(figsize=(max(8.4, 1.5 * len(grupos)), 4.6))
    ax.bar(x - ancho / 2 - 0.01, t_canales["canal_real_pc"], ancho, linewidth=0,
           color=g.color(0), label="canal real (ciclo de EE.UU.)")
    ax.bar(x + ancho / 2 + 0.01, t_canales["canal_financiero_pc"], ancho, linewidth=0,
           color=g.color(1), label="canal financiero (tasa de la Fed)")

    # Las etiquetas se parten en varias lineas: sin esto se encaraman entre si.
    marcas = ["\n".join(textwrap.wrap(etiquetas.get(v, v), 16)) + f"\nh = {h}"
              for v, h in grupos]
    ax.set_xticks(x)
    ax.set_xticklabels(marcas, fontsize=8)

    for xi, (r, f) in enumerate(zip(t_canales["canal_real_pc"],
                                    t_canales["canal_financiero_pc"])):
        ax.text(xi - ancho / 2 - 0.01, r, format(r, ".0f"), ha="center", va="bottom",
                fontsize=8, color=config.TINTA_2)
        ax.text(xi + ancho / 2 + 0.01, f, format(f, ".0f"), ha="center", va="bottom",
                fontsize=8, color=config.TINTA_2)

    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(t_canales[["canal_real_pc", "canal_financiero_pc"]].max()) * 1.18)
    ax.set_ylabel("porcentaje de la varianza explicada")
    rect = g.encabezado(
        fig, "Canal real frente a canal financiero",
        "Participacion de cada choque de EE.UU. en la varianza del error de "
        "prediccion de las variables de Costa Rica.", alto=0.93)
    # La leyenda va fuera del area de datos: dentro tapa las barras altas.
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.34), ncols=2)
    fig.tight_layout(rect=rect)
    return g.guardar(fig, "13_canal_real_vs_financiero_" + nombre_bloque, demo)
