"""Isobars and saturation domes for the T-v plots of the new states."""
import json, sys
import numpy as np
import CoolProp.CoolProp as CP
CP.set_reference_state("R134a", "ASHRAE")

states = json.load(open("states2_final.json"))
old_keys = set(json.load(open(sys.argv[1])) if len(sys.argv) > 1 else [])

def v_at(f, P, T):
    return 1 / CP.PropsSI("D", "T", T + 273.15, "P", P * 1e3, f)

def isobar(f, P, Tlo, Thi, n=44):
    Ts = CP.PropsSI("T", "P", P * 1e3, "Q", 0, f) - 273.15
    pts = []
    for T in np.linspace(Tlo, Thi, n):
        if abs(T - Ts) < 0.3: continue
        pts.append([round(float(T), 2), float(f"{v_at(f, P, T):.5g}")])
    vf = 1 / CP.PropsSI("D", "P", P * 1e3, "Q", 0, f); vg = 1 / CP.PropsSI("D", "P", P * 1e3, "Q", 1, f)
    pts += [[round(Ts, 2), float(f"{vf:.5g}")], [round(Ts, 2), float(f"{vg:.5g}")]]
    pts.sort(key=lambda p: (p[0], p[1]))
    return pts

def dome(f, Tlo, Tc, n=60):
    liq, vap = [], []
    for T in np.linspace(Tlo, Tc - 0.05, n):
        liq.append([round(float(T), 2), float(f"{1 / CP.PropsSI('D', 'T', T + 273.15, 'Q', 0, f):.5g}")])
        vap.append([round(float(T), 2), float(f"{1 / CP.PropsSI('D', 'T', T + 273.15, 'Q', 1, f):.5g}")])
    return {"liq": liq, "vap": vap}

iso = {"w": {}, "r": {}}
for s in states:
    k = s["pk"]; fl = s["fluid"]
    if fl == "w" and k in old_keys: continue
    if k in iso[fl]: continue
    if fl == "w":
        iso["w"][k] = isobar("Water", s["P"], 1, 850)
    else:
        iso["r"][k] = isobar("R134a", s["P"], -45, 180)
out = {"iso": iso, "rdome": dome("R134a", -45, CP.PropsSI("Tcrit", "R134a") - 273.15)}
json.dump(out, open("curves2.json", "w"))
print({k: len(v) for k, v in iso.items()})
