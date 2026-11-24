"""Independent re-solve of every X1-X8 version: CoolProp (IAPWS-95) for water with no table emulation,
direct integration of air's ideal-gas c_p for X1, analytic gas relations otherwise.
python3 check_final2.py   (reads final2_templates.json)"""
import json, math, os
import CoolProp.CoolProp as CP
from scipy.optimize import brentq
from a17 import h_true, s0_true
HERE = os.path.dirname(os.path.abspath(__file__))
K = lambda c: c + 273.15
R, cp = 0.287, 1.005; E = 0.4 / 1.4
def w(o, *a): return CP.PropsSI(o, *a, "Water")
def PT(o, P, T): return w(o, "P", P * 1e3, "T", K(T)) / 1e3
def Ps(o, P, s): return w(o, "P", P * 1e3, "S", s * 1e3) / 1e3
def sat(o, P, q): return w(o, "P", P * 1e3, "Q", q) / (1e3 if o in "HS" else 1)
def vf(P): return 1 / w("D", "P", P * 1e3, "Q", 0)
PSI = 6.894757                          # kPa per psia
BTU, BTUR = 2.326, 4.1868               # kJ/kg per Btu/lbm, kJ/kg·K per Btu/lbm·R
u_true = lambda T: h_true(T) - R * T

def solve(tid, p):
    g = p.get
    if tid == "X1":
        r, rc, T1, P1 = g("r"), g("rc"), g("T1"), g("P1")
        T2 = brentq(lambda T: s0_true(T) - s0_true(T1) - R * math.log(r * T / T1), T1, 4 * T1)
        T3 = rc * T2
        T4 = brentq(lambda T: s0_true(T) - s0_true(T3) - R * math.log((T / T3) * (rc / r)), T1, T3)
        qin = h_true(T3) - h_true(T2); w_ = qin - (u_true(T4) - u_true(T1)); v1 = R * T1 / P1
        return [T2, qin, 100 * w_ / qin, w_ / (v1 * (1 - 1 / r))]
    if tid == "X2":
        rp, T1, T3, eps, cpe = g("rp"), g("T1F") + 459.67, g("T3F") + 459.67, g("eps"), 0.240
        T2, T4 = T1 * rp ** E, T3 / rp ** E; T5 = T2 + eps * (T4 - T2)
        wn = cpe * ((T3 - T4) - (T2 - T1))
        return [T2 - 459.67, T4 - 459.67, T5 - 459.67, 100 * wn / (cpe * (T3 - T5))]
    if tid == "X3":
        V1, P0, m, T3, T4, T5, P5 = g("V1"), g("P0"), g("m"), g("T3r"), g("T4"), g("T5r"), g("P5r")
        V6 = math.sqrt(2000 * cp * (T5 - T5 * (P0 / P5) ** E)); F = m * (V6 - V1) / 1000; Wp = F * V1
        return [V6, F, Wp, 100 * Wp / (m * cp * (T4 - T3))]
    if tid == "X4":
        Pb, T3, Pc = g("Pb"), g("T3"), g("Pc")
        h1 = sat("H", Pc, 0); wp = vf(Pc) * (Pb - Pc); h3, s3 = PT("H", Pb, T3), PT("S", Pb, T3); h4 = Ps("H", Pc, s3)
        wn = h3 - h4 - wp
        return [wp, w("Q", "P", Pc * 1e3, "S", s3 * 1e3), 100 * wn / (h3 - h1 - wp), g("Wmw") * 1000 / wn]
    if tid == "X5":
        P3, T3, P4, T5, Pc = g("P3") * PSI, (g("T3") - 32) / 1.8, g("P4") * PSI, (g("T5") - 32) / 1.8, g("Pc") * PSI
        h1 = sat("H", Pc, 0); wp = vf(Pc) * (P3 - Pc); h2 = h1 + wp
        h3, s3 = PT("H", P3, T3), PT("S", P3, T3); h4 = Ps("H", P4, s3); h5, s5 = PT("H", P4, T5), PT("S", P4, T5); h6 = Ps("H", Pc, s5)
        qin = (h3 - h2) + (h5 - h4); wn = (h3 - h4) + (h5 - h6) - wp
        return [h4 / BTU, w("Q", "P", Pc * 1e3, "S", s5 * 1e3), qin / BTU, 100 * wn / qin]
    if tid == "X6":
        Pb, T4, Pf, Pc = g("Pb"), g("T4"), g("Pf"), g("Pc")
        h1 = sat("H", Pc, 0); h2 = h1 + vf(Pc) * (Pb - Pc); h3 = h7 = sat("H", Pf, 0)
        h4, s4 = PT("H", Pb, T4), PT("S", Pb, T4); h5, h6 = Ps("H", Pf, s4), Ps("H", Pc, s4)
        y = (h3 - h2) / (h5 - h7); wn = (h4 - h5) + (1 - y) * (h5 - h6) - (h2 - h1)
        return [y, h4 - h3, wn, 100 * wn / (h4 - h3)]
    if tid == "X7":
        Pb, T5, Pp, Pc, m, f = g("Pb"), g("T5"), g("Pp"), g("Pc"), g("m"), g("f")
        h5, s5 = PT("H", Pb, T5), PT("S", Pb, T5); h6, h7 = Ps("H", Pp, s5), Ps("H", Pc, s5)
        mp, mc = f * m, (1 - f) * m; hfp, hfc = sat("H", Pp, 0), sat("H", Pc, 0)
        h2, h9 = hfc + vf(Pc) * (Pb - Pc), hfp + vf(Pp) * (Pb - Pp)
        Qp = mp * (h6 - hfp); Wn = m * (h5 - h6) + mc * (h6 - h7) - mc * (h2 - hfc) - mp * (h9 - hfp); Qin = m * h5 - mc * h2 - mp * h9
        return [Qp, Wn, Qin, 100 * (Wn + Qp) / Qin]
    if tid == "X8":
        PH, PL = g("PH"), g("PL")
        TH, TL = w("T", "P", PH * 1e3, "Q", 0), w("T", "P", PL * 1e3, "Q", 0)
        sfH, sgH = sat("S", PH, 0), sat("S", PH, 1); sfL, sgL = sat("S", PL, 0), sat("S", PL, 1)
        return [100 * (1 - TL / TH), sat("H", PH, 1) - sat("H", PH, 0), (sgH - sfL) / (sgL - sfL), (sfH - sfL) / (sgL - sfL)]
    raise KeyError(tid)

if __name__ == "__main__":
    tpls = json.load(open(os.path.join(HERE, "final2_templates.json")))
    worst = {}; flagged = 0; n = 0
    for t in tpls:
        for vi, v in enumerate(t["v"]):
            for q, tr in zip(v["parts"], solve(t["id"], v["_p"])):
                n += 1; ratio = abs(q["ans"] - tr) / (q["tol"] * abs(q["ans"]))
                worst[t["id"]] = max(worst.get(t["id"], 0), ratio)
                if ratio > 0.7:
                    flagged += 1; print(f"{t['id']} v{vi} ({q['id']}) ans {q['ans']:.6g} truth {tr:.6g} tol {q['tol']} ratio {ratio:.2f}")
    print("flagged", flagged, "of", n); print({k: round(v, 2) for k, v in worst.items()})
