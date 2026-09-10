# -*- coding: utf-8 -*-
"""
Estilo unico de todas las figuras.

Reglas que se respetan en todo el proyecto:
  - un solo eje por panel (nunca dos escalas y): si las unidades diferen,
    se usan multiplos pequenos o se indexa a base 100
  - paleta categorica en orden fijo, nunca ciclada
  - leyenda siempre que haya 2 o mas series
  - rejilla y ejes recesivos, marcas finas
"""
from __future__ import annotations

import os
import time
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

import config

plt.rcParams.update({
    "figure.facecolor": config.SUPERFICIE,
    "axes.facecolor": config.SUPERFICIE,
    "savefig.facecolor": config.SUPERFICIE,
    "font.family": ["DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.titlecolor": config.TINTA,
    "axes.labelcolor": config.TINTA_2,
    "axes.labelsize": 9,
    "text.color": config.TINTA,
    "xtick.color": config.TINTA_3,
    "ytick.color": config.TINTA_3,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.edgecolor": config.REJILLA,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "grid.color": config.REJILLA,
    "grid.linewidth": 0.7,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "lines.linewidth": 1.8,
    "lines.solid_capstyle": "round",
    "figure.dpi": 110,
})


def color(i: int) -> str:
    return config.SERIES[i % len(config.SERIES)]


def eje(ax, titulo: str = "", subtitulo: str = "", unidad: str = ""):
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)
    if titulo:
        ax.set_title(titulo, loc="left", pad=20 if subtitulo else 8)
    if subtitulo:
        ax.text(0, 1.035, subtitulo, transform=ax.transAxes, fontsize=8.5,
                color=config.TINTA_2, va="bottom")
    if unidad:
        ax.set_ylabel(unidad)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    return ax


def marca_covid(ax, rango=("2020-03-01", "2020-08-01")):
    ax.axvspan(pd.Timestamp(rango[0]), pd.Timestamp(rango[1]),
               color=config.TINTA_3, alpha=0.10, lw=0, zorder=0)


def encabezado(fig, titulo: str, subtitulo: str = "", alto: float = 0.90):
    """
    Titulo y subtitulo de figura sin solaparse. Devuelve el rect que hay que
    pasarle a tight_layout para que el cuerpo no invada el encabezado.
    """
    fig.suptitle(titulo, x=0.006, y=0.995, ha="left", va="top",
                 fontsize=12.5, fontweight="bold")
    if subtitulo:
        fig.text(0.006, 0.952, subtitulo, ha="left", va="top",
                 fontsize=8.5, color=config.TINTA_2)
    return [0, 0, 1, alto if subtitulo else alto + 0.04]


def nota(fig, texto: str):
    fig.text(0.01, -0.01, texto, fontsize=7.5, color=config.TINTA_3,
             ha="left", va="top", wrap=True)


def aviso_demo(fig):
    fig.text(0.5, 0.5, "DATOS DEMO", fontsize=44, color="#e34948", alpha=0.13,
             ha="center", va="center", rotation=24, zorder=10,
             transform=fig.transFigure)


def guardar(fig, nombre: str, demo: bool = False):
    """
    Guarda la figura escribiendo primero un archivo temporal y despues
    reemplazando el definitivo.

    En Windows, sobrescribir un PNG que el Explorador esta leyendo para generar
    su miniatura falla con OSError 22. Escribir aparte y reemplazar evita el
    conflicto, y si el reemplazo choca se reintenta un par de veces.
    """
    if demo:
        aviso_demo(fig)
    ruta = config.FIGURAS / f"{nombre}.png"
    temporal = ruta.with_suffix(".tmp.png")
    fig.savefig(temporal, dpi=config.DPI, bbox_inches="tight")
    plt.close(fig)

    for intento in range(5):
        try:
            os.replace(temporal, ruta)
            return ruta
        except OSError:
            time.sleep(0.4 * (intento + 1))
    # Si tras los reintentos sigue bloqueado, se conserva el temporal y se avisa.
    warnings.warn(f"No se pudo reemplazar {ruta.name}; queda en {temporal.name}. "
                  f"Cerra el visor de imagenes o el Explorador sobre esa carpeta.")
    return temporal
