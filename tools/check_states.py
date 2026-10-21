"""Independent check: recompute every answer straight from the equation of state (no table emulation)."""
import json, sys
import CoolProp.CoolProp as CP
CP.set_reference_state("R134a", "ASHRAE")
items = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "states2.json"))
NAME = {"w": "Water", "r": "R134a"}
KEY = {"T": "T", "P": "P", "v": "D", "u": "U", "h": "H", "s": "S", "x": "Q"}
def conv(k, v):
    if k == "T": return v + 273.15
    if k == "v": return 1 / v
    if k == "x": return v
    return v * 1e3
def back(k, v):
    return {"T": v - 273.15, "P": v / 1e3, "D": 1 / v, "U": v / 1e3, "H": v / 1e3, "S": v / 1e3, "Q": v}[k]
bad = 0; worst = []
for it in items:
    f = NAME[it["fluid"]]
    g = it["given"]
    try:
        if g[1][0] == "state":
            q = 0 if "liquid" in g[1][1] else 1
            a = (KEY[g[0][0]], conv(g[0][0], g[0][1]), "Q", q)
        else:
            a = (KEY[g[0][0]], conv(g[0][0], g[0][1]), KEY[g[1][0]], conv(g[1][0], g[1][1]))
        try: phase_cp = CP.PhaseSI(*a, f)
        except ValueError: phase_cp = "?"
        if it["phase"] == "cl" and it["table"] in ("A-4", "A-11"):
            T = g[0][1] + 273.15
            truth = back(KEY[it["ask"]], CP.PropsSI(KEY[it["ask"]], "T", T, "Q", 0, f))
        else:
            k = KEY[it["ask"]]
            try:
                truth = back(k, CP.PropsSI(k, *a, f))
            except ValueError:
                # T with u/h/s: solve on the saturation line, else by P root-find
                T = g[0][1] + 273.15; gk = KEY[g[1][0]]; y = conv(g[1][0], g[1][1])
                yf = CP.PropsSI(gk, "T", T, "Q", 0, f); yg = CP.PropsSI(gk, "T", T, "Q", 1, f)
                if yf < y < yg:
                    q = (y - yf) / (yg - yf); a = ("T", T, "Q", q); phase_cp = "twophase"
                    truth = back(k, CP.PropsSI(k, "T", T, "Q", q, f)) if k != "Q" else q
                else:
                    from scipy.optimize import brentq
                    Ps = CP.PropsSI("P", "T", T, "Q", 0, f)
                    fn = lambda P: CP.PropsSI(gk, "T", T, "P", P, f) - y
                    P = brentq(fn, 100, Ps * 0.999) if y > yg else brentq(fn, Ps * 1.001, 5e7)
                    truth = back(k, CP.PropsSI(k, "T", T, "P", P, f)); phase_cp = CP.PhaseSI("T", T, "P", P, f)
    except Exception as e:
        print("ERR", it["id"], e); bad += 1; continue
    exp_phase = {"cl": ("liquid", "supercritical_liquid"), "sh": ("gas", "supercritical_gas", "supercritical"), "mix": ("twophase",), "sl": ("twophase", "liquid"), "sv": ("twophase", "gas")}[it["phase"]]
    ph_ok = phase_cp in exp_phase
    ans = it["answer"]
    tol = max(it["tol"] * abs(ans), it.get("atol", 0))
    err = abs(truth - ans)
    if not ph_ok or err > tol:
        bad += 1
        print(f"{it['id']} {it['fluid']} {it['phase']}/{phase_cp} ask {it['ask']} ans {ans} truth {truth:.6g} err {err:.3g} tol {tol:.3g} tags {it['tags']} given {g}")
    worst.append((err / tol if tol else 0, it["id"]))
    it["_ratio"] = err / tol if tol else 0
    it["_ok"] = ph_ok
worst.sort(reverse=True)
print("checked", len(items), "flagged", bad, "worst ratios", worst[:8])

if len(sys.argv) > 2:
    keep = [it for it in items if it.get("_ok") and it.get("_ratio", 9) <= 0.7]
    for i, it in enumerate(keep):
        it.pop("_ratio", None); it.pop("_ok", None)
        it["id"] = ("R" if it["fluid"] == "r" else "W") + f"{i + 1:03d}"
    json.dump(keep, open(sys.argv[2], "w"), ensure_ascii=False)
    print("kept", len(keep))
