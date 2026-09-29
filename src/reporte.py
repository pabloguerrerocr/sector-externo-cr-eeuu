# -*- coding: utf-8 -*-
"""
Arma salidas/reporte.md: que dio cada prueba, que figura la respalda y como
se lee. Es el borrador del capitulo de resultados.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

import config


def _md(df: pd.DataFrame, decimales: int = 4) -> str:
    return df.round(decimales).to_markdown(index=False)


def escribir(contexto: dict) -> str:
    hoy = dt.date.today().isoformat()
    panel = contexto["panel"]
    L: list[str] = []
    A = L.append

    A("# Efecto del ciclo economico y la politica monetaria de EE.UU.")
    A("## sobre el sector externo de Costa Rica, 2015-2025")
    A("")
    A(f"Generado el {hoy} por `main.py`. "
      f"Muestra: {panel.index.min().date()} a {panel.index.max().date()}, "
      f"{len(panel)} observaciones mensuales.")
    A("")
    A("**Todos los datos son reales.** Estados Unidos viene de FRED (Reserva Federal "
      "de San Luis) y Costa Rica de los cuadros publicados por el Banco Central de "
      "Costa Rica en su portal de indicadores economicos.")
    A("")

    A("## Origen de los datos")
    A("")
    A(_md(contexto["origenes"]))
    A("")

    A("## Pregunta")
    A("")
    A("Costa Rica es una economia pequena y abierta expuesta a Estados Unidos por "
      "dos vias. El **canal real**: cuando la economia estadounidense crece, aumenta "
      "la demanda de exportaciones ticas. El **canal financiero**: cuando la Reserva "
      "Federal sube su tasa, el capital tiende a salir de economias emergentes hacia "
      "activos en dolares, y eso presiona el tipo de cambio y las reservas.")
    A("")
    A("La pregunta es cual de los dos pesa mas, y la respuesta esta en la "
      "descomposicion de la varianza del error de prediccion de cada bloque.")
    A("")

    for bloque in contexto["bloques"]:
        n = bloque["nombre"]
        A(f"## Bloque {n}")
        A("")
        A(f"*{bloque['descripcion']}*")
        A("")
        A(f"Variables: `{'`, `'.join(bloque['columnas'])}`. "
          f"Observaciones: {bloque['n_obs']}. Rezagos elegidos por HQIC: {bloque['rezagos']}.")
        A("")

        A("### Orden de integracion")
        A("")
        A(_md(bloque["raices"][["variable", "transformacion", "adf_p", "kpss_p",
                                "conclusion", "orden_integracion"]]))
        A("")
        A("ADF rechaza raiz unitaria cuando p < 0.05; KPSS rechaza estacionariedad "
          "cuando p < 0.05. Cuando se contradicen, la fila queda como *ambiguo* y asi "
          "se reporta, sin forzar una conclusion.")
        A("")

        A("### Cointegracion")
        A("")
        A("**Johansen**")
        A("")
        A(_md(bloque["johansen"]))
        A("")
        A(f"Rango al 5 por ciento: **r = {bloque['rango']}**. "
          + ("Hay relacion de largo plazo entre las variables, de modo que existe un "
             "equilibrio al que el sistema regresa tras un choque."
             if bloque["rango"] > 0 else
             "No hay evidencia de relacion de largo plazo."))
        A("")
        A("**Engle-Granger, los ocho pares con menor p-valor**")
        A("")
        A(_md(bloque["engle_granger"].head(8)))
        A("")
        if bloque.get("vecm") is not None:
            A("**Vector de largo plazo y velocidad de ajuste (VECM)**")
            A("")
            A(bloque["vecm"].round(4).to_markdown())
            A("")
            A("El coeficiente de ajuste dice que fraccion del desequilibrio se corrige "
              "cada mes. Negativo y significativo en la variable tica significa que "
              "Costa Rica es la que se ajusta, no Estados Unidos: exactamente lo que "
              "predice la teoria para una economia pequena y abierta.")
            A("")

        A("### Canal real frente a canal financiero")
        A("")
        A("Porcentaje de la varianza del error de prediccion atribuido a cada choque:")
        A("")
        A(_md(bloque["canales"], 2))
        A("")
        A(bloque["lectura_canales"])
        A("")

        A("**Causalidad de Granger, pares significativos al 5 por ciento**")
        A("")
        sig = bloque["granger"][bloque["granger"]["causa_en_sentido_granger"] == "si"]
        A(_md(sig) if len(sig) else "Ningun par resulto significativo.")
        A("")

        A("**Diagnosticos**")
        A("")
        A(_md(bloque["diagnosticos"]))
        A("")

    A("## Figuras")
    A("")
    for r in contexto["figuras"]:
        A(f"- `salidas/figuras/{r.name}`")
    A("")
    A("## Tablas")
    A("")
    for r in sorted(config.TABLAS.glob("*.csv")):
        A(f"- `salidas/tablas/{r.name}`")
    A("")

    A("## Limitaciones que hay que declarar")
    A("")
    A("- **La produccion industrial de EE.UU. es una aproximacion mensual del ciclo "
      "real.** El PIB solo existe trimestral y 44 trimestres no alcanzan para un VAR. "
      "Es una decision de frecuencia, no una equivalencia.")
    A("- **El balance comercial no es lo mismo que las exportaciones.** El BCCR "
      "publica el saldo acumulado; aqui se desacumulo para obtener el flujo mensual. "
      "Un choque externo puede mover importaciones y exportaciones a la vez, y el "
      "saldo neto esconde parte de ese movimiento.")
    A("- **El ITCER es multilateral.** Mide la competitividad frente a una canasta de "
      "socios, no solo frente a EE.UU., asi que mezcla el efecto del dolar con el de "
      "las demas monedas. Un tipo de cambio real bilateral con EE.UU. aislaria mejor "
      "el canal estadounidense.")
    A("- **Identificacion de Cholesky con EE.UU. ordenado primero.** Supone que Costa "
      "Rica no afecta contemporaneamente a Estados Unidos. Es razonable para una "
      "economia de este tamano, pero sigue siendo un supuesto: conviene reportar la "
      "robustez invirtiendo el orden de las variables ticas.")
    A("- **2020 se controla con una dummy exogena.** Sin ese control el choque COVID "
      "domina la estimacion y las respuestas al impulso se vuelven irreconocibles.")
    A("")

    texto = "\n".join(L)
    ruta = config.SALIDAS / "reporte.md"
    ruta.write_text(texto, encoding="utf-8")
    return str(ruta)
