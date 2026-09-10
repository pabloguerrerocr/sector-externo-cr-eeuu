# -*- coding: utf-8 -*-
"""
Lector de los archivos Excel que exporta el portal del BCCR (sdd.bccr.fi.cr).

Formato de esos archivos, verificado en los cuatro cuadros descargados:
    fila 0   titulo del cuadro
    fila 1   unidad o nota
    filas 2-3 vacias
    fila 4   encabezado: 'Fecha' y una o mas columnas de valores
    fila 5+  datos

Ademas resuelve dos cosas que el BCCR entrega de forma incomoda:
  - series diarias que hay que llevar a mensual
  - series acumuladas en el ano ('cifras acumuladas al mes'), que hay que
    desacumular para obtener el flujo del mes
"""
from __future__ import annotations

import pandas as pd


def leer(ruta, columna: int = 1) -> tuple[pd.Series, str, str]:
    """
    Devuelve (serie, titulo, unidad).
    `columna` elige cual columna de valores usar cuando el cuadro trae varias
    (por ejemplo compra y venta del tipo de cambio).
    """
    crudo = pd.read_excel(ruta, sheet_name=0, header=None)
    titulo = str(crudo.iloc[0, 0]).strip()
    unidad = str(crudo.iloc[1, 0]).strip()

    # Localiza la fila del encabezado buscando la celda que dice 'Fecha'.
    fila_enc = None
    for i in range(min(15, len(crudo))):
        if str(crudo.iloc[i, 0]).strip().lower().startswith("fecha"):
            fila_enc = i
            break
    if fila_enc is None:
        raise ValueError(f"No encontre la fila de encabezado en {ruta}")

    datos = crudo.iloc[fila_enc + 1:, [0, columna]].copy()
    datos.columns = ["fecha", "valor"]
    datos["fecha"] = pd.to_datetime(datos["fecha"], errors="coerce")
    datos["valor"] = pd.to_numeric(datos["valor"], errors="coerce")
    serie = datos.dropna().set_index("fecha")["valor"].sort_index()
    return serie, titulo, unidad


def a_mensual(s: pd.Series, como: str = "promedio") -> pd.Series:
    """
    Lleva una serie a frecuencia mensual con fecha al inicio del mes.
    'promedio' para tasas e indices, 'ultimo' para saldos de fin de periodo.
    """
    if como == "ultimo":
        return s.resample("MS").last().dropna()
    return s.resample("MS").mean().dropna()


def desacumular(s: pd.Series) -> pd.Series:
    """
    Convierte una serie acumulada dentro de cada ano en el flujo de cada mes.

    El BCCR publica el balance comercial como 'cifras acumuladas al mes': el
    dato de marzo es enero+febrero+marzo. El flujo de marzo es la diferencia
    con febrero, salvo en enero, donde el acumulado ya es el flujo del mes.
    """
    s = s.sort_index()
    flujo = s.diff()
    enero = s.index.month == 1
    flujo[enero] = s[enero]
    return flujo.dropna()
