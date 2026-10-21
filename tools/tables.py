"""Emulate Cengel & Boles property tables (water A-4..A-7, R-134a A-11..A-13).

Values come from CoolProp (IAPWS-95 for water; Tillner-Roth & Baehr for R-134a with the
ASHRAE reference state, h = s = 0 for saturated liquid at -40 C, which is Cengel's), evaluated
on Cengel's grid and rounded the way the printed tables round them. Students interpolate
linearly between printed rows, so answers are built the same way.
"""
import math
import CoolProp.CoolProp as CP

CP.set_reference_state("R134a", "ASHRAE")

def rdec(x, d):
    return round(x + 0.0, d)

def rsig(x, n):
    if x == 0:
        return 0.0
    d = n - 1 - int(math.floor(math.log10(abs(x))))
    return round(x, d)

def fmt(x, d=None, n=None):
    """Format like the table prints it."""
    if n is not None:
        x = rsig(x, n)
        d = max(0, n - 1 - int(math.floor(math.log10(abs(x))))) if x else 0
    s = f"{x:,.{d}f}" if abs(x) >= 10000 else f"{x:.{d}f}"
    return s.replace("-", "−")


class Fluid:
    def __init__(self, key, cp_name, label):
        self.key, self.cp, self.label = key, cp_name, label

    # ----- raw (true) values -----
    def raw_sat_T(self, Tc, q):
        T = Tc + 273.15
        return dict(P=CP.PropsSI("P", "T", T, "Q", q, self.cp) / 1e3,
                    v=1 / CP.PropsSI("D", "T", T, "Q", q, self.cp),
                    u=CP.PropsSI("U", "T", T, "Q", q, self.cp) / 1e3,
                    h=CP.PropsSI("H", "T", T, "Q", q, self.cp) / 1e3,
                    s=CP.PropsSI("S", "T", T, "Q", q, self.cp) / 1e3)

    def raw_sat_P(self, PkPa, q):
        P = PkPa * 1e3
        d = dict(T=CP.PropsSI("T", "P", P, "Q", q, self.cp) - 273.15,
                 v=1 / CP.PropsSI("D", "P", P, "Q", q, self.cp),
                 u=CP.PropsSI("U", "P", P, "Q", q, self.cp) / 1e3,
                 h=CP.PropsSI("H", "P", P, "Q", q, self.cp) / 1e3,
                 s=CP.PropsSI("S", "P", P, "Q", q, self.cp) / 1e3)
        return d

    def raw_PT(self, PkPa, Tc):
        P, T = PkPa * 1e3, Tc + 273.15
        return dict(v=1 / CP.PropsSI("D", "T", T, "P", P, self.cp),
                    u=CP.PropsSI("U", "T", T, "P", P, self.cp) / 1e3,
                    h=CP.PropsSI("H", "T", T, "P", P, self.cp) / 1e3,
                    s=CP.PropsSI("S", "T", T, "P", P, self.cp) / 1e3)

    def Tsat_true(self, PkPa):
        return CP.PropsSI("T", "P", PkPa * 1e3, "Q", 0, self.cp) - 273.15

    def Psat_true(self, Tc):
        return CP.PropsSI("P", "T", Tc + 273.15, "Q", 0, self.cp) / 1e3


class Water(Fluid):
    TT, PT, SHT, CLT = "A-4", "A-5", "A-6", "A-7"
    T_GRID = [0.01] + list(range(5, 371, 5)) + [373.95]
    P_GRID = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 101.325,
              125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 450, 500, 550, 600, 650,
              700, 750, 800, 850, 900, 950, 1000, 1100, 1200, 1300, 1400, 1500, 1750, 2000, 2250,
              2500, 3000, 3500, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000,
              14000, 15000, 16000, 17000, 18000, 19000, 20000]
    # Superheated blocks (kPa -> temperature rows, Sat row excluded). Only blocks whose rows we
    # are confident match the printed book are used for interpolation.
    SH = {
        10:   [50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800],
        50:   [100, 150, 200, 250, 300, 400, 500, 600, 700, 800],
        100:  [100, 150, 200, 250, 300, 400, 500, 600, 700, 800],
        200:  [150, 200, 250, 300, 400, 500, 600, 700, 800],
        300:  [150, 200, 250, 300, 400, 500, 600, 700, 800],
        400:  [150, 200, 250, 300, 400, 500, 600, 700, 800],
        600:  [200, 250, 300, 350, 400, 500, 600, 700, 800],
        800:  [200, 250, 300, 350, 400, 500, 600, 700, 800],
        1000: [200, 250, 300, 350, 400, 500, 600, 700, 800],
        1200: [200, 250, 300, 350, 400, 500, 600, 700, 800],
        1400: [200, 250, 300, 350, 400, 500, 600, 700, 800],
        3000: [250, 300, 350, 400, 450, 500, 600, 700, 800],
        5000: [300, 350, 400, 450, 500, 600, 700, 800],
        8000: [300, 350, 400, 450, 500, 550, 600, 700, 800],
        10000: [350, 400, 450, 500, 550, 600, 650, 700, 800],
    }
    CL_P = [5000, 10000, 15000, 20000]
    CL_T = list(range(20, 341, 20))

    def __init__(self):
        super().__init__("w", "Water", "Water")

    def satT(self, Tc):
        f, g = self.raw_sat_T(Tc, 0), self.raw_sat_T(Tc, 1)
        r = dict(T=Tc, P=rsig(f["P"], 5), vf=rdec(f["v"], 6), vg=rsig(g["v"], 5))
        for k in "uhs":
            d = 2 if k != "s" else 4
            r[k + "f"], r[k + "g"], r[k + "fg"] = rdec(f[k], d), rdec(g[k], d), rdec(g[k] - f[k], d)
        r["ufg"] = rdec(g["u"] - f["u"], 2)
        r["vfg"] = rsig(g["v"] - f["v"], 5)
        return r

    def satP(self, P):
        f, g = self.raw_sat_P(P, 0), self.raw_sat_P(P, 1)
        r = dict(P=P, T=rdec(f["T"], 2), vf=rdec(f["v"], 6), vg=rsig(g["v"], 5))
        for k in "uhs":
            d = 2 if k != "s" else 4
            r[k + "f"], r[k + "g"], r[k + "fg"] = rdec(f[k], d), rdec(g[k], d), rdec(g[k] - f[k], d)
        r["vfg"] = rsig(g["v"] - f["v"], 5)
        return r

    def sh(self, P, Tc):
        d = self.raw_PT(P, Tc)
        return dict(T=Tc, v=rsig(d["v"], 5), u=rdec(d["u"], 1), h=rdec(d["h"], 1), s=rdec(d["s"], 4))

    def shsat(self, P):
        g = self.satP(P)
        return dict(T=g["T"], v=g["vg"], u=rdec(g["ug"], 1), h=rdec(g["hg"], 1), s=g["sg"])

    def cl(self, P, Tc):
        d = self.raw_PT(P, Tc)
        return dict(T=Tc, v=rdec(d["v"], 7), u=rdec(d["u"], 2), h=rdec(d["h"], 2), s=rdec(d["s"], 4))

    # how each property prints, for explanation text
    def pf(self, k, x, table):
        if k == "v":
            if table == self.CLT:
                return fmt(x, 7)
            return fmt(x, 6) if x < 0.01 else fmt(x, n=5)
        if k in "uh":
            return fmt(x, 1 if table == self.SHT else 2)
        if k == "s":
            return fmt(x, 4)
        if k == "P":
            return fmt(x, n=5)
        if k == "T":
            return fmt(x, 2)
        if k == "x":
            return fmt(x, 4)
        return str(x)

    def pblock(self, P):
        return f"P = {fmt_P(P)}"


class R134a(Fluid):
    TT, PT, SHT, CLT = "A-11", "A-12", "A-13", None
    T_GRID = list(range(-40, 45, 2)) + [60, 70, 80, 90]
    P_GRID = [60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 240, 280, 320, 360, 400, 450, 500, 550,
              600, 700, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000]
    SH_P = [60, 100, 140, 180, 200, 240, 280, 320, 400, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600]
    SH = {}

    def __init__(self):
        super().__init__("r", "R134a", "R-134a")
        for P in self.SH_P:
            ts = self.Tsat_true(P)
            first = int(math.floor(ts / 10.0) * 10 + 10)
            self.SH[P] = list(range(first, 101, 10))

    def _P(self, P):
        return rdec(P, 2) if P < 1000 else rdec(P, 1)

    def satT(self, Tc):
        f, g = self.raw_sat_T(Tc, 0), self.raw_sat_T(Tc, 1)
        r = dict(T=Tc, P=self._P(f["P"]), vf=rdec(f["v"], 7), vg=rdec(g["v"], 5))
        for k in "uhs":
            d = 2 if k != "s" else 5
            r[k + "f"], r[k + "g"], r[k + "fg"] = rdec(f[k], d), rdec(g[k], d), rdec(g[k] - f[k], d)
        r["vfg"] = rdec(g["v"] - f["v"], 5)
        return r

    def satP(self, P):
        f, g = self.raw_sat_P(P, 0), self.raw_sat_P(P, 1)
        r = dict(P=P, T=rdec(f["T"], 2), vf=rdec(f["v"], 7), vg=rdec(g["v"], 5))
        for k in "uhs":
            d = 2 if k != "s" else 5
            r[k + "f"], r[k + "g"], r[k + "fg"] = rdec(f[k], d), rdec(g[k], d), rdec(g[k] - f[k], d)
        r["vfg"] = rdec(g["v"] - f["v"], 5)
        return r

    def sh(self, P, Tc):
        d = self.raw_PT(P, Tc)
        return dict(T=Tc, v=rsig(d["v"], 5), u=rdec(d["u"], 2), h=rdec(d["h"], 2), s=rdec(d["s"], 4))

    def shsat(self, P):
        g = self.satP(P)
        return dict(T=g["T"], v=rsig(g["vg"], 5), u=g["ug"], h=g["hg"], s=rdec(g["sg"], 4))

    def pf(self, k, x, table):
        if k == "v":
            return fmt(x, 7) if x < 0.002 else fmt(x, n=5)
        if k in "uh":
            return fmt(x, 2)
        if k == "s":
            return fmt(x, 5 if table in (self.TT, self.PT) else 4)
        if k == "P":
            return fmt(x, 2) if x < 1000 else fmt(x, 1)
        if k == "T":
            return fmt(x, 2)
        if k == "x":
            return fmt(x, 4)
        return str(x)


def fmt_P(p):
    if p >= 1000:
        s = f"{p / 1000:.4f}".rstrip("0").rstrip(".")
        return s + " MPa"
    if float(p).is_integer():
        return f"{int(p)} kPa"
    return f"{p:g} kPa"


def fmt_T(t):
    if float(t).is_integer():
        return f"{int(t)} °C".replace("-", "−")
    return (f"{t:.2f}".rstrip("0").rstrip(".") + " °C").replace("-", "−")


WATER = Water()
R = R134a()
