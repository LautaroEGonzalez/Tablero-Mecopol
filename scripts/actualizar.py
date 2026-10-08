"""
MECOPOL · Tablero de inflación — actualización de datos
=======================================================

Baja las series del IPC del INDEC desde la API de Series de Tiempo
(apis.datos.gob.ar), calcula todos los indicadores del tablero y los
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
FIN_MANDATO = 48                        # mes 48 = último mes completo de un mandato

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
def etiqueta(fecha):
    return f"{MESES_ES[fecha.month - 1]}-{str(fecha.year)[2:]}"


def meses_entre(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)


def r(x, n=2):
    """Redondea y convierte NaN en None (JSON válido)."""
    return None if x is None or pd.isna(x) else round(float(x), n)


# ------------------------------------------------------------------
# Cálculo
# ------------------------------------------------------------------
def main():
    hoy = pd.Timestamp.today().normalize()
    gobiernos = {g: pd.Timestamp(v["base"]) for g, v in CONFIG["gobiernos"].items()}

    # 1. Nivel general --------------------------------------------------
    print("📥 IPC nacional, nivel general")
    nac = traer([IPC_NAC], "2016-12-01", hoy.strftime("%Y-%m-%d"))[IPC_NAC].dropna()
    mes = nac.index.max()
    print(f"   último dato: {etiqueta(mes)} = {nac[mes]:,.2f}")

    var = nac.pct_change().dropna()
    empalme = CONFIG.get("empalme_macri") or []
    if len(empalme) == 13:
        previas = pd.Series(np.array(empalme, dtype=float) / 100,
                            index=pd.date_range("2015-12-01", "2016-12-01", freq="MS"))
        var = pd.concat([previas, var])
        print("   ✅ empalme 2016 cargado: Macri entra en la comparación")
    else:
        gobiernos.pop("Macri", None)
        print("   ℹ️ sin empalme 2016: Macri queda afuera")

    indice = (1 + var).cumprod()
    indice.loc[var.index[0] - pd.DateOffset(months=1)] = 1.0
    indice = indice.sort_index()

    def interanual(f):
        a = f - pd.DateOffset(months=12)
        if f in indice.index and a in indice.index:
            return (indice[f] / indice[a] - 1) * 100
        return np.nan

    K = meses_entre(gobiernos["Milei"], mes)

    # 2. KPIs del último mes -------------------------------------------
    previo = mes - pd.DateOffset(months=1)
    dic_ant = pd.Timestamp(year=mes.year - 1, month=12, day=1)
    kpis = {
        "mensual": r((nac[mes] / nac[previo] - 1) * 100),
        "mensual_previo": r((nac[previo] / nac[previo - pd.DateOffset(months=1)] - 1) * 100),
        "interanual": r(interanual(mes), 1),
        "interanual_previo": r(interanual(previo), 1),
        "acum_anio": r((nac[mes] / nac[dic_ant] - 1) * 100, 1),
        "acum_gobierno": r((indice[mes] / indice[gobiernos["Milei"]] - 1) * 100, 1),
        "nivel": r(nac[mes]),
    }

    serie = [{"fecha": f.strftime("%Y-%m"),
              "mensual": r((nac[f] / nac[f - pd.DateOffset(months=1)] - 1) * 100),
              "interanual": r(interanual(f), 1)}
             for f in nac.index[1:]]

    # 3. Trayectorias por mes de gobierno ------------------------------
    tray = {}
    for g, b in gobiernos.items():
        fechas = pd.date_range(b, b + pd.DateOffset(months=FIN_MANDATO), freq="MS")
        acum = (indice.reindex(fechas) / indice[b] - 1) * 100
        tray[g] = [r(v, 1) for v in acum.values]

    misma_altura = []
    for g, b in gobiernos.items():
        t = b + pd.DateOffset(months=K)
        acum = tray[g][K]
        misma_altura.append({
            "gobierno": g, "mes": etiqueta(t), "acumulada": acum,
            "promedio_mensual": r(((1 + acum / 100) ** (1 / K) - 1) * 100),
            "interanual_al_asumir": r(interanual(b), 1),
            "interanual_misma_altura": r(interanual(t), 1),
        })

    # 4. Rubros: precios relativos y mes actual ------------------------
    ids_div = {}
    for nombre, clave in DIVISIONES.items():
        fid = CONFIG.get("ids_divisiones", {}).get(nombre) or buscar_division(nombre, clave)
        print(f"   {'✅' if fid else '❌'} {nombre}: {fid}")
        if fid:
            ids_div[nombre] = fid
    if len(ids_div) < len(DIVISIONES):
        faltan = sorted(set(DIVISIONES) - set(ids_div))
        raise RuntimeError(f"Faltan rubros: {faltan}. Cargar sus ids en config.json → ids_divisiones")

    div = traer(list(ids_div.values()), "2019-10-01", mes.strftime("%Y-%m-%d"))
    div.columns = list(ids_div)

    relativos = {"rubros": list(div.columns)}
    for g in ["Fernández", "Milei"]:
        b = gobiernos[g]
        t = b + pd.DateOffset(months=K)
        rel = ((div.loc[t] / div.loc[b]) / (nac[t] / nac[b]) - 1) * 100
        relativos[g] = [r(v, 1) for v in rel.values]

    rubros_mes = [{"rubro": n,
                   "mensual": r((div.loc[mes, n] / div.loc[previo, n] - 1) * 100),
                   "interanual": r((div.loc[mes, n] / div.loc[mes - pd.DateOffset(months=12), n] - 1) * 100, 1)}
                  for n in div.columns]

    # 5. Escenarios hasta el fin del mandato ---------------------------
    rem = CONFIG["rem"]
    rem_2027 = ((1 + rem["anual_2027"] / 100) ** (1 / 12) - 1) * 100
    escenarios_def = {
        "Desinflación rápida (1%)": lambda f: 1.0,
        "Consenso REM": lambda f: rem["mensual"].get(f.strftime("%Y-%m"), rem_2027),
        "Se estanca en 2%": lambda f: 2.0,
        "Shock electoral": lambda f: ({8: 4.0, 9: 6.0, 10: 4.0, 11: 3.0}[f.month]
                                      if f.year == 2027 and f.month >= 8 else 2.0),
    }
    futuras = pd.date_range(mes + pd.DateOffset(months=1), periods=FIN_MANDATO - K, freq="MS")
    nivel_hoy = 1 + tray["Milei"][K] / 100
    escenarios, fin_mandato = {}, []
    for g in gobiernos:
        if g != "Milei":
            fin = gobiernos[g] + pd.DateOffset(months=FIN_MANDATO)
            fin_mandato.append({"caso": f"{g} (real)", "gobierno": g,
                                "acumulada": tray[g][FIN_MANDATO],
                                "interanual_final": r(interanual(fin), 1)})
    for nombre, regla in escenarios_def.items():
        tasas = np.array([regla(f) for f in futuras]) / 100
        camino = np.r_[nivel_hoy, nivel_hoy * np.cumprod(1 + tasas)]
        acum = (camino - 1) * 100
        escenarios[nombre] = [r(v, 1) for v in acum]
        completo = tray["Milei"][:K] + list(acum)
        fin_mandato.append({
            "caso": f"Milei · {nombre}", "gobierno": "Milei",
            "acumulada": r(completo[FIN_MANDATO], 1),
            "interanual_final": r(((1 + completo[FIN_MANDATO] / 100) /
                                   (1 + completo[FIN_MANDATO - 12] / 100) - 1) * 100, 1),
        })

    primeros5 = tray["Milei"][5]
    resto = ((1 + tray["Milei"][K] / 100) / (1 + primeros5 / 100) - 1) * 100

    # 6. Controles de calidad -------------------------------------------
    assert 0 < len(serie) and kpis["mensual"] is not None, "Serie vacía"
    assert all(v is not None for v in relativos["Milei"]), "Precios relativos incompletos"
    assert abs(tray["Milei"][0]) < 1e-9, "La trayectoria no arranca en 0"

    datos = {
        "actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "ultimo_mes": mes.strftime("%Y-%m"),
        "ultimo_mes_etiqueta": etiqueta(mes),
        "mes_gobierno": K,
        "fin_mandato": FIN_MANDATO,
        "kpis": kpis,
        "serie_mensual": serie,
        "gobiernos": {g: {"base": etiqueta(b), "color": CONFIG["gobiernos"][g]["color"]}
                      for g, b in gobiernos.items()},
        "trayectorias": tray,
        "misma_altura": misma_altura,
        "precios_relativos": relativos,
        "rubros_mes": rubros_mes,
        "escenarios": {"desde_mes": K, "series": escenarios, "rem_publicado": rem["publicado"]},
        "cierre_mandato": fin_mandato,
        "milei_tramos": {"primeros_5": r(primeros5, 1), "resto": r(resto, 1), "meses_resto": K - 5},
        "fuentes": {"nivel_general": IPC_NAC, "divisiones": ids_div},
    }

    # Si los números no cambiaron, no se reescribe el archivo: así la Action
    # no genera un commit por día y la fecha muestra el último cambio real.
    if SALIDA.exists():
        previo = json.loads(SALIDA.read_text(encoding="utf-8"))
        sin_fecha = lambda x: {k: v for k, v in x.items() if k != "actualizado"}
        if sin_fecha(previo) == json.loads(json.dumps(sin_fecha(datos), ensure_ascii=False)):
            print(f"✔️ Sin datos nuevos (último mes: {etiqueta(mes)}).")
            return

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"💾 {SALIDA.relative_to(RAIZ)} · {etiqueta(mes)} · mes {K} de Milei · "
          f"mensual {kpis['mensual']}% · interanual {kpis['interanual']}%")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"⛔ {e}")
        sys.exit(1)
