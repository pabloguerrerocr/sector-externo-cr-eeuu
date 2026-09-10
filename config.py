# -*- coding: utf-8 -*-
"""
Configuracion central.

Efecto del ciclo economico y la politica monetaria de Estados Unidos
sobre el sector externo de Costa Rica: 2015-2025.

Todo lo que se cambia a mano (periodo, series, rutas, colores) vive aqui.
"""
from pathlib import Path

# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent
DATA_RAW = RAIZ / "data" / "raw"
DATA_PROC = RAIZ / "data" / "procesado"
SALIDAS = RAIZ / "salidas"
FIGURAS = SALIDAS / "figuras"
TABLAS = SALIDAS / "tablas"

for _d in (DATA_RAW, DATA_PROC, FIGURAS, TABLAS):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Periodo de estudio
# --------------------------------------------------------------------------
INICIO = "2015-01-01"
FIN = "2025-12-31"

# --------------------------------------------------------------------------
# Estados Unidos - FRED (publico, sin llave). Se cachea en data/raw/cache/
# --------------------------------------------------------------------------
FRED = {
    "pib_eeuu":  {"id": "GDPC1",           "frec": "Q", "etiqueta": "PIB real EE.UU. (mm USD encadenados)"},
    "crec_eeuu": {"id": "A191RL1Q225SBEA", "frec": "Q", "etiqueta": "Crecimiento PIB real EE.UU. (% anualizado)"},
    "ffr":       {"id": "FEDFUNDS",        "frec": "M", "etiqueta": "Tasa de fondos federales (%)"},
    "ipi_eeuu":  {"id": "INDPRO",          "frec": "M", "etiqueta": "Produccion industrial EE.UU. (indice)"},
    "t2y":       {"id": "DGS2",            "frec": "D", "etiqueta": "Bono del Tesoro EE.UU. 2 anos (%)"},
    "dolar":     {"id": "DTWEXBGS",        "frec": "D", "etiqueta": "Indice amplio del dolar (nominal)"},
}

# --------------------------------------------------------------------------
# Costa Rica - archivos Excel descargados del portal del BCCR
#   https://sdd.bccr.fi.cr/es/IndicadoresEconomicos/Inicio/
#
# 'columna'    : cual columna de valores usar (algunos cuadros traen varias)
# 'agregacion' : promedio para tasas y precios, ultimo para saldos
# 'acumulada'  : True si el cuadro publica cifras acumuladas en el ano
# --------------------------------------------------------------------------
BCCR = {
    "tc_venta": {
        "archivo": "tipo_cambio.xlsx", "columna": 2, "agregacion": "promedio",
        "acumulada": False, "frec": "M",
        "etiqueta": "Tipo de cambio de venta (colones por USD)",
        "cuadro": "Contenedor/6?Cuadro=1",
    },
    "balcom": {
        "archivo": "balance_comercial.xlsx", "columna": 1, "agregacion": "ultimo",
        "acumulada": True, "frec": "M",
        "etiqueta": "Balance comercial mensual (millones USD)",
        "cuadro": "Contenedor/452?Cuadro=112",
    },
    "reservas": {
        "archivo": "reservas.xlsx", "columna": 1, "agregacion": "ultimo",
        "acumulada": False, "frec": "M",
        "etiqueta": "Reservas internacionales netas (millones USD)",
        "cuadro": "Contenedor/516?Cuadro=70",
    },
    "tpm": {
        "archivo": "tpm.xlsx", "columna": 1, "agregacion": "promedio",
        "acumulada": False, "frec": "M",
        "etiqueta": "Tasa de politica monetaria del BCCR (%)",
        "cuadro": "Contenedor/358?Cuadro=223",
    },
    "itcer": {
        "archivo": "itcer.xlsx", "columna": 1, "agregacion": "promedio",
        "acumulada": False, "frec": "M",
        "etiqueta": "ITCER multilateral (indice, base ene-1997 = 100)",
        "cuadro": "buscar 'tipo de cambio efectivo real' en el portal",
    },
    "export_cr": {
        "archivo": "exportaciones.xlsx", "columna": 5, "agregacion": "ultimo",
        "acumulada": True, "frec": "M",
        "etiqueta": "Exportaciones FOB mensuales (millones USD)",
        "cuadro": "buscar 'exportaciones FOB acumuladas' en el portal",
    },
    "cuenta_fin": {
        "archivo": "balanza_pagos.xlsx", "columna": 68, "agregacion": "promedio",
        "acumulada": False, "frec": "Q",
        "etiqueta": "Cuenta financiera de la balanza de pagos (millones USD)",
        "cuadro": "buscar 'balanza de pagos trimestral MBP6' en el portal",
    },
}

# --------------------------------------------------------------------------
# Bloques de modelacion
#
# Todos los bloques comparten las variables de EE.UU. -el ciclo real y la
# politica monetaria- y cambian las de Costa Rica. Asi la descomposicion de
# varianza de cada bloque contesta la misma pregunta sobre una parte distinta
# del sector externo.
#
# Cuatro variables con 132 observaciones mensuales es una relacion sana entre
# parametros y datos. Meter las siete en un solo VAR no lo seria.
# --------------------------------------------------------------------------
BLOQUE_COMERCIAL = {
    "nombre": "comercial",
    "frecuencia": "M",
    "variables": ["ipi_eeuu", "ffr", "export_cr", "itcer"],
    "logaritmo": ["ipi_eeuu", "export_cr", "itcer"],
    "max_lags": 12,
    "descripcion": "canal real y canal financiero sobre las exportaciones y la "
                   "competitividad medida por el ITCER",
}
BLOQUE_FINANCIERO = {
    "nombre": "financiero",
    "frecuencia": "M",
    "variables": ["ipi_eeuu", "ffr", "reservas", "tpm"],
    "logaritmo": ["ipi_eeuu", "reservas"],
    "max_lags": 12,
    "descripcion": "transmision hacia las reservas y la respuesta de politica "
                   "monetaria del BCCR",
}
BLOQUE_BALANZA = {
    "nombre": "balanza_pagos",
    "frecuencia": "Q",
    "variables": ["pib_eeuu", "ffr", "cuenta_fin"],
    "logaritmo": ["pib_eeuu"],   # cuenta_fin cambia de signo: no admite log
    "max_lags": 4,
    "descripcion": "flujos de capital medidos por la cuenta financiera de la "
                   "balanza de pagos; trimestral, deliberadamente parsimonioso "
                   "porque solo hay ~44 observaciones",
}
BLOQUES = [BLOQUE_COMERCIAL, BLOQUE_FINANCIERO, BLOQUE_BALANZA]

# Choque COVID: dummy exogena. Sin esto, 2020 domina la estimacion.
COVID_MENSUAL = ("2020-03-01", "2020-08-01")
COVID_TRIMESTRAL = ("2020-01-01", "2020-06-30")

NIVEL_SIG = 0.05      # nivel de significancia de todas las pruebas
PERIODOS_IRF = 24     # horizonte de las funciones impulso-respuesta

# --------------------------------------------------------------------------
# Estilo de graficos (paleta categorica validada, orden fijo)
# --------------------------------------------------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
          "#008300", "#4a3aa7", "#e34948"]
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TINTA_3 = "#8a8880"
SUPERFICIE = "#fcfcfb"
REJILLA = "#e6e5e0"
DPI = 300
