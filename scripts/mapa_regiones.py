"""
Genera docs/geo/regiones_ipc.json: las 6 regiones del IPC del INDEC dibujadas a partir
de los departamentos del IGN (repo github.com/mgaitan/departamentos_argentina, SIG 250).
Se corre una sola vez, a mano:  pip install shapely  y  python scripts/mapa_regiones.py <departamentos-argentina.json>
"""
import sys
import json, unicodedata
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

norm = lambda s: unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().upper().strip()
GBA24 = ["ALMIRANTE BROWN","AVELLANEDA","BERAZATEGUI","ESTEBAN ECHEVERRIA","EZEIZA","FLORENCIO VARELA",
 "GENERAL SAN MARTIN","HURLINGHAM","ITUZAINGO","JOSE C PAZ","LA MATANZA","LANUS","LOMAS DE ZAMORA",
 "MALVINAS ARGENTINAS","MERLO","MORENO","MORON","QUILMES","SAN FERNANDO","SAN ISIDRO","SAN MIGUEL",
 "TIGRE","TRES DE FEBRERO","VICENTE LOPEZ"]
REG = {"Pampeana": ["BUENOS AIRES","CORDOBA","ENTRE RIOS","LA PAMPA","SANTA FE"],
       "Noreste": ["CHACO","CORRIENTES","FORMOSA","MISIONES"],
       "Noroeste": ["CATAMARCA","JUJUY","LA RIOJA","SALTA","SANTIAGO DEL ESTERO","TUCUMAN"],
       "Cuyo": ["MENDOZA","SAN JUAN","SAN LUIS"],
       "Patagonia": ["CHUBUT","NEUQUEN","RIO NEGRO","SANTA CRUZ","TIERRA DEL FUEGO"]}
d = json.load(open(sys.argv[1]))
geoms = {k: [] for k in ["GBA"] + list(REG)}
gba_found = set()
for f in d['features']:
    p = f['properties']; prov = norm(p['provincia']); dep = norm(p['departamento'])
    g = shape(f['geometry']).buffer(0)
    # En el archivo del IGN las etiquetas de estos dos departamentos vienen cruzadas:
    # "ISLAS MALVINAS" es el sector antártico y "ISLAS DEL ATLANTICO SUR" incluye Malvinas.
    # Se deja fuera la Antártida (va en un recuadro aparte en los mapas bicontinentales)
    # y de las islas del Atlántico Sur se conservan las Malvinas.
    if g.bounds[1] < -60:
        continue
    if dep == "ISLAS DEL ATLANTICO SUR":
        from shapely.geometry import MultiPolygon
        partes = g.geoms if g.geom_type == "MultiPolygon" else [g]
        g = MultiPolygon([p for p in partes if p.centroid.x < -56])
    if prov == "CIUDAD AUTONOMA DE BUENOS AIRES" or (prov == "BUENOS AIRES" and dep in [norm(x) for x in GBA24]):
        geoms["GBA"].append(g); gba_found.add(dep); continue
    for r, ps in REG.items():
        if prov in ps: geoms[r].append(g); break
    else:
        print("sin región:", prov, dep)
print("GBA partidos encontrados:", len(gba_found - {""}), sorted(set(norm(x) for x in GBA24) - gba_found))
feats = []
for r, gs in geoms.items():
    u = unary_union(gs).buffer(0.02).buffer(-0.02)   # cierra las rendijas entre departamentos
    u = u.simplify(0.004 if r == "GBA" else 0.03, preserve_topology=True)
    if r != "GBA":  # sacar islas diminutas
        if u.geom_type == "MultiPolygon":
            from shapely.geometry import MultiPolygon
            u = MultiPolygon([p for p in u.geoms if p.area > 0.002])
    m = mapping(u)
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 3), round(c[1], 3)]
    m = {"type": m["type"], "coordinates": rnd(m["coordinates"])}
    feats.append({"type": "Feature", "properties": {"name": r, "cx": round(u.centroid.x, 2), "cy": round(u.centroid.y, 2)}, "geometry": m})
    print(r, u.geom_type, round(u.area, 2), u.bounds)
out = {"type": "FeatureCollection", "features": feats}
json.dump(out, open('docs/geo/regiones_ipc.json', 'w'), separators=(',', ':'))
import os; print(os.path.getsize('docs/geo/regiones_ipc.json'))
