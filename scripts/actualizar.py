"""
MECOPOL · Tablero de precios — actualización de datos
=====================================================

Baja las series del IPC del INDEC desde la API de Series de Tiempo
(apis.datos.gob.ar), calcula los indicadores del gobierno actual y los
guarda en docs/data/dashboard.json, que es lo que lee la página.

Lo corre la GitHub Action todos los días. También se puede correr a mano:
    pip install -r requirements.txt
    python scripts/actualizar.py

Si algo falla (la API no responde, falta una serie, un control no da),
el script termina con error y NO pisa el JSON anterior: la página sigue
mostrando los últimos datos buenos y GitHub avisa por mail.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "docs" / "data" / "dashboard.json"
CONFIG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))

API = "https://apis.datos.gob.ar/series/api/series/"
SEARCH = "https://apis.datos.gob.ar/series/api/search/"
IPC_NAC = "148.3_INIVELNAL_DICI_M_26"   # IPC Nacional, nivel general (dic-2016 = 100)

DIVISIONES = {
    "Alimentos y bebidas no alcohólicas": "alimen",
    "Bebidas alcohólicas y tabaco": "tabaco",
    "Prendas de vestir y calzado": "prenda",
    "Vivienda, agua, electricidad, gas y otros combustibles": "vivien",
    "Equipamiento y mantenimiento del hogar": "equip",
    "Salud": "salud",
    "Transporte": "transp",
    "Comunicación": "comuni",
    "Recreación y cultura": "recrea",
    "Educación": "educa",
    "Restaurantes y hoteles": "restau",
    "Bienes y servicios varios": "vario",
}
REGIONES = ["gba", "pampeana", "noreste", "noroeste", "cuyo", "patagonia"]
MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

SESION = requests.Session()
SESION.headers["User-Agent"] = "mecopol-dashboard (github actions)"


# ------------------------------------------------------------------
# Acceso a la API
# ------------------------------------------------------------------
def pedir(url, params, intentos=4):
    """GET con reintentos: la API a veces tarda o devuelve 5xx."""
    for i in range(intentos):
        try:
            r = SESION.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            print(f"  ⚠️ HTTP {r.status_code} (intento {i + 1})")
        except requests.RequestException as e:
            print(f"  ⚠️ {e.__class__.__name__} (intento {i + 1})")
        time.sleep(5 * (i + 1))
    raise RuntimeError(f"La API no respondió: {url} {params}")


def traer(ids, desde, hasta):
    """Descarga series (máx. 40 por consulta) y devuelve un DataFrame mensual."""
    partes = []
    for i in range(0, len(ids), 40):
        lote = ids[i:i + 40]
        j = pedir(API, {"ids": ",".join(lote), "start_date": desde,
                        "end_date": hasta, "limit": 1000})
        partes.append(pd.DataFrame(j["data"], columns=["fecha"] + lote).set_index("fecha"))
    df = pd.concat(partes, axis=1).apply(pd.to_numeric, errors="coerce")
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def buscar_division(nombre, clave):
    """Busca la serie NACIONAL, mensual y en nivel (no en variación) de una división."""
    for pagina in range(3):
        j = pedir(SEARCH, {"q": f"IPC {nombre} Nacional Base dic 2016 Mensual",
                           "limit": 100, "start": pagina * 100})
        for x in j.get("data", []):
            f, d = x.get("field", {}), x.get("dataset", {})
            fid = f.get("id") or ""
            desc = (f.get("description") or "").lower()
            dset = (d.get("title") or "").lower()
            if (f.get("frequency") == "R/P1M"
                    and "diciembre 2016" in dset and "nacional" in dset
                    and clave in desc
                    and ("nacional" in desc or "NAL_" in fid)
                    and not any(p in desc for p in ["variaci", "tasa", "incidencia"] + REGIONES)):
                return fid
    return None


# ------------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------------
def ym(fecha):
    return fecha.strftime("%Y-%m")


def etiqueta(fecha):
    return f"{MESES_ES[fecha.month - 1]}-{str(fecha.year)[2:]}"


def meses_entre(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)


def r(x, n=2):
    """Redondea y convierte NaN en None (JSON válido)."""
    return None if x is None or pd.isna(x) else round(float(x), n)


def var(s, a, b):
    """Variación porcentual de la serie s entre las fechas a (base) y b."""
    return (s[b] / s[a] - 1) * 100


# ------------------------------------------------------------------
# Cálculo
# ------------------------------------------------------------------
def main():
    hoy = pd.Timestamp.today().normalize()
    inicio = pd.Timestamp(CONFIG["inicio_gobierno"])
    fin = pd.Timestamp(CONFIG["fin_mandato"])
    un_mes, un_anio = pd.DateOffset(months=1), pd.DateOffset(months=12)

    # 1. Nivel general --------------------------------------------------
    print("📥 IPC nacional, nivel general")
    desde = ym(inicio - pd.DateOffset(months=14)) + "-01"
    nac = traer([IPC_NAC], desde, hoy.strftime("%Y-%m-%d"))[IPC_NAC].dropna()
    mes = nac.index.max()
    previo = mes - un_mes
    K = meses_entre(inicio, mes)
    print(f"   último dato: {etiqueta(mes)} = {nac[mes]:,.2f} · mes {K} de gobierno")

    acum_gob = var(nac, inicio, mes)
    kpis = {
        "mensual": r(var(nac, previo, mes)),
        "mensual_previo": r(var(nac, previo - un_mes, previo)),
        "interanual": r(var(nac, mes - un_anio, mes), 1),
        "interanual_previo": r(var(nac, previo - un_anio, previo), 1),
        "acum_anio": r(var(nac, pd.Timestamp(year=mes.year - 1, month=12, day=1), mes), 1),
        "acum_gobierno": r(acum_gob, 1),
        "promedio_mensual": r(((1 + acum_gob / 100) ** (1 / K) - 1) * 100),
    }

    serie = [{
        "fecha": ym(f),
        "mensual": r(var(nac, f - un_mes, f)),
        "interanual": r(var(nac, f - un_anio, f), 1),
        "acumulada": r(var(nac, inicio, f), 1),
    } for f in nac.index if f > inicio]

    pico = max(serie, key=lambda x: x["mensual"])
    primeros5 = var(nac, inicio, inicio + pd.DateOffset(months=5))
    resto = ((1 + acum_gob / 100) / (1 + primeros5 / 100) - 1) * 100

    # 2. Rubros ---------------------------------------------------------
    ids_div = {}
    for nombre, clave in DIVISIONES.items():
        fid = CONFIG.get("ids_divisiones", {}).get(nombre) or buscar_division(nombre, clave)
        print(f"   {'✅' if fid else '❌'} {nombre}: {fid}")
        if fid:
            ids_div[nombre] = fid
    if len(ids_div) < len(DIVISIONES):
        faltan = sorted(set(DIVISIONES) - set(ids_div))
        raise RuntimeError(f"Faltan rubros: {faltan}. Cargar sus ids en config.json → ids_divisiones")

    div = traer(list(ids_div.values()), desde, ym(mes) + "-01")
    div.columns = list(ids_div)

    rubros = []
    for n in div.columns:
        s = div[n]
        acum = var(s, inicio, mes)
        rubros.append({
            "rubro": n,
            "mensual": r(var(s, previo, mes)),
            "interanual": r(var(s, mes - un_anio, mes), 1),
            "acum_gobierno": r(acum, 1),
            "relativo": r(((1 + acum / 100) / (1 + acum_gob / 100) - 1) * 100, 1),
        })

    # 3. Escenarios hasta el fin del mandato ---------------------------
    rem = CONFIG["rem"]
    rem_2027 = ((1 + rem["anual_2027"] / 100) ** (1 / 12) - 1) * 100
    reglas = {
        "Desinflación rápida": lambda f: 1.0,
        "Consenso REM": lambda f: rem["mensual"].get(ym(f), rem_2027),
        "Se estanca en 2%": lambda f: 2.0,
        "Shock electoral": lambda f: ({8: 4.0, 9: 6.0, 10: 4.0, 11: 3.0}[f.month]
                                      if f.year == 2027 and f.month >= 8 else 2.0),
    }
    supuestos = {
        "Desinflación rápida": "1% mensual hasta el final",
        "Consenso REM": f"Expectativas del BCRA ({etiqueta(pd.Timestamp(rem['publicado'] + '-01'))})",
        "Se estanca en 2%": "La baja se frena en el nivel actual",
        "Shock electoral": "2% mensual y salto en el tramo electoral de 2027",
    }
    futuras = pd.date_range(mes + un_mes, fin, freq="MS")
    fechas_esc = [ym(mes)] + [ym(f) for f in futuras]
    escenarios, cierre = {}, []
    nivel_hoy = 1 + acum_gob / 100
    # índice relativo a 'inicio' para calcular la interanual al final
    rel_inicio = (nac / nac[inicio]).loc[inicio:]
    for nombre, regla in reglas.items():
        tasas = np.array([regla(f) for f in futuras]) / 100
        camino = np.r_[nivel_hoy, nivel_hoy * np.cumprod(1 + tasas)]
        escenarios[nombre] = [r((v - 1) * 100, 1) for v in camino]
        completo = pd.concat([rel_inicio.loc[:previo], pd.Series(camino, index=[mes] + list(futuras))])
        cierre.append({
            "escenario": nombre,
            "supuesto": supuestos[nombre],
            "acumulada": r((completo[fin] - 1) * 100, 1),
            "interanual_final": r((completo[fin] / completo[fin - un_anio] - 1) * 100, 1),
        })

    # 4. Controles de calidad -------------------------------------------
    assert serie and kpis["mensual"] is not None, "Serie vacía"
    assert all(x["relativo"] is not None for x in rubros), "Rubros incompletos"

    datos = {
        "actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "ultimo_mes": ym(mes),
        "inicio": ym(inicio),
        "fin_mandato": ym(fin),
        "mes_gobierno": K,
        "meses_restantes": meses_entre(mes, fin),
        "kpis": kpis,
        "serie": serie,
        "hitos": {
            "pico": pico,
            "primeros_5": r(primeros5, 1),
            "resto": r(resto, 1),
            "meses_resto": K - 5,
        },
        "rubros": rubros,
        "escenarios": {"fechas": fechas_esc, "series": escenarios, "rem_publicado": rem["publicado"]},
        "cierre": cierre,
        "fuentes": {"nivel_general": IPC_NAC, "divisiones": ids_div},
    }

    # Si los números no cambiaron, no se reescribe el archivo: así la Action
    # no genera un commit por día y la fecha muestra el último cambio real.
    if SALIDA.exists():
        previo_json = json.loads(SALIDA.read_text(encoding="utf-8"))
        sin_fecha = lambda x: {k: v for k, v in x.items() if k != "actualizado"}
        if sin_fecha(previo_json) == json.loads(json.dumps(sin_fecha(datos), ensure_ascii=False)):
            print(f"✔️ Sin datos nuevos (último mes: {etiqueta(mes)}).")
            return

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"💾 {SALIDA.relative_to(RAIZ)} · {etiqueta(mes)} · mes {K} · "
          f"mensual {kpis['mensual']}% · interanual {kpis['interanual']}%")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"⛔ {e}")
        sys.exit(1)
