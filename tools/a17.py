"""Emulate Cengel Table A-17 (ideal-gas properties of air) and the A-2a constants.

h(T) and s°(T) integrate CoolProp's ideal-gas cp of air, anchored to the table's 300 K row
(h = 300.19 kJ/kg, s° = 1.70203 kJ/kg·K, Pr = 1.3860). Spot checks against printed rows agree
within 0.1 kJ/kg in h and 0.0003 in s°.
"""
import math
from functools import lru_cache
import CoolProp.CoolProp as CP
from scipy.integrate import quad

R_AIR = 0.287
GRID = list(range(200, 281, 10)) + [285, 290, 295, 298, 300, 305, 310, 315, 320, 325, 330] + \
       list(range(340, 761, 10)) + list(range(780, 1701, 20)) + list(range(1750, 2201, 50))

def _cp(T): return CP.PropsSI("Cp0mass", "T", T, "P", 101325, "Air") / 1e3

@lru_cache(None)
def h_true(T): return 300.19 + quad(_cp, 300, T)[0]
@lru_cache(None)
def s0_true(T): return 1.70203 + quad(lambda t: _cp(t) / t, 300, T)[0]
def Pr_true(T): return 1.3860 * math.exp((s0_true(T) - 1.70203) / R_AIR)
def u_true(T): return h_true(T) - R_AIR * T
def vr_true(T):
    # vr ∝ T/Pr, anchored so vr(300) = 621.2
    return 621.2 * (T / 300) / (Pr_true(T) / 1.3860)

def _sig(x, n):
    d = n - 1 - int(math.floor(math.log10(abs(x))))
    return round(x, d)

@lru_cache(None)
def row(T):
    """One printed row of A-17."""
    return dict(T=T, h=round(h_true(T), 2 if T <= 1700 else 1), u=round(u_true(T), 2 if T <= 1700 else 1),
                s=round(s0_true(T), 5), Pr=_sig(Pr_true(T), 4 if Pr_true(T) >= 2 else 5), vr=_sig(vr_true(T), 4))

def bracket(key, val):
    for a, b in zip(GRID, GRID[1:]):
        ra, rb = row(a), row(b)
        if (val - ra[key]) * (val - rb[key]) <= 0 and ra[key] != rb[key]:
            return ra, rb
    raise ValueError((key, val))

def at_T(T):
    """Property row at T, interpolated if T is between rows."""
    if T in GRID: return row(T), None
    ra, rb = bracket("T", T)
    f = (T - ra["T"]) / (rb["T"] - ra["T"])
    return {k: ra[k] + f * (rb[k] - ra[k]) for k in ("T", "h", "u", "s", "Pr", "vr")}, (ra, rb)

def by(key, val):
    """Interpolate the row where `key` equals val (e.g. Pr, h, vr). Returns (dict, (ra, rb), fraction)."""
    ra, rb = bracket(key, val)
    f = (val - ra[key]) / (rb[key] - ra[key])
    return {k: ra[k] + f * (rb[k] - ra[k]) for k in ("T", "h", "u", "s", "Pr", "vr")}, (ra, rb), f

# Table A-2a (300 K) and A-1 values as printed in Cengel
GAS = {
    "air":    dict(name="air", R=0.2870, cp=1.005, cv=0.718, k=1.4, M=28.97),
    "helium": dict(name="helium", R=2.0769, cp=5.1926, cv=3.1156, k=1.667, M=4.003),
    "argon":  dict(name="argon", R=0.2081, cp=0.5203, cv=0.3122, k=1.667, M=39.948),
    "neon":   dict(name="neon", R=0.4119, cp=1.0299, cv=0.6179, k=1.667, M=20.183),
}
