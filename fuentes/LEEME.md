# Fuentes que no están en la API

| Archivo | Qué es | De dónde sale |
|---|---|---|
| `IPC-Provincias-2007-2018_CIFRA.xlsx` | Planilla original del IPC Provincias, mensual, ene-2007 a dic-2018, base enero 2014 = 100 | [CIFRA-CTA](https://centrocifra.org.ar/estadisticas/ipc-provincias/) |
| `ipc_provincias_cifra.csv` | La misma serie en CSV (`fecha,indice`), que es lo que lee `scripts/historia.py` | Convertida de la planilla, sin cambios en los valores |
| `indec_oficial_2007_2015.csv` | Inflación anual que publicó el INDEC entre 2007 y 2015, con el link a la nota de cada año | Diarios de la época, ver columna `fuente` |

## Por qué CIFRA-CTA entre 2007 y 2016

Entre 2007 y 2015 el INDEC estuvo intervenido y su IPC quedó muy por debajo de los índices provinciales. En 2016 no hubo índice nacional. El IPC Provincias de CIFRA (centro de estudios de la CTA) promedia los índices de diez provincias con ponderaciones de la ENGHo. Metodología: [nota de CIFRA](https://centrocifra.org.ar/wp-content/uploads/2023/08/Nota-metodologica-IPC-Provincias.pdf).

Control: la variación promedio de 2018 da 34,1%, igual a la que informa la nota metodológica.

## Cómo se arma la serie larga

Se encadenan variaciones mensuales: INDEC IPC GBA hasta enero de 2007 (la serie de CIFRA empieza ese mes), CIFRA de febrero de 2007 a diciembre de 2016 e INDEC IPC Nacional desde enero de 2017.
