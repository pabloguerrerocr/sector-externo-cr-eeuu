# -*- coding: utf-8 -*-
"""
Descripcion del comportamiento de las variables, 2015-2025.

EE.UU.: ciclo real (produccion industrial, PIB) y politica monetaria (tasa de
fondos federales). Costa Rica: exportaciones FOB, ITCER, balance comercial,
tipo de cambio, reservas internacionales, tasa de politica monetaria del BCCR y
cuenta financiera de la balanza de pagos.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
from src import dataset, graficos as g


def _indice_100(s: pd.Series) -> pd.Series:
    return s / s.dropna().iloc[0] * 100


def tabla_resumen(p: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for c in p.columns:
        s = p[c].dropna()
        if not len(s):
            continue
        filas.append({
            "variable": c, "etiqueta": dataset.etiqueta(c), "n": len(s),
            "inicio": s.index.min().date(), "fin": s.index.max().date(),
            "media": s.mean(), "desv_est": s.std(), "min": s.min(), "max": s.max(),
            "asimetria": s.skew(), "curtosis": s.kurtosis(),
        })
    t = pd.DataFrame(filas)
    t.to_csv(config.TABLAS / "01_estadisticas_descriptivas.csv", index=False)
    return t


def fig_series_niveles(p: pd.DataFrame):
    """Multiplos pequenos: cada variable en su escala. Nunca dos ejes y."""
    cols = ["ipi_eeuu", "ffr", "export_cr", "itcer", "reservas", "tpm"]
    fig, axes = plt.subplots(3, 2, figsize=(9.8, 8), sharex=True)
    for i, (c, ax) in enumerate(zip(cols, axes.ravel())):
        ax.plot(p.index, p[c], color=g.color(i))
        g.marca_covid(ax)
        g.eje(ax, dataset.etiqueta(c))
        u = p[c].dropna()
        ax.annotate(format(u.iloc[-1], ",.1f"), xy=(u.index[-1], u.iloc[-1]),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=8, color=config.TINTA_2, va="center")
    rect = g.encabezado(
        fig, "Estados Unidos y el sector externo de Costa Rica, 2015-2025",
        "Series mensuales en niveles. La franja gris marca el choque COVID "
        "(marzo-agosto 2020).", alto=0.93)
    fig.tight_layout(rect=rect)
    return g.guardar(fig, "01_series_niveles")


def fig_dos_bancos_centrales(p: pd.DataFrame):
    """
    La Fed y el BCCR en un solo eje: las dos son tasas en por ciento, asi que
    comparten unidad legitimamente. Es la figura que muestra el canal
    financiero a simple vista.
    """
    fig, ax = plt.subplots(figsize=(9.4, 4.6))
    for i, c in enumerate(["ffr", "tpm"]):
        ax.plot(p.index, p[c], color=g.color(i), label=dataset.etiqueta(c))
        u = p[c].dropna()
        ax.annotate("Fed" if c == "ffr" else "BCCR",
                    xy=(u.index[-1], u.iloc[-1]), xytext=(6, 0),
                    textcoords="offset points", fontsize=9,
                    color=g.color(i), va="center", fontweight="bold")
    brecha = (p["tpm"] - p["ffr"]).mean()
    ax.fill_between(p.index, p["ffr"], p["tpm"], color=config.TINTA_3,
                    alpha=0.10, linewidth=0)
    g.eje(ax, "La Fed y el Banco Central de Costa Rica",
          f"El area sombreada es el diferencial de tasas. Promedio del periodo: "
          f"{brecha:.2f} puntos porcentuales a favor de Costa Rica.", "por ciento")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return g.guardar(fig, "02_fed_vs_bccr")


def fig_indexado(p: pd.DataFrame):
    """Series de distinta unidad, comparables en un solo eje: base 100."""
    cols = ["ipi_eeuu", "export_cr", "itcer"]
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    for i, c in enumerate(cols):
        s = _indice_100(p[c])
        ax.plot(s.index, s, color=g.color(i), label=dataset.etiqueta(c))
        ax.annotate(dataset.etiqueta(c).split("(")[0].strip()[:26],
                    xy=(s.index[-1], s.iloc[-1]), xytext=(5, 0),
                    textcoords="offset points", fontsize=8, color=g.color(i), va="center")
    ax.axhline(100, color=config.TINTA_3, lw=0.8, ls=(0, (4, 3)))
    g.marca_covid(ax)
    g.eje(ax, "Trayectoria comparada, base enero 2015 = 100",
          "Indexar permite comparar en un solo eje series con unidades distintas.",
          "indice (2015-01 = 100)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return g.guardar(fig, "03_indexado_base100")


def fig_balance_comercial(p: pd.DataFrame):
    """El balance comercial cambia de signo: barras divergentes, no linea."""
    s = p["balcom"].dropna()
    fig, ax = plt.subplots(figsize=(9.4, 4.2))
    colores = [config.SERIES[2] if v >= 0 else config.SERIES[1] for v in s]
    ax.bar(s.index, s.values, width=22, color=colores, linewidth=0)
    ax.axhline(0, color=config.TINTA, lw=1.0)
    media = s.mean()
    ax.axhline(media, color=config.TINTA_3, lw=0.9, ls=(0, (4, 3)))
    ax.annotate(f"promedio {media:,.0f}", xy=(s.index[3], media), xytext=(0, -12),
                textcoords="offset points", fontsize=8, color=config.TINTA_2)
    g.eje(ax, "Balance comercial mensual de Costa Rica",
          "Naranja: deficit del mes. Verde: superavit. Serie desacumulada a "
          "partir del dato acumulado que publica el BCCR.", "millones de USD")
    fig.tight_layout()
    return g.guardar(fig, "04_balance_comercial")


def fig_variaciones(p: pd.DataFrame):
    """Variacion interanual: quita estacionalidad y hace comparables las tasas."""
    var = p[["ipi_eeuu", "export_cr", "reservas"]].pct_change(12) * 100
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    for i, c in enumerate(var.columns):
        ax.plot(var.index, var[c], color=g.color(i), label=dataset.etiqueta(c))
    ax.axhline(0, color=config.TINTA_2, lw=0.9)
    g.marca_covid(ax)
    g.eje(ax, "Variacion interanual",
          "Todas en la misma unidad (%), por eso comparten eje.",
          "variacion interanual (%)")
    ax.legend(loc="upper left", ncols=2)
    fig.tight_layout()
    return g.guardar(fig, "05_variacion_interanual")


def _diferenciar(p: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    d = p[cols].copy()
    for c in cols:
        if c in ("ffr", "tpm", "balcom", "cuenta_fin"):
            d[c] = d[c].diff()                 # tasas y flujos: diferencia simple
        else:
            d[c] = np.log(d[c]).diff()         # niveles positivos: variacion log
    return d.dropna()


def fig_correlaciones(p: pd.DataFrame):
    """Correlacion entre tasas de variacion; en niveles seria espuria."""
    cols = ["ipi_eeuu", "ffr", "export_cr", "itcer", "reservas", "tpm"]
    corr = _diferenciar(p, cols).corr()

    fig, ax = plt.subplots(figsize=(6.6, 5.6))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr)))
    ax.set_yticklabels(corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            v = corr.iloc[i, j]
            ax.text(j, i, format(v, ".2f"), ha="center", va="center", fontsize=8,
                    color="#ffffff" if abs(v) > 0.55 else config.TINTA)
    ax.set_title("Correlacion contemporanea entre tasas de variacion",
                 loc="left", pad=10)
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.8, label="coeficiente de correlacion")
    fig.tight_layout()
    corr.to_csv(config.TABLAS / "02_matriz_correlacion.csv")
    return g.guardar(fig, "06_correlaciones")


def fig_correlacion_cruzada(p: pd.DataFrame, rezagos: int = 18):
    """
    En que rezago EE.UU. anticipa al sector externo tico. Primera evidencia
    descriptiva sobre canal real frente a canal financiero.
    """
    cols = ["ipi_eeuu", "ffr", "export_cr", "itcer", "reservas"]
    d = _diferenciar(p, cols)
    destinos = [("export_cr", "exportaciones"), ("itcer", "ITCER"),
                ("reservas", "reservas")]
    ks = np.arange(-rezagos, rezagos + 1)
    ic = 1.96 / np.sqrt(len(d))

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4), sharey=True)
    for ax, impulso, titulo in (
        (axes[0], "ipi_eeuu", "Canal real (produccion industrial de EE.UU.)"),
        (axes[1], "ffr", "Canal financiero (tasa de fondos federales)"),
    ):
        for i, (destino, lab) in enumerate(destinos):
            cc = [d[impulso].corr(d[destino].shift(-k)) for k in ks]
            ax.plot(ks, cc, color=g.color(i), label=lab)
        ax.axhline(0, color=config.TINTA_2, lw=0.9)
        for s in (ic, -ic):
            ax.axhline(s, color=config.TINTA_3, lw=0.7, ls=(0, (3, 3)))
        ax.axvline(0, color=config.REJILLA, lw=1.2)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.set_xlabel("rezago k en meses (k > 0: EE.UU. adelanta a Costa Rica)")
        ax.set_title(titulo, loc="left")
        ax.legend(loc="upper left")
    axes[0].set_ylabel("correlacion cruzada")
    rect = g.encabezado(
        fig, "Correlaciones cruzadas, tasas de variacion mensual",
        "Lineas punteadas: banda de no significancia al 95 por ciento.", alto=0.87)
    fig.tight_layout(rect=rect)
    return g.guardar(fig, "07_correlacion_cruzada")


def fig_cuenta_financiera(q: pd.DataFrame):
    """La cuenta financiera cambia de signo: barras divergentes, no linea."""
    s = q["cuenta_fin"].dropna()
    fig, ax = plt.subplots(figsize=(9.4, 4.2))
    colores = [config.SERIES[2] if v >= 0 else config.SERIES[1] for v in s]
    ax.bar(s.index, s.values, width=70, color=colores, linewidth=0)
    ax.axhline(0, color=config.TINTA, lw=1.0)
    g.eje(ax, "Cuenta financiera de la balanza de pagos, Costa Rica",
          "Datos trimestrales, manual MBP6. Verde: saldo positivo. "
          "Naranja: saldo negativo.", "millones de USD")
    fig.tight_layout()
    return g.guardar(fig, "08_cuenta_financiera")


def ejecutar(p: pd.DataFrame, q: pd.DataFrame) -> list:
    tabla_resumen(p)
    return [
        fig_series_niveles(p),
        fig_dos_bancos_centrales(p),
        fig_indexado(p),
        fig_balance_comercial(p),
        fig_variaciones(p),
        fig_correlaciones(p),
        fig_correlacion_cruzada(p),
        fig_cuenta_financiera(q),
    ]
