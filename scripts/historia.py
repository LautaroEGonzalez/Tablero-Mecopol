"""
MECOPOL · Mirada larga — inflación por gobierno, 2003 en adelante
================================================================

Arma la serie mensual de precios desde 2002 con los datos OFICIALES y
calcula la inflación de cada gobierno. Escribe docs/data/historia.json.

Serie principal (oficial):
  2002 a dic-2006      INDEC, IPC GBA histórico (API de Series de Tiempo)
  ene-2007 a dic-2013  INDEC, IPC GBA base abril 2008 (API de Series de Tiempo)
  ene-2014 a oct-2015  INDEC, IPC Nacional urbano, IPCNu (fuentes/indec_ipcnu_2014_2015.csv)
  nov-2015 a abr-2016  sin IPC del INDEC: IPC de la Ciudad de Buenos Aires
                       (fuentes/ipc_2015_2016_sin_indice_nacional.csv)
  may-2016 a dic-2016  INDEC, IPC GBA base abril 2016 (mismo archivo)
  desde ene-2017       INDEC, IPC Nacional (API de Series de Tiempo)

Serie alternativa, para comparar: igual a la oficial salvo de feb-2007 a
dic-2016, donde se usa el IPC Provincias de CIFRA-CTA
(fuentes/ipc_provincias_cifra.csv). Ver fuentes/LEEME.md.

Se encadenan las VARIACIONES MENSUALES de cada fuente, así que las
distintas bases de los índices no importan.
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
HUECO = RAIZ / "fuentes" / "ipc_2015_2016_sin_indice_nacional.csv"  # nov-2015 a dic-2016
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
ALT_DESDE = pd.Timestamp("2007-02-01")   # la serie de CIFRA arranca en ene-2007: su primera variación es feb-2007
ALT_HASTA = pd.Timestamp("2016-12-01")


def serie_api(sid, desde, hasta):
    j = pedir(API, {"ids": sid, "start_date": desde, "end_date": hasta, "limit": 1000})
    s = pd.Series({pd.Timestamp(f): v for f, v in j["data"]}, dtype="float64").dropna().sort_index()
    if s.empty:
        raise RuntimeError(f"La serie {sid} vino vacía")
    return s


def indice(var):
    """Índice 100 en el mes anterior a la primera variación."""
    idx = (1 + var).cumprod()
    idx.loc[var.index[0] - pd.DateOffset(months=1)] = 1.0
    return idx.sort_index() * 100


def main():
    hoy = pd.Timestamp.today().normalize()

    # 1. Fuentes ----------------------------------------------------------
    print("📥 INDEC IPC GBA histórico")
    gba = serie_api(IPC_GBA_HISTORICO, "2001-12-01", "2007-01-01")
    print("📥 INDEC IPC GBA base abril 2008")
    gba08 = serie_api(IPC_GBA_2008, "2006-01-01", "2013-12-01")
    print("📥 INDEC IPC Nacional")
    nac = serie_api(IPC_NAC, "2016-12-01", hoy.strftime("%Y-%m-%d"))
    print("📥 IPCNu 2014-2015 y nov-2015 a dic-2016 (archivos locales)")
    ipcnu = pd.read_csv(IPCNU, parse_dates=["fecha"]).set_index("fecha")["variacion_mensual"].astype(float) / 100
    hueco = pd.read_csv(HUECO, parse_dates=["fecha"]).set_index("fecha")
    print("📥 CIFRA-CTA IPC Provincias (archivo local, serie alternativa)")
    cif = pd.read_csv(CIFRA, parse_dates=["fecha"]).set_index("fecha")["indice"].astype(float).sort_index()

    for nombre, s, a, b in [("INDEC histórico", gba, "2002-01-01", "2007-01-01"),
                            ("IPC GBA 2008", gba08, "2006-12-01", "2013-12-01"),
                            ("IPCNu", ipcnu, "2014-01-01", "2015-10-01"),
                            ("nov-2015 a dic-2016", hueco, "2015-11-01", "2016-12-01"),
                            ("CIFRA", cif, "2007-01-01", "2016-12-01")]:
        faltan = pd.date_range(a, b, freq="MS").difference(s.index)
        if len(faltan):
            raise RuntimeError(f"A {nombre} le faltan meses: {[ym(f) for f in faltan[:6]]}")

    # Control: con el IPC GBA del INDEC, 2005 dio 12,3% (dic a dic). Si no da, la serie no es la correcta.
    control = (gba[pd.Timestamp("2005-12-01")] / gba[pd.Timestamp("2004-12-01")] - 1) * 100
    if not 11.5 < control < 13.0:
        raise RuntimeError(f"La serie {IPC_GBA_HISTORICO} da {control:.1f}% en 2005 (esperado 12,3%). "
                           "Revisar config.json → historia.id_ipc_historico")

    # 2. Serie oficial, encadenando variaciones mensuales -------------------
    tramos = [  # (variaciones, serie, organismo)
        (gba.pct_change().loc["2002-01-01":"2006-12-01"], "IPC GBA", "INDEC"),
        (gba08.pct_change().loc["2007-01-01":"2013-12-01"], "IPC GBA", "INDEC"),
        (ipcnu.loc["2014-01-01":"2015-10-01"], "IPCNu (nacional urbano)", "INDEC"),
    ]
    for serie_h, g in hueco.groupby("serie", sort=False):
        org = "INDEC" if serie_h.startswith("INDEC") else "Estadística CABA"
        tramos.append((g["variacion_mensual"].astype(float) / 100, serie_h.replace("INDEC ", ""), org))
    tramos.append((nac.pct_change().loc["2017-01-01":], "IPC Nacional", "INDEC"))
    var = pd.concat([t[0] for t in tramos]).dropna().sort_index()
    serie_de = pd.concat([pd.Series(t[1], index=t[0].index) for t in tramos])
    org_de = pd.concat([pd.Series(t[2], index=t[0].index) for t in tramos])
    if var.index.duplicated().any() or len(pd.date_range(var.index[0], var.index[-1], freq="MS")) != len(var):
        raise RuntimeError("La serie oficial encadenada tiene huecos o meses repetidos")
    idx = indice(var)
    ultimo = idx.index.max()
    print(f"   serie oficial {ym(idx.index.min())} → {ym(ultimo)} ({len(idx)} meses)")

    # Control: año por año tiene que dar lo que publicó el INDEC (2007-2014, años completos).
    oficial_pub = pd.read_csv(OFICIAL).set_index("anio")
    for anio in range(2007, 2015):
        calc = (idx[pd.Timestamp(anio, 12, 1)] / idx[pd.Timestamp(anio - 1, 12, 1)] - 1) * 100
        if abs(calc - oficial_pub.loc[anio, "variacion"]) > 0.35:
            raise RuntimeError(f"La serie oficial mensual da {calc:.1f}% en {anio} y el INDEC publicó "
                               f"{oficial_pub.loc[anio, 'variacion']}%. Revisar {IPC_GBA_2008} o {IPCNU.name}")

    # 3. Serie alternativa: CIFRA-CTA de feb-2007 a dic-2016 ----------------
    var_alt = var.copy()
    v_cif = cif.pct_change().loc[ALT_DESDE:ALT_HASTA]
    var_alt.loc[v_cif.index] = v_cif
    alt = indice(var_alt)

    def interanual(f, s):
        a = f - pd.DateOffset(months=12)
        return (s[f] / s[a] - 1) * 100 if f in s.index and a in s.index else None

    # 4. Serie mensual para el gráfico: oficial y CIFRA-CTA por separado ----
    serie = []
    for f in idx.index:
        if f < pd.Timestamp("2003-01-01"):
            continue
        serie.append({"fecha": ym(f), "mensual": r(var[f] * 100), "interanual": r(interanual(f, idx), 1),
                      "serie": serie_de[f], "organismo": org_de[f],
                      "cifra": r(interanual(f, cif), 1) if f in cif.index else None})

    # 5. Inflación anual (dic a dic) ---------------------------------------
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

    anual = []
    for anio in range(2003, ultimo.year + 1):
        dic_ant, fin = pd.Timestamp(anio - 1, 12, 1), min(pd.Timestamp(anio, 12, 1), ultimo)
        meses_anio = var.loc[pd.Timestamp(anio, 1, 1):fin]
        fila = {"anio": anio, "variacion": r((idx[fin] / idx[dic_ant] - 1) * 100, 1),
                "meses": fin.month, "parcial": fin < pd.Timestamp(anio, 12, 1), "hasta": ym(fin),
                "gobierno": dueño(anio),
                "series": list(dict.fromkeys(f"{org_de[m]} {serie_de[m]}" for m in meses_anio.index))}
        if pd.Timestamp(anio, 1, 1) <= ALT_HASTA and fin >= ALT_DESDE:
            fila["alternativa"] = {"variacion": r((alt[fin] / alt[dic_ant] - 1) * 100, 1), "fuente": "CIFRA-CTA, IPC Provincias"}
        if anio in oficial_pub.index:
            o = oficial_pub.loc[anio]
            fila["publicado"] = {"variacion": float(o["variacion"]), "meses": int(o["meses"]),
                                 "nota": o["nota"], "fuente": o["fuente"]}
        anual.append(fila)

    # 6. Métricas por gobierno ---------------------------------------------
    def metricas(s, v, base, fin):
        n = (fin.year - base.year) * 12 + (fin.month - base.month)
        acum = (s[fin] / s[base] - 1) * 100
        mens = v.loc[base + pd.DateOffset(months=1):fin] * 100
        tramo = s.loc[base:fin]
        return n, acum, mens, tramo

    gobiernos = []
    for g in GOBIERNOS:
        base = pd.Timestamp(g["base"] + "-01")
        fin = min(pd.Timestamp(g["fin"] + "-01"), ultimo)
        n, acum, mens, tramo = metricas(idx, var, base, fin)
        fila = {
            **{k: g[k] for k in ("id", "nombre", "corto", "color")},
            "base": g["base"], "fin": ym(fin), "en_curso": fin < pd.Timestamp(g["fin"] + "-01"),
            "meses": n,
            "acumulada": r(acum, 1),
            "promedio_anual": r(((1 + acum / 100) ** (12 / n) - 1) * 100, 1),
            "promedio_mensual": r(((1 + acum / 100) ** (1 / n) - 1) * 100, 2),
            "heredada": r(interanual(base, idx), 1),
            "entregada": r(interanual(fin, idx), 1),
            "mes_max": {"fecha": ym(mens.idxmax()), "valor": r(mens.max(), 1)},
            "mes_min": {"fecha": ym(mens.idxmin()), "valor": r(mens.min(), 1)},
            "trayectoria": [r((v / tramo.iloc[0] - 1) * 100, 1) for v in tramo.values],
            "series": list(dict.fromkeys(f"{org_de[m]} {serie_de[m]}" for m in mens.index)),
        }
        if base <= ALT_HASTA and fin >= ALT_DESDE:
            _, acum_a, _, _ = metricas(alt, var_alt, base, fin)
            fila["alternativa"] = {"acumulada": r(acum_a, 1),
                                   "promedio_anual": r(((1 + acum_a / 100) ** (12 / n) - 1) * 100, 1)}
        gobiernos.append(fila)

    # 7. Por años calendario, oficial y alternativa ------------------------
    def promedio(filas, clave):
        prod, meses = 1.0, 0
        for f in filas:
            src = f.get(clave) or f
            prod *= 1 + src["variacion"] / 100
            meses += f["meses"]
        return r((prod ** (12 / meses) - 1) * 100, 1) if meses else None

    calendario = []
    for g in GOBIERNOS:
        filas = [f for f in anual if f["gobierno"] == g["id"]]
        if not filas:
            continue
        calendario.append({"id": g["id"], "anios": f"{filas[0]['anio']}–{filas[-1]['anio']}",
                           "oficial": promedio(filas, "_"), "alternativa": promedio(filas, "alternativa"),
                           "difiere": any("alternativa" in f for f in filas)})

    empalme, previo = [], None
    for f in idx.index[1:]:
        clave = (org_de[f], serie_de[f])
        if clave != previo:
            empalme.append({"desde": ym(f), "hasta": ym(f), "fuente": clave[0], "serie": clave[1]})
            previo = clave
        else:
            empalme[-1]["hasta"] = ym(f)

    datos = {
        "actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "ultimo_mes": ym(ultimo),
        "serie": serie,
        "anual": anual,
        "gobiernos": gobiernos,
        "calendario": calendario,
        "empalme": empalme,
        "alternativa": {"fuente": "CIFRA-CTA", "serie": "IPC Provincias", "desde": ym(ALT_DESDE), "hasta": ym(ALT_HASTA)},
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
