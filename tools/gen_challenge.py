"""Challenge problems for Exam 2 (Nov 2026): harder than the exam, same eight-step format.

16 templates x 24 versions. Ideas come from the Exam 2 scope (Ch. 5, 6, 7, 9 through Brayton) and the
shapes of Matthew's past exams: a turbine with a bypass throttle feeding a mixer (old Final, Problem 3),
a gas-generator core with a ram inlet, a two-fuel gas turbine, a Diesel engine with power from speed.
Writes challenge_templates.json. Run check_challenge.py on the result.
"""
import json, math, random
from tables import WATER as W, R as RF
import a17
from a17 import GAS
import exam2_common as ec
from exam2_common import *
from gen_exam2 import fP, fT, pct, r_rows, rowlab, hx_terms, cycle_terms, CYC_MC, CYC_PV, cyc_assume, shuffle_mc

AIR = GAS["air"]
CPA, CVA, RA, KA = AIR["cp"], AIR["cv"], AIR["R"], 1.4
E = 0.4 / 1.4
T0K = 273.15
TEMPLATES = []

def template(tid, title, ch, slot, pts, tier):
    def deco(fn):
        TEMPLATES.append(dict(id=tid, title=title, ch=ch, slot=slot, pts=pts, tier=tier, fn=fn))
        return fn
    return deco

def prm(loc):
    return {k: v for k, v in loc.items() if isinstance(v, (int, float, str)) and k not in ("stem",)}

# ---------------------------------------------------------------- extra assumptions for these problems
ec.LIB.update({
    "incomp":   ("Incompressible solids, constant c", "The blocks are incompressible solids with constant specific heats from Table A-3, so Δu = cΔT and Δs = c ln(T<sub>2</sub>/T<sub>1</sub>) with T in kelvins."),
    "rigid":    ("Rigid tank", "The tank is rigid, so V is constant: v<sub>2</sub> = v<sub>1</sub>, and there is no boundary work."),
    "qe":       ("Quasi-equilibrium, constant P", "The piston moves slowly with a fixed load, so the process is quasi-equilibrium at constant pressure."),
    "surr":     ("Boundary out at T<sub>0</sub>", "Draw the entropy boundary just outside the device, in the surroundings at T<sub>0</sub>, so the heat leaving crosses the boundary at T<sub>0</sub>."),
    "thr":      ("Throttle: h stays the same", "The valve is adiabatic, has no work, and its KE change is small, so h<sub>out</sub> = h<sub>in</sub>."),
    "drive":    ("Turbine drives only the compressor", "In the gas generator, all of the turbine's work goes to the compressor: w<sub>T</sub> = w<sub>C</sub>."),
    "fuel":     ("Heat input from fuel", "The fuel's heating value becomes q<sub>in</sub>, and the fuel's mass is small next to the air's."),
    "four":     ("Four-stroke engine", "A four-stroke engine fires once every two crankshaft revolutions."),
    "regen":    ("Regenerator, no losses outside", "The regenerator is insulated: the heat the turbine exhaust gives up goes into the compressed air."),
    "rev2":     ("Reversible devices for the limit", "For the upper limit only, the devices are reversible (Carnot), so S<sub>gen</sub> = 0."),
    "sconst":   ("Entropy is conserved", "Entropy in equals entropy out, so S<sub>gen</sub> = 0."),
    "tavg":     ("Temperatures average", "The final temperature is the mass-weighted average of the starting temperatures."),
    "constPres":("No pressure drop", "Pressure stays the same through the heat exchanger or mixer."),
})

# ---------------------------------------------------------------- water superheated-block interpolation
def w_rows(P):
    return [dict(W.shsat(P), sat=True)] + [dict(W.sh(P, T), sat=False) for T in W.SH[P]]

def w_interp(P, key, val):
    rows = w_rows(P)
    for a, b in zip(rows, rows[1:]):
        if (val - a[key]) * (val - b[key]) <= 0 and a[key] != b[key]:
            f = (val - a[key]) / (b[key] - a[key])
            return {k: a[k] + f * (b[k] - a[k]) for k in ("T", "v", "u", "h", "s")}, a, b
    raise AssertionError((P, key, val))

def r_interp(P, key, val):
    rows = r_rows(P)
    for a, b in zip(rows, rows[1:]):
        if (val - a[key]) * (val - b[key]) <= 0 and a[key] != b[key]:
            f = (val - a[key]) / (b[key] - a[key])
            return {k: a[k] + f * (b[k] - a[k]) for k in ("T", "v", "u", "h", "s")}, a, b
    raise AssertionError((P, key, val))

def safe(f):
    try: return f()
    except (AssertionError, ValueError, IndexError): return None

def between(a, b, key, val, d):
    return f"between the {rowlab(a)} and {rowlab(b)} rows ({key} = {num(a[key], d)} and {num(b[key], d)}), so interpolate"

def a17where(x, y, f):
    if f < 0.03: return f"essentially the {x['T']} K row"
    if f > 0.97: return f"essentially the {y['T']} K row"
    return f"between the {x['T']} K and {y['T']} K rows of A-17, so interpolate"

def strike_closed(spec, res, p="Apply the first law to the system. Cross out every term your assumptions remove."):
    labels = [("Qin", "Q<sub>in</sub>", "L", "+"), ("Win", "W<sub>in</sub>", "L", "+"), ("Qout", "Q<sub>out</sub>", "L", "−"), ("Wout", "W<sub>out</sub>", "L", "−"),
              ("dU", "ΔU", "R", ""), ("dKE", "ΔKE", "R", "+"), ("dPE", "ΔPE", "R", "+")]
    t = []
    for i, h, side, sign in labels:
        if i in spec:
            ok, w = spec[i]; t.append(term(i, h, side, sign, True, ok, w))
        else:
            t.append(term(i, h, side, sign))
    return strike_custom(t, res, p)

def multi_terms(ins, outs, res, keepQin=False, keepQout=False, keepWin=False, keepWout=False, qr="adiabatic", ke=("lowke", "nope"),
                p="Cross out every term your assumptions remove, and pick the reason for each."):
    t = [term("Qin", "Q̇<sub>in</sub>", "L", "+", not keepQin, [] if keepQin else [qr if not keepQout else "dir"], "" if keepQin else ("Heat leaves." if keepQout else "Insulated: no heat crosses the boundary.")),
         term("Win", "Ẇ<sub>in</sub>", "L", "+", not keepWin, [] if keepWin else (["dir"] if keepWout else ["noshaft"]), "" if keepWin else ("Work comes out." if keepWout else "No shaft or wires."))]
    for i, h in enumerate(ins): t.append(term(f"in{i}", h, "L", "+"))
    t.append(term("kein", "∑ṁ(V²/2 + gz)<sub>in</sub>", "L", "+", True, list(ke), "Small velocities, same height."))
    t.append(term("Qout", "Q̇<sub>out</sub>", "L", "−", not keepQout, [] if keepQout else [qr if not keepQin else "dir"], "" if keepQout else ("Heat comes in." if keepQin else "Insulated: no heat crosses the boundary.")))
    t.append(term("Wout", "Ẇ<sub>out</sub>", "L", "−", not keepWout, [] if keepWout else (["dir"] if keepWin else ["noshaft"]), "" if keepWout else ("Work goes in." if keepWin else "No shaft or wires.")))
    for i, h in enumerate(outs): t.append(term(f"out{i}", h, "L", "−"))
    t.append(term("keout", "∑ṁ(V²/2 + gz)<sub>out</sub>", "L", "−", True, list(ke), "Small velocities, same height."))
    t.append(term("dE", "dE<sub>cv</sub>/dt", "R", "", True, ["steady"], "Steady operation."))
    return strike_custom(t, res, p)

SGEN_SF = "Ṡ<sub>gen</sub> = ∑ṁs<sub>out</sub> − ∑ṁs<sub>in</sub> − ∑Q̇<sub>k</sub>/T<sub>k</sub> ≥ 0 (heat in counts +, heat out −)"
SGEN_CL = "S<sub>gen</sub> = ΔS<sub>sys</sub> − ∑Q<sub>k</sub>/T<sub>k</sub> ≥ 0 (heat in counts +, heat out −)"

# =================================================================== C1: old Final, Problem 3 shape
@template("C1", "Turbine and bypass valve feeding a mixer", 7, "E", 20, "hardest")
def C1(rng):
    P1 = rng.choice([3000, 5000, 8000]); T1 = rng.choice([t for t in W.SH[P1] if 400 <= t <= 600])
    P2 = rng.choice([400, 600, 800, 1000]); eta = rng.choice([0.75, 0.78, 0.80, 0.82, 0.85, 0.88]); m = rng.choice([5, 8, 10, 12, 15, 20])
    s1 = W.sh(P1, T1)
    assert s1["s"] > W.shsat(P2)["s"] + 0.02
    s2s, a2, b2 = w_interp(P2, "s", s1["s"]); h2s = s2s["h"]
    h2a = s1["h"] - eta * (s1["h"] - h2s)
    T3 = rng.choice([t for t in W.SH[P2] if t <= T1])
    s3 = W.sh(P2, T3)
    assert h2a + 40 < s3["h"] < s1["h"] - 20
    y = (s1["h"] - s3["h"]) / (s1["h"] - h2a); assert 0.3 <= y <= 0.85
    mT = y * m; mV = m - mT; Wd = mT * (s1["h"] - h2a); Sg = m * (s3["s"] - s1["s"])
    st2a, a2a, b2a = w_interp(P2, "h", h2a); sv, av, bv = w_interp(P2, "h", s1["h"])
    SgT = mT * (st2a["s"] - s1["s"]); SgV = mV * (sv["s"] - s1["s"]); SgM = Sg - SgT - SgV
    big = max([("turbine", SgT), ("valve", SgV), ("mixer", SgM)], key=lambda x: x[1])[0]
    stem = (f"Steam at {fP(P1)} and {fT(T1)} flows at {m} kg/s into a plant's steam header. Part of it runs through an adiabatic turbine with an isentropic efficiency of {int(round(eta * 100))}% "
            f"that exhausts at {fP(P2)}. The rest bypasses the turbine through an adiabatic throttling valve to {fP(P2)}. The two streams meet in an insulated mixing chamber, "
            f"and the combined stream leaves at {fP(P2)} and {fT(T3)}. Determine (a) the enthalpy at the turbine exit, (b) the mass flow rate through the turbine, "
            "(c) the turbine's power output, and (d) the total rate of entropy generation.")
    parts = [part("a", "Turbine exit enthalpy, h<sub>2</sub>", "kJ/kg", h2a, 0.005, 3,
                  [(h2s, "That's the isentropic exit, h<sub>2s</sub>. The real turbine extracts less: h<sub>2</sub> = h<sub>1</sub> − η(h<sub>1</sub> − h<sub>2s</sub>)."),
                   (s1["h"] - (s1["h"] - h2s) / eta, "For a turbine, η multiplies the ideal drop. Dividing by η gives more work than the ideal turbine.")]),
             part("b", "Mass flow through the turbine, ṁ<sub>T</sub>", "kg/s", mT, 0.01, 3,
                  [(mV, "That's the valve's flow. Check: the turbine stream leaves colder, so y = (h<sub>1</sub> − h<sub>3</sub>)/(h<sub>1</sub> − h<sub>2</sub>)."),
                   (m * (s1["h"] - s3["h"]) / (s1["h"] - h2s), "That uses the isentropic exit enthalpy. The stream entering the mixer has the actual h<sub>2</sub>.")]),
             part("c", "Turbine power, Ẇ<sub>T</sub>", "kW", Wd, 0.01, 3,
                  [(m * (s1["h"] - h2a), "Only part of the steam goes through the turbine. Use ṁ<sub>T</sub>, not the full flow."),
                   (mT * (s1["h"] - h2s), "That's the isentropic power. Use the actual h<sub>2</sub>.")]),
             part("d", "Total entropy generation, Ṡ<sub>gen</sub>", "kW/K", Sg, 0.02, 2,
                  [(SgT, "That's only the turbine's share. With one boundary around all three devices, Ṡ<sub>gen</sub> = ṁ(s<sub>3</sub> − s<sub>1</sub>)."),
                   (SgT + SgV, "The mixer generates entropy too: two streams at different temperatures mix irreversibly.")])]
    plan = ("Plan: get h<sub>2</sub> from the turbine efficiency, then let the mixer's energy balance decide the split. "
            "For S<sub>gen</sub>, draw one boundary around everything: one stream in, one stream out, no heat.")
    steps = [self_step(f"Find the turbine exit enthalpy, the split, the turbine power and the total entropy generated when steam runs through a turbine and a bypass valve in parallel, then mixes. {plan}"),
             mc(2, "You want the entropy generated by the whole arrangement. Where should the boundary go?",
                ["Around all three devices: one stream in (state 1), one stream out (state 3), turbine work crossing, no heat",
                 "Around the turbine only: the valve and mixer don't generate entropy",
                 "Around the mixer only: it's the only device with two inlets",
                 "Around nothing: S<sub>gen</sub> is zero because every device is adiabatic"],
                0, "Adiabatic doesn't mean reversible. Every device here generates entropy. One boundary around all of them gives Ṡ<sub>gen</sub> = ṁ(s<sub>3</sub> − s<sub>1</sub>) in one line, and it also gives Ẇ<sub>T</sub> = ṁ(h<sub>1</sub> − h<sub>3</sub>) as a check."),
             assume([f"State 1: {fP(P1)}, {fT(T1)}, ṁ = {m} kg/s", f"Turbine: η<sub>T</sub> = {eta}, exits at {fP(P2)}", f"Valve: to {fP(P2)}", f"State 3: {fP(P2)}, {fT(T3)}"],
                    ["h<sub>2</sub> (kJ/kg)", "ṁ<sub>T</sub> (kg/s)", "Ẇ<sub>T</sub> (kW)", "Ṡ<sub>gen</sub> (kW/K)"],
                    [("open", True, "Steam flows through every device."), ("steady", True, "Steady operation."),
                     ("adiabatic", True, "Turbine, valve and mixer are all adiabatic or insulated."), ("lowke", True, "No velocities given."), ("nope", True, "Same height."),
                     ("steam", True, "Rule 1: steam tables; every state here is superheated (A-6)."),
                     ("thr", True, "The bypass valve is a throttle."), ("noshaft", True, "The mixer has no shaft or wires.", "The mixing chamber has no shaft, wires or moving boundary."),
                     ("isen", True, "For the comparison turbine only: s<sub>2s</sub> = s<sub>1</sub>."),
                     ("sconst", False, "Adiabatic isn't reversible. Throttling and mixing always generate entropy."),
                     ("rev", False, "η &lt; 1, so the turbine isn't reversible."), ("steamideal", False, "Rule 1: tables for steam.")]),
             multi([("η<sub>T</sub> = (h<sub>1</sub> − h<sub>2</sub>)/(h<sub>1</sub> − h<sub>2s</sub>)", True, ""), ("Valve: h<sub>v</sub> = h<sub>1</sub>", True, ""),
                    ("Mixer: ṁ<sub>T</sub>h<sub>2</sub> + (ṁ − ṁ<sub>T</sub>)h<sub>1</sub> = ṁh<sub>3</sub>", True, ""), (SGEN_SF, True, ""),
                    ("h<sub>3</sub> = (h<sub>2</sub> + h<sub>1</sub>)/2", False, "Only if the flows are equal, and nothing says they are."),
                    ("η<sub>T</sub> = (h<sub>1</sub> − h<sub>2s</sub>)/(h<sub>1</sub> − h<sub>2</sub>)", False, "Upside down for a turbine.")],
                   "ṁ<sub>T</sub>h<sub>2</sub> + (ṁ − ṁ<sub>T</sub>)h<sub>1</sub> = ṁh<sub>3</sub> and Ṡ<sub>gen</sub> = ṁ(s<sub>3</sub> − s<sub>1</sub>)"),
             multi_terms(["ṁ<sub>T</sub>h<sub>2</sub>", "(ṁ − ṁ<sub>T</sub>)h<sub>1</sub>"], ["ṁh<sub>3</sub>"],
                         "Mixer: ṁ<sub>T</sub>h<sub>2</sub> + (ṁ − ṁ<sub>T</sub>)h<sub>1</sub> = ṁh<sub>3</sub>, so y = ṁ<sub>T</sub>/ṁ = (h<sub>1</sub> − h<sub>3</sub>)/(h<sub>1</sub> − h<sub>2</sub>)",
                         p="Apply the steady-flow first law to the mixing chamber (the valve stream enters at h<sub>1</sub>). Cross out every term that drops."),
             props([("h<sub>1</sub>", s1["h"], "kJ/kg", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"), ("s<sub>1</sub>", s1["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"),
                    ("h<sub>2s</sub> (s = s<sub>1</sub>)", h2s, "kJ/kg", "A-6", 0.004, f"{fP(P2)} block, " + between(a2, b2, "s", s1["s"], 4)),
                    ("h<sub>3</sub>", s3["h"], "kJ/kg", "A-6", 0.003, f"{fP(P2)} block, {fT(T3)} row"), ("s<sub>3</sub>", s3["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P2)} block, {fT(T3)} row")]),
             calc([f"s<sub>1</sub> = {num(s1['s'], 4)} &gt; s<sub>g</sub>@{fP(P2)}, so the isentropic exit is still superheated; interpolate in the {fP(P2)} block: h<sub>2s</sub> = {sg(h2s, 5)} kJ/kg",
                   f"h<sub>2</sub> = h<sub>1</sub> − η(h<sub>1</sub> − h<sub>2s</sub>) = {num(s1['h'], 1)} − {eta}({num(s1['h'], 1)} − {sg(h2s, 5)}) = <b>{sg(h2a, 5)} kJ/kg</b>",
                   f"Mixer: y = (h<sub>1</sub> − h<sub>3</sub>)/(h<sub>1</sub> − h<sub>2</sub>) = ({num(s1['h'], 1)} − {num(s3['h'], 1)})/({num(s1['h'], 1)} − {sg(h2a, 5)}) = {sg(y)}",
                   f"ṁ<sub>T</sub> = y ṁ = ({sg(y)})({m}) = <b>{sg(mT)} kg/s</b>; the valve carries {sg(mV)} kg/s",
                   f"Ẇ<sub>T</sub> = ṁ<sub>T</sub>(h<sub>1</sub> − h<sub>2</sub>) = ({sg(mT)})({num(s1['h'], 1)} − {sg(h2a, 5)}) = <b>{sg(Wd)} kW</b> (check with the big boundary: ṁ(h<sub>1</sub> − h<sub>3</sub>) = {sg(m * (s1['h'] - s3['h']))} kW)",
                   f"Ṡ<sub>gen</sub> = ṁ(s<sub>3</sub> − s<sub>1</sub>) = {m}({num(s3['s'], 4)} − {num(s1['s'], 4)}) = <b>{sg(Sg, 3)} kW/K</b>",
                   f"Where it comes from: turbine {sg(SgT, 3)}, valve {sg(SgV, 3)}, mixer {sg(SgM, 3)} kW/K (using s<sub>2</sub> = {sg(st2a['s'], 5)} and the valve exit s = {sg(sv['s'], 5)} kJ/kg·K from the {fP(P2)} block)"]),
             mc(8, "Split Ṡ<sub>gen</sub> device by device (last line of step 7). Which device generates the most entropy here, and what does that say?",
                [f"The {big}: it is the biggest source of lost work, so it's the first thing to fix",
                 "The turbine always generates the most, because it's the only device with work", "None of them: adiabatic devices generate no entropy",
                 "They all generate the same amount"],
                0, "Throttling steam through a big pressure drop throws away the work a turbine could have made, and mixing streams at different temperatures adds more. "
                   "Sending more steam through the turbine and less through the valve cuts S<sub>gen</sub> and raises the power. A design that sends most of the steam through the valve is close to the worst possible.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C2: turbine with extraction and heat loss
@template("C2", "Turbine with steam extraction and heat loss", 5, "B", 16, "challenge")
def C2(rng):
    P1 = rng.choice([5000, 8000, 10000]); T1 = rng.choice([t for t in W.SH[P1] if 450 <= t <= 600]); m1 = rng.choice([10, 12, 15, 18, 20, 25])
    s1 = W.sh(P1, T1)
    P2 = rng.choice([600, 800, 1000, 1200, 1400])
    T2 = rng.choice([t for t in W.SH[P2] if t < T1 and W.sh(P2, t)["s"] > s1["s"] + 0.04 and W.sh(P2, t)["h"] < s1["h"] - 150])
    s2 = W.sh(P2, T2); f = rng.choice([0.10, 0.12, 0.15, 0.18, 0.20, 0.25]); m2 = f * m1; m3 = m1 - m2
    P3 = rng.choice([10, 15, 20, 30, 50]); x3 = rng.choice([0.88, 0.90, 0.92, 0.94]); st = W.satP(P3)
    h3 = st["hf"] + x3 * st["hfg"]; sx3 = st["sf"] + x3 * st["sfg"]; assert sx3 > s2["s"]
    Q = rng.choice([100, 150, 200, 250, 300, 400]); Tc0 = rng.choice([20, 25, 30]); T0 = Tc0 + T0K
    Wd = m1 * s1["h"] - m2 * s2["h"] - m3 * h3 - Q
    Sg = m2 * s2["s"] + m3 * sx3 - m1 * s1["s"] + Q / T0
    stem = (f"Steam enters a turbine at {fP(P1)} and {fT(T1)} at {m1} kg/s. {int(round(f * 100))}% of the steam is extracted at {fP(P2)} and {fT(T2)} to heat feedwater; "
            f"the rest leaves at {fP(P3)} with a quality of {x3}. The turbine casing loses {Q} kW of heat to the turbine hall at {fT(Tc0)}. "
            "Determine (a) the enthalpy of the exhaust steam, (b) the power output, and (c) the rate of entropy generation, counting the heat lost to the hall.")
    parts = [part("a", "Exhaust enthalpy, h<sub>3</sub>", "kJ/kg", h3, 0.005, 2, [(x3 * st["hg"], "h = h<sub>f</sub> + x h<sub>fg</sub>; the liquid part carries h<sub>f</sub>.")]),
             part("b", "Power output, Ẇ<sub>out</sub>", "kW", Wd, 0.01, 4,
                  [(Wd + Q, "That leaves out the heat loss. Energy leaving as heat isn't available as work."), (Wd + 2 * Q, "The heat leaves, so it's subtracted, not added."),
                   (m1 * (s1["h"] - h3) - Q, "Only the steam that stays in goes all the way to state 3. The extracted steam leaves at state 2."),
                   (m1 * s1["h"] - m2 * s2["h"] - m1 * h3 - Q, "Mass balance: ṁ<sub>3</sub> = ṁ<sub>1</sub> − ṁ<sub>2</sub>.")]),
             part("c", "Entropy generation, Ṡ<sub>gen</sub>", "kW/K", Sg, 0.02, 4,
                  [(Sg - Q / T0, "Heat leaving carries entropy out: add Q̇<sub>out</sub>/T<sub>0</sub> to the generation."), (Sg - 2 * Q / T0, "Sign: heat leaving makes S<sub>gen</sub> bigger. Ṡ<sub>gen</sub> = (out − in) + Q̇<sub>out</sub>/T<sub>0</sub>."),
                   (m2 * s2["s"] + m3 * sx3 - m1 * s1["s"] + Q / Tc0, "Use T<sub>0</sub> in kelvins.")])]
    steps = [self_step("Find the exhaust enthalpy, the power and the entropy generated by a turbine with one extraction and a heat loss. Plan: mass balance first, then one energy balance and one entropy balance around the whole turbine."),
             mc(2, "The heat leaves the casing, which is hotter than the hall. To count all the entropy the heat loss creates, where should the boundary be?",
                ["Just outside the casing, in the hall air at T<sub>0</sub>, so the heat crosses the boundary at T<sub>0</sub>",
                 "On the steam side of the casing, at the steam temperature", "It doesn't matter; Q/T is the same everywhere",
                 "Leave the heat out of the entropy balance"],
                0, "The temperature where heat crosses the boundary sets Q/T. Pushing the boundary out to T<sub>0</sub> includes the entropy made as heat flows from the hot casing into the cooler hall."),
             assume([f"In: {fP(P1)}, {fT(T1)}, ṁ<sub>1</sub> = {m1} kg/s", f"Extraction: {fP(P2)}, {fT(T2)}, {int(round(f * 100))}% of ṁ<sub>1</sub>", f"Exhaust: {fP(P3)}, x<sub>3</sub> = {x3}",
                     f"Q̇<sub>out</sub> = {Q} kW to the hall at {fT(Tc0)}"], ["h<sub>3</sub> (kJ/kg)", "Ẇ<sub>out</sub> (kW)", "Ṡ<sub>gen</sub> (kW/K)"],
                    [("open", True, "Steam crosses the boundary at three places."), ("steady", True, "Steady operation."), ("lowke", True, "No velocities given."), ("nope", True, "Same height."),
                     ("steam", True, "Rule 1: A-6 for the superheated states, A-5 for the exhaust mixture."), ("surr", True, "So the heat crosses at T<sub>0</sub>."),
                     ("adiabatic", False, "The casing loses heat."), ("rev", False, "Real turbine; the exit entropies rise."), ("steamideal", False, "Rule 1: tables for steam.")]),
             multi([("ṁ<sub>1</sub> = ṁ<sub>2</sub> + ṁ<sub>3</sub>", True, ""), (FIRST_SF, True, ""), (SGEN_SF, True, ""),
                    ("η<sub>T</sub> = (h<sub>1</sub> − h<sub>2a</sub>)/(h<sub>1</sub> − h<sub>2s</sub>)", False, "No efficiency is given or asked for, and the turbine isn't adiabatic."),
                    ("Ṡ<sub>gen</sub> = ṁ(s<sub>3</sub> − s<sub>1</sub>)", False, "That's for one inlet, one exit, no heat. Here there are two exits and a heat loss.")], FIRST_SF),
             multi_terms(["ṁ<sub>1</sub>h<sub>1</sub>"], ["ṁ<sub>2</sub>h<sub>2</sub>", "ṁ<sub>3</sub>h<sub>3</sub>"],
                         "Ẇ<sub>out</sub> = ṁ<sub>1</sub>h<sub>1</sub> − ṁ<sub>2</sub>h<sub>2</sub> − ṁ<sub>3</sub>h<sub>3</sub> − Q̇<sub>out</sub>", keepQout=True, keepWout=True),
             props([("h<sub>1</sub>", s1["h"], "kJ/kg", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"), ("s<sub>1</sub>", s1["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"),
                    ("h<sub>2</sub>", s2["h"], "kJ/kg", "A-6", 0.003, f"{fP(P2)} block, {fT(T2)} row"), ("s<sub>2</sub>", s2["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P2)} block, {fT(T2)} row"),
                    ("h<sub>f</sub>, h<sub>fg</sub> at P<sub>3</sub>: h<sub>f</sub>", st["hf"], "kJ/kg", "A-5", 0.003, fP(P3)), ("h<sub>fg</sub> at P<sub>3</sub>", st["hfg"], "kJ/kg", "A-5", 0.003, fP(P3)),
                    ("s<sub>f</sub> at P<sub>3</sub>", st["sf"], "kJ/kg·K", "A-5", 0.003, fP(P3)), ("s<sub>fg</sub> at P<sub>3</sub>", st["sfg"], "kJ/kg·K", "A-5", 0.003, fP(P3))]),
             calc([f"ṁ<sub>2</sub> = {f}({m1}) = {sg(m2)} kg/s; ṁ<sub>3</sub> = {m1} − {sg(m2)} = {sg(m3)} kg/s",
                   f"h<sub>3</sub> = h<sub>f</sub> + x<sub>3</sub>h<sub>fg</sub> = {num(st['hf'], 2)} + {x3}({num(st['hfg'], 1)}) = <b>{sg(h3, 5)} kJ/kg</b>",
                   f"Ẇ<sub>out</sub> = ({m1})({num(s1['h'], 1)}) − ({sg(m2)})({num(s2['h'], 1)}) − ({sg(m3)})({sg(h3, 5)}) − {Q} = <b>{sg(Wd)} kW</b>",
                   f"s<sub>3</sub> = s<sub>f</sub> + x<sub>3</sub>s<sub>fg</sub> = {num(st['sf'], 4)} + {x3}({num(st['sfg'], 4)}) = {sg(sx3, 5)} kJ/kg·K",
                   f"Ṡ<sub>gen</sub> = ṁ<sub>2</sub>s<sub>2</sub> + ṁ<sub>3</sub>s<sub>3</sub> − ṁ<sub>1</sub>s<sub>1</sub> + Q̇<sub>out</sub>/T<sub>0</sub> = ({sg(m2)})({num(s2['s'], 4)}) + ({sg(m3)})({sg(sx3, 5)}) − ({m1})({num(s1['s'], 4)}) + {Q}/{num(T0, 2)} = <b>{sg(Sg, 3)} kW/K</b>"]),
             mc(8, f"The heat loss is {Q} kW. How much does it change the power and the entropy generation?",
                [f"Power drops by exactly {Q} kW, and Ṡ<sub>gen</sub> rises by Q̇/T<sub>0</sub> = {sg(Q / T0, 3)} kW/K, usually a modest share of the total",
                 "The heat loss raises the power", "The heat loss lowers Ṡ<sub>gen</sub> because entropy leaves with the heat", "Neither changes"],
                0, "Heat leaving takes energy that could have been work. In the entropy balance, heat leaving carries entropy out, so the steam's own entropy rise plus Q/T<sub>0</sub> is what the second law sees.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C3: compressor + aftercooler, A-17
@template("C3", "Air compressor and aftercooler", 7, "C", 16, "challenge")
def C3(rng):
    T1 = rng.choice([290, 300]); P1 = 100; rp = rng.choice([6, 8, 10, 12]); eta = rng.choice([0.80, 0.82, 0.84, 0.85, 0.86, 0.88]); m = rng.choice([0.5, 0.8, 1.0, 1.2, 1.5, 2.0])
    T3 = rng.choice([310, 320, 330]); Tw1 = rng.choice([10, 15, 20]); dTw = rng.choice([8, 10, 12, 15]); Tw2 = Tw1 + dTw
    r1, r3 = a17.row(T1), a17.row(T3)
    s2s, (a, b), fr = a17.by("Pr", r1["Pr"] * rp); h2s = s2s["h"]
    h2a = r1["h"] + (h2s - r1["h"]) / eta; s2a, (c, d), fr2 = a17.by("h", h2a); T2a = s2a["T"]
    Wd = m * (h2a - r1["h"]); Q = m * (h2a - r3["h"])
    w1, w2 = W.satT(Tw1), W.satT(Tw2); mw = Q / (w2["hf"] - w1["hf"])
    dsa = r3["s"] - r1["s"] - RA * math.log(rp); Sg = m * dsa + mw * (w2["sf"] - w1["sf"])
    T2cold = T1 * (1 + (rp ** E - 1) / eta)
    stem = (f"Air at {P1} kPa and {T1} K is compressed steadily to {P1 * rp} kPa by a compressor with an isentropic efficiency of {int(round(eta * 100))}%, at {m} kg/s. "
            f"It then passes through an aftercooler (a heat exchanger with no pressure drop) and leaves at {T3} K. Cooling water enters the aftercooler at {fT(Tw1)} and leaves at {fT(Tw2)}. "
            "The compressor and aftercooler are insulated. Using variable specific heats for air, determine (a) the air temperature leaving the compressor, (b) the compressor power, "
            "(c) the cooling-water flow rate, and (d) the total rate of entropy generation in the compressor and aftercooler together.")
    parts = [part("a", "Compressor exit temperature, T<sub>2</sub>", "K", T2a, 0.006, 3,
                  [(s2s["T"], "That's T<sub>2s</sub>. The real compressor needs more work, so it runs hotter."), (T2cold, "That's the constant-c<sub>p</sub> result. Use P<sub>r</sub> and h from A-17.")], floor=0.004),
             part("b", "Compressor power, Ẇ<sub>in</sub>", "kW", Wd, 0.01, 3,
                  [(m * (h2s - r1["h"]), "That's the isentropic power. Divide the ideal work by η for a compressor."), (m * (h2s - r1["h"]) * eta, "For a compressor, divide by η; multiplying gives less than the ideal work.")]),
             part("c", "Cooling-water flow, ṁ<sub>w</sub>", "kg/s", mw, 0.015, 3,
                  [(m * (h2s - r3["h"]) / (w2["hf"] - w1["hf"]), "The air enters the aftercooler at the actual h<sub>2</sub>, not h<sub>2s</sub>."),
                   (Q / (4.18 * dTw), "Tables first for liquid water: h<sub>f</sub> at each temperature (A-4).")]),
             part("d", "Total entropy generation, Ṡ<sub>gen</sub>", "kW/K", Sg, 0.02, 3,
                  [(m * (r3["s"] - r1["s"]) + mw * (w2["sf"] - w1["sf"]), "The air's pressure rises, so its Δs includes −R ln(P<sub>3</sub>/P<sub>1</sub>)."),
                   (m * dsa, "That's only the air. The water's entropy rises too, and both streams are inside the boundary.")])]
    steps = [self_step("Find the compressor exit temperature, the power, the water flow and the total entropy generated in a compressor followed by an aftercooler. Plan: A-17 for every air state, the efficiency for state 2, then one energy balance on the cooler and one entropy balance on the whole system."),
             dia("Which T-s sketch shows the compression (1 → 2)?", ["ts_comp", "ts_comp_left", "ts_turb_gas", "ts_comp_isoP"], 0,
                 "The ideal compressor goes straight up (s constant) to 2s on the high-pressure line. The real one generates entropy, so 2 sits to the right of 2s and hotter. The aftercooler then runs left along the high-pressure line to 3."),
             assume([f"P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {T1} K", f"P<sub>2</sub> = P<sub>3</sub> = {P1 * rp} kPa, η<sub>C</sub> = {eta}", f"ṁ = {m} kg/s, T<sub>3</sub> = {T3} K", f"Water: {fT(Tw1)} → {fT(Tw2)}"],
                    ["T<sub>2</sub> (K)", "Ẇ<sub>in</sub> (kW)", "ṁ<sub>w</sub> (kg/s)", "Ṡ<sub>gen</sub> (kW/K)"],
                    [("open", True, "Air and water flow through."), ("steady", True, "Steady operation."), ("adiabatic", True, "Both devices are insulated."),
                     ("ideal", True, "Air at 100 kPa to about 1 MPa and 290+ K: far above its critical point, Z ≈ 1 (rule 2)."),
                     ("a17", True, f"Rule 4: the air's temperature changes by roughly {int(round(T2a - T1, -1))} K, a large ΔT."), ("constPres", True, "Given: no pressure drop in the aftercooler."), ("noshaft", True, "The aftercooler has no shaft or wires.", "The aftercooler has no shaft, wires or moving boundary."),
                     ("liqT", True, "Rule 1: the cooling water's h and s come from A-4 at its temperature."), ("lowke", True, "Small velocities."), ("nope", True, "Same height."),
                     ("isen", True, "For the comparison compressor only: s<sub>2s</sub> = s<sub>1</sub>."),
                     ("constc_big", False, "The ΔT is too large for constant c (rule 4)."), ("cpwater", False, "Tables first for water.")]),
             multi([("P<sub>r2s</sub> = P<sub>r1</sub>(P<sub>2</sub>/P<sub>1</sub>)", True, ""), ("η<sub>C</sub> = (h<sub>2s</sub> − h<sub>1</sub>)/(h<sub>2</sub> − h<sub>1</sub>)", True, ""),
                    ("Aftercooler: ṁ(h<sub>2</sub> − h<sub>3</sub>) = ṁ<sub>w</sub>(h<sub>w2</sub> − h<sub>w1</sub>)", True, ""),
                    ("Ṡ<sub>gen</sub> = ṁ(s°<sub>3</sub> − s°<sub>1</sub> − R ln(P<sub>3</sub>/P<sub>1</sub>)) + ṁ<sub>w</sub>(s<sub>w2</sub> − s<sub>w1</sub>)", True, ""),
                    ("T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>", False, "Constant-c relation; rule 4 says A-17 here."),
                    ("Δs<sub>air</sub> = s°<sub>3</sub> − s°<sub>1</sub>", False, "That's missing the pressure term.")], FIRST_SF),
             multi_terms(["ṁh<sub>2</sub>", "ṁ<sub>w</sub>h<sub>w1</sub>"], ["ṁh<sub>3</sub>", "ṁ<sub>w</sub>h<sub>w2</sub>"],
                         "Aftercooler: ṁ(h<sub>2</sub> − h<sub>3</sub>) = ṁ<sub>w</sub>(h<sub>w2</sub> − h<sub>w1</sub>)",
                         p="Apply the steady-flow first law to the whole aftercooler (both streams inside). Cross out every term that drops."),
             props([("h<sub>1</sub>", r1["h"], "kJ/kg", "A-17", 0.003, f"{T1} K"), ("P<sub>r1</sub>", r1["Pr"], "", "A-17", 0.004, f"{T1} K"), ("s°<sub>1</sub>", r1["s"], "kJ/kg·K", "A-17", 0.003, f"{T1} K"),
                    ("h<sub>3</sub>", r3["h"], "kJ/kg", "A-17", 0.003, f"{T3} K"), ("s°<sub>3</sub>", r3["s"], "kJ/kg·K", "A-17", 0.003, f"{T3} K"),
                    ("h<sub>w1</sub> = h<sub>f</sub>", w1["hf"], "kJ/kg", "A-4", 0.003, fT(Tw1)), ("h<sub>w2</sub> = h<sub>f</sub>", w2["hf"], "kJ/kg", "A-4", 0.003, fT(Tw2)),
                    ("s<sub>w1</sub> = s<sub>f</sub>", w1["sf"], "kJ/kg·K", "A-4", 0.004, fT(Tw1)), ("s<sub>w2</sub> = s<sub>f</sub>", w2["sf"], "kJ/kg·K", "A-4", 0.004, fT(Tw2))]),
             calc([f"P<sub>r2s</sub> = ({sg(r1['Pr'], 4)})({rp}) = {sg(r1['Pr'] * rp, 4)}: {a17where(a, b, fr)}; h<sub>2s</sub> = {sg(h2s, 5)} kJ/kg",
                   f"h<sub>2</sub> = h<sub>1</sub> + (h<sub>2s</sub> − h<sub>1</sub>)/η = {num(r1['h'], 2)} + ({sg(h2s, 5)} − {num(r1['h'], 2)})/{eta} = {sg(h2a, 5)} kJ/kg: {a17where(c, d, fr2)}; T<sub>2</sub> = <b>{sg(T2a)} K</b>",
                   f"Ẇ<sub>in</sub> = ṁ(h<sub>2</sub> − h<sub>1</sub>) = {m}({sg(h2a, 5)} − {num(r1['h'], 2)}) = <b>{sg(Wd)} kW</b>",
                   f"Q̇ = ṁ(h<sub>2</sub> − h<sub>3</sub>) = {sg(Q)} kW; ṁ<sub>w</sub> = Q̇/(h<sub>w2</sub> − h<sub>w1</sub>) = {sg(Q)}/({num(w2['hf'], 2)} − {num(w1['hf'], 2)}) = <b>{sg(mw)} kg/s</b>",
                   f"Δs<sub>air</sub> = s°<sub>3</sub> − s°<sub>1</sub> − R ln(P<sub>3</sub>/P<sub>1</sub>) = {num(r3['s'], 5)} − {num(r1['s'], 5)} − 0.287 ln {rp} = {sg(dsa, 4)} kJ/kg·K (negative: cooled and squeezed)",
                   f"Ṡ<sub>gen</sub> = ṁΔs<sub>air</sub> + ṁ<sub>w</sub>(s<sub>w2</sub> − s<sub>w1</sub>) = ({m})({sg(dsa, 4)}) + ({sg(mw)})({num(w2['sf'], 4)} − {num(w1['sf'], 4)}) = <b>{sg(Sg, 3)} kW/K</b>"]),
             mc(8, "The air's entropy goes down across the whole system. Does that break the second law?",
                ["No: the water's entropy rises by more, and the total generation is positive, which is what the second law requires",
                 "Yes: entropy can never decrease", "No, because the compressor is adiabatic", "Yes, unless the compressor is reversible"],
                0, "One stream's entropy can fall when it gives heat to another stream. The second law is about the total: Ṡ<sub>gen</sub> ≥ 0. Most of the generation here is heat crossing a big temperature gap in the aftercooler, which is why plants use the hot compressed air for something before throwing that heat away.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C4: two metal blocks
METALS = {"iron": 0.45, "copper": 0.385, "aluminum": 0.902}
@template("C4", "Two metal blocks reach equilibrium", 7, "E", 20, "challenge")
def C4(rng):
    hot, cold = rng.sample(list(METALS), 2)
    ch, cc = METALS[hot], METALS[cold]
    mh = rng.choice([10, 15, 20, 25, 30, 40, 50]); mc_ = rng.choice([10, 15, 20, 25, 30, 40, 50])
    Th = rng.choice([150, 200, 250, 300, 350]); Tc = rng.choice([5, 10, 15, 20, 25])
    Tf = (mh * ch * Th + mc_ * cc * Tc) / (mh * ch + mc_ * cc)
    dSh = mh * ch * math.log((Tf + T0K) / (Th + T0K)); dSc = mc_ * cc * math.log((Tf + T0K) / (Tc + T0K)); Sg = dSh + dSc
    Q = mh * ch * (Th - Tf)
    stem = (f"A {mh}-kg {hot} block at {fT(Th)} is placed against a {mc_}-kg {cold} block at {fT(Tc)} inside an insulated enclosure, and the two come to thermal equilibrium. "
            f"Determine (a) the final temperature, (b) the entropy change of the {hot} block, (c) the entropy change of the {cold} block, and (d) the total entropy generated.")
    parts = [part("a", "Final temperature, T<sub>f</sub>", "°C", Tf, 0.006, 2,
                  [((mh * Th + mc_ * Tc) / (mh + mc_), "Mass-weighting isn't enough: weight each block by mc, because the metals store different heat per degree.")]),
             part("b", f"ΔS of the {hot} block", "kJ/K", dSh, 0.01, 2,
                  [(-Q / (Th + T0K), "Q/T only works at constant temperature. The block's temperature falls, so use mc ln(T<sub>f</sub>/T<sub>1</sub>)."),
                   (mh * ch * math.log(Tf / Th), "Use kelvins in the logarithm.")]),
             part("c", f"ΔS of the {cold} block", "kJ/K", dSc, 0.01, 2,
                  [(Q / (Tc + T0K), "Q/T only works at constant temperature. Use mc ln(T<sub>f</sub>/T<sub>1</sub>)."),
                   (mc_ * cc * math.log(Tf / Tc), "Use kelvins in the logarithm.")]),
             part("d", "Entropy generated, S<sub>gen</sub>", "kJ/K", Sg, 0.02, 2, [(-dSh + dSc, "ΔS of the hot block is negative. Add the two changes with their signs.")])]
    steps = [self_step("Find the final temperature and the entropy changes when two metal blocks reach equilibrium in an insulated box. Plan: one first-law balance with both blocks as the system, then mc ln(T<sub>2</sub>/T<sub>1</sub>) for each block."),
             mc(2, "Which system makes the first law simplest?",
                ["Both blocks together: the heat passed between them is internal and the enclosure is insulated, so Q = 0 and W = 0",
                 "The hot block alone, with Q = 0", "The enclosure air, as an open system", "Each block separately, both with Q = 0"],
                0, "With both blocks inside, nothing crosses the boundary, so ΔU<sub>hot</sub> + ΔU<sub>cold</sub> = 0. Pick one block alone and Q is not zero; it's the heat passing between them."),
             assume([f"{hot.capitalize()}: {mh} kg at {fT(Th)}", f"{cold.capitalize()}: {mc_} kg at {fT(Tc)}"],
                    ["T<sub>f</sub> (°C)", f"ΔS<sub>{hot}</sub> (kJ/K)", f"ΔS<sub>{cold}</sub> (kJ/K)", "S<sub>gen</sub> (kJ/K)"],
                    [("closed", True, "No mass crosses the boundary."), ("adiabatic", True, "The enclosure is insulated.", "The enclosure is insulated: no heat crosses the boundary around both blocks."),
                     ("stationary", True, "The blocks don't move: ΔKE = ΔPE = 0."), ("incomp", True, "Solids: Table A-3 gives c."),
                     ("noshaft", True, "No work crosses the boundary.", "No work crosses the boundary: no shaft, no wires, and solids don't do boundary work."),
                     ("tavg", False, "Only if both blocks had the same mc."), ("sconst", False, "Heat flowing across a finite temperature difference generates entropy."),
                     ("isothermal", False, "Both temperatures change.")]),
             multi([("m<sub>h</sub>c<sub>h</sub>(T<sub>f</sub> − T<sub>h</sub>) + m<sub>c</sub>c<sub>c</sub>(T<sub>f</sub> − T<sub>c</sub>) = 0", True, ""), ("ΔS = mc ln(T<sub>2</sub>/T<sub>1</sub>), T in K", True, ""),
                    (SGEN_CL, True, ""), ("ΔS = Q/T", False, "Only for a reservoir at constant temperature."),
                    ("T<sub>f</sub> = (T<sub>h</sub> + T<sub>c</sub>)/2", False, "Only for equal mc.")], FIRST_CL),
             strike_closed({"Qin": (["adiabatic"], "Insulated."), "Qout": (["adiabatic"], "Insulated."), "Win": (["noshaft"], "No work."), "Wout": (["noshaft"], "No work."),
                            "dKE": (["stationary"], "The blocks don't move."), "dPE": (["stationary"], "The blocks don't move.")},
                           f"0 = ΔU<sub>{hot}</sub> + ΔU<sub>{cold}</sub> = m<sub>h</sub>c<sub>h</sub>(T<sub>f</sub> − T<sub>h</sub>) + m<sub>c</sub>c<sub>c</sub>(T<sub>f</sub> − T<sub>c</sub>)"),
             props([(f"c for {hot}", ch, "kJ/kg·K", "A-3", 0.004, hot), (f"c for {cold}", cc, "kJ/kg·K", "A-3", 0.004, cold)]),
             calc([f"T<sub>f</sub> = (m<sub>h</sub>c<sub>h</sub>T<sub>h</sub> + m<sub>c</sub>c<sub>c</sub>T<sub>c</sub>)/(m<sub>h</sub>c<sub>h</sub> + m<sub>c</sub>c<sub>c</sub>) = ({mh}·{ch}·{Th} + {mc_}·{cc}·{Tc})/({mh}·{ch} + {mc_}·{cc}) = <b>{num(Tf, 1)} °C</b> = {num(Tf + T0K, 2)} K",
                   f"ΔS<sub>{hot}</sub> = ({mh})({ch}) ln({num(Tf + T0K, 2)}/{num(Th + T0K, 2)}) = <b>{sg(dSh, 4)} kJ/K</b>",
                   f"ΔS<sub>{cold}</sub> = ({mc_})({cc}) ln({num(Tf + T0K, 2)}/{num(Tc + T0K, 2)}) = <b>+{sg(dSc, 4)} kJ/K</b>",
                   f"Isolated system, no heat crosses: S<sub>gen</sub> = ΔS<sub>{hot}</sub> + ΔS<sub>{cold}</sub> = <b>{sg(Sg, 3)} kJ/K</b>"]),
             mc(8, "The hot block's entropy falls. Why is the total still positive?",
                ["The same heat leaves the hot block at high T and enters the cold block at low T, and Q/T is bigger at the lower temperature",
                 "Because the cold block is heavier", "It isn't always positive; it depends on the metals", "Because metal is incompressible"],
                0, f"Energy is conserved ({sg(Q)} kJ leaves one block and enters the other), but entropy isn't: heat crossing a temperature difference always generates entropy. "
                   "Only if the blocks started at the same temperature would S<sub>gen</sub> be zero.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C5: rigid tank of steam cools
@template("C5", "Rigid tank of steam cools to the room", 7, "E", 20, "challenge")
def C5(rng):
    P1 = rng.choice([200, 300, 400, 600, 800, 1000]); T1 = rng.choice([t for t in W.SH[P1] if 200 <= t <= 500]); V = rng.choice([0.2, 0.3, 0.4, 0.5, 0.8, 1.0])
    Tc0 = rng.choice([20, 25, 30]); T0 = Tc0 + T0K
    s1 = W.sh(P1, T1); m = V / s1["v"]; st = W.satT(Tc0)
    x2 = (s1["v"] - st["vf"]) / (st["vg"] - st["vf"]); assert 0 < x2 < 1
    u2 = st["uf"] + x2 * st["ufg"]; s2 = st["sf"] + x2 * st["sfg"]; P2 = st["P"]
    Q = m * (s1["u"] - u2); dS = m * (s2 - s1["s"]); Sg = dS + Q / T0
    h2 = st["hf"] + x2 * st["hfg"]
    stem = (f"A {V}-m³ rigid tank holds steam at {fP(P1)} and {fT(T1)}. It sits in a room at {fT(Tc0)} and cools until the steam reaches room temperature. "
            "Determine (a) the final pressure, (b) the final quality, (c) the heat transferred to the room, and (d) the total entropy generated, counting the room.")
    parts = [part("a", "Final pressure, P<sub>2</sub>", "kPa", P2, 0.006, 2, [(P1 * Tc0 / T1, "Steam isn't an ideal gas, and it condenses. At room temperature inside the dome, P = P<sub>sat</sub>@T<sub>2</sub>."),
                                                                              (P1 * (Tc0 + T0K) / (T1 + T0K), "Steam isn't an ideal gas. Once it's in the dome, P = P<sub>sat</sub>@T<sub>2</sub>.")]),
             part("b", "Final quality, x<sub>2</sub>", "", x2, 0.01, 2, [(s1["v"] / st["vg"], "x = (v − v<sub>f</sub>)/v<sub>fg</sub>. Subtract v<sub>f</sub> (it's tiny here, so check your digits).")] if abs(s1["v"] / st["vg"] - x2) / x2 > 0.006 else []),
             part("c", "Heat to the room, Q<sub>out</sub>", "kJ", Q, 0.01, 3, [(m * (s1["h"] - h2), "A rigid tank does no boundary work, so Q<sub>out</sub> = m(u<sub>1</sub> − u<sub>2</sub>), not Δh.")]),
             part("d", "Total entropy generated, S<sub>gen</sub>", "kJ/K", Sg, 0.02, 3,
                  [(dS, "That's only the steam. The room gains Q/T<sub>0</sub>, and S<sub>gen</sub> = ΔS<sub>steam</sub> + Q<sub>out</sub>/T<sub>0</sub>."),
                   (dS + Q / Tc0, "Use T<sub>0</sub> in kelvins.")])]
    steps = [self_step("Find the final pressure and quality, the heat lost and the entropy generated when a rigid tank of steam cools to room temperature. Plan: v stays constant, so state 2 is fixed by T<sub>2</sub> and v<sub>2</sub> = v<sub>1</sub>; then the closed-system first law and an entropy balance with the room as a reservoir."),
             mc(2, "On a T-v diagram, which path does the steam follow?",
                ["Straight down a vertical line (v constant) from the superheated region into the dome", "Horizontally to the left at constant T", "Down and to the left along a constant-pressure line", "Straight up at constant v"],
                0, "A rigid tank fixes v. Cooling drops T at constant v, so the state falls straight down and enters the dome; at room temperature it is a wet mixture at P<sub>sat</sub>."),
             assume([f"V = {V} m³, rigid", f"State 1: {fP(P1)}, {fT(T1)}", f"T<sub>2</sub> = T<sub>0</sub> = {fT(Tc0)}"],
                    ["P<sub>2</sub> (kPa)", "x<sub>2</sub>", "Q<sub>out</sub> (kJ)", "S<sub>gen</sub> (kJ/K)"],
                    [("closed", True, "No mass crosses the boundary."), ("rigid", True, "Given: a rigid tank."), ("stationary", True, "The tank doesn't move."),
                     ("steam", True, "Rule 1: A-6 for state 1, A-4 for the mixture at room temperature."),
                     ("reservoir", True, "The room is large enough to stay at T<sub>0</sub>.", "The room acts as a thermal reservoir at T<sub>0</sub>."),
                     ("steamideal", False, "Rule 1: tables for steam, and it condenses."), ("constP", False, "Rigid tank: v is constant, P falls."), ("adiabatic", False, "Heat leaves to the room.")]),
             multi([("v<sub>2</sub> = v<sub>1</sub> = V/m", True, ""), (FIRST_CL, True, ""), (SGEN_CL, True, ""), ("ΔS<sub>room</sub> = Q<sub>out</sub>/T<sub>0</sub>", True, ""),
                    ("P<sub>1</sub>/T<sub>1</sub> = P<sub>2</sub>/T<sub>2</sub>", False, "Ideal-gas relation; steam isn't ideal and it condenses."), ("Q = mΔh", False, "That's for constant pressure. A rigid tank uses Δu.")], FIRST_CL),
             strike_closed({"Qin": (["dir"], "Heat leaves."), "Win": (["rigid"], "Rigid: no boundary work."), "Wout": (["rigid"], "Rigid: no boundary work."),
                            "dKE": (["stationary"], "The tank doesn't move."), "dPE": (["stationary"], "The tank doesn't move.")}, "−Q<sub>out</sub> = m(u<sub>2</sub> − u<sub>1</sub>)"),
             props([("v<sub>1</sub>", s1["v"], "m³/kg", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"), ("u<sub>1</sub>", s1["u"], "kJ/kg", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"),
                    ("s<sub>1</sub>", s1["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P1)} block, {fT(T1)} row"), ("P<sub>sat</sub> at T<sub>2</sub>", P2, "kPa", "A-4", 0.004, fT(Tc0)),
                    ("v<sub>f</sub> at T<sub>2</sub>", st["vf"], "m³/kg", "A-4", 0.003, fT(Tc0)), ("v<sub>g</sub> at T<sub>2</sub>", st["vg"], "m³/kg", "A-4", 0.003, fT(Tc0)),
                    ("u<sub>f</sub>, u<sub>fg</sub> at T<sub>2</sub>: u<sub>f</sub>", st["uf"], "kJ/kg", "A-4", 0.003, fT(Tc0)), ("u<sub>fg</sub> at T<sub>2</sub>", st["ufg"], "kJ/kg", "A-4", 0.003, fT(Tc0)),
                    ("s<sub>f</sub> at T<sub>2</sub>", st["sf"], "kJ/kg·K", "A-4", 0.004, fT(Tc0)), ("s<sub>fg</sub> at T<sub>2</sub>", st["sfg"], "kJ/kg·K", "A-4", 0.003, fT(Tc0))]),
             calc([f"m = V/v<sub>1</sub> = {V}/{sg(s1['v'], 5)} = {sg(m)} kg",
                   f"v<sub>2</sub> = v<sub>1</sub> = {sg(s1['v'], 5)} m³/kg, which is between v<sub>f</sub> and v<sub>g</sub> at {fT(Tc0)}, so it's a mixture: P<sub>2</sub> = P<sub>sat</sub> = <b>{sg(P2)} kPa</b>",
                   f"x<sub>2</sub> = (v<sub>2</sub> − v<sub>f</sub>)/(v<sub>g</sub> − v<sub>f</sub>) = ({sg(s1['v'], 5)} − {st['vf']})/({sg(st['vg'], 5)} − {st['vf']}) = <b>{sg(x2, 4)}</b>",
                   f"u<sub>2</sub> = u<sub>f</sub> + x<sub>2</sub>u<sub>fg</sub> = {num(st['uf'], 2)} + ({sg(x2, 4)})({num(st['ufg'], 2)}) = {sg(u2, 5)} kJ/kg",
                   f"Q<sub>out</sub> = m(u<sub>1</sub> − u<sub>2</sub>) = ({sg(m)})({num(s1['u'], 1)} − {sg(u2, 5)}) = <b>{sg(Q)} kJ</b>",
                   f"s<sub>2</sub> = s<sub>f</sub> + x<sub>2</sub>s<sub>fg</sub> = {sg(s2, 5)} kJ/kg·K; ΔS<sub>steam</sub> = m(s<sub>2</sub> − s<sub>1</sub>) = {sg(dS, 4)} kJ/K",
                   f"S<sub>gen</sub> = ΔS<sub>steam</sub> + Q<sub>out</sub>/T<sub>0</sub> = {sg(dS, 4)} + {sg(Q)}/{num(T0, 2)} = <b>{sg(Sg, 3)} kJ/K</b>"]),
             mc(8, f"The steam's entropy drops by {sg(-dS, 3)} kJ/K. Is S<sub>gen</sub> = {sg(Sg, 3)} kJ/K believable?",
                ["Yes: the room gains Q/T<sub>0</sub>, which is more than the steam loses, because the heat left the steam at temperatures above T<sub>0</sub>",
                 "No: S<sub>gen</sub> should equal the steam's entropy drop", "No: S<sub>gen</sub> must be zero for a closed system", "Yes, but only because the tank is rigid"],
                0, "The steam gave up heat while it was hotter than the room. That heat-transfer across a temperature difference is where the generation comes from. "
                   "Also notice how little steam is left as vapor at room temperature: x<sub>2</sub> is small because v<sub>g</sub> at room temperature is huge.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C6: R-134a heated at constant P by a reservoir
@template("C6", "R-134a heated at constant pressure by a reservoir", 7, "E", 20, "challenge")
def C6(rng):
    P = rng.choice([200, 240, 280, 320, 400, 500, 600, 700, 800]); m = rng.choice([0.5, 0.8, 1.0, 1.5, 2.0, 2.5, 3.0]); x1 = rng.choice([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    st = RF.satP(P); T2 = rng.choice([t for t in RF.SH[P] if t >= st["T"] + 15 and t <= 90]); s2 = RF.sh(P, T2)
    TR = rng.choice([T2 + 20, T2 + 40, T2 + 60, T2 + 80]); TRK = TR + T0K
    v1 = st["vf"] + x1 * (st["vg"] - st["vf"]); u1 = st["uf"] + x1 * st["ufg"]; h1 = st["hf"] + x1 * st["hfg"]; ss1 = st["sf"] + x1 * st["sfg"]
    Wb = m * P * (s2["v"] - v1); Q = m * (s2["h"] - h1); dS = m * (s2["s"] - ss1); Sg = dS - Q / TRK
    stem = (f"A piston-cylinder device holds {m} kg of R-134a at {P} kPa with a quality of {x1}. Heat flows in from a reservoir at {fT(TR)} until the R-134a reaches {fT(T2)}, "
            "while the piston's weight keeps the pressure constant. Determine (a) the boundary work, (b) the heat transferred, (c) the entropy change of the R-134a, and (d) the total entropy generated, counting the reservoir.")
    parts = [part("a", "Boundary work, W<sub>b,out</sub>", "kJ", Wb, 0.01, 2, [(m * P * s2["v"], "W<sub>b</sub> = mP(v<sub>2</sub> − v<sub>1</sub>): subtract the starting volume.")]),
             part("b", "Heat in, Q<sub>in</sub>", "kJ", Q, 0.01, 3,
                  [(m * (s2["u"] - u1), "That leaves out the boundary work. At constant P, Q<sub>in</sub> = ΔU + W<sub>b,out</sub> = mΔh."),
                   (m * (s2["u"] - u1) - Wb, "The boundary work goes out, so it adds to the heat needed: Q<sub>in</sub> = ΔU + W<sub>b,out</sub>.")]),
             part("c", "ΔS of the R-134a", "kJ/K", dS, 0.01, 2, [(m * (s2["s"] - st["sg"]), "s<sub>1</sub> is for the mixture: s<sub>f</sub> + x<sub>1</sub>s<sub>fg</sub>, not s<sub>g</sub>.")]),
             part("d", "Total entropy generated, S<sub>gen</sub>", "kJ/K", Sg, 0.02, 3,
                  [(dS + Q / TRK, "The reservoir loses heat, so its entropy falls: S<sub>gen</sub> = ΔS<sub>R-134a</sub> − Q/T<sub>R</sub>."), (dS - Q / TR, "Use T<sub>R</sub> in kelvins.")])]
    steps = [self_step("Find the boundary work, heat, entropy change and entropy generated when R-134a is heated at constant pressure by a hotter reservoir. Plan: fix both states from the R-134a tables, use the constant-pressure first law, then add the reservoir's entropy change."),
             mc(2, "On a P-v diagram, which path does the R-134a follow?",
                ["A horizontal line to the right: constant pressure, from inside the dome out into the superheated region",
                 "A vertical line up: constant volume", "A curve down and to the right, like an isotherm", "A horizontal line to the left"],
                0, "The piston's weight fixes P. Heating boils off the liquid and then superheats the vapor, so v grows along a horizontal line."),
             assume([f"m = {m} kg, P = {P} kPa", f"x<sub>1</sub> = {x1}", f"T<sub>2</sub> = {fT(T2)}", f"Reservoir: {fT(TR)}"],
                    ["W<sub>b</sub> (kJ)", "Q<sub>in</sub> (kJ)", "ΔS (kJ/K)", "S<sub>gen</sub> (kJ/K)"],
                    [("closed", True, "No mass crosses the boundary."), ("qe", True, "The piston's weight holds P constant."), ("stationary", True, "The device doesn't move."),
                     ("r134", True, "Rule 1: A-12 for the mixture, A-13 for the superheated end state."), ("reservoir", True, "The heat source stays at T<sub>R</sub>.", "The heat comes from a thermal reservoir at T<sub>R</sub>."),
                     ("r134ideal", False, "Rule 1: R-134a uses its tables."), ("constv", False, "The piston moves."), ("isothermal", False, "The temperature rises once the liquid is gone.")]),
             multi([("W<sub>b</sub> = mP(v<sub>2</sub> − v<sub>1</sub>)", True, ""), (FIRST_CL, True, ""), ("At constant P: Q<sub>in</sub> = m(h<sub>2</sub> − h<sub>1</sub>)", True, ""),
                    (SGEN_CL, True, ""), ("Q<sub>in</sub> = m(u<sub>2</sub> − u<sub>1</sub>)", False, "That forgets the boundary work."), ("ΔS = Q/T<sub>R</sub>", False, "That's the reservoir, not the R-134a.")], FIRST_CL),
             strike_closed({"Qout": (["dir"], "Heat comes in."), "Win": (["dir"], "The gas pushes the piston out."), "dKE": (["stationary"], "Doesn't move."), "dPE": (["stationary"], "Doesn't move.")},
                           "Q<sub>in</sub> − W<sub>b,out</sub> = m(u<sub>2</sub> − u<sub>1</sub>), and with W<sub>b,out</sub> = mP(v<sub>2</sub> − v<sub>1</sub>): Q<sub>in</sub> = m(h<sub>2</sub> − h<sub>1</sub>)"),
             props([("v<sub>f</sub>", st["vf"], "m³/kg", "A-12", 0.003, f"{P} kPa"), ("v<sub>g</sub>", st["vg"], "m³/kg", "A-12", 0.003, f"{P} kPa"),
                    ("h<sub>f</sub>", st["hf"], "kJ/kg", "A-12", 0.003, f"{P} kPa"), ("h<sub>fg</sub>", st["hfg"], "kJ/kg", "A-12", 0.003, f"{P} kPa"),
                    ("s<sub>f</sub>", st["sf"], "kJ/kg·K", "A-12", 0.003, f"{P} kPa"), ("s<sub>fg</sub>", st["sfg"], "kJ/kg·K", "A-12", 0.003, f"{P} kPa"),
                    ("v<sub>2</sub>", s2["v"], "m³/kg", "A-13", 0.003, f"{P} kPa block, {fT(T2)} row"), ("h<sub>2</sub>", s2["h"], "kJ/kg", "A-13", 0.003, f"{P} kPa block, {fT(T2)} row"),
                    ("s<sub>2</sub>", s2["s"], "kJ/kg·K", "A-13", 0.003, f"{P} kPa block, {fT(T2)} row")]),
             calc([f"v<sub>1</sub> = v<sub>f</sub> + x<sub>1</sub>v<sub>fg</sub> = {sg(v1, 4)} m³/kg; h<sub>1</sub> = h<sub>f</sub> + x<sub>1</sub>h<sub>fg</sub> = {sg(h1, 5)} kJ/kg; s<sub>1</sub> = s<sub>f</sub> + x<sub>1</sub>s<sub>fg</sub> = {sg(ss1, 5)} kJ/kg·K",
                   f"W<sub>b</sub> = mP(v<sub>2</sub> − v<sub>1</sub>) = ({m})({P})({sg(s2['v'], 5)} − {sg(v1, 4)}) = <b>{sg(Wb)} kJ</b>",
                   f"Q<sub>in</sub> = m(h<sub>2</sub> − h<sub>1</sub>) = ({m})({num(s2['h'], 2)} − {sg(h1, 5)}) = <b>{sg(Q)} kJ</b>",
                   f"ΔS = m(s<sub>2</sub> − s<sub>1</sub>) = ({m})({num(s2['s'], 4)} − {sg(ss1, 5)}) = <b>{sg(dS, 4)} kJ/K</b>",
                   f"S<sub>gen</sub> = ΔS − Q<sub>in</sub>/T<sub>R</sub> = {sg(dS, 4)} − {sg(Q)}/{num(TRK, 2)} = <b>{sg(Sg, 3)} kJ/K</b>"]),
             mc(8, f"What would happen to S<sub>gen</sub> if the reservoir were at {fT(T2)} instead of {fT(TR)}?",
                ["It would shrink: heat would cross a smaller temperature difference", "It would grow", "It wouldn't change", "It would become negative"],
                0, "S<sub>gen</sub> here comes from heat crossing the gap between the reservoir and the colder R-134a. A cooler reservoir means a smaller gap, so less generation. It can't go below zero.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C7: engine driving a heat pump
@template("C7", "Fuel-fired engine driving a heat pump", 6, "D", 14, "challenge")
def C7(rng):
    TH = rng.choice([700, 800, 900, 1000, 1100]); Th = rng.choice([20, 21, 22]); To = rng.choice([-10, -5, 0, 5])
    QH = rng.choice([10, 15, 20, 25, 30]); eta = rng.choice([0.25, 0.28, 0.30, 0.32, 0.35]); COP = rng.choice([2.5, 2.8, 3.0, 3.2, 3.5])
    THK, ThK, ToK = TH + T0K, Th + T0K, To + T0K
    etaC = 1 - ThK / THK; COPC = ThK / (ThK - ToK); assert eta < 0.8 * etaC and COP < 0.8 * COPC
    Wd = eta * QH; Qhouse = QH * (1 - eta) + Wd * COP; Qmax = QH * (1 - etaC + etaC * COPC)
    stem = (f"A home is heated by a small engine and a heat pump. The engine burns fuel, receiving {QH} kW of heat at {fT(TH)}, and runs at a thermal efficiency of {int(round(eta * 100))}%. "
            f"Its waste heat goes into the house at {fT(Th)}. All of its work drives a heat pump with a COP of {COP}, which takes heat from the outdoors at {fT(To)} and delivers it to the house. "
            "Determine (a) the engine's power output, (b) the total heat delivered to the house, and (c) the most heat the house could receive from the same fuel if both machines were reversible.")
    parts = [part("a", "Engine power, Ẇ", "kW", Wd, 0.01, 4, []),
             part("b", "Heat to the house, Q̇<sub>house</sub>", "kW", Qhouse, 0.01, 5,
                  [(Wd * COP, "The engine's waste heat Q̇<sub>L</sub> goes into the house too."), (QH * (1 - eta), "That's only the engine's waste heat. Add the heat pump's Q̇<sub>H</sub> = COP·Ẇ."),
                   (QH * (1 - eta) + Wd * (COP - 1), "The heat pump delivers COP·Ẇ to the house, not (COP − 1)·Ẇ.")]),
             part("c", "Reversible limit, Q̇<sub>house,max</sub>", "kW", Qmax, 0.015, 5,
                  [(QH * (1 - (Th / TH) + (Th / TH) * Th / (Th - To)), "Carnot needs kelvins."),
                   (QH * (1 - etaC) + QH * (1 - ToK / THK) * COPC, "The engine rejects heat to the house, so its Carnot limit runs between T<sub>H</sub> and T<sub>house</sub>, not the outdoors."),
                   (QH * etaC * COPC, "Don't forget the engine's waste heat, which also heats the house.")])]
    steps = [self_step("Find the engine's power, the heat reaching the house, and the reversible upper limit for an engine-driven heat pump. Plan: treat each machine as a cycle with its own first law, then add what each puts into the house."),
             mc(2, "Sketch the two machines between their reservoirs. Which picture is right?",
                ["Engine: fuel at T<sub>H</sub> → engine → house at T<sub>house</sub>, with W out. Heat pump: outdoors → heat pump (W in) → house. The house receives two heat flows.",
                 "Engine: fuel → engine → outdoors. Heat pump: outdoors → house.", "One machine between the fuel and the outdoors", "The heat pump moves heat from the house to the outdoors"],
                0, "The house is the cold reservoir for the engine and the hot reservoir for the heat pump. That's why the engine's waste heat isn't wasted here."),
             assume([f"Engine: Q̇<sub>H</sub> = {QH} kW at {fT(TH)}, η = {eta}", f"Heat pump: COP = {COP}", f"House {fT(Th)}, outdoors {fT(To)}"],
                    ["Ẇ (kW)", "Q̇<sub>house</sub> (kW)", "Q̇<sub>house,max</sub> (kW)"],
                    [("cycle", True, "Both machines run in cycles."), ("reservoir", True, "Fuel, house and outdoors stay at their temperatures."),
                     ("steady", True, "Steady operation.", "Steady operation: all rates are constant."), ("rev2", True, "Only for part (c)."),
                     ("rev", False, "The actual machines have η and COP well below Carnot."), ("adiabatic", False, "These are heat engines; heat is the point.")]),
             multi([("Engine: Ẇ = ηQ̇<sub>H</sub>; Q̇<sub>L</sub> = Q̇<sub>H</sub> − Ẇ", True, ""), ("Heat pump: Q̇<sub>H,HP</sub> = COP·Ẇ", True, ""),
                    ("η<sub>Carnot</sub> = 1 − T<sub>house</sub>/T<sub>H</sub>; COP<sub>HP,Carnot</sub> = T<sub>house</sub>/(T<sub>house</sub> − T<sub>out</sub>), in K", True, ""),
                    (FIRST_CYC, True, ""), ("η<sub>Carnot</sub> = 1 − T<sub>out</sub>/T<sub>H</sub>", False, "The engine rejects to the house, not the outdoors."),
                    ("COP<sub>HP</sub> = T<sub>out</sub>/(T<sub>house</sub> − T<sub>out</sub>)", False, "That's the refrigerator COP.")], FIRST_CYC),
             cycle_terms("Q̇<sub>H</sub>", "Q̇<sub>L</sub>", False, "Engine: Q̇<sub>H</sub> = Ẇ<sub>out</sub> + Q̇<sub>L</sub>, so Q̇<sub>L</sub> = Q̇<sub>H</sub>(1 − η)"),
             props([("T<sub>H</sub>", THK, "K", "Given / computed", 0.002, None), ("T<sub>house</sub>", ThK, "K", "Given / computed", 0.002, None), ("T<sub>out</sub>", ToK, "K", "Given / computed", 0.002, None)]),
             calc([f"Ẇ = ηQ̇<sub>H</sub> = ({eta})({QH}) = <b>{sg(Wd)} kW</b>; engine waste heat to the house Q̇<sub>L</sub> = {QH} − {sg(Wd)} = {sg(QH - Wd)} kW",
                   f"Heat pump: Q̇<sub>H,HP</sub> = COP·Ẇ = ({COP})({sg(Wd)}) = {sg(Wd * COP)} kW",
                   f"Q̇<sub>house</sub> = {sg(QH - Wd)} + {sg(Wd * COP)} = <b>{sg(Qhouse)} kW</b> ({sg(Qhouse / QH, 3)} kW per kW of fuel)",
                   f"Limits: η<sub>C</sub> = 1 − {num(ThK, 2)}/{num(THK, 2)} = {sg(etaC, 3)}; COP<sub>C</sub> = {num(ThK, 2)}/({num(ThK, 2)} − {num(ToK, 2)}) = {sg(COPC, 3)}",
                   f"Q̇<sub>house,max</sub> = Q̇<sub>H</sub>[(1 − η<sub>C</sub>) + η<sub>C</sub>COP<sub>C</sub>] = {QH}[{sg(1 - etaC, 3)} + ({sg(etaC, 3)})({sg(COPC, 3)})] = <b>{sg(Qmax)} kW</b>"]),
             mc(8, f"A plain furnace would put about {QH} kW into the house. What does this comparison say?",
                [f"This system delivers {sg(Qhouse / QH, 3)} times the fuel's heat, and the reversible limit is {sg(Qmax / QH, 3)} times: burning fuel straight into a house wastes most of its potential",
                 "It breaks the first law; you can't get more heat than the fuel's energy", "The furnace is better because it has no losses", "They're the same once you count the outdoors"],
                0, "Energy is conserved: the extra heat comes from the cold outdoors, pumped in with the engine's work. A furnace turns high-temperature heat into low-temperature heat directly and throws away the chance to make work along the way.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C8: heat-driven cooler, three reservoirs
@template("C8", "Heat-driven vaccine cooler with no work input", 6, "D", 14, "hardest")
def C8(rng):
    Ts = rng.choice([90, 100, 120, 150, 180]); TL = rng.choice([2, 4, 5]); To = rng.choice([30, 35, 40, 45])
    TsK, TLK, ToK = Ts + T0K, TL + T0K, To + T0K
    Qs = rng.choice([0.5, 0.8, 1.0, 1.2, 1.5, 2.0])
    copmax = (1 - ToK / TsK) * TLK / (ToK - TLK)
    frac = rng.choice([0.4, 0.5, 0.6, 0.7, 1.25, 1.4, 1.6])
    QL = round(frac * copmax * Qs, 2); assert QL > 0.05
    Qo = Qs + QL; Sg = Qo / ToK - Qs / TsK - QL / TLK
    assert abs(Sg) > 2e-4
    QLmax = copmax * Qs
    stem = (f"An inventor claims a vaccine cooler for clinics without reliable power. It has no compressor and no electrical input: it takes {Qs} kW of heat from a solar-heated fluid at {fT(Ts)}, "
            f"removes {QL} kW from the vaccine compartment at {fT(TL)}, and rejects heat to the outdoor air at {fT(To)}. "
            "Treating all three as reservoirs, determine (a) the heat rejected to the outdoors, (b) the rate of entropy generation (a negative value means the claim is impossible), and "
            "(c) the most heat that could be removed from the compartment with the same heat input.")
    parts = [part("a", "Heat rejected, Q̇<sub>out</sub>", "kW", Qo, 0.005, 3, [(Qs - QL, "Both the source heat and the heat pulled from the compartment have to go somewhere: Q̇<sub>out</sub> = Q̇<sub>s</sub> + Q̇<sub>L</sub>.")]),
             part("b", "Entropy generation, Ṡ<sub>gen</sub> (kW/K; negative = impossible)", "kW/K", Sg, 0.03, 5,
                  [(-Sg, "Sign: heat leaving the device to the outdoors carries entropy out of the device into the air. Ṡ<sub>gen</sub> = Q̇<sub>out</sub>/T<sub>0</sub> − Q̇<sub>s</sub>/T<sub>s</sub> − Q̇<sub>L</sub>/T<sub>L</sub>."),
                   (Qo / To - Qs / Ts - QL / TL, "Use kelvins.")]),
             part("c", "Most heat removable, Q̇<sub>L,max</sub>", "kW", QLmax, 0.01, 4,
                  [(Qs * (1 - ToK / TsK), "That's the work a Carnot engine could make. Run that work through a Carnot refrigerator: × T<sub>L</sub>/(T<sub>0</sub> − T<sub>L</sub>)."),
                   (Qs * TLK / (ToK - TLK), "That treats the heat input as if it were work. Heat is worth only (1 − T<sub>0</sub>/T<sub>s</sub>) of its value as work.")])]
    verdict = "possible (Ṡ<sub>gen</sub> &gt; 0)" if Sg > 0 else "impossible (Ṡ<sub>gen</sub> &lt; 0)"
    ctx = {"t": "Keeping vaccines cold without the grid",
           "b": "Most vaccines must stay between 2 and 8 °C from factory to arm. Many rural clinics have no grid power or lose it often, so they rely on solar direct-drive refrigerators or on heat-driven absorption fridges that run on gas or kerosene. When the cold chain breaks, doses spoil and people in the hardest-to-reach places go without.",
           "q": "This problem asks only whether a claim obeys physics. What else should a health ministry ask before buying thousands of these coolers for remote clinics, and who should be in the room when it decides?",
           "src": ["WHO PQS specification for vaccine refrigerators (E003)", "https://extranet.who.int/prequal/key-resources/documents/pqs-performance-specification-e003rf051-refrigerator-or-combined"]}
    steps = [self_step("Decide whether a heat-driven cooler with three reservoirs obeys both laws, and find its best possible cooling. Plan: first law for the outdoor heat, entropy balance for the verdict, then a Carnot engine driving a Carnot refrigerator for the limit."),
             mc(2, "Draw the energy flows. Which picture is right?",
                ["Heat in from the hot source and from the cold compartment; heat out to the outdoors; no work",
                 "Heat in from the hot source; heat out to both the compartment and the outdoors", "Heat in from the outdoors; heat out to the compartment", "Work in; heat out to the compartment"],
                0, "A cooler pulls heat out of the cold space. With no work, the only way to pay for that is high-temperature heat from the source. All of it ends up in the outdoor air."),
             assume([f"Q̇<sub>s</sub> = {Qs} kW at {fT(Ts)}", f"Q̇<sub>L</sub> = {QL} kW from {fT(TL)}", f"Outdoors: {fT(To)}", "Ẇ = 0"],
                    ["Q̇<sub>out</sub> (kW)", "Ṡ<sub>gen</sub> (kW/K)", "Q̇<sub>L,max</sub> (kW)"],
                    [("cycle", True, "The cooler runs in a cycle; its own entropy doesn't change."), ("reservoir", True, "Given."),
                     ("noshaft", True, "No compressor and no electrical input.", "No work crosses the boundary."), ("rev2", True, "Only for part (c)."),
                     ("sconst", False, "That's the reversible limit, not the claim."), ("adiabatic", False, "Heat crosses at three places.")]),
             multi([("Q̇<sub>s</sub> + Q̇<sub>L</sub> = Q̇<sub>out</sub>", True, ""), ("Ṡ<sub>gen</sub> = Q̇<sub>out</sub>/T<sub>0</sub> − Q̇<sub>s</sub>/T<sub>s</sub> − Q̇<sub>L</sub>/T<sub>L</sub> ≥ 0", True, ""),
                    ("Q̇<sub>L,max</sub> = Q̇<sub>s</sub>(1 − T<sub>0</sub>/T<sub>s</sub>)·T<sub>L</sub>/(T<sub>0</sub> − T<sub>L</sub>)", True, ""),
                    ("COP = T<sub>L</sub>/(T<sub>0</sub> − T<sub>L</sub>)", False, "That's for a work-driven refrigerator. Here the input is heat."),
                    ("η = 1 − T<sub>L</sub>/T<sub>s</sub>", False, "The engine part rejects to the outdoors, not the compartment.")], FIRST_CYC),
             strike_custom([term("Qs", "Q̇<sub>s</sub>", "L", "+"), term("QL", "Q̇<sub>L</sub>", "L", "+"), term("Win", "Ẇ<sub>in</sub>", "L", "+", True, ["noshaft"], "No work input."),
                            term("Qout", "Q̇<sub>out</sub>", "L", "−"), term("Wout", "Ẇ<sub>out</sub>", "L", "−", True, ["noshaft"], "No work output."),
                            term("dE", "dE/dt", "R", "", True, ["cycle"], "Cyclic device.")], "Q̇<sub>out</sub> = Q̇<sub>s</sub> + Q̇<sub>L</sub>",
                           p="Apply the first law to the cooler. Cross out every term that drops."),
             props([("T<sub>s</sub>", TsK, "K", "Given / computed", 0.002, None), ("T<sub>L</sub>", TLK, "K", "Given / computed", 0.002, None), ("T<sub>0</sub>", ToK, "K", "Given / computed", 0.002, None)]),
             calc([f"Q̇<sub>out</sub> = {Qs} + {QL} = <b>{sg(Qo)} kW</b>",
                   f"Ṡ<sub>gen</sub> = {sg(Qo)}/{num(ToK, 2)} − {Qs}/{num(TsK, 2)} − {QL}/{num(TLK, 2)} = {sg(Qo / ToK, 4)} − {sg(Qs / TsK, 4)} − {sg(QL / TLK, 4)} = <b>{sg(Sg, 3)} kW/K</b>: the claim is {verdict}",
                   f"Limit: a Carnot engine from {fT(Ts)} to {fT(To)} turns Q̇<sub>s</sub> into Ẇ = {Qs}(1 − {num(ToK, 2)}/{num(TsK, 2)}) = {sg(Qs * (1 - ToK / TsK), 4)} kW",
                   f"That work drives a Carnot refrigerator with COP = {num(TLK, 2)}/({num(ToK, 2)} − {num(TLK, 2)}) = {sg(TLK / (ToK - TLK), 4)}",
                   f"Q̇<sub>L,max</sub> = ({sg(Qs * (1 - ToK / TsK), 4)})({sg(TLK / (ToK - TLK), 4)}) = <b>{sg(QLmax)} kW</b> (the claim is {QL} kW)"]),
             mc(8, "Check your verdict against part (c). What must be true?",
                ["The claim is possible exactly when Q̇<sub>L</sub> ≤ Q̇<sub>L,max</sub>, and Ṡ<sub>gen</sub> has the matching sign",
                 "Part (c) and the sign of Ṡ<sub>gen</sub> can disagree", "Any claim with Q̇<sub>out</sub> = Q̇<sub>s</sub> + Q̇<sub>L</sub> is possible", "The claim is possible if Q̇<sub>L</sub> &lt; Q̇<sub>s</sub>"],
                0, f"The first law alone can't catch a bad claim; any numbers can be made to balance. The second law can. Here Q̇<sub>L</sub> = {QL} kW against a limit of {sg(QLmax)} kW, so the verdict is {verdict}. "
                   "Notice how hot weather hurts: a higher T<sub>0</sub> cuts both the engine part and the refrigerator part.")]
    return stem, parts, steps, ctx, prm(locals())

# =================================================================== C9: hot-gas nozzle with isentropic efficiency (A-17)
@template("C9", "Hot-gas nozzle with isentropic efficiency", 7, "E", 20, "challenge")
def C9(rng):
    P1 = rng.choice([200, 250, 300, 350, 400]); T1 = rng.choice([700, 760, 800, 860, 900, 1000]); V1 = rng.choice([20, 30, 40, 50])
    P2 = rng.choice([85, 90, 95, 100]); eta = rng.choice([0.90, 0.92, 0.93, 0.94, 0.95, 0.96])
    r1 = a17.row(T1); s2s, (a, b), fr = a17.by("Pr", r1["Pr"] * P2 / P1); h2s = s2s["h"]
    h2a = r1["h"] - eta * (r1["h"] - h2s); s2a, (c, d), fr2 = a17.by("h", h2a); T2a = s2a["T"]
    V2s = math.sqrt(V1 ** 2 + 2000 * (r1["h"] - h2s)); V2a = math.sqrt(V1 ** 2 + 2000 * (r1["h"] - h2a))
    sgen = s2a["s"] - r1["s"] - RA * math.log(P2 / P1)
    stem = (f"Hot combustion gases, modeled as air, enter an adiabatic nozzle at {P1} kPa and {T1} K with a velocity of {V1} m/s and leave at {P2} kPa. "
            f"The nozzle's isentropic efficiency is {int(round(eta * 100))}%. Using variable specific heats, determine (a) the exit enthalpy for an isentropic nozzle, "
            "(b) the actual exit velocity, (c) the actual exit temperature, and (d) the entropy generated per kilogram of gas.")
    parts = [part("a", "Isentropic exit enthalpy, h<sub>2s</sub>", "kJ/kg", h2s, 0.005, 2, [(safe(lambda: a17.by("Pr", r1["Pr"] * P1 / P2)[0]["h"]), "Expansion: P<sub>r2</sub> = P<sub>r1</sub>(P<sub>2</sub>/P<sub>1</sub>), which is smaller than P<sub>r1</sub>.")]),
             part("b", "Exit velocity, V<sub>2</sub>", "m/s", V2a, 0.01, 3,
                  [(V2s, "That's the isentropic velocity. The real nozzle converts only η of the ideal enthalpy drop."), (math.sqrt(V1 ** 2 + 2 * (r1["h"] - h2a)), "Multiply kJ/kg by 1000 to get m²/s²."),
                   (math.sqrt(eta) * V2s, "η applies to the enthalpy drop (kinetic energy), not the velocity directly; with V<sub>1</sub> included, use h<sub>2</sub> = h<sub>1</sub> − η(h<sub>1</sub> − h<sub>2s</sub>).")]),
             part("c", "Exit temperature, T<sub>2</sub>", "K", T2a, 0.006, 2, [(s2s["T"], "That's T<sub>2s</sub>. The real nozzle leaves hotter.")]),
             part("d", "Entropy generated, s<sub>gen</sub>", "kJ/kg·K", sgen, 0.06, 2,
                  [(s2a["s"] - r1["s"], "Don't forget the pressure term: −R ln(P<sub>2</sub>/P<sub>1</sub>), which is positive for an expansion."),
                   (s2a["s"] - r1["s"] + RA * math.log(P2 / P1), "Sign: Δs = s°<sub>2</sub> − s°<sub>1</sub> − R ln(P<sub>2</sub>/P<sub>1</sub>).")])]
    steps = [self_step("Find the ideal exit enthalpy, the actual exit velocity and temperature, and the entropy generated in a real nozzle. Plan: P<sub>r</sub> for the ideal exit, η for the actual exit, then the energy balance for V<sub>2</sub>."),
             dia("Which T-s sketch shows the expansion?", ["ts_turb_gas", "ts_comp", "ts_comp_isoP", "ts_comp_left"], 0,
                 "The ideal nozzle drops straight down (s constant) from the high-pressure line to the low-pressure line. The real one ends on the same low-pressure line but a little to the right, and hotter."),
             assume([f"P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {T1} K, V<sub>1</sub> = {V1} m/s", f"P<sub>2</sub> = {P2} kPa", f"η<sub>N</sub> = {eta}"],
                    ["h<sub>2s</sub> (kJ/kg)", "V<sub>2</sub> (m/s)", "T<sub>2</sub> (K)", "s<sub>gen</sub> (kJ/kg·K)"],
                    [("open", True, "Gas flows through."), ("steady", True, "Steady operation."), ("adiabatic", True, "Given."), ("noshaft", True, "Nozzles have no work."),
                     ("nope", True, "Same height."), ("ideal", True, "Hot air at low pressure: Z ≈ 1 (rule 2)."), ("a17", True, f"Rule 4: the gas cools by roughly {int(round(T1 - T2a, -1))} K."),
                     ("isen", True, "For the comparison nozzle only: s<sub>2s</sub> = s<sub>1</sub>."),
                     ("lowke", False, "A nozzle exists to make kinetic energy."), ("rev", False, "η &lt; 1.")]),
             multi([("P<sub>r2s</sub> = P<sub>r1</sub>(P<sub>2</sub>/P<sub>1</sub>)", True, ""), ("η<sub>N</sub> = (h<sub>1</sub> − h<sub>2</sub>)/(h<sub>1</sub> − h<sub>2s</sub>)", True, ""),
                    (FIRST_SF, True, ""), ("s<sub>gen</sub> = s°<sub>2</sub> − s°<sub>1</sub> − R ln(P<sub>2</sub>/P<sub>1</sub>)", True, ""),
                    ("V<sub>2</sub> = ηV<sub>2s</sub>", False, "η is on kinetic energy, so on V², not V."), ("A<sub>1</sub>V<sub>1</sub> = A<sub>2</sub>V<sub>2</sub>", False, "Density changes; nothing asks for areas.")], FIRST_SF),
             sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Win": (["noshaft"], "No work."), "Wout": (["noshaft"], "No work."),
                        "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."), "dE": (["steady"], "Steady.")},
                       "h<sub>1</sub> + V<sub>1</sub>²/2 = h<sub>2</sub> + V<sub>2</sub>²/2"),
             props([("h<sub>1</sub>", r1["h"], "kJ/kg", "A-17", 0.003, f"{T1} K"), ("P<sub>r1</sub>", r1["Pr"], "", "A-17", 0.004, f"{T1} K"), ("s°<sub>1</sub>", r1["s"], "kJ/kg·K", "A-17", 0.003, f"{T1} K")]),
             calc([f"P<sub>r2s</sub> = {sg(r1['Pr'], 4)}({P2}/{P1}) = {sg(r1['Pr'] * P2 / P1, 4)}: {a17where(a, b, fr)}; h<sub>2s</sub> = <b>{sg(h2s, 5)} kJ/kg</b>",
                   f"h<sub>2</sub> = h<sub>1</sub> − η(h<sub>1</sub> − h<sub>2s</sub>) = {num(r1['h'], 2)} − {eta}({num(r1['h'], 2)} − {sg(h2s, 5)}) = {sg(h2a, 5)} kJ/kg",
                   f"V<sub>2</sub> = √[V<sub>1</sub>² + 2(h<sub>1</sub> − h<sub>2</sub>)(1000)] = √[{V1}² + 2000({num(r1['h'], 2)} − {sg(h2a, 5)})] = <b>{sg(V2a)} m/s</b> (ideal: {sg(V2s)} m/s)",
                   f"h<sub>2</sub> = {sg(h2a, 5)} kJ/kg: {a17where(c, d, fr2)}; T<sub>2</sub> = <b>{sg(T2a)} K</b>, s°<sub>2</sub> = {sg(s2a['s'], 5)}",
                   f"s<sub>gen</sub> = s°<sub>2</sub> − s°<sub>1</sub> − R ln(P<sub>2</sub>/P<sub>1</sub>) = {sg(s2a['s'], 5)} − {num(r1['s'], 5)} − 0.287 ln({P2}/{P1}) = <b>{sg(sgen, 3)} kJ/kg·K</b>"]),
             mc(8, "Check the sign and size of s<sub>gen</sub>. What should you see?",
                ["Small and positive: a good nozzle wastes only a few percent of the ideal kinetic energy", "Negative, because the gas cools", "Zero, because the nozzle is adiabatic", "Large, about R ln(P<sub>1</sub>/P<sub>2</sub>)"],
                0, "Cooling doesn't lower entropy here: the pressure drop raises it. An ideal nozzle would give exactly zero, so a small positive number is right. If you got something near R ln(P<sub>1</sub>/P<sub>2</sub>), you dropped s°.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C10: jet engine core (old exam's gas generator)
@template("C10", "Jet engine core: ram inlet to exhaust nozzle", 9, "F", 22, "hardest")
def C10(rng):
    Va = rng.choice([200, 220, 240, 260, 280]); P0 = rng.choice([30, 35, 40, 45, 50]); T0a = rng.choice([220, 230, 240, 250])
    rp = rng.choice([8, 10, 12, 14]); T3 = rng.choice([1200, 1300, 1400, 1500])
    T1 = T0a + Va ** 2 / 2000 / CPA; P1 = P0 * (T1 / T0a) ** (1 / E)
    T2 = T1 * rp ** E; P2 = rp * P1; T4 = T3 - (T2 - T1); P4 = P2 * (T4 / T3) ** (1 / E)
    T5 = T4 * (P0 / P4) ** E; V5 = math.sqrt(2000 * CPA * (T4 - T5)); assert P4 > P0 * 1.3
    stem = (f"An aircraft flies at {Va} m/s where the air is at {P0} kPa and {T0a} K. Its engine core works like this: a diffuser slows the incoming air to nearly zero velocity, "
            f"a compressor raises the pressure by a factor of {rp}, the combustor heats the air to {T3} K at constant pressure, the turbine makes just enough work to drive the compressor, "
            "and a nozzle expands the gas back to the outside pressure. Every device is ideal (isentropic where it can be). Using cold-air-standard assumptions, "
            "determine (a) the pressure at the diffuser exit, (b) the turbine exit temperature, (c) the turbine exit pressure, and (d) the jet velocity leaving the nozzle.")
    parts = [part("a", "Diffuser exit pressure, P<sub>1</sub>", "kPa", P1, 0.01, 4,
                  [(P0, "The diffuser raises the pressure: it turns the air's kinetic energy into enthalpy, isentropically."), (P0 * (T1 / T0a) ** E, "For pressure, the exponent is k/(k − 1) = 3.5.")]),
             part("b", "Turbine exit temperature, T<sub>4</sub>", "K", T4, 0.006, 6,
                  [(T3 / rp ** E, "The turbine doesn't expand all the way down. It only makes the compressor's work: c<sub>p</sub>(T<sub>3</sub> − T<sub>4</sub>) = c<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>)."),
                   (T3 - (T0a * rp ** E - T0a), "Start the compressor at T<sub>1</sub> after the diffuser's ram heating, not at the outside air temperature.")]),
             part("c", "Turbine exit pressure, P<sub>4</sub>", "kPa", P4, 0.015, 6,
                  [(P2 * (T4 / T3) ** E, "For pressure, use the exponent k/(k − 1): P<sub>4</sub> = P<sub>3</sub>(T<sub>4</sub>/T<sub>3</sub>)<sup>3.5</sup>."), (P0, "The turbine stops above outside pressure; the nozzle does the rest.")]),
             part("d", "Jet velocity, V<sub>5</sub>", "m/s", V5, 0.01, 6,
                  [(math.sqrt(2 * CPA * (T4 - T5)), "Multiply by 1000 to turn kJ/kg into m²/s²."),
                   (math.sqrt(2000 * CPA * (T4 - T5)) - Va, "That's the velocity gain (V<sub>5</sub> − V<sub>a</sub>). The question asks for V<sub>5</sub>.")])]
    ctx = {"t": "Who lives under the flight path?",
           "b": "A University of Washington study for the state legislature found that communities under and downwind of Sea-Tac's landing paths breathe a kind of ultrafine particle that comes from aircraft, smaller than the particles from freeway traffic. Smaller particles reach deeper into the body. Paine Field in Everett added commercial passenger service in 2019.",
           "q": "Your jet velocity sets the engine's thrust. What tradeoffs between thrust, fuel, noise and exhaust land on people who live near an airport but may never fly from it? Who gets a say?",
           "src": ["UW News: Communities around Sea-Tac exposed to a unique mix of air pollution (2019)", "https://www.washington.edu/news/2019/12/03/communities-around-sea-tac-airport-exposed-to-a-unique-mix-of-air-pollution-associated-with-aircraft/"]}
    steps = [self_step("Follow the air through a jet engine core, device by device: diffuser, compressor, combustor, turbine, nozzle. Plan: each device is a steady-flow control volume; the turbine's job is fixed by the compressor's work."),
             mc(2, "Sketch the T-s path. Which description is right?",
                ["0→1 up (ram heating, s constant), 1→2 up (compressor), 2→3 right along high P (combustor), 3→4 down partway (turbine), 4→5 down to the outside pressure line (nozzle)",
                 "Like a power-plant Brayton cycle: the turbine expands all the way to outside pressure", "The diffuser cools the air", "The nozzle raises the pressure"],
                0, "In a jet engine, the turbine expands only far enough to run the compressor. The leftover pressure drop happens in the nozzle, and that's what makes the jet."),
             assume([f"Flight: V<sub>a</sub> = {Va} m/s, P<sub>0</sub> = {P0} kPa, T<sub>0</sub> = {T0a} K", f"r<sub>p</sub> = {rp}, T<sub>3</sub> = {T3} K"],
                    ["P<sub>1</sub> (kPa)", "T<sub>4</sub> (K)", "P<sub>4</sub> (kPa)", "V<sub>5</sub> (m/s)"],
                    [("open", True, "Every device is a control volume."), ("steady", True, "Steady flight."), ("coldair", True, "The problem says so (rule 4)."),
                     ("isen", True, "Ideal devices.", "The diffuser, compressor, turbine and nozzle are isentropic (reversible and adiabatic)."), ("drive", True, "Given."), ("noshaft", True, "The diffuser and nozzle have no shaft.", "The diffuser and nozzle have no shaft or wires."),
                     ("nope", True, "Height changes are small."), ("lowv1", True, "Slowed to nearly zero in the diffuser, and nearly zero at the nozzle inlet.", "The velocity leaving the diffuser, and entering the nozzle, is negligible."),
                     ("lowke", False, "The diffuser and nozzle exist to trade kinetic energy and enthalpy."), ("closed", False, "Air flows through.")]),
             multi([("Diffuser: h<sub>0</sub> + V<sub>a</sub>²/2 = h<sub>1</sub>", True, ""), ("P<sub>1</sub>/P<sub>0</sub> = (T<sub>1</sub>/T<sub>0</sub>)<sup>k/(k−1)</sup>", True, ""),
                    ("w<sub>T</sub> = w<sub>C</sub>: T<sub>3</sub> − T<sub>4</sub> = T<sub>2</sub> − T<sub>1</sub>", True, ""), ("Nozzle: h<sub>4</sub> = h<sub>5</sub> + V<sub>5</sub>²/2", True, ""),
                    ("T<sub>4</sub>/T<sub>3</sub> = (1/r<sub>p</sub>)<sup>(k−1)/k</sup>", False, "That expands all the way to the compressor inlet pressure, which is a power plant, not a jet."),
                    ("P<sub>1</sub> = P<sub>0</sub>", False, "The diffuser's job is ram compression.")], FIRST_SF),
             sf_single({"Qin": (["isen"], "Isentropic, so adiabatic."), "Qout": (["isen"], "Isentropic, so adiabatic."), "Win": (["noshaft"], "No work in a diffuser."), "Wout": (["noshaft"], "No work in a diffuser."),
                        "mke2": (["lowv1"], "Slowed to nearly zero."), "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."), "dE": (["steady"], "Steady.")},
                       "Diffuser: h<sub>0</sub> + V<sub>a</sub>²/2 = h<sub>1</sub>, so T<sub>1</sub> = T<sub>0</sub> + V<sub>a</sub>²/(2c<sub>p</sub>)",
                       p="Apply the steady-flow first law to the diffuser (0→1). Cross out every term that drops."),
             props([("c<sub>p</sub> for air", CPA, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("k for air", 1.4, "", "A-2a", 0.003, "300 K")]),
             calc([f"T<sub>1</sub> = {T0a} + {Va}²/(2·1.005·1000) = {sg(T1)} K; P<sub>1</sub> = {P0}({sg(T1)}/{T0a})<sup>3.5</sup> = <b>{sg(P1)} kPa</b>",
                   f"T<sub>2</sub> = T<sub>1</sub>r<sub>p</sub><sup>0.2857</sup> = ({sg(T1)})({rp})<sup>0.2857</sup> = {sg(T2)} K; P<sub>2</sub> = P<sub>3</sub> = {sg(P2)} kPa",
                   f"Turbine drives compressor: T<sub>4</sub> = T<sub>3</sub> − (T<sub>2</sub> − T<sub>1</sub>) = {T3} − ({sg(T2)} − {sg(T1)}) = <b>{sg(T4)} K</b>",
                   f"P<sub>4</sub> = P<sub>3</sub>(T<sub>4</sub>/T<sub>3</sub>)<sup>3.5</sup> = ({sg(P2)})({sg(T4)}/{T3})<sup>3.5</sup> = <b>{sg(P4)} kPa</b>",
                   f"Nozzle: T<sub>5</sub> = T<sub>4</sub>(P<sub>0</sub>/P<sub>4</sub>)<sup>0.2857</sup> = {sg(T5)} K; V<sub>5</sub> = √[2c<sub>p</sub>(T<sub>4</sub> − T<sub>5</sub>)(1000)] = <b>{sg(V5)} m/s</b>"]),
             mc(8, f"The jet leaves at {sg(V5)} m/s and the plane flies at {Va} m/s. What does that tell you?",
                [f"The engine speeds each kilogram of air up by about {sg(V5 - Va)} m/s; thrust per kg/s of air is roughly that difference",
                 "The engine is broken if V<sub>5</sub> &gt; V<sub>a</sub>", "Thrust is zero because the turbine work equals the compressor work",
                 "V<sub>5</sub> should equal V<sub>a</sub> for steady flight"],
                0, "Net work out of the shaft is zero here, but the engine still produces a useful output: kinetic energy in the jet. Thrust per unit mass flow is about V<sub>5</sub> − V<sub>a</sub>.")]
    return stem, parts, steps, ctx, prm(locals())

# =================================================================== C11: Brayton, real devices, A-17, mass flow
@template("C11", "Gas turbine with real devices and variable specific heats", 9, "F", 22, "hardest")
def C11(rng):
    T1 = rng.choice([290, 300]); rp = rng.choice([8, 10, 12, 14]); T3 = rng.choice([1200, 1300, 1400, 1500])
    eC = rng.choice([0.80, 0.82, 0.84, 0.86, 0.88]); eT = rng.choice([0.85, 0.87, 0.88, 0.90, 0.92]); Wmw = rng.choice([20, 40, 60, 80, 100, 150])
    r1, r3 = a17.row(T1), a17.row(T3)
    s2s, (a, b), f2 = a17.by("Pr", r1["Pr"] * rp); s4s, (c, d), f4 = a17.by("Pr", r3["Pr"] / rp)
    h2 = r1["h"] + (s2s["h"] - r1["h"]) / eC; h4 = r3["h"] - eT * (r3["h"] - s4s["h"])
    wc, wt = h2 - r1["h"], r3["h"] - h4; wn = wt - wc; qin = r3["h"] - h2; eta = wn / qin; m = Wmw * 1000 / wn; assert wn > 50
    wn_ideal = (r3["h"] - s4s["h"]) - (s2s["h"] - r1["h"])
    stem = (f"A gas-turbine power plant has a pressure ratio of {rp}. Air enters the compressor at 100 kPa and {T1} K and enters the turbine at {T3} K. "
            f"The compressor's isentropic efficiency is {int(round(eC * 100))}% and the turbine's is {int(round(eT * 100))}%. The plant makes {Wmw} MW of net power. "
            "Using variable specific heats, determine (a) the enthalpy at the compressor exit, (b) the enthalpy at the turbine exit, (c) the thermal efficiency, and (d) the air mass flow rate.")
    parts = [part("a", "h<sub>2</sub>, compressor exit", "kJ/kg", h2, 0.005, 5,
                  [(s2s["h"], "That's h<sub>2s</sub>. Real compressors need more work: divide the ideal rise by η<sub>C</sub>."), (r1["h"] + (s2s["h"] - r1["h"]) * eC, "For a compressor, divide by η; multiplying gives less than ideal.")]),
             part("b", "h<sub>4</sub>, turbine exit", "kJ/kg", h4, 0.005, 5,
                  [(s4s["h"], "That's h<sub>4s</sub>. A real turbine extracts less, so it leaves hotter."), (r3["h"] - (r3["h"] - s4s["h"]) / eT, "For a turbine, multiply the ideal drop by η.")]),
             part("c", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 6,
                  [(pct(1 - rp ** -E), "That's the ideal cold-air efficiency. Real devices cut it a lot."), (pct(wn / (r3["h"] - s2s["h"])), "q<sub>in</sub> starts from the actual h<sub>2</sub>, not h<sub>2s</sub>."),
                   (pct(wn_ideal / (r3["h"] - s2s["h"])), "That's the ideal cycle with A-17. Use the real h<sub>2</sub> and h<sub>4</sub>.")]),
             part("d", "Air mass flow, ṁ", "kg/s", m, 0.01, 6, [(Wmw * 1000 / wn_ideal, "Use the actual net work, which is smaller, so more air is needed."), (Wmw / wn, "MW to kW: multiply by 1000.")])]
    steps = [self_step("Find the real compressor and turbine exit enthalpies, the efficiency and the air flow for a gas turbine with real devices. Plan: P<sub>r</sub> for the ideal exits, efficiencies for the real ones, then w<sub>net</sub> and ṁ = Ẇ<sub>net</sub>/w<sub>net</sub>."),
             dia("Which P-v diagram is the (ideal version of the) cycle?", CYC_PV, 3, "Brayton: two isentropes joined by two constant-pressure lines. On T-s, the real compressor and turbine both lean to the right of the ideal vertical lines."),
             assume([f"r<sub>p</sub> = {rp}, T<sub>1</sub> = {T1} K, T<sub>3</sub> = {T3} K", f"η<sub>C</sub> = {eC}, η<sub>T</sub> = {eT}", f"Ẇ<sub>net</sub> = {Wmw} MW"],
                    ["h<sub>2</sub> (kJ/kg)", "h<sub>4</sub> (kJ/kg)", "η<sub>th</sub> (%)", "ṁ (kg/s)"],
                    [("open", True, "Each device is a control volume."), ("steady", True, "Steady operation."),
                     ("airstd", True, f"Rule 4: air spans about {T3 - T1} K and the problem asks for variable specific heats."),
                     ("isen", True, "For the comparison devices only.", "The comparison compressor and turbine are isentropic: P<sub>r</sub> ratios apply to 2s and 4s."),
                     ("lowke", True, "Small KE changes."), ("nope", True, "Same height."), ("adiabatic", True, "Compressor and turbine are adiabatic."),
                     ("coldair", False, "The problem asks for variable specific heats."), ("rev", False, "η &lt; 1 for both devices.")]),
             multi([("P<sub>r2s</sub> = P<sub>r1</sub>r<sub>p</sub>; P<sub>r4s</sub> = P<sub>r3</sub>/r<sub>p</sub>", True, ""), ("h<sub>2</sub> = h<sub>1</sub> + (h<sub>2s</sub> − h<sub>1</sub>)/η<sub>C</sub>", True, ""),
                    ("h<sub>4</sub> = h<sub>3</sub> − η<sub>T</sub>(h<sub>3</sub> − h<sub>4s</sub>)", True, ""), ("η<sub>th</sub> = w<sub>net</sub>/q<sub>in</sub>; ṁ = Ẇ<sub>net</sub>/w<sub>net</sub>", True, ""), (FIRST_SF, True, ""),
                    ("η = 1 − 1/r<sub>p</sub><sup>(k−1)/k</sup>", False, "Only for the ideal cold-air cycle.")], FIRST_SF),
             sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Win": (["dir"], "Work comes out of a turbine."),
                        "mke1": (["lowke"], "Small KE changes."), "mke2": (["lowke"], "Small KE changes."), "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."), "dE": (["steady"], "Steady.")},
                       "Turbine: w<sub>T,out</sub> = h<sub>3</sub> − h<sub>4</sub>", p="Apply the steady-flow first law to the turbine (3→4). Cross out every term that drops."),
             props([("h<sub>1</sub>", r1["h"], "kJ/kg", "A-17", 0.003, f"{T1} K"), ("P<sub>r1</sub>", r1["Pr"], "", "A-17", 0.004, f"{T1} K"),
                    ("h<sub>3</sub>", r3["h"], "kJ/kg", "A-17", 0.003, f"{T3} K"), ("P<sub>r3</sub>", r3["Pr"], "", "A-17", 0.004, f"{T3} K")]),
             calc([f"P<sub>r2s</sub> = {sg(r1['Pr'], 4)}({rp}) = {sg(r1['Pr'] * rp, 4)}: {a17where(a, b, f2)}; h<sub>2s</sub> = {sg(s2s['h'], 5)} kJ/kg",
                   f"h<sub>2</sub> = {num(r1['h'], 2)} + ({sg(s2s['h'], 5)} − {num(r1['h'], 2)})/{eC} = <b>{sg(h2, 5)} kJ/kg</b>",
                   f"P<sub>r4s</sub> = {sg(r3['Pr'], 4)}/{rp} = {sg(r3['Pr'] / rp, 4)}: {a17where(c, d, f4)}; h<sub>4s</sub> = {sg(s4s['h'], 5)} kJ/kg",
                   f"h<sub>4</sub> = {num(r3['h'], 2)} − {eT}({num(r3['h'], 2)} − {sg(s4s['h'], 5)}) = <b>{sg(h4, 5)} kJ/kg</b>",
                   f"w<sub>C</sub> = {sg(wc)}, w<sub>T</sub> = {sg(wt)}, w<sub>net</sub> = {sg(wn)} kJ/kg (back work ratio {pct(wc / wt):.0f}%); q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub> = {sg(qin)} kJ/kg",
                   f"η<sub>th</sub> = {sg(wn)}/{sg(qin)} = <b>{pct(eta):.1f}%</b>",
                   f"ṁ = Ẇ<sub>net</sub>/w<sub>net</sub> = {Wmw * 1000}/{sg(wn)} = <b>{sg(m)} kg/s</b>"]),
             mc(8, f"The ideal version of this cycle would have w<sub>net</sub> ≈ {sg(wn_ideal)} kJ/kg. Why does the real one lose so much more than the device efficiencies suggest?",
                ["The back work ratio is large, so small losses in the compressor and turbine eat a big share of the small difference between them",
                 "Because A-17 is less accurate than constant c<sub>p</sub>", "Because q<sub>in</sub> goes up", "It doesn't; the losses are about the same percentage"],
                0, f"Net work is the difference of two big numbers. With a back work ratio near {pct(wc / wt):.0f}%, a few percent off each device can cut w<sub>net</sub> by a quarter or more. That is why early gas turbines barely ran.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C12: regenerative gas turbine on two fuels (old Final, two-fuel Brayton)
@template("C12", "Regenerative peaker plant on two fuels", 9, "F", 22, "hardest")
def C12(rng):
    T1 = rng.choice([290, 300]); rp = rng.choice([6, 7, 8, 9, 10]); T3 = rng.choice([1100, 1200, 1300, 1400])
    eC = rng.choice([0.82, 0.84, 0.86, 0.88]); eT = rng.choice([0.86, 0.88, 0.90, 0.92]); eps = rng.choice([0.65, 0.70, 0.75, 0.80, 0.85]); Wmw = rng.choice([25, 40, 50, 60, 80])
    HVg, HVh = 50000, 120000
    T2s = T1 * rp ** E; T2 = T1 + (T2s - T1) / eC; T4s = T3 / rp ** E; T4 = T3 - eT * (T3 - T4s); assert T4 - T2 > 60
    T5 = T2 + eps * (T4 - T2); qin = CPA * (T3 - T5); wn = CPA * ((T3 - T4) - (T2 - T1)); eta = wn / qin
    m = Wmw * 1000 / wn; mg = m * qin / HVg; mh = m * qin / HVh
    eta_noreg = wn / (CPA * (T3 - T2))
    stem = (f"A city's peaker plant runs a regenerative gas turbine with a pressure ratio of {rp}. Air enters the compressor at {T1} K and the turbine at {T3} K. "
            f"The compressor's isentropic efficiency is {int(round(eC * 100))}%, the turbine's is {int(round(eT * 100))}%, and the regenerator's effectiveness is {int(round(eps * 100))}%. "
            f"The plant makes {Wmw} MW of net power. Using cold-air-standard assumptions, determine (a) the air temperature entering the combustor, (b) the thermal efficiency, "
            f"(c) the air mass flow rate, (d) the fuel flow if it burns natural gas (heating value {HVg:,} kJ/kg), and (e) the fuel flow if it burns hydrogen ({HVh:,} kJ/kg).")
    parts = [part("a", "Combustor inlet temperature, T<sub>5</sub>", "K", T5, 0.005, 4,
                  [(T2s + eps * (T4s - T2s), "Use the actual T<sub>2</sub> and T<sub>4</sub>, not the isentropic ones."), (T4 - eps * (T4 - T2), "Effectiveness is measured from the cold side: T<sub>5</sub> = T<sub>2</sub> + ε(T<sub>4</sub> − T<sub>2</sub>)."),
                   (eps * T4, "ε multiplies the temperature difference, T<sub>4</sub> − T<sub>2</sub>.")]),
             part("b", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 5,
                  [(pct(eta_noreg), "That's without the regenerator: q<sub>in</sub> now starts from T<sub>5</sub>, not T<sub>2</sub>."), (pct(1 - rp ** -E), "That's the ideal simple Brayton efficiency.")]),
             part("c", "Air mass flow, ṁ", "kg/s", m, 0.01, 4, [(Wmw / wn, "MW to kW: multiply by 1000.")]),
             part("d", "Natural gas flow, ṁ<sub>gas</sub>", "kg/s", mg, 0.015, 5, [(m * CPA * (T3 - T2) / HVg, "With the regenerator, the combustor only heats from T<sub>5</sub> to T<sub>3</sub>.")]),
             part("e", "Hydrogen flow, ṁ<sub>H₂</sub>", "kg/s", mh, 0.015, 4, [(mg, "Use hydrogen's heating value.")])]
    ctx = {"t": "Who lives next to the peaker?",
           "b": "Peaker plants run only a few hundred hours a year, on the hottest and coldest days, but that is when they emit the most NOx and particulates. In New York City, a coalition of environmental justice groups found that many of the city's oldest peakers sit in the South Bronx, Sunset Park and other low-income communities and communities of color already overburdened by pollution. Burning hydrogen removes carbon dioxide, but a hotter flame can make more NOx unless the combustor is redesigned.",
           "q": "Your answer to (e) shows hydrogen needs far less fuel by mass. Does switching fuels fix the problem for the people who live next to the plant? What other options (batteries, demand response) would you want on the table, and who should choose?",
           "src": ["PEAK Coalition fact sheet (Clean Energy Group)", "https://www.cleanegroup.org/wp-content/uploads/Peak-Coalition-Fact-Sheet.pdf"]}
    steps = [self_step("Find the combustor inlet temperature, the efficiency, the air flow and the fuel flows for a regenerative gas turbine with real devices. Plan: actual T<sub>2</sub> and T<sub>4</sub> first, then the regenerator, then q<sub>in</sub> from the combustor alone."),
             mc(2, "Where does the regenerator sit on the T-s diagram?",
                ["It heats the compressed air from T<sub>2</sub> to T<sub>5</sub> using the turbine exhaust, which cools from T<sub>4</sub>; the combustor only adds heat from T<sub>5</sub> to T<sub>3</sub>",
                 "It cools the air before the compressor", "It reheats the gas between two turbine stages", "It adds heat at constant volume"],
                0, "Regeneration only helps when the turbine exhaust is hotter than the compressor exit (T<sub>4</sub> &gt; T<sub>2</sub>), which is why it suits low pressure ratios."),
             assume([f"r<sub>p</sub> = {rp}, T<sub>1</sub> = {T1} K, T<sub>3</sub> = {T3} K", f"η<sub>C</sub> = {eC}, η<sub>T</sub> = {eT}, ε = {eps}", f"Ẇ<sub>net</sub> = {Wmw} MW", f"HV: gas {HVg:,}, H₂ {HVh:,} kJ/kg"],
                    ["T<sub>5</sub> (K)", "η<sub>th</sub> (%)", "ṁ (kg/s)", "ṁ<sub>gas</sub> (kg/s)", "ṁ<sub>H₂</sub> (kg/s)"],
                    [("open", True, "Each device is a control volume."), ("steady", True, "Steady operation."), ("coldair", True, "The problem says so (rule 4)."),
                     ("regen", True, "Given an effectiveness."), ("noshaft", True, "The regenerator has no shaft or wires.", "The regenerator has no shaft, wires or moving boundary."), ("fuel", True, "Needed to turn q<sub>in</sub> into a fuel flow."), ("lowke", True, "Small KE changes."), ("nope", True, "Same height."),
                     ("airstd", False, "The problem asks for cold-air-standard."), ("rev", False, "η &lt; 1 for both devices.")]),
             multi([("T<sub>2</sub> = T<sub>1</sub> + (T<sub>2s</sub> − T<sub>1</sub>)/η<sub>C</sub>; T<sub>4</sub> = T<sub>3</sub> − η<sub>T</sub>(T<sub>3</sub> − T<sub>4s</sub>)", True, ""),
                    ("T<sub>5</sub> = T<sub>2</sub> + ε(T<sub>4</sub> − T<sub>2</sub>)", True, ""), ("q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>5</sub>)", True, ""),
                    ("ṁ<sub>fuel</sub> = ṁq<sub>in</sub>/HV", True, ""), (FIRST_SF, True, ""), ("q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)", False, "That ignores the regenerator.")], FIRST_SF),
             multi_terms(["ṁh<sub>2</sub>", "ṁh<sub>4</sub>"], ["ṁh<sub>5</sub>", "ṁh<sub>6</sub>"], "Regenerator: h<sub>5</sub> − h<sub>2</sub> = h<sub>4</sub> − h<sub>6</sub>",
                         qr="regen", p="Apply the steady-flow first law to the whole regenerator (both streams inside). Cross out every term that drops."),
             props([("c<sub>p</sub> for air", CPA, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("k for air", 1.4, "", "A-2a", 0.003, "300 K")]),
             calc([f"T<sub>2s</sub> = {T1}({rp})<sup>0.2857</sup> = {sg(T2s)} K; T<sub>2</sub> = {T1} + ({sg(T2s)} − {T1})/{eC} = {sg(T2)} K",
                   f"T<sub>4s</sub> = {T3}/{rp}<sup>0.2857</sup> = {sg(T4s)} K; T<sub>4</sub> = {T3} − {eT}({T3} − {sg(T4s)}) = {sg(T4)} K (hotter than T<sub>2</sub>, so regeneration helps)",
                   f"T<sub>5</sub> = T<sub>2</sub> + ε(T<sub>4</sub> − T<sub>2</sub>) = {sg(T2)} + {eps}({sg(T4)} − {sg(T2)}) = <b>{sg(T5)} K</b>",
                   f"w<sub>net</sub> = c<sub>p</sub>[(T<sub>3</sub> − T<sub>4</sub>) − (T<sub>2</sub> − T<sub>1</sub>)] = {sg(wn)} kJ/kg; q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>5</sub>) = {sg(qin)} kJ/kg",
                   f"η<sub>th</sub> = {sg(wn)}/{sg(qin)} = <b>{pct(eta):.1f}%</b> (without the regenerator: {pct(eta_noreg):.1f}%)",
                   f"ṁ = {Wmw * 1000}/{sg(wn)} = <b>{sg(m)} kg/s</b>",
                   f"ṁ<sub>gas</sub> = ṁq<sub>in</sub>/HV = ({sg(m)})({sg(qin)})/{HVg} = <b>{sg(mg, 3)} kg/s</b>; ṁ<sub>H₂</sub> = ({sg(m)})({sg(qin)})/{HVh} = <b>{sg(mh, 3)} kg/s</b>"]),
             mc(8, "Compare the two fuel flows. What's right?",
                [f"Hydrogen needs {HVg / HVh:.2f} times the mass of natural gas, because the cycle needs the same heat and hydrogen carries more energy per kilogram",
                 "Hydrogen raises the efficiency", "The air flow changes with the fuel", "The fuel flow is the same for both"],
                0, "The cycle's efficiency and air flow don't depend on the fuel in this model. Only the fuel flow does. Mass isn't the whole story: hydrogen is so light that it takes far more volume, and it brings its own NOx and supply questions.")]
    return stem, parts, steps, ctx, prm(locals())

# =================================================================== C13: Otto with variable specific heats
@template("C13", "Otto cycle with variable specific heats", 9, "F", 22, "hardest")
def C13(rng):
    r = rng.choice([8, 9, 10]); T1 = rng.choice([290, 300, 310]); P1 = rng.choice([95, 100]); qin = rng.choice([700, 800, 900, 1000, 1100, 1200])
    r1 = a17.row(T1); s2, (a, b), f2 = a17.by("vr", r1["vr"] / r); u3 = s2["u"] + qin
    assert u3 < a17.row(2150)["u"]
    s3, (c, d), f3 = a17.by("u", u3); s4, (e, g), f4 = a17.by("vr", s3["vr"] * r)
    qout = s4["u"] - r1["u"]; wn = qin - qout; eta = wn / qin
    v1 = RA * T1 / P1; mep = wn / (v1 * (1 - 1 / r))
    T2c = T1 * r ** 0.4
    stem = (f"An ideal Otto cycle has a compression ratio of {r}. At the start of compression the air is at {P1} kPa and {T1} K, and {qin} kJ/kg of heat is added. "
            "Accounting for the variation of specific heats with temperature, determine (a) the temperature after compression, (b) the maximum temperature, (c) the thermal efficiency, and (d) the mean effective pressure.")
    parts = [part("a", "T<sub>2</sub>", "K", s2["T"], 0.006, 5, [(T2c, "That's the cold-air result. With A-17, use v<sub>r2</sub> = v<sub>r1</sub>/r."), (safe(lambda: a17.by("vr", r1["vr"] * r)[0]["T"]), "Compression makes v smaller: v<sub>r2</sub> = v<sub>r1</sub>/r.")]),
             part("b", "T<sub>3</sub>", "K", s3["T"], 0.006, 5, [(safe(lambda: a17.by("h", s2["h"] + qin)[0]["T"]), "Heat goes in at constant volume: u<sub>3</sub> = u<sub>2</sub> + q<sub>in</sub>, not h.")]),
             part("c", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 6, [(pct(1 - r ** -0.4), "That's the cold-air value. Use q<sub>out</sub> = u<sub>4</sub> − u<sub>1</sub> from A-17.")]),
             part("d", "Mean effective pressure, MEP", "kPa", mep, 0.015, 6, [(wn / v1, "MEP divides by the displacement, v<sub>1</sub> − v<sub>2</sub> = v<sub>1</sub>(1 − 1/r), not v<sub>1</sub>.")])]
    steps = [self_step("Find the compression and peak temperatures, the efficiency and the MEP of an ideal Otto cycle with variable specific heats. Plan: v<sub>r</sub> for each isentrope, u for each constant-volume heat transfer."),
             dia("Which P-v diagram is the Otto cycle?", CYC_PV, 0, "Otto: two isentropes joined by two constant-volume lines."),
             cyc_assume([f"r = {r}", f"P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {T1} K", f"q<sub>in</sub> = {qin} kJ/kg"], ["T<sub>2</sub> (K)", "T<sub>3</sub> (K)", "η<sub>th</sub> (%)", "MEP (kPa)"],
                        [("airstd", True, "Rule 4: the problem asks for variable specific heats, and T spans more than 1000 K."), ("intrev", True, "Ideal cycle: compression and expansion are isentropic."),
                         ("constv", True, "Otto adds and rejects heat at constant volume."), ("stationary", True, "Standard for cycles."),
                         ("coldair", False, "The problem asks for variable specific heats."), ("constP", False, "That's Diesel's heat addition.")]),
             multi([("v<sub>r2</sub> = v<sub>r1</sub>/r; v<sub>r4</sub> = r·v<sub>r3</sub>", True, ""), ("q<sub>in</sub> = u<sub>3</sub> − u<sub>2</sub>; q<sub>out</sub> = u<sub>4</sub> − u<sub>1</sub>", True, ""),
                    ("MEP = w<sub>net</sub>/(v<sub>1</sub> − v<sub>2</sub>), v<sub>1</sub> = RT<sub>1</sub>/P<sub>1</sub>", True, ""), (FIRST_CL + " (per kg, for each process)", True, ""),
                    ("P<sub>r2</sub> = P<sub>r1</sub>r", False, "P<sub>r</sub> is for pressure ratios; Otto gives a volume ratio, so use v<sub>r</sub>."),
                    ("η = 1 − 1/r<sup>k−1</sup>", False, "Only for constant specific heats.")], FIRST_CL),
             strike_custom([term("qin", "q<sub>in</sub>", "L", "+"), term("win", "w<sub>b,in</sub>", "L", "+", True, ["constv"], "Constant volume: no boundary work."),
                            term("qout", "q<sub>out</sub>", "L", "−", True, ["dir"], "Heat comes in during 2→3."), term("wout", "w<sub>b,out</sub>", "L", "−", True, ["constv"], "Constant volume: no boundary work."),
                            term("du", "Δu", "R", ""), term("dke", "Δke", "R", "+", True, ["stationary"], ""), term("dpe", "Δpe", "R", "+", True, ["stationary"], "")],
                           "Process 2→3: q<sub>in</sub> = u<sub>3</sub> − u<sub>2</sub>", p="Apply the first law to the heat-addition process, 2→3. Cross out every term that drops."),
             props([("u<sub>1</sub>", r1["u"], "kJ/kg", "A-17", 0.003, f"{T1} K"), ("v<sub>r1</sub>", r1["vr"], "", "A-17", 0.004, f"{T1} K"), ("R for air", RA, "kJ/kg·K", "A-1", 0.003, "air")]),
             calc([f"v<sub>r2</sub> = {sg(r1['vr'], 4)}/{r} = {sg(r1['vr'] / r, 4)}: {a17where(a, b, f2)}; T<sub>2</sub> = <b>{sg(s2['T'])} K</b>, u<sub>2</sub> = {sg(s2['u'], 5)} kJ/kg",
                   f"u<sub>3</sub> = u<sub>2</sub> + q<sub>in</sub> = {sg(s2['u'], 5)} + {qin} = {sg(u3, 5)} kJ/kg: {a17where(c, d, f3)}; T<sub>3</sub> = <b>{sg(s3['T'])} K</b>, v<sub>r3</sub> = {sg(s3['vr'], 4)}",
                   f"v<sub>r4</sub> = r·v<sub>r3</sub> = {sg(s3['vr'] * r, 4)}: {a17where(e, g, f4)}; u<sub>4</sub> = {sg(s4['u'], 5)} kJ/kg",
                   f"q<sub>out</sub> = u<sub>4</sub> − u<sub>1</sub> = {sg(qout)} kJ/kg; w<sub>net</sub> = {qin} − {sg(qout)} = {sg(wn)} kJ/kg; η<sub>th</sub> = <b>{pct(eta):.1f}%</b>",
                   f"v<sub>1</sub> = RT<sub>1</sub>/P<sub>1</sub> = (0.287)({T1})/{P1} = {sg(v1)} m³/kg; MEP = w<sub>net</sub>/[v<sub>1</sub>(1 − 1/r)] = <b>{sg(mep)} kPa</b>"]),
             mc(8, f"The cold-air answer would be η = {pct(1 - r ** -0.4):.1f}%. Why is yours lower?",
                ["Air's specific heats rise with temperature, so the same heat raises T less, and the cycle runs at a lower average temperature than the cold-air model assumes",
                 "A-17 has rounding errors", "Because MEP is high", "It shouldn't be; something is wrong"],
                0, "The cold-air model overpredicts. Real spark-ignition engines do worse still: friction, heat loss and incomplete combustion.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C14: Diesel generator power
@template("C14", "Diesel generator: power from displacement and speed", 9, "F", 22, "challenge")
def C14(rng):
    r = rng.choice([16, 17, 18, 19, 20]); T1 = rng.choice([300, 310, 320]); P1 = rng.choice([95, 100]); qin = rng.choice([800, 900, 1000, 1100, 1200, 1300])
    Vd = rng.choice([4, 6, 8, 10, 12, 15]); rpm = rng.choice([1200, 1500, 1800])
    T2 = T1 * r ** 0.4; T3 = T2 + qin / CPA; rc = T3 / T2; assert rc < r / 3
    T4 = T3 * (rc / r) ** 0.4; qout = CVA * (T4 - T1); wn = qin - qout; eta = wn / qin
    v1 = RA * T1 / P1; mep = wn / (v1 * (1 - 1 / r)); Wd = mep * Vd / 1000 * rpm / 60 / 2
    stem = (f"A four-stroke diesel generator has a total displacement of {Vd} L and runs at {rpm} rpm with a compression ratio of {r}. "
            f"At the start of compression the air is at {P1} kPa and {T1} K, and the fuel adds {qin} kJ of heat per kilogram of air at constant pressure. "
            "Using an ideal Diesel cycle and cold-air-standard assumptions, determine (a) the cutoff ratio, (b) the thermal efficiency, (c) the mean effective pressure, and (d) the power output.")
    parts = [part("a", "Cutoff ratio, r<sub>c</sub>", "", rc, 0.01, 5, [((T2 + qin / CVA) / T2, "Diesel adds heat at constant pressure: use c<sub>p</sub>.")]),
             part("b", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 5, [(pct(1 - r ** -0.4), "That's the Otto efficiency. Diesel's has the cutoff-ratio term."),
                                                                                   (pct(1 - CPA * (T4 - T1) / qin), "Heat is rejected at constant volume: q<sub>out</sub> = c<sub>v</sub>(T<sub>4</sub> − T<sub>1</sub>).")]),
             part("c", "Mean effective pressure, MEP", "kPa", mep, 0.015, 5, [(wn / v1, "Divide by the displacement per kg, v<sub>1</sub> − v<sub>2</sub>, not v<sub>1</sub>.")]),
             part("d", "Power output, Ẇ", "kW", Wd, 0.015, 7, [(Wd * 2, "Four-stroke: one power stroke every two revolutions. Divide by 2."),
                                                               (mep * Vd / 1000 * rpm / 2, "Revolutions per minute: divide by 60 for per second."), (Wd * 1000, "Liters to m³: divide by 1000.")])]
    ctx = {"t": "Power that arrives by barge",
           "b": "About 190 rural Alaska communities, many of them Alaska Native villages off the road system, get their electricity mostly from diesel generators. Fuel arrives by barge or plane, and electricity there can cost three to five times what it does in Anchorage. The state's Power Cost Equalization program pays part of residential bills to bring rates closer to urban levels.",
           "q": "Your efficiency answer is an ideal limit; real gensets do worse. If a village could raise its generator efficiency, add wind or solar, or recover the engine's waste heat for the school, how should it decide, and who pays for the change?",
           "src": ["Alaska Energy Authority, Power Cost Equalization", "https://www.akenergyauthority.org/PCE"]}
    steps = [self_step("Find the cutoff ratio, efficiency, MEP and power of a four-stroke diesel engine. Plan: state temperatures from the cold-air relations, then MEP from w<sub>net</sub>, then power from MEP × displacement × power strokes per second."),
             dia("Which P-v diagram is the Diesel cycle?", CYC_PV, 1, "Diesel: isentropic compression, heat added at constant pressure, isentropic expansion, heat rejected at constant volume."),
             cyc_assume([f"r = {r}, P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {T1} K", f"q<sub>in</sub> = {qin} kJ/kg", f"V<sub>d</sub> = {Vd} L, {rpm} rpm, four-stroke"],
                        ["r<sub>c</sub>", "η<sub>th</sub> (%)", "MEP (kPa)", "Ẇ (kW)"],
                        [("coldair", True, "The problem says so (rule 4)."), ("intrev", True, "Ideal cycle."), ("constP", True, "Diesel adds heat at constant pressure.", "Heat is added at constant pressure (2→3)."),
                         ("four", True, "Given."), ("stationary", True, "Standard for cycles."), ("constv", False, "That's Otto's heat addition."), ("open", False, "The cylinder's air is analyzed as a closed system.")]),
             multi([("T<sub>2</sub> = T<sub>1</sub>r<sup>k−1</sup>; q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>); r<sub>c</sub> = T<sub>3</sub>/T<sub>2</sub>", True, ""),
                    ("T<sub>4</sub> = T<sub>3</sub>(r<sub>c</sub>/r)<sup>k−1</sup>; q<sub>out</sub> = c<sub>v</sub>(T<sub>4</sub> − T<sub>1</sub>)", True, ""),
                    ("MEP = w<sub>net</sub>/(v<sub>1</sub> − v<sub>2</sub>)", True, ""), ("Ẇ = MEP·V<sub>d</sub>·(rpm/60)/2", True, ""),
                    (FIRST_CL + " (per kg, for each process)", True, ""), ("Ẇ = MEP·V<sub>d</sub>·rpm/60", False, "That's a two-stroke engine.")], FIRST_CL),
             strike_custom([term("qin", "q<sub>in</sub>", "L", "+"), term("win", "w<sub>b,in</sub>", "L", "+", True, ["dir"], "The gas expands: work goes out."),
                            term("qout", "q<sub>out</sub>", "L", "−", True, ["dir"], "Heat comes in during 2→3."), term("wout", "w<sub>b,out</sub>", "L", "−"),
                            term("du", "Δu", "R", ""), term("dke", "Δke", "R", "+", True, ["stationary"], ""), term("dpe", "Δpe", "R", "+", True, ["stationary"], "")],
                           "Process 2→3: q<sub>in</sub> = (u<sub>3</sub> − u<sub>2</sub>) + P(v<sub>3</sub> − v<sub>2</sub>) = h<sub>3</sub> − h<sub>2</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)",
                           p="Apply the first law to the heat-addition process, 2→3. Cross out every term that drops."),
             props([("c<sub>p</sub> for air", CPA, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("c<sub>v</sub> for air", CVA, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("R for air", RA, "kJ/kg·K", "A-1", 0.003, "air")]),
             calc([f"T<sub>2</sub> = ({T1})({r})<sup>0.4</sup> = {sg(T2)} K; T<sub>3</sub> = T<sub>2</sub> + q<sub>in</sub>/c<sub>p</sub> = {sg(T3)} K",
                   f"r<sub>c</sub> = T<sub>3</sub>/T<sub>2</sub> = <b>{sg(rc)}</b>",
                   f"T<sub>4</sub> = T<sub>3</sub>(r<sub>c</sub>/r)<sup>0.4</sup> = {sg(T4)} K; q<sub>out</sub> = 0.718({sg(T4)} − {T1}) = {sg(qout)} kJ/kg; w<sub>net</sub> = {sg(wn)} kJ/kg",
                   f"η<sub>th</sub> = w<sub>net</sub>/q<sub>in</sub> = <b>{pct(eta):.1f}%</b>",
                   f"v<sub>1</sub> = RT<sub>1</sub>/P<sub>1</sub> = {sg(v1)} m³/kg; MEP = w<sub>net</sub>/[v<sub>1</sub>(1 − 1/r)] = <b>{sg(mep)} kPa</b>",
                   f"Ẇ = MEP·V<sub>d</sub>·(rpm/60)/2 = ({sg(mep)})({Vd}/1000)({rpm}/60)/2 = <b>{sg(Wd)} kW</b>"]),
             mc(8, f"Is {sg(Wd)} kW believable for a {Vd}-L engine?",
                ["Roughly: an ideal, naturally aspirated diesel makes about 5 to 15 kW per liter at these speeds (turbocharged gensets push in denser air and make two or three times that)",
                 "No, it should be under 1 kW", "No, it should be in the megawatts", "It can't be checked"],
                0, f"That's {sg(Wd / Vd, 3)} kW per liter. An ideal cycle has no friction, heat loss or pumping losses, so a real engine of this size breathing outside air would make less. If you're off by a factor of 2, 60 or 1000, check the four-stroke factor, rpm and liters.")]
    return stem, parts, steps, ctx, prm(locals())

# =================================================================== C15: desuperheater
@template("C15", "Desuperheater: spraying water into steam", 5, "B", 16, "challenge")
def C15(rng):
    P = rng.choice([1000, 1200, 1400, 3000, 5000]); T1 = rng.choice([t for t in W.SH[P] if t >= 400])
    T3 = rng.choice([t for t in W.SH[P] if t < T1 - 50 and t > W.Tsat_true(P) + 15]); Tw = rng.choice([20, 40, 60, 80, 100]); m1 = rng.choice([2, 5, 8, 10, 15, 20])
    s1, s3, w = W.sh(P, T1), W.sh(P, T3), W.satT(Tw)
    y = (s1["h"] - s3["h"]) / (s3["h"] - w["hf"]); m2 = y * m1; m3 = m1 + m2
    Vdot3 = m3 * s3["v"]; Vdot1 = m1 * s1["v"]
    Sg = m3 * s3["s"] - m1 * s1["s"] - m2 * w["sf"]
    stem = (f"A desuperheater cools superheated steam by spraying liquid water into it. Steam at {fP(P)} and {fT(T1)} enters at {m1} kg/s, and liquid water at {fT(Tw)} is sprayed in at the same pressure. "
            f"The mixture leaves at {fP(P)} and {fT(T3)}. The unit is insulated. Determine (a) the spray-water flow rate, (b) the volume flow rate leaving, and (c) the rate of entropy generation.")
    parts = [part("a", "Spray-water flow, ṁ<sub>2</sub>", "kg/s", m2, 0.01, 6,
                  [(m1 * (s3["h"] - w["hf"]) / (s1["h"] - s3["h"]), "Your ratio is upside down. The steam gives up h<sub>1</sub> − h<sub>3</sub>; each kg of water absorbs h<sub>3</sub> − h<sub>2</sub>."),
                   (m1 * 2.0 * (T1 - T3) / (4.18 * (T3 - Tw)), "The water boils and superheats, so cΔT can't follow it. Use table enthalpies.")]),
             part("b", "Exit volume flow, V̇<sub>3</sub>", "m³/s", Vdot3, 0.01, 4, [(m1 * s3["v"], "The water joins the steam: use ṁ<sub>3</sub> = ṁ<sub>1</sub> + ṁ<sub>2</sub>.")]),
             part("c", "Entropy generation, Ṡ<sub>gen</sub>", "kW/K", Sg, 0.02, 6,
                  [(m3 * s3["s"] - m1 * s1["s"], "The spray water carries entropy in: subtract ṁ<sub>2</sub>s<sub>2</sub>."), (m1 * (s3["s"] - s1["s"]), "The water stream counts too.")])]
    steps = [self_step("Find the spray-water flow, the exit volume flow and the entropy generated in an insulated desuperheater. Plan: mass and energy balances give the spray flow; one entropy balance gives the generation."),
             mc(2, "Which mass balance applies?", ["ṁ<sub>1</sub> + ṁ<sub>2</sub> = ṁ<sub>3</sub>", "ṁ<sub>1</sub> = ṁ<sub>3</sub>", "ṁ<sub>2</sub> = ṁ<sub>3</sub> − ṁ<sub>1</sub> = 0", "No mass balance: it's closed"],
                0, "Two streams in, one out, steady. The water becomes part of the steam."),
             assume([f"Steam: {fP(P)}, {fT(T1)}, {m1} kg/s", f"Spray: liquid at {fT(Tw)}", f"Exit: {fP(P)}, {fT(T3)}"], ["ṁ<sub>2</sub> (kg/s)", "V̇<sub>3</sub> (m³/s)", "Ṡ<sub>gen</sub> (kW/K)"],
                    [("open", True, "Three streams cross."), ("steady", True, "Steady operation."), ("adiabatic", True, "Insulated."), ("noshaft", True, "No work."),
                     ("lowke", True, "Small velocities."), ("nope", True, "Same height."), ("steam", True, "Rule 1: A-6 for the steam states."),
                     ("liqT", True, "Rule 1: the spray is compressed liquid; use h<sub>f</sub> and s<sub>f</sub> at its temperature."),
                     ("cpwater", False, "The water changes phase; tables first."), ("tavg", False, "The streams have very different h; one boils.")]),
             multi([("ṁ<sub>1</sub> + ṁ<sub>2</sub> = ṁ<sub>3</sub>", True, ""), (FIRST_SF, True, ""), (SGEN_SF, True, ""), ("V̇ = ṁv", True, ""),
                    ("ṁ<sub>1</sub>c<sub>p</sub>(T<sub>1</sub> − T<sub>3</sub>) = ṁ<sub>2</sub>c(T<sub>3</sub> − T<sub>2</sub>)", False, "The spray water boils; only enthalpies follow that.")], FIRST_SF),
             multi_terms(["ṁ<sub>1</sub>h<sub>1</sub>", "ṁ<sub>2</sub>h<sub>2</sub>"], ["ṁ<sub>3</sub>h<sub>3</sub>"], "ṁ<sub>1</sub>h<sub>1</sub> + ṁ<sub>2</sub>h<sub>2</sub> = (ṁ<sub>1</sub> + ṁ<sub>2</sub>)h<sub>3</sub>"),
             props([("h<sub>1</sub>", s1["h"], "kJ/kg", "A-6", 0.003, f"{fP(P)} block, {fT(T1)} row"), ("s<sub>1</sub>", s1["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P)} block, {fT(T1)} row"),
                    ("h<sub>2</sub> = h<sub>f</sub>", w["hf"], "kJ/kg", "A-4", 0.003, fT(Tw)), ("s<sub>2</sub> = s<sub>f</sub>", w["sf"], "kJ/kg·K", "A-4", 0.003, fT(Tw)),
                    ("h<sub>3</sub>", s3["h"], "kJ/kg", "A-6", 0.003, f"{fP(P)} block, {fT(T3)} row"), ("v<sub>3</sub>", s3["v"], "m³/kg", "A-6", 0.003, f"{fP(P)} block, {fT(T3)} row"),
                    ("s<sub>3</sub>", s3["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P)} block, {fT(T3)} row")]),
             calc([f"Divide by ṁ<sub>1</sub>: ṁ<sub>2</sub>/ṁ<sub>1</sub> = (h<sub>1</sub> − h<sub>3</sub>)/(h<sub>3</sub> − h<sub>2</sub>) = ({num(s1['h'], 1)} − {num(s3['h'], 1)})/({num(s3['h'], 1)} − {num(w['hf'], 2)}) = {sg(y)}",
                   f"ṁ<sub>2</sub> = ({sg(y)})({m1}) = <b>{sg(m2)} kg/s</b>; ṁ<sub>3</sub> = {sg(m3)} kg/s",
                   f"V̇<sub>3</sub> = ṁ<sub>3</sub>v<sub>3</sub> = ({sg(m3)})({sg(s3['v'], 5)}) = <b>{sg(Vdot3)} m³/s</b> (steam in: {sg(Vdot1)} m³/s)",
                   f"Ṡ<sub>gen</sub> = ṁ<sub>3</sub>s<sub>3</sub> − ṁ<sub>1</sub>s<sub>1</sub> − ṁ<sub>2</sub>s<sub>2</sub> = ({sg(m3)})({num(s3['s'], 4)}) − ({m1})({num(s1['s'], 4)}) − ({sg(m2)})({num(w['sf'], 4)}) = <b>{sg(Sg, 3)} kW/K</b>"]),
             mc(8, "Cooling the steam lowers its entropy. Why is Ṡ<sub>gen</sub> still positive?",
                ["The cold spray water's entropy jumps as it boils and superheats, by more than the steam's entropy drops",
                 "Because the unit is insulated", "It isn't always; it depends on the pressure", "Because the volume flow goes down"],
                0, "Mixing a cold liquid into hot steam is about as irreversible as a mixer gets. Plants accept the loss because it is a fast, simple way to protect a turbine or process from overheated steam.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== C16: throttle + evaporator chilling water
@template("C16", "Expansion valve and evaporator chilling water", 5, "C", 16, "challenge")
def C16(rng):
    PH = rng.choice([800, 900, 1000, 1200]); PL = rng.choice([140, 160, 180, 200, 240])
    Twi = rng.choice([15, 20, 25]); Two = rng.choice([5, 10]); mw = rng.choice([0.2, 0.3, 0.5, 0.8, 1.0, 1.5])
    hi, lo = RF.satP(PH), RF.satP(PL); w1, w2 = W.satT(Twi), W.satT(Two)
    h1 = hi["hf"]; x2 = (h1 - lo["hf"]) / lo["hfg"]; h3 = lo["hg"]
    Q = mw * (w1["hf"] - w2["hf"]); mR = Q / (h3 - h1)
    s2 = lo["sf"] + x2 * lo["sfg"]; SgV = mR * (s2 - hi["sf"]); SgE = mR * (lo["sg"] - s2) + mw * (w2["sf"] - w1["sf"])
    stem = (f"Saturated liquid R-134a at {PH} kPa passes through an adiabatic expansion valve to {PL} kPa and then through an insulated evaporator, leaving as saturated vapor at {PL} kPa. "
            f"In the evaporator it chills {mw} kg/s of water from {fT(Twi)} to {fT(Two)}. Determine (a) the quality leaving the valve, (b) the R-134a mass flow rate, "
            "(c) the rate of entropy generation in the valve, and (d) the rate of entropy generation in the evaporator.")
    parts = [part("a", "Quality after the valve, x<sub>2</sub>", "", x2, 0.01, 3, [((h1 - lo["hf"]) / lo["hg"], "x = (h − h<sub>f</sub>)/h<sub>fg</sub>, not over h<sub>g</sub>.")]),
             part("b", "R-134a flow, ṁ<sub>R</sub>", "kg/s", mR, 0.01, 4, [(Q / lo["hfg"], "The R-134a enters the evaporator already partly vapor: it absorbs h<sub>g</sub> − h<sub>2</sub>, not all of h<sub>fg</sub>."),
                                                                         (mw * 4.18 * (Twi - Two) / (h3 - h1), "Tables first for the water: h<sub>f</sub> at each temperature.")]),
             part("c", "Ṡ<sub>gen</sub> in the valve", "kW/K", SgV, 0.02, 4, [(0.0, "Adiabatic isn't reversible. Throttling generates entropy: ṁ(s<sub>2</sub> − s<sub>1</sub>)."),
                                                                             (mR * (lo["sf"] - hi["sf"]), "s<sub>2</sub> is for the mixture: s<sub>f</sub> + x<sub>2</sub>s<sub>fg</sub>.")]),
             part("d", "Ṡ<sub>gen</sub> in the evaporator", "kW/K", SgE, 0.03, 5, [(mR * (lo["sg"] - s2), "The water's entropy falls; include both streams."),
                                                                                  (mR * (lo["sg"] - s2) + mw * (w1["sf"] - w2["sf"]), "Sign: the water is cooled, so its Δs is negative.")])]
    steps = [self_step("Find the quality after the valve, the R-134a flow, and the entropy generated in the valve and in the evaporator. Plan: h stays constant through the valve; the evaporator's energy balance gives the flow; one entropy balance per device."),
             mc(2, "On a T-s diagram, where does the valve take the R-134a?",
                ["From the saturated-liquid line at P<sub>H</sub> down and to the right into the dome at P<sub>L</sub>: T falls, s rises",
                 "Straight down at constant s", "Along the saturated-liquid line", "Up and to the right, out of the dome"],
                0, "Throttling keeps h constant, not s. The liquid flashes partly to vapor and cools, and its entropy rises because the process is irreversible."),
             assume([f"Valve: saturated liquid at {PH} kPa → {PL} kPa", f"Evaporator exit: saturated vapor at {PL} kPa", f"Water: {mw} kg/s, {fT(Twi)} → {fT(Two)}"],
                    ["x<sub>2</sub>", "ṁ<sub>R</sub> (kg/s)", "Ṡ<sub>gen,valve</sub> (kW/K)", "Ṡ<sub>gen,evap</sub> (kW/K)"],
                    [("open", True, "Both streams flow."), ("steady", True, "Steady operation."), ("adiabatic", True, "Valve and evaporator are insulated."), ("noshaft", True, "No work in either."),
                     ("lowke", True, "Small velocities."), ("nope", True, "Same height."), ("thr", True, "The expansion valve is a throttle."),
                     ("r134", True, "Rule 1: R-134a from A-12."), ("liqT", True, "Rule 1: water h and s from A-4 at its temperatures."),
                     ("isen", False, "Throttling is irreversible; s rises."), ("cpwater", False, "Tables first for water.")]),
             multi([("Valve: h<sub>2</sub> = h<sub>1</sub>", True, ""), ("Evaporator: ṁ<sub>R</sub>(h<sub>3</sub> − h<sub>2</sub>) = ṁ<sub>w</sub>(h<sub>w,in</sub> − h<sub>w,out</sub>)", True, ""),
                    (SGEN_SF, True, ""), ("s<sub>2</sub> = s<sub>1</sub>", False, "That's isentropic. A valve keeps h, not s.")], FIRST_SF),
             multi_terms(["ṁ<sub>R</sub>h<sub>2</sub>", "ṁ<sub>w</sub>h<sub>w,in</sub>"], ["ṁ<sub>R</sub>h<sub>3</sub>", "ṁ<sub>w</sub>h<sub>w,out</sub>"],
                         "ṁ<sub>R</sub>(h<sub>3</sub> − h<sub>2</sub>) = ṁ<sub>w</sub>(h<sub>w,in</sub> − h<sub>w,out</sub>)",
                         p="Apply the steady-flow first law to the whole evaporator (both streams inside). Cross out every term that drops."),
             props([("h<sub>f</sub> at P<sub>H</sub>", hi["hf"], "kJ/kg", "A-12", 0.003, f"{PH} kPa"), ("s<sub>f</sub> at P<sub>H</sub>", hi["sf"], "kJ/kg·K", "A-12", 0.004, f"{PH} kPa"),
                    ("h<sub>f</sub> at P<sub>L</sub>", lo["hf"], "kJ/kg", "A-12", 0.004, f"{PL} kPa"), ("h<sub>fg</sub> at P<sub>L</sub>", lo["hfg"], "kJ/kg", "A-12", 0.003, f"{PL} kPa"),
                    ("h<sub>g</sub> at P<sub>L</sub>", lo["hg"], "kJ/kg", "A-12", 0.003, f"{PL} kPa"), ("s<sub>f</sub> at P<sub>L</sub>", lo["sf"], "kJ/kg·K", "A-12", 0.004, f"{PL} kPa"),
                    ("s<sub>fg</sub> at P<sub>L</sub>", lo["sfg"], "kJ/kg·K", "A-12", 0.003, f"{PL} kPa"), ("s<sub>g</sub> at P<sub>L</sub>", lo["sg"], "kJ/kg·K", "A-12", 0.003, f"{PL} kPa"),
                    ("h<sub>w,in</sub>, s<sub>w,in</sub>: h<sub>f</sub>", w1["hf"], "kJ/kg", "A-4", 0.003, fT(Twi)), ("s<sub>f</sub> at T<sub>w,in</sub>", w1["sf"], "kJ/kg·K", "A-4", 0.004, fT(Twi)),
                    ("h<sub>f</sub> at T<sub>w,out</sub>", w2["hf"], "kJ/kg", "A-4", 0.003, fT(Two)), ("s<sub>f</sub> at T<sub>w,out</sub>", w2["sf"], "kJ/kg·K", "A-4", 0.006, fT(Two))]),
             calc([f"h<sub>2</sub> = h<sub>1</sub> = {num(h1, 2)} kJ/kg; x<sub>2</sub> = ({num(h1, 2)} − {num(lo['hf'], 2)})/{num(lo['hfg'], 2)} = <b>{sg(x2, 4)}</b>",
                   f"Q̇ = ṁ<sub>w</sub>(h<sub>w,in</sub> − h<sub>w,out</sub>) = {mw}({num(w1['hf'], 2)} − {num(w2['hf'], 2)}) = {sg(Q)} kW",
                   f"ṁ<sub>R</sub> = Q̇/(h<sub>g</sub> − h<sub>2</sub>) = {sg(Q)}/({num(lo['hg'], 2)} − {num(h1, 2)}) = <b>{sg(mR, 4)} kg/s</b>",
                   f"s<sub>2</sub> = s<sub>f</sub> + x<sub>2</sub>s<sub>fg</sub> = {sg(s2, 5)} kJ/kg·K; Ṡ<sub>gen,valve</sub> = ṁ<sub>R</sub>(s<sub>2</sub> − s<sub>1</sub>) = ({sg(mR, 4)})({sg(s2, 5)} − {num(hi['sf'], 5)}) = <b>{sg(SgV, 3)} kW/K</b>",
                   f"Ṡ<sub>gen,evap</sub> = ṁ<sub>R</sub>(s<sub>g</sub> − s<sub>2</sub>) + ṁ<sub>w</sub>(s<sub>w,out</sub> − s<sub>w,in</sub>) = ({sg(mR, 4)})({num(lo['sg'], 5)} − {sg(s2, 5)}) + {mw}({num(w2['sf'], 4)} − {num(w1['sf'], 4)}) = <b>{sg(SgE, 3)} kW/K</b>"]),
             mc(8, "Both numbers are small and positive. Which device would you redesign first, and why?",
                ["Compare them: the bigger Ṡ<sub>gen</sub> marks the bigger waste. The valve's loss is the price of skipping an expansion turbine; the evaporator's comes from the temperature gap between the water and the R-134a",
                 "Neither: positive entropy generation means the system works well", "The evaporator, always, because it has two streams", "The valve, always, because it has no moving parts"],
                0, "Entropy generation is a map of where the losses are. Shrinking the evaporator's temperature gap (a bigger exchanger) or recovering work in the expansion both cut it, at a cost. Comparing the two numbers tells you where the money buys the most.")]
    return stem, parts, steps, None, prm(locals())

# ---------------------------------------------------------------- build
def build(nvar=24, seed=20261109):
    out = []
    for T in TEMPLATES:
        rng = random.Random(seed + sum(map(ord, T["id"])) * 7)
        seen, vs, tries = set(), [], 0
        while len(vs) < nvar and tries < 6000:
            tries += 1
            try:
                stem, parts, steps, ctx, p = T["fn"](rng)
            except (AssertionError, ValueError, IndexError, ZeroDivisionError):
                continue
            if stem in seen: continue
            seen.add(stem)
            steps = [shuffle_mc(s, rng) for s in steps]
            assert [s["n"] for s in steps] == list(range(1, 9)), (T["id"], [s["n"] for s in steps])
            vs.append({"stem": stem, "fig": None, "parts": parts, "steps": steps, "ctx": ctx, "_p": p})
        assert len(vs) == nvar, (T["id"], len(vs), tries)
        out.append({"id": T["id"], "title": T["title"], "ch": T["ch"], "slot": T["slot"], "pts": T["pts"], "tier": T["tier"], "v": vs})
    return out

if __name__ == "__main__":
    tpls = build()
    json.dump(tpls, open("challenge_templates.json", "w"), ensure_ascii=False)
    print(len(tpls), [(t["id"], len(t["v"])) for t in tpls])
