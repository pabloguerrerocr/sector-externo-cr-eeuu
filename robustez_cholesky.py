# -*- coding: utf-8 -*-
"""
Robustez de la descomposicion de varianza al orden de Cholesky.

    python robustez_cholesky.py

La descomposicion de main.py identifica los choques con Cholesky y EE.UU.
primero. El orden es un supuesto, y el README lo declara como robustez
pendiente. Este script la hace, sin descargar nada (lee data/procesado/):

  1. Reestima cada bloque con los cuatro ordenes posibles que respetan
     "EE.UU. antes que Costa Rica": base, variables ticas invertidas, variables
     de EE.UU. invertidas (tasa de la Fed antes que el ciclo real) y ambas.
  2. Calcula la descomposicion de varianza generalizada (Pesaran y Shin,
     1998), que no depende del orden de las variables. Si el canal financiero
     domina tambien ahi, el resultado no es un artefacto del ordenamiento.

Mismo panel, mismas transformaciones, misma dummy COVID y mismos rezagos (HQIC)
que main.py. No toca las salidas existentes: escribe
salidas/tablas/13_robustez_cholesky.csv y salidas/robustez_cholesky.md.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

import config
from src import dataset

warnings.filterwarnings("ignore")

HORIZONTES = {"M": (6, 12, 24), "Q": (6, 12)}
ETIQUETAS = {
    "log_export_cr": "Exportaciones FOB", "log_itcer": "ITCER",
    "log_reservas": "Reservas internacionales", "tpm": "Tasa de politica del BCCR",
    "cuenta_fin": "Cuenta financiera",
}


def cargar(frecuencia: str) -> pd.DataFrame:
    archivo = "panel_mensual.csv" if frecuencia == "M" else "panel_trimestral.csv"
    return pd.read_csv(config.DATA_PROC / archivo, index_col="fecha", parse_dates=True)


def fevd_cholesky(res, H: int) -> np.ndarray:
    """decomp[i, j]: % de la varianza de i a H periodos explicado por j."""
    return res.fevd(H).decomp[:, H - 1, :] * 100


def fevd_generalizada(res, H: int) -> np.ndarray:
    """Pesaran y Shin (1998), filas normalizadas a 100. Invariante al orden."""
    phi = res.ma_rep(H - 1)                  # (H, k, k): Phi_0 ... Phi_{H-1}
    sigma = np.asarray(res.sigma_u)
    num = np.zeros_like(sigma)
    den = np.zeros(sigma.shape[0])
    for h in range(H):
        a = phi[h] @ sigma
        num += a ** 2
        den += np.diag(a @ phi[h].T)
    theta = num / np.diag(sigma)[None, :] / den[:, None]
    return theta / theta.sum(axis=1, keepdims=True) * 100


def ordenes(cols: list[str]) -> dict[str, list[str]]:
    eeuu = [c for c in cols if "ipi" in c or "pib" in c or c == "ffr"]
    cr = [c for c in cols if c not in eeuu]
    out = {"base (main.py)": eeuu + cr,
           "EE.UU. invertido (Fed primero)": eeuu[::-1] + cr}
    if len(cr) > 1:
        out["Costa Rica invertido"] = eeuu + cr[::-1]
        out["ambos invertidos"] = eeuu[::-1] + cr[::-1]
    return out


def main():
    filas = []
    for spec in config.BLOQUES:
        frec = spec["frecuencia"]
        X = dataset.transformar(cargar(frec), spec)
        rango = config.COVID_MENSUAL if frec == "M" else config.COVID_TRIMESTRAL
        exog = dataset.dummy_covid(X.index, rango)
        p = VAR(X, exog=exog).select_order(spec["max_lags"]).selected_orders["hqic"]
        p = max(int(p), 1)
        real = next(c for c in X.columns if "ipi" in c or "pib" in c)
        objetivos = [c for c in X.columns if c not in (real, "ffr")]
        print(f"\nBloque {spec['nombre']}: n = {len(X)}, rezagos HQIC = {p}")

        especificaciones = {nombre: VAR(X[orden], exog=exog).fit(p)
                            for nombre, orden in ordenes(list(X.columns)).items()}
        base = especificaciones["base (main.py)"]
        especificaciones["generalizada (sin orden)"] = base

        for nombre, res in especificaciones.items():
            nombres = list(res.names)
            for H in HORIZONTES[frec]:
                d = (fevd_generalizada(res, H) if nombre.startswith("generalizada")
                     else fevd_cholesky(res, H))
                for v in objetivos:
                    i = nombres.index(v)
                    r, f = d[i, nombres.index(real)], d[i, nombres.index("ffr")]
                    filas.append({"bloque": spec["nombre"], "especificacion": nombre,
                                  "variable": v, "horizonte": H,
                                  "canal_real_pc": r, "canal_financiero_pc": f,
                                  "canal_dominante": "financiero" if f > r else "real"})

    t = pd.DataFrame(filas)
    t.to_csv(config.TABLAS / "13_robustez_cholesky.csv", index=False)

    # Resumen: cuantas combinaciones domina cada canal en cada especificacion.
    resumen = (t.groupby("especificacion", sort=False)["canal_dominante"]
                 .apply(lambda s: f"{(s == 'financiero').sum()} de {len(s)}"))
    print("\nCombinaciones donde domina el canal financiero")
    print(resumen.to_string())

    largo = t[t.horizonte == t.groupby(["bloque", "variable"]).horizonte.transform("max")]
    piv = largo.pivot_table(index=["bloque", "variable", "horizonte"], columns="especificacion",
                            values="canal_financiero_pc", sort=False).round(1)
    piv_r = largo.pivot_table(index=["bloque", "variable", "horizonte"], columns="especificacion",
                              values="canal_real_pc", sort=False).round(1)
    print("\nCanal financiero (% de la varianza) en el horizonte mas largo")
    print(piv.to_string())
    print("\nCanal real (% de la varianza) en el horizonte mas largo")
    print(piv_r.to_string())

    with open(config.SALIDAS / "robustez_cholesky.md", "w", encoding="utf-8") as fh:
        fh.write("# Robustez al orden de Cholesky\n\n")
        fh.write("Generado por `robustez_cholesky.py`. Mismo panel, transformaciones, "
                 "dummy COVID y rezagos (HQIC) que `main.py`.\n\n")
        fh.write("## Combinaciones donde domina el canal financiero\n\n")
        fh.write(resumen.rename("combinaciones").to_frame().to_markdown() + "\n\n")
        fh.write("## Canal financiero en el horizonte mas largo (% de la varianza)\n\n")
        fh.write(piv.to_markdown() + "\n\n")
        fh.write("## Canal real en el horizonte mas largo (% de la varianza)\n\n")
        fh.write(piv_r.to_markdown() + "\n\n")
        fh.write("La especificacion generalizada (Pesaran y Shin, 1998) no depende del "
                 "orden de las variables; sus filas se normalizan a 100.\n")
    print(f"\nTabla: {config.TABLAS / '13_robustez_cholesky.csv'}")


if __name__ == "__main__":
    main()
