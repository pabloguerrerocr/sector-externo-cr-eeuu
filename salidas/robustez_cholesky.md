# Robustez al orden de Cholesky

Generado por `robustez_cholesky.py`. Mismo panel, transformaciones, dummy COVID y rezagos (HQIC) que `main.py`.

## Combinaciones donde domina el canal financiero

| especificacion                 | combinaciones   |
|:-------------------------------|:----------------|
| base (main.py)                 | 14 de 14        |
| EE.UU. invertido (Fed primero) | 11 de 14        |
| Costa Rica invertido           | 12 de 12        |
| ambos invertidos               | 9 de 12         |
| generalizada (sin orden)       | 14 de 14        |

## Canal financiero en el horizonte mas largo (% de la varianza)

|                                     |   base (main.py) |   EE.UU. invertido (Fed primero) |   Costa Rica invertido |   ambos invertidos |   generalizada (sin orden) |
|:------------------------------------|-----------------:|---------------------------------:|-----------------------:|-------------------:|---------------------------:|
| ('comercial', 'log_export_cr', 24)  |             10.4 |                              7.7 |                   10.4 |                7.7 |                        9.1 |
| ('comercial', 'log_itcer', 24)      |             43.2 |                             37.8 |                   43.2 |               37.8 |                       38.9 |
| ('financiero', 'log_reservas', 24)  |             44.4 |                             41.9 |                   44.4 |               41.9 |                       33.2 |
| ('financiero', 'tpm', 24)           |             43.9 |                             43.5 |                   43.9 |               43.5 |                       32.5 |
| ('balanza_pagos', 'cuenta_fin', 12) |             26.1 |                             23.4 |                  nan   |              nan   |                       23.6 |

## Canal real en el horizonte mas largo (% de la varianza)

|                                     |   base (main.py) |   EE.UU. invertido (Fed primero) |   Costa Rica invertido |   ambos invertidos |   generalizada (sin orden) |
|:------------------------------------|-----------------:|---------------------------------:|-----------------------:|-------------------:|---------------------------:|
| ('comercial', 'log_export_cr', 24)  |              6.2 |                              8.9 |                    6.2 |                8.9 |                        7.3 |
| ('comercial', 'log_itcer', 24)      |              4.5 |                              9.9 |                    4.5 |                9.9 |                        4.6 |
| ('financiero', 'log_reservas', 24)  |              3.3 |                              5.8 |                    3.3 |                5.8 |                        2.6 |
| ('financiero', 'tpm', 24)           |              0.6 |                              1   |                    0.6 |                1   |                        0.4 |
| ('balanza_pagos', 'cuenta_fin', 12) |              2.8 |                              5.4 |                  nan   |              nan   |                        2.8 |

La especificacion generalizada (Pesaran y Shin, 1998) no depende del orden de las variables; sus filas se normalizan a 100.
