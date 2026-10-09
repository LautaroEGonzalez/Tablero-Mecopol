"""
MECOPOL · Mirada larga — inflación por gobierno, 2003 en adelante
================================================================

Arma una serie mensual de precios desde 2002 encadenando tres fuentes,
y calcula la inflación de cada gobierno. Escribe docs/data/historia.json.

  hasta ene-2007   INDEC, IPC GBA histórico (API de Series de Tiempo)
  feb-2007 a 2016  CIFRA-CTA, IPC Provincias (fuentes/ipc_provincias_cifra.csv)
  desde ene-2017   INDEC, IPC Nacional (API de Series de Tiempo)

Por qué CIFRA entre 2007 y 2016: el IPC del INDEC de esos años está
muy inferior a los índices provinciales (2007-2015) o no existe con
cobertura nacional (2016). El
IPC Provincias promedia los índices de diez provincias con ponderaciones
de la ENGHo. La serie de CIFRA empieza en enero de 2007, así que la
variación de ese mes sale del INDEC. Ver fuentes/LEEME.md.

Se encadenan las VARIACIONES MENSUALES de cada fuente, así que las
distintas bases de los índices no importan.

Además se guardan, mes a mes, los dos interanuales por separado para
compararlos en todo el período: el que publicó el INDEC (IPC GBA, IPCNu
e IPC Nacional) y el de CIFRA-CTA (2008-2018).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from actualizar import pedir, API, IPC_NAC, etiqueta, ym, r  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "docs" / "data" / "historia.json"
CIFRA = RAIZ / "fuentes" / "ipc_provincias_cifra.csv"
OFICIAL = RAIZ / "fuentes" / "indec_oficial_2007_2015.csv"   # lo que publicó el INDEC en esos años
IPCNU = RAIZ / "fuentes" / "indec_ipcnu_2014_2015.csv"         # IPC Nacional urbano, ene-2014 a oct-2015
CONFIG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
HIST = CONFIG.get("historia", {})

IPC_GBA_HISTORICO = HIST.get("id_ipc_historico", "178.1_NL_GENERAL_0_0_13")
IPC_GBA_2008 = HIST.get("id_ipc_gba_2008", "96.3_ING_2008_M_19")   # IPC GBA base abril 2008, hasta dic-2013

# base = último mes completo del gobierno anterior; fin = último mes completo propio
GOBIERNOS = HIST.get("gobiernos") or [
    {"id": "nk",    "nombre": "Néstor Kirchner",       "corto": "Kirchner",  "base": "2003-04", "fin": "2007-11", "color": "#199e70"},
    {"id": "cfk1",  "nombre": "Cristina Fernández I",  "corto": "CFK I",     "base": "2007-11", "fin": "2011-11", "color": "#d95926"},
    {"id": "cfk2",  "nombre": "Cristina Fernández II", "corto": "CFK II",    "base": "2011-11", "fin": "2015-11", "color": "#9085e9"},
    {"id": "macri", "nombre": "Mauricio Macri",        "corto": "Macri",     "base": "2015-11", "fin": "2019-11", "color": "#c98500"},
    {"id": "af",    "nombre": "Alberto Fernández",     "corto": "Fernández", "base": "2019-11", "fin": "2023-11", "color": "#3987e5"},
    {"id": "milei", "nombre": "Javier Milei",          "corto": "Milei",     "base": "2023-11", "fin": "2027-11", "color": "#d55181"},
]
CORTE_1 = pd.Timestamp("2007-01-01")   # último mes INDEC histórico (CIFRA arranca en ene-2007)
CORTE_2 = pd.Timestamp("2016-12-01")   # último mes CIFRA


def serie_api(sid, desde, hasta):
    j = pedir(API, {"ids": sid, "start_date": desde, "end_date": hasta, "limit": 1000})
    s = pd.Series({pd.Timestamp(f): v for f, v in j["data"]}, dtype="float64").dropna().sort_index()
    if s.empty:
        raise RuntimeError(f"La serie {sid} vino vacía")
    return s


def main():
    hoy = pd.Timestamp.today().normalize()

    # 1. Fuentes ----------------------------------------------------------
    print("📥 INDEC IPC GBA histórico")
    gba = serie_api(IPC_GBA_HISTORICO, "2001-12-01", "2007-01-01")
    print("📥 CIFRA-CTA IPC Provincias (archivo local)")
    cif = pd.read_csv(CIFRA, parse_dates=["fecha"]).set_index("fecha")["indice"].astype(float).sort_index()
    print("📥 INDEC IPC Nacional")
    nac = serie_api(IPC_NAC, "2016-12-01", hoy.strftime("%Y-%m-%d"))
    print("📥 INDEC IPC GBA base abril 2008 e IPCNu (serie oficial 2007-2015)")
    gba08 = serie_api(IPC_GBA_2008, "2006-01-01", "2013-12-01")
    ipcnu = pd.read_csv(IPCNU, parse_dates=["fecha"]).set_index("fecha")["variacion_mensual"].astype(float) / 100

    for nombre, s, a, b in [("INDEC histórico", gba, "2002-01-01", "2007-01-01"),
                            ("CIFRA", cif, "2007-01-01", "2016-12-01")]:
        faltan = pd.date_range(a, b, freq="MS").difference(s.index)
        if len(faltan):
            raise RuntimeError(f"A {nombre} le faltan meses: {[ym(f) for f in faltan[:6]]}")

    # Control: con el IPC GBA del INDEC, 2005 dio 12,3% (dic a dic). Si no da, la serie no es la correcta.
    control = (gba[pd.Timestamp("2005-12-01")] / gba[pd.Timestamp("2004-12-01")] - 1) * 100
    if not 11.5 < control < 13.0:
        raise RuntimeError(f"La serie {IPC_GBA_HISTORICO} da {control:.1f}% en 2005 (esperado 12,3%). "
                           "Revisar config.json → historia.id_ipc_historico")

    # 2. Variaciones mensuales encadenadas --------------------------------
    v_gba = gba.pct_change().loc["2002-01-01":CORTE_1]
    v_cif = cif.pct_change().loc[CORTE_1 + pd.DateOffset(months=1):CORTE_2]
    v_nac = nac.pct_change().loc[CORTE_2 + pd.DateOffset(months=1):]
    var = pd.concat([v_gba, v_cif, v_nac]).dropna()
    fuente = pd.Series("INDEC (GBA)", index=v_gba.index)
    fuente = pd.concat([fuente, pd.Series("CIFRA-CTA", index=v_cif.index),
                        pd.Series("INDEC (Nacional)", index=v_nac.index)])
    meses = pd.date_range(var.index[0], var.index[-1], freq="MS")
    if len(meses) != len(var):
        raise RuntimeError("La serie encadenada tiene huecos")

    idx = (1 + var).cumprod()
    idx.loc[var.index[0] - pd.DateOffset(months=1)] = 1.0
    idx = idx.sort_index() * 100
    ultimo = idx.index.max()
    print(f"   serie {ym(idx.index.min())} → {ym(ultimo)} ({len(idx)} meses)")

    def interanual(f, s=None):
        s = idx if s is None else s
        a = f - pd.DateOffset(months=12)
        return (s[f] / s[a] - 1) * 100 if f in s.index and a in s.index else None

    # 2b. Las dos mediciones por separado, para el gráfico de dos líneas ---
    # INDEC: lo que publicó el organismo. GBA hasta 2013, IPCNu 2014-oct 2015,
    # sin índice nacional hasta dic-2016 (no hay interanual hasta dic-2017).
    v_ofi = pd.concat([gba.pct_change().loc["2002-01-01":"2006-12-01"],
                       gba08.pct_change().loc["2007-01-01":"2013-12-01"],
                       ipcnu.loc["2014-01-01":"2015-10-01"]])
    ofi = (1 + v_ofi).cumprod() * 100
    ofi.loc[pd.Timestamp("2001-12-01")] = 100.0
    ofi = ofi.sort_index()
    oficial_anual = pd.read_csv(OFICIAL).set_index("anio")
    for anio in range(2007, 2015):
        calc = (ofi[pd.Timestamp(anio, 12, 1)] / ofi[pd.Timestamp(anio - 1, 12, 1)] - 1) * 100
        if abs(calc - oficial_anual.loc[anio, "variacion"]) > 0.35:
            raise RuntimeError(f"La serie oficial mensual da {calc:.1f}% en {anio} y el INDEC publicó "
                               f"{oficial_anual.loc[anio, 'variacion']}%. Revisar {IPC_GBA_2008} o {IPCNU.name}")
    nac_i = nac / nac.iloc[0]
    tramo_ofi = lambda f: ("IPC GBA" if f < pd.Timestamp("2014-01-01") else
                           "IPCNu (nacional urbano)" if f <= pd.Timestamp("2015-10-01") else "IPC Nacional")
    ia_indec = {f: (interanual(f, ofi), tramo_ofi(f)) for f in ofi.index}
    ia_indec.update({f: (interanual(f, nac_i), "IPC Nacional") for f in nac_i.index})
    ia_cifra = {f: interanual(f, cif) for f in cif.index}

    # 3. Serie mensual para el gráfico -------------------------------------
    serie = []
    for f in idx.index:
        if f < pd.Timestamp("2003-01-01"):
            continue
        ind, tr = ia_indec.get(f, (None, None))
        serie.append({"fecha": ym(f), "mensual": r(var[f] * 100), "interanual": r(interanual(f), 1), "fuente": fuente[f],
                      "indec": r(ind, 1), "indec_serie": tr if ind is not None else None, "cifra": r(ia_cifra.get(f), 1)})

    # 4. Inflación anual (dic a dic) ---------------------------------------
    def dueño(anio):
        # el gobierno que gobernó la mayor parte de ese año calendario
        mejor, n = None, 0
        for g in GOBIERNOS:
            ini = pd.Timestamp(g["base"] + "-01") + pd.DateOffset(months=1)
            fin = pd.Timestamp(g["fin"] + "-01")
            k = sum(1 for m in range(1, 13) if ini <= pd.Timestamp(anio, m, 1) <= fin)
            if k > n:
                mejor, n = g["id"], k
        return mejor

    oficial = oficial_anual
    anual = []
    for anio in range(2003, ultimo.year + 1):
        dic_ant, fin = pd.Timestamp(anio - 1, 12, 1), min(pd.Timestamp(anio, 12, 1), ultimo)
        fila = {"anio": anio, "variacion": r((idx[fin] / idx[dic_ant] - 1) * 100, 1),
                "meses": fin.month, "parcial": fin < pd.Timestamp(anio, 12, 1), "hasta": ym(fin),
                "gobierno": dueño(anio), "fuente": fuente[fin]}
        if anio in oficial.index:
            o = oficial.loc[anio]
            fila["oficial"] = {"variacion": float(o["variacion"]), "meses": int(o["meses"]),
                               "nota": o["nota"], "fuente": o["fuente"]}
        anual.append(fila)

    # Comparación por años calendario: misma cuenta con las dos series.
    # En los años sin dato oficial distinto (antes de 2007 y desde 2016) se usa la misma cifra.
    def promedio(filas, clave):
        prod, meses = 1.0, 0
        for f in filas:
            src = f.get("oficial") if clave == "oficial" and f.get("oficial") else f
            prod *= 1 + src["variacion"] / 100
            meses += src["meses"]
        return r((prod ** (12 / meses) - 1) * 100, 1) if meses else None

    calendario = []
    for g in GOBIERNOS:
        filas = [f for f in anual if f["gobierno"] == g["id"]]
        if not filas:
            continue
        alt, ofi = promedio(filas, "variacion"), promedio(filas, "oficial")
        calendario.append({"id": g["id"], "anios": f"{filas[0]['anio']}–{filas[-1]['anio']}",
                           "alternativa": alt, "oficial": ofi,
                           "difiere": any("oficial" in f for f in filas)})

    # 5. Métricas por gobierno ---------------------------------------------
    gobiernos = []
    for g in GOBIERNOS:
        base = pd.Timestamp(g["base"] + "-01")
        fin = min(pd.Timestamp(g["fin"] + "-01"), ultimo)
        n = (fin.year - base.year) * 12 + (fin.month - base.month)
        acum = (idx[fin] / idx[base] - 1) * 100
        tramo = idx.loc[base:fin]
        mens = var.loc[base + pd.DateOffset(months=1):fin] * 100
        gobiernos.append({
            **{k: g[k] for k in ("id", "nombre", "corto", "color")},
            "base": g["base"], "fin": ym(fin), "en_curso": fin < pd.Timestamp(g["fin"] + "-01"),
            "meses": n,
            "acumulada": r(acum, 1),
            "promedio_anual": r(((1 + acum / 100) ** (12 / n) - 1) * 100, 1),
            "promedio_mensual": r(((1 + acum / 100) ** (1 / n) - 1) * 100, 2),
            "heredada": r(interanual(base), 1),
            "entregada": r(interanual(fin), 1),
            "mes_max": {"fecha": ym(mens.idxmax()), "valor": r(mens.max(), 1)},
            "mes_min": {"fecha": ym(mens.idxmin()), "valor": r(mens.min(), 1)},
            "trayectoria": [r((v / tramo.iloc[0] - 1) * 100, 1) for v in tramo.values],
        })

    datos = {
        "actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "ultimo_mes": ym(ultimo),
        "serie": serie,
        "anual": anual,
        "gobiernos": gobiernos,
        "calendario": calendario,
        "lineas": {
            "indec": "INDEC: IPC GBA hasta dic-2013, IPC Nacional urbano (IPCNu) de ene-2014 a oct-2015 e IPC Nacional desde dic-2016. "
                     "Entre nov-2015 y nov-2017 no hay interanual oficial nacional.",
            "cifra": "CIFRA-CTA: IPC Provincias, ene-2007 a dic-2018 (el interanual arranca en ene-2008).",
        },
        "empalme": [
            {"desde": "2002-01", "hasta": ym(CORTE_1), "fuente": "INDEC", "serie": f"IPC GBA histórico ({IPC_GBA_HISTORICO})"},
            {"desde": ym(CORTE_1 + pd.DateOffset(months=1)), "hasta": ym(CORTE_2), "fuente": "CIFRA-CTA", "serie": "IPC Provincias"},
            {"desde": ym(CORTE_2 + pd.DateOffset(months=1)), "hasta": ym(ultimo), "fuente": "INDEC", "serie": f"IPC Nacional ({IPC_NAC})"},
        ],
    }

    if SALIDA.exists():
        previo = json.loads(SALIDA.read_text(encoding="utf-8"))
        sin = lambda x: {k: v for k, v in x.items() if k != "actualizado"}
        if sin(previo) == json.loads(json.dumps(sin(datos), ensure_ascii=False)):
            print("✔️ Sin cambios en la serie histórica.")
            return
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    resumen = " · ".join(f"{g['corto']} {g['promedio_anual']}%/año" for g in gobiernos)
    print(f"💾 {SALIDA.relative_to(RAIZ)} · {resumen}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"⛔ {e}")
        sys.exit(1)
