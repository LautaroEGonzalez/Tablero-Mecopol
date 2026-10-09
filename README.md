# Tablero de precios · MECOPOL

Tablero de inflación de la **Mesa de Economía Política (UNLa)**, con datos oficiales del INDEC que se actualizan solos.

Versión enfocada en el gobierno de Milei:

- Inflación mensual, interanual y acumulada desde diciembre de 2023
- Precios relativos y variación por rubro
- Inflación por región, con mapa y la variación de cada rubro en cada región
- IPC recalculado con la canasta de la ENGHo 2017/18 (estimación propia)

Y una segunda página, **Mirada larga** (`docs/historia.html`, borrador), con la inflación por gobierno desde 2003: Kirchner, CFK I y II, Macri, Alberto Fernández y Milei.

Y una tercera, **Universidades y Ley 27.795** (`docs/universidades.html`, borrador): qué dice la ley y el decreto 759/2025, contador de días, financiamiento real del programa 26 por gobierno (Presupuesto Abierto e IPC del INDEC) y cronología. Por ahora, solo fuentes oficiales.

## Ramas

| Rama | Qué tiene |
|---|---|
| `main` | Esta versión, solo Milei. Es la que publica GitHub Pages |
| `comparativo` | La versión anterior: gobierno vs. gobierno (Fernández, Milei y Macri con empalme) |

Para ver la versión comparativa: `git switch comparativo`. Para traer un archivo de esa rama a `main`: `git checkout comparativo -- <ruta>`.

## Cómo funciona

```
API de datos.gob.ar ──► scripts/actualizar.py ──► docs/data/dashboard.json ──► docs/index.html
                         (GitHub Action, todos los días)                       (GitHub Pages)
```

| Archivo | Qué es |
|---|---|
| `scripts/actualizar.py` | Baja las series del IPC, calcula todo y escribe el JSON |
| `scripts/historia.py` | Arma la serie larga 2002–hoy y escribe `docs/data/historia.json` |
| `scripts/universidades.py` | Arma `docs/data/universidades.json` con los hechos de `fuentes/universidades_fuentes.csv` y la serie de Presupuesto Abierto deflactada con el IPC |
| `fuentes/` | Series que no están en la API: IPCNu 2014–2015, nov-2015 a dic-2016, el IPC oficial anual 2007–2015 con sus links y el IPC Provincias de CIFRA-CTA (estimación alternativa) |
| `config.json` | Lo que se edita a mano: fechas del mandato e ids de rubros |
| `docs/index.html` | El tablero. Lee el JSON y dibuja los gráficos |
| `docs/data/dashboard.json` | Los datos procesados. Lo escribe la Action, no se toca a mano |
| `.github/workflows/actualizar.yml` | La tarea programada que corre el script y guarda los datos |

Si la API falla o falta una serie, el script corta con error y **no pisa los datos anteriores**: el tablero sigue mostrando la última versión buena y GitHub manda un mail al dueño del repositorio.

## Puesta en marcha (una sola vez)

1. **Crear el repositorio** en GitHub (público, para que Pages sea gratis) y subir estos archivos.
2. **Activar Pages:** *Settings → Pages → Source: Deploy from a branch → Branch: `main` / carpeta `/docs`* → *Save*.
3. **Primera actualización:** *Actions → Actualizar datos → Run workflow*. Tarda uno o dos minutos.
4. **Ver el tablero** en `https://<usuario>.github.io/<repositorio>/`.

Hasta que corra la primera actualización, el tablero muestra datos de prueba con un aviso arriba.

## Tareas de mantenimiento

| Cuándo | Qué hacer |
|---|---|
| Si la Action falla con "Faltan rubros" | Buscar el id de la serie en datos.gob.ar y cargarlo en `ids_divisiones` |

Todo se puede editar desde la web de GitHub, con el lápiz de cada archivo. Al guardar, la Action corre sola.

## Correrlo en una computadora

```bash
pip install -r requirements.txt
python scripts/actualizar.py
cd docs && python -m http.server 8000   # abrir http://localhost:8000
```

## Insertarlo en otra página

En Wix o Google Sites se puede incrustar con un iframe apuntando a la URL de Pages:

```html
<iframe src="https://<usuario>.github.io/<repositorio>/" width="100%" height="1800" style="border:0"></iframe>
```

## Fuentes y metodología

- IPC Nacional, INDEC, base diciembre 2016 = 100, vía la [API de Series de Tiempo](https://datos.gob.ar/series).
- Base: noviembre de 2023, último mes completo antes de la asunción del 10 de diciembre.
- Mirada larga: serie oficial del INDEC (IPC GBA hasta 2013, IPCNu 2014–oct 2015, IPC GBA may–dic 2016, IPC Nacional desde 2017; de nov-2015 a abr-2016, sin IPC del INDEC, el IPC de la Ciudad de Buenos Aires). Para comparar, la estimación alternativa del IPC Provincias de [CIFRA-CTA](https://centrocifra.org.ar/estadisticas/ipc-provincias/) entre 2007 y 2016. Detalle en `fuentes/LEEME.md`.
