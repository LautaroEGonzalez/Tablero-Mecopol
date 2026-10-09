"""
MECOPOL · Universidades y Ley 27.795 — primera etapa, solo fuentes oficiales
==========================================================================

Arma docs/data/universidades.json para docs/universidades.html.

- Hechos (fechas, votaciones, normas, fallos): fuentes/universidades_fuentes.csv.
  Solo entran datos con fuente oficial (Boletín Oficial, Congreso, Poder Judicial).
- Financiamiento: baja de Presupuesto Abierto (Ministerio de Economía) el crédito
  anual de cada año, suma el DEVENGADO del programa 26 "Desarrollo de la Educación
  Superior" (el que nombra el art. 2 de la Ley 27.795) y lo deflacta con el IPC
  promedio anual de la serie oficial del tablero (docs/data/historia.json, INDEC).
- UNAJ: si el archivo de Presupuesto Abierto trae el detalle por universidad
  (columna subparcial_desc), se calcula también la serie de la UNAJ.

No se usan cifras de consultoras, centros de estudio ni medios. Si Presupuesto
Abierto no se puede bajar, la página muestra la sección como pendiente.

Los años cerrados se bajan una sola vez y quedan guardados en el JSON (clave
"presupuesto_abierto"); el año en curso se vuelve a bajar cada 7 días.
"""

import csv
import io
import json
import re
import sys
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from actualizar import SESION, r  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "docs" / "data" / "universidades.json"
HISTORIA = RAIZ / "docs" / "data" / "historia.json"
FUENTES = RAIZ / "fuentes" / "universidades_fuentes.csv"

PA_URL = "https://dgsiaf-repo.mecon.gob.ar/repository/pa/datasets/{anio}/credito-anual-{anio}.zip"
PA_PAGINA = "https://www.presupuestoabierto.gob.ar/sici/datos-abiertos"
PROGRAMA = "desarrollo de la educacion superior"
UNAJ = "arturo jauretche"
DESDE = 2015                 # para tener la base de Macri (2015 → 2019)
MAX_DESCARGAS = 4            # por corrida, para no pasar el tiempo de la Action; el resto sigue al día siguiente
MANDATOS = [("macri", 2015, 2019), ("af", 2019, 2023), ("milei", 2023, None)]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------- Presupuesto Abierto
def bajar_anio(anio):
    """Devuelve los totales del programa para un año, en millones de pesos."""
    url = PA_URL.format(anio=anio)
    with tempfile.TemporaryFile() as tmp:
        with SESION.get(url, timeout=180, stream=True) as resp:
            resp.raise_for_status()
            for parte in resp.iter_content(1 << 20):
                tmp.write(parte)
        tmp.seek(0)
        with zipfile.ZipFile(tmp) as z:
            nombre = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            crudo = z.read(nombre)
    for enc in ("utf-8-sig", "latin-1"):
        try:
            texto = crudo.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    del crudo
    primera = texto.split("\n", 1)[0]
    sep = ";" if primera.count(";") > primera.count(",") else ","
    cab = {norm(c): c for c in next(csv.reader([primera], delimiter=sep))}

    def col(*opciones, obligatoria=True):
        for o in opciones:
            if o in cab:
                return cab[o]
        if obligatoria:
            raise RuntimeError(f"{anio}: falta la columna {opciones[0]} (hay: {list(cab)[:12]}…)")
        return None

    c_prog, c_dev, c_vig = col("programa_desc"), col("credito_devengado"), col("credito_vigente")
    c_inc = col("inciso_id", obligatoria=False)
    c_sub = col("subparcial_desc", obligatoria=False)
    usar = [c for c in (c_prog, c_dev, c_vig, c_inc, c_sub) if c]
    tot = {"devengado": 0.0, "vigente": 0.0, "devengado_inciso5": 0.0, "unaj_devengado": 0.0, "unaj_vigente": 0.0, "filas": 0}
    for ch in pd.read_csv(io.StringIO(texto), sep=sep, usecols=usar, dtype=str, chunksize=200_000):
        ch = ch[ch[c_prog].map(norm).str.contains(PROGRAMA, na=False)]
        if ch.empty:
            continue
        for c in (c_dev, c_vig):
            ch[c] = pd.to_numeric(ch[c].str.replace(",", ".", regex=False), errors="coerce").fillna(0)
        tot["filas"] += len(ch)
        tot["devengado"] += ch[c_dev].sum()
        tot["vigente"] += ch[c_vig].sum()
        if c_inc:
            tot["devengado_inciso5"] += ch.loc[ch[c_inc].str.strip() == "5", c_dev].sum()
        if c_sub:
            es_unaj = ch[c_sub].map(norm).str.contains(UNAJ, na=False)
            tot["unaj_devengado"] += ch.loc[es_unaj, c_dev].sum()
            tot["unaj_vigente"] += ch.loc[es_unaj, c_vig].sum()
    if not tot["filas"]:
        raise RuntimeError(f"{anio}: no aparece el programa '{PROGRAMA}'")
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in tot.items()} | {
        "url": url, "bajado": datetime.now(timezone.utc).date().isoformat()}


def presupuesto_abierto(previo):
    hoy = datetime.now(timezone.utc).date()
    cache = dict(previo.get("presupuesto_abierto", {}))
    errores, seguidos, bajados = [], 0, 0
    # primero 2023 (la base) y los años más recientes
    orden = [2023, 2024, 2025] + list(range(2022, DESDE - 1, -1)) + list(range(2026, hoy.year + 1))
    for anio in dict.fromkeys(a for a in orden if DESDE <= a <= hoy.year):
        c = cache.get(str(anio))
        cerrado = anio < hoy.year and not (anio == hoy.year - 1 and hoy.month <= 3)
        if c and (cerrado or (hoy - datetime.fromisoformat(c["bajado"]).date()).days < 7):
            continue
        if bajados >= MAX_DESCARGAS:
            print(f"   {anio}: queda para la próxima corrida")
            continue
        try:
            print(f"📥 Presupuesto Abierto {anio}")
            bajados += 1
            cache[str(anio)] = bajar_anio(anio)
            print(f"   devengado {cache[str(anio)]['devengado']:,.0f} M$ ({cache[str(anio)]['filas']} filas)")
        except Exception as e:  # noqa: BLE001
            errores.append(f"{anio}: {str(e)[:160]}")
            print(f"   ⚠️ {anio}: {str(e)[:160]}")
            seguidos += 1
            if seguidos >= 2 and not cache:
                errores.append("Se cortó la descarga: Presupuesto Abierto no responde")
                print("   ⚠️ Presupuesto Abierto no responde; la sección queda pendiente")
                break
            continue
        seguidos = 0
    return cache, errores



# ------------------------------------------------------------------ deflactor
def ipc_promedio_anual():
    h = json.loads(HISTORIA.read_text(encoding="utf-8"))
    nivel, idx = 100.0, {}
    for x in h["serie"]:
        nivel *= 1 + x["mensual"] / 100
        idx[x["fecha"]] = nivel
    prom = {}
    for anio in {int(f[:4]) for f in idx}:
        meses = [v for f, v in idx.items() if f.startswith(f"{anio}-")]
        if len(meses) == 12:
            prom[anio] = sum(meses) / 12
    gobs = {g["id"]: {k: g[k] for k in ("id", "nombre", "corto", "color", "base", "fin")} for g in h["gobiernos"]}
    return prom, gobs


def gobierno_de(anio, gobs):
    mejor, n = None, 0
    for g in gobs.values():
        ini = pd.Timestamp(g["base"] + "-01") + pd.DateOffset(months=1)
        fin = pd.Timestamp(g["fin"] + "-01")
        k = sum(1 for m in range(1, 13) if ini <= pd.Timestamp(anio, m, 1) <= fin)
        if k > n:
            mejor, n = g["id"], k
    return mejor or list(gobs)[-1]      # años futuros: el último gobierno



# ----------------------------------------------------------------------- main
def main():
    previo = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    filas = list(csv.DictReader(FUENTES.open(encoding="utf-8")))
    F = {}
    for f in filas:
        F.setdefault(f["seccion"], []).append(f)
    ipc, gobs = ipc_promedio_anual()
    hoy = datetime.now(timezone.utc).date()

    # serie propia: devengado real, 2023 = 100 (solo años cerrados con IPC de 12 meses)
    cache, errores = presupuesto_abierto(previo)
    indice, unaj_idx, controles = [], [], []
    base = cache.get("2023")
    if base and 2023 in ipc and base["devengado"] > 0:
        real23 = base["devengado"] / ipc[2023]
        u23 = (base.get("unaj_devengado") or 0) / ipc[2023]
        for a in sorted(int(x) for x in cache):
            c = cache[str(a)]
            if a not in ipc or a >= hoy.year or c["devengado"] <= 0:
                continue
            indice.append({"anio": a, "valor": r(c["devengado"] / ipc[a] / real23 * 100, 1), "tipo": "ejecutado",
                           "devengado_millones": r(c["devengado"], 1), "ipc_promedio": r(ipc[a], 2),
                           "gobierno": gobierno_de(a, gobs)})
            if u23 and c.get("unaj_devengado"):
                unaj_idx.append({"anio": a, "valor": r(c["unaj_devengado"] / ipc[a] / u23 * 100, 1),
                                 "devengado_millones": r(c["unaj_devengado"], 1)})
        # controles de consistencia (no contra terceros): el programa aparece y los montos son razonables
        for x in indice:
            if not 20 <= x["valor"] <= 250:
                controles.append(f"{x['anio']}: índice {x['valor']} fuera de rango, revisar el archivo de Presupuesto Abierto")
    if controles:
        print("⚠️ " + " · ".join(controles))
        indice, unaj_idx = [], []
    por = {x["anio"]: x for x in indice}

    tarjetas = []
    ult = max(por) if por else None
    for gid, a0, a1 in MANDATOS:
        a1 = a1 or ult
        g = gobs.get(gid, {"id": gid, "corto": gid, "nombre": gid, "color": "#888"})
        x0, x1 = por.get(a0), por.get(a1) if a1 else None
        tarjetas.append({"id": gid, "corto": g["corto"], "nombre": g["nombre"], "color": g["color"], "desde": a0, "hasta": a1,
                         "variacion": r((x1["valor"] / x0["valor"] - 1) * 100, 1) if x0 and x1 else None})

    # UNAJ en el año en curso: crédito vigente según Presupuesto Abierto
    actual = cache.get(str(hoy.year), {})
    unaj = {"indice": unaj_idx if len(unaj_idx) >= 3 else [],
            "vigente_actual": {"anio": hoy.year, "millones": r(actual["unaj_vigente"], 1),
                               "sistema_millones": r(actual["vigente"], 1), "bajado": actual.get("bajado")}
            if actual.get("unaj_vigente") else None}

    def link_de(f):
        return {"fecha": f["fecha"], "texto": f["texto"], "fuente": f["fuente"], "link": f["link"]}

    datos = {
        "actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "etapa": "solo fuentes oficiales",
        "hitos": {f["clave"]: link_de(f) for f in F.get("hito", [])},
        "ley": [{"clave": f["clave"], "texto": f["texto"], "fuente": f["fuente"], "link": f["link"]} for f in F.get("ley", [])],
        "gobierno_dice": [{"texto": f["texto"], "fuente": f["fuente"], "link": f["link"]} for f in F.get("gobierno", [])],
        "cronologia": [{"actor": f["tipo"], **link_de(f)} for f in F.get("crono", [])],
        "pendientes": [f["texto"] for f in F.get("pendiente", [])],
        "tarjetas": tarjetas,
        "indice": indice,
        "unaj": unaj,
        "gobiernos": list(gobs.values()),
        "ipc_promedio": {str(a): r(v, 2) for a, v in sorted(ipc.items()) if a >= DESDE},
        "presupuesto_abierto_estado": {"errores": errores, "controles": controles,
                                       "anios": sorted(int(a) for a in cache), "url": PA_PAGINA},
        "presupuesto_abierto": cache,
    }

    if previo:
        sin = lambda x: {k: v for k, v in x.items() if k != "actualizado"}
        if sin(previo) == json.loads(json.dumps(sin(datos), ensure_ascii=False)):
            print("✔️ Sin cambios en universidades.")
            return
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"💾 {SALIDA.relative_to(RAIZ)} · años de Presupuesto Abierto: {datos['presupuesto_abierto_estado']['anios']} · " +
          " · ".join(f"{t['corto']} {t['variacion']}%" for t in tarjetas))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"⛔ {e}")
        sys.exit(1)
