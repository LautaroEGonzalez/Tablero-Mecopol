# Fuentes que no están en la API

| Archivo | Qué es | De dónde sale |
|---|---|---|
| `IPC-Provincias-2007-2018_CIFRA.xlsx` | Planilla original del IPC Provincias, mensual, ene-2007 a dic-2018, base enero 2014 = 100 | [CIFRA-CTA](https://centrocifra.org.ar/estadisticas/ipc-provincias/) |
| `ipc_provincias_cifra.csv` | La misma serie en CSV (`fecha,indice`), que es lo que lee `scripts/historia.py` | Convertida de la planilla, sin cambios en los valores |
| `ponderaciones_ipc.csv` | Peso de cada rubro en el IPC vigente (ENGHo 2004/05, a precios de dic-2016) y en la ENGHo 2017/18, total país. El peso nacional vigente se calcula promediando las seis regiones del cuadro 17 con el peso de cada región del cuadro 18 | [IPC dic-2025, cuadros 17 y 18](https://www.indec.gob.ar/uploads/informesdeprensa/ipc_01_266741F036E8.pdf) y [ENGHo 2017-2018, cuadro 1](https://www.indec.gob.ar/ftp/cuadros/sociedad/engho_2017_2018_informe_gastos.pdf) |
| `ponderaciones_regionales.csv` | Peso de cada rubro en la canasta de cada región del IPC y peso de cada región en el total nacional (fila `_peso_region`) | [IPC dic-2025, cuadros 17 y 18](https://www.indec.gob.ar/uploads/informesdeprensa/ipc_01_266741F036E8.pdf) |
| `estimaciones_reponderadas.csv` | Lo que publicaron otros (Di Tella, CEPA, consultoras, el Gobierno) con las ponderaciones 2017/18, para comparar con la estimación propia | Link en la columna `link` |
| `indec_ipcnu_2014_2015.csv` | Variación mensual del IPC Nacional urbano (IPCNu) del INDEC, ene-2014 a oct-2015. Sale de los índices de cada informe de prensa; donde solo se tiene la variación publicada (redondeada a un decimal), se usa esa. Encadenada da 23,8% en 2014 (publicado: 23,9%) y 11,9% en ene-oct 2015 | Informes de prensa IPCNu del INDEC, link en la columna `fuente` |
| `indec_oficial_2007_2015.csv` | Inflación anual que publicó el INDEC entre 2007 y 2015, con el link a la nota de cada año | Diarios de la época, ver columna `fuente` |

## Por qué CIFRA-CTA entre 2007 y 2016

En 2007 cambiaron la conducción y la metodología del IPC del INDEC, y hasta 2015 el índice oficial quedó muy por debajo de los provinciales. En 2016 no hubo índice nacional. El IPC Provincias de CIFRA (centro de estudios de la CTA) promedia los índices de diez provincias con ponderaciones de la ENGHo. Metodología: [nota de CIFRA](https://centrocifra.org.ar/wp-content/uploads/2023/08/Nota-metodologica-IPC-Provincias.pdf).

Control: la variación promedio de 2018 da 34,1%, igual a la que informa la nota metodológica.

## Cómo se arma la serie larga

Se encadenan variaciones mensuales: INDEC IPC GBA hasta enero de 2007 (la serie de CIFRA empieza ese mes), CIFRA de febrero de 2007 a diciembre de 2016 e INDEC IPC Nacional desde enero de 2017.

## Las dos líneas del gráfico interanual

En "Mirada larga" el interanual mes a mes se dibuja con dos líneas en todo el período, sin elegir una: la del INDEC (IPC GBA histórico hasta 2006, IPC GBA base abril 2008 `96.3_ING_2008_M_19` de 2007 a 2013, IPCNu de 2014 a octubre de 2015 e IPC Nacional desde diciembre de 2017) y la de CIFRA-CTA (2008 a 2018). Entre noviembre de 2015 y noviembre de 2017 no hay interanual oficial nacional. `scripts/historia.py` controla que la serie oficial mensual dé, año por año, lo que publicó el INDEC (tolerancia 0,35 puntos).

## IPC con la canasta 2017/18 (estimación MECOPOL)

`scripts/actualizar.py` calcula cuánto cuesta en cada mes la canasta de la ENGHo 2017/18 (12 rubros, total país), valuada con los índices de cada división del IPC y con los precios promedio del período de la encuesta (nov-2017 a nov-2018). Como agregar por divisiones nacionales no reproduce exacto el nivel general, al índice oficial se le aplica solo el efecto del cambio de ponderaciones. El log de la Action muestra el control: con las ponderaciones vigentes, la cuenta tiene que dar casi igual que el oficial.

## Mapa de regiones

`docs/geo/regiones_ipc.json` dibuja las seis regiones del IPC uniendo los departamentos del IGN (SIG 250, vía [github.com/mgaitan/departamentos_argentina](https://github.com/mgaitan/departamentos_argentina)). GBA es la Ciudad de Buenos Aires más los 24 partidos del conurbano; el resto de la provincia de Buenos Aires va en Pampeana. Incluye las Islas Malvinas dentro de Patagonia; el sector antártico no se dibuja en este mapa. Se regenera con `scripts/mapa_regiones.py` (no lo corre la Action).
