"""Exam 2 guided-problem templates (Ch. 5, 6, 7, 9): 20 templates x 24 variants, eight-step format."""
import json, math, random, itertools
from tables import WATER as W, R as RF, rsig
import a17
from a17 import GAS
from exam2_common import *

AIR, HE = GAS["air"], GAS["helium"]
TEMPLATES = []

def template(tid, title, ch, slot, pts):
    def deco(fn):
        TEMPLATES.append(dict(id=tid, title=title, ch=ch, slot=slot, pts=pts, fn=fn))
        return fn
    return deco

def fP(p): return (f"{p / 1000:g} MPa" if p >= 1000 else f"{p:g} kPa")
def fT(t): return f"{t:g} °C".replace("-", "−")
def pct(x): return 100 * x

# ---------------------------------------------------------------- R-134a superheated helpers
def r_rows(P):
    rows = [dict(RF.shsat(P), sat=True)] + [dict(RF.sh(P, T), sat=False) for T in RF.SH[P]]
    return rows
def r_interp(P, key, val):
    rows = r_rows(P)
    for a, b in zip(rows, rows[1:]):
        if (val - a[key]) * (val - b[key]) <= 0 and a[key] != b[key]:
            f = (val - a[key]) / (b[key] - a[key])
            return {k: a[k] + f * (b[k] - a[k]) for k in ("T", "v", "u", "h", "s")}, a, b
    raise AssertionError((P, key, val))
def rowlab(r): return "Sat." if r.get("sat") else fT(r["T"])

# =================================================================== Ch. 5 single-stream devices
@template("E1", "Steam nozzle that loses heat", 5, "B", 16)
def E1(rng):
    P1 = rng.choice([600, 800, 1000, 1200, 1400]); T1 = rng.choice([300, 350, 400])
    P2 = rng.choice([100, 200, 300]); T2 = rng.choice([t for t in W.SH[P2] if t <= T1 - 100 and t > W.Tsat_true(P2) + 20])
    V1 = rng.choice([5, 8, 10, 12, 15]); A1 = rng.choice([200, 300, 400, 500, 600, 800]); Q = rng.choice([40, 60, 80, 100])
    s1, s2 = W.sh(P1, T1), W.sh(P2, T2)
    m = (A1 / 1e4) * V1 / s1["v"]
    V2 = math.sqrt(V1 ** 2 + 2000 * ((s1["h"] - s2["h"]) - Q / m))
    assert 300 < V2 < 1000
    A2 = m * s2["v"] / V2 * 1e4
    V2noQ = math.sqrt(V1 ** 2 + 2000 * (s1["h"] - s2["h"]))
    stem = (f"Steam enters a nozzle at {fP(P1)} and {fT(T1)} with a velocity of {V1} m/s through an inlet area of {A1} cm². "
            f"It leaves at {fP(P2)} and {fT(T2)}, and the nozzle loses heat to its surroundings at {Q} kW. "
            "Determine (a) the mass flow rate of the steam, (b) the exit velocity, and (c) the exit area.")
    parts = [part("a", "Mass flow rate, ṁ", "kg/s", m, 0.01, 2,
                  [(m * 1e4, "Convert the area: 1 m² = 10,000 cm²."), ((A1 / 1e4) * V1 * s1["v"], "ṁ = A V/v: divide by the specific volume, don't multiply.")]),
             part("b", "Exit velocity, V<sub>2</sub>", "m/s", V2, 0.01, 2, key=[V2noQ], diag=
                  [(math.sqrt(V1 ** 2 + 2 * ((s1["h"] - s2["h"]) - Q / m)), "h is in kJ/kg. Multiply by 1000 to get m²/s² before taking the square root."),
                   (V2noQ, "That leaves out the heat loss. Heat leaving the steam lowers the exit kinetic energy."),
                   (math.sqrt(V1 ** 2 + 2000 * ((s1["h"] - s2["h"]) + Q / m)), "The heat leaves the nozzle, so it subtracts: q<sub>out</sub> = Q̇<sub>out</sub>/ṁ.")]),
             part("c", "Exit area, A<sub>2</sub>", "cm²", A2, 0.015, 2, key=[m * s2["v"] / V2noQ * 1e4], diag=
                  [(A2 / 1e4, "That's in m². Multiply by 10,000 for cm²."), (m * s1["v"] / V2 * 1e4, "Use v<sub>2</sub> at the exit state, not v<sub>1</sub>."), (m * s2["v"] / V2noQ * 1e4, "That uses the exit velocity without the heat loss.")])]
    steps = [self_step("Find the mass flow, exit velocity and exit area for steam in a nozzle that loses heat."),
             open_step("nozzle"),
             assume([f"P<sub>1</sub> = {fP(P1)}, T<sub>1</sub> = {fT(T1)}, V<sub>1</sub> = {V1} m/s, A<sub>1</sub> = {A1} cm²",
                     f"P<sub>2</sub> = {fP(P2)}, T<sub>2</sub> = {fT(T2)}", f"Q̇<sub>out</sub> = {Q} kW"],
                    ["ṁ (kg/s)", "V<sub>2</sub> (m/s)", "A<sub>2</sub> (cm²)"],
                    [("open", True, "Steam flows in and out."), ("steady", True, "The nozzle runs at a steady condition."),
                     ("noshaft", True, "A nozzle has no shaft, wires or moving boundary."), ("nope", True, "A nozzle is short; any height change is tiny."),
                     ("steam", True, "Rule 1: water uses the steam tables. Both states are superheated (Table A-6)."),
                     ("adiabatic", False, "The problem gives a heat loss."), ("lowke", False, "A nozzle exists to raise V. The exit KE is the main result."),
                     ("steamideal", False, "Tables first: never ideal gas for steam (rule 1)."), ("closed", False, "Steam crosses the boundary.")]),
             multi([("ṁ = A<sub>1</sub>V<sub>1</sub>/v<sub>1</sub>", True, ""), (FIRST_SF, True, ""), ("A<sub>2</sub> = ṁv<sub>2</sub>/V<sub>2</sub>", True, ""),
                    ("Pv = RT", False, "Steam comes from the tables, not the ideal-gas law."), ("h<sub>2</sub> = h<sub>1</sub>", False, "That's a throttling valve, where the velocity barely changes."),
                    ("A<sub>1</sub>V<sub>1</sub> = A<sub>2</sub>V<sub>2</sub>", False, "Only if the density stays constant. Steam expands, so use ṁ = AV/v at each end.")], FIRST_SF),
             sf_single({"Qin": (["dir"], "Heat leaves the nozzle."), "Win": (["noshaft"], "No work in a nozzle."), "Wout": (["noshaft"], "No work in a nozzle."),
                        "mpe1": (["nope"], "Same height in and out."), "mpe2": (["nope"], "Same height in and out."), "dE": (["steady"], "Steady operation.")},
                       "ṁ(h<sub>1</sub> + V<sub>1</sub>²/2) − Q̇<sub>out</sub> = ṁ(h<sub>2</sub> + V<sub>2</sub>²/2)"),
             props([("v<sub>1</sub>", s1["v"], "m³/kg", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"), ("h<sub>1</sub>", s1["h"], "kJ/kg", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"),
                    ("v<sub>2</sub>", s2["v"], "m³/kg", "A-6", 0.003, f"{fP(P2)} block, {fT(T2)} row"), ("h<sub>2</sub>", s2["h"], "kJ/kg", "A-6", 0.003, f"{fP(P2)} block, {fT(T2)} row")]),
             calc([f"ṁ = A<sub>1</sub>V<sub>1</sub>/v<sub>1</sub> = ({A1}/10,000)({V1})/{sg(s1['v'], 5)} = <b>{sg(m)} kg/s</b>",
                   f"q<sub>out</sub> = Q̇<sub>out</sub>/ṁ = {Q}/{sg(m)} = {sg(Q / m)} kJ/kg",
                   f"V<sub>2</sub> = √[V<sub>1</sub>² + 2(h<sub>1</sub> − h<sub>2</sub> − q<sub>out</sub>)(1000 m²/s² per kJ/kg)] = √[{V1}² + 2000({num(s1['h'], 1)} − {num(s2['h'], 1)} − {sg(Q / m)})] = <b>{sg(V2)} m/s</b>",
                   f"A<sub>2</sub> = ṁv<sub>2</sub>/V<sub>2</sub> = ({sg(m)})({sg(s2['v'], 5)})/{sg(V2)} = {sg(A2 / 1e4)} m² = <b>{sg(A2)} cm²</b>"]),
             mc(8, f"Without the heat loss, V<sub>2</sub> would be about {sg(V2noQ)} m/s. Where should your answer sit?",
                [f"A little below {sg(V2noQ)} m/s: heat leaving the steam takes energy that would have become kinetic energy",
                 f"Above {sg(V2noQ)} m/s: the heat loss speeds the steam up", f"Exactly {sg(V2noQ)} m/s: heat doesn't affect velocity", "Below the inlet velocity"],
                0, "Heat leaving lowers the energy available for kinetic energy, so V<sub>2</sub> comes in a bit under the no-loss value. An answer above it has the heat term's sign flipped.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E2", "Helium compressor that loses heat", 5, "B", 16)
def E2(rng):
    P1 = rng.choice([100, 105, 110, 120]); T1 = rng.choice([290, 295, 300]); P2 = rng.choice([500, 600, 700, 800])
    T2 = rng.choice([430, 440, 450, 460, 470, 480]); q = rng.choice([10, 12, 15, 18, 20]); mmin = rng.choice([30, 45, 60, 75, 90])
    m = mmin / 60
    w = HE["cp"] * (T2 - T1) + q; Wd = m * w; Vd = m * HE["R"] * T1 / P1
    stem = (f"Helium is compressed steadily from {P1} kPa and {T1} K to {P2} kPa and {T2} K. The compressor loses {q} kJ/kg of heat to its surroundings, "
            f"and the mass flow rate is {mmin} kg/min. Determine (a) the work input per kilogram, (b) the power input, and (c) the volume flow rate at the inlet.")
    parts = [part("a", "Work input per kilogram, w<sub>in</sub>", "kJ/kg", w, 0.01, 2,
                  [(HE["cv"] * (T2 - T1) + q, "Steady flow carries flow work, so use c<sub>p</sub> (Δh), not c<sub>v</sub>."),
                   (HE["cp"] * (T2 - T1) - q, "Heat leaves, so the compressor must supply it too: add q<sub>out</sub>."),
                   (1.005 * (T2 - T1) + q, "1.005 is air's c<sub>p</sub>. Helium's is 5.1926 kJ/kg·K (A-2a).")]),
             part("b", "Power input, Ẇ<sub>in</sub>", "kW", Wd, 0.01, 2, [(Wd * 60, "Convert kg/min to kg/s first.")]),
             part("c", "Inlet volume flow rate, V̇<sub>1</sub>", "m³/s", Vd, 0.01, 2,
                  [(m * 0.287 * T1 / P1, "Use helium's gas constant, R = 2.0769 kJ/kg·K, not air's."), (Vd * 60, "Convert kg/min to kg/s first.")])]
    steps = [self_step("Find the work per kilogram, the power, and the inlet volume flow for a helium compressor that loses heat."),
             open_step("compressor"),
             assume([f"P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {T1} K", f"P<sub>2</sub> = {P2} kPa, T<sub>2</sub> = {T2} K", f"q<sub>out</sub> = {q} kJ/kg", f"ṁ = {mmin} kg/min"],
                    ["w<sub>in</sub> (kJ/kg)", "Ẇ<sub>in</sub> (kW)", "V̇<sub>1</sub> (m³/s)"],
                    [("open", True, "Helium flows in and out."), ("steady", True, "Steady operation."),
                     ("ideal", True, "Helium at about 100 to 800 kPa and 300 K is far above its critical temperature (5.2 K): Z ≈ 1 (rule 2)."),
                     ("noble", True, "Rule 3: helium is a noble gas, so constant c<sub>p</sub> is exact even over 150+ K."),
                     ("lowke", True, "No velocities given; KE changes across a compressor are small."), ("nope", True, "Same height in and out."),
                     ("adiabatic", False, "The problem gives a heat loss."), ("a17", False, "A-17 is for air. Helium's c<sub>p</sub> doesn't change with T."),
                     ("isothermal", False, "The temperature rises from {0} K to {1} K.".format(T1, T2))]),
             multi([(FIRST_SF, True, ""), ("Δh = c<sub>p</sub>ΔT", True, ""), ("V̇ = ṁRT/P", True, ""),
                    ("Δu = c<sub>v</sub>ΔT", False, "Steady flow uses h, which includes the flow work, so it needs c<sub>p</sub>."),
                    ("T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>", False, "That's for an isentropic process. This one loses heat, and both temperatures are given.")], FIRST_SF),
             sf_single({"Qin": (["dir"], "Heat leaves."), "Wout": (["dir"], "Work goes in."), "mke1": (["lowke"], "KE changes are small."), "mke2": (["lowke"], "KE changes are small."),
                        "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."), "dE": (["steady"], "Steady operation.")},
                       "Ẇ<sub>in</sub> = ṁ(h<sub>2</sub> − h<sub>1</sub>) + Q̇<sub>out</sub> = ṁ[c<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>) + q<sub>out</sub>]"),
             props([("c<sub>p</sub> for helium", HE["cp"], "kJ/kg·K", "A-2a", 0.003, "helium"), ("R for helium", HE["R"], "kJ/kg·K", "A-1", 0.003, "helium")]),
             calc([f"w<sub>in</sub> = c<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>) + q<sub>out</sub> = (5.1926)({T2} − {T1}) + {q} = <b>{sg(w)} kJ/kg</b>",
                   f"ṁ = {mmin}/60 = {sg(m)} kg/s",
                   f"Ẇ<sub>in</sub> = ṁw<sub>in</sub> = ({sg(m)})({sg(w)}) = <b>{sg(Wd)} kW</b>",
                   f"V̇<sub>1</sub> = ṁRT<sub>1</sub>/P<sub>1</sub> = ({sg(m)})(2.0769)({T1})/{P1} = <b>{sg(Vd)} m³/s</b>"]),
             mc(8, "Compare w<sub>in</sub> with c<sub>p</sub>ΔT alone. Which should be bigger?",
                ["w<sub>in</sub>, by exactly q<sub>out</sub>: the compressor pays for the heat that leaks out", "c<sub>p</sub>ΔT: heat loss reduces the work",
                 "They're equal: heat doesn't enter the balance", "Can't tell without the pressure ratio"],
                0, "Energy in as work must cover both the enthalpy rise and the heat that escapes.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E3", "Steam turbine with fast exhaust", 5, "B", 16)
def E3(rng):
    P1 = rng.choice([3000, 5000, 8000, 10000]); T1 = rng.choice([400, 450, 500, 600])
    P2 = rng.choice([10, 15, 20, 25, 50]); x = rng.choice([0.88, 0.90, 0.92, 0.94, 0.95])
    V1 = rng.choice([30, 40, 50, 60]); V2 = rng.choice([150, 180, 200]); m = rng.choice([8, 10, 12, 15, 20])
    s1 = W.sh(P1, T1); st = W.satP(P2)
    h2 = st["hf"] + x * st["hfg"]; v2 = st["vf"] + x * (st["vg"] - st["vf"])
    Wd = m * ((s1["h"] - h2) + (V1 ** 2 - V2 ** 2) / 2000); A2 = m * v2 / V2
    assert Wd > 0
    stem = (f"Steam enters an adiabatic turbine at {fP(P1)} and {fT(T1)} with a velocity of {V1} m/s, and leaves at {fP(P2)} with a quality of {x} and a velocity of {V2} m/s. "
            f"The mass flow rate is {m} kg/s. Determine (a) the exit enthalpy, (b) the power output, and (c) the exit area.")
    parts = [part("a", "Exit enthalpy, h<sub>2</sub>", "kJ/kg", h2, 0.005, 2,
                  [(x * st["hg"], "h = h<sub>f</sub> + x h<sub>fg</sub>. The liquid part carries h<sub>f</sub> too."), (st["hf"] + (1 - x) * st["hfg"], "Quality multiplies h<sub>fg</sub>: x is the vapor fraction.")]),
             part("b", "Power output, Ẇ<sub>out</sub>", "kW", Wd, 0.01, 2, key=[m * (s1["h"] - h2)], diag=
                  [(m * (s1["h"] - h2), "That leaves out the kinetic-energy change. The exhaust leaves fast enough to matter here."),
                   (m * ((s1["h"] - h2) + (V1 ** 2 - V2 ** 2) / 2), "V²/2 is in m²/s² = J/kg. Divide by 1000 to get kJ/kg."),
                   (m * ((s1["h"] - h2) - (V1 ** 2 - V2 ** 2) / 2000), "KE leaving the turbine is energy that didn't become work: ΔKE reduces the power.")]),
             part("c", "Exit area, A<sub>2</sub>", "m²", A2, 0.01, 2,
                  [(m * s1["v"] / V2, "Use v<sub>2</sub> at the exit state, not v<sub>1</sub>."), (m * st["vg"] / V2, "The exit is a mixture: v<sub>2</sub> = v<sub>f</sub> + x(v<sub>g</sub> − v<sub>f</sub>), not v<sub>g</sub>.")])]
    steps = [self_step("Find the exit enthalpy, power output and exit area for an adiabatic steam turbine with a fast exhaust."),
             open_step("turbine"),
             assume([f"P<sub>1</sub> = {fP(P1)}, T<sub>1</sub> = {fT(T1)}, V<sub>1</sub> = {V1} m/s", f"P<sub>2</sub> = {fP(P2)}, x<sub>2</sub> = {x}, V<sub>2</sub> = {V2} m/s", f"ṁ = {m} kg/s"],
                    ["h<sub>2</sub> (kJ/kg)", "Ẇ<sub>out</sub> (kW)", "A<sub>2</sub> (m²)"],
                    [("open", True, "Steam flows through."), ("steady", True, "Steady operation."), ("adiabatic", True, "The problem says adiabatic."),
                     ("nope", True, "Same height in and out."), ("steam", True, "Rule 1: superheated inlet (A-6), mixture exit (A-5)."),
                     ("lowke", False, "Both velocities are given and the exhaust is fast: keep the KE terms."),
                     ("steamideal", False, "Never ideal gas for steam (rule 1)."), ("isen", False, "Not needed: the exit state is given (x<sub>2</sub>).")]),
             multi([(FIRST_SF, True, ""), ("h<sub>2</sub> = h<sub>f</sub> + x h<sub>fg</sub>", True, ""), ("A<sub>2</sub> = ṁv<sub>2</sub>/V<sub>2</sub>", True, ""),
                    ("s<sub>2</sub> = s<sub>1</sub>", False, "Nothing says the turbine is reversible, and the exit state is already fixed by P<sub>2</sub> and x<sub>2</sub>."),
                    ("Ẇ = ṁc<sub>p</sub>ΔT", False, "Steam uses the tables, not cΔT (rule 1).")], FIRST_SF),
             sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Win": (["dir"], "Work comes out."),
                        "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."), "dE": (["steady"], "Steady operation.")},
                       "Ẇ<sub>out</sub> = ṁ[(h<sub>1</sub> − h<sub>2</sub>) + (V<sub>1</sub>² − V<sub>2</sub>²)/2]"),
             props([("h<sub>1</sub>", s1["h"], "kJ/kg", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"), ("h<sub>f</sub> at P<sub>2</sub>", st["hf"], "kJ/kg", "A-5", 0.003, fP(P2)),
                    ("h<sub>fg</sub> at P<sub>2</sub>", st["hfg"], "kJ/kg", "A-5", 0.003, fP(P2)), ("v<sub>f</sub> at P<sub>2</sub>", st["vf"], "m³/kg", "A-5", 0.003, fP(P2)), ("v<sub>g</sub> at P<sub>2</sub>", st["vg"], "m³/kg", "A-5", 0.003, fP(P2))]),
             calc([f"h<sub>2</sub> = h<sub>f</sub> + x h<sub>fg</sub> = {num(st['hf'], 2)} + {x}({num(st['hfg'], 1)}) = <b>{sg(h2, 5)} kJ/kg</b>",
                   f"ΔKE = (V<sub>1</sub>² − V<sub>2</sub>²)/2 = ({V1}² − {V2}²)/2000 = {sg((V1 ** 2 - V2 ** 2) / 2000)} kJ/kg",
                   f"Ẇ<sub>out</sub> = {m}[({num(s1['h'], 1)} − {sg(h2, 5)}) + ({sg((V1 ** 2 - V2 ** 2) / 2000)})] = <b>{sg(Wd)} kW</b>",
                   f"v<sub>2</sub> = v<sub>f</sub> + x(v<sub>g</sub> − v<sub>f</sub>) = {num(st['vf'], 6)} + {x}({sg(st['vg'], 5)} − {num(st['vf'], 6)}) = {sg(v2)} m³/kg",
                   f"A<sub>2</sub> = ṁv<sub>2</sub>/V<sub>2</sub> = ({m})({sg(v2)})/{V2} = <b>{sg(A2)} m²</b>"]),
             mc(8, "How big is the kinetic-energy term next to h<sub>1</sub> − h<sub>2</sub>?",
                [f"Small, about {abs((V1 ** 2 - V2 ** 2) / 2000) / (s1['h'] - h2) * 100:.0f}% of it: noticeable, but the enthalpy drop does almost all the work",
                 "Larger than the enthalpy drop", "Exactly zero, because the turbine is adiabatic", "About half of it"],
                0, "Exhaust velocities of 100 to 200 m/s carry 5 to 20 kJ/kg, against an enthalpy drop of several hundred. It's worth keeping, but a KE term bigger than the enthalpy drop would mean a units slip (forgetting the 1000).")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E4", "Jet-engine inlet diffuser", 5, "B", 16)
def E4(rng):
    T1c = rng.choice([-30, -20, -10, 0, 10]); P1 = rng.choice([60, 70, 80, 90]); V1 = rng.choice([200, 220, 240, 260, 280])
    V2 = rng.choice([40, 50, 60, 80]); A1 = rng.choice([0.3, 0.4, 0.5, 0.6])
    T1 = K(T1c); T2 = T1 + (V1 ** 2 - V2 ** 2) / (2000 * AIR["cp"])
    P2 = round(P1 * (T2 / T1) ** 3.5 * rng.choice([0.95, 0.97, 0.98]))
    m = P1 * A1 * V1 / (AIR["R"] * T1); A2 = m * AIR["R"] * T2 / (P2 * V2)
    stem = (f"Air at {P1} kPa and {fT(T1c)} enters an aircraft engine's adiabatic diffuser at {V1} m/s through an inlet area of {A1} m². "
            f"It leaves at {P2} kPa with a velocity of {V2} m/s. Determine (a) the mass flow rate of the air, (b) the exit temperature in kelvins, and (c) the exit area.")
    parts = [part("a", "Mass flow rate, ṁ", "kg/s", m, 0.01, 2, [(P1 * A1 * V1 / (AIR["R"] * T1c) if T1c else None, "Use kelvins in Pv = RT.")]),
             part("b", "Exit temperature, T<sub>2</sub>", "K", T2, 0.005, 2,
                  [(T1 + (V1 ** 2 - V2 ** 2) / (2000 * AIR["cv"]), "Steady flow uses Δh = c<sub>p</sub>ΔT, not c<sub>v</sub>."),
                   (T1 + (V1 ** 2 - V2 ** 2) / (2 * AIR["cp"]), "V²/2 is in J/kg. Divide by 1000 to match c<sub>p</sub> in kJ/kg·K."),
                   (T1 - (V1 ** 2 - V2 ** 2) / (2000 * AIR["cp"]), "The air slows down, so its temperature rises.")]),
             part("c", "Exit area, A<sub>2</sub>", "m²", A2, 0.015, 2,
                  [(m * AIR["R"] * T1 / (P1 * V2), "Use the exit state, T<sub>2</sub> and P<sub>2</sub>, for v<sub>2</sub>."), (A1 * V1 / V2, "The density changes: use ṁ = A<sub>2</sub>V<sub>2</sub>/v<sub>2</sub>.")])]
    dT = T2 - T1
    steps = [self_step("Find the mass flow, exit temperature and exit area of air slowing down in an adiabatic diffuser."),
             open_step("diffuser"),
             assume([f"P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {fT(T1c)}, V<sub>1</sub> = {V1} m/s, A<sub>1</sub> = {A1} m²", f"P<sub>2</sub> = {P2} kPa, V<sub>2</sub> = {V2} m/s"],
                    ["ṁ (kg/s)", "T<sub>2</sub> (K)", "A<sub>2</sub> (m²)"],
                    [("open", True, "Air flows through."), ("steady", True, "Steady operation."), ("adiabatic", True, "Given."), ("noshaft", True, "A diffuser has no shaft or wires."),
                     ("nope", True, "Same height."), ("ideal", True, "Air at low pressure, far above its critical temperature (132.5 K): Z ≈ 1 (rule 2)."),
                     ("constc", True, f"Rule 4: the air warms only about {dT:.0f} K near room temperature, a small ΔT."),
                     ("lowke", False, "Slowing the air is the diffuser's whole job: the KE change is the main term."),
                     ("a17", False, f"The temperature changes only about {dT:.0f} K, so constant c is the course rule.")]),
             multi([("ṁ = PAV/(RT)", True, ""), (FIRST_SF, True, ""), ("Δh = c<sub>p</sub>ΔT", True, ""),
                    ("A<sub>1</sub>V<sub>1</sub> = A<sub>2</sub>V<sub>2</sub>", False, "Only for constant density. Air is compressed in a diffuser."),
                    ("Δu = c<sub>v</sub>ΔT", False, "Steady flow uses h.")], FIRST_SF),
             sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Win": (["noshaft"], "No work."), "Wout": (["noshaft"], "No work."),
                        "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."), "dE": (["steady"], "Steady operation.")},
                       "h<sub>1</sub> + V<sub>1</sub>²/2 = h<sub>2</sub> + V<sub>2</sub>²/2, so T<sub>2</sub> = T<sub>1</sub> + (V<sub>1</sub>² − V<sub>2</sub>²)/(2c<sub>p</sub>)"),
             props([("R for air", AIR["R"], "kJ/kg·K", "A-1", 0.003, "air"), ("c<sub>p</sub> for air", AIR["cp"], "kJ/kg·K", "A-2a", 0.003, "air, 300 K")]),
             calc([f"T<sub>1</sub> = {fT(T1c)} = {sg(T1, 5)} K",
                   f"ṁ = P<sub>1</sub>A<sub>1</sub>V<sub>1</sub>/(RT<sub>1</sub>) = ({P1})({A1})({V1})/[(0.287)({sg(T1, 5)})] = <b>{sg(m)} kg/s</b>",
                   f"T<sub>2</sub> = T<sub>1</sub> + (V<sub>1</sub>² − V<sub>2</sub>²)/(2c<sub>p</sub>) = {sg(T1, 5)} + ({V1}² − {V2}²)/[(2)(1.005)(1000)] = <b>{sg(T2, 5)} K</b> ({sg(T2 - 273.15, 3)} °C)",
                   f"A<sub>2</sub> = ṁRT<sub>2</sub>/(P<sub>2</sub>V<sub>2</sub>) = ({sg(m)})(0.287)({sg(T2, 5)})/[({P2})({V2})] = <b>{sg(A2)} m²</b>"]),
             mc(8, "The air slows from " + f"{V1} to {V2} m/s. Which result makes sense?",
                [f"A temperature rise of roughly {dT:.0f} K and an exit area larger than the inlet", "A temperature drop, because the air expands",
                 "A rise of thousands of kelvins", "An exit area smaller than the inlet"],
                0, f"Kinetic energy turns into enthalpy: about (V²/2)/c<sub>p</sub> ≈ {dT:.0f} K. A slower flow of denser air still needs a bigger area. Thousands of kelvins means the 1000 was dropped.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E5", "R-134a through an expansion valve", 5, "B", 16)
def E5(rng):
    P2 = rng.choice([100, 120, 140, 160, 180, 200, 240]); m = rng.choice([0.02, 0.03, 0.05, 0.08, 0.10])
    kind = rng.choice(["sat", "sat", "sub"])
    if kind == "sat":
        P1 = rng.choice([600, 700, 800, 900, 1000, 1200]); s1 = RF.satP(P1); h1 = s1["hf"]; inlet = f"saturated liquid at {fP(P1)}"
        row1 = ("h<sub>1</sub> = h<sub>f</sub> at P<sub>1</sub>", h1, "kJ/kg", "A-12", 0.003, fP(P1)); T1 = s1["T"]
        why1 = f"Inlet is saturated liquid: h<sub>1</sub> = h<sub>f</sub>@{fP(P1)} = {num(h1, 2)} kJ/kg"
    else:
        P1 = rng.choice([800, 900, 1000, 1200]); Ts = RF.Tsat_true(P1)
        T1 = rng.choice([t for t in RF.T_GRID if Ts - 12 <= t <= Ts - 3]); h1 = RF.satT(T1)["hf"]; inlet = f"subcooled liquid at {fP(P1)} and {fT(T1)}"
        row1 = ("h<sub>1</sub> ≈ h<sub>f</sub>@T<sub>1</sub>", h1, "kJ/kg", "A-11", 0.003, fT(T1))
        why1 = f"Inlet: {fT(T1)} is below T<sub>sat</sub>@{fP(P1)} = {num(RF.satP(P1)['T'], 2)} °C, so it is subcooled liquid: h<sub>1</sub> ≈ h<sub>f</sub>@{fT(T1)} = {num(h1, 2)} kJ/kg"
    st = RF.satP(P2)
    x = (h1 - st["hf"]) / st["hfg"]; T2 = st["T"]; v2 = st["vf"] + x * (st["vg"] - st["vf"]); Vd = m * v2 * 1000
    stem = (f"R-134a enters an expansion valve as {inlet} and leaves at {fP(P2)}. The mass flow rate is {m} kg/s. "
            "Determine (a) the quality at the exit, (b) the exit temperature, and (c) the volume flow rate at the exit, in L/s.")
    parts = [part("a", "Exit quality, x<sub>2</sub>", "", x, 0.01, 2, [(1 - x, "That's 1 − x, the liquid fraction."), (h1 / st["hg"], "That's h/h<sub>g</sub>. Subtract h<sub>f</sub> first, then divide by h<sub>fg</sub>.")]),
             part("b", "Exit temperature, T<sub>2</sub>", "°C", T2, 0.01, 2, [(T1, "The temperature doesn't stay the same: the valve drops it to T<sub>sat</sub> at the exit pressure.")]),
             part("c", "Exit volume flow rate, V̇<sub>2</sub>", "L/s", Vd, 0.015, 2, [(m * st["vg"] * 1000, "The exit is a mixture: v<sub>2</sub> = v<sub>f</sub> + x(v<sub>g</sub> − v<sub>f</sub>).")])]
    steps = [self_step("Find the exit quality, temperature and volume flow of R-134a leaving an expansion valve."),
             open_step("valve"),
             assume([f"Inlet: {inlet}", f"P<sub>2</sub> = {fP(P2)}", f"ṁ = {m} kg/s"], ["x<sub>2</sub>", "T<sub>2</sub> (°C)", "V̇<sub>2</sub> (L/s)"],
                    [("open", True, "Refrigerant flows through."), ("steady", True, "Steady operation."), ("adiabatic", True, "A valve is small; little heat crosses in the short time the fluid spends inside."),
                     ("noshaft", True, "A valve has no shaft or wires."), ("lowke", True, "Velocities in and out are similar."), ("nope", True, "Same height."),
                     ("r134", True, "Rule 1: R-134a tables."), ("isothermal", False, "The temperature drops sharply through the valve."),
                     ("r134ideal", False, "Never ideal gas for R-134a (rule 1)."), ("isen", False, "A throttle is highly irreversible: h stays the same, s rises.")]
                    + ([("liqTr", True, "Rule 1, compressed liquid: no compressed-liquid table for R-134a.")] if kind == "sub" else [])),
             multi([(FIRST_SF, True, ""), ("x = (h − h<sub>f</sub>)/h<sub>fg</sub>", True, ""), ("V̇ = ṁv", True, ""),
                    ("s<sub>2</sub> = s<sub>1</sub>", False, "That's an isentropic device. A valve keeps h, not s."), ("Pv = RT", False, "R-134a uses its tables.")], FIRST_SF),
             sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Win": (["noshaft"], "No work."), "Wout": (["noshaft"], "No work."),
                        "mke1": (["lowke"], "Similar velocities."), "mke2": (["lowke"], "Similar velocities."), "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."),
                        "dE": (["steady"], "Steady operation.")}, "h<sub>2</sub> = h<sub>1</sub>"),
             props([row1, ("h<sub>f</sub> at P<sub>2</sub>", st["hf"], "kJ/kg", "A-12", 0.003, fP(P2)), ("h<sub>fg</sub> at P<sub>2</sub>", st["hfg"], "kJ/kg", "A-12", 0.003, fP(P2)),
                    ("T<sub>sat</sub> at P<sub>2</sub>", st["T"], "°C", "A-12", 0.003, fP(P2)), ("v<sub>f</sub> at P<sub>2</sub>", st["vf"], "m³/kg", "A-12", 0.003, fP(P2)), ("v<sub>g</sub> at P<sub>2</sub>", st["vg"], "m³/kg", "A-12", 0.003, fP(P2))]),
             calc([why1, f"h<sub>2</sub> = h<sub>1</sub>. At {fP(P2)}: h<sub>f</sub> = {num(st['hf'], 2)} &lt; h<sub>2</sub> &lt; h<sub>g</sub> = {num(st['hg'], 2)}, so it's a mixture",
                   f"x<sub>2</sub> = (h<sub>2</sub> − h<sub>f</sub>)/h<sub>fg</sub> = ({num(h1, 2)} − {num(st['hf'], 2)})/{num(st['hfg'], 2)} = <b>{sg(x)}</b>",
                   f"T<sub>2</sub> = T<sub>sat</sub>@{fP(P2)} = <b>{num(T2, 2)} °C</b>",
                   f"v<sub>2</sub> = v<sub>f</sub> + x(v<sub>g</sub> − v<sub>f</sub>) = {num(st['vf'], 7)} + {sg(x)}({sg(st['vg'], 5)} − {num(st['vf'], 7)}) = {sg(v2)} m³/kg",
                   f"V̇<sub>2</sub> = ṁv<sub>2</sub> = ({m})({sg(v2)}) = {sg(Vd / 1000)} m³/s = <b>{sg(Vd)} L/s</b>"]),
             mc(8, "Most of the exit stream is still liquid, yet its temperature fell by tens of degrees. What did that?",
                ["A small part of the liquid boiled (flashed); the energy to boil it came from cooling the rest down to T<sub>sat</sub> at the low pressure",
                 "The valve removed heat", "The valve did work on the fluid", "The temperature only looks lower because of the units"],
                0, "With h fixed, the only way to reach the low-pressure saturation state is for some liquid to evaporate. That flash is why an expansion valve makes the cold stream in a refrigerator.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

# =================================================================== Ch. 5 multi-stream
def hx_terms(names_in, names_out, res, qreason="shell", ke=("lowke", "nope")):
    t = [term("Qin", "Q̇<sub>in</sub>", "L", "+", True, [qreason], "No heat lost to the surroundings." if qreason == "shell" else "Insulated: no heat to the surroundings."),
         term("Win", "Ẇ<sub>in</sub>", "L", "+", True, ["noshaft"], "No work.")]
    for i, h in enumerate(names_in):
        t.append(term(f"in{i}", h, "L", "+"))
    t.append(term("kein", "∑ṁ(V²/2 + gz)<sub>in</sub>", "L", "+", True, list(ke), "Small velocities, same height."))
    t.append(term("Qout", "Q̇<sub>out</sub>", "L", "−", True, [qreason], "No heat lost to the surroundings." if qreason == "shell" else "Insulated: no heat to the surroundings."))
    t.append(term("Wout", "Ẇ<sub>out</sub>", "L", "−", True, ["noshaft"], "No work."))
    for i, h in enumerate(names_out):
        t.append(term(f"out{i}", h, "L", "−"))
    t.append(term("keout", "∑ṁ(V²/2 + gz)<sub>out</sub>", "L", "−", True, list(ke), "Small velocities, same height."))
    t.append(term("dE", "dE<sub>cv</sub>/dt", "R", "", True, ["steady"], "Steady operation."))
    return strike_custom(t, res)

HX_SYS = ["The whole heat exchanger, both streams inside: the heat passed between them stays inside the boundary",
          "Only the hot stream, with Q̇ = 0 because the shell is insulated",
          "Only the cold stream, with work going in", "A closed system made of the tubes"]
HX_W = ("With the whole exchanger as the system, the heat passing from one stream to the other is internal, and no heat is lost to the surroundings. "
        "If you pick one stream alone, Q̇ is not zero: it's the heat crossing the tube wall.")

@template("E6", "Power-plant condenser cooled by river water", 5, "C", 16)
def E6(rng):
    P = rng.choice([10, 15, 20, 25, 30, 40, 50]); x = rng.choice([0.85, 0.88, 0.90, 0.92, 0.95])
    T3 = rng.choice([10, 15, 20]); T4 = T3 + rng.choice([5, 10]); mw = rng.choice([60, 80, 100, 120, 150])
    st = W.satP(P); h1 = st["hf"] + x * st["hfg"]; h2 = st["hf"]; h3 = W.satT(T3)["hf"]; h4 = W.satT(T4)["hf"]
    Q = mw * (h4 - h3); ms = Q / (h1 - h2)
    assert T4 < st["T"] - 3
    stem = (f"Steam leaves a power plant's turbine and enters the condenser at {fP(P)} with a quality of {x}. It leaves as saturated liquid at the same pressure, and the condenser is well insulated. "
            f"River water enters the condenser tubes at {fT(T3)} at a rate of {mw} kg/s and leaves at {fT(T4)}. "
            "Determine (a) the rate of heat transfer to the river water and (b) the mass flow rate of the steam.")
    parts = [part("a", "Heat transfer rate to the river water, Q̇", "kW", Q, 0.01, 3, []),
             part("b", "Steam mass flow rate, ṁ<sub>s</sub>", "kg/s", ms, 0.01, 3,
                  [(Q / st["hfg"], "The steam enters with x = " + f"{x}" + ", so it releases x h<sub>fg</sub> per kg, not all of h<sub>fg</sub>."),
                   (Q / (h1 - h3), "The steam leaves as saturated liquid at its own pressure (h<sub>f</sub>@P), not at the river temperature.")])]
    ctx = {"t": "Where does the heat go?",
           "b": "Every steam power plant rejects heat. With once-through cooling it goes into a river, lake or bay, and warmer water holds less dissolved oxygen, which stresses fish. Discharge permits cap how warm the returned water can be, and in hot, dry summers some plants have had to cut their output because the river was already too warm.",
           "q": f"In this problem the river water warms by {T4 - T3} °C. Who should have a say in how much a river can be warmed: the plant, regulators, tribes and fishing communities downstream, or the people who need the power during a heat wave?", "src": None}
    steps = [self_step("Find the heat rejected to the river and the steam flow rate in a power-plant condenser."),
             mc(2, "What system makes this problem simplest?", HX_SYS, 0, HX_W),
             assume([f"Steam: P = {fP(P)}, x<sub>1</sub> = {x}; leaves as saturated liquid", f"River water: T<sub>3</sub> = {fT(T3)}, T<sub>4</sub> = {fT(T4)}, ṁ<sub>w</sub> = {mw} kg/s"],
                    ["Q̇ (kW)", "ṁ<sub>s</sub> (kg/s)"],
                    [("open", True, "Two streams flow through."), ("steady", True, "Steady operation."), ("shell", True, "Heat goes only from steam to river water."),
                     ("noshaft", True, "No shaft or wires."), ("lowke", True, "Velocities are small."), ("nope", True, "Height changes are small."),
                     ("steam", True, "Rule 1: the steam side uses Table A-5."), ("liqT", True, "Rule 1: river water is a compressed liquid, h ≈ h<sub>f</sub>@T (Table A-4)."),
                     ("cpwater", False, "Tables first for water, liquid included (rule 1)."), ("closed", False, "Both streams cross the boundary.")]),
             multi([(FIRST_SF, True, ""), ("ṁ<sub>1</sub> = ṁ<sub>2</sub> and ṁ<sub>3</sub> = ṁ<sub>4</sub>", True, ""), ("h = h<sub>f</sub> + x h<sub>fg</sub>", True, ""),
                    ("Q̇ = ṁcΔT for the river water", False, "Rule 1: water uses its tables, h<sub>f</sub>@T."),
                    ("ṁ<sub>s</sub> = ṁ<sub>w</sub>", False, "The two streams never mix, and they have different flow rates.")], FIRST_SF),
             hx_terms(["ṁ<sub>s</sub>h<sub>1</sub>", "ṁ<sub>w</sub>h<sub>3</sub>"], ["ṁ<sub>s</sub>h<sub>2</sub>", "ṁ<sub>w</sub>h<sub>4</sub>"],
                      "ṁ<sub>s</sub>(h<sub>1</sub> − h<sub>2</sub>) = ṁ<sub>w</sub>(h<sub>4</sub> − h<sub>3</sub>) = Q̇"),
             props([("h<sub>f</sub> at P", st["hf"], "kJ/kg", "A-5", 0.003, fP(P)), ("h<sub>fg</sub> at P", st["hfg"], "kJ/kg", "A-5", 0.003, fP(P)),
                    ("h<sub>3</sub> = h<sub>f</sub>@T<sub>3</sub>", h3, "kJ/kg", "A-4", 0.003, fT(T3)), ("h<sub>4</sub> = h<sub>f</sub>@T<sub>4</sub>", h4, "kJ/kg", "A-4", 0.003, fT(T4))]),
             calc([f"Q̇ = ṁ<sub>w</sub>(h<sub>4</sub> − h<sub>3</sub>) = {mw}({num(h4, 2)} − {num(h3, 2)}) = <b>{sg(Q)} kW</b>",
                   f"h<sub>1</sub> = h<sub>f</sub> + x h<sub>fg</sub> = {num(st['hf'], 2)} + {x}({num(st['hfg'], 1)}) = {sg(h1, 5)} kJ/kg; h<sub>2</sub> = h<sub>f</sub> = {num(h2, 2)} kJ/kg",
                   f"ṁ<sub>s</sub> = Q̇/(h<sub>1</sub> − h<sub>2</sub>) = {sg(Q)}/({sg(h1, 5)} − {num(h2, 2)}) = <b>{sg(ms)} kg/s</b>"]),
             mc(8, "The steam flow is much smaller than the river-water flow. Why?",
                ["Each kilogram of steam gives up roughly 2000 kJ as it condenses, while each kilogram of river water warms only 5 to 10 °C, absorbing about 20 to 40 kJ",
                 "Steam is less dense than water", "Some steam escapes", "The condenser stores energy"],
                0, "Condensing releases the latent heat, about 50 to 100 times what a few degrees of warming absorbs. A steam flow bigger than the water flow would mean a slip in h<sub>1</sub> or h<sub>2</sub>.")]
    return stem, parts, steps, ctx, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E7", "Open feedwater heater (mixing chamber)", 5, "C", 16)
def E7(rng):
    P = rng.choice([200, 300, 400, 600, 800]); T1 = rng.choice([t for t in W.SH[P] if t <= 350 and t > W.Tsat_true(P) + 20])
    T2 = rng.choice([15, 20, 30, 40, 50, 60]); m2 = rng.choice([1, 1.5, 2, 3, 4, 5])
    s1 = W.sh(P, T1); h2 = W.satT(T2)["hf"]; st = W.satP(P); h3 = st["hf"]
    y = (h3 - h2) / (s1["h"] - h3); m1 = y * m2; T3 = st["T"]
    stem = (f"In an open feedwater heater, superheated steam at {fP(P)} and {fT(T1)} mixes with liquid water at {fT(T2)} and the same pressure. "
            f"The mixture leaves as saturated liquid at {fP(P)}. The liquid water flow is {m2} kg/s. "
            "Determine (a) the steam needed per kilogram of liquid water, (b) the steam mass flow rate, and (c) the exit temperature.")
    parts = [part("a", "Steam per kg of liquid water, ṁ<sub>1</sub>/ṁ<sub>2</sub>", "", y, 0.01, 2, [(1 / y, "That's ṁ<sub>2</sub>/ṁ<sub>1</sub>: the ratio is upside down.")]),
             part("b", "Steam mass flow rate, ṁ<sub>1</sub>", "kg/s", m1, 0.01, 2, [(m2 / y, "Your ratio is upside down (ṁ<sub>2</sub>/ṁ<sub>1</sub>). Use ṁ<sub>1</sub>/ṁ<sub>2</sub> = (h<sub>3</sub> − h<sub>2</sub>)/(h<sub>1</sub> − h<sub>3</sub>).")]),
             part("c", "Exit temperature, T<sub>3</sub>", "°C", T3, 0.005, 2,
                  [((m1 * T1 + m2 * T2) / (m1 + m2), "Temperatures don't average when one stream condenses. The exit is saturated liquid at P, so T<sub>3</sub> = T<sub>sat</sub>.")])]
    steps = [self_step("Find the steam needed, the steam flow and the exit temperature in an open feedwater heater."),
             mc(2, "Which mass balance applies?", ["ṁ<sub>1</sub> + ṁ<sub>2</sub> = ṁ<sub>3</sub>", "ṁ<sub>1</sub> = ṁ<sub>2</sub> = ṁ<sub>3</sub>",
                                                    "ṁ<sub>3</sub> = ṁ<sub>1</sub> − ṁ<sub>2</sub>", "No mass balance: it's a closed system"],
                0, "Two streams in, one out, steady: what goes in comes out."),
             assume([f"Steam: {fP(P)}, {fT(T1)}", f"Liquid: {fT(T2)}, ṁ<sub>2</sub> = {m2} kg/s", f"Exit: saturated liquid at {fP(P)}"],
                    ["ṁ<sub>1</sub>/ṁ<sub>2</sub>", "ṁ<sub>1</sub> (kg/s)", "T<sub>3</sub> (°C)"],
                    [("open", True, "Three streams cross the boundary."), ("steady", True, "Steady operation."), ("adiabatic", True, "Mixing chambers are usually insulated."),
                     ("noshaft", True, "No shaft or wires."), ("lowke", True, "Velocities are small."), ("nope", True, "Height changes are small."),
                     ("steam", True, "Rule 1: steam (A-6) and saturated liquid (A-5) from the tables."), ("liqT", True, "Rule 1: the cold water is compressed liquid, h ≈ h<sub>f</sub>@T."),
                     ("cpwater", False, "The steam condenses; cΔT can't follow a phase change, and tables come first."), ("closed", False, "Mass crosses the boundary.")]),
             multi([("ṁ<sub>1</sub> + ṁ<sub>2</sub> = ṁ<sub>3</sub>", True, ""), (FIRST_SF, True, ""),
                    ("T<sub>3</sub> = (ṁ<sub>1</sub>T<sub>1</sub> + ṁ<sub>2</sub>T<sub>2</sub>)/ṁ<sub>3</sub>", False, "Only for streams with the same constant c and no phase change."),
                    ("ṁ<sub>1</sub> = ṁ<sub>2</sub>", False, "Nothing says the flows are equal.")], FIRST_SF),
             hx_terms(["ṁ<sub>1</sub>h<sub>1</sub>", "ṁ<sub>2</sub>h<sub>2</sub>"], ["ṁ<sub>3</sub>h<sub>3</sub>"],
                      "ṁ<sub>1</sub>h<sub>1</sub> + ṁ<sub>2</sub>h<sub>2</sub> = (ṁ<sub>1</sub> + ṁ<sub>2</sub>)h<sub>3</sub>", qreason="adiabatic"),
             props([("h<sub>1</sub>", s1["h"], "kJ/kg", "A-6", 0.003, f"{fP(P)} block, {fT(T1)} row"), ("h<sub>2</sub> = h<sub>f</sub>@T<sub>2</sub>", h2, "kJ/kg", "A-4", 0.003, fT(T2)),
                    ("h<sub>3</sub> = h<sub>f</sub> at P", h3, "kJ/kg", "A-5", 0.003, fP(P)), ("T<sub>sat</sub> at P", st["T"], "°C", "A-5", 0.003, fP(P))]),
             calc([f"Divide the energy balance by ṁ<sub>2</sub>: y(h<sub>1</sub> − h<sub>3</sub>) = h<sub>3</sub> − h<sub>2</sub>, with y = ṁ<sub>1</sub>/ṁ<sub>2</sub>",
                   f"y = ({num(h3, 2)} − {num(h2, 2)})/({num(s1['h'], 1)} − {num(h3, 2)}) = <b>{sg(y)}</b>",
                   f"ṁ<sub>1</sub> = yṁ<sub>2</sub> = ({sg(y)})({m2}) = <b>{sg(m1)} kg/s</b>",
                   f"T<sub>3</sub> = T<sub>sat</sub>@{fP(P)} = <b>{num(T3, 2)} °C</b>"]),
             mc(8, "Does it make sense that you need much less steam than cold water?",
                ["Yes: each kg of steam releases its superheat plus its latent heat, far more than a kg of cold water absorbs warming up",
                 "No: the flows should be equal", "No: you should need more steam than water", "Yes: steam is lighter"],
                0, "Condensing steam carries about 2000 kJ/kg of latent heat, so a little steam heats a lot of water.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E8", "R-134a condenser cooled by outdoor air", 5, "C", 16)
def E8(rng):
    P = rng.choice([800, 900, 1000, 1200]); T1 = rng.choice([t for t in RF.SH[P][1:] if t <= 80])
    Ts = RF.Tsat_true(P); T2 = rng.choice([t for t in RF.T_GRID if Ts - 12 <= t <= Ts - 4])
    mR = rng.choice([0.03, 0.05, 0.08, 0.10, 0.12]); Ta = rng.choice([20, 25, 30]); dTa = rng.choice([8, 10, 12, 15])
    r1 = RF.sh(P, T1); h2 = RF.satT(T2)["hf"]
    Q = mR * (r1["h"] - h2); ma = Q / (AIR["cp"] * dTa); Va = ma * AIR["R"] * K(Ta) / 100
    stem = (f"R-134a enters an air-cooled condenser at {fP(P)} and {fT(T1)} and leaves at the same pressure and {fT(T2)}. Its mass flow rate is {mR} kg/s. "
            f"Outdoor air at 100 kPa and {fT(Ta)} blows across the coils and leaves {dTa} °C warmer. "
            "Determine (a) the rate of heat rejected by the refrigerant, (b) the mass flow rate of the air, and (c) the volume flow rate of the incoming air.")
    hfP = RF.satP(P)["hf"]
    parts = [part("a", "Heat rejected, Q̇", "kW", Q, 0.01, 2, [(mR * (r1["h"] - hfP), "The refrigerant leaves subcooled at " + fT(T2) + ": use h<sub>f</sub> at that temperature, not at the pressure.")]),
             part("b", "Air mass flow rate, ṁ<sub>air</sub>", "kg/s", ma, 0.01, 2, [(Q / (AIR["cv"] * dTa), "Air flows: use c<sub>p</sub>.")]),
             part("c", "Air volume flow rate at the inlet, V̇", "m³/s", Va, 0.015, 2, [(ma * AIR["R"] * Ta / 100, "Use kelvins in Pv = RT.")])]
    steps = [self_step("Find the heat rejected, the air flow and the air volume flow for an air-cooled R-134a condenser."),
             mc(2, "What system makes this problem simplest?", HX_SYS, 0, HX_W),
             assume([f"R-134a: {fP(P)}, {fT(T1)} in; {fT(T2)} out; ṁ<sub>R</sub> = {mR} kg/s", f"Air: 100 kPa, {fT(Ta)} in; warms by {dTa} °C"],
                    ["Q̇ (kW)", "ṁ<sub>air</sub> (kg/s)", "V̇<sub>air</sub> (m³/s)"],
                    [("open", True, "Both streams flow through."), ("steady", True, "Steady operation."), ("shell", True, "Heat goes only from refrigerant to air."),
                     ("noshaft", True, "Treat the fan's work as negligible."), ("lowke", True, "Small velocity changes."), ("nope", True, "Height changes are small."),
                     ("r134", True, "Rule 1: R-134a tables (A-13 in, A-11 out)."), ("liqTr", True, "Rule 1: the exit is subcooled liquid."),
                     ("ideal", True, "Air near 1 atm and room temperature: Z ≈ 1 (rule 2)."), ("constc", True, f"Rule 4: the air warms only {dTa} °C."),
                     ("r134ideal", False, "Never ideal gas for R-134a (rule 1)."), ("a17", False, "Small ΔT for air: constant c (rule 4).")]),
             multi([(FIRST_SF, True, ""), ("Δh<sub>air</sub> = c<sub>p</sub>ΔT", True, ""), ("V̇ = ṁRT/P", True, ""),
                    ("Δh<sub>R</sub> = c<sub>p</sub>ΔT for the refrigerant", False, "R-134a changes phase here, and rule 1 says tables."),
                    ("ṁ<sub>air</sub> = ṁ<sub>R</sub>", False, "Separate streams with different flows.")], FIRST_SF),
             hx_terms(["ṁ<sub>R</sub>h<sub>1</sub>", "ṁ<sub>air</sub>h<sub>3</sub>"], ["ṁ<sub>R</sub>h<sub>2</sub>", "ṁ<sub>air</sub>h<sub>4</sub>"],
                      "ṁ<sub>R</sub>(h<sub>1</sub> − h<sub>2</sub>) = ṁ<sub>air</sub>c<sub>p</sub>(T<sub>4</sub> − T<sub>3</sub>) = Q̇"),
             props([("h<sub>1</sub>", r1["h"], "kJ/kg", "A-13", 0.003, f"{fP(P)} block, {fT(T1)} row"), ("h<sub>2</sub> ≈ h<sub>f</sub>@T<sub>2</sub>", h2, "kJ/kg", "A-11", 0.003, fT(T2)),
                    ("c<sub>p</sub> for air", AIR["cp"], "kJ/kg·K", "A-2a", 0.003, "air"), ("R for air", AIR["R"], "kJ/kg·K", "A-1", 0.003, "air")]),
             calc([f"Exit check: {fT(T2)} &lt; T<sub>sat</sub>@{fP(P)} = {num(RF.satP(P)['T'], 2)} °C, so subcooled: h<sub>2</sub> ≈ h<sub>f</sub>@{fT(T2)} = {num(h2, 2)} kJ/kg",
                   f"Q̇ = ṁ<sub>R</sub>(h<sub>1</sub> − h<sub>2</sub>) = {mR}({num(r1['h'], 2)} − {num(h2, 2)}) = <b>{sg(Q)} kW</b>",
                   f"ṁ<sub>air</sub> = Q̇/(c<sub>p</sub>ΔT) = {sg(Q)}/[(1.005)({dTa})] = <b>{sg(ma)} kg/s</b>",
                   f"V̇ = ṁRT/P = ({sg(ma)})(0.287)({sg(K(Ta), 5)})/100 = <b>{sg(Va)} m³/s</b>"]),
             mc(8, "The air flow is much bigger than the refrigerant flow. Is that right?",
                ["Yes: each kg of refrigerant gives up over 150 kJ as it condenses, while each kg of air carries only about 1 kJ per degree",
                 "No: the flows must match", "No: air should flow less because it is lighter", "Yes, because air is an ideal gas"],
                0, "Condensing releases a lot per kilogram; warming air by a few degrees absorbs little. That's why condenser fans move so much air.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E9", "Exhaust heat recovery for hot water", 5, "C", 16)
def E9(rng):
    Tg1 = rng.choice([700, 750, 780, 800, 820, 860, 900]); Tg2 = rng.choice([400, 420, 440, 460, 480])
    mg = rng.choice([0.5, 0.8, 1.0, 1.2, 1.5, 2.0]); T3 = rng.choice([10, 15, 20]); T4 = rng.choice([50, 60, 70, 80, 90])
    a1, a2 = a17.row(Tg1), a17.row(Tg2); h3, h4 = W.satT(T3)["hf"], W.satT(T4)["hf"]
    Q = mg * (a1["h"] - a2["h"]); mw = Q / (h4 - h3); Qc = mg * AIR["cp"] * (Tg1 - Tg2)
    stem = (f"Hot exhaust gas from a generator, treated as air, enters a heat-recovery exchanger at {Tg1} K and leaves at {Tg2} K, with a mass flow rate of {mg} kg/s. "
            f"It heats water at 200 kPa from {fT(T3)} to {fT(T4)} for a school's kitchen and showers. Determine (a) the rate of heat recovered, (b) the water flow rate, "
            "and (c) the heat rate you would have computed with constant c<sub>p</sub> = 1.005 kJ/kg·K.")
    parts = [part("a", "Heat recovered, Q̇ (Table A-17)", "kW", Q, 0.01, 2, [(Qc, "That's the constant-c<sub>p</sub> estimate. Over a drop of several hundred kelvins, use Table A-17 (rule 4).")]),
             part("b", "Water flow rate, ṁ<sub>w</sub>", "kg/s", mw, 0.01, 2, [(Q / (4.18 * (T4 - T3)) if abs(Q / (4.18 * (T4 - T3)) - mw) > 0.01 * mw else None, "Rule 1: use h<sub>f</sub>@T from Table A-4.")]),
             part("c", "Constant-c<sub>p</sub> estimate of Q̇", "kW", Qc, 0.01, 2, [])]
    steps = [self_step("Find the heat recovered from hot exhaust, the water it can heat, and how far off a constant-c<sub>p</sub> estimate would be."),
             mc(2, "What system makes this problem simplest?", HX_SYS, 0, HX_W),
             assume([f"Gas (air): {Tg1} K in, {Tg2} K out, ṁ<sub>g</sub> = {mg} kg/s", f"Water: 200 kPa, {fT(T3)} in, {fT(T4)} out"],
                    ["Q̇ (kW)", "ṁ<sub>w</sub> (kg/s)", "Q̇ with constant c<sub>p</sub> (kW)"],
                    [("open", True, "Both streams flow through."), ("steady", True, "Steady operation."), ("shell", True, "Heat goes only from gas to water."),
                     ("noshaft", True, "No work."), ("lowke", True, "Small velocity changes."), ("nope", True, "Small height changes."),
                     ("ideal", True, "Hot exhaust near 1 atm: far above air's critical point, Z ≈ 1 (rule 2)."),
                     ("a17", True, f"Rule 4: the gas cools by {Tg1 - Tg2} K, a large ΔT, so Table A-17."),
                     ("liqT", True, "Rule 1: the water stays liquid at 200 kPa: h ≈ h<sub>f</sub>@T (Table A-4)."),
                     ("constc", False, "Not for a ΔT this large. Part (c) shows how far off it is."), ("cpwater", False, "Tables for water (rule 1).")]),
             multi([(FIRST_SF, True, ""), ("Q̇ = ṁ<sub>g</sub>(h<sub>1</sub> − h<sub>2</sub>), h from A-17", True, ""), ("Q̇ = ṁ<sub>w</sub>(h<sub>4</sub> − h<sub>3</sub>), h<sub>f</sub>@T from A-4", True, ""),
                    ("Q̇ = ṁ<sub>g</sub>c<sub>p</sub>(T<sub>1</sub> − T<sub>2</sub>), for part (c) only", True, ""), ("T<sub>4</sub> = T<sub>2</sub>", False, "The streams don't have to leave at the same temperature.")], FIRST_SF),
             hx_terms(["ṁ<sub>g</sub>h<sub>1</sub>", "ṁ<sub>w</sub>h<sub>3</sub>"], ["ṁ<sub>g</sub>h<sub>2</sub>", "ṁ<sub>w</sub>h<sub>4</sub>"],
                      "ṁ<sub>g</sub>(h<sub>1</sub> − h<sub>2</sub>) = ṁ<sub>w</sub>(h<sub>4</sub> − h<sub>3</sub>) = Q̇"),
             props([(f"h at {Tg1} K", a1["h"], "kJ/kg", "A-17", 0.003, "air"), (f"h at {Tg2} K", a2["h"], "kJ/kg", "A-17", 0.003, "air"),
                    ("h<sub>3</sub> = h<sub>f</sub>@T<sub>3</sub>", h3, "kJ/kg", "A-4", 0.003, fT(T3)), ("h<sub>4</sub> = h<sub>f</sub>@T<sub>4</sub>", h4, "kJ/kg", "A-4", 0.003, fT(T4))]),
             calc([f"Q̇ = ṁ<sub>g</sub>(h<sub>1</sub> − h<sub>2</sub>) = {mg}({num(a1['h'], 2)} − {num(a2['h'], 2)}) = <b>{sg(Q)} kW</b>",
                   f"ṁ<sub>w</sub> = Q̇/(h<sub>4</sub> − h<sub>3</sub>) = {sg(Q)}/({num(h4, 2)} − {num(h3, 2)}) = <b>{sg(mw)} kg/s</b>",
                   f"Constant c<sub>p</sub>: ṁ<sub>g</sub>c<sub>p</sub>(T<sub>1</sub> − T<sub>2</sub>) = {mg}(1.005)({Tg1 - Tg2}) = <b>{sg(Qc)} kW</b>, about {abs(Q - Qc) / Q * 100:.0f}% low"]),
             mc(8, "Why does the constant-c<sub>p</sub> estimate come out low?",
                ["Air's c<sub>p</sub> rises with temperature, and this gas is far hotter than the 300 K where 1.005 applies",
                 "Because the gas isn't really air", "Because water's c is larger", "It shouldn't: the two must agree"],
                0, "Between 400 and 900 K, air's c<sub>p</sub> runs from about 1.01 kJ/kg·K at 400 K to about 1.12 at 900 K. That's why rule 4 sends large ΔT to A-17.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

# =================================================================== Ch. 6 second law
CYC_MC = ["Heat engine: Q<sub>H</sub> in from the hot reservoir, net work out, Q<sub>L</sub> rejected to the cold reservoir",
          "Refrigerator: work in, Q<sub>L</sub> removed from the cold space, Q<sub>H</sub> rejected to the warm surroundings",
          "Heat pump: work in, Q<sub>L</sub> taken from the cold outdoors, Q<sub>H</sub> delivered to the warm space",
          "Heat in from the hot reservoir, all of it converted to work, nothing rejected"]

def cycle_terms(qin_lab, qout_lab, win_keep, res):
    t = [term("Qin", qin_lab, "L", "+"), term("Win", "Ẇ<sub>in</sub>", "L", "+", not win_keep, [] if win_keep else ["dir"], "" if win_keep else "Work comes out of an engine."),
         term("Qout", qout_lab, "L", "−"), term("Wout", "Ẇ<sub>out</sub>", "L", "−", win_keep, ["dir"] if win_keep else [], "Work goes in." if win_keep else ""),
         term("dE", "dE/dt", "R", "", True, ["cycle"], "Each cycle returns to its starting state.")]
    return strike_custom(t, res)

@template("E10", "Is the engine claim possible?", 6, "D", 14)
def E10(rng):
    kind = rng.choice(["geo", "solar", "bio"])
    TH = {"geo": rng.choice([150, 160, 170, 180, 200]), "solar": rng.choice([300, 350, 380, 400]), "bio": rng.choice([450, 500, 550])}[kind]
    TL = rng.choice([10, 15, 20, 25, 30]); QH = rng.choice([2000, 4000, 5000, 8000, 10000, 15000])
    THK, TLK = K(TH), K(TL); emax = 1 - TLK / THK
    ok = rng.random() < 0.55
    eta = round(emax * (rng.uniform(0.55, 0.85) if ok else rng.uniform(1.06, 1.25)), 2)
    if (eta < emax) != ok: ok = eta < emax
    Wd = eta * QH; QL = QH - Wd; Sg = QL / TLK - QH / THK
    src = {"geo": f"a geothermal well at {fT(TH)}", "solar": f"a solar-thermal collector field at {fT(TH)}", "bio": f"a biomass boiler at {fT(TH)}"}[kind]
    stem = (f"A developer proposes a power plant that takes {QH:,} kW of heat from {src} and rejects heat to a river at {fT(TL)}. "
            f"The brochure claims {Wd:,.0f} kW of net power. Determine (a) the claimed thermal efficiency, (b) the rate of heat rejected to the river, "
            "(c) the maximum possible efficiency, and (d) the rate of entropy generation (a negative value means the claim is impossible).")
    parts = [part("a", "Claimed thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.005, 1, []),
             part("b", "Heat rejected, Q̇<sub>L</sub>", "kW", QL, 0.005, 1, [(QH + Wd, "Q̇<sub>L</sub> = Q̇<sub>H</sub> − Ẇ<sub>net</sub>.")]),
             part("c", "Maximum (Carnot) efficiency, η<sub>max</sub>", "%", pct(emax), 0.01, 1, [(pct(1 - TL / TH), "Carnot efficiency needs absolute temperatures: convert to kelvins.")]),
             part("d", "Entropy generation rate, Ṡ<sub>gen</sub>", "kW/K", Sg, 0.02, 1,
                  [(QL / TL - QH / TH, "Use kelvins in Q/T."), (QH / THK - QL / TLK, "Signs flipped: the hot reservoir loses Q̇<sub>H</sub>/T<sub>H</sub> of entropy and the river gains Q̇<sub>L</sub>/T<sub>L</sub>.")])]
    steps = [self_step("Check whether a proposed power plant's claimed output is physically possible."),
             mc(2, "Which energy-flow picture is this?", CYC_MC, 0, "Heat comes in from a hot source, work comes out, and heat must be rejected to a cold sink. The “all of it converted to work, nothing rejected” option violates the Kelvin-Planck statement."),
             assume([f"Q̇<sub>H</sub> = {QH:,} kW from T<sub>H</sub> = {fT(TH)}", f"T<sub>L</sub> = {fT(TL)}", f"Claimed Ẇ<sub>net</sub> = {Wd:,.0f} kW"],
                    ["η<sub>th</sub> (%)", "Q̇<sub>L</sub> (kW)", "η<sub>max</sub> (%)", "Ṡ<sub>gen</sub> (kW/K)"],
                    [("cycle", True, "A power plant runs its working fluid in a cycle."), ("reservoir", True, "The heat source and the river are large enough to stay at fixed temperatures."),
                     ("rev", False, "Only the Carnot comparison is reversible; a real plant is not."), ("isothermal", False, "The working fluid's temperature changes around the cycle."),
                     ("ideal", False, "No working-fluid properties are needed.")]),
             multi([(FIRST_CYC, True, ""), ("η<sub>th</sub> = Ẇ<sub>net</sub>/Q̇<sub>H</sub>", True, ""), ("η<sub>max</sub> = 1 − T<sub>L</sub>/T<sub>H</sub> (kelvins)", True, ""),
                    ("Ṡ<sub>gen</sub> = Q̇<sub>L</sub>/T<sub>L</sub> − Q̇<sub>H</sub>/T<sub>H</sub>", True, ""),
                    ("η<sub>th</sub> = 1 − T<sub>L</sub>/T<sub>H</sub> for this plant", False, "That's only the reversible limit, not the real plant's efficiency."),
                    ("COP = Q̇<sub>L</sub>/Ẇ", False, "That's a refrigerator's figure of merit.")], FIRST_CYC),
             cycle_terms("Q̇<sub>in</sub> = Q̇<sub>H</sub>", "Q̇<sub>out</sub> = Q̇<sub>L</sub>", False, "Ẇ<sub>net,out</sub> = Q̇<sub>H</sub> − Q̇<sub>L</sub>"),
             props([("T<sub>H</sub>", THK, "K", "Given / computed", 0.002, None), ("T<sub>L</sub>", TLK, "K", "Given / computed", 0.002, None)]),
             calc([f"η<sub>th</sub> = {Wd:,.0f}/{QH:,} = <b>{pct(eta):.1f}%</b>",
                   f"Q̇<sub>L</sub> = Q̇<sub>H</sub> − Ẇ<sub>net</sub> = {QH:,} − {Wd:,.0f} = <b>{QL:,.0f} kW</b>",
                   f"η<sub>max</sub> = 1 − {sg(TLK, 5)}/{sg(THK, 5)} = <b>{pct(emax):.1f}%</b>",
                   f"Ṡ<sub>gen</sub> = Q̇<sub>L</sub>/T<sub>L</sub> − Q̇<sub>H</sub>/T<sub>H</sub> = {QL:,.0f}/{sg(TLK, 5)} − {QH:,}/{sg(THK, 5)} = <b>{sg(Sg, 3)} kW/K</b>"]),
             mc(8, "So, is the claim possible?",
                ["Yes: η<sub>th</sub> is below the Carnot limit, and Ṡ<sub>gen</sub> &gt; 0", "No: η<sub>th</sub> is above the Carnot limit, and Ṡ<sub>gen</sub> &lt; 0",
                 "Yes, as long as energy is conserved", "Can't tell without the working fluid"],
                0 if ok else 1, "The two tests agree: an efficiency above 1 − T<sub>L</sub>/T<sub>H</sub> is exactly the case where total entropy would decrease. Conserving energy isn't enough; the first law is satisfied either way.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E11", "Heat pump for a home", 6, "D", 14)
def E11(rng):
    QH = rng.choice([6, 8, 10, 12, 15, 18]); Ti = rng.choice([20, 21, 22]); To = rng.choice([-15, -10, -5, 0, 5])
    COP = rng.choice([2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.5])
    THK, TLK = K(Ti), K(To); Wd = QH / COP; QL = QH - Wd; cmax = THK / (THK - TLK); Wmin = QH / cmax
    stem = (f"A heat pump keeps a home at {fT(Ti)} when it is {fT(To)} outside. The house loses heat at {QH} kW, and the heat pump's COP is {COP}. "
            "Determine (a) the electric power the heat pump uses, (b) the rate of heat it pulls from the outdoor air, (c) the highest COP possible between these temperatures, "
            "and (d) the minimum power that would do the job.")
    parts = [part("a", "Power input, Ẇ<sub>in</sub>", "kW", Wd, 0.01, 1, [(QH * COP, "COP = Q̇<sub>H</sub>/Ẇ<sub>in</sub>, so divide.")]),
             part("b", "Heat from outdoors, Q̇<sub>L</sub>", "kW", QL, 0.01, 1, [(QH + Wd, "Q̇<sub>L</sub> = Q̇<sub>H</sub> − Ẇ<sub>in</sub>: the work adds to what comes from outside.")]),
             part("c", "Maximum COP, COP<sub>HP,max</sub>", "", cmax, 0.01, 1,
                  [(TLK / (THK - TLK), "That's the refrigerator's COP. A heat pump's is T<sub>H</sub>/(T<sub>H</sub> − T<sub>L</sub>)."),
                   (Ti / (Ti - To) if Ti != To else None, "Use kelvins in Carnot COPs.")]),
             part("d", "Minimum power, Ẇ<sub>min</sub>", "kW", Wmin, 0.01, 1, [])]
    ctx = {"t": "Who gets the heat pump?",
           "b": "A heat pump delivers the same heat as electric baseboards for a fraction of the electricity. But the upfront cost is high, and renters rarely choose their own heating equipment. Households that spend a large share of their income on energy often stand to save the most and are often the last to get the upgrade unless a program pays for it.",
           "q": f"Here the heat pump uses about {Wd:.1f} kW where resistance heat would use {QH} kW. In a rental, who should pay for the switch: the owner, the tenant, the utility, or a public program?",
           "src": None}
    steps = [self_step("Find the power, the heat pulled from outdoors, and the Carnot limit for a home heat pump."),
             mc(2, "Which energy-flow picture is this?", CYC_MC, 2, "The desired output is Q̇<sub>H</sub> into the warm house; work goes in to move heat from the cold outdoors."),
             assume([f"Q̇<sub>H</sub> = {QH} kW", f"T<sub>H</sub> = {fT(Ti)}, T<sub>L</sub> = {fT(To)}", f"COP<sub>HP</sub> = {COP}"],
                    ["Ẇ<sub>in</sub> (kW)", "Q̇<sub>L</sub> (kW)", "COP<sub>HP,max</sub>", "Ẇ<sub>min</sub> (kW)"],
                    [("cycle", True, "The refrigerant runs in a cycle."), ("reservoir", True, "The house and outdoors stay at fixed temperatures."),
                     ("rev", False, "The real heat pump isn't reversible: its COP is below the Carnot value."), ("isothermal", False, "Not relevant to a cycle analysis.")]),
             multi([(FIRST_CYC, True, ""), ("COP<sub>HP</sub> = Q̇<sub>H</sub>/Ẇ<sub>in</sub>", True, ""), ("COP<sub>HP,max</sub> = T<sub>H</sub>/(T<sub>H</sub> − T<sub>L</sub>)", True, ""),
                    ("COP<sub>R</sub> = Q̇<sub>L</sub>/Ẇ<sub>in</sub>", False, "The goal here is heating, so the figure of merit uses Q̇<sub>H</sub>."),
                    ("η = Ẇ/Q̇<sub>H</sub>", False, "That's a heat engine's efficiency.")], FIRST_CYC),
             cycle_terms("Q̇<sub>in</sub> = Q̇<sub>L</sub>", "Q̇<sub>out</sub> = Q̇<sub>H</sub>", True, "Q̇<sub>H</sub> = Q̇<sub>L</sub> + Ẇ<sub>in</sub>"),
             props([("T<sub>H</sub>", THK, "K", "Given / computed", 0.002, None), ("T<sub>L</sub>", TLK, "K", "Given / computed", 0.002, None)]),
             calc([f"Ẇ<sub>in</sub> = Q̇<sub>H</sub>/COP = {QH}/{COP} = <b>{sg(Wd)} kW</b>",
                   f"Q̇<sub>L</sub> = Q̇<sub>H</sub> − Ẇ<sub>in</sub> = {QH} − {sg(Wd)} = <b>{sg(QL)} kW</b>",
                   f"COP<sub>HP,max</sub> = {sg(THK, 5)}/({sg(THK, 5)} − {sg(TLK, 5)}) = <b>{sg(cmax)}</b>",
                   f"Ẇ<sub>min</sub> = Q̇<sub>H</sub>/COP<sub>max</sub> = {QH}/{sg(cmax)} = <b>{sg(Wmin)} kW</b>"]),
             mc(8, "What happens to COP<sub>HP,max</sub> on a colder day?",
                ["It falls, because T<sub>H</sub> − T<sub>L</sub> grows: heat pumps work harder in deep cold", "It rises, because more heat is needed",
                 "It stays the same; COP depends only on the equipment", "It becomes less than 1"],
                0, "COP<sub>max</sub> = T<sub>H</sub>/(T<sub>H</sub> − T<sub>L</sub>). A bigger temperature lift means more work per unit of heat. T<sub>H</sub>/(T<sub>H</sub> − T<sub>L</sub>) is always greater than 1.")]
    return stem, parts, steps, ctx, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E12", "Food bank walk-in cooler", 6, "D", 14)
def E12(rng):
    QL = rng.choice([3, 4, 5, 6, 8]); TL = rng.choice([-20, -10, 0, 2, 4]); TH = rng.choice([25, 30, 35]); COP = rng.choice([1.5, 1.8, 2.0, 2.2, 2.5, 3.0])
    THK, TLK = K(TH), K(TL); Wd = QL / COP; QHd = QL + Wd; cmax = TLK / (THK - TLK); Sg = QHd / THK - QL / TLK
    stem = (f"A community food bank's walk-in {'freezer' if TL < 0 else 'cooler'} is held at {fT(TL)} in a back room at {fT(TH)}. "
            f"Its refrigeration unit removes heat at {QL} kW and draws {sg(Wd, 3)} kW of electric power. Determine (a) the COP, (b) the heat rejected to the back room, "
            "(c) the maximum possible COP, and (d) the rate of entropy generation.")
    Wd = float(sg(Wd, 3)); COPa = QL / Wd; QHd = QL + Wd; Sg = QHd / THK - QL / TLK
    parts = [part("a", "COP<sub>R</sub>", "", COPa, 0.01, 1, [(QHd / Wd, "That's the heat-pump COP. A refrigerator's useful output is Q̇<sub>L</sub>.")]),
             part("b", "Heat rejected, Q̇<sub>H</sub>", "kW", QHd, 0.01, 1, [(QL - Wd, "Q̇<sub>H</sub> = Q̇<sub>L</sub> + Ẇ<sub>in</sub>.")]),
             part("c", "Maximum COP, COP<sub>R,max</sub>", "", cmax, 0.01, 1, [(THK / (THK - TLK), "That's the heat-pump limit. For a refrigerator: T<sub>L</sub>/(T<sub>H</sub> − T<sub>L</sub>).")]),
             part("d", "Entropy generation, Ṡ<sub>gen</sub>", "kW/K", Sg, 0.03, 1, [(QHd / TH - QL / TL if TL else None, "Use kelvins in Q/T.")])]
    steps = [self_step("Find the actual and maximum COP, the heat rejected, and the entropy generated by a food bank's refrigeration unit."),
             mc(2, "Which energy-flow picture is this?", CYC_MC, 1, "The goal is removing Q̇<sub>L</sub> from the cold space; work goes in and Q̇<sub>H</sub> goes to the room."),
             assume([f"Q̇<sub>L</sub> = {QL} kW", f"Ẇ<sub>in</sub> = {Wd} kW", f"T<sub>L</sub> = {fT(TL)}, T<sub>H</sub> = {fT(TH)}"],
                    ["COP<sub>R</sub>", "Q̇<sub>H</sub> (kW)", "COP<sub>R,max</sub>", "Ṡ<sub>gen</sub> (kW/K)"],
                    [("cycle", True, "The refrigerant runs in a cycle."), ("reservoir", True, "The cold space and the room stay at fixed temperatures."),
                     ("rev", False, "A real unit is irreversible, which is why Ṡ<sub>gen</sub> &gt; 0.")]),
             multi([(FIRST_CYC, True, ""), ("COP<sub>R</sub> = Q̇<sub>L</sub>/Ẇ<sub>in</sub>", True, ""), ("COP<sub>R,max</sub> = T<sub>L</sub>/(T<sub>H</sub> − T<sub>L</sub>)", True, ""),
                    ("Ṡ<sub>gen</sub> = Q̇<sub>H</sub>/T<sub>H</sub> − Q̇<sub>L</sub>/T<sub>L</sub>", True, ""),
                    ("COP = T<sub>H</sub>/(T<sub>H</sub> − T<sub>L</sub>)", False, "That's the heat-pump limit.")], FIRST_CYC),
             cycle_terms("Q̇<sub>in</sub> = Q̇<sub>L</sub>", "Q̇<sub>out</sub> = Q̇<sub>H</sub>", True, "Q̇<sub>H</sub> = Q̇<sub>L</sub> + Ẇ<sub>in</sub>"),
             props([("T<sub>H</sub>", THK, "K", "Given / computed", 0.002, None), ("T<sub>L</sub>", TLK, "K", "Given / computed", 0.002, None)]),
             calc([f"COP<sub>R</sub> = {QL}/{Wd} = <b>{sg(COPa)}</b>", f"Q̇<sub>H</sub> = {QL} + {Wd} = <b>{sg(QHd)} kW</b>",
                   f"COP<sub>R,max</sub> = {sg(TLK, 5)}/({sg(THK, 5)} − {sg(TLK, 5)}) = <b>{sg(cmax)}</b>",
                   f"Ṡ<sub>gen</sub> = {sg(QHd)}/{sg(THK, 5)} − {QL}/{sg(TLK, 5)} = <b>{sg(Sg, 3)} kW/K</b>"]),
             mc(8, "Check your answers against each other. What must be true?",
                ["COP<sub>R</sub> &lt; COP<sub>R,max</sub> and Ṡ<sub>gen</sub> &gt; 0", "COP<sub>R</sub> &gt; COP<sub>R,max</sub>", "Ṡ<sub>gen</sub> &lt; 0", "Q̇<sub>H</sub> &lt; Q̇<sub>L</sub>"],
                0, "A real refrigerator falls short of Carnot and generates entropy. Q̇<sub>H</sub> must exceed Q̇<sub>L</sub> by the work input.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

# =================================================================== Ch. 7 isentropic efficiency
@template("E13", "Steam turbine: isentropic efficiency and entropy generation", 7, "E", 20)
def E13(rng):
    P1 = rng.choice([3000, 5000, 8000, 10000]); T1 = rng.choice([400, 450, 500, 600]); P2 = rng.choice([10, 15, 20, 25, 30, 40, 50, 75, 100])
    eta = rng.choice([0.78, 0.80, 0.82, 0.85, 0.88, 0.90]); m = rng.choice([5, 8, 10, 12, 15, 20])
    s1 = W.sh(P1, T1); st = W.satP(P2)
    x2s = (s1["s"] - st["sf"]) / st["sfg"]; assert 0 < x2s < 1
    h2s = st["hf"] + x2s * st["hfg"]; h2a = s1["h"] - eta * (s1["h"] - h2s); x2a = (h2a - st["hf"]) / st["hfg"]; assert x2a < 1
    s2a = st["sf"] + x2a * st["sfg"]; Wd = m * (s1["h"] - h2a); Sg = m * (s2a - s1["s"])
    stem = (f"Steam enters an adiabatic turbine at {fP(P1)} and {fT(T1)} and leaves at {fP(P2)}. The turbine's isentropic efficiency is {int(eta * 100)}% and the mass flow rate is {m} kg/s. "
            "Determine (a) the exit enthalpy for an isentropic turbine, (b) the actual exit enthalpy, (c) the power output, and (d) the rate of entropy generation.")
    parts = [part("a", "Isentropic exit enthalpy, h<sub>2s</sub>", "kJ/kg", h2s, 0.005, 2, [(st["hg"], "s<sub>1</sub> &lt; s<sub>g</sub> at P<sub>2</sub>, so the isentropic exit is a mixture. Find x<sub>2s</sub> first.")]),
             part("b", "Actual exit enthalpy, h<sub>2a</sub>", "kJ/kg", h2a, 0.005, 2,
                  [(s1["h"] - (s1["h"] - h2s) / eta, "For a turbine, the actual drop is smaller: h<sub>1</sub> − h<sub>2a</sub> = η(h<sub>1</sub> − h<sub>2s</sub>)."), (h2s, "That's the isentropic exit. The real turbine ends at a higher h.")]),
             part("c", "Power output, Ẇ<sub>out</sub>", "kW", Wd, 0.01, 2, [(m * (s1["h"] - h2s), "That's the isentropic power. Multiply by η.")]),
             part("d", "Entropy generation, Ṡ<sub>gen</sub>", "kW/K", Sg, 0.03, 1, [(m * (st["sg"] - s1["s"]), "s<sub>2a</sub> comes from x<sub>2a</sub>: s<sub>f</sub> + x<sub>2a</sub>s<sub>fg</sub>, not s<sub>g</sub>.")])]
    steps = [self_step("Find the ideal and actual exit enthalpies, the power, and the entropy generated in a steam turbine with known isentropic efficiency."),
             dia("Which T-s sketch shows this turbine?", ["ts_turb", "ts_turb_left", "ts_comp_dome", "ts_turb_isoT"], 0,
                 "The ideal expansion drops straight down (s constant) to 2s. The real turbine generates entropy, so 2a lies on the same exit pressure line but to the right of 2s."),
             assume([f"P<sub>1</sub> = {fP(P1)}, T<sub>1</sub> = {fT(T1)}", f"P<sub>2</sub> = {fP(P2)}", f"η<sub>T</sub> = {eta}", f"ṁ = {m} kg/s"],
                    ["h<sub>2s</sub> (kJ/kg)", "h<sub>2a</sub> (kJ/kg)", "Ẇ<sub>out</sub> (kW)", "Ṡ<sub>gen</sub> (kW/K)"],
                    [("open", True, "Steam flows through."), ("steady", True, "Steady operation."), ("adiabatic", True, "Given."),
                     ("lowke", True, "No velocities given."), ("nope", True, "Same height."), ("steam", True, "Rule 1: A-6 inlet, A-5 exit."),
                     ("isen", True, "For the comparison turbine only: s<sub>2s</sub> = s<sub>1</sub>."),
                     ("rev", False, "The real turbine isn't reversible: η &lt; 1."), ("steamideal", False, "Rule 1: tables for steam.")]),
             multi([(FIRST_SF, True, ""), ("s<sub>2s</sub> = s<sub>1</sub>", True, ""), ("η<sub>T</sub> = (h<sub>1</sub> − h<sub>2a</sub>)/(h<sub>1</sub> − h<sub>2s</sub>)", True, ""),
                    ("Ṡ<sub>gen</sub> = ṁ(s<sub>2a</sub> − s<sub>1</sub>) for an adiabatic device", True, ""),
                    ("η<sub>T</sub> = (h<sub>1</sub> − h<sub>2s</sub>)/(h<sub>1</sub> − h<sub>2a</sub>)", False, "That's upside down: it would give η &gt; 1 for a turbine."),
                    ("T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>", False, "That's for an ideal gas with constant c, not steam.")], FIRST_SF),
             sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Win": (["dir"], "Work comes out."),
                        "mke1": (["lowke"], "No velocities given."), "mke2": (["lowke"], "No velocities given."), "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."),
                        "dE": (["steady"], "Steady operation.")}, "Ẇ<sub>out</sub> = ṁ(h<sub>1</sub> − h<sub>2a</sub>)"),
             props([("h<sub>1</sub>", s1["h"], "kJ/kg", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"), ("s<sub>1</sub>", s1["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"),
                    ("h<sub>f</sub> at P<sub>2</sub>", st["hf"], "kJ/kg", "A-5", 0.003, fP(P2)), ("h<sub>fg</sub> at P<sub>2</sub>", st["hfg"], "kJ/kg", "A-5", 0.003, fP(P2)),
                    ("s<sub>f</sub> at P<sub>2</sub>", st["sf"], "kJ/kg·K", "A-5", 0.003, fP(P2)), ("s<sub>fg</sub> at P<sub>2</sub>", st["sfg"], "kJ/kg·K", "A-5", 0.003, fP(P2))]),
             calc([f"x<sub>2s</sub> = (s<sub>1</sub> − s<sub>f</sub>)/s<sub>fg</sub> = ({num(s1['s'], 4)} − {num(st['sf'], 4)})/{num(st['sfg'], 4)} = {sg(x2s)}",
                   f"h<sub>2s</sub> = h<sub>f</sub> + x<sub>2s</sub>h<sub>fg</sub> = {num(st['hf'], 2)} + ({sg(x2s)})({num(st['hfg'], 1)}) = <b>{sg(h2s, 5)} kJ/kg</b>",
                   f"h<sub>2a</sub> = h<sub>1</sub> − η(h<sub>1</sub> − h<sub>2s</sub>) = {num(s1['h'], 1)} − {eta}({num(s1['h'], 1)} − {sg(h2s, 5)}) = <b>{sg(h2a, 5)} kJ/kg</b>",
                   f"Ẇ<sub>out</sub> = ṁ(h<sub>1</sub> − h<sub>2a</sub>) = {m}({num(s1['h'], 1)} − {sg(h2a, 5)}) = <b>{sg(Wd)} kW</b>",
                   f"x<sub>2a</sub> = (h<sub>2a</sub> − h<sub>f</sub>)/h<sub>fg</sub> = {sg(x2a)}; s<sub>2a</sub> = s<sub>f</sub> + x<sub>2a</sub>s<sub>fg</sub> = {sg(s2a, 5)} kJ/kg·K",
                   f"Ṡ<sub>gen</sub> = ṁ(s<sub>2a</sub> − s<sub>1</sub>) = {m}({sg(s2a, 5)} − {num(s1['s'], 4)}) = <b>{sg(Sg, 3)} kW/K</b>"]),
             mc(8, "Where must h<sub>2a</sub> fall?",
                ["Between h<sub>2s</sub> and h<sub>1</sub>, and closer to h<sub>2s</sub> when η is high", "Below h<sub>2s</sub>", "Above h<sub>1</sub>", "Exactly at h<sub>2s</sub>"],
                0, "A real turbine extracts less than the ideal one, so it leaves with more enthalpy than h<sub>2s</sub>. Below h<sub>2s</sub> would mean η &gt; 1.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E14", "Air compressor with variable specific heats", 7, "E", 20)
def E14(rng):
    T1 = rng.choice([290, 295, 300, 305, 310]); P1 = rng.choice([95, 100]); rp = rng.choice([6, 7, 8, 9, 10, 12])
    eta = rng.choice([0.80, 0.82, 0.85, 0.87, 0.88]); m = rng.choice([0.5, 1, 1.5, 2, 3])
    r1 = a17.row(T1); Pr2 = r1["Pr"] * rp; s2, (ra, rb), f = a17.by("Pr", Pr2)
    h2s = s2["h"]; ws = h2s - r1["h"]; wa = ws / eta; h2a = r1["h"] + wa
    t2a, (qa, qb), g = a17.by("h", h2a); T2a = t2a["T"]; s02a = t2a["s"]
    Sg = m * (s02a - r1["s"] - AIR["R"] * math.log(rp)); Wd = m * wa
    T2c = T1 * rp ** (0.4 / 1.4)
    stem = (f"Air is compressed in an adiabatic compressor from {P1} kPa and {T1} K to {P1 * rp} kPa. The isentropic efficiency is {int(eta * 100)}% and the mass flow rate is {m} kg/s. "
            "Using variable specific heats, determine (a) the isentropic exit enthalpy, (b) the power input, (c) the actual exit temperature, and (d) the rate of entropy generation.")
    parts = [part("a", "Isentropic exit enthalpy, h<sub>2s</sub>", "kJ/kg", h2s, 0.005, 2, [(r1["h"] + AIR["cp"] * (T2c - T1), "That's the constant-c<sub>p</sub> shortcut. With variable specific heats, use P<sub>r</sub> from A-17.")]),
             part("b", "Power input, Ẇ<sub>in</sub>", "kW", Wd, 0.01, 2, [(m * ws * eta, "For a compressor, the actual work is larger: w<sub>a</sub> = w<sub>s</sub>/η."), (m * ws, "That's the isentropic work. Divide by η.")]),
             part("c", "Actual exit temperature, T<sub>2a</sub>", "K", T2a, 0.005, 2, [(s2["T"], "That's T<sub>2s</sub>. The real compressor ends hotter.")]),
             part("d", "Entropy generation, Ṡ<sub>gen</sub>", "kW/K", Sg, 0.04, 1, [(m * (s02a - r1["s"]), "Include the pressure term: s<sub>2</sub> − s<sub>1</sub> = s°<sub>2</sub> − s°<sub>1</sub> − R ln(P<sub>2</sub>/P<sub>1</sub>).")])]
    steps = [self_step("Find the ideal exit enthalpy, the power, the actual exit temperature, and the entropy generated in an air compressor."),
             dia("Which T-s sketch shows this compressor?", ["ts_comp", "ts_comp_left", "ts_turb_gas", "ts_comp_isoP"], 0,
                 "Ideal compression goes straight up (s constant) to the high-pressure line at 2s. The real compressor generates entropy, so 2a sits to the right of 2s on the same line, at a higher temperature."),
             assume([f"P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {T1} K", f"P<sub>2</sub> = {P1 * rp} kPa", f"η<sub>C</sub> = {eta}", f"ṁ = {m} kg/s"],
                    ["h<sub>2s</sub> (kJ/kg)", "Ẇ<sub>in</sub> (kW)", "T<sub>2a</sub> (K)", "Ṡ<sub>gen</sub> (kW/K)"],
                    [("open", True, "Air flows through."), ("steady", True, "Steady operation."), ("adiabatic", True, "Given."), ("lowke", True, "No velocities given."), ("nope", True, "Same height."),
                     ("ideal", True, "Air at modest pressure, far above its critical temperature: Z ≈ 1 (rule 2)."),
                     ("a17", True, "Rule 4: the air heats by a few hundred kelvins, and the problem asks for variable specific heats."),
                     ("isen", True, "For the comparison compressor: s<sub>2s</sub> = s<sub>1</sub>."),
                     ("constc", False, "Not for this ΔT, and the problem says variable specific heats."), ("rev", False, "η &lt; 1: the real compressor is irreversible.")]),
             multi([(FIRST_SF, True, ""), ("P<sub>r2</sub> = P<sub>r1</sub>(P<sub>2</sub>/P<sub>1</sub>)", True, ""), ("η<sub>C</sub> = (h<sub>2s</sub> − h<sub>1</sub>)/(h<sub>2a</sub> − h<sub>1</sub>)", True, ""),
                    ("s<sub>2</sub> − s<sub>1</sub> = s°<sub>2</sub> − s°<sub>1</sub> − R ln(P<sub>2</sub>/P<sub>1</sub>)", True, ""),
                    ("η<sub>C</sub> = (h<sub>2a</sub> − h<sub>1</sub>)/(h<sub>2s</sub> − h<sub>1</sub>)", False, "Upside down: a compressor needs more work than the ideal one."),
                    ("T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>", False, "That's the constant-c relation; this problem uses A-17.")], FIRST_SF),
             sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Wout": (["dir"], "Work goes in."),
                        "mke1": (["lowke"], "No velocities given."), "mke2": (["lowke"], "No velocities given."), "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."),
                        "dE": (["steady"], "Steady operation.")}, "Ẇ<sub>in</sub> = ṁ(h<sub>2a</sub> − h<sub>1</sub>)"),
             props([("h<sub>1</sub>", r1["h"], "kJ/kg", "A-17", 0.003, f"{T1} K"), ("P<sub>r1</sub>", r1["Pr"], "", "A-17", 0.004, f"{T1} K"),
                    ("s°<sub>1</sub>", r1["s"], "kJ/kg·K", "A-17", 0.003, f"{T1} K"), ("R for air", AIR["R"], "kJ/kg·K", "A-1", 0.003, "air")]),
             calc([f"P<sub>r2</sub> = P<sub>r1</sub>(P<sub>2</sub>/P<sub>1</sub>) = ({sg(r1['Pr'], 4)})({rp}) = {sg(Pr2, 4)}",
                   f"In A-17, P<sub>r</sub> = {sg(Pr2, 4)} falls between {ra['T']} K (P<sub>r</sub> = {sg(ra['Pr'], 4)}, h = {num(ra['h'], 2)}) and {rb['T']} K (P<sub>r</sub> = {sg(rb['Pr'], 4)}, h = {num(rb['h'], 2)}): interpolate, h<sub>2s</sub> = <b>{sg(h2s, 5)} kJ/kg</b>",
                   f"w<sub>s</sub> = h<sub>2s</sub> − h<sub>1</sub> = {sg(ws)} kJ/kg; w<sub>a</sub> = w<sub>s</sub>/η = {sg(ws)}/{eta} = {sg(wa)} kJ/kg",
                   f"Ẇ<sub>in</sub> = ṁw<sub>a</sub> = ({m})({sg(wa)}) = <b>{sg(Wd)} kW</b>",
                   f"h<sub>2a</sub> = h<sub>1</sub> + w<sub>a</sub> = {sg(h2a, 5)} kJ/kg. In A-17 it falls between {qa['T']} K and {qb['T']} K: T<sub>2a</sub> = <b>{sg(T2a, 4)} K</b>, s°<sub>2a</sub> = {sg(s02a, 5)}",
                   f"Ṡ<sub>gen</sub> = ṁ[s°<sub>2a</sub> − s°<sub>1</sub> − R ln(P<sub>2</sub>/P<sub>1</sub>)] = {m}[{sg(s02a, 5)} − {num(r1['s'], 5)} − 0.287 ln {rp}] = <b>{sg(Sg, 3)} kW/K</b>"]),
             mc(8, "Compare T<sub>2a</sub> with T<sub>2s</sub>. What must be true?",
                ["T<sub>2a</sub> &gt; T<sub>2s</sub>: the extra work of a real compressor ends up heating the air", "T<sub>2a</sub> &lt; T<sub>2s</sub>", "They're equal", "T<sub>2a</sub> is below T<sub>1</sub>"],
                0, "Irreversibilities turn some of the work into extra internal energy, so the real exit is hotter and Ṡ<sub>gen</sub> &gt; 0.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E15", "R-134a compressor: isentropic efficiency", 7, "E", 20)
def E15(rng):
    P1 = rng.choice([100, 120, 140, 160, 180, 200, 240]); P2 = rng.choice([600, 700, 800, 900, 1000, 1200])
    eta = rng.choice([0.75, 0.78, 0.80, 0.82, 0.85, 0.88]); m = rng.choice([0.03, 0.05, 0.08, 0.10, 0.12, 0.15])
    s1 = RF.satP(P1); h1 = s1["hg"]; sv = round(s1["sg"], 4)
    i2s, a, b = r_interp(P2, "s", sv); h2s = i2s["h"]
    h2a = h1 + (h2s - h1) / eta; i2a, c, d = r_interp(P2, "h", h2a); T2a = i2a["T"]; s2a = i2a["s"]
    Wd = m * (h2a - h1); Sg = m * (s2a - sv)
    stem = (f"R-134a enters an adiabatic compressor as saturated vapor at {fP(P1)} and leaves at {fP(P2)}. The isentropic efficiency is {int(eta * 100)}% and the mass flow rate is {m} kg/s. "
            "Determine (a) the isentropic exit enthalpy, (b) the power input, (c) the actual exit temperature, and (d) the rate of entropy generation.")
    parts = [part("a", "Isentropic exit enthalpy, h<sub>2s</sub>", "kJ/kg", h2s, 0.004, 2, [(RF.shsat(P2)["h"], "That's h<sub>g</sub> at P<sub>2</sub>. The exit is superheated: interpolate in the A-13 block at s = s<sub>1</sub>.")]),
             part("b", "Power input, Ẇ<sub>in</sub>", "kW", Wd, 0.01, 2, [(m * (h2s - h1) * eta, "A compressor needs more work than the ideal one: divide by η."), (m * (h2s - h1), "That's the isentropic power.")]),
             part("c", "Actual exit temperature, T<sub>2a</sub>", "°C", T2a, 0.01, 2, [(i2s["T"], "That's T<sub>2s</sub>. The real exit is hotter.")]),
             part("d", "Entropy generation, Ṡ<sub>gen</sub>", "kW/K", Sg, 0.06, 1, [])]
    steps = [self_step("Find the ideal exit enthalpy, power, actual exit temperature and entropy generation for an R-134a compressor."),
             dia("Which T-s sketch shows this compressor?", ["ts_rcomp", "ts_rcomp_left", "ts_turb", "ts_rcomp_dome"], 0,
                 "The inlet sits on the saturated-vapor line. Ideal compression goes straight up into the superheated region to 2s; the real exit 2a is on the same pressure line, to the right."),
             assume([f"Saturated vapor at P<sub>1</sub> = {fP(P1)}", f"P<sub>2</sub> = {fP(P2)}", f"η<sub>C</sub> = {eta}", f"ṁ = {m} kg/s"],
                    ["h<sub>2s</sub> (kJ/kg)", "Ẇ<sub>in</sub> (kW)", "T<sub>2a</sub> (°C)", "Ṡ<sub>gen</sub> (kW/K)"],
                    [("open", True, "Refrigerant flows through."), ("steady", True, "Steady operation."), ("adiabatic", True, "Given."), ("lowke", True, "No velocities given."), ("nope", True, "Same height."),
                     ("r134", True, "Rule 1: A-12 inlet, A-13 exit."), ("isen", True, "For the comparison compressor: s<sub>2s</sub> = s<sub>1</sub>."),
                     ("r134ideal", False, "Never ideal gas for R-134a (rule 1)."), ("constc", False, "No cΔT shortcuts for R-134a (rule 1).")]),
             multi([(FIRST_SF, True, ""), ("s<sub>2s</sub> = s<sub>1</sub>", True, ""), ("η<sub>C</sub> = (h<sub>2s</sub> − h<sub>1</sub>)/(h<sub>2a</sub> − h<sub>1</sub>)", True, ""),
                    ("Ṡ<sub>gen</sub> = ṁ(s<sub>2a</sub> − s<sub>1</sub>)", True, ""),
                    ("T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>", False, "Ideal-gas relation: not for R-134a.")], FIRST_SF),
             sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Wout": (["dir"], "Work goes in."),
                        "mke1": (["lowke"], "No velocities given."), "mke2": (["lowke"], "No velocities given."), "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."),
                        "dE": (["steady"], "Steady operation.")}, "Ẇ<sub>in</sub> = ṁ(h<sub>2a</sub> − h<sub>1</sub>)"),
             props([("h<sub>1</sub> = h<sub>g</sub> at P<sub>1</sub>", h1, "kJ/kg", "A-12", 0.003, fP(P1)), ("s<sub>1</sub> = s<sub>g</sub> at P<sub>1</sub>", s1["sg"], "kJ/kg·K", "A-12", 0.003, fP(P1))]),
             calc([f"s<sub>2s</sub> = s<sub>1</sub> = {num(sv, 4)} kJ/kg·K. In A-13's {fP(P2)} block it falls between the {rowlab(a)} row (s = {num(a['s'], 4)}, h = {num(a['h'], 2)}) and the {rowlab(b)} row (s = {num(b['s'], 4)}, h = {num(b['h'], 2)})",
                   f"Interpolate: h<sub>2s</sub> = <b>{sg(h2s, 5)} kJ/kg</b> (T<sub>2s</sub> = {sg(i2s['T'], 3)} °C)",
                   f"h<sub>2a</sub> = h<sub>1</sub> + (h<sub>2s</sub> − h<sub>1</sub>)/η = {num(h1, 2)} + ({sg(h2s, 5)} − {num(h1, 2)})/{eta} = {sg(h2a, 5)} kJ/kg",
                   f"Ẇ<sub>in</sub> = ṁ(h<sub>2a</sub> − h<sub>1</sub>) = {m}({sg(h2a, 5)} − {num(h1, 2)}) = <b>{sg(Wd)} kW</b>",
                   f"h<sub>2a</sub> falls between the {rowlab(c)} row (h = {num(c['h'], 2)}) and the {rowlab(d)} row (h = {num(d['h'], 2)}): T<sub>2a</sub> = <b>{sg(T2a, 3)} °C</b>, s<sub>2a</sub> = {sg(s2a, 4)}",
                   f"Ṡ<sub>gen</sub> = ṁ(s<sub>2a</sub> − s<sub>1</sub>) = {m}({sg(s2a, 4)} − {num(sv, 4)}) = <b>{sg(Sg, 2)} kW/K</b>"]),
             mc(8, "Ṡ<sub>gen</sub> comes out small here. Is that a problem?",
                ["No: the mass flow is small, and only the sign has to be positive; T<sub>2a</sub> &gt; T<sub>2s</sub> confirms the direction",
                 "Yes: it should be at least 1 kW/K", "Yes: it should be negative for a compressor", "No: it should be exactly zero"],
                0, "Entropy generation scales with the flow rate. What must hold is Ṡ<sub>gen</sub> &gt; 0, which matches the real exit being hotter than the ideal one.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

# =================================================================== Ch. 9 cycles
CYC_PV = ["pv_otto", "pv_diesel", "pv_dual", "pv_brayton"]
def cyc_assume(givens, finds, extra):
    return assume(givens, finds, [("closed", True, "Reciprocating engine: the air in the cylinder is a closed system.")] + extra)

@template("E16", "Otto cycle, cold-air-standard", 9, "F", 22)
def E16(rng):
    r = rng.choice([7, 8, 9, 10, 11]); T1 = rng.choice([290, 295, 300, 310, 320]); P1 = rng.choice([90, 95, 100]); qin = rng.choice([600, 700, 800, 900, 1000])
    k, cv = 1.4, AIR["cv"]
    T2 = T1 * r ** (k - 1); T3 = T2 + qin / cv; T4 = T3 / r ** (k - 1); qout = cv * (T4 - T1); w = qin - qout; eta = 1 - r ** (1 - k)
    stem = (f"An ideal Otto cycle has a compression ratio of {r}. At the start of compression, air is at {P1} kPa and {T1} K, and {qin} kJ/kg of heat is added at constant volume. "
            "Using cold-air-standard assumptions, determine (a) the temperature after compression, (b) the maximum temperature, (c) the net work per kilogram, and (d) the thermal efficiency.")
    parts = [part("a", "T<sub>2</sub>", "K", T2, 0.005, 2, [(T1 * r ** k, "Temperature uses the exponent k − 1: T<sub>2</sub> = T<sub>1</sub>r<sup>k−1</sup>."), (T1 * r, "That uses T ∝ r (exponent 1). Isentropic compression needs r<sup>k−1</sup>.")]),
             part("b", "T<sub>3</sub>", "K", T3, 0.005, 3, [(T2 + qin / AIR["cp"], "Heat is added at constant volume: use c<sub>v</sub>.")]),
             part("c", "Net work, w<sub>net</sub>", "kJ/kg", w, 0.01, 2, []),
             part("d", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.005, 2, [(pct(1 - T1 / T3), "That's the Carnot efficiency between T<sub>1</sub> and T<sub>3</sub>, the upper limit, not Otto's.")])]
    steps = [self_step("Find the compression temperature, peak temperature, net work and efficiency of an ideal Otto cycle."),
             dia("Which P-v diagram is the Otto cycle?", CYC_PV, 0, "Otto: isentropic compression, heat added at constant volume (vertical line), isentropic expansion, heat rejected at constant volume."),
             cyc_assume([f"r = {r}", f"P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {T1} K", f"q<sub>in</sub> = {qin} kJ/kg"], ["T<sub>2</sub> (K)", "T<sub>3</sub> (K)", "w<sub>net</sub> (kJ/kg)", "η<sub>th</sub> (%)"],
                        [("coldair", True, "The problem says so (rule 4)."), ("intrev", True, "Ideal cycle: compression and expansion are isentropic."),
                         ("constv", True, "Spark ignition adds heat so fast that the piston barely moves."), ("stationary", True, "Standard for cycles; your deck says you don't need to write it."),
                         ("constP", False, "That's the Diesel cycle's heat addition."), ("airstd", False, "Valid in general, but the problem asks for cold-air-standard."), ("open", False, "Otto analysis treats the cylinder's air as a closed system.")]),
             multi([("T<sub>2</sub>/T<sub>1</sub> = (v<sub>1</sub>/v<sub>2</sub>)<sup>k−1</sup>", True, ""), ("q<sub>in</sub> = c<sub>v</sub>(T<sub>3</sub> − T<sub>2</sub>)", True, ""),
                    ("η<sub>Otto</sub> = 1 − 1/r<sup>k−1</sup>", True, ""), (FIRST_CL + " (per kg, for each process)", True, ""),
                    ("q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)", False, "Heat addition is at constant volume, so c<sub>v</sub>."),
                    ("η = 1 − T<sub>L</sub>/T<sub>H</sub>", False, "That's Carnot, the upper limit.")], FIRST_CL),
             strike_custom([term("qin", "q<sub>in</sub>", "L", "+"), term("win", "w<sub>b,in</sub>", "L", "+", True, ["constv"], "Constant volume: no boundary work."),
                            term("qout", "q<sub>out</sub>", "L", "−", True, ["dir"], "Heat comes in during 2→3."),
                            term("wout", "w<sub>b,out</sub>", "L", "−", True, ["constv"], "Constant volume: no boundary work."),
                            term("du", "Δu", "R", ""), term("dke", "Δke", "R", "+", True, ["stationary"], ""), term("dpe", "Δpe", "R", "+", True, ["stationary"], "")],
                           "Process 2→3: q<sub>in</sub> = u<sub>3</sub> − u<sub>2</sub> = c<sub>v</sub>(T<sub>3</sub> − T<sub>2</sub>)",
                           p="Apply the first law to the heat-addition process, 2→3. Cross out every term that drops."),
             props([("c<sub>v</sub> for air", cv, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("k for air", 1.4, "", "A-2a", 0.003, "300 K")]),
             calc([f"T<sub>2</sub> = T<sub>1</sub>r<sup>k−1</sup> = ({T1})({r})<sup>0.4</sup> = <b>{sg(T2)} K</b>",
                   f"T<sub>3</sub> = T<sub>2</sub> + q<sub>in</sub>/c<sub>v</sub> = {sg(T2)} + {qin}/0.718 = <b>{sg(T3)} K</b>",
                   f"T<sub>4</sub> = T<sub>3</sub>/r<sup>k−1</sup> = {sg(T4)} K; q<sub>out</sub> = c<sub>v</sub>(T<sub>4</sub> − T<sub>1</sub>) = {sg(qout)} kJ/kg",
                   f"w<sub>net</sub> = q<sub>in</sub> − q<sub>out</sub> = {qin} − {sg(qout)} = <b>{sg(w)} kJ/kg</b>",
                   f"η<sub>th</sub> = 1 − 1/r<sup>k−1</sup> = 1 − 1/{r}<sup>0.4</sup> = <b>{pct(eta):.1f}%</b> (check: w<sub>net</sub>/q<sub>in</sub> = {pct(w / qin):.1f}%)"]),
             mc(8, f"The Carnot efficiency between T<sub>1</sub> and T<sub>3</sub> is {pct(1 - T1 / T3):.0f}%. How does your Otto efficiency compare?",
                ["Lower: Otto adds and rejects heat over a range of temperatures, not at the extremes", "Higher: Otto beats Carnot with high compression", "Exactly equal", "It can't be compared"],
                0, "No cycle between the same temperature limits beats Carnot. Otto's η depends only on r, and real SI engines manage about 25 to 30%.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E17", "Diesel cycle, cold-air-standard", 9, "F", 22)
def E17(rng):
    r = rng.choice([14, 16, 18, 20, 22]); rc = rng.choice([1.6, 1.8, 2.0, 2.2, 2.5]); T1 = rng.choice([290, 300, 310, 320]); P1 = rng.choice([90, 95, 100])
    k, cv, cp = 1.4, AIR["cv"], AIR["cp"]
    T2 = T1 * r ** (k - 1); T3 = rc * T2; T4 = T3 * (rc / r) ** (k - 1); qin = cp * (T3 - T2); qout = cv * (T4 - T1); eta = 1 - qout / qin
    stem = (f"An ideal Diesel cycle has a compression ratio of {r} and a cutoff ratio of {rc}. At the start of compression, air is at {P1} kPa and {T1} K. "
            "Using cold-air-standard assumptions, determine (a) the temperature after compression, (b) the temperature after heat addition, (c) the heat added per kilogram, and (d) the thermal efficiency.")
    parts = [part("a", "T<sub>2</sub>", "K", T2, 0.005, 2, [(T1 * r ** k, "Temperature uses k − 1.")]),
             part("b", "T<sub>3</sub>", "K", T3, 0.005, 2, [(rc * T1, "Multiply r<sub>c</sub> by T<sub>2</sub>, the temperature at the start of heat addition, not T<sub>1</sub>.")]),
             part("c", "Heat added, q<sub>in</sub>", "kJ/kg", qin, 0.01, 2, [(cv * (T3 - T2), "Diesel heat addition is at constant pressure: use c<sub>p</sub>.")]),
             part("d", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 3, [(pct(1 - r ** (1 - k)), "That's the Otto efficiency for the same r. Diesel's is lower, by the cutoff factor.")])]
    steps = [self_step("Find the temperatures, heat input and efficiency of an ideal Diesel cycle."),
             dia("Which P-v diagram is the Diesel cycle?", CYC_PV, 1, "Diesel: isentropic compression, heat added at constant pressure (horizontal line), isentropic expansion, heat rejected at constant volume."),
             cyc_assume([f"r = {r}, r<sub>c</sub> = {rc}", f"P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {T1} K"], ["T<sub>2</sub> (K)", "T<sub>3</sub> (K)", "q<sub>in</sub> (kJ/kg)", "η<sub>th</sub> (%)"],
                        [("coldair", True, "The problem says so (rule 4)."), ("intrev", True, "Ideal cycle."),
                         ("constP", True, "Fuel burns as the piston starts moving down, so heat goes in at constant pressure."), ("stationary", True, "Standard for cycles."),
                         ("constv", False, "That's Otto's heat addition."), ("open", False, "The cylinder's air is a closed system.")]),
             multi([("T<sub>2</sub>/T<sub>1</sub> = r<sup>k−1</sup>", True, ""), ("T<sub>3</sub>/T<sub>2</sub> = r<sub>c</sub>", True, ""), ("q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)", True, ""),
                    ("q<sub>out</sub> = c<sub>v</sub>(T<sub>4</sub> − T<sub>1</sub>)", True, ""), (FIRST_CL + " (per kg, for each process)", True, ""),
                    ("η = 1 − 1/r<sup>k−1</sup>", False, "That's Otto. Diesel's efficiency also depends on r<sub>c</sub>.")], FIRST_CL),
             strike_custom([term("qin", "q<sub>in</sub>", "L", "+"), term("win", "w<sub>b,in</sub>", "L", "+", True, ["dir"], "The gas expands, so boundary work goes out."),
                            term("qout", "q<sub>out</sub>", "L", "−", True, ["dir"], "Heat comes in during 2→3."), term("wout", "w<sub>b,out</sub>", "L", "−"),
                            term("du", "Δu", "R", ""), term("dke", "Δke", "R", "+", True, ["stationary"], ""), term("dpe", "Δpe", "R", "+", True, ["stationary"], "")],
                           "Process 2→3: q<sub>in</sub> − w<sub>b,out</sub> = u<sub>3</sub> − u<sub>2</sub>; at constant P, w<sub>b</sub> = P(v<sub>3</sub> − v<sub>2</sub>), so q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)",
                           p="Apply the first law to the heat-addition process, 2→3. Cross out every term that drops."),
             props([("c<sub>p</sub> for air", cp, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("c<sub>v</sub> for air", cv, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("k for air", 1.4, "", "A-2a", 0.003, "300 K")]),
             calc([f"T<sub>2</sub> = T<sub>1</sub>r<sup>k−1</sup> = ({T1})({r})<sup>0.4</sup> = <b>{sg(T2)} K</b>",
                   f"T<sub>3</sub> = r<sub>c</sub>T<sub>2</sub> = ({rc})({sg(T2)}) = <b>{sg(T3)} K</b>",
                   f"q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>) = 1.005({sg(T3)} − {sg(T2)}) = <b>{sg(qin)} kJ/kg</b>",
                   f"T<sub>4</sub> = T<sub>3</sub>(v<sub>3</sub>/v<sub>4</sub>)<sup>k−1</sup> = T<sub>3</sub>(r<sub>c</sub>/r)<sup>0.4</sup> = {sg(T4)} K; q<sub>out</sub> = c<sub>v</sub>(T<sub>4</sub> − T<sub>1</sub>) = {sg(qout)} kJ/kg",
                   f"η<sub>th</sub> = 1 − q<sub>out</sub>/q<sub>in</sub> = 1 − {sg(qout)}/{sg(qin)} = <b>{pct(eta):.1f}%</b>"]),
             mc(8, f"An Otto cycle with r = {r} would reach {pct(1 - r ** -0.4):.0f}%. Why is your Diesel number lower?",
                ["At the same compression ratio, constant-pressure heat addition is less efficient; Diesel engines win in practice because they can use much higher r",
                 "Diesel engines are always less efficient than gasoline engines", "Because c<sub>p</sub> &gt; c<sub>v</sub> means more heat is wasted", "It shouldn't be lower"],
                0, "For the same r, η<sub>Otto</sub> &gt; η<sub>Diesel</sub>. Real Diesels run r of 14 to 22 without knock, which is why they end up more efficient.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E18", "Dual cycle, cold-air-standard", 9, "F", 22)
def E18(rng):
    r = rng.choice([14, 16, 18]); rp = rng.choice([1.3, 1.5, 1.8]); rc = rng.choice([1.2, 1.4, 1.6]); T1 = rng.choice([290, 300, 310])
    k, cv, cp = 1.4, AIR["cv"], AIR["cp"]
    T2 = T1 * r ** (k - 1); Tx = rp * T2; T3 = rc * Tx; T4 = T3 * (rc / r) ** (k - 1)
    qin = cv * (Tx - T2) + cp * (T3 - Tx); qout = cv * (T4 - T1); eta = 1 - qout / qin
    stem = (f"An ideal dual cycle has a compression ratio of {r}. During heat addition, the pressure first rises by a factor of {rp} at constant volume, then the volume grows by a factor of {rc} at constant pressure. "
            f"At the start of compression, air is at 100 kPa and {T1} K. Using cold-air-standard assumptions, determine (a) the temperature after compression, "
            "(b) the temperature at the end of the constant-volume heat addition, (c) the total heat added per kilogram, and (d) the thermal efficiency.")
    parts = [part("a", "T<sub>2</sub>", "K", T2, 0.005, 2, [(T1 * r ** k, "Temperature uses k − 1.")]),
             part("b", "T<sub>x</sub> (end of constant-volume heating)", "K", Tx, 0.005, 2, [(T2 * rp ** ((k - 1) / k), "At constant volume, T is proportional to P: T<sub>x</sub> = r<sub>p</sub>T<sub>2</sub>.")]),
             part("c", "Total heat added, q<sub>in</sub>", "kJ/kg", qin, 0.01, 2, [(cp * (T3 - T2), "The first part is at constant volume (c<sub>v</sub>), the second at constant pressure (c<sub>p</sub>)."), (cv * (T3 - T2), "The second part of the heating is at constant pressure: c<sub>p</sub>.")]),
             part("d", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 3, [])]
    steps = [self_step("Find the temperatures, heat input and efficiency of an ideal dual cycle."),
             dia("Which P-v diagram is the dual cycle?", CYC_PV, 2, "Dual: heat is added partly at constant volume (vertical) and partly at constant pressure (horizontal), between two isentropes."),
             cyc_assume([f"r = {r}, r<sub>p</sub> = {rp}, r<sub>c</sub> = {rc}", f"P<sub>1</sub> = 100 kPa, T<sub>1</sub> = {T1} K"], ["T<sub>2</sub> (K)", "T<sub>x</sub> (K)", "q<sub>in</sub> (kJ/kg)", "η<sub>th</sub> (%)"],
                        [("coldair", True, "The problem says so (rule 4)."), ("intrev", True, "Ideal cycle."),
                         ("constv", True, "First part of heat addition: constant volume.", "The first part of the heat addition happens at constant volume."),
                         ("constP", True, "Second part: constant pressure.", "The rest of the heat addition happens at constant pressure."),
                         ("stationary", True, "Standard for cycles."), ("open", False, "Closed-system analysis.")]),
             multi([("T<sub>2</sub>/T<sub>1</sub> = r<sup>k−1</sup>", True, ""), ("T<sub>x</sub> = r<sub>p</sub>T<sub>2</sub>, T<sub>3</sub> = r<sub>c</sub>T<sub>x</sub>", True, ""),
                    ("q<sub>in</sub> = c<sub>v</sub>(T<sub>x</sub> − T<sub>2</sub>) + c<sub>p</sub>(T<sub>3</sub> − T<sub>x</sub>)", True, ""), ("q<sub>out</sub> = c<sub>v</sub>(T<sub>4</sub> − T<sub>1</sub>)", True, ""),
                    (FIRST_CL + " (per kg, for each process)", True, ""), ("η = 1 − 1/r<sup>k−1</sup>", False, "Otto's formula; the dual cycle's is lower.")], FIRST_CL),
             strike_custom([term("qin", "q<sub>in</sub>", "L", "+"), term("win", "w<sub>b,in</sub>", "L", "+", True, ["constv"], "Constant volume."),
                            term("qout", "q<sub>out</sub>", "L", "−", True, ["dir"], "Heat comes in."), term("wout", "w<sub>b,out</sub>", "L", "−", True, ["constv"], "Constant volume."),
                            term("du", "Δu", "R", ""), term("dke", "Δke", "R", "+", True, ["stationary"], ""), term("dpe", "Δpe", "R", "+", True, ["stationary"], "")],
                           "Process 2→x: q<sub>in,v</sub> = c<sub>v</sub>(T<sub>x</sub> − T<sub>2</sub>). (For x→3 the boundary work stays, giving q<sub>in,P</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>x</sub>).)",
                           p="Apply the first law to the constant-volume part of heat addition, 2→x. Cross out every term that drops."),
             props([("c<sub>p</sub> for air", cp, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("c<sub>v</sub> for air", cv, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("k for air", 1.4, "", "A-2a", 0.003, "300 K")]),
             calc([f"T<sub>2</sub> = ({T1})({r})<sup>0.4</sup> = <b>{sg(T2)} K</b>", f"T<sub>x</sub> = r<sub>p</sub>T<sub>2</sub> = ({rp})({sg(T2)}) = <b>{sg(Tx)} K</b>",
                   f"T<sub>3</sub> = r<sub>c</sub>T<sub>x</sub> = ({rc})({sg(Tx)}) = {sg(T3)} K",
                   f"q<sub>in</sub> = 0.718({sg(Tx)} − {sg(T2)}) + 1.005({sg(T3)} − {sg(Tx)}) = <b>{sg(qin)} kJ/kg</b>",
                   f"T<sub>4</sub> = T<sub>3</sub>(r<sub>c</sub>/r)<sup>0.4</sup> = {sg(T4)} K; q<sub>out</sub> = 0.718({sg(T4)} − {T1}) = {sg(qout)} kJ/kg",
                   f"η<sub>th</sub> = 1 − q<sub>out</sub>/q<sub>in</sub> = <b>{pct(eta):.1f}%</b>"]),
             mc(8, "Where should the dual cycle's efficiency fall?",
                [f"Between Diesel and Otto at the same r: below {pct(1 - r ** -0.4):.0f}%", "Above the Otto value for the same r", "Below the Diesel value with the same r and r<sub>c</sub>", "Exactly at Otto's value"],
                0, "Part of the heat goes in at constant volume (Otto-like), part at constant pressure (Diesel-like), so its efficiency lands in between.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

def brayton_strike(res):
    return sf_single({"Qin": (["isen"], "Isentropic, so adiabatic."), "Qout": (["isen"], "Isentropic, so adiabatic."), "Wout": (["dir"], "Work goes into a compressor."),
                      "mke1": (["lowke"], "Small KE changes."), "mke2": (["lowke"], "Small KE changes."), "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."),
                      "dE": (["steady"], "Steady operation.")}, res, p="Apply the steady-flow first law to the compressor (1→2). Cross out every term that drops.")

@template("E19", "Brayton cycle, cold-air-standard", 9, "F", 22)
def E19(rng):
    rp = rng.choice([8, 10, 12, 14, 16]); T1 = rng.choice([290, 300, 310]); T3 = rng.choice([1100, 1200, 1300, 1400, 1500])
    e = 0.4 / 1.4; cp = AIR["cp"]
    T2 = T1 * rp ** e; T4 = T3 / rp ** e; wc = cp * (T2 - T1); wt = cp * (T3 - T4); rbw = wc / wt; eta = 1 - rp ** -e
    stem = (f"A simple ideal Brayton cycle runs on air with a pressure ratio of {rp}. Air enters the compressor at {T1} K and the turbine at {T3} K. "
            "Using cold-air-standard assumptions, determine (a) the compressor exit temperature, (b) the turbine exit temperature, (c) the back work ratio, and (d) the thermal efficiency.")
    parts = [part("a", "T<sub>2</sub>", "K", T2, 0.005, 2, [(T1 * rp ** 0.4, "With a pressure ratio, the exponent is (k − 1)/k = 0.286, not k − 1.")]),
             part("b", "T<sub>4</sub>", "K", T4, 0.005, 2, [(T3 / rp ** 0.4, "Use (k − 1)/k with pressure ratios.")]),
             part("c", "Back work ratio, w<sub>c</sub>/w<sub>t</sub>", "%", pct(rbw), 0.01, 2, [(pct(wt / wc), "Back work ratio is compressor work over turbine work.")]),
             part("d", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.005, 3, [(pct(1 - T1 / T3), "That's Carnot between T<sub>1</sub> and T<sub>3</sub>.")])]
    steps = [self_step("Find the compressor and turbine exit temperatures, back work ratio and efficiency of an ideal Brayton cycle."),
             dia("Which P-v diagram is the Brayton cycle?", CYC_PV, 3, "Brayton: isentropic compression, heat added at constant pressure, isentropic expansion all the way down, heat rejected at constant pressure."),
             assume([f"r<sub>p</sub> = {rp}", f"T<sub>1</sub> = {T1} K, T<sub>3</sub> = {T3} K"], ["T<sub>2</sub> (K)", "T<sub>4</sub> (K)", "r<sub>bw</sub> (%)", "η<sub>th</sub> (%)"],
                    [("open", True, "Each device (compressor, combustor, turbine) is a control volume."), ("steady", True, "Steady operation."),
                     ("coldair", True, "The problem says so (rule 4)."), ("isen", True, "Ideal cycle: compressor and turbine are isentropic.", "The compressor and turbine are isentropic (reversible and adiabatic)."),
                     ("lowke", True, "Small KE changes."), ("nope", True, "Same height."),
                     ("closed", False, "Gas turbines are open, steady-flow devices."), ("constv", False, "Brayton heat addition is at constant pressure.")]),
             multi([("T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>", True, ""), ("w = c<sub>p</sub>ΔT for each device", True, ""),
                    ("r<sub>bw</sub> = w<sub>c</sub>/w<sub>t</sub>", True, ""), ("η = 1 − 1/r<sub>p</sub><sup>(k−1)/k</sup>", True, ""), (FIRST_SF, True, ""),
                    ("T<sub>2</sub>/T<sub>1</sub> = r<sup>k−1</sup>", False, "That's the volume-ratio form, for Otto and Diesel.")], FIRST_SF),
             brayton_strike("w<sub>c,in</sub> = h<sub>2</sub> − h<sub>1</sub> = c<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>)"),
             props([("c<sub>p</sub> for air", cp, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("k for air", 1.4, "", "A-2a", 0.003, "300 K")]),
             calc([f"T<sub>2</sub> = T<sub>1</sub>r<sub>p</sub><sup>(k−1)/k</sup> = ({T1})({rp})<sup>0.2857</sup> = <b>{sg(T2)} K</b>",
                   f"T<sub>4</sub> = T<sub>3</sub>/r<sub>p</sub><sup>(k−1)/k</sup> = {T3}/{rp}<sup>0.2857</sup> = <b>{sg(T4)} K</b>",
                   f"w<sub>c</sub> = 1.005({sg(T2)} − {T1}) = {sg(wc)} kJ/kg; w<sub>t</sub> = 1.005({T3} − {sg(T4)}) = {sg(wt)} kJ/kg",
                   f"r<sub>bw</sub> = w<sub>c</sub>/w<sub>t</sub> = <b>{pct(rbw):.1f}%</b>", f"η<sub>th</sub> = 1 − 1/{rp}<sup>0.2857</sup> = <b>{pct(eta):.1f}%</b>"]),
             mc(8, "Gas turbines have a large back work ratio. What does yours say?",
                ["Roughly 40 to 60% of the turbine's work goes back into the compressor, which is normal for gas turbines", "It should be under 5%, like a steam plant",
                 "It should be over 100%", "Back work ratio doesn't apply to Brayton"],
                0, "Compressing a gas takes a lot of work, so gas turbines send a big share of turbine output back to the compressor. Steam plants pump a liquid and have back work ratios of a few percent.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

@template("E20", "Brayton cycle with variable specific heats", 9, "F", 22)
def E20(rng):
    rp = rng.choice([8, 10, 12, 14, 16]); T1 = rng.choice([290, 300]); T3 = rng.choice([1100, 1200, 1300, 1400, 1500])
    r1, r3 = a17.row(T1), a17.row(T3)
    s2, (a, b), f2 = a17.by("Pr", r1["Pr"] * rp); s4, (c, d), f4 = a17.by("Pr", r3["Pr"] / rp)
    def where(x, y, f): return f"essentially the {x['T']} K row" if f < 0.03 else (f"essentially the {y['T']} K row" if f > 0.97 else f"between {x['T']} K and {y['T']} K in A-17, so interpolate")
    h2, h4 = s2["h"], s4["h"]; wnet = (r3["h"] - h4) - (h2 - r1["h"]); qin = r3["h"] - h2; eta = wnet / qin
    e = 0.4 / 1.4
    stem = (f"A simple ideal Brayton cycle runs on air with a pressure ratio of {rp}. Air enters the compressor at {T1} K and the turbine at {T3} K. "
            "Accounting for the variation of specific heats with temperature, determine (a) the enthalpy at the compressor exit, (b) the enthalpy at the turbine exit, (c) the net work per kilogram, and (d) the thermal efficiency.")
    parts = [part("a", "h<sub>2</sub>", "kJ/kg", h2, 0.005, 2, [(r1["h"] + AIR["cp"] * T1 * (rp ** e - 1), "That's the constant-c<sub>p</sub> shortcut. Use P<sub>r</sub> from A-17.")]),
             part("b", "h<sub>4</sub>", "kJ/kg", h4, 0.005, 2, [(r3["h"] - AIR["cp"] * T3 * (1 - rp ** -e), "That's the constant-c<sub>p</sub> shortcut. Use P<sub>r4</sub> = P<sub>r3</sub>/r<sub>p</sub> in A-17.")]),
             part("c", "Net work, w<sub>net</sub>", "kJ/kg", wnet, 0.01, 2, []),
             part("d", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 3, [(pct(1 - rp ** -e), "That's the cold-air-standard value. With variable specific heats, use w<sub>net</sub>/q<sub>in</sub>.")])]
    steps = [self_step("Find the compressor and turbine exit enthalpies, net work and efficiency of an ideal Brayton cycle using Table A-17."),
             dia("Which P-v diagram is the Brayton cycle?", CYC_PV, 3, "Brayton: two isentropes joined by two constant-pressure lines."),
             assume([f"r<sub>p</sub> = {rp}", f"T<sub>1</sub> = {T1} K, T<sub>3</sub> = {T3} K"], ["h<sub>2</sub> (kJ/kg)", "h<sub>4</sub> (kJ/kg)", "w<sub>net</sub> (kJ/kg)", "η<sub>th</sub> (%)"],
                    [("open", True, "Each device is a control volume."), ("steady", True, "Steady operation."),
                     ("airstd", True, f"Rule 4: the temperature spans about {T3 - T1} K, a large ΔT, and the problem asks for variable specific heats."),
                     ("isen", True, "Ideal cycle.", "The compressor and turbine are isentropic (reversible and adiabatic)."), ("lowke", True, "Small KE changes."), ("nope", True, "Same height."),
                     ("coldair", False, "The problem asks for variable specific heats."), ("closed", False, "Open, steady-flow devices.")]),
             multi([("P<sub>r2</sub> = P<sub>r1</sub>r<sub>p</sub>, P<sub>r4</sub> = P<sub>r3</sub>/r<sub>p</sub>", True, ""), ("w = Δh for each device", True, ""),
                    ("η = w<sub>net</sub>/q<sub>in</sub>", True, ""), (FIRST_SF, True, ""),
                    ("T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>", False, "Constant-c relation; this problem uses A-17."),
                    ("v<sub>r2</sub> = v<sub>r1</sub>/r", False, "v<sub>r</sub> is for volume ratios (Otto, Diesel).")], FIRST_SF),
             brayton_strike("w<sub>c,in</sub> = h<sub>2</sub> − h<sub>1</sub>"),
             props([("h<sub>1</sub>", r1["h"], "kJ/kg", "A-17", 0.003, f"{T1} K"), ("P<sub>r1</sub>", r1["Pr"], "", "A-17", 0.004, f"{T1} K"),
                    ("h<sub>3</sub>", r3["h"], "kJ/kg", "A-17", 0.003, f"{T3} K"), ("P<sub>r3</sub>", r3["Pr"], "", "A-17", 0.004, f"{T3} K")]),
             calc([f"P<sub>r2</sub> = ({sg(r1['Pr'], 4)})({rp}) = {sg(r1['Pr'] * rp, 4)}: {where(a, b, f2)}; h<sub>2</sub> = <b>{sg(h2, 5)} kJ/kg</b>",
                   f"P<sub>r4</sub> = {sg(r3['Pr'], 4)}/{rp} = {sg(r3['Pr'] / rp, 4)}: {where(c, d, f4)}; h<sub>4</sub> = <b>{sg(h4, 5)} kJ/kg</b>",
                   f"w<sub>net</sub> = (h<sub>3</sub> − h<sub>4</sub>) − (h<sub>2</sub> − h<sub>1</sub>) = ({num(r3['h'], 2)} − {sg(h4, 5)}) − ({sg(h2, 5)} − {num(r1['h'], 2)}) = <b>{sg(wnet)} kJ/kg</b>",
                   f"q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub> = {sg(qin)} kJ/kg; η<sub>th</sub> = w<sub>net</sub>/q<sub>in</sub> = <b>{pct(eta):.1f}%</b>"]),
             mc(8, f"The cold-air-standard efficiency for r<sub>p</sub> = {rp} is {pct(1 - rp ** -e):.1f}%. How does yours compare?",
                ["A little lower: air's c<sub>p</sub> grows at high temperature, which changes the temperature ratios slightly", "Much higher, over 70%", "Exactly the same", "Negative"],
                0, "With variable specific heats, efficiency comes out a bit below the constant-c value. A big gap means a P<sub>r</sub> was multiplied where it should have been divided.")]
    return stem, parts, steps, None, {k: v for k, v in locals().items() if isinstance(v, (int, float, str)) and k not in ('stem',)}

# ---------------------------------------------------------------- build
def shuffle_mc(step, rng):
    if step["k"] in ("mc", "dia"):
        idx = list(range(len(step["o"]))); rng.shuffle(idx)
        step["o"] = [step["o"][i] for i in idx]; step["a"] = idx.index(step["a"])
    return step

def build(nvar=24, seed=20261120):
    out = []
    for T in TEMPLATES:
        rng = random.Random(seed + sum(map(ord, T["id"])) * 7)
        seen, vs, tries = set(), [], 0
        while len(vs) < nvar and tries < 4000:
            tries += 1
            try:
                stem, parts, steps, ctx, prm = T["fn"](rng)
            except (AssertionError, ValueError, IndexError):
                continue
            if stem in seen: continue
            seen.add(stem)
            steps = [shuffle_mc(s, rng) for s in steps]
            assert [s["n"] for s in steps] == list(range(1, 9)), (T["id"], [s["n"] for s in steps])
            vs.append({"stem": stem, "fig": None, "parts": parts, "steps": steps, "ctx": ctx, "_p": prm})
        assert len(vs) == nvar, (T["id"], len(vs))
        out.append({"id": T["id"], "title": T["title"], "ch": T["ch"], "slot": T["slot"], "pts": T["pts"], "v": vs})
    return out

if __name__ == "__main__":
    tpls = build()
    json.dump(tpls, open("exam2_templates.json", "w"), ensure_ascii=False)
    print(len(tpls), [(t["id"], len(t["v"])) for t in tpls])
