# -*- coding: utf-8 -*-
"""
Exporta los resultados que usa el tablero interactivo del sitio.

    python exportar_tablero.py

Sin descargas: lee data/procesado/ y reestima los bloques igual que main.py
(mismas transformaciones, dummy COVID y rezagos HQIC). Escribe dos tablas:

  salidas/tablas/14_irf_bandas.csv
      respuesta de cada variable tica a los choques de EE.UU., con la banda
      Monte Carlo al 95 % (500 replicas, semilla 7: la misma de las figuras).
  salidas/tablas/15_fevd_especificaciones.csv
      descomposicion de varianza en cada horizonte con tres identificaciones:
      Cholesky base, Cholesky con la Fed primero y generalizada (Pesaran-Shin).
"""
from __future__ import annotations

import warnings

import pandas as pd
from statsmodels.tsa.api import VAR

import config
from robustez_cholesky import cargar, fevd_cholesky, fevd_generalizada, ordenes
from src import dataset

warnings.filterwarnings("ignore")


def main():
    irf_filas, fevd_filas = [], []
    for spec in config.BLOQUES:
        frec = spec["frecuencia"]
        X = dataset.transformar(cargar(frec), spec)
        rango = config.COVID_MENSUAL if frec == "M" else config.COVID_TRIMESTRAL
        exog = dataset.dummy_covid(X.index, rango)
        p = max(int(VAR(X, exog=exog).select_order(spec["max_lags"]).selected_orders["hqic"]), 1)
        periodos = config.PERIODOS_IRF if frec == "M" else 12
        real = next(c for c in X.columns if "ipi" in c or "pib" in c)
        objetivos = [c for c in X.columns if c not in (real, "ffr")]

        base = VAR(X, exog=exog).fit(p)
        irf = base.irf(periodos)
        inf, sup = irf.errband_mc(orth=True, repl=500, signif=0.05, seed=7)
        nombres = list(base.names)
        for v in objetivos:
            i = nombres.index(v)
            for imp in (real, "ffr"):
                j = nombres.index(imp)
                for h in range(periodos + 1):
                    irf_filas.append({"bloque": spec["nombre"], "respuesta": v, "impulso": imp,
                                      "horizonte": h, "efecto": irf.orth_irfs[h, i, j],
                                      "inferior": inf[h, i, j], "superior": sup[h, i, j]})

        fed_primero = VAR(X[ordenes(list(X.columns))["EE.UU. invertido (Fed primero)"]],
                          exog=exog).fit(p)
        for nombre, res, fn in (("base", base, fevd_cholesky),
                                ("fed_primero", fed_primero, fevd_cholesky),
                                ("generalizada", base, fevd_generalizada)):
            n = list(res.names)
            for H in range(1, periodos + 1):
                d = fn(res, H)
                for v in objetivos:
                    i = n.index(v)
                    fevd_filas.append({"bloque": spec["nombre"], "especificacion": nombre,
                                       "variable": v, "horizonte": H,
                                       "canal_real_pc": d[i, n.index(real)],
                                       "canal_financiero_pc": d[i, n.index("ffr")]})
        print(f"{spec['nombre']}: {len(objetivos)} variables, {periodos} periodos")

    pd.DataFrame(irf_filas).to_csv(config.TABLAS / "14_irf_bandas.csv", index=False)
    pd.DataFrame(fevd_filas).to_csv(config.TABLAS / "15_fevd_especificaciones.csv", index=False)
    print("Tablas 14 y 15 en", config.TABLAS)


if __name__ == "__main__":
    main()
