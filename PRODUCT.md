# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Equipo de la Mesa de Economía Política (MECOPOL) de la Universidad Nacional de Lanús y su comunidad universitaria. Lo consultan como herramienta propia y lo difunden desde ahí. Otros públicos pueden llegar por un link compartido, pero no son el destinatario principal.

## Product Purpose

Mostrar la inflación durante el gobierno de Milei con datos del INDEC que se actualizan solos. El éxito es que quien abre la página vea en segundos cuánto dio la inflación del último mes y cómo viene respecto del mes anterior; el resto (serie, regiones, rubros, canasta) se consulta a continuación.

## Positioning

Es la lectura propia de MECOPOL sobre los datos oficiales: suma precios relativos por rubro y un IPC recalculado con la canasta de la ENGHo 2017/18, identificado siempre como estimación de MECOPOL y no como dato oficial.

## Operating Context

Página única publicada en GitHub Pages desde `docs/`. Una GitHub Action revisa las fuentes todos los días y reescribe `docs/data/dashboard.json`. El INDEC publica a mediados de cada mes; entre la publicación y la carga en la API puede haber un estado parcial, con avisos en la página. El README documenta la inserción por iframe en Wix o Google Sites.

## Capabilities and Constraints

- HTML, CSS y JavaScript sin framework ni paso de build; gráficos con ECharts desde CDN.
- Se edita a mano y también desde la web de GitHub, así que debe seguir siendo simple de mantener.
- Secciones: cifras del mes, serie mes a mes, regiones (mapa, tabla, mapa de calor), rubros y precios relativos, canasta 2017/18, comparación con otras estimaciones, notas de fuente y método.
- Estados que deben seguir funcionando: datos de prueba, dato parcial, error de carga.
- Términos: rubro, división, nivel general, interanual, acumulada, "desde nov-23", canasta 2017/18.

## Brand Commitments

- El logo de MECOPOL (`docs/img/logo-mecopol.png`) y su bordó y rosa son la identidad y se mantienen.
- Español rioplatense, directo y sin jerga innecesaria.

## Evidence on Hand

Datos reales del INDEC en `docs/data/dashboard.json` y geometría de regiones en `docs/geo/regiones_ipc.json`. No se inventan cifras, fuentes ni comparaciones.

## Product Principles

1. La cifra del mes se ve primero, sin buscarla.
2. Lo oficial y lo estimado por MECOPOL nunca se confunden.
3. Cada dato muestra su período y su fuente.
4. Actualizarse solo no puede romper la página, ni siquiera con datos parciales.
