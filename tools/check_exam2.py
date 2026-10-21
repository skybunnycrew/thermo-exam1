"""Independent re-solve of every Exam 2 variant: water and R-134a straight from the equation of state
(no table emulation), ideal gases analytically, air with variable c from direct cp integration."""
import json, math, sys
import CoolProp.CoolProp as CP
from scipy.optimize import brentq
from a17 import h_true, s0_true, Pr_true
CP.set_reference_state("R134a", "ASHRAE")
K = lambda c: c + 273.15
def w(o, *a): return CP.PropsSI(o, *a, "Water")
def r(o, *a): return CP.PropsSI(o, *a, "R134a")
Rair, cpA, cvA = 0.287, 1.005, 0.718
cpHe, RHe = 5.1926, 2.0769

def solve(tid, p):
    g = p.get
    if tid == "E1":
        v1 = 1 / w("D", "P", g("P1") * 1e3, "T", K(g("T1"))); h1 = w("H", "P", g("P1") * 1e3, "T", K(g("T1"))) / 1e3
        v2 = 1 / w("D", "P", g("P2") * 1e3, "T", K(g("T2"))); h2 = w("H", "P", g("P2") * 1e3, "T", K(g("T2"))) / 1e3
        m = g("A1") / 1e4 * g("V1") / v1; V2 = math.sqrt(g("V1") ** 2 + 2000 * (h1 - h2 - g("Q") / m))
        return [m, V2, m * v2 / V2 * 1e4]
    if tid == "E2":
        m = g("mmin") / 60; wi = cpHe * (g("T2") - g("T1")) + g("q")
        return [wi, m * wi, m * RHe * g("T1") / g("P1")]
    if tid == "E3":
        P1, T1, P2, x = g("P1") * 1e3, K(g("T1")), g("P2") * 1e3, g("x")
        h1 = w("H", "P", P1, "T", T1) / 1e3; h2 = w("H", "P", P2, "Q", x) / 1e3; v2 = 1 / w("D", "P", P2, "Q", x)
        Wd = g("m") * ((h1 - h2) + (g("V1") ** 2 - g("V2") ** 2) / 2000)
        return [h2, Wd, g("m") * v2 / g("V2")]
    if tid == "E4":
        T1 = K(g("T1c")); T2 = T1 + (g("V1") ** 2 - g("V2") ** 2) / 2000 / cpA
        m = g("P1") * g("A1") * g("V1") / (Rair * T1)
        return [m, T2, m * Rair * T2 / (g("P2") * g("V2"))]
    if tid == "E5":
        P1 = g("P1") * 1e3
        h1 = r("H", "P", P1, "Q", 0) if g("kind") == "sat" else r("H", "T", K(g("T1")), "Q", 0)
        P2 = g("P2") * 1e3; x = r("Q", "P", P2, "H", h1); T2 = r("T", "P", P2, "Q", 0) - 273.15
        v2 = 1 / r("D", "P", P2, "H", h1)
        return [x, T2, g("m") * v2 * 1000]
    if tid == "E6":
        P = g("P") * 1e3; h1 = w("H", "P", P, "Q", g("x")) / 1e3; h2 = w("H", "P", P, "Q", 0) / 1e3
        h3 = w("H", "T", K(g("T3")), "Q", 0) / 1e3; h4 = w("H", "T", K(g("T4")), "Q", 0) / 1e3
        Q = g("mw") * (h4 - h3); return [Q, Q / (h1 - h2)]
    if tid == "E7":
        P = g("P") * 1e3; h1 = w("H", "P", P, "T", K(g("T1"))) / 1e3; h2 = w("H", "T", K(g("T2")), "Q", 0) / 1e3; h3 = w("H", "P", P, "Q", 0) / 1e3
        y = (h3 - h2) / (h1 - h3); return [y, y * g("m2"), w("T", "P", P, "Q", 0) - 273.15]
    if tid == "E8":
        h1 = r("H", "P", g("P") * 1e3, "T", K(g("T1"))) / 1e3; h2 = r("H", "T", K(g("T2")), "Q", 0) / 1e3
        Q = g("mR") * (h1 - h2); ma = Q / (cpA * g("dTa")); return [Q, ma, ma * Rair * K(g("Ta")) / 100]
    if tid == "E9":
        Q = g("mg") * (h_true(g("Tg1")) - h_true(g("Tg2")))
        h3 = w("H", "T", K(g("T3")), "Q", 0) / 1e3; h4 = w("H", "T", K(g("T4")), "Q", 0) / 1e3
        return [Q, Q / (h4 - h3), g("mg") * cpA * (g("Tg1") - g("Tg2"))]
    if tid == "E10":
        TH, TL, QH, eta = K(g("TH")), K(g("TL")), g("QH"), g("eta")
        Wd = eta * QH; QL = QH - Wd; return [100 * eta, QL, 100 * (1 - TL / TH), QL / TL - QH / TH]
    if tid == "E11":
        TH, TL = K(g("Ti")), K(g("To")); Wd = g("QH") / g("COP"); cm = TH / (TH - TL)
        return [Wd, g("QH") - Wd, cm, g("QH") / cm]
    if tid == "E12":
        TH, TL = K(g("TH")), K(g("TL")); Wd = g("Wd"); QH = g("QL") + Wd
        return [g("QL") / Wd, QH, TL / (TH - TL), QH / TH - g("QL") / TL]
    if tid == "E13":
        P1, T1, P2 = g("P1") * 1e3, K(g("T1")), g("P2") * 1e3
        h1 = w("H", "P", P1, "T", T1) / 1e3; s1 = w("S", "P", P1, "T", T1)
        h2s = w("H", "P", P2, "S", s1) / 1e3; h2a = h1 - g("eta") * (h1 - h2s)
        s2a = w("S", "P", P2, "H", h2a * 1e3) / 1e3
        return [h2s, h2a, g("m") * (h1 - h2a), g("m") * (s2a - s1 / 1e3)]
    if tid == "E14":
        T1, rp = g("T1"), g("rp"); h1 = h_true(T1)
        T2s = brentq(lambda T: Pr_true(T) - Pr_true(T1) * rp, T1, 2000); h2s = h_true(T2s)
        wa = (h2s - h1) / g("eta"); T2a = brentq(lambda T: h_true(T) - (h1 + wa), T1, 2000)
        return [h2s, g("m") * wa, T2a, g("m") * (s0_true(T2a) - s0_true(T1) - Rair * math.log(rp))]
    if tid == "E15":
        P1, P2 = g("P1") * 1e3, g("P2") * 1e3
        h1 = r("H", "P", P1, "Q", 1) / 1e3; s1 = r("S", "P", P1, "Q", 1)
        h2s = r("H", "P", P2, "S", s1) / 1e3; h2a = h1 + (h2s - h1) / g("eta")
        T2a = r("T", "P", P2, "H", h2a * 1e3) - 273.15; s2a = r("S", "P", P2, "H", h2a * 1e3)
        return [h2s, g("m") * (h2a - h1), T2a, g("m") * (s2a - s1) / 1e3]
    if tid == "E16":
        rr, T1, q = g("r"), g("T1"), g("qin"); T2 = T1 * rr ** 0.4; T3 = T2 + q / cvA; T4 = T3 / rr ** 0.4
        return [T2, T3, q - cvA * (T4 - T1), 100 * (1 - rr ** -0.4)]
    if tid == "E17":
        rr, rc, T1 = g("r"), g("rc"), g("T1"); T2 = T1 * rr ** 0.4; T3 = rc * T2; T4 = T3 * (rc / rr) ** 0.4
        qin = cpA * (T3 - T2); return [T2, T3, qin, 100 * (1 - cvA * (T4 - T1) / qin)]
    if tid == "E18":
        rr, rp, rc, T1 = g("r"), g("rp"), g("rc"), g("T1"); T2 = T1 * rr ** 0.4; Tx = rp * T2; T3 = rc * Tx; T4 = T3 * (rc / rr) ** 0.4
        qin = cvA * (Tx - T2) + cpA * (T3 - Tx); return [T2, Tx, qin, 100 * (1 - cvA * (T4 - T1) / qin)]
    if tid == "E19":
        rp, T1, T3 = g("rp"), g("T1"), g("T3"); e = 0.4 / 1.4; T2 = T1 * rp ** e; T4 = T3 / rp ** e
        return [T2, T4, 100 * (T2 - T1) / (T3 - T4), 100 * (1 - rp ** -e)]
    if tid == "E20":
        rp, T1, T3 = g("rp"), g("T1"), g("T3")
        T2 = brentq(lambda T: Pr_true(T) - Pr_true(T1) * rp, T1, 2200); T4 = brentq(lambda T: Pr_true(T) - Pr_true(T3) / rp, 250, T3)
        h1, h2, h3, h4 = h_true(T1), h_true(T2), h_true(T3), h_true(T4); wn = (h3 - h4) - (h2 - h1)
        return [h2, h4, wn, 100 * wn / (h3 - h2)]
    raise KeyError(tid)

tpls = json.load(open("exam2_templates.json"))
worst = []; flagged = 0
for t in tpls:
    for vi, v in enumerate(t["v"]):
        truth = solve(t["id"], v["_p"])
        assert len(truth) == len(v["parts"]), t["id"]
        for q, tr in zip(v["parts"], truth):
            ratio = abs(q["ans"] - tr) / (q["tol"] * abs(q["ans"]))
            worst.append((ratio, t["id"], vi, q["id"], q["ans"], tr))
            if ratio > 0.7:
                flagged += 1
                print(f"{t['id']} v{vi} ({q['id']}) ans {q['ans']:.6g} truth {tr:.6g} ratio {ratio:.2f}")
worst.sort(reverse=True)
by = {}
for x in worst: by[x[1]] = max(by.get(x[1], 0), x[0])
print("flagged", flagged, "of", len(worst)); print({k: round(v, 2) for k, v in by.items()})
