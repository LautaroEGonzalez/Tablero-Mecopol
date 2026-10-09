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
# IPC reponderado
# ------------------------------------------------------------------
PONDERACIONES = RAIZ / "fuentes" / "ponderaciones_ipc.csv"
ENCUESTA = ("2017-11-01", "2018-11-01")   # período de relevamiento de la ENGHo 2017/18


def reponderar(ids_div, nac_corta, inicio, mes):
    un_mes, un_anio = pd.DateOffset(months=1), pd.DateOffset(months=12)
    pond = pd.read_csv(PONDERACIONES).set_index("division")
    div = traer(list(ids_div.values()), "2016-12-01", ym(mes) + "-01")
    div.columns = list(ids_div)
    nac = traer([IPC_NAC], "2016-12-01", ym(mes) + "-01")[IPC_NAC]
    div, nac = div.loc[:mes], nac.loc[:mes]

    w_vig = pond.loc[div.columns, "pond_ipc_vigente"]
    w_new = pond.loc[div.columns, "pond_engho_2017_18"]
    w_vig, w_new = w_vig / w_vig.sum(), w_new / w_new.sum()

    # Control: con las ponderaciones vigentes (precios de dic-2016) se tiene que
    # reproducir el nivel general oficial.
    control = (div.div(div.loc["2016-12-01"]) * w_vig).sum(axis=1) * 100
    # Reponderado: canasta de la ENGHo 2017/18 valuada a los precios de cada mes.
    precios_encuesta = div.loc[ENCUESTA[0]:ENCUESTA[1]].mean()
    rep = (div.div(precios_encuesta) * w_new).sum(axis=1)
    rep = rep / rep.iloc[0] * 100
    # Agregar por divisiones nacionales no reproduce exacto el nivel general (el INDEC
    # agrega por regiones). Para no arrastrar ese desvío, se aplica al índice oficial
    # solo el efecto del cambio de ponderaciones: oficial × (reponderado / control).
    rep = nac * rep / control

    def v(s, a, b):
        return r((s[b] / s[a] - 1) * 100, 1)

    err = (control[mes] / control[inicio]) / (nac[mes] / nac[inicio]) - 1
    print(f"   control reponderación: con las ponderaciones vigentes la acumulada da "
          f"{v(control, inicio, mes)}% vs. {v(nac, inicio, mes)}% oficial ({err * 100:+.2f}%)")
    dic = pd.Timestamp(mes.year - 1, 12, 1)
    resumen = {
        "mensual": {"oficial": v(nac, mes - un_mes, mes), "reponderado": v(rep, mes - un_mes, mes)},
        "interanual": {"oficial": v(nac, mes - un_anio, mes), "reponderado": v(rep, mes - un_anio, mes)},
        "acum_anio": {"oficial": v(nac, dic, mes), "reponderado": v(rep, dic, mes)},
        "acum_gobierno": {"oficial": v(nac, inicio, mes), "reponderado": v(rep, inicio, mes)},
    }
    anios = {str(a): {"oficial": v(nac, pd.Timestamp(a - 1, 12, 1), pd.Timestamp(a, 12, 1)),
                      "reponderado": v(rep, pd.Timestamp(a - 1, 12, 1), pd.Timestamp(a, 12, 1))}
             for a in range(2017, mes.year) if pd.Timestamp(a, 12, 1) <= mes}
    print(f"   reponderado: acumulada {resumen['acum_gobierno']['reponderado']}% vs. "
          f"{resumen['acum_gobierno']['oficial']}% oficial · 2024: {anios.get('2024')}")
    serie = [{"fecha": ym(f),
              "oficial": {"mensual": v(nac, f - un_mes, f), "interanual": v(nac, f - un_anio, f), "acumulada": v(nac, inicio, f)},
              "reponderado": {"mensual": v(rep, f - un_mes, f), "interanual": v(rep, f - un_anio, f), "acumulada": v(rep, inicio, f)}}
             for f in rep.index if f > inicio]
    # Las mismas cuentas que publicaron otros, con esta estimación
    otras = []
    for _, e in pd.read_csv(RAIZ / "fuentes" / "estimaciones_reponderadas.csv").iterrows():
        a, b = pd.Timestamp(e["desde"] + "-01"), pd.Timestamp(e["hasta"] + "-01")
        dec = 2 if e["tipo"] == "mensual" else 1
        propia = r((rep[b] / rep[a] - 1) * 100, dec) if a in rep.index and b in rep.index else None
        oficial_aca = r((nac[b] / nac[a] - 1) * 100, dec) if a in nac.index and b in nac.index else None
        otras.append({k: (None if pd.isna(e[k]) else e[k]) for k in e.index} |
                     {"mecopol": propia, "oficial_mecopol": oficial_aca})
    return {
        "resumen": resumen,
        "anios": anios,
        "otras": otras,
        "serie": serie,
        "ponderaciones": [{"rubro": n, "vigente": r(w_vig[n] * 100, 1), "engho_2017_18": r(w_new[n] * 100, 1)}
                          for n in div.columns],
        "control_error_pct": r(err * 100, 2),
        "periodo_encuesta": [ym(pd.Timestamp(ENCUESTA[0])), ym(pd.Timestamp(ENCUESTA[1]))],
    }


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

    # 3. IPC reponderado con la ENGHo 2017/18 (estimación propia) --------
    # El IPC oficial pondera los rubros con la encuesta de gastos 2004/05
    # (actualizada por precios a dic-2016). Acá se recalcula con la canasta de
    # la ENGHo 2017/18: costo de esa canasta fija en cada mes, por divisiones.
    reponderado = reponderar(ids_div, nac, inicio, mes)

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
        "reponderado": reponderado,
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
