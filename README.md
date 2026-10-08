# Tablero de precios · MECOPOL

Tablero de inflación de la **Mesa de Economía Política (UNLa)**, con datos oficiales del INDEC que se actualizan solos.

- Inflación mensual, interanual y acumulada
- Gobierno vs. gobierno a la misma altura del mandato
- Precios relativos por rubro
- Escenarios hasta el fin del mandato

## Cómo funciona

```
API de datos.gob.ar ──► scripts/actualizar.py ──► docs/data/dashboard.json ──► docs/index.html
                         (GitHub Action, todos los días)                       (GitHub Pages)
```

| Archivo | Qué es |
|---|---|
| `scripts/actualizar.py` | Baja las series del IPC, calcula todo y escribe el JSON |
| `config.json` | Lo que se edita a mano: colores, REM, empalme de Macri |
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
| Cada vez que sale el REM del BCRA (principios de mes) | Actualizar `rem` en `config.json` |
| Si la Action falla con "Faltan rubros" | Buscar el id de la serie en datos.gob.ar y cargarlo en `ids_divisiones` |
| Para sumar a Macri | Cargar las 13 variaciones mensuales del IPC CABA (dic-2015 a dic-2016) en `empalme_macri` |

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
- Mes base de cada gobierno: noviembre del año de asunción (último mes completo del gobierno anterior).
- Los escenarios son supuestos explícitos, no pronósticos.
