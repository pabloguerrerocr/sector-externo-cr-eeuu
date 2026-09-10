# Efecto del ciclo económico y la política monetaria de EE.UU. sobre el sector externo de Costa Rica, 2015–2025

Investigación con **datos reales y públicos** sobre cómo se transmiten a Costa Rica
los dos canales por los que Estados Unidos afecta a una economía pequeña y abierta:
el **canal real** (su ciclo económico mueve la demanda de exportaciones) y el
**canal financiero** (la tasa de la Fed mueve los flujos de capital).

El pipeline corre de punta a punta: descarga los datos, prueba raíces unitarias,
prueba cointegración, estima el modelo, produce 19 figuras a 300 dpi y escribe un
reporte en markdown.

## Resultado principal

**El canal financiero domina al canal real en casi toda la línea.** A 24 meses,
la tasa de fondos federales explica:

| Variable de Costa Rica | Canal real | Canal financiero |
|---|---:|---:|
| Reservas internacionales | 3 % | **44 %** |
| Tasa de política monetaria del BCCR | 1 % | **44 %** |
| Tipo de cambio | 14 % | **40 %** |
| Balance comercial | 3 % | 7 % |

Los detalles, con sus pruebas de diagnóstico y limitaciones, están en
[`salidas/reporte.md`](salidas/reporte.md).

## Correr

```bash
pip install -r requirements.txt
python main.py                      # los dos bloques
python main.py --bloque financiero  # solo uno
```

| Ruta | Qué es |
|---|---|
| `salidas/reporte.md` | resultados narrados, con las tablas de cada prueba |
| `salidas/figuras/*.png` | 19 figuras a 300 dpi |
| `salidas/tablas/*.csv` | cada prueba estadística en su propio CSV |
| `data/procesado/` | el panel armado y el registro de origen de cada serie |

## Los datos

**Estados Unidos — FRED**, público y sin llave. Se cachea en `data/raw/cache/`
porque FRED limita la frecuencia de peticiones y el análisis tiene que poder
correr sin red.

| Serie | Código |
|---|---|
| Producción industrial (ciclo real, mensual) | `INDPRO` |
| Tasa de fondos federales | `FEDFUNDS` |
| PIB real trimestral | `GDPC1` |
| Bono del Tesoro a 2 años | `DGS2` |
| Índice amplio del dólar | `DTWEXBGS` |

**Costa Rica — BCCR**, descargados a mano del portal de indicadores económicos
(https://sdd.bccr.fi.cr/es/IndicadoresEconomicos/Inicio/) y puestos en `data/raw/`:

| Archivo | Cuadro del BCCR | Tratamiento |
|---|---|---|
| `tipo_cambio.xlsx` | Contenedor/6?Cuadro=1 | diario → promedio mensual, columna de venta |
| `balance_comercial.xlsx` | Contenedor/452?Cuadro=112 | **desacumulado**: el BCCR lo publica acumulado en el año |
| `reservas.xlsx` | Contenedor/516?Cuadro=70 | saldo de fin de mes |
| `tpm.xlsx` | Contenedor/358?Cuadro=223 | diario → promedio mensual |

`src/bccr_excel.py` lee el formato exacto que exporta ese portal (encabezado en la
fila 5) y resuelve la desacumulación. La verificación está en el código: la suma de
los flujos mensuales de un año reproduce el acumulado de diciembre con diferencia 0.

Para actualizar, se vuelven a bajar los cuatro Excel y se corre `main.py`. El portal
carga los cuadros por JavaScript y tiene protección antibot, así que no hay forma
razonable de automatizar la descarga sin el token del servicio web del BCCR.

## Los dos bloques y por qué

Cuatro variables con 132 observaciones mensuales es una relación sana entre
parámetros y datos. Meter las seis en un solo VAR no lo sería. Los dos bloques
comparten las variables de EE.UU. y cambian las de Costa Rica:

- **Bloque comercial** — `ipi_eeuu`, `ffr`, `balcom`, `tc_venta`
  Cómo llegan los dos canales al balance comercial y al tipo de cambio.
- **Bloque financiero** — `ipi_eeuu`, `ffr`, `reservas`, `tpm`
  La transmisión hacia las reservas y la respuesta de política del BCCR.

## Decisiones metodológicas que hay que poder defender

- **Identificación de Cholesky con EE.UU. ordenado primero.** Costa Rica es una
  economía pequeña y abierta: no se le supone efecto contemporáneo sobre EE.UU. Es
  razonable, pero es un supuesto. Conviene reportar la robustez invirtiendo el orden
  de las dos variables ticas.
- **Dummy exógena para el COVID** (marzo–agosto 2020). Sin ese control, 2020 domina
  la estimación y las respuestas al impulso se vuelven irreconocibles.
- **Rezagos por HQIC.** AIC sobreparametriza con muestras cortas y BIC se queda
  corto. El CSV `06_seleccion_rezagos_*` trae los tres criterios.
- **ADF y KPSS juntos.** Tienen hipótesis nulas opuestas. Cuando se contradicen, la
  fila queda marcada como `ambiguo` en vez de forzar una conclusión.
- **Producción industrial como medida mensual del ciclo real.** El PIB solo existe
  trimestral y 44 trimestres no alcanzan para un VAR. Es una decisión de frecuencia,
  no una equivalencia.

## Limitaciones

- **El balance comercial no es lo mismo que las exportaciones.** Un choque externo
  puede mover importaciones y exportaciones a la vez, y el saldo neto esconde parte
  de ese movimiento. Bajar la serie de exportaciones por separado es la mejora más
  directa.
- **Falta el ITCER** (tipo de cambio efectivo real multilateral), que es la medida
  correcta de competitividad. Aquí se usó el tipo de cambio nominal de venta.
- **Los residuos no son normales y hay autocorrelación remanente** en los dos
  bloques. Está reportado en `08_diagnosticos_*.csv`. Es habitual en series
  macroeconómicas con el choque de 2020 adentro, pero obliga a leer los intervalos
  de confianza con cautela.
- **Las reservas suben tras un alza de la Fed**, que es lo contrario de la historia
  clásica de fuga de capitales. Casi seguro refleja el episodio 2022–2024, cuando
  Costa Rica acumuló reservas de forma agresiva mientras la Fed subía. Es una
  correlación de ese período, no una ley general, y así hay que presentarla.

## Estructura

```
config.py              periodo, series, bloques de modelación, paleta
main.py                orquestador
src/fuentes.py         descarga y caché de FRED
src/bccr_excel.py      lector de los Excel del BCCR y desacumulación
src/dataset.py         armado del panel mensual
src/graficos.py        estilo único de todas las figuras
src/descriptivo.py     estadísticas y figuras descriptivas
src/estacionariedad.py ADF y KPSS
src/cointegracion.py   Engle-Granger y Johansen
src/modelo.py          VAR/VECM, Granger, IRF, descomposición de varianza
src/reporte.py         arma salidas/reporte.md
```
