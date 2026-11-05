---
name: Tablero de Precios MECOPOL
description: La cifra del mes impresa a sangre, como un afiche de la universidad pública.
colors:
  bordo: "#950b32"
  bordo-osc: "#6d0623"
  hist: "#bc677a"
  rosa: "#ff8bae"
  rosa-hist: "#dd7a96"
  crema: "#f7efe6"
  negro: "#1a0a10"
  placa-logo: "#ffffff"
  txt-2: "#5e4a50"
  txt-2-tinta: "#c9b7bc"
  linea: "rgba(26,10,16,.2)"
  linea-tinta: "rgba(247,239,230,.22)"
  resalta: "rgba(26,10,16,.05)"
  resalta-tinta: "rgba(247,239,230,.07)"
  grilla: "rgba(26,10,16,.12)"
  grilla-tinta: "rgba(247,239,230,.14)"
  mapa-1: "#f4c9d6"
  mapa-2: "#e77f9f"
  mapa-3: "#c02a57"
  mapa-4: "#6d0623"
  mapa-sin-dato: "#eadfd3"
  calor-1: "rgba(149,11,50,.08)"
  calor-2: "rgba(149,11,50,.24)"
  calor-3: "rgba(149,11,50,.4)"
  calor-4: "rgba(149,11,50,.56)"
typography:
  cifra-mes:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "min(calc((100cqw - 440px) * .92 / (.44 * var(--n) + .25)), 270px)"
    fontWeight: 400
    lineHeight: 1.16
  cifra:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "clamp(52px, 5.6cqw, 88px)"
    fontWeight: 400
    lineHeight: 1.16
  cifra-comparada:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "clamp(38px, 3.6vw, 50px)"
    fontWeight: 400
    lineHeight: 1.16
  headline-afiche:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "clamp(38px, 4cqw, 58px)"
    fontWeight: 400
    lineHeight: 1.06
  headline:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "clamp(38px, 4.6vw, 62px)"
    fontWeight: 400
    lineHeight: 1.08
  title:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "clamp(26px, 2.8vw, 34px)"
    fontWeight: 400
    lineHeight: 1.15
  title-pie:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "24px"
    fontWeight: 400
    lineHeight: 1.15
  banda:
    fontFamily: "Public Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "19px"
    fontWeight: 800
    lineHeight: 1.2
  body-afiche:
    fontFamily: "Public Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.4
  body:
    fontFamily: "Public Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  tabla:
    fontFamily: "Public Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    fontFeature: "tnum"
  control:
    fontFamily: "Public Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 600
  label:
    fontFamily: "Public Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 600
rounded:
  recto: "0"
spacing:
  margen: "max(clamp(16px, 3.4vw, 48px), calc((100vw - 1344px) / 2))"
  seccion: "clamp(48px, 6vw, 84px)"
  bloque: "22px"
  columna: "36px"
  filete-aire: "16px"
components:
  banda:
    backgroundColor: "{colors.bordo}"
    textColor: "{colors.crema}"
    typography: "{typography.banda}"
    rounded: "{rounded.recto}"
  afiche:
    backgroundColor: "{colors.bordo}"
    textColor: "{colors.crema}"
    typography: "{typography.cifra-mes}"
    rounded: "{rounded.recto}"
  cifra:
    backgroundColor: "{colors.crema}"
    textColor: "{colors.bordo}"
    typography: "{typography.cifra}"
    rounded: "{rounded.recto}"
    padding: "28px 20px 30px"
  cifra-estimada:
    backgroundColor: "{colors.negro}"
    textColor: "{colors.rosa}"
    typography: "{typography.cifra}"
    rounded: "{rounded.recto}"
    padding: "28px 20px 30px"
  selector:
    backgroundColor: "transparent"
    textColor: "{colors.bordo}"
    typography: "{typography.control}"
    rounded: "{rounded.recto}"
    padding: "0 16px"
    height: "44px"
  selector-elegido:
    backgroundColor: "{colors.bordo}"
    textColor: "{colors.crema}"
    typography: "{typography.control}"
    rounded: "{rounded.recto}"
    padding: "0 16px"
    height: "44px"
  selector-tinta:
    backgroundColor: "transparent"
    textColor: "{colors.rosa}"
    typography: "{typography.control}"
    rounded: "{rounded.recto}"
    padding: "0 16px"
    height: "44px"
  selector-tinta-elegido:
    backgroundColor: "{colors.rosa}"
    textColor: "{colors.negro}"
    typography: "{typography.control}"
    rounded: "{rounded.recto}"
    padding: "0 16px"
    height: "44px"
  calor-maximo:
    backgroundColor: "{colors.bordo}"
    textColor: "{colors.crema}"
    rounded: "{rounded.recto}"
    padding: "8px"
  aviso:
    backgroundColor: "{colors.crema}"
    textColor: "{colors.negro}"
    rounded: "{rounded.recto}"
    padding: "11px 14px"
  pie:
    backgroundColor: "{colors.bordo}"
    textColor: "{colors.crema}"
    rounded: "{rounded.recto}"
---

# Design System: Tablero de Precios MECOPOL

## Overview

**Creative North Star: "El afiche de la universidad pública"**

El tablero se imprime, no se ilumina. La cifra del mes ocupa el campo bordó a sangre, en crema y al tamaño de un cartel de pared; todo lo demás se ordena debajo con filetes, tintas planas y dos familias tipográficas. La jerarquía sale del tamaño, no de contenedores ni de efectos.

El mundo es serigráfico: cada color es una tinta que se ve entera, cada borde es un corte recto y cada separación es un filete. La densidad crece a medida que se baja, del cartel a las tablas, porque quien entra primero lee y después consulta. La lectura propia de MECOPOL tiene su propia tinta, un campo negro con rosa, y por eso nunca se puede tomar por un dato oficial.

Este sistema rechaza dos cosas confirmadas: la fila de cuatro tarjetas iguales y el vidrio oscuro con brillos.

**Key Characteristics:**
- Tintas planas sobre papel crema, con el bordó y el rosa del logo como identidad.
- Una cifra de cartel en Anton, con Public Sans para todo lo que se lee de corrido.
- Dos voces visibles: oficial en bordó, estimación de MECOPOL en negro con rosa.
- Esquinas rectas y filetes de 3px en lugar de tarjetas y sombras.
- Alturas fijas en píxeles, para vivir dentro de un iframe.

## Colors

Cuatro tintas de afiche (bordó, crema, negro y rosa) y unos pocos tintes sólidos derivados, cada uno con una tarea en los datos.

### Primary
- **Bordó MECOPOL** (#950b32): la voz de lo oficial. Campo del afiche, banda, pie, cifras y títulos sobre papel, filetes, último mes sobre papel y máximo de cada fila del mapa de calor. Viene del logo y no se cambia.
- **Bordó Quemado** (#6d0623): la tinta más oscura del bordó. Pista de la barra del mandato, fondo del código en el pie y escalón superior del mapa.
- **Bordó Tinte** (#bc677a): historial sobre papel, en tinte sólido (3,4:1 sobre crema).

### Secondary
- **Rosa MECOPOL** (#ff8bae): junto con el negro firma la estimación: cifras, títulos, selector y serie de la canasta. Sobre el campo bordó aparece además en el signo % de la cifra del mes (4:1), como tinta de identidad del logo; ahí no significa estimación.
- **Rosa Medio** (#dd7a96): historial sobre el campo bordó (3,1:1).

### Neutral
- **Crema Papel** (#f7efe6): el papel de toda la página y la tinta de lectura sobre bordó y sobre negro (7,8:1 y 16,9:1).
- **Tinta Negra** (#1a0a10): texto sobre papel y campo de la estimación. Sobre papel y sin rosa es tinta de lectura y segundo polo de las barras divergentes de rubros, no la firma de MECOPOL.
- **Tinta Lavada** (#5e4a50) y **Tinta Lavada sobre Negro** (#c9b7bc): textos secundarios, ejes y notas de cada contexto (7,2:1 y 10:1).
- **Filetes finos y resaltes** (`linea`, `resalta`, `grilla` y sus pares `-tinta`): líneas de tabla, hover de fila y grilla de gráficos. Son las únicas transparencias de interfaz y siempre apoyan sobre un fondo plano.
- **Placa del Logo** (#ffffff): fondo del logo dentro de la banda, con 3px de aire.

### Escalas de datos
- **Mapa** (`mapa-1` a `mapa-4`: #f4c9d6, #e77f9f, #c02a57, #6d0623): cuatro tintas de la más clara a la más oscura. `mapa-sin-dato` (#eadfd3) queda para la geometría sin valor.
- **Mapa de calor** (`calor-1` a `calor-4`): bordó al 8, 24, 40 y 56 %, siempre sobre crema, donde resuelve a #efddd8, #dfb8bb, #d0949e y #c06f81. El texto negro lee entre 14,6:1 y 5,3:1 en los cuatro.

### Named Rules
**La Regla de las Dos Voces.** Lo oficial va en bordó; lo estimado por MECOPOL, siempre en tinta negra con rosa. La firma es el par, en la cifra y en toda su sección. Dentro del campo negro el contraste manda: el bordó no se lee sobre negro (2,2:1), así que lo oficial pasa a crema o a tinta lavada, y el rosa queda solo para la estimación de MECOPOL.

**La Regla del Último Mes.** En el campo bordó, el último mes va en crema y el historial en rosa medio. Sobre papel, el último mes va en bordó y el historial en #bc677a sólido. El último mes siempre lleva la tinta más fuerte del contexto.

**La Regla de los Cuatro Escalones.** El mapa y el mapa de calor se pintan en cuatro escalones planos de intervalos iguales, sin rampa continua. El máximo de cada fila del mapa de calor va en bordó lleno con texto crema, fuera de los cuatro escalones.

## Typography

**Display Font:** Anton (con Arial Narrow, sans-serif)
**Body Font:** Public Sans, peso variable de 400 a 800 (con Helvetica Neue, Arial, sans-serif)

**Character:** Anton es la letra de cartel: angosta, un solo peso, hecha para verse de lejos. Public Sans es la voz institucional que explica, etiqueta y sostiene las tablas sin competir.

### Hierarchy
- **Cifra del mes** (Anton 400, se ajusta a la cantidad de caracteres hasta 270px, 1,16): solo la inflación del último mes en el afiche. Hasta 170px en pantallas angostas. El signo % va a la mitad del tamaño y en rosa.
- **Cifra** (Anton 400, clamp de 52 a 88px, 1,16): las cifras de la fila bajo el afiche. Baja a un clamp de 44 a 76px hasta 1040px.
- **Cifra comparada** (Anton 400, clamp de 38 a 50px, 1,16): los cuatro valores de la canasta.
- **Headline de afiche** (Anton 400, clamp de 32 a 46px, 1,06): título del mes dentro del campo bordó.
- **Headline** (Anton 400, clamp de 38 a 62px, 1,08): títulos de sección, en la tinta de acento del contexto.
- **Title** (Anton 400, clamp de 26 a 34px, 1,15; 24px en el pie): subtítulos de sección y del pie.
- **Banda** (Public Sans 800, 19px, 1,2): el título del tablero en la banda fija. Es lo único titular que no va en Anton, porque la banda no compite con el afiche.
- **Body** (Public Sans 400, 16px, 1,5; 17px y 1,4 en el afiche): lectura, con un máximo de 68 a 72 caracteres por línea.
- **Tabla** (Public Sans 400, de 13 a 15px según densidad, cifras tabulares): todas las tablas.
- **Control** (Public Sans, 14px; 600 en selectores, 500 en navegación y 700 en la sección activa).
- **Label** (Public Sans 600, 13px): encabezados de tabla y notas. Los ejes de los gráficos van a 12px y 400. Sin mayúsculas sostenidas.

### Named Rules
**La Regla del Cartel.** Anton lleva cifras de cartel y títulos; lo que se consulta (tablas, ejes, etiquetas del mapa) va en Public Sans.

**La Regla del Decimal de la Canasta.** La serie de la canasta se muestra con un decimal porque así la entrega el generador. No se le agregan decimales al formatear: el segundo sería un cero inventado.

## Layout

Una sola columna de bandas a todo el ancho, con margen lateral fluido de 16 a 48px que centra el contenido en 1344px. El afiche se divide en cifra flexible y columna de 300 a 400px, con 340px de alto mínimo. La fila de cifras reparte tres partes iguales y una de 1,2 para el bloque negro, que llega hasta el borde de la pantalla. Las secciones separan sus bloques con 22px; las columnas internas, con 36px. Los dos gráficos de Poder de compra van en dos columnas iguales de 340px de alto (280px en pantallas angostas), cada uno con su leyenda debajo, y se apilan a 900px.

El orden se rearma por ancho: a 1040px o menos el afiche pasa a una columna con el título arriba de la cifra, las cifras van de a dos y solo queda fija la fila de secciones, que se desliza en horizontal. A 900px se apilan regiones y canasta, y los valores de la canasta van de a dos. A 700px aparece la indicación de deslizar y las tablas anchas mantienen fija la primera columna. A 560px los gráficos bajan de 400 a 300px, el mapa de 600 a 480px, y la tabla de otras estimaciones se rearma como fichas.

**La Regla del Iframe.** Ningún alto depende del viewport, porque la página se inserta por iframe: nada de `vh`, `dvh`, `svh` ni `lvh`. Los altos de afiche, gráficos, mapa y barras van en píxeles fijos por rango de ancho; lo único fluido se calcula sobre el ancho del marco o del contenedor (`vw`, `cqw`).

## Elevation & Depth

El sistema es plano: no hay elevación. La profundidad se resuelve con el cambio de campo (bordó, crema, negro) y con filetes de 3px. La banda fija se separa por su color y no por una sombra.

**La Regla de la Tinta Plana.** Sin sombras, degradados ni desenfoque. Dos mecanismos técnicos llevan el nombre `shadow` sin serlo y siguen permitidos: el subrayado interior de 2 a 3px de la navegación, sin difuminar, y la banda plana de hover del gráfico de barras. Ambos se ven como tinta plana.

## Shapes

Esquinas rectas en todo (0), incluidos tooltips, barras, marcadores cuadrados de 7 a 9px en los gráficos y muestras de leyenda. Los filetes son el otro elemento formal: 3px para separar secciones y cifras y para encabezar cada caja, 2px en el contorno del selector, 1px en tablas. El borde crema de 1,5px entre regiones del mapa actúa como un corte de papel.

## Components

### Buttons
Selector segmentado de tinta entera: se usa para cambiar la medida de un gráfico; no hay otros botones.
- **Shape:** rectos (0), con contorno de 2px en la tinta de acento y 44px de alto mínimo.
- **Default:** fondo transparente y texto en la tinta de acento (bordó sobre papel, rosa sobre negro).
- **Elegido:** tinta llena con el texto invertido (crema sobre bordó, negro sobre rosa).
- **Hover / Focus:** resalte del 5 o 7 % en .15s; contorno de foco de 3px en el color del texto, hacia adentro.

### Cards / Containers
No hay tarjetas. La caja de contenido es un filete superior de 3px en la tinta del texto y 16px de aire, sin fondo propio. Las cifras se separan con filetes verticales de 3px en bordó.

### Navigation
Banda fija en bordó con la placa del logo (50px), el título del tablero y las secciones en Public Sans 14px, con 44px de alto mínimo. El hover marca un subrayado crema de 2px; la sección activa, uno de 3px y peso 700. A 1040px o menos se esconde la fila del logo y queda fija solo la de secciones.

### Afiche (signature)
El campo bordó a sangre con la cifra del mes en crema. A la derecha, alineados a la derecha: título del mes, comparación con el mes anterior, barra del mandato de 6px y 13 barras en rosa medio con la última en crema. Las barras suben desde la base en .7s (`cubic-bezier(.16, 1, .3, 1)`), con 35ms de escalonado por barra. En escritorio, la punta de la coma de la cifra termina a la altura de la base de las barras, a 20px del borde del campo. El afiche es compacto a propósito: mide unos 360px de alto en escritorio y las barras 80px (56px en pantallas angostas), para que la fila de cifras entre en la primera pantalla. Un afiche de más de media pantalla se probó y resultó excesivo, sobre todo en el teléfono.

### Fila de cifras
Cifras oficiales en bordó sobre papel, con comparación y una línea mínima de 2px en bordó terminada en un marcador cuadrado. La última celda es el bloque negro de la estimación, en rosa, que lleva escrito que no es dato oficial y enlaza a su método.

### Sección de tinta negra
La sección de la canasta redefine todas las tintas del contexto: campo negro, texto crema, títulos, selector y serie en rosa de 3px, con la serie oficial en crema de 2px. La tooltip se invierte a crema con texto negro. Cualquier pieza de la estimación se arma con este contexto, no con colores sueltos.

### Mapa y mapa de calor
Mapa de regiones en los cuatro escalones, con etiquetas como fichas de papel: fondo crema, borde negro de 1px, nombre en 600 y valor en 800. GBA lleva su ficha en el mar, unida al AMBA por una línea de 1px. El mapa de calor compara dentro de cada fila, con 2px entre celdas, texto negro y el máximo en bordó lleno.

### Barras divergentes
Precio relativo de cada rubro desde un eje central de 1px: bordó si se encareció más que el promedio, negro si se encareció menos, en barras de 12px con el valor a un costado.

### Avisos de estado
Datos de prueba, dato parcial y error de carga. Fondo crema, texto negro a 14px y filete bordó: de 3px abajo si ocupa todo el ancho, de 3px en todo el contorno si va dentro de una sección.

### Tooltips y movimiento
Tooltips rectas sin sombra, de texto crema sobre negro en lo oficial. Transiciones de .15s para estados y 400ms para gráficos. Con `prefers-reduced-motion`, todo queda quieto.

## Do's and Don'ts

### Do:
- **Do** poner cada dato oficial en bordó sobre papel y cada estimación de MECOPOL en el contexto de tinta negra con rosa, con la leyenda «Estimación de MECOPOL».
- **Do** dar al último mes la tinta más fuerte de su contexto: crema con historial en rosa medio sobre bordó, bordó con historial en #bc677a sólido sobre papel.
- **Do** pintar mapa y mapa de calor en cuatro escalones planos de intervalos iguales, y el máximo de cada fila del mapa de calor en bordó lleno.
- **Do** dimensionar los altos en píxeles por rango de ancho, porque la página se inserta por iframe.
- **Do** mostrar la serie de la canasta con un decimal, como la entrega el generador.
- **Do** usar una sola escala por comparación, y dejar que la jerarquía salga del tamaño.
- **Do** mantener el logo de `docs/img/logo-mecopol.png` sobre su placa blanca, y 44px de alto mínimo en los controles.

### Don't:
- **Don't** usar sombras, degradados ni desenfoque; tampoco esquinas redondeadas.
- **Don't** usar el par de negro y rosa para un dato oficial, ni el bordó como voz de la estimación.
- **Don't** usar unidades de alto de viewport (`vh`, `dvh`, `svh`, `lvh`) en ninguna medida.
- **Don't** pintar datos con rampas continuas ni usar más de cuatro escalones.
- **Don't** agregar decimales a la serie de la canasta al formatearla.
- **Don't** volver a la fila de cuatro tarjetas iguales ni al vidrio oscuro con brillos.
