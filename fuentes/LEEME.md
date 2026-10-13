# Fuentes que no están en la API

| Archivo | Qué es | De dónde sale |
|---|---|---|
| `IPC-Provincias-2007-2018_CIFRA.xlsx` | Planilla original del IPC Provincias, mensual, ene-2007 a dic-2018, base enero 2014 = 100 | [CIFRA-CTA](https://centrocifra.org.ar/estadisticas/ipc-provincias/) |
| `ipc_provincias_cifra.csv` | La misma serie en CSV (`fecha,indice`), que es lo que lee `scripts/historia.py` | Convertida de la planilla, sin cambios en los valores |
| `ponderaciones_ipc.csv` | Peso de cada rubro en el IPC vigente (ENGHo 2004/05, a precios de dic-2016) y en la ENGHo 2017/18, total país. El peso nacional vigente se calcula promediando las seis regiones del cuadro 17 con el peso de cada región del cuadro 18 | [IPC dic-2025, cuadros 17 y 18](https://www.indec.gob.ar/uploads/informesdeprensa/ipc_01_266741F036E8.pdf) y [ENGHo 2017-2018, cuadro 1](https://www.indec.gob.ar/ftp/cuadros/sociedad/engho_2017_2018_informe_gastos.pdf) |
| `ponderaciones_regionales.csv` | Peso de cada rubro en la canasta de cada región del IPC y peso de cada región en el total nacional (fila `_peso_region`) | [IPC dic-2025, cuadros 17 y 18](https://www.indec.gob.ar/uploads/informesdeprensa/ipc_01_266741F036E8.pdf) |
| `estimaciones_reponderadas.csv` | Lo que publicaron otros (Di Tella, CEPA, consultoras, el Gobierno) con las ponderaciones 2017/18, para comparar con la estimación propia | Link en la columna `link` |
| `indec_ipcnu_2014_2015.csv` | Variación mensual del IPC Nacional urbano (IPCNu) del INDEC, ene-2014 a oct-2015. Sale de los índices de cada informe de prensa; donde solo se tiene la variación publicada (redondeada a un decimal), se usa esa. Encadenada da 23,8% en 2014 (publicado: 23,9%) y 11,9% en ene-oct 2015 | Informes de prensa IPCNu del INDEC, link en la columna `fuente` |
| `ipc_2015_2016_sin_indice_nacional.csv` | Variación mensual de nov-2015 a dic-2016: IPC de la Ciudad de Buenos Aires (nov-2015 a abr-2016, calculada con los índices del cuadro 5 de los informes de la Dirección de Estadística porteña) e IPC GBA del INDEC (may a dic-2016, la publicada en cada informe) | Link en la columna `fuente` |
| `universidades_fuentes.csv` | Hechos de la página "Universidades y Ley 27.795". Columnas `seccion, clave, fecha, valor, valor_max, tipo, texto, fuente, link`. Secciones: `hito` (fechas de los contadores), `situacion` (dónde estamos hoy), `crono` (`clave` = carril `ley`/`cautelar`/`fondo`, `tipo` = actor, `valor` = `apelacion` si es un recurso del Estado; sin `fecha` si no está confirmada), `articulo` (cumplimiento por artículo; `fecha` = desde cuándo es exigible, `tipo` = `cautelar` o `sentencia`), `ley` (texto de los arts. 5 y 9), `gobierno` (decreto 759) y `juez` (sentencia de fondo) | Link en la columna `link`. Normas, Congreso y Ministerio: oficiales. Fallos: prensa jurídica cuando no están en un sitio oficial |
| `salario_nodocente.csv` | Básico nodocente de la categoría 3, mes a mes desde dic-2023. Columnas `mes, basico, variacion, fuente, link`: va el básico del instructivo oficial de liquidación o, si no está, el % de aumento del mes. Meses consecutivos; si una fila trae las dos cosas se controla que cierren | Instructivos de liquidación (UNCuyo, UNGS), datos abiertos UNC, UTN BA |
| `ipc_publicado.csv` | IPC nacional (mensual, interanual y acumulado del año) tal como lo publica el INDEC en su informe. Se carga a mano el día de la publicación: si la API de datos.gob.ar todavía no tiene ese mes, la portada lo muestra igual y marca rubros, regiones y canasta "a la espera de la carga del dato en la API del INDEC". Cuando la API lo carga, el cálculo completo lo reemplaza solo | Informe del INDEC, link en la columna `link` |
| `indec_oficial_2007_2015.csv` | Inflación anual que publicó el INDEC entre 2007 y 2015, con el link a la nota de cada año | Diarios de la época, ver columna `fuente` |

## Cómo se arma la serie larga (Mirada larga)

La serie principal es la **oficial**. Se encadenan variaciones mensuales:

| Período | Serie | De dónde sale |
|---|---|---|
| 2002 a dic-2006 | INDEC, IPC GBA histórico | API, `178.1_NL_GENERAL_0_0_13` |
| ene-2007 a dic-2013 | INDEC, IPC GBA base abril 2008 | API, `96.3_ING_2008_M_19` |
| ene-2014 a oct-2015 | INDEC, IPC Nacional urbano (IPCNu) | `indec_ipcnu_2014_2015.csv` |
| nov-2015 a abr-2016 | IPC de la Ciudad de Buenos Aires (IPCBA). En esos meses el INDEC no publicó índice de precios (emergencia del sistema estadístico, decreto 55/2016) y mencionó como referencias los índices de la Ciudad y de San Luis | `ipc_2015_2016_sin_indice_nacional.csv` |
| may-2016 a dic-2016 | INDEC, IPC GBA base abril 2016 | mismo archivo, un informe de prensa por mes |
| desde ene-2017 | INDEC, IPC Nacional | API |

Control: año por año, de 2007 a 2014, la serie tiene que dar lo que publicó el INDEC (`indec_oficial_2007_2015.csv`, tolerancia 0,35 puntos). Si no da, `scripts/historia.py` corta con error.

## Estimación alternativa: CIFRA-CTA

Entre 2007 y 2016 hubo mediciones distintas de la oficial (institutos provinciales, consultoras, centros de estudio) que dieron valores más altos. Para comparar, la página muestra el IPC Provincias de CIFRA, centro de estudios de la CTA, que promedia índices de diez provincias con ponderaciones de la ENGHo ([nota metodológica](https://centrocifra.org.ar/wp-content/uploads/2023/08/Nota-metodologica-IPC-Provincias.pdf)). Aparece siempre como alternativa: rayada en las barras anuales, línea naranja en el interanual y columna aparte en los cuadros. La serie alternativa es igual a la oficial salvo de feb-2007 a dic-2016.

Control: la variación promedio de 2018 da 34,1%, igual a la que informa la nota metodológica.

## IPC con la canasta 2017/18 (estimación MECOPOL)

`scripts/actualizar.py` calcula cuánto cuesta en cada mes la canasta de la ENGHo 2017/18 (12 rubros, total país), valuada con los índices de cada división del IPC y con los precios promedio del período de la encuesta (nov-2017 a nov-2018). Como agregar por divisiones nacionales no reproduce exacto el nivel general, al índice oficial se le aplica solo el efecto del cambio de ponderaciones. El log de la Action muestra el control: con las ponderaciones vigentes, la cuenta tiene que dar casi igual que el oficial.

## Mapa de regiones

`docs/geo/regiones_ipc.json` dibuja las seis regiones del IPC uniendo los departamentos del IGN (SIG 250, vía [github.com/mgaitan/departamentos_argentina](https://github.com/mgaitan/departamentos_argentina)). GBA es la Ciudad de Buenos Aires más los 24 partidos del conurbano; el resto de la provincia de Buenos Aires va en Pampeana. Incluye las Islas Malvinas dentro de Patagonia; el sector antártico no se dibuja en este mapa. Se regenera con `scripts/mapa_regiones.py` (no lo corre la Action).

## Universidades y Ley 27.795

`scripts/universidades.py` arma `docs/data/universidades.json`:

- **Hechos:** situación actual, cronología en tres carriles (la ley, la cautelar por los arts. 5 y 6, el amparo de fondo), fechas de los contadores de días y cumplimiento por artículo salen de `universidades_fuentes.csv`, cada uno con su link. Para cargar un fallo o una apelación nueva se agrega una fila `crono` (y una `hito` si tiene que tener contador) y se actualiza `situacion`.
- **Salario nodocente:** índice real del básico con noviembre 2023 = 100 (el art. 5 manda actualizar por IPC desde el 1/12/2023), con el IPC mensual de `dashboard.json` (INDEC). Cuando sale un aumento nuevo se agrega una fila al final de `salario_nodocente.csv`; el mes entra al gráfico cuando el INDEC publica su IPC. Excluye sumas no remunerativas y la garantía salarial de las categorías bajas.
- **Financiamiento (oculto por ahora en la página):** el script sigue bajando de Presupuesto Abierto el crédito anual de cada año (`dgsiaf-repo.mecon.gob.ar/repository/pa/datasets/<año>/credito-anual-<año>.zip`), suma el devengado del programa 26 "Desarrollo de la Educación Superior" (el que nombra el art. 2 de la ley) y lo deflacta con el IPC promedio anual de `historia.json` (INDEC), con 2023 = 100. Los años cerrados quedan guardados en el JSON. También guarda el detalle de la UNAJ (columna `subparcial_desc`).
