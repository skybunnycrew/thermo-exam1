"""Independent re-solve of every challenge variant: water and R-134a straight from the equation of state
(CoolProp, no table emulation), air with variable c from direct c_p integration, gases and solids analytically."""
import json, math
import CoolProp.CoolProp as CP
from scipy.optimize import brentq
from a17 import h_true, s0_true, Pr_true, u_true, vr_true
CP.set_reference_state("R134a", "ASHRAE")
K = lambda c: c + 273.15
def w(o, *a): return CP.PropsSI(o, *a, "Water")
def r(o, *a): return CP.PropsSI(o, *a, "R134a")
R, cp, cv = 0.287, 1.005, 0.718
E = 0.4 / 1.4
def Tof(f, target, lo=200, hi=2600): return brentq(lambda T: f(T) - target, lo, hi)

def solve(tid, p):
    g = p.get
    if tid.startswith("P"):
        return solve_past(tid, p)
    if tid == "C1":
        P1, T1, P2 = g("P1") * 1e3, K(g("T1")), g("P2") * 1e3
        h1 = w("H", "P", P1, "T", T1) / 1e3; s1 = w("S", "P", P1, "T", T1)
        h2s = w("H", "P", P2, "S", s1) / 1e3; h2 = h1 - g("eta") * (h1 - h2s)
        h3 = w("H", "P", P2, "T", K(g("T3"))) / 1e3; s3 = w("S", "P", P2, "T", K(g("T3")))
        y = (h1 - h3) / (h1 - h2); mT = y * g("m")
        return [h2, mT, mT * (h1 - h2), g("m") * (s3 - s1) / 1e3]
    if tid == "C2":
        P1, T1, P2, T2, P3, x3 = g("P1") * 1e3, K(g("T1")), g("P2") * 1e3, K(g("T2")), g("P3") * 1e3, g("x3")
        h1, s1 = w("H", "P", P1, "T", T1) / 1e3, w("S", "P", P1, "T", T1) / 1e3
        h2, s2 = w("H", "P", P2, "T", T2) / 1e3, w("S", "P", P2, "T", T2) / 1e3
        h3, s3 = w("H", "P", P3, "Q", x3) / 1e3, w("S", "P", P3, "Q", x3) / 1e3
        m1, m2 = g("m1"), g("f") * g("m1"); m3 = m1 - m2
        return [h3, m1 * h1 - m2 * h2 - m3 * h3 - g("Q"), m2 * s2 + m3 * s3 - m1 * s1 + g("Q") / K(g("Tc0"))]
    if tid == "C3":
        T1, rp, m = g("T1"), g("rp"), g("m"); h1 = h_true(T1)
        T2s = Tof(Pr_true, Pr_true(T1) * rp); h2 = h1 + (h_true(T2s) - h1) / g("eta"); T2 = Tof(h_true, h2)
        Q = m * (h2 - h_true(g("T3")))
        hw1, hw2 = w("H", "T", K(g("Tw1")), "Q", 0) / 1e3, w("H", "T", K(g("Tw2")), "Q", 0) / 1e3
        sw1, sw2 = w("S", "T", K(g("Tw1")), "Q", 0) / 1e3, w("S", "T", K(g("Tw2")), "Q", 0) / 1e3
        mw = Q / (hw2 - hw1)
        return [T2, m * (h2 - h1), mw, m * (s0_true(g("T3")) - s0_true(T1) - R * math.log(rp)) + mw * (sw2 - sw1)]
    if tid == "C4":
        mh, ch, mc, cc, Th, Tc = g("mh"), g("ch"), g("mc_"), g("cc"), K(g("Th")), K(g("Tc"))
        Tf = (mh * ch * Th + mc * cc * Tc) / (mh * ch + mc * cc)
        a, b = mh * ch * math.log(Tf / Th), mc * cc * math.log(Tf / Tc)
        return [Tf - 273.15, a, b, a + b]
    if tid == "C5":
        P1, T1, T2 = g("P1") * 1e3, K(g("T1")), K(g("Tc0"))
        D = w("D", "P", P1, "T", T1); m = g("V") * D
        x2 = w("Q", "T", T2, "D", D); u1 = w("U", "P", P1, "T", T1) / 1e3; u2 = w("U", "T", T2, "D", D) / 1e3
        s1 = w("S", "P", P1, "T", T1) / 1e3; s2 = w("S", "T", T2, "D", D) / 1e3
        Q = m * (u1 - u2)
        return [w("P", "T", T2, "Q", 0) / 1e3, x2, Q, m * (s2 - s1) + Q / T2]
    if tid == "C6":
        P, x1, m = g("P") * 1e3, g("x1"), g("m"); T2 = K(g("T2"))
        v1 = 1 / r("D", "P", P, "Q", x1); h1 = r("H", "P", P, "Q", x1) / 1e3; s1 = r("S", "P", P, "Q", x1) / 1e3
        v2 = 1 / r("D", "P", P, "T", T2); h2 = r("H", "P", P, "T", T2) / 1e3; s2 = r("S", "P", P, "T", T2) / 1e3
        Q = m * (h2 - h1)
        return [m * P / 1e3 * (v2 - v1), Q, m * (s2 - s1), m * (s2 - s1) - Q / K(g("TR"))]
    if tid == "C7":
        TH, Th, To = K(g("TH")), K(g("Th")), K(g("To")); QH, eta, COP = g("QH"), g("eta"), g("COP")
        W = eta * QH; eC = 1 - Th / TH; cC = Th / (Th - To)
        return [W, QH - W + COP * W, QH * (1 - eC) + QH * eC * cC]
    if tid == "C8":
        Ts, TL, To = K(g("Ts")), K(g("TL")), K(g("To")); Qs, QL = g("Qs"), g("QL")
        return [Qs + QL, (Qs + QL) / To - Qs / Ts - QL / TL, Qs * (1 - To / Ts) * TL / (To - TL)]
    if tid == "C9":
        T1, P1, P2, V1 = g("T1"), g("P1"), g("P2"), g("V1"); h1 = h_true(T1)
        T2s = Tof(Pr_true, Pr_true(T1) * P2 / P1); h2s = h_true(T2s); h2 = h1 - g("eta") * (h1 - h2s); T2 = Tof(h_true, h2)
        return [h2s, math.sqrt(V1 ** 2 + 2000 * (h1 - h2)), T2, s0_true(T2) - s0_true(T1) - R * math.log(P2 / P1)]
    if tid == "C10":
        Va, P0, T0, rp, T3 = g("Va"), g("P0"), g("T0a"), g("rp"), g("T3")
        T1 = T0 + Va ** 2 / 2000 / cp; P1 = P0 * (T1 / T0) ** 3.5; T2 = T1 * rp ** E; T4 = T3 - (T2 - T1); P4 = rp * P1 * (T4 / T3) ** 3.5
        T5 = T4 * (P0 / P4) ** E
        return [P1, T4, P4, math.sqrt(2000 * cp * (T4 - T5))]
    if tid == "C11":
        T1, rp, T3 = g("T1"), g("rp"), g("T3")
        h1, h3 = h_true(T1), h_true(T3)
        h2s = h_true(Tof(Pr_true, Pr_true(T1) * rp)); h4s = h_true(Tof(Pr_true, Pr_true(T3) / rp))
        h2 = h1 + (h2s - h1) / g("eC"); h4 = h3 - g("eT") * (h3 - h4s); wn = (h3 - h4) - (h2 - h1)
        return [h2, h4, 100 * wn / (h3 - h2), g("Wmw") * 1000 / wn]
    if tid == "C12":
        T1, rp, T3 = g("T1"), g("rp"), g("T3")
        T2 = T1 + (T1 * rp ** E - T1) / g("eC"); T4 = T3 - g("eT") * (T3 - T3 / rp ** E); T5 = T2 + g("eps") * (T4 - T2)
        wn = cp * ((T3 - T4) - (T2 - T1)); qin = cp * (T3 - T5); m = g("Wmw") * 1000 / wn
        return [T5, 100 * wn / qin, m, m * qin / 50000, m * qin / 120000]
    if tid == "C13":
        rr, T1, P1, q = g("r"), g("T1"), g("P1"), g("qin")
        T2 = Tof(vr_true, vr_true(T1) / rr); u3 = u_true(T2) + q; T3 = Tof(u_true, u3)
        T4 = Tof(vr_true, vr_true(T3) * rr); wn = q - (u_true(T4) - u_true(T1))
        v1 = R * T1 / P1
        return [T2, T3, 100 * wn / q, wn / (v1 * (1 - 1 / rr))]
    if tid == "C14":
        rr, T1, P1, q = g("r"), g("T1"), g("P1"), g("qin")
        T2 = T1 * rr ** 0.4; T3 = T2 + q / cp; rc = T3 / T2; T4 = T3 * (rc / rr) ** 0.4
        wn = q - cv * (T4 - T1); v1 = R * T1 / P1; mep = wn / (v1 * (1 - 1 / rr))
        return [rc, 100 * wn / q, mep, mep * g("Vd") / 1000 * g("rpm") / 120]
    if tid == "C15":
        P = g("P") * 1e3
        h1, s1 = w("H", "P", P, "T", K(g("T1"))) / 1e3, w("S", "P", P, "T", K(g("T1"))) / 1e3
        h3, s3, v3 = w("H", "P", P, "T", K(g("T3"))) / 1e3, w("S", "P", P, "T", K(g("T3"))) / 1e3, 1 / w("D", "P", P, "T", K(g("T3")))
        h2, s2 = w("H", "T", K(g("Tw")), "Q", 0) / 1e3, w("S", "T", K(g("Tw")), "Q", 0) / 1e3
        m1 = g("m1"); m2 = m1 * (h1 - h3) / (h3 - h2); m3 = m1 + m2
        return [m2, m3 * v3, m3 * s3 - m1 * s1 - m2 * s2]
    if tid == "C16":
        PH, PL, mw = g("PH") * 1e3, g("PL") * 1e3, g("mw")
        h1, s1 = r("H", "P", PH, "Q", 0) / 1e3, r("S", "P", PH, "Q", 0) / 1e3
        x2 = r("Q", "P", PL, "H", h1 * 1e3); s2 = r("S", "P", PL, "H", h1 * 1e3) / 1e3
        hg, sgv = r("H", "P", PL, "Q", 1) / 1e3, r("S", "P", PL, "Q", 1) / 1e3
        hw1, hw2 = w("H", "T", K(g("Twi")), "Q", 0) / 1e3, w("H", "T", K(g("Two")), "Q", 0) / 1e3
        sw1, sw2 = w("S", "T", K(g("Twi")), "Q", 0) / 1e3, w("S", "T", K(g("Two")), "Q", 0) / 1e3
        mR = mw * (hw1 - hw2) / (hg - h1)
        return [x2, mR, mR * (s2 - s1), mR * (sgv - s2) + mw * (sw2 - sw1)]
    raise KeyError(tid)

FK = lambda F: (F - 32) / 1.8 + 273.15
def wEh(F): return w("H", "T", FK(F), "Q", 0) / 2326
def wEs(F): return w("S", "T", FK(F), "Q", 0) / 4186.8
def wEv(F): return 16.0185 / w("D", "T", FK(F), "Q", 0)
def solve_past(tid, p):
    g = p.get; R0 = 459.67
    if tid == "P1":
        QL = g("mw") * (wEh(g("Twi")) - wEh(g("Two"))); T = FK(g("Te"))
        hf, hg = r("H", "T", T, "Q", 0) / 2326, r("H", "T", T, "Q", 1) / 2326; hin = hf + g("xin") * (hg - hf)
        Wb = g("W") * 2544.43 / 3600; QH = QL + Wb
        return [QL / (hg - hin), QH * 3600, QH / Wb, (g("TH") + R0) / (g("TH") - g("Twi"))]
    if tid == "P2":
        m = g("Vd") / wEv(g("T1")); QL = m * (wEh(g("T2")) - wEh(g("T1"))); QH = (g("TH") + R0) * m * (wEs(g("T2")) - wEs(g("T1")))
        return [m, QL, (QH - QL) * 1.055056 / 1000, 100 * (QH - QL) / QH]
    if tid == "P3":
        P1, T1, T2 = g("P1") * 1e3, K(g("T1")), K(g("T2"))
        h1, s1 = w("H", "P", P1, "T", T1) / 1e3, w("S", "P", P1, "T", T1) / 1e3
        h2, s2 = w("H", "T", T2, "Q", 1) / 1e3, w("S", "T", T2, "Q", 1) / 1e3
        dke = (g("V1") ** 2 - g("V2") ** 2) / 2000; q = h1 - h2 + dke - g("w")
        h2s = w("H", "T", T2, "S", s1 * 1e3) / 1e3
        return [q, s2 - s1 + q / g("T0"), 100 * g("w") / (h1 - h2s + dke)]
    if tid == "P4":
        cpE, RE = 0.240, 0.06855; y = g("y"); Ti, Tc = g("Tin") + R0, g("Tc") + R0; Th = (Ti - y * Tc) / (1 - y)
        sT = y * cpE * math.log(Tc / Ti) + (1 - y) * cpE * math.log(Th / Ti)
        return [Th - R0, sT + RE * math.log(g("Pin")), math.exp(-sT / RE)]
    if tid == "P5":
        mA, mB, TA, TB, PA, PB = g("mA"), g("mB"), g("TA"), g("TB"), g("PA"), g("PB")
        Tf = Tof(u_true, (mA * u_true(TA) + mB * u_true(TB)) / (mA + mB))
        Pf = (mA + mB) * R * Tf / (mA * R * TA / PA + mB * R * TB / PB)
        return [Tf, Pf, mA * (s0_true(Tf) - s0_true(TA) - R * math.log(Pf / PA)) + mB * (s0_true(Tf) - s0_true(TB) - R * math.log(Pf / PB))]
    if tid == "P6":
        P1, T1, V1, P2, n = g("P1"), g("T1"), g("V1"), g("P2"), g("n")
        m = P1 * V1 / (R * T1); T2 = T1 * (P2 / P1) ** ((n - 1) / n); Wi = m * R * (T2 - T1) / (n - 1); Q = Wi - m * (u_true(T2) - u_true(T1))
        return [T2, Wi, Q, m * (s0_true(T2) - s0_true(T1) - R * math.log(P2 / P1)) + Q / T1]
    if tid == "P7":
        T1, rr, n = g("T1"), g("r"), g("n"); e = (n - 1) / n; x = math.sqrt(rr)
        ws = 2 * n * R * T1 / (n - 1) * (x ** e - 1); w1 = n * R * T1 / (n - 1) * (rr ** e - 1)
        return [100 * x, ws, 100 * (1 - ws / w1), cp * T1 * (x ** e - 1)]
    if tid == "P8":
        P1, T1, P2, m = g("P1") * 1e3, K(g("T1")), g("P2") * 1e3, g("m")
        D = w("D", "P", P1, "T", T1); u1, s1 = w("U", "P", P1, "T", T1) / 1e3, w("S", "P", P1, "T", T1) / 1e3
        T2 = w("T", "P", P2, "D", D); u2, s2 = w("U", "P", P2, "D", D) / 1e3, w("S", "P", P2, "D", D) / 1e3
        return [T2 - 273.15, m * (u2 - u1), m * (s2 - s1)]
    if tid == "P9":
        kk = g("k") / 3600; TH = g("Tin") + 273.15; Wm, f = g("Wmax"), g("f")
        need = kk * (g("Tin") - g("Tcold")); cop = f * TH / (g("Tin") - g("Tcold"))
        return [math.sqrt(Wm * TH / kk), math.sqrt(f * Wm * TH / kk), need - cop * Wm]
    raise KeyError(tid)

if __name__ == "__main__":
    tpls = json.load(open("challenge_templates.json"))
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
                    print(f"{t['id']} v{vi} ({q['id']}) ans {q['ans']:.6g} truth {tr:.6g} tol {q['tol']} ratio {ratio:.2f}")
    by = {}
    for x in worst: by[x[1]] = max(by.get(x[1], 0), x[0])
    print("flagged", flagged, "of", len(worst)); print({k: round(v, 2) for k, v in by.items()})
