# Efecto del ciclo economico y la politica monetaria de EE.UU.
## sobre el sector externo de Costa Rica, 2015-2025

Generado el 2026-09-10 por `main.py`. Muestra: 2015-01-01 a 2025-12-01, 132 observaciones mensuales.

**Todos los datos son reales.** Estados Unidos viene de FRED (Reserva Federal de San Luis) y Costa Rica de los cuadros publicados por el Banco Central de Costa Rica en su portal de indicadores economicos.

## Origen de los datos

| variable   | etiqueta                                                | frecuencia   | origen                        | titulo_original                                                              |
|:-----------|:--------------------------------------------------------|:-------------|:------------------------------|:-----------------------------------------------------------------------------|
| pib_eeuu   | PIB real EE.UU. (mm USD encadenados)                    | Q            | FRED - GDPC1                  | nan                                                                          |
| ffr        | Tasa de fondos federales (%)                            | M            | FRED - FEDFUNDS               | nan                                                                          |
| ipi_eeuu   | Produccion industrial EE.UU. (indice)                   | M            | FRED - INDPRO                 | nan                                                                          |
| t2y        | Bono del Tesoro EE.UU. 2 anos (%)                       | D            | FRED - DGS2                   | nan                                                                          |
| dolar      | Indice amplio del dolar (nominal)                       | D            | FRED - DTWEXBGS               | nan                                                                          |
| tc_venta   | Tipo de cambio de venta (colones por USD)               | M            | BCCR - tipo_cambio.xlsx       | Tipo cambio de compra y de venta del dólar de los Estados Unidos de América  |
| balcom     | Balance comercial mensual (millones USD)                | M            | BCCR - balance_comercial.xlsx | Balance comercial acumulado                                                  |
| reservas   | Reservas internacionales netas (millones USD)           | M            | BCCR - reservas.xlsx          | Reservas netas del Banco Central                                             |
| tpm        | Tasa de politica monetaria del BCCR (%)                 | M            | BCCR - tpm.xlsx               | Tasa de política monetaria                                                   |
| itcer      | ITCER multilateral (indice, base ene-1997 = 100)        | M            | BCCR - itcer.xlsx             | Índice de tipo de cambio efectivo real multilateral con ponderadores móviles |
| export_cr  | Exportaciones FOB mensuales (millones USD)              | M            | BCCR - exportaciones.xlsx     | Exportaciones FOB acumuladas                                                 |
| cuenta_fin | Cuenta financiera de la balanza de pagos (millones USD) | Q            | BCCR - balanza_pagos.xlsx     | Balanza de pagos trimestral (MBP6)                                           |

## Pregunta

Costa Rica es una economia pequena y abierta expuesta a Estados Unidos por dos vias. El **canal real**: cuando la economia estadounidense crece, aumenta la demanda de exportaciones ticas. El **canal financiero**: cuando la Reserva Federal sube su tasa, el capital tiende a salir de economias emergentes hacia activos en dolares, y eso presiona el tipo de cambio y las reservas.

La pregunta es cual de los dos pesa mas, y la respuesta esta en la descomposicion de la varianza del error de prediccion de cada bloque.

## Bloque comercial

*canal real y canal financiero sobre las exportaciones y la competitividad medida por el ITCER*

Variables: `log_ipi_eeuu`, `ffr`, `log_export_cr`, `log_itcer`. Observaciones: 132. Rezagos elegidos por HQIC: 3.

### Orden de integracion

| variable      | transformacion   |   adf_p |   kpss_p | conclusion      | orden_integracion   |
|:--------------|:-----------------|--------:|---------:|:----------------|:--------------------|
| log_ipi_eeuu  | nivel            |  0.0693 |   0.1    | ambiguo         | I(1)                |
| log_ipi_eeuu  | 1a diferencia    |  0      |   0.1    | estacionaria    | I(1)                |
| ffr           | nivel            |  0.1921 |   0.0119 | no estacionaria | I(1)                |
| ffr           | 1a diferencia    |  0.038  |   0.1    | estacionaria    | I(1)                |
| log_export_cr | nivel            |  0.9026 |   0.01   | no estacionaria | I(1)                |
| log_export_cr | 1a diferencia    |  0.0002 |   0.1    | estacionaria    | I(1)                |
| log_itcer     | nivel            |  0.8199 |   0.01   | no estacionaria | I(1)                |
| log_itcer     | 1a diferencia    |  0      |   0.1    | estacionaria    | I(1)                |

ADF rechaza raiz unitaria cuando p < 0.05; KPSS rechaza estacionariedad cuando p < 0.05. Cuando se contradicen, la fila queda como *ambiguo* y asi se reporta, sin forzar una conclusion.

### Cointegracion

**Johansen**

| hipotesis   |   traza |   traza_crit_5pc | traza_rechaza   |   max_valor_propio |   mvp_crit_5pc | mvp_rechaza   |   valor_propio |
|:------------|--------:|-----------------:|:----------------|-------------------:|---------------:|:--------------|---------------:|
| r <= 0      | 30.7192 |          47.8545 | no              |            13.5738 |        27.5858 | no            |         0.0999 |
| r <= 1      | 17.1454 |          29.7961 | no              |             9.3418 |        21.1314 | no            |         0.0699 |
| r <= 2      |  7.8036 |          15.4943 | no              |             6.4492 |        14.2639 | no            |         0.0488 |
| r <= 3      |  1.3544 |           3.8415 | no              |             1.3544 |         3.8415 | no            |         0.0104 |

Rango al 5 por ciento: **r = 0**. No hay evidencia de relacion de largo plazo.

**Engle-Granger, los ocho pares con menor p-valor**

| dependiente   | independiente   |   estadistico |   p_valor |   critico_5pc | cointegran   |
|:--------------|:----------------|--------------:|----------:|--------------:|:-------------|
| ffr           | log_export_cr   |       -3.7166 |    0.0174 |       -3.3832 | si           |
| log_ipi_eeuu  | ffr             |       -3.4868 |    0.0336 |       -3.3832 | si           |
| log_ipi_eeuu  | log_export_cr   |       -3.3666 |    0.0462 |       -3.3832 | si           |
| log_ipi_eeuu  | log_itcer       |       -3.2743 |    0.0584 |       -3.3832 | no           |
| log_export_cr | ffr             |       -2.3783 |    0.3352 |       -3.3832 | no           |
| log_itcer     | ffr             |       -1.9669 |    0.5457 |       -3.3832 | no           |
| ffr           | log_itcer       |       -1.8463 |    0.607  |       -3.3832 | no           |
| log_itcer     | log_export_cr   |       -1.6601 |    0.6949 |       -3.3832 | no           |

### Canal real frente a canal financiero

Porcentaje de la varianza del error de prediccion atribuido a cada choque:

| variable      |   horizonte |   canal_real_pc |   canal_financiero_pc |   razon_real_sobre_financiero | canal_dominante   |
|:--------------|------------:|----------------:|----------------------:|------------------------------:|:------------------|
| log_export_cr |           6 |            1.8  |                  2.98 |                          0.6  | financiero        |
| log_export_cr |          12 |            4.05 |                  6.01 |                          0.67 | financiero        |
| log_export_cr |          24 |            6.25 |                 10.43 |                          0.6  | financiero        |
| log_itcer     |           6 |            1.68 |                  5.35 |                          0.31 | financiero        |
| log_itcer     |          12 |            2.54 |                 22.76 |                          0.11 | financiero        |
| log_itcer     |          24 |            4.49 |                 43.22 |                          0.1  | financiero        |

En 6 de 6 combinaciones de variable y horizonte domina el **canal financiero**. A 24 meses, sobre ITCER, el canal real explica 4.5 por ciento y el financiero 43.2 por ciento de la varianza.

**Causalidad de Granger, pares significativos al 5 por ciento**

| causa        | efecto        |   estadistico_F |   p_valor | causa_en_sentido_granger   |
|:-------------|:--------------|----------------:|----------:|:---------------------------|
| ffr          | log_ipi_eeuu  |         11.6456 |    0      | si                         |
| log_ipi_eeuu | ffr           |          5.355  |    0.0012 | si                         |
| log_itcer    | log_export_cr |          3.7617 |    0.0109 | si                         |
| ffr          | log_itcer     |          3.0396 |    0.0288 | si                         |
| ffr          | log_export_cr |          2.9898 |    0.0308 | si                         |

**Diagnosticos**

| prueba                             | H0                                          |   estadistico |   p_valor | conclusion   |
|:-----------------------------------|:--------------------------------------------|--------------:|----------:|:-------------|
| Portmanteau (autocorrelacion)      | sin autocorrelacion                         |      189.258  |    0.0004 | se rechaza   |
| Jarque-Bera multivariada           | residuos normales                           |      462.703  |    0      | se rechaza   |
| Estabilidad (raices del polinomio) | todas las raices fuera del circulo unitario |        1.0194 |  nan      | estable      |

## Bloque financiero

*transmision hacia las reservas y la respuesta de politica monetaria del BCCR*

Variables: `log_ipi_eeuu`, `ffr`, `log_reservas`, `tpm`. Observaciones: 132. Rezagos elegidos por HQIC: 3.

### Orden de integracion

| variable     | transformacion   |   adf_p |   kpss_p | conclusion      | orden_integracion   |
|:-------------|:-----------------|--------:|---------:|:----------------|:--------------------|
| log_ipi_eeuu | nivel            |  0.0693 |   0.1    | ambiguo         | I(1)                |
| log_ipi_eeuu | 1a diferencia    |  0      |   0.1    | estacionaria    | I(1)                |
| ffr          | nivel            |  0.1921 |   0.0119 | no estacionaria | I(1)                |
| ffr          | 1a diferencia    |  0.038  |   0.1    | estacionaria    | I(1)                |
| log_reservas | nivel            |  0.9452 |   0.01   | no estacionaria | I(1)                |
| log_reservas | 1a diferencia    |  0      |   0.1    | estacionaria    | I(1)                |
| tpm          | nivel            |  0.0524 |   0.1    | ambiguo         | I(1)                |
| tpm          | 1a diferencia    |  0.0082 |   0.1    | estacionaria    | I(1)                |

ADF rechaza raiz unitaria cuando p < 0.05; KPSS rechaza estacionariedad cuando p < 0.05. Cuando se contradicen, la fila queda como *ambiguo* y asi se reporta, sin forzar una conclusion.

### Cointegracion

**Johansen**

| hipotesis   |   traza |   traza_crit_5pc | traza_rechaza   |   max_valor_propio |   mvp_crit_5pc | mvp_rechaza   |   valor_propio |
|:------------|--------:|-----------------:|:----------------|-------------------:|---------------:|:--------------|---------------:|
| r <= 0      | 55.9824 |          47.8545 | si              |            30.7683 |        27.5858 | si            |         0.2122 |
| r <= 1      | 25.2141 |          29.7961 | no              |            11.8837 |        21.1314 | no            |         0.088  |
| r <= 2      | 13.3304 |          15.4943 | no              |            11.4861 |        14.2639 | no            |         0.0852 |
| r <= 3      |  1.8443 |           3.8415 | no              |             1.8443 |         3.8415 | no            |         0.0142 |

Rango al 5 por ciento: **r = 1**. Hay relacion de largo plazo entre las variables, de modo que existe un equilibrio al que el sistema regresa tras un choque.

**Engle-Granger, los ocho pares con menor p-valor**

| dependiente   | independiente   |   estadistico |   p_valor |   critico_5pc | cointegran   |
|:--------------|:----------------|--------------:|----------:|--------------:|:-------------|
| log_ipi_eeuu  | tpm             |       -3.7537 |    0.0156 |       -3.3832 | si           |
| log_ipi_eeuu  | ffr             |       -3.4868 |    0.0336 |       -3.3832 | si           |
| log_ipi_eeuu  | log_reservas    |       -3.3216 |    0.0518 |       -3.3832 | no           |
| tpm           | log_reservas    |       -3.2487 |    0.0622 |       -3.3832 | no           |
| tpm           | ffr             |       -3.1322 |    0.082  |       -3.3832 | no           |
| tpm           | log_ipi_eeuu    |       -2.0901 |    0.4816 |       -3.3832 | no           |
| ffr           | log_reservas    |       -1.6599 |    0.695  |       -3.3832 | no           |
| ffr           | tpm             |       -1.5784 |    0.7299 |       -3.3832 | no           |

**Vector de largo plazo y velocidad de ajuste (VECM)**

|              |   vector_1 |   ajuste_1 |   t_ajuste_1 |   p_ajuste_1 |
|:-------------|-----------:|-----------:|-------------:|-------------:|
| log_ipi_eeuu |     1      |    -0.3006 |      -5.5898 |       0      |
| ffr          |     0.0119 |    -3.2378 |      -6.2344 |       0      |
| log_reservas |    -0.0255 |    -0.3562 |      -1.6871 |       0.0916 |
| tpm          |    -0.0163 |     1.7026 |       1.5209 |       0.1283 |

El coeficiente de ajuste dice que fraccion del desequilibrio se corrige cada mes. Negativo y significativo en la variable tica significa que Costa Rica es la que se ajusta, no Estados Unidos: exactamente lo que predice la teoria para una economia pequena y abierta.

### Canal real frente a canal financiero

Porcentaje de la varianza del error de prediccion atribuido a cada choque:

| variable     |   horizonte |   canal_real_pc |   canal_financiero_pc |   razon_real_sobre_financiero | canal_dominante   |
|:-------------|------------:|----------------:|----------------------:|------------------------------:|:------------------|
| log_reservas |           6 |            1.46 |                  2.85 |                          0.51 | financiero        |
| log_reservas |          12 |            2.24 |                 17.07 |                          0.13 | financiero        |
| log_reservas |          24 |            3.27 |                 44.44 |                          0.07 | financiero        |
| tpm          |           6 |            0.51 |                 38.4  |                          0.01 | financiero        |
| tpm          |          12 |            0.26 |                 43.64 |                          0.01 | financiero        |
| tpm          |          24 |            0.58 |                 43.87 |                          0.01 | financiero        |

En 6 de 6 combinaciones de variable y horizonte domina el **canal financiero**. A 24 meses, sobre tasa de politica del BCCR, el canal real explica 0.6 por ciento y el financiero 43.9 por ciento de la varianza.

**Causalidad de Granger, pares significativos al 5 por ciento**

| causa        | efecto       |   estadistico_F |   p_valor | causa_en_sentido_granger   |
|:-------------|:-------------|----------------:|----------:|:---------------------------|
| ffr          | log_ipi_eeuu |         12.8511 |     0     | si                         |
| tpm          | ffr          |          9.681  |     0     | si                         |
| log_ipi_eeuu | ffr          |          8.756  |     0     | si                         |
| ffr          | log_reservas |          3.0875 |     0.027 | si                         |

**Diagnosticos**

| prueba                             | H0                                          |   estadistico |   p_valor | conclusion   |
|:-----------------------------------|:--------------------------------------------|--------------:|----------:|:-------------|
| Portmanteau (autocorrelacion)      | sin autocorrelacion                         |      171.385  |    0.0063 | se rechaza   |
| Jarque-Bera multivariada           | residuos normales                           |      494.829  |    0      | se rechaza   |
| Estabilidad (raices del polinomio) | todas las raices fuera del circulo unitario |        1.0271 |  nan      | estable      |

## Bloque balanza_pagos

*flujos de capital medidos por la cuenta financiera de la balanza de pagos; trimestral, deliberadamente parsimonioso porque solo hay ~44 observaciones*

Variables: `log_pib_eeuu`, `ffr`, `cuenta_fin`. Observaciones: 44. Rezagos elegidos por HQIC: 2.

### Orden de integracion

| variable     | transformacion   |   adf_p |   kpss_p | conclusion   | orden_integracion   |
|:-------------|:-----------------|--------:|---------:|:-------------|:--------------------|
| log_pib_eeuu | nivel            |  0.008  |   0.0993 | estacionaria | I(0)                |
| log_pib_eeuu | 1a diferencia    |  0      |   0.1    | estacionaria | I(0)                |
| ffr          | nivel            |  0.2068 |   0.1    | ambiguo      | revisar             |
| ffr          | 1a diferencia    |  0.12   |   0.1    | ambiguo      | revisar             |
| cuenta_fin   | nivel            |  0      |   0.0773 | estacionaria | I(0)                |
| cuenta_fin   | 1a diferencia    |  0.0428 |   0.1    | estacionaria | I(0)                |

ADF rechaza raiz unitaria cuando p < 0.05; KPSS rechaza estacionariedad cuando p < 0.05. Cuando se contradicen, la fila queda como *ambiguo* y asi se reporta, sin forzar una conclusion.

### Cointegracion

**Johansen**

| hipotesis   |   traza |   traza_crit_5pc | traza_rechaza   |   max_valor_propio |   mvp_crit_5pc | mvp_rechaza   |   valor_propio |
|:------------|--------:|-----------------:|:----------------|-------------------:|---------------:|:--------------|---------------:|
| r <= 0      | 43.228  |          29.7961 | si              |            31.0631 |        21.1314 | si            |         0.5227 |
| r <= 1      | 12.165  |          15.4943 | no              |            11.9335 |        14.2639 | no            |         0.2473 |
| r <= 2      |  0.2315 |           3.8415 | no              |             0.2315 |         3.8415 | no            |         0.0055 |

Rango al 5 por ciento: **r = 1**. Hay relacion de largo plazo entre las variables, de modo que existe un equilibrio al que el sistema regresa tras un choque.

**Engle-Granger, los ocho pares con menor p-valor**

| dependiente   | independiente   |   estadistico |   p_valor |   critico_5pc | cointegran   |
|:--------------|:----------------|--------------:|----------:|--------------:|:-------------|
| cuenta_fin    | ffr             |       -8.683  |    0      |       -3.4819 | si           |
| cuenta_fin    | log_pib_eeuu    |       -7.5979 |    0      |       -3.4819 | si           |
| ffr           | log_pib_eeuu    |       -2.3879 |    0.3306 |       -3.4819 | no           |
| ffr           | cuenta_fin      |       -1.4658 |    0.7741 |       -3.4819 | no           |
| log_pib_eeuu  | ffr             |       -1.4361 |    0.7849 |       -3.4819 | no           |
| log_pib_eeuu  | cuenta_fin      |       -0.7176 |    0.9447 |       -3.4819 | no           |

**Vector de largo plazo y velocidad de ajuste (VECM)**

|              |   vector_1 |   ajuste_1 |   t_ajuste_1 |   p_ajuste_1 |
|:-------------|-----------:|-----------:|-------------:|-------------:|
| log_pib_eeuu |     1      |     0.006  |       2.7479 |       0.006  |
| ffr          |     0.122  |     0.0764 |       1.7529 |       0.0796 |
| cuenta_fin   |     0.0019 |  -457.965  |      -4.7167 |       0      |

El coeficiente de ajuste dice que fraccion del desequilibrio se corrige cada mes. Negativo y significativo en la variable tica significa que Costa Rica es la que se ajusta, no Estados Unidos: exactamente lo que predice la teoria para una economia pequena y abierta.

### Canal real frente a canal financiero

Porcentaje de la varianza del error de prediccion atribuido a cada choque:

| variable   |   horizonte |   canal_real_pc |   canal_financiero_pc |   razon_real_sobre_financiero | canal_dominante   |
|:-----------|------------:|----------------:|----------------------:|------------------------------:|:------------------|
| cuenta_fin |           6 |            2.57 |                 21.34 |                          0.12 | financiero        |
| cuenta_fin |          12 |            2.79 |                 26.06 |                          0.11 | financiero        |

En 2 de 2 combinaciones de variable y horizonte domina el **canal financiero**. A 12 trimestres, sobre cuenta financiera, el canal real explica 2.8 por ciento y el financiero 26.1 por ciento de la varianza.

**Causalidad de Granger, pares significativos al 5 por ciento**

| causa        | efecto     |   estadistico_F |   p_valor | causa_en_sentido_granger   |
|:-------------|:-----------|----------------:|----------:|:---------------------------|
| ffr          | cuenta_fin |          8.3862 |    0.0004 | si                         |
| log_pib_eeuu | ffr        |          5.5103 |    0.0053 | si                         |

**Diagnosticos**

| prueba                             | H0                                          |   estadistico |   p_valor | conclusion    |
|:-----------------------------------|:--------------------------------------------|--------------:|----------:|:--------------|
| Portmanteau (autocorrelacion)      | sin autocorrelacion                         |       97.2969 |    0.0252 | se rechaza    |
| Jarque-Bera multivariada           | residuos normales                           |        6.4302 |    0.3768 | no se rechaza |
| Estabilidad (raices del polinomio) | todas las raices fuera del circulo unitario |        1.0057 |  nan      | estable       |

## Figuras

- `salidas/figuras/01_series_niveles.png`
- `salidas/figuras/02_fed_vs_bccr.png`
- `salidas/figuras/03_indexado_base100.png`
- `salidas/figuras/04_balance_comercial.png`
- `salidas/figuras/05_variacion_interanual.png`
- `salidas/figuras/06_correlaciones.png`
- `salidas/figuras/07_correlacion_cruzada.png`
- `salidas/figuras/08_cuenta_financiera.png`
- `salidas/figuras/08_niveles_vs_diferencias_comercial.png`
- `salidas/figuras/10_johansen_comercial.png`
- `salidas/figuras/09_residuo_largo_plazo_comercial.png`
- `salidas/figuras/11_impulso_respuesta_comercial.png`
- `salidas/figuras/12_descomposicion_varianza_comercial.png`
- `salidas/figuras/13_canal_real_vs_financiero_comercial.png`
- `salidas/figuras/08_niveles_vs_diferencias_financiero.png`
- `salidas/figuras/10_johansen_financiero.png`
- `salidas/figuras/09_residuo_largo_plazo_financiero.png`
- `salidas/figuras/11_impulso_respuesta_financiero.png`
- `salidas/figuras/12_descomposicion_varianza_financiero.png`
- `salidas/figuras/13_canal_real_vs_financiero_financiero.png`
- `salidas/figuras/08_niveles_vs_diferencias_balanza_pagos.png`
- `salidas/figuras/10_johansen_balanza_pagos.png`
- `salidas/figuras/09_residuo_largo_plazo_balanza_pagos.png`
- `salidas/figuras/11_impulso_respuesta_balanza_pagos.png`
- `salidas/figuras/12_descomposicion_varianza_balanza_pagos.png`
- `salidas/figuras/13_canal_real_vs_financiero_balanza_pagos.png`

## Tablas

- `salidas/tablas/01_estadisticas_descriptivas.csv`
- `salidas/tablas/02_matriz_correlacion.csv`
- `salidas/tablas/03_raices_unitarias_balanza_pagos.csv`
- `salidas/tablas/03_raices_unitarias_comercial.csv`
- `salidas/tablas/03_raices_unitarias_financiero.csv`
- `salidas/tablas/04_engle_granger_balanza_pagos.csv`
- `salidas/tablas/04_engle_granger_comercial.csv`
- `salidas/tablas/04_engle_granger_financiero.csv`
- `salidas/tablas/05_johansen_balanza_pagos.csv`
- `salidas/tablas/05_johansen_comercial.csv`
- `salidas/tablas/05_johansen_financiero.csv`
- `salidas/tablas/06_seleccion_rezagos_balanza_pagos.csv`
- `salidas/tablas/06_seleccion_rezagos_comercial.csv`
- `salidas/tablas/06_seleccion_rezagos_financiero.csv`
- `salidas/tablas/07_vecm_largo_plazo_balanza_pagos.csv`
- `salidas/tablas/07_vecm_largo_plazo_financiero.csv`
- `salidas/tablas/08_diagnosticos_balanza_pagos.csv`
- `salidas/tablas/08_diagnosticos_comercial.csv`
- `salidas/tablas/08_diagnosticos_financiero.csv`
- `salidas/tablas/09_granger_balanza_pagos.csv`
- `salidas/tablas/09_granger_comercial.csv`
- `salidas/tablas/09_granger_financiero.csv`
- `salidas/tablas/10_impulso_respuesta_balanza_pagos.csv`
- `salidas/tablas/10_impulso_respuesta_comercial.csv`
- `salidas/tablas/10_impulso_respuesta_financiero.csv`
- `salidas/tablas/11_descomposicion_varianza_balanza_pagos.csv`
- `salidas/tablas/11_descomposicion_varianza_comercial.csv`
- `salidas/tablas/11_descomposicion_varianza_financiero.csv`
- `salidas/tablas/12_canal_real_vs_financiero_balanza_pagos.csv`
- `salidas/tablas/12_canal_real_vs_financiero_comercial.csv`
- `salidas/tablas/12_canal_real_vs_financiero_financiero.csv`

## Limitaciones que hay que declarar

- **La produccion industrial de EE.UU. es una aproximacion mensual del ciclo real.** El PIB solo existe trimestral y 44 trimestres no alcanzan para un VAR. Es una decision de frecuencia, no una equivalencia.
- **El balance comercial no es lo mismo que las exportaciones.** El BCCR publica el saldo acumulado; aqui se desacumulo para obtener el flujo mensual. Un choque externo puede mover importaciones y exportaciones a la vez, y el saldo neto esconde parte de ese movimiento.
- **El ITCER es multilateral.** Mide la competitividad frente a una canasta de socios, no solo frente a EE.UU., asi que mezcla el efecto del dolar con el de las demas monedas. Un tipo de cambio real bilateral con EE.UU. aislaria mejor el canal estadounidense.
- **Identificacion de Cholesky con EE.UU. ordenado primero.** Supone que Costa Rica no afecta contemporaneamente a Estados Unidos. Es razonable para una economia de este tamano, pero sigue siendo un supuesto: conviene reportar la robustez invirtiendo el orden de las variables ticas.
- **2020 se controla con una dummy exogena.** Sin ese control el choque COVID domina la estimacion y las respuestas al impulso se vuelven irreconocibles.
