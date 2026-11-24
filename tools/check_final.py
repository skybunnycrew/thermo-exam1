"""Independent re-solve of every final-set version straight from IAPWS-95 (CoolProp), no table emulation.
PYTHONPATH=/path/to/thermo-exam1/tools python3 check_final.py"""
import json, math, os
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__))
K = lambda c: c + 273.15
def w(o, *a): return CP.PropsSI(o, *a, "Water")
def PT(o, P, T): return w(o, "P", P * 1e3, "T", K(T)) / (1e3 if o in "HSU" else 1)
def Ps(o, P, s): return w(o, "P", P * 1e3, "S", s * 1e3) / (1e3 if o in "HSUT" and o != "T" else 1)
def Ph(o, P, h): return w(o, "P", P * 1e3, "H", h * 1e3) / (1e3 if o in "HSU" else 1)
def sat(o, P, q): return w(o, "P", P * 1e3, "Q", q) / (1e3 if o in "HSU" else 1)
def vf(P): return 1 / w("D", "P", P * 1e3, "Q", 0)
cp, cv, R, E = 1.005, 0.718, 0.287, 0.4 / 1.4
GAS = {"air": (0.2870, 0.718), "helium": (2.0769, 3.1156), "hydrogen": (4.124, 10.183)}

def solve(tid, p):
    g = p.get
    if tid == "F1":
        P3, T3, P4, T5, Pc, eT, eP = g("P3"), g("T3"), g("P4"), g("T5"), g("Pc"), g("eT"), g("eP")
        h1 = sat("H", Pc, 0); h2 = h1 + vf(Pc) * (P3 - Pc) / eP
        h3, s3 = PT("H", P3, T3), PT("S", P3, T3); h4 = h3 - eT * (h3 - Ps("H", P4, s3))
        h5, s5 = PT("H", P4, T5), PT("S", P4, T5); h6 = h5 - eT * (h5 - Ps("H", Pc, s5))
        x6 = Ph("Q", Pc, h6); wn = (h3 - h4) + (h5 - h6) - (h2 - h1); qin = (h3 - h2) + (h5 - h4)
        return [h4, x6, 100 * wn / qin, g("Wmw") * 1000 / wn]
    if tid == "F2":
        P3, T3, Pc, eT, eP = g("P3"), g("T3"), g("Pc"), g("eT"), g("eP")
        h1 = sat("H", Pc, 0); h2 = h1 + vf(Pc) * (P3 - Pc) / eP; h3, s3 = PT("H", P3, T3), PT("S", P3, T3)
        h4 = h3 - eT * (h3 - Ps("H", Pc, s3)); wn = h3 - h4 - (h2 - h1); m = g("Wmw") * 1000 / wn
        hw1, hw2 = w("H", "T", K(g("Tw1")), "Q", 0) / 1e3, w("H", "T", K(g("Tw2")), "Q", 0) / 1e3
        return [Ph("Q", Pc, h4), 100 * wn / (h3 - h2), m, m * (h4 - h1) / (hw2 - hw1)]
    if tid == "F3":
        Pb, T5, Pf, Pc = g("Pb"), g("T5"), g("Pf"), g("Pc")
        h1 = sat("H", Pc, 0); h2 = h1 + vf(Pc) * (Pf - Pc); h3 = sat("H", Pf, 0); h4 = h3 + vf(Pf) * (Pb - Pf)
        h5, s5 = PT("H", Pb, T5), PT("S", Pb, T5); h6, h7 = Ps("H", Pf, s5), Ps("H", Pc, s5)
        y = (h3 - h2) / (h6 - h2); wn = (h5 - h6) + (1 - y) * (h6 - h7) - (1 - y) * (h2 - h1) - (h4 - h3)
        return [y, h5 - h4, wn, 100 * wn / (h5 - h4)]
    if tid == "F4":
        Pb, T5, Pp, Pc, m, Qp = g("Pb"), g("T5"), g("Pp"), g("Pc"), g("m"), g("Qp")
        h5, s5 = PT("H", Pb, T5), PT("S", Pb, T5); h6, h7 = Ps("H", Pp, s5), Ps("H", Pc, s5)
        mp = Qp / (h6 - sat("H", Pp, 0)); mc = m - mp
        h2a = sat("H", Pc, 0) + vf(Pc) * (Pb - Pc); h2b = sat("H", Pp, 0) + vf(Pp) * (Pb - Pp)
        Wn = m * (h5 - h6) + mc * (h6 - h7) - mc * vf(Pc) * (Pb - Pc) - mp * vf(Pp) * (Pb - Pp)
        Qin = m * h5 - mc * h2a - mp * h2b
        return [mp, Wn, Qin, 100 * (Wn + Qp) / Qin]
    if tid == "F5":
        rp, T1, T3, Tst, Pb, Ts, Pc = g("rp"), g("T1"), g("T3"), g("Tst"), g("Pb"), g("Ts"), g("Pc")
        T2, T4 = T1 * rp ** E, T3 / rp ** E; wg = cp * ((T3 - T4) - (T2 - T1)); qin = cp * (T3 - T2)
        h1 = sat("H", Pc, 0); h2 = h1 + vf(Pc) * (Pb - Pc); h3, s3 = PT("H", Pb, Ts), PT("S", Pb, Ts); h4 = Ps("H", Pc, s3)
        y = cp * (T4 - Tst) / (h3 - h2); wt = wg + y * ((h3 - h4) - (h2 - h1))
        return [T4, y, 100 * wt / qin, g("Wmw") * 1000 / wt]
    if tid == "F6":
        R_, cv_ = GAS[g("gas")]; m, TH, TL, r = g("m"), g("TH"), g("TL"), g("r")
        W_ = m * R_ * (TH - TL) * math.log(r); Qh = m * R_ * TH * math.log(r)
        return [Qh, W_, W_ * g("rpm") / 60, 100 * W_ / (Qh + m * cv_ * (TH - TL))]
    if tid == "F7":
        T1, TH, rp = g("T1"), g("TH"), g("rp"); wn = R * (TH - T1) * math.log(rp)
        return [R * T1 * math.log(rp), wn, g("Wmw") * 1000 / wn, 100 * (1 - rp ** -E)]
    if tid == "F8":
        T1, T3, rp, eps = g("T1"), g("T3"), g("rp"), g("eps"); x = math.sqrt(rp)
        T2, T4 = T1 * x ** E, T3 / x ** E; wc, wt = 2 * cp * (T2 - T1), 2 * cp * (T3 - T4)
        T5 = T2 + eps * (T4 - T2); qin = cp * (T3 - T5) + cp * (T3 - T4)
        return [T2, 100 * wc / wt, 100 * (wt - wc) / qin, 100 * (1 - rp ** -E)]
    if tid == "F9":
        P3, T3, Pc, eT, TH = g("P3"), g("T3"), g("Pc"), g("eT"), g("TH"); TL = K(g("TLc"))
        h1, s1 = sat("H", Pc, 0), sat("S", Pc, 0); h2 = h1 + vf(Pc) * (P3 - Pc)
        h3, s3 = PT("H", P3, T3), PT("S", P3, T3); h4 = h3 - eT * (h3 - Ps("H", Pc, s3)); s4 = Ph("S", Pc, h4)
        a, b, c = s4 - s3, s3 - s1 - (h3 - h2) / TH, s1 - s4 + (h4 - h1) / TL
        return [a, b, c, a + b + c]
    raise KeyError(tid)

if __name__ == "__main__":
    d = json.load(open(os.path.join(HERE, "final_templates.json")))
    worst = {}; flagged = 0; n = 0
    for t in d["new"]:
        for vi, v in enumerate(t["v"]):
            for q, tr in zip(v["parts"], solve(t["id"], v["_p"])):
                n += 1; ratio = abs(q["ans"] - tr) / (q["tol"] * abs(q["ans"]))
                worst[t["id"]] = max(worst.get(t["id"], 0), ratio)
                if ratio > 0.7:
                    flagged += 1; print(f"{t['id']} v{vi} ({q['id']}) ans {q['ans']:.6g} truth {tr:.6g} tol {q['tol']} ratio {ratio:.2f}")
    print("flagged", flagged, "of", n); print({k: round(v, 2) for k, v in worst.items()})
