# -*- coding: utf-8 -*-
"""
Corre el analisis completo con datos reales.

    python main.py                          # los tres bloques
    python main.py --bloque balanza_pagos   # solo uno

Datos: FRED para Estados Unidos (cacheado), Excel del BCCR para Costa Rica.
Salidas: salidas/figuras/*.png, salidas/tablas/*.csv, salidas/reporte.md
"""
from __future__ import annotations

import argparse
import sys
import warnings

import pandas as pd

import config
from src import (cointegracion as co, dataset, descriptivo, estacionariedad as est,
                 modelo as mo, reporte)

warnings.filterwarnings("ignore")

ETIQUETAS = {
    "log_ipi_eeuu": "produccion industrial EE.UU.",
    "log_pib_eeuu": "PIB real EE.UU.",
    "ffr": "tasa de fondos federales",
    "log_export_cr": "exportaciones FOB",
    "log_itcer": "ITCER",
    "log_reservas": "reservas internacionales",
    "tpm": "tasa de politica del BCCR",
    "cuenta_fin": "cuenta financiera",
}


def _titulo(t: str):
    print("\n" + t)
    print("-" * len(t))


def correr_bloque(panel: pd.DataFrame, spec: dict) -> tuple[dict, list]:
    nombre = spec["nombre"]
    X = dataset.transformar(panel, spec)
    rango_covid = (config.COVID_MENSUAL if spec["frecuencia"] == "M"
                   else config.COVID_TRIMESTRAL)
    exog = dataset.dummy_covid(X.index, rango_covid)
    figuras = []

    _titulo(f"Bloque {nombre}: {list(X.columns)}  (n = {len(X)})")
    print(spec["descripcion"])

    # --- raices unitarias ---------------------------------------------------
    raices = est.probar(X, nombre)
    print()
    print(raices[["variable", "transformacion", "adf_p", "kpss_p", "conclusion"]]
          .to_string(index=False))
    figuras.append(est.fig_niveles_vs_diferencias(X, nombre))

    # --- rezagos ------------------------------------------------------------
    tab_rez, p = mo.seleccionar_rezagos(X, spec["max_lags"], nombre, exog)
    print(f"\nRezagos elegidos por HQIC: {p}")

    # --- cointegracion ------------------------------------------------------
    k_diff = max(p - 1, 1)
    eg = co.engle_granger(X, nombre)
    tj, rango = co.johansen(X, nombre, k_ar_diff=k_diff)
    print(f"Rango de cointegracion (Johansen, traza, 5%): r = {rango}")
    figuras.append(co.fig_johansen(tj, rango, nombre))

    objetivo_cr = [c for c in X.columns
                   if not any(k in c for k in ("ipi", "pib")) and c != "ffr"]
    if objetivo_cr:
        otras = [c for c in X.columns if c != objetivo_cr[0]]
        figuras.append(co.fig_residuo(X, objetivo_cr[0], otras, nombre))

    tabla_vecm = None
    if rango > 0:
        try:
            _, tabla_vecm = mo.estimar_vecm(X, rango, k_diff, nombre, exog)
            print("\nVECM: vector de largo plazo y velocidad de ajuste")
            print(tabla_vecm.round(4).to_string())
        except Exception as e:
            print(f"VECM no estimable: {type(e).__name__} - {e}")

    # --- VAR en niveles: IRF y descomposicion de varianza -------------------
    var = mo.estimar_var(X, p, exog)
    diag = mo.diagnosticos(var, nombre)
    print("\nDiagnosticos")
    print(diag.to_string(index=False))

    gr = mo.granger(var, nombre)
    sig = gr[gr["causa_en_sentido_granger"] == "si"]
    print(f"\nCausalidad de Granger: {len(sig)} de {len(gr)} pares significativos al 5%")
    if len(sig):
        print(sig.head(6).to_string(index=False))

    real = next(c for c in X.columns if "ipi" in c or "pib" in c)
    fin = "ffr"
    periodos = config.PERIODOS_IRF if spec["frecuencia"] == "M" else 12
    figuras.append(mo.fig_irf(var, [real, fin], objetivo_cr, periodos, nombre,
                              etiquetas=ETIQUETAS))
    mo.irf_tabla(var, periodos, nombre)
    f = mo.fevd(var, periodos, nombre)
    figuras.append(mo.fig_fevd(f, objetivo_cr, nombre, etiquetas=ETIQUETAS))
    canales = mo.comparar_canales(f, real, fin, objetivo_cr, nombre)
    figuras.append(mo.fig_canales(canales, nombre, etiquetas=ETIQUETAS))

    print("\nCanal real frente a canal financiero (% de la varianza explicada)")
    print(canales.round(2).to_string(index=False))

    conteo = canales["canal_dominante"].value_counts()
    gana = conteo.index[0]
    ult = canales.iloc[-1]
    unidad = "meses" if spec["frecuencia"] == "M" else "trimestres"
    lectura = (
        f"En {int(conteo.iloc[0])} de {len(canales)} combinaciones de variable y "
        f"horizonte domina el **canal {gana}**. A {int(ult['horizonte'])} {unidad}, "
        f"sobre {ETIQUETAS.get(ult['variable'], ult['variable'])}, el canal real "
        f"explica {ult['canal_real_pc']:.1f} por ciento y el financiero "
        f"{ult['canal_financiero_pc']:.1f} por ciento de la varianza."
    )
    print("\n" + lectura.replace("**", ""))

    ctx = {"nombre": nombre, "descripcion": spec["descripcion"],
           "columnas": list(X.columns), "n_obs": len(X), "rezagos": p,
           "raices": raices, "johansen": tj, "rango": rango, "engle_granger": eg,
           "vecm": tabla_vecm, "granger": gr, "canales": canales,
           "lectura_canales": lectura, "diagnosticos": diag}
    return ctx, figuras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bloque",
                    choices=["comercial", "financiero", "balanza_pagos", "todos"],
                    default="todos")
    args = ap.parse_args()

    _titulo("1. Datos")
    try:
        mensual, trimestral = dataset.construir()
    except FileNotFoundError as e:
        print(f"\n{e}")
        sys.exit(1)

    origenes = pd.read_csv(config.DATA_PROC / "origen_de_los_datos.csv")
    print(origenes[["variable", "origen"]].to_string(index=False))
    print(f"\nPanel mensual:    {mensual.shape[0]} observaciones, "
          f"{mensual.index.min().date()} a {mensual.index.max().date()}")
    print(f"Panel trimestral: {trimestral.shape[0]} observaciones, "
          f"{trimestral.index.min().date()} a {trimestral.index.max().date()}")

    _titulo("2. Descripcion")
    figuras = descriptivo.ejecutar(mensual, trimestral)
    print(f"{len(figuras)} figuras descriptivas")

    bloques = []
    for spec in config.BLOQUES:
        if args.bloque not in ("todos", spec["nombre"]):
            continue
        base = mensual if spec["frecuencia"] == "M" else trimestral
        try:
            ctx, figs = correr_bloque(base, spec)
            bloques.append(ctx)
            figuras += figs
        except Exception as e:
            print(f"\nBloque {spec['nombre']} fallo: {type(e).__name__} - {e}")

    _titulo("3. Reporte")
    ruta = reporte.escribir({"origenes": origenes, "bloques": bloques,
                             "figuras": figuras, "panel": mensual,
                             "panel_q": trimestral})
    print(f"Reporte: {ruta}")
    print(f"Figuras: {len(figuras)} en {config.FIGURAS}")
    print(f"Tablas:  {len(list(config.TABLAS.glob('*.csv')))} en {config.TABLAS}")


if __name__ == "__main__":
    main()
