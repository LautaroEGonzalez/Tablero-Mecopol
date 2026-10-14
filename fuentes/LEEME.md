# Fuentes que no están en la API

| Archivo | Qué es | De dónde sale |
|---|---|---|
| `ponderaciones_ipc.csv` | Peso de cada rubro en el IPC vigente (ENGHo 2004/05, a precios de dic-2016) y en la ENGHo 2017/18, total país. El peso nacional vigente se calcula promediando las seis regiones del cuadro 17 con el peso de cada región del cuadro 18 | [IPC dic-2025, cuadros 17 y 18](https://www.indec.gob.ar/uploads/informesdeprensa/ipc_01_266741F036E8.pdf) y [ENGHo 2017-2018, cuadro 1](https://www.indec.gob.ar/ftp/cuadros/sociedad/engho_2017_2018_informe_gastos.pdf) |
| `ponderaciones_regionales.csv` | Peso de cada rubro en la canasta de cada región del IPC y peso de cada región en el total nacional (fila `_peso_region`) | [IPC dic-2025, cuadros 17 y 18](https://www.indec.gob.ar/uploads/informesdeprensa/ipc_01_266741F036E8.pdf) |
| `estimaciones_reponderadas.csv` | Lo que publicaron otros (Di Tella, CEPA, consultoras, el Gobierno) con las ponderaciones 2017/18, para comparar con la estimación propia | Link en la columna `link` |
| `ipc_publicado.csv` | IPC nacional (mensual, interanual y acumulado del año) tal como lo publica el INDEC en su informe. Se carga a mano el día de la publicación: si la API de datos.gob.ar todavía no tiene ese mes, la portada lo muestra igual y marca rubros, regiones y canasta "a la espera de la carga del dato en la API del INDEC". Cuando la API lo carga, el cálculo completo lo reemplaza solo | Informe del INDEC, link en la columna `link` |

## IPC con la canasta 2017/18 (estimación MECOPOL)

`scripts/actualizar.py` calcula cuánto cuesta en cada mes la canasta de la ENGHo 2017/18 (12 rubros, total país), valuada con los índices de cada división del IPC y con los precios promedio del período de la encuesta (nov-2017 a nov-2018). Como agregar por divisiones nacionales no reproduce exacto el nivel general, al índice oficial se le aplica solo el efecto del cambio de ponderaciones. El log de la Action muestra el control: con las ponderaciones vigentes, la cuenta tiene que dar casi igual que el oficial.

## Mapa de regiones

`docs/geo/regiones_ipc.json` dibuja las seis regiones del IPC uniendo los departamentos del IGN (SIG 250, vía [github.com/mgaitan/departamentos_argentina](https://github.com/mgaitan/departamentos_argentina)). GBA es la Ciudad de Buenos Aires más los 24 partidos del conurbano; el resto de la provincia de Buenos Aires va en Pampeana. Incluye las Islas Malvinas dentro de Patagonia; el sector antártico no se dibuja en este mapa. Se regenera con `scripts/mapa_regiones.py` (no lo corre la Action).

## Mirada larga y Universidades

Se mudaron al repositorio [Análisis Económicos](https://github.com/LautaroEGonzalez/Analisis-Economicos), con sus scripts y sus fuentes.
