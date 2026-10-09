"""
MECOPOL · Universidades y Ley 27.795
====================================

Arma docs/data/universidades.json para docs/universidades.html.

1. Lee las cifras recopiladas, cada una con su fuente y link
   (fuentes/universidades_fuentes.csv).
2. Intenta calcular una serie propia: baja de Presupuesto Abierto el crédito
   anual de cada año (dgsiaf-repo.mecon.gob.ar), suma el DEVENGADO del programa
   "Desarrollo de la Educación Superior" y lo deflacta con el IPC promedio anual
   de la serie oficial que usa el tablero (docs/data/historia.json).
3. Controla la serie propia contra las cifras recopiladas. Si da parecido, la
   usa para los años ejecutados; si no, o si no se pudo bajar, usa las
   recopiladas y deja la propia en el JSON para revisarla.

Los años cerrados se bajan una sola vez y quedan guardados en el JSON
(clave "presupuesto_abierto"); el año en curso se vuelve a bajar cada 7 días.
2026 (crédito vigente) y 2027 (proyecto) salen siempre de las cifras
recopiladas: no son ejecución.
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
MAX_DESCARGAS = 4           # por corrida, para no pasar el tiempo de la Action; el resto sigue al día siguiente
TOLERANCIA = 8.0             # puntos del índice 2023 = 100 contra las cifras recopiladas
MANDATOS = [("macri", 2015, 2019), ("af", 2019, 2023), ("milei", 2023, None)]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- recopiladas
def leer_fuentes():
    filas = list(csv.DictReader(FUENTES.open(encoding="utf-8")))
    por = {}
    for f in filas:
        por.setdefault(f["seccion"], []).append(f)
    return por


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
    tot = {"devengado": 0.0, "vigente": 0.0, "devengado_inciso5": 0.0, "unaj_devengado": 0.0, "filas": 0}
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
            tot["unaj_devengado"] += ch.loc[ch[c_sub].map(norm).str.contains(UNAJ, na=False), c_dev].sum()
    if not tot["filas"]:
        raise RuntimeError(f"{anio}: no aparece el programa '{PROGRAMA}'")
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in tot.items()} | {
        "url": url, "bajado": datetime.now(timezone.utc).date().isoformat()}


def presupuesto_abierto(previo):
    hoy = datetime.now(timezone.utc).date()
    cache = dict(previo.get("presupuesto_abierto", {}))
    errores, seguidos, bajados = [], 0, 0
    # primero los años que sirven para controlar contra las cifras recopiladas
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
                print("   ⚠️ Presupuesto Abierto no responde; se usan las cifras recopiladas")
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
    F = leer_fuentes()
    ipc, gobs = ipc_promedio_anual()

    recop = {int(f["fecha"]): {"anio": int(f["fecha"]), "valor": float(f["valor"]), "tipo": f["tipo"],
                               "como": f["texto"], "fuente": f["fuente"], "link": f["link"], "origen": "recopilada"}
             for f in F["indice"]}

    # serie propia
    cache, errores = presupuesto_abierto(previo)
    propio, unaj = {}, {}
    base = cache.get("2023")
    if base and 2023 in ipc:
        real23 = base["devengado"] / ipc[2023]
        u23 = base.get("unaj_devengado") or 0
        for a, c in cache.items():
            a = int(a)
            if a in ipc and c["devengado"] > 0:
                propio[a] = round(c["devengado"] / ipc[a] / real23 * 100, 1)
                if u23 and c.get("unaj_devengado"):
                    unaj[a] = round(c["unaj_devengado"] / ipc[a] / (u23 / ipc[2023]) * 100, 1)
    control = [{"anio": a, "propia": propio[a], "recopilada": recop[a]["valor"], "dif": r(propio[a] - recop[a]["valor"], 1)}
               for a in sorted(propio) if a in recop and a != 2023]
    usa_propia = bool(control) and all(abs(c["dif"]) <= TOLERANCIA for c in control) and 2024 in propio
    if propio:
        print("🔎 Control serie propia vs. recopilada: " + ", ".join(f"{c['anio']} {c['propia']} vs {c['recopilada']}" for c in control))
    print(f"   modo: {'serie propia' if usa_propia else 'cifras recopiladas'}")

    indice = []
    for a in sorted(set(recop) | (set(propio) if usa_propia else set())):
        if usa_propia and a in propio:
            fila = {"anio": a, "valor": propio[a], "tipo": "ejecutado", "origen": "propia",
                    "como": "Devengado del programa Desarrollo de la Educación Superior, deflactado con el IPC promedio anual",
                    "fuente": "Presupuesto Abierto (MECON) e IPC del tablero", "link": PA_PAGINA}
            if a in recop:
                fila["recopilada"] = recop[a]["valor"]
        elif a in recop:   # años sin serie propia (todavía no bajados, o vigente y proyecto): cifra recopilada
            fila = dict(recop[a])
        else:
            continue
        fila["gobierno"] = gobierno_de(a, gobs)
        indice.append(fila)
    por_anio = {x["anio"]: x for x in indice}

    # variación real por mandato
    directo = lambda x: x.get("origen") == "propia" or x["anio"] == 2023 or "vs. 2023" in x.get("como", "")
    ultimo_ej = max(x["anio"] for x in indice if x["tipo"] == "ejecutado")
    tarjetas = []
    for gid, a0, a1 in MANDATOS:
        a1 = a1 or ultimo_ej
        g = gobs.get(gid, {"id": gid, "corto": gid, "nombre": gid, "color": "#888"})
        x0, x1 = por_anio.get(a0), por_anio.get(a1)
        t = {"id": gid, "corto": g["corto"], "nombre": g["nombre"], "color": g["color"], "desde": a0, "hasta": a1,
             "variacion": r((x1["valor"] / x0["valor"] - 1) * 100, 1) if x0 and x1 else None,
             # aproximado: una punta sale de encadenar variaciones de fuentes distintas, no de una comparación directa con 2023
             "aproximado": bool(x0 and x1 and not (directo(x0) and directo(x1))),
             "fuentes": []}
        if x0 and x1:   # aproximado: todas las fuentes del encadenamiento; si no, las de las puntas
            tramo = [por_anio[a] for a in range(a0, a1 + 1) if a in por_anio] if t["aproximado"] else [x0, x1]
            t["fuentes"] = list(dict.fromkeys(x["fuente"] for x in tramo if x.get("fuente")))
        if gid == "milei" and 2026 in por_anio and por_anio[2026]["tipo"] == "vigente":
            t["vigente_2026"] = r(por_anio[2026]["valor"] - 100, 1)
        tarjetas.append(t)

    def filas(sec):
        return F.get(sec, [])

    cifras = {}
    for f in filas("cifra"):
        cifras.setdefault(f["clave"], {})[f["tipo"]] = {"valor": num(f["valor"]), "texto": f["texto"], "fecha": f["fecha"],
                                                         "fuente": f["fuente"], "link": f["link"]}
    datos = {
        "actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "modo": "propia" if usa_propia else "recopilada",
        "hitos": {f["clave"]: {"fecha": f["fecha"], "texto": f["texto"], "link": f["link"]} for f in filas("hito")},
        "estado": {"texto": filas("estado")[0]["texto"], "detalle": filas("estado")[0]["tipo"]} if filas("estado") else None,
        "tarjetas": tarjetas,
        "indice": indice,
        "pbi": [{"anio": int(f["fecha"]), "valor": float(f["valor"]), "max": num(f["valor_max"]), "tipo": f["tipo"],
                 "nota": f["texto"], "fuente": f["fuente"], "link": f["link"], "gobierno": gobierno_de(int(f["fecha"]), gobs)}
                for f in filas("pbi")],
        "salario": [{"fecha": f["fecha"], "valor": float(f["valor"]), "fuente": f["fuente"], "link": f["link"], "nota": f["texto"]}
                    for f in filas("salario")],
        "cifras": cifras,
        "unaj": {"presupuesto_2026": {f["clave"]: {"valor": float(f["valor"]), "texto": f["texto"]} for f in filas("unaj")},
                 "fuente": filas("unaj")[0]["fuente"] if filas("unaj") else None,
                 "link": filas("unaj")[0]["link"] if filas("unaj") else None,
                 "indice": [{"anio": a, "valor": v} for a, v in sorted(unaj.items())] if len(unaj) >= 3 and usa_propia else []},
        "cronologia": [{"fecha": f["fecha"], "actor": f["tipo"], "texto": f["texto"], "link": f["link"]} for f in filas("crono")],
        "gobiernos": list(gobs.values()),
        "ipc_promedio": {str(a): r(v, 2) for a, v in sorted(ipc.items()) if a >= DESDE},
        "serie_propia": {"indice": {str(a): v for a, v in sorted(propio.items())}, "control": control,
                         "tolerancia": TOLERANCIA, "errores": errores},
        "presupuesto_abierto": cache,
    }

    if previo:
        sin = lambda x: {k: v for k, v in x.items() if k != "actualizado"}
        if sin(previo) == json.loads(json.dumps(sin(datos), ensure_ascii=False)):
            print("✔️ Sin cambios en universidades.")
            return
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"💾 {SALIDA.relative_to(RAIZ)} · modo {datos['modo']} · " +
          " · ".join(f"{t['corto']} {t['variacion']}%" for t in tarjetas))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"⛔ {e}")
        sys.exit(1)
