"""Final-exam challenge set (held back; NOT on the public prep site until Matthew says so).

Run from anywhere with the public site's tools on the path:
    PYTHONPATH=/path/to/thermo-exam1/tools python3 gen_final.py
Writes final_templates.json next to this file: the nine new templates below plus the five Brayton-family
templates pulled off the public page on Nov 11 (E19, E20 from gen_exam2; C10, C11, C12 from gen_challenge).
Modeled on Matthew's old Finals (F23 reheat Rankine on Ghost's pellets, F24/F25 simple real Rankine, F23 pump,
F24 two-fuel Brayton and gas generator, F25 real-compressor Brayton) and the Final Exam Topics list
(Ch. 10, cogeneration, combined cycles, Stirling and Ericsson). Ch. 8 (exergy) and Ch. 11 stay out.
"""
import json, math, os, random, sys
import gen_challenge as GC
from gen_challenge import *          # helpers, W (steam tables), a17, ec.LIB, part/step builders
import gen_exam2 as GE

HERE = os.path.dirname(os.path.abspath(__file__))

# A-6 blocks the Rankine problems use that the Exam 2 build didn't need (rows as Çengel prints them)
for _P, _rows in {2000: [250, 300, 350, 400, 450, 500, 600, 700, 800], 4000: [275, 300, 350, 400, 450, 500, 600, 700, 800],
                  6000: [300, 350, 400, 450, 500, 550, 600, 700, 800], 7000: [300, 350, 400, 450, 500, 550, 600, 700, 800],
                  9000: [325, 350, 400, 450, 500, 550, 600, 650, 700, 800], 12500: [350, 400, 450, 500, 550, 600, 650, 700, 800],
                  15000: [350, 400, 450, 500, 550, 600, 650, 700, 800]}.items():
    W.SH.setdefault(_P, [t for t in _rows if t > W.satP(_P)["T"] + 2])

ec.LIB.update({
    "pumpliq": ("Pump: incompressible liquid", "The pump handles liquid water, which is nearly incompressible: w<sub>p,s</sub> = v<sub>1</sub>(P<sub>out</sub> − P<sub>in</sub>)."),
    "condsat": ("Condenser exit is saturated liquid", "The water leaves the condenser as saturated liquid at the condenser pressure."),
    "nodrop":  ("No pressure drops in boiler or condenser", "Heat is added in the boiler and rejected in the condenser at constant pressure."),
    "fwhsat":  ("Open feedwater heater exit is saturated liquid", "The open feedwater heater is insulated, and its exit is saturated liquid at the heater pressure."),
    "procsat": ("Process heater exit is saturated liquid", "Steam sent to the process heater leaves it as saturated liquid at the heater pressure."),
    "hrsg":    ("Heat recovery steam generator is insulated", "All the heat the exhaust gas gives up in the HRSG goes into the steam."),
    "regenI":  ("Ideal regenerator", "The regenerator is ideal: the gas leaves the hot side at the temperature the cold side entered, so no outside heat is needed between the two isotherms."),
    "isoT":    ("Isothermal heat transfer at T<sub>H</sub> and T<sub>L</sub>", "Heat comes in only at T<sub>H</sub> (isothermal expansion) and leaves only at T<sub>L</sub> (isothermal compression)."),
    "condins": ("Condenser is insulated outside", "The condenser is insulated: all the heat the steam gives up goes into the cooling water."),
})

FT = []
def ftemplate(tid, title, ch, slot, pts, tier, note=None):
    def deco(fn):
        FT.append(dict(id=tid, title=title, ch=ch, slot=slot, pts=pts, tier=tier, fn=fn, grp="final", note=note))
        return fn
    return deco

def dome_x(P, s):
    st = W.satP(P); x = (s - st["sf"]) / st["sfg"]; return x, st["hf"] + x * st["hfg"], st

def at_Ps(P, s):
    """State at pressure P with entropy s: wet (A-5) or superheated (A-6 interpolation). Returns (h, how, wet)."""
    st = W.satP(P)
    if s < st["sg"]:
        x = (s - st["sf"]) / st["sfg"]
        return st["hf"] + x * st["hfg"], f"s &lt; s<sub>g</sub> at {fP(P)}, so it's wet: x = (s − s<sub>f</sub>)/s<sub>fg</sub> = {sg(x, 4)}, h = h<sub>f</sub> + xh<sub>fg</sub>", True
    d, a, b = w_interp(P, "s", s)
    return d["h"], f"s &gt; s<sub>g</sub> at {fP(P)}, so it's superheated: {fP(P)} block, " + between(a, b, "s", s, 4), False

def pump(Pin, Pout, eta=1.0):
    st = W.satP(Pin); ws = st["vf"] * (Pout - Pin); return st, ws / eta

TS_RANKINE = ("On the T-s diagram: 1 sits on the saturated-liquid line at the condenser pressure; the pump lifts it almost straight up to 2 (a tiny step); "
              "the boiler runs along the high-pressure line through the dome to the superheated state 3; the turbine drops to 4 at the condenser pressure "
              "(straight down if ideal, leaning right if real); the condenser runs left along the low-pressure line back to 1.")

def rk_assume(givens, finds, extra=(), real=True):
    base = [("open", True, "Each device is a steady-flow control volume."), ("steady", True, "Steady operation."), ("lowke", True, "Small KE changes."), ("nope", True, "Small PE changes."),
            ("adiabatic", True, "Pumps and turbines are adiabatic.", "The pumps and turbines are adiabatic."), ("steam", True, "Rule 1: steam tables (A-4 to A-6) for every state."),
            ("pumpliq", True, "Liquid water in the pump."), ("noshaft", True, "Boilers, condensers and heaters have no shaft or wires.", "Boilers, condensers and heaters have no shaft or wires."), ("condsat", True, "Standard for Rankine cycles unless told otherwise."), ("nodrop", True, "Standard for Rankine cycles."),
            ("steamideal", False, "Rule 1: never ideal gas for steam.")]
    if real: base.append(("isen", True, "For the comparison (ideal) turbine and pump: s<sub>out,s</sub> = s<sub>in</sub>.", "The comparison turbine and pump are isentropic, so s<sub>2s</sub> = s<sub>1</sub> and s<sub>4s</sub> = s<sub>3</sub>."))
    return assume(givens, finds, base + list(extra))

def turb_strike(i, o):
    return sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Win": (["dir"], "Work comes out of a turbine."),
                      "mke1": (["lowke"], "Small KE."), "mke2": (["lowke"], "Small KE."), "mpe1": (["nope"], "Small PE."), "mpe2": (["nope"], "Small PE."), "dE": (["steady"], "Steady.")},
                     f"Turbine: w<sub>T,out</sub> = h<sub>{i}</sub> − h<sub>{o}</sub>", p=f"Apply the steady-flow first law to the turbine ({i}→{o}; the template labels inlet 1 and exit 2). Cross out every term that drops.")

# =================================================================== F1: Ghost's pellet-fired reheat plant (F23 Final 2.1)
@ftemplate("F1", "Ghost's pellet-fired reheat steam plant", 10, "R", 30, "hardest", "Old Final (F23), reheat Rankine with real turbines and pump")
def F1(rng):
    P3 = rng.choice([4000, 5000, 6000, 8000, 10000]); T3 = rng.choice([t for t in W.SH[P3] if 400 <= t <= 600])
    P4 = rng.choice([p for p in (400, 600, 800, 1000, 1200, 1400, 2000) if P3 / 16 <= p <= P3 / 4]); T5 = rng.choice([t for t in W.SH[P4] if 350 <= t <= T3])
    Pc = rng.choice([7.5, 10, 15, 20]); eT = rng.choice([0.85, 0.87, 0.88, 0.90, 0.92]); eP = rng.choice([0.80, 0.85, 0.90]); Wmw = rng.choice([5, 10, 15, 25])
    s3 = W.sh(P3, T3); s5 = W.sh(P4, T5)
    st1, wp = pump(Pc, P3, eP); h1 = st1["hf"]; h2 = h1 + wp
    h4s, how4, wet4 = at_Ps(P4, s3["s"]); h4 = s3["h"] - eT * (s3["h"] - h4s)
    x6s, h6s, stc = dome_x(Pc, s5["s"]); assert x6s < 0.99
    h6 = s5["h"] - eT * (s5["h"] - h6s); x6 = (h6 - stc["hf"]) / stc["hfg"]; assert x6 < 1
    wt = (s3["h"] - h4) + (s5["h"] - h6); qin = (s3["h"] - h2) + (s5["h"] - h4); wn = wt - wp; eta = wn / qin; m = Wmw * 1000 / wn
    x_noreheat, h_nr_s, _ = dome_x(Pc, s3["s"]); x_nr = (s3["h"] - eT * (s3["h"] - h_nr_s) - stc["hf"]) / stc["hfg"]
    stem = (f"Your rabbit colleague Ghost wants a steam power plant for the rescue whose boiler burns its used wood-pellet bedding. It's a reheat Rankine cycle making {Wmw} MW of net power. Steam enters the high-pressure turbine at "
            f"{fP(P3)} and {fT(T3)} and leaves at {fP(P4)}; it is reheated to {fT(T5)} and expands in the low-pressure turbine to the condenser at {fP(Pc)}. Both turbines have an isentropic efficiency of "
            f"{int(round(eT * 100))}% and the pump {int(round(eP * 100))}%. Determine (a) the enthalpy leaving the high-pressure turbine, (b) the quality leaving the low-pressure turbine, "
            "(c) the thermal efficiency, and (d) the steam mass flow rate.")
    parts = [part("a", "h<sub>4</sub>, high-pressure turbine exit", "kJ/kg", h4, 0.005, 6, [(h4s, "That's the isentropic exit. A real turbine extracts less: h<sub>4</sub> = h<sub>3</sub> − η(h<sub>3</sub> − h<sub>4s</sub>)."),
                                                                                         (s3["h"] - (s3["h"] - h4s) / eT, "For a turbine, multiply the ideal drop by η; dividing gives more than ideal.")]),
             part("b", "x<sub>6</sub>, low-pressure turbine exit", "", x6, 0.01, 6, [(x6s, "That's the isentropic exit quality. The real exit is drier because less energy left as work."),
                                                                                  (x_nr, "That's the exit quality without reheat. Expand from state 5 (after reheating), not state 3.")]),
             part("c", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 10, [(pct(wn / (s3["h"] - h2)), "Reheating adds heat too: q<sub>in</sub> = (h<sub>3</sub> − h<sub>2</sub>) + (h<sub>5</sub> − h<sub>4</sub>)."),
                                                                                   (pct(wt / qin), "Subtract the pump work: w<sub>net</sub> = w<sub>T</sub> − w<sub>p</sub>."),
                                                                                   (pct(((s3["h"] - h4s) + (s5["h"] - h6s) - wp * eP) / ((s3["h"] - h2) + (s5["h"] - h4s))), "That's the ideal cycle. Use the actual h<sub>4</sub> and h<sub>6</sub>.")]),
             part("d", "Steam mass flow, ṁ", "kg/s", m, 0.012, 8, [(Wmw / wn, "MW to kW: multiply by 1000."), (Wmw * 1000 / wt, "Divide by the net work, not the turbine work.")])]
    ctx = {"t": "Is burning pellets clean energy?",
           "b": "Wood pellets are burned for electricity because trees regrow, but making them takes heavy industry. Enviva, once the world's largest wood-pellet producer, ran about ten plants in the US Southeast and filed for bankruptcy in 2024. Environmental lawyers reported that pellet plants put out dust, fine particles and other air pollution, often next to communities of color that already carry a heavy industrial load, while the pellets were shipped overseas to be burned.",
           "q": "Ghost's plant would burn bedding the rescue has already used. A utility-scale plant buys its pellets from factories like Enviva's. When we decide whether to call a power source renewable, should the pollution from making the fuel, and who breathes it, count?",
           "src": ["SELC: World's largest biomass wood pellet producer files for bankruptcy (2024)", "https://www.southernenvironment.org/?p=31990"]}
    steps = [self_step("Find the high-pressure turbine exit, the low-pressure exit quality, the efficiency and the steam flow of a reheat Rankine cycle with real turbines and pump. Plan: fix all six states in order, using η for each real device, then add up two turbine works, two boiler heats, and one pump."),
             mc(2, "Sketch the T-s diagram. Which description is right?",
                ["1 on the liquid line at P<sub>c</sub>; tiny pump step to 2; boiler to 3; HP turbine down to 4 at P<sub>4</sub> (leaning right); reheat along P<sub>4</sub> to 5; LP turbine down to 6 at P<sub>c</sub>; condenser back to 1",
                 "Like a simple Rankine cycle, but the reheat happens after the LP turbine", "The reheat runs at the boiler pressure", "Reheat makes the turbine exit wetter"],
                0, "Reheating at an intermediate pressure moves the LP expansion to the right on T-s, so the steam ends drier. That protects the turbine blades from water droplets."),
             rk_assume([f"HP turbine in: {fP(P3)}, {fT(T3)}", f"Reheat: {fP(P4)} to {fT(T5)}", f"Condenser: {fP(Pc)}", f"η<sub>T</sub> = {eT} (both), η<sub>P</sub> = {eP}", f"Ẇ<sub>net</sub> = {Wmw} MW"],
                       ["h<sub>4</sub> (kJ/kg)", "x<sub>6</sub>", "η<sub>th</sub> (%)", "ṁ (kg/s)"]),
             multi([("w<sub>p</sub> = v<sub>1</sub>(P<sub>2</sub> − P<sub>1</sub>)/η<sub>P</sub>; h<sub>2</sub> = h<sub>1</sub> + w<sub>p</sub>", True, ""),
                    ("η<sub>T</sub> = (h<sub>in</sub> − h<sub>out</sub>)/(h<sub>in</sub> − h<sub>out,s</sub>) for each turbine", True, ""),
                    ("q<sub>in</sub> = (h<sub>3</sub> − h<sub>2</sub>) + (h<sub>5</sub> − h<sub>4</sub>); w<sub>T</sub> = (h<sub>3</sub> − h<sub>4</sub>) + (h<sub>5</sub> − h<sub>6</sub>)", True, ""),
                    ("η<sub>th</sub> = (w<sub>T</sub> − w<sub>p</sub>)/q<sub>in</sub>; ṁ = Ẇ<sub>net</sub>/w<sub>net</sub>", True, ""), (FIRST_SF, True, ""),
                    ("η = 1 − T<sub>L</sub>/T<sub>H</sub>", False, "That's Carnot, an upper limit, not this cycle's efficiency.")], FIRST_SF),
             turb_strike(5, 6),
             props([("h<sub>1</sub> = h<sub>f</sub>", h1, "kJ/kg", "A-5", 0.003, fP(Pc)), ("v<sub>1</sub> = v<sub>f</sub>", st1["vf"], "m³/kg", "A-5", 0.003, fP(Pc)),
                    ("h<sub>3</sub>", s3["h"], "kJ/kg", "A-6", 0.003, f"{fP(P3)} block, {fT(T3)} row"), ("s<sub>3</sub>", s3["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P3)} block, {fT(T3)} row"),
                    ("h<sub>4s</sub> (s = s<sub>3</sub>)", h4s, "kJ/kg", "A-5" if wet4 else "A-6", 0.004, f"{fP(P4)}"),
                    ("h<sub>5</sub>", s5["h"], "kJ/kg", "A-6", 0.003, f"{fP(P4)} block, {fT(T5)} row"), ("s<sub>5</sub>", s5["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P4)} block, {fT(T5)} row"),
                    ("h<sub>f</sub> at P<sub>c</sub>", stc["hf"], "kJ/kg", "A-5", 0.003, fP(Pc)), ("h<sub>fg</sub> at P<sub>c</sub>", stc["hfg"], "kJ/kg", "A-5", 0.003, fP(Pc)),
                    ("s<sub>f</sub> at P<sub>c</sub>", stc["sf"], "kJ/kg·K", "A-5", 0.003, fP(Pc)), ("s<sub>fg</sub> at P<sub>c</sub>", stc["sfg"], "kJ/kg·K", "A-5", 0.003, fP(Pc))]),
             calc([f"Pump: w<sub>p</sub> = v<sub>1</sub>(P<sub>3</sub> − P<sub>c</sub>)/η<sub>P</sub> = ({st1['vf']})({P3} − {Pc:g})/{eP} = {sg(wp)} kJ/kg; h<sub>2</sub> = {num(h1, 2)} + {sg(wp)} = {sg(h2, 5)} kJ/kg",
                   f"HP turbine: {how4}; h<sub>4s</sub> = {sg(h4s, 5)} kJ/kg",
                   f"h<sub>4</sub> = {num(s3['h'], 1)} − {eT}({num(s3['h'], 1)} − {sg(h4s, 5)}) = <b>{sg(h4, 5)} kJ/kg</b>",
                   f"LP turbine: x<sub>6s</sub> = ({num(s5['s'], 4)} − {num(stc['sf'], 4)})/{num(stc['sfg'], 4)} = {sg(x6s, 4)}; h<sub>6s</sub> = {sg(h6s, 5)} kJ/kg",
                   f"h<sub>6</sub> = {num(s5['h'], 1)} − {eT}({num(s5['h'], 1)} − {sg(h6s, 5)}) = {sg(h6, 5)} kJ/kg; x<sub>6</sub> = (h<sub>6</sub> − h<sub>f</sub>)/h<sub>fg</sub> = <b>{sg(x6, 4)}</b>",
                   f"w<sub>T</sub> = ({num(s3['h'], 1)} − {sg(h4, 5)}) + ({num(s5['h'], 1)} − {sg(h6, 5)}) = {sg(wt)} kJ/kg; w<sub>net</sub> = {sg(wt)} − {sg(wp)} = {sg(wn)} kJ/kg",
                   f"q<sub>in</sub> = ({num(s3['h'], 1)} − {sg(h2, 5)}) + ({num(s5['h'], 1)} − {sg(h4, 5)}) = {sg(qin)} kJ/kg; η<sub>th</sub> = <b>{pct(eta):.1f}%</b>",
                   f"ṁ = {Wmw * 1000}/{sg(wn)} = <b>{sg(m)} kg/s</b>"]),
             mc(8, f"Without reheat, the same turbine would leave the steam at x ≈ {sg(x_nr, 3)}. What did reheat buy?",
                [f"Drier exhaust (x<sub>6</sub> = {sg(x6, 3)}), which protects the last turbine blades, plus more work per kilogram; the efficiency changes only a little",
                 "A big jump in efficiency, which is the main reason to reheat", "Nothing; reheat only costs fuel", "A lower condenser pressure"],
                0, "Reheat's main job is moisture control; it lets plants use higher boiler pressures without wrecking the low-pressure turbine. Pump work is tiny next to turbine work because the pump moves liquid, which is why the Rankine cycle has a small back work ratio.")]
    return stem, parts, steps, ctx, prm(locals())

# =================================================================== F2: simple real Rankine with river cooling (F24/F25 Final)
@ftemplate("F2", "Coal-to-gas plant: real Rankine cycle and its cooling water", 10, "R", 26, "challenge", "Old Finals (F24, F25), simple Rankine with a real turbine")
def F2(rng):
    P3 = rng.choice([3000, 4000, 5000, 6000, 8000, 10000]); T3 = rng.choice([t for t in W.SH[P3] if 400 <= t <= 600]); Pc = rng.choice([7.5, 10, 15, 20])
    eT = rng.choice([0.82, 0.85, 0.87, 0.88, 0.90]); eP = rng.choice([0.80, 0.85, 1.0]); Wmw = rng.choice([100, 150, 200, 300, 400])
    Tw1 = rng.choice([10, 15]); dTw = rng.choice([5, 10]); Tw2 = Tw1 + dTw
    s3 = W.sh(P3, T3); st1, wp = pump(Pc, P3, eP); h1 = st1["hf"]; h2 = h1 + wp
    x4s, h4s, stc = dome_x(Pc, s3["s"]); assert x4s < 0.97
    h4 = s3["h"] - eT * (s3["h"] - h4s); x4 = (h4 - stc["hf"]) / stc["hfg"]; assert x4 < 1
    wn = (s3["h"] - h4) - wp; qin = s3["h"] - h2; eta = wn / qin; m = Wmw * 1000 / wn; QL = m * (h4 - h1)
    w1, w2 = W.satT(Tw1), W.satT(Tw2); mw = QL / (w2["hf"] - w1["hf"])
    eta_ideal = ((s3["h"] - h4s) - wp * eP) / (s3["h"] - (h1 + wp * eP))
    pump_txt = "an ideal pump" if eP == 1.0 else f"a pump with an isentropic efficiency of {int(round(eP * 100))}%"
    stem = (f"A plant converted from coal to natural gas keeps its steam cycle: a simple Rankine cycle making {Wmw} MW of net power. Steam enters the turbine at {fP(P3)} and {fT(T3)}, and the condenser runs at {fP(Pc)}. "
            f"The turbine's isentropic efficiency is {int(round(eT * 100))}%, with {pump_txt}. River water cools the condenser, warming from {fT(Tw1)} to {fT(Tw2)}. "
            "Determine (a) the quality leaving the turbine, (b) the thermal efficiency, (c) the steam mass flow rate, and (d) the cooling-water flow rate.")
    parts = [part("a", "Turbine exit quality, x<sub>4</sub>", "", x4, 0.008, 5, [(x4s, "That's the isentropic exit quality. Use η to find the actual h<sub>4</sub> first.")]),
             part("b", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 7, [(pct(eta_ideal), "That's the ideal cycle. Use the actual h<sub>4</sub>."), (pct((s3["h"] - h4) / qin), "Subtract the pump work."),
                                                                                   (pct(1 - (Pc and (stc["T"] + 273.15)) / (T3 + 273.15)), "That's Carnot between the boiler exit and the condenser temperatures, an upper limit.")]),
             part("c", "Steam mass flow, ṁ", "kg/s", m, 0.012, 6, [(Wmw * 1000 / (s3["h"] - h4), "Divide by the net work, not the turbine work.")]),
             part("d", "Cooling-water flow, ṁ<sub>w</sub>", "kg/s", mw, 0.015, 8, [(m * (h4s - h1) / (w2["hf"] - w1["hf"]), "The steam enters the condenser at the actual h<sub>4</sub>, not h<sub>4s</sub>."),
                                                                                    (Wmw * 1000 / (w2["hf"] - w1["hf"]), "The river takes the waste heat, Q̇<sub>out</sub> = ṁ(h<sub>4</sub> − h<sub>1</sub>), not the power."),
                                                                                    (QL / (4.18 * dTw), "Tables first for liquid water: h<sub>f</sub> at each temperature (A-4).")])]
    ctx = {"t": "Washington's last coal plant",
           "b": "A 2011 state law required TransAlta's Centralia plant, Washington's only coal plant, to stop burning coal by the end of 2025. It hasn't run since mid-December 2025, even as federal emergency orders told it to stay ready as a coal plant. Under a July 2026 agreement with the Department of Ecology, it is to be converted to burn natural gas as a backup (peaker) plant by 2028, with TransAlta putting $7 million to $21 million into clean-energy projects in Lewis and Thurston counties.",
           "q": "The steam cycle you just analyzed doesn't care what heats the boiler. What changes for the people of Centralia when the fuel changes, and who should decide how a town that built itself around a plant moves on?",
           "src": ["WA Department of Ecology news release, July 31, 2026", "https://ecology.wa.gov/about-us/who-we-are/news/2026/july-31-state-s-only-coal-power-plant-shifting-to-natural-gas-serve-as-backup-power-for-region"]}
    steps = [self_step("Find the turbine exit quality, the efficiency, the steam flow and the river water needed for a simple Rankine cycle with a real turbine. Plan: four states in order; the net power sets ṁ; the condenser's energy balance sets the river flow."),
             mc(2, "Sketch the cycle on T-s. Which description is right?", [TS_RANKINE, "A rectangle, like a Carnot cycle", "The pump runs along the saturated-liquid line", "The turbine exit is always superheated"],
                0, "Mark the ideal turbine exit 4s straight below 3 and the real exit 4 to its right. The condenser line from 4 to 1 is where the river picks up the waste heat."),
             rk_assume([f"Turbine in: {fP(P3)}, {fT(T3)}", f"Condenser: {fP(Pc)}", f"η<sub>T</sub> = {eT}, η<sub>P</sub> = {eP}", f"Ẇ<sub>net</sub> = {Wmw} MW", f"River: {fT(Tw1)} → {fT(Tw2)}"],
                       ["x<sub>4</sub>", "η<sub>th</sub> (%)", "ṁ (kg/s)", "ṁ<sub>w</sub> (kg/s)"], [("liqT", True, "Rule 1: river water h from A-4 at its temperature."), ("condins", True, "Standard for condenser problems."), ("cpwater", False, "Tables first for water.")]),
             multi([("w<sub>p</sub> = v<sub>1</sub>(P<sub>2</sub> − P<sub>1</sub>)/η<sub>P</sub>", True, ""), ("h<sub>4</sub> = h<sub>3</sub> − η<sub>T</sub>(h<sub>3</sub> − h<sub>4s</sub>)", True, ""),
                    ("η<sub>th</sub> = (w<sub>T</sub> − w<sub>p</sub>)/(h<sub>3</sub> − h<sub>2</sub>)", True, ""), ("Condenser: ṁ(h<sub>4</sub> − h<sub>1</sub>) = ṁ<sub>w</sub>(h<sub>w2</sub> − h<sub>w1</sub>)", True, ""), (FIRST_SF, True, ""),
                    ("ṁ<sub>w</sub> = Ẇ<sub>net</sub>/(h<sub>w2</sub> − h<sub>w1</sub>)", False, "The river carries the waste heat, not the power.")], FIRST_SF),
             multi_terms(["ṁh<sub>4</sub>", "ṁ<sub>w</sub>h<sub>w1</sub>"], ["ṁh<sub>1</sub>", "ṁ<sub>w</sub>h<sub>w2</sub>"], "Condenser: ṁ(h<sub>4</sub> − h<sub>1</sub>) = ṁ<sub>w</sub>(h<sub>w2</sub> − h<sub>w1</sub>)", qr="condins",
                         p="Apply the steady-flow first law to the whole condenser (steam and river water inside). Cross out every term that drops."),
             props([("h<sub>1</sub> = h<sub>f</sub>", h1, "kJ/kg", "A-5", 0.003, fP(Pc)), ("v<sub>1</sub> = v<sub>f</sub>", st1["vf"], "m³/kg", "A-5", 0.003, fP(Pc)),
                    ("h<sub>3</sub>", s3["h"], "kJ/kg", "A-6", 0.003, f"{fP(P3)} block, {fT(T3)} row"), ("s<sub>3</sub>", s3["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P3)} block, {fT(T3)} row"),
                    ("h<sub>fg</sub> at P<sub>c</sub>", stc["hfg"], "kJ/kg", "A-5", 0.003, fP(Pc)), ("s<sub>f</sub> at P<sub>c</sub>", stc["sf"], "kJ/kg·K", "A-5", 0.003, fP(Pc)),
                    ("s<sub>fg</sub> at P<sub>c</sub>", stc["sfg"], "kJ/kg·K", "A-5", 0.003, fP(Pc)),
                    ("h<sub>w1</sub> = h<sub>f</sub>", w1["hf"], "kJ/kg", "A-4", 0.003, fT(Tw1)), ("h<sub>w2</sub> = h<sub>f</sub>", w2["hf"], "kJ/kg", "A-4", 0.003, fT(Tw2))]),
             calc([f"w<sub>p</sub> = ({st1['vf']})({P3} − {Pc:g})/{eP} = {sg(wp)} kJ/kg; h<sub>2</sub> = {sg(h2, 5)} kJ/kg",
                   f"x<sub>4s</sub> = ({num(s3['s'], 4)} − {num(stc['sf'], 4)})/{num(stc['sfg'], 4)} = {sg(x4s, 4)}; h<sub>4s</sub> = {sg(h4s, 5)} kJ/kg",
                   f"h<sub>4</sub> = {num(s3['h'], 1)} − {eT}({num(s3['h'], 1)} − {sg(h4s, 5)}) = {sg(h4, 5)} kJ/kg; x<sub>4</sub> = <b>{sg(x4, 4)}</b>",
                   f"w<sub>net</sub> = ({num(s3['h'], 1)} − {sg(h4, 5)}) − {sg(wp)} = {sg(wn)} kJ/kg; q<sub>in</sub> = {sg(qin)} kJ/kg; η<sub>th</sub> = <b>{pct(eta):.1f}%</b>",
                   f"ṁ = {Wmw * 1000}/{sg(wn)} = <b>{sg(m)} kg/s</b>",
                   f"Q̇<sub>out</sub> = ṁ(h<sub>4</sub> − h<sub>1</sub>) = {sg(QL)} kW; ṁ<sub>w</sub> = {sg(QL)}/({num(w2['hf'], 2)} − {num(w1['hf'], 2)}) = <b>{sg(mw)} kg/s</b>"]),
             mc(8, f"The river carries about {sg(QL / (Wmw * 1000), 2)} kW of waste heat for every kW the plant sells. Is that reasonable?",
                ["Yes: with η near a third, roughly two kW are rejected for every one produced, and a real plant's river or cooling-tower water flows are this large",
                 "No: waste heat should be smaller than the power", "No: a real plant rejects no heat", "Yes, but only for ideal pumps"],
                0, "Kelvin-Planck: a heat engine must reject heat. That is why thermal plants sit on rivers and why permits cap how warm the river may get downstream.")]
    return stem, parts, steps, ctx, prm(locals())

# =================================================================== F3: ideal regenerative Rankine with one open FWH
@ftemplate("F3", "Regenerative Rankine with an open feedwater heater", 10, "R", 24, "challenge")
def F3(rng):
    Pb = rng.choice([4000, 6000, 8000, 10000, 12500, 15000]); T5 = rng.choice([t for t in W.SH[Pb] if 450 <= t <= 600]); Pf = rng.choice([400, 600, 800, 1000, 1200]); Pc = rng.choice([10, 15, 20])
    s5 = W.sh(Pb, T5); stc, wp1 = pump(Pc, Pf); h1 = stc["hf"]; h2 = h1 + wp1
    stf, wp2 = pump(Pf, Pb); h3 = stf["hf"]; h4 = h3 + wp2
    h6, how6, wet6 = at_Ps(Pf, s5["s"]); x7, h7, _ = dome_x(Pc, s5["s"]); assert x7 < 0.95
    y = (h3 - h2) / (h6 - h2); qin = s5["h"] - h4; wt = (s5["h"] - h6) + (1 - y) * (h6 - h7); wp = (1 - y) * wp1 + wp2; wn = wt - wp; eta = wn / qin
    wps = stc["vf"] * (Pb - Pc); eta_s = ((s5["h"] - h7) - wps) / (s5["h"] - (h1 + wps))
    stem = (f"An ideal regenerative Rankine cycle has one open feedwater heater. Steam enters the turbine at {fP(Pb)} and {fT(T5)}. Some steam is bled from the turbine at {fP(Pf)} into the open feedwater heater, "
            f"and the rest expands to the condenser at {fP(Pc)}. Water leaves the condenser and the feedwater heater as saturated liquid. Determine (a) the fraction of steam bled, (b) the heat added per kilogram "
            "of steam in the boiler, (c) the net work per kilogram of steam in the boiler, and (d) the thermal efficiency.")
    parts = [part("a", "Fraction bled, y", "", y, 0.01, 6, [((h3 - h1) / (h6 - h1), "The condensate enters the heater after the low-pressure pump, at h<sub>2</sub>, not h<sub>1</sub>."), ((h6 - h3) / (h6 - h2), "Upside down: y(h<sub>6</sub> − h<sub>3</sub>) = (1 − y)(h<sub>3</sub> − h<sub>2</sub>) gives y = (h<sub>3</sub> − h<sub>2</sub>)/(h<sub>6</sub> − h<sub>2</sub>).")]),
             part("b", "q<sub>in</sub>", "kJ/kg", qin, 0.005, 5, [(s5["h"] - h3, "The boiler receives water after the high-pressure pump, at h<sub>4</sub>.")]),
             part("c", "w<sub>net</sub>", "kJ/kg", wn, 0.01, 7, [((s5["h"] - h7) - wp1 - wp2, "Only (1 − y) of the steam expands all the way to the condenser, and only (1 − y) goes through the low-pressure pump."),
                                                             (wt, "Subtract both pumps' work.")]),
             part("d", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.008, 6, [(pct(eta_s), "That's the simple Rankine cycle without the heater.")])]
    steps = [self_step("Find the bled fraction, heat in, net work and efficiency of an ideal Rankine cycle with one open feedwater heater. Plan: number the seven states, fix each, then let the heater's energy balance set y; everything per kg of steam through the boiler."),
             mc(2, "Where does the open feedwater heater sit, and what does it do?",
                ["Between the two pumps: bled steam at state 6 mixes with the pumped condensate at 2, and saturated liquid at 3 leaves to the high-pressure pump",
                 "After the boiler, to superheat the steam", "Between the turbine and condenser", "It replaces the condenser"],
                0, "The heater is a mixing chamber. Bled steam preheats the feedwater, so the boiler adds less heat at low temperature, which raises the average temperature of heat addition."),
             rk_assume([f"Turbine in: {fP(Pb)}, {fT(T5)}", f"Bleed: {fP(Pf)}", f"Condenser: {fP(Pc)}", "Ideal cycle"], ["y", "q<sub>in</sub> (kJ/kg)", "w<sub>net</sub> (kJ/kg)", "η<sub>th</sub> (%)"],
                       [("fwhsat", True, "Given."), ("isen", True, "Ideal cycle: s<sub>6</sub> = s<sub>7</sub> = s<sub>5</sub>, and the pumps are isentropic.", "Ideal cycle: turbines and pumps are isentropic.")], real=False),
             multi([("FWH: yh<sub>6</sub> + (1 − y)h<sub>2</sub> = h<sub>3</sub>", True, ""), ("q<sub>in</sub> = h<sub>5</sub> − h<sub>4</sub>", True, ""),
                    ("w<sub>T</sub> = (h<sub>5</sub> − h<sub>6</sub>) + (1 − y)(h<sub>6</sub> − h<sub>7</sub>)", True, ""), ("w<sub>p</sub> = (1 − y)v<sub>1</sub>(P<sub>f</sub> − P<sub>c</sub>) + v<sub>3</sub>(P<sub>b</sub> − P<sub>f</sub>)", True, ""),
                    (FIRST_SF, True, ""), ("y = (h<sub>3</sub> − h<sub>2</sub>)/(h<sub>6</sub> − h<sub>3</sub>)", False, "The denominator is h<sub>6</sub> − h<sub>2</sub>.")], FIRST_SF),
             multi_terms(["yh<sub>6</sub>", "(1 − y)h<sub>2</sub>"], ["h<sub>3</sub>"], "FWH, per kg through the boiler: yh<sub>6</sub> + (1 − y)h<sub>2</sub> = h<sub>3</sub>", qr="fwhsat",
                         p="Apply the steady-flow first law to the open feedwater heater (per kg of steam through the boiler). Cross out every term that drops."),
             props([("h<sub>1</sub>, v<sub>1</sub> at P<sub>c</sub>: h<sub>f</sub>", h1, "kJ/kg", "A-5", 0.003, fP(Pc)), ("v<sub>f</sub> at P<sub>c</sub>", stc["vf"], "m³/kg", "A-5", 0.003, fP(Pc)),
                    ("h<sub>3</sub> = h<sub>f</sub> at P<sub>f</sub>", h3, "kJ/kg", "A-5", 0.003, fP(Pf)), ("v<sub>3</sub> = v<sub>f</sub> at P<sub>f</sub>", stf["vf"], "m³/kg", "A-5", 0.003, fP(Pf)),
                    ("h<sub>5</sub>", s5["h"], "kJ/kg", "A-6", 0.003, f"{fP(Pb)} block, {fT(T5)} row"), ("s<sub>5</sub>", s5["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(Pb)} block, {fT(T5)} row"),
                    ("h<sub>6</sub> (s = s<sub>5</sub>)", h6, "kJ/kg", "A-5" if wet6 else "A-6", 0.004, fP(Pf)), ("h<sub>7</sub> (s = s<sub>5</sub>)", h7, "kJ/kg", "A-5", 0.004, fP(Pc))]),
             calc([f"Low-pressure pump: w<sub>p1</sub> = ({stc['vf']})({Pf} − {Pc}) = {sg(wp1, 3)} kJ/kg; h<sub>2</sub> = {sg(h2, 5)} kJ/kg",
                   f"High-pressure pump: w<sub>p2</sub> = ({stf['vf']})({Pb} − {Pf}) = {sg(wp2)} kJ/kg; h<sub>4</sub> = {num(h3, 2)} + {sg(wp2)} = {sg(h4, 5)} kJ/kg",
                   f"Bleed state 6: {how6}; h<sub>6</sub> = {sg(h6, 5)} kJ/kg. Condenser inlet: x<sub>7</sub> = {sg(x7, 4)}, h<sub>7</sub> = {sg(h7, 5)} kJ/kg",
                   f"y = (h<sub>3</sub> − h<sub>2</sub>)/(h<sub>6</sub> − h<sub>2</sub>) = ({num(h3, 2)} − {sg(h2, 5)})/({sg(h6, 5)} − {sg(h2, 5)}) = <b>{sg(y, 4)}</b>",
                   f"q<sub>in</sub> = h<sub>5</sub> − h<sub>4</sub> = <b>{sg(qin)} kJ/kg</b>",
                   f"w<sub>T</sub> = ({num(s5['h'], 1)} − {sg(h6, 5)}) + (1 − {sg(y, 4)})({sg(h6, 5)} − {sg(h7, 5)}) = {sg(wt)}; w<sub>p</sub> = {sg(wp)}; w<sub>net</sub> = <b>{sg(wn)} kJ/kg</b>",
                   f"η<sub>th</sub> = {sg(wn)}/{sg(qin)} = <b>{pct(eta):.1f}%</b> (simple Rankine, same pressures: {pct(eta_s):.1f}%)"]),
             mc(8, "The heater lowers the net work per kilogram but raises the efficiency. How can both be true?",
                ["Bled steam makes less work, but it saves even more boiler heat, all of it added at the lowest temperatures; heat added cold is what drags the efficiency down",
                 "It can't; one of the numbers is wrong", "The pumps do less work", "The condenser pressure drops"],
                0, "Regeneration raises the average temperature at which heat enters the cycle, which moves the cycle toward Carnot. Plants make up the lost work per kilogram with a little more steam flow.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== F4: cogeneration with a process heater
@ftemplate("F4", "Cogeneration: power plus process steam for a campus", 10, "R", 24, "challenge")
def F4(rng):
    Pb = rng.choice([4000, 5000, 6000, 7000, 8000]); T5 = rng.choice([t for t in W.SH[Pb] if 400 <= t <= 550]); Pp = rng.choice([400, 500, 600, 800]); Pc = rng.choice([10, 15, 20])
    m = rng.choice([10, 15, 20, 25, 30]); Qp = rng.choice([5000, 8000, 10000, 12000, 15000, 20000])
    s5 = W.sh(Pb, T5); h6, how6, wet6 = at_Ps(Pp, s5["s"]); x7, h7, stc = dome_x(Pc, s5["s"])
    stp = W.satP(Pp); mp = Qp / (h6 - stp["hf"]); assert 0.15 * m < mp < 0.85 * m
    mc_ = m - mp; wpc = stc["vf"] * (Pb - Pc); wpp = stp["vf"] * (Pb - Pp)
    h2a = stc["hf"] + wpc; h2b = stp["hf"] + wpp; h4 = (mc_ * h2a + mp * h2b) / m
    Wt = m * (s5["h"] - h6) + mc_ * (h6 - h7); Wp = mc_ * wpc + mp * wpp; Wn = Wt - Wp; Qin = m * (s5["h"] - h4); eu = (Wn + Qp) / Qin
    stem = (f"A campus cogeneration plant runs on an ideal Rankine cycle with {m} kg/s of steam entering the turbine at {fP(Pb)} and {fT(T5)}. Part of the steam is extracted at {fP(Pp)} to supply "
            f"{Qp / 1000:g} MW of process heat for heating and sterilization; it leaves the process heater as saturated liquid and is pumped back to the boiler pressure. The rest expands to the condenser at {fP(Pc)}, "
            "leaves as saturated liquid and is pumped to the boiler pressure. The two pumped streams mix before the boiler. Determine (a) the extracted mass flow rate, (b) the net power, "
            "(c) the boiler heat input, and (d) the utilization factor.")
    parts = [part("a", "Extracted flow, ṁ<sub>p</sub>", "kg/s", mp, 0.01, 6, [(Qp / (h6 - stc["hf"]), "The process heater's water leaves as saturated liquid at the process pressure, not the condenser pressure."),
                                                                         (Qp / stp["hfg"], "The extracted steam isn't saturated vapor; use the turbine's h<sub>6</sub> at the extraction pressure.")]),
             part("b", "Net power, Ẇ<sub>net</sub>", "kW", Wn, 0.01, 6, [(m * (s5["h"] - h7) - Wp, "Only the condenser stream expands all the way to state 7."), (Wt, "Subtract both pumps.")]),
             part("c", "Boiler heat, Q̇<sub>in</sub>", "kW", Qin, 0.006, 6, [(m * (s5["h"] - h2a), "The boiler receives the mixed feedwater, h<sub>4</sub> = (ṁ<sub>c</sub>h<sub>2a</sub> + ṁ<sub>p</sub>h<sub>2b</sub>)/ṁ.")]),
             part("d", "Utilization factor, ε<sub>u</sub>", "%", pct(eu), 0.01, 6, [(pct(Wn / Qin), "That's the electrical efficiency. Utilization counts the process heat as useful too: (Ẇ<sub>net</sub> + Q̇<sub>p</sub>)/Q̇<sub>in</sub>.")])]
    steps = [self_step("Find the extracted steam, net power, boiler heat and utilization factor of a cogeneration plant. Plan: the process heat fixes ṁ<sub>p</sub>; then turbine, pumps and mixing chamber in turn; utilization counts both useful outputs."),
             mc(2, "Sketch the plant. Which description is right?",
                ["Boiler → turbine; at P<sub>p</sub> part of the steam leaves the turbine for the process heater; the rest goes on to the condenser; two pumps; the streams mix before the boiler",
                 "All the steam goes through the process heater, then the turbine", "The process heater replaces the boiler", "The extracted steam goes to the condenser"],
                0, "Cogeneration uses the steam's lower-temperature energy for heating instead of dumping it into a river, which is why its utilization is far above its electrical efficiency."),
             rk_assume([f"ṁ = {m} kg/s, {fP(Pb)}, {fT(T5)}", f"Extraction: {fP(Pp)}, Q̇<sub>p</sub> = {Qp / 1000:g} MW", f"Condenser: {fP(Pc)}", "Ideal turbine and pumps"],
                       ["ṁ<sub>p</sub> (kg/s)", "Ẇ<sub>net</sub> (kW)", "Q̇<sub>in</sub> (kW)", "ε<sub>u</sub> (%)"],
                       [("procsat", True, "Given."), ("isen", True, "Ideal turbine and pumps.", "The turbine and pumps are isentropic.")], real=False),
             multi([("Q̇<sub>p</sub> = ṁ<sub>p</sub>(h<sub>6</sub> − h<sub>f@Pp</sub>)", True, ""), ("Ẇ<sub>T</sub> = ṁ(h<sub>5</sub> − h<sub>6</sub>) + (ṁ − ṁ<sub>p</sub>)(h<sub>6</sub> − h<sub>7</sub>)", True, ""),
                    ("Mixing: ṁh<sub>4</sub> = ṁ<sub>c</sub>h<sub>2a</sub> + ṁ<sub>p</sub>h<sub>2b</sub>", True, ""), ("ε<sub>u</sub> = (Ẇ<sub>net</sub> + Q̇<sub>p</sub>)/Q̇<sub>in</sub>", True, ""), (FIRST_SF, True, ""),
                    ("ε<sub>u</sub> = Ẇ<sub>net</sub>/Q̇<sub>in</sub>", False, "That's the electrical efficiency only.")], FIRST_SF),
             sf_single({"Win": (["dir"], "Heat leaves the steam; no work."), "Wout": (["noshaft"], "No shaft."), "Qin": (["dir"], "Heat leaves the steam."),
                        "mke1": (["lowke"], "Small KE."), "mke2": (["lowke"], "Small KE."), "mpe1": (["nope"], "Small PE."), "mpe2": (["nope"], "Small PE."), "dE": (["steady"], "Steady.")},
                       "Process heater: Q̇<sub>p</sub> = ṁ<sub>p</sub>(h<sub>6</sub> − h<sub>f@Pp</sub>)", p="Apply the steady-flow first law to the process heater (steam side). Cross out every term that drops."),
             props([("h<sub>5</sub>", s5["h"], "kJ/kg", "A-6", 0.003, f"{fP(Pb)} block, {fT(T5)} row"), ("s<sub>5</sub>", s5["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(Pb)} block, {fT(T5)} row"),
                    ("h<sub>6</sub> (s = s<sub>5</sub>)", h6, "kJ/kg", "A-5" if wet6 else "A-6", 0.004, fP(Pp)), ("h<sub>7</sub> (s = s<sub>5</sub>)", h7, "kJ/kg", "A-5", 0.004, fP(Pc)),
                    ("h<sub>f</sub> at P<sub>p</sub>", stp["hf"], "kJ/kg", "A-5", 0.003, fP(Pp)), ("v<sub>f</sub> at P<sub>p</sub>", stp["vf"], "m³/kg", "A-5", 0.003, fP(Pp)),
                    ("h<sub>f</sub> at P<sub>c</sub>", stc["hf"], "kJ/kg", "A-5", 0.003, fP(Pc)), ("v<sub>f</sub> at P<sub>c</sub>", stc["vf"], "m³/kg", "A-5", 0.003, fP(Pc))]),
             calc([f"Extraction state: {how6}; h<sub>6</sub> = {sg(h6, 5)} kJ/kg. Condenser inlet: h<sub>7</sub> = {sg(h7, 5)} kJ/kg (x = {sg(x7, 3)})",
                   f"ṁ<sub>p</sub> = Q̇<sub>p</sub>/(h<sub>6</sub> − h<sub>f@Pp</sub>) = {Qp}/({sg(h6, 5)} − {num(stp['hf'], 2)}) = <b>{sg(mp)} kg/s</b>; ṁ<sub>c</sub> = {sg(mc_)} kg/s",
                   f"Pumps: w<sub>pc</sub> = {sg(wpc)} kJ/kg, w<sub>pp</sub> = {sg(wpp)} kJ/kg; h<sub>2a</sub> = {sg(h2a, 5)}, h<sub>2b</sub> = {sg(h2b, 5)} kJ/kg",
                   f"Ẇ<sub>T</sub> = {m}({num(s5['h'], 1)} − {sg(h6, 5)}) + {sg(mc_)}({sg(h6, 5)} − {sg(h7, 5)}) = {sg(Wt)} kW; Ẇ<sub>p</sub> = {sg(Wp, 3)} kW; Ẇ<sub>net</sub> = <b>{sg(Wn)} kW</b>",
                   f"h<sub>4</sub> = ({sg(mc_)}·{sg(h2a, 5)} + {sg(mp)}·{sg(h2b, 5)})/{m} = {sg(h4, 5)} kJ/kg; Q̇<sub>in</sub> = {m}({num(s5['h'], 1)} − {sg(h4, 5)}) = <b>{sg(Qin)} kW</b>",
                   f"ε<sub>u</sub> = ({sg(Wn)} + {Qp})/{sg(Qin)} = <b>{pct(eu):.1f}%</b> (electrical efficiency alone: {pct(Wn / Qin):.1f}%)"]),
             mc(8, "Why isn't ε<sub>u</sub> 100% for this ideal plant?",
                ["The condenser still throws away the heat from the steam that didn't go to the process; only an all-process plant (no condenser) would use everything",
                 "Because the pumps are inefficient", "It should be 100% for any ideal plant", "Because of the mixing chamber"],
                0, "Campuses, hospitals and factories use cogeneration because they need heat anyway. The utilization factor rewards using the heat; the second law still caps how much of it could have been work.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== F5: combined gas-steam cycle
@ftemplate("F5", "Combined gas-steam power plant", 10, "R", 26, "hardest")
def F5(rng):
    rp = rng.choice([8, 10, 12, 14]); T1 = rng.choice([290, 300]); T3 = rng.choice([1300, 1400, 1500]); Tst = rng.choice([400, 420, 450, 480])
    Pb = rng.choice([4000, 6000, 8000, 10000]); Ts = rng.choice([t for t in W.SH[Pb] if 400 <= t <= 550]); Pc = rng.choice([7.5, 10, 15]); Wmw = rng.choice([200, 300, 450, 600])
    T2 = T1 * rp ** E; T4 = T3 / rp ** E; assert T4 - 273.15 > Ts + 25 and T4 > Tst + 200
    wg = CPA * ((T3 - T4) - (T2 - T1)); qin = CPA * (T3 - T2)
    s3 = W.sh(Pb, Ts); st1, wp = pump(Pc, Pb); h2 = st1["hf"] + wp; x4, h4, stc = dome_x(Pc, s3["s"]); assert x4 < 0.95
    ws = (s3["h"] - h4) - wp; y = CPA * (T4 - Tst) / (s3["h"] - h2)   # kg steam per kg air
    wtot = wg + y * ws; eta = wtot / qin; ma = Wmw * 1000 / wtot
    stem = (f"A combined-cycle plant runs an ideal gas-turbine (Brayton) cycle on air with a pressure ratio of {rp}, compressor inlet at {T1} K and turbine inlet at {T3} K. The turbine exhaust passes through a heat recovery "
            f"steam generator and leaves to the stack at {Tst} K. The steam runs an ideal Rankine cycle: {fP(Pb)} and {fT(Ts)} at the turbine inlet, condenser at {fP(Pc)}. The plant makes {Wmw} MW. "
            "Using cold-air-standard assumptions for the gas cycle, determine (a) the gas-turbine exhaust temperature, (b) the kilograms of steam per kilogram of air, (c) the combined thermal efficiency, "
            "and (d) the air mass flow rate.")
    parts = [part("a", "Gas turbine exhaust, T<sub>4</sub>", "K", T4, 0.005, 5, [(T3 / rp ** 0.4, "With pressure ratios, use (k − 1)/k = 0.286.")]),
             part("b", "Steam per kg of air, ṁ<sub>s</sub>/ṁ<sub>a</sub>", "", y, 0.01, 7, [(CPA * (T4 - T1) / (s3["h"] - h2), "The gas leaves the HRSG at the stack temperature, not T<sub>1</sub>."),
                                                                                         ((s3["h"] - h2) / (CPA * (T4 - Tst)), "Upside down: ṁ<sub>s</sub>/ṁ<sub>a</sub> = c<sub>p</sub>(T<sub>4</sub> − T<sub>stack</sub>)/(h<sub>3</sub> − h<sub>2</sub>).")]),
             part("c", "Combined efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 8, [(pct(wg / qin), "That's the gas cycle alone. Add the steam cycle's work, which costs no extra fuel."),
                                                                                    (pct(ws / (s3["h"] - h2)), "That's the steam cycle alone."), (pct((wg + ws) / qin), "Weight the steam work by ṁ<sub>s</sub>/ṁ<sub>a</sub>.")]),
             part("d", "Air mass flow, ṁ<sub>a</sub>", "kg/s", ma, 0.012, 6, [(Wmw * 1000 / wg, "The steam cycle makes part of the power: divide by w<sub>gas</sub> + (ṁ<sub>s</sub>/ṁ<sub>a</sub>)w<sub>steam</sub>.")])]
    steps = [self_step("Find the gas-turbine exhaust temperature, the steam-to-air ratio, the combined efficiency and the air flow of a combined-cycle plant. Plan: gas cycle temperatures first; the HRSG energy balance links the two cycles; all heat comes in at the gas combustor."),
             mc(2, "How are the two cycles connected?",
                ["The gas turbine's hot exhaust is the steam cycle's boiler (the HRSG); the only fuel burns in the gas cycle's combustor",
                 "The steam turbine drives the gas compressor", "The steam cycle burns its own fuel, and the gas cycle uses the steam's waste heat", "They share a condenser"],
                0, "The gas cycle rejects heat at several hundred kelvins, hot enough to boil water at high pressure. Using it is why combined cycles reach 55–60% in real plants."),
             assume([f"Gas: r<sub>p</sub> = {rp}, T<sub>1</sub> = {T1} K, T<sub>3</sub> = {T3} K", f"Stack: {Tst} K", f"Steam: {fP(Pb)}, {fT(Ts)}; condenser {fP(Pc)}", f"Ẇ = {Wmw} MW"],
                    ["T<sub>4</sub> (K)", "ṁ<sub>s</sub>/ṁ<sub>a</sub>", "η<sub>th</sub> (%)", "ṁ<sub>a</sub> (kg/s)"],
                    [("open", True, "Every device is a control volume."), ("steady", True, "Steady operation."), ("coldair", True, "Given, for the gas cycle (rule 4)."), ("steam", True, "Rule 1: steam tables for the steam cycle."),
                     ("isen", True, "Both cycles are ideal.", "Compressor, gas turbine, pump and steam turbine are isentropic."), ("hrsg", True, "Given."), ("noshaft", True, "The HRSG has no shaft or wires.", "The HRSG has no shaft or wires."), ("lowke", True, "Small KE changes."), ("nope", True, "Same height."),
                     ("condsat", True, "Standard."), ("pumpliq", True, "Liquid in the pump."), ("steamideal", False, "Steam uses its tables.")]),
             multi([("T<sub>2</sub> = T<sub>1</sub>r<sub>p</sub><sup>(k−1)/k</sup>; T<sub>4</sub> = T<sub>3</sub>/r<sub>p</sub><sup>(k−1)/k</sup>", True, ""),
                    ("HRSG: ṁ<sub>a</sub>c<sub>p</sub>(T<sub>4</sub> − T<sub>stack</sub>) = ṁ<sub>s</sub>(h<sub>3</sub> − h<sub>2</sub>)", True, ""),
                    ("η = [w<sub>gas</sub> + (ṁ<sub>s</sub>/ṁ<sub>a</sub>)w<sub>steam</sub>]/c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)", True, ""), (FIRST_SF, True, ""),
                    ("η = η<sub>gas</sub> + η<sub>steam</sub>", False, "Efficiencies don't add; the steam cycle's heat is the gas cycle's waste, not new fuel.")], FIRST_SF),
             multi_terms(["ṁ<sub>a</sub>h<sub>4</sub>", "ṁ<sub>s</sub>h<sub>2</sub>"], ["ṁ<sub>a</sub>h<sub>stack</sub>", "ṁ<sub>s</sub>h<sub>3</sub>"], "HRSG: ṁ<sub>a</sub>c<sub>p</sub>(T<sub>4</sub> − T<sub>stack</sub>) = ṁ<sub>s</sub>(h<sub>3</sub> − h<sub>2</sub>)",
                         qr="hrsg", p="Apply the steady-flow first law to the whole HRSG (gas and steam inside). Cross out every term that drops."),
             props([("c<sub>p</sub> for air", CPA, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("h<sub>1</sub> = h<sub>f</sub>", st1["hf"], "kJ/kg", "A-5", 0.003, fP(Pc)), ("v<sub>f</sub>", st1["vf"], "m³/kg", "A-5", 0.003, fP(Pc)),
                    ("h<sub>3</sub>", s3["h"], "kJ/kg", "A-6", 0.003, f"{fP(Pb)} block, {fT(Ts)} row"), ("s<sub>3</sub>", s3["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(Pb)} block, {fT(Ts)} row"),
                    ("h<sub>4</sub> steam (s = s<sub>3</sub>)", h4, "kJ/kg", "A-5", 0.004, fP(Pc))]),
             calc([f"Gas: T<sub>2</sub> = {T1}({rp})<sup>0.2857</sup> = {sg(T2)} K; T<sub>4</sub> = {T3}/{rp}<sup>0.2857</sup> = <b>{sg(T4)} K</b>",
                   f"w<sub>gas</sub> = 1.005[({T3} − {sg(T4)}) − ({sg(T2)} − {T1})] = {sg(wg)} kJ/kg air; q<sub>in</sub> = 1.005({T3} − {sg(T2)}) = {sg(qin)} kJ/kg air",
                   f"Steam: w<sub>p</sub> = {sg(wp)}; h<sub>2</sub> = {sg(h2, 5)}; h<sub>4</sub> = {sg(h4, 5)} kJ/kg (x = {sg(x4, 3)}); w<sub>steam</sub> = {sg(ws)} kJ/kg steam",
                   f"ṁ<sub>s</sub>/ṁ<sub>a</sub> = 1.005({sg(T4)} − {Tst})/({num(s3['h'], 1)} − {sg(h2, 5)}) = <b>{sg(y, 4)}</b>",
                   f"w per kg air = {sg(wg)} + ({sg(y, 4)})({sg(ws)}) = {sg(wtot)} kJ/kg; η<sub>th</sub> = {sg(wtot)}/{sg(qin)} = <b>{pct(eta):.1f}%</b> (gas alone {pct(wg / qin):.1f}%)",
                   f"ṁ<sub>a</sub> = {Wmw * 1000}/{sg(wtot)} = <b>{sg(ma)} kg/s</b>"]),
             mc(8, "Why can't you drop the stack temperature to T<sub>1</sub> and make even more steam?",
                ["The steam leaving the economizer and boiling at high pressure is far hotter than T<sub>1</sub>; the gas can only cool to a bit above the water it's heating, and cooled exhaust can condense acid in the stack",
                 "You could; it's just not done", "The first law forbids it", "Because the gas turbine is isentropic"],
                0, "Heat flows only from hot to cold. The HRSG's pinch, where gas and water temperatures come closest, limits how much steam the exhaust can make.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== F6: Stirling engine (makerspace build tie-in)
GASES_ST = {"air": (0.2870, 0.718), "helium": (2.0769, 3.1156), "hydrogen": (4.124, 10.183)}
@ftemplate("F6", "Ideal Stirling engine, with and without its regenerator", 9, "S", 20, "challenge")
def F6(rng):
    gas = rng.choice(list(GASES_ST)); R_, cv_ = GASES_ST[gas]
    TH = rng.choice([500, 600, 700, 800, 900]); TL = rng.choice([290, 300, 320, 350]); r = rng.choice([2, 2.5, 3, 4, 5])
    m = rng.choice([0.001, 0.002, 0.005, 0.01, 0.02]) * (1 if gas == "air" else 0.2); rpm = rng.choice([300, 600, 900, 1200, 1500])
    Qin = m * R_ * TH * math.log(r); W_ = m * R_ * (TH - TL) * math.log(r); Wdot = W_ * rpm / 60; eta = 1 - TL / TH
    Qreg = m * cv_ * (TH - TL); eta_nr = W_ / (Qin + Qreg)
    stem = (f"An ideal Stirling engine holds {m:g} kg of {gas}. It runs between {TH} K and {TL} K with a maximum-to-minimum volume ratio of {r:g}, and completes one cycle per revolution at {rpm} rpm. "
            f"Determine (a) the heat added per cycle at {TH} K, (b) the net work per cycle, (c) the power output, and (d) the thermal efficiency if the engine had no regenerator, "
            "so that the heat for the constant-volume warming also had to come from the hot source.")
    parts = [part("a", "Heat in per cycle, Q<sub>H</sub>", "kJ", Qin, 0.01, 5, [(m * R_ * TH * r, "Isothermal expansion: Q = mRT ln(V<sub>max</sub>/V<sub>min</sub>), with a logarithm."), (Qin + Qreg, "With an ideal regenerator, the constant-volume heating comes from the regenerator, not the source.")]),
             part("b", "Net work per cycle, W<sub>net</sub>", "kJ", W_, 0.01, 5, [(Qin, "That's the heat in. The engine rejects mRT<sub>L</sub> ln r at the cold side.")]),
             part("c", "Power, Ẇ", "kW", Wdot, 0.01, 4, [(W_ * rpm, "rpm is per minute: divide by 60.")]),
             part("d", "Efficiency without a regenerator", "%", pct(eta_nr), 0.01, 6, [(pct(eta), "That's with an ideal regenerator, which equals Carnot. Without it, add mc<sub>v</sub>(T<sub>H</sub> − T<sub>L</sub>) to the heat input."),
                                                                                   (pct(W_ / (Qin + m * (cv_ + R_) * (TH - TL))), "The regenerator steps are at constant volume: use c<sub>v</sub>.")])]
    steps = [self_step("Find the heat in, work, power and no-regenerator efficiency of an ideal Stirling engine. Plan: each process is simple on its own: two isotherms (Q = W = mRT ln r) and two constant-volume steps the regenerator handles."),
             mc(2, "Sketch the Stirling cycle on P-v and T-s. Which is right?",
                ["Two isotherms (T<sub>H</sub> and T<sub>L</sub>) joined by two constant-volume lines; on T-s, two horizontal lines joined by two curves that the regenerator connects",
                 "Two isentropes and two constant-volume lines (that's Otto)", "Two isotherms and two isentropes (that's Carnot)", "Two isotherms and two constant-pressure lines (that's Ericsson)"],
                0, "Swap Carnot's isentropes for constant-volume steps, then let a regenerator store the heat from one constant-volume step and give it back in the other. All outside heat then crosses at T<sub>H</sub> and T<sub>L</sub>, so the efficiency equals Carnot."),
             cyc_assume([f"{m:g} kg of {gas}", f"T<sub>H</sub> = {TH} K, T<sub>L</sub> = {TL} K", f"V<sub>max</sub>/V<sub>min</sub> = {r:g}", f"{rpm} rpm, one cycle per revolution"],
                        ["Q<sub>H</sub> (kJ)", "W<sub>net</sub> (kJ)", "Ẇ (kW)", "η<sub>no regen</sub> (%)"],
                        [("ideal", True, f"{gas.capitalize()} far from its critical point: Z ≈ 1."), ("intrev", True, "Ideal cycle."), ("isoT", True, "Ideal Stirling."), ("regenI", True, "For parts (a) to (c)."),
                         ("stationary", True, "Standard for cycles."), ("coldair", False, "The working gas is given; use its own R and c<sub>v</sub> (A-2a)."), ("constP", False, "Stirling's regeneration is at constant volume.")]),
             multi([("Isothermal: Q = W = mRT ln(V<sub>2</sub>/V<sub>1</sub>)", True, ""), ("W<sub>net</sub> = mR(T<sub>H</sub> − T<sub>L</sub>) ln r", True, ""), ("Constant volume: Q = mc<sub>v</sub>ΔT", True, ""),
                    ("η<sub>Stirling</sub> = 1 − T<sub>L</sub>/T<sub>H</sub> with an ideal regenerator", True, ""), (FIRST_CL, True, ""), ("Q = mc<sub>p</sub>ΔT for the regenerator steps", False, "Stirling's regeneration is at constant volume.")], FIRST_CL),
             strike_closed({"Qout": (["dir"], "Heat comes in during the hot expansion."), "Win": (["dir"], "The gas expands: work goes out."), "dU": (["isoT"], "Ideal gas at constant T: ΔU = 0."),
                            "dKE": (["stationary"], "Doesn't move."), "dPE": (["stationary"], "Doesn't move.")}, "Isothermal expansion at T<sub>H</sub>: Q<sub>in</sub> = W<sub>out</sub> = mRT<sub>H</sub> ln r",
                           p="Apply the first law to the isothermal expansion at T<sub>H</sub>. Cross out every term that drops."),
             props([(f"R for {gas}", R_, "kJ/kg·K", "A-1", 0.003, gas), (f"c<sub>v</sub> for {gas}", cv_, "kJ/kg·K", "A-2a", 0.003, gas)]),
             calc([f"Q<sub>H</sub> = mRT<sub>H</sub> ln r = ({m:g})({R_})({TH}) ln {r:g} = <b>{sg(Qin)} kJ</b>",
                   f"Q<sub>L</sub> = mRT<sub>L</sub> ln r = {sg(m * R_ * TL * math.log(r))} kJ; W<sub>net</sub> = Q<sub>H</sub> − Q<sub>L</sub> = <b>{sg(W_)} kJ</b>",
                   f"Ẇ = W<sub>net</sub> × {rpm}/60 = <b>{sg(Wdot)} kW</b>; with the regenerator η = W/Q<sub>H</sub> = {pct(eta):.1f}% = 1 − T<sub>L</sub>/T<sub>H</sub>",
                   f"No regenerator: extra heat mc<sub>v</sub>(T<sub>H</sub> − T<sub>L</sub>) = ({m:g})({cv_})({TH - TL}) = {sg(Qreg)} kJ; η = {sg(W_)}/({sg(Qin)} + {sg(Qreg)}) = <b>{pct(eta_nr):.1f}%</b>"]),
             mc(8, "Your makerspace Stirling engine runs on a candle and an ice cube, with no regenerator worth the name. What does part (d) say about it?",
                ["Without regeneration, most of each cycle's heat just warms and cools the gas, so the efficiency falls far below Carnot; that's why small demonstration engines barely turn",
                 "It should still reach Carnot", "Regenerators only matter for power, not efficiency", "Efficiency rises without a regenerator"],
                0, "The regenerator is the whole trick. Real Stirling engines pack it with fine wire mesh that soaks up heat on one pass and hands it back on the next.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== F7: Ericsson vs Brayton
@ftemplate("F7", "Ideal Ericsson cycle against a Brayton cycle", 9, "S", 20, "challenge")
def F7(rng):
    T1 = rng.choice([290, 300, 310]); TH = rng.choice([1000, 1100, 1200, 1300]); rp = rng.choice([4, 6, 8, 10]); Wmw = rng.choice([1, 2, 5, 10])
    lr = math.log(rp); wc = RA * T1 * lr; wt = RA * TH * lr; wn = wt - wc; eta = 1 - T1 / TH; m = Wmw * 1000 / wn
    etaB = 1 - rp ** -E; wB = CPA * TH * (1 - rp ** -E) - CPA * T1 * (rp ** E - 1)
    stem = (f"An ideal Ericsson cycle uses air as a steady-flow working fluid. The compressor works isothermally at {T1} K and the turbine isothermally at {TH} K, both with a pressure ratio of {rp}, "
            f"and an ideal regenerator transfers heat between the two constant-pressure lines. The plant makes {Wmw} MW. Determine (a) the compressor work per kilogram, (b) the net work per kilogram, "
            f"(c) the air mass flow rate, and (d) the efficiency of an ideal cold-air Brayton cycle with the same pressure ratio (for comparison).")
    parts = [part("a", "Compressor work, w<sub>c</sub>", "kJ/kg", wc, 0.01, 5, [(CPA * T1 * (rp ** E - 1), "That's an isentropic compressor. Isothermal compression: w = RT ln(P<sub>2</sub>/P<sub>1</sub>)."), (RA * T1 * rp, "Use ln r<sub>p</sub>.")]),
             part("b", "Net work, w<sub>net</sub>", "kJ/kg", wn, 0.01, 5, [(wt, "Subtract the compressor work.")]),
             part("c", "Air mass flow, ṁ", "kg/s", m, 0.01, 4, [(Wmw / wn, "MW to kW: multiply by 1000.")]),
             part("d", "Brayton efficiency, same r<sub>p</sub>", "%", pct(etaB), 0.005, 6, [(pct(eta), "That's Ericsson (Carnot). Brayton: η = 1 − 1/r<sub>p</sub><sup>(k−1)/k</sup>."), (pct(1 - rp ** -0.4), "Use (k − 1)/k with pressure ratios.")])]
    steps = [self_step("Find the compressor work, net work and air flow of an ideal Ericsson cycle, and compare its efficiency with a Brayton cycle. Plan: isothermal steady-flow work for each machine; the regenerator covers the constant-pressure heating."),
             mc(2, "On T-s, what does the Ericsson cycle look like?",
                ["Two horizontal lines (isothermal compression at T<sub>L</sub>, expansion at T<sub>H</sub>) joined by two constant-pressure curves that the regenerator connects",
                 "Two vertical lines joined by constant-pressure curves (that's Brayton)", "A rectangle (that's Carnot)", "Two horizontal lines joined by constant-volume curves (that's Stirling)"],
                0, "Ericsson is Brayton with isothermal machines and perfect regeneration. With all outside heat at T<sub>H</sub> and T<sub>L</sub>, its efficiency is Carnot's."),
             assume([f"T<sub>L</sub> = {T1} K, T<sub>H</sub> = {TH} K", f"r<sub>p</sub> = {rp}", f"Ẇ<sub>net</sub> = {Wmw} MW"], ["w<sub>c</sub> (kJ/kg)", "w<sub>net</sub> (kJ/kg)", "ṁ (kg/s)", "η<sub>Brayton</sub> (%)"],
                    [("open", True, "Steady-flow machines."), ("steady", True, "Steady operation."), ("ideal", True, "Air: Z ≈ 1."), ("isoT", True, "Ideal Ericsson."), ("regenI", True, "Given."),
                     ("lowke", True, "Small KE changes."), ("nope", True, "Same height."), ("coldair", True, "Only for the Brayton comparison in (d).", "For the Brayton comparison only: cold-air-standard, k = 1.4."),
                     ("isen", False, "Ericsson's compressor and turbine are isothermal, not isentropic.")]),
             multi([("Isothermal steady flow, ideal gas: w = RT ln(P<sub>high</sub>/P<sub>low</sub>)", True, ""), ("w<sub>net</sub> = R(T<sub>H</sub> − T<sub>L</sub>) ln r<sub>p</sub>; η = 1 − T<sub>L</sub>/T<sub>H</sub>", True, ""),
                    ("η<sub>Brayton</sub> = 1 − 1/r<sub>p</sub><sup>(k−1)/k</sup>", True, ""), (FIRST_SF, True, ""), ("w<sub>c</sub> = c<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>)", False, "Isothermal: T<sub>2</sub> = T<sub>1</sub>, yet work is done; the heat removed balances it.")], FIRST_SF),
             sf_single({"Qin": (["dir"], "Heat leaves during isothermal compression."), "Wout": (["dir"], "Work goes in."), "mke1": (["lowke"], "Small KE."), "mke2": (["lowke"], "Small KE."),
                        "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."), "dE": (["steady"], "Steady.")},
                       "Isothermal compressor: w<sub>in</sub> = q<sub>out</sub> (h doesn't change for an ideal gas at constant T), and q<sub>out</sub> = T<sub>L</sub>(s<sub>1</sub> − s<sub>2</sub>) = RT<sub>L</sub> ln r<sub>p</sub>",
                       p="Apply the steady-flow first law to the isothermal compressor. Cross out every term that drops."),
             props([("R for air", RA, "kJ/kg·K", "A-1", 0.003, "air"), ("c<sub>p</sub> for air", CPA, "kJ/kg·K", "A-2a", 0.003, "300 K")]),
             calc([f"w<sub>c</sub> = RT<sub>L</sub> ln r<sub>p</sub> = (0.287)({T1}) ln {rp} = <b>{sg(wc)} kJ/kg</b>",
                   f"w<sub>t</sub> = RT<sub>H</sub> ln r<sub>p</sub> = {sg(wt)} kJ/kg; w<sub>net</sub> = <b>{sg(wn)} kJ/kg</b>; η<sub>Ericsson</sub> = 1 − {T1}/{TH} = {pct(eta):.1f}%",
                   f"ṁ = {Wmw * 1000}/{sg(wn)} = <b>{sg(m)} kg/s</b>",
                   f"Brayton, same r<sub>p</sub>: η = 1 − 1/{rp}<sup>0.2857</sup> = <b>{pct(etaB):.1f}%</b>, with w<sub>net</sub> = {sg(wB)} kJ/kg between the same T<sub>1</sub> and T<sub>3</sub> = {TH} K"]),
             mc(8, "Real gas turbines approach the Ericsson cycle with what hardware?",
                ["Many stages of compression with intercooling, many stages of expansion with reheat, and a regenerator: the more stages, the closer to isothermal",
                 "A bigger combustor", "A higher pressure ratio only", "None; Ericsson can't be approached"],
                0, "That's the link between this problem and Brayton with intercooling, reheat and regeneration: each added stage nudges the zigzag closer to the two isotherms.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== F8: Brayton with intercooling, reheat and regeneration
@ftemplate("F8", "Gas turbine with intercooling, reheat and regeneration", 9, "F", 24, "hardest")
def F8(rng):
    T1 = rng.choice([290, 300, 310]); T3 = rng.choice([1100, 1200, 1300, 1400]); rp = rng.choice([8, 9, 12, 16]); eps = rng.choice([0.0, 0.0, 0.7, 0.75, 0.8, 0.85, 1.0])
    x = math.sqrt(rp); Tc = T1 * x ** E; Tt = T3 / x ** E
    wc = 2 * CPA * (Tc - T1); wt = 2 * CPA * (T3 - Tt); bwr = wc / wt; wn = wt - wc
    T5 = Tc + eps * (Tt - Tc); qin = CPA * (T3 - T5) + CPA * (T3 - Tt); eta = wn / qin
    eta_simple = 1 - rp ** -E; bwr_simple = (T1 * (rp ** E - 1)) / (T3 * (1 - rp ** -E))
    epst = "an ideal regenerator" if eps == 1 else ("no regenerator" if eps == 0 else f"a regenerator with an effectiveness of {int(round(eps * 100))}%")
    stem = (f"An ideal gas-turbine cycle with an overall pressure ratio of {rp} has two stages of compression with perfect intercooling and two stages of expansion with perfect reheat, each pair with equal pressure ratios. "
            f"Air enters each compressor stage at {T1} K and each turbine stage at {T3} K, and the cycle has {epst}. Using cold-air-standard assumptions, determine (a) the temperature leaving each compressor stage, "
            "(b) the back work ratio, (c) the thermal efficiency, and (d) the efficiency of a simple ideal Brayton cycle with the same overall pressure ratio and temperatures.")
    parts = [part("a", "Compressor stage exit, T<sub>2</sub>", "K", Tc, 0.005, 4, [(T1 * rp ** E, "Each stage has ratio √r<sub>p</sub>, not r<sub>p</sub>.")]),
             part("b", "Back work ratio, w<sub>c</sub>/w<sub>t</sub>", "%", pct(bwr), 0.01, 6, [(pct(bwr_simple), "That's the simple cycle. Intercooling and reheat change both works.")]),
             part("c", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 8, [(pct(wn / (CPA * (T3 - Tc) + CPA * (T3 - Tt))), "With a regenerator, the combustor starts from T<sub>5</sub> = T<sub>2</sub> + ε(T<sub>4</sub> − T<sub>2</sub>)."),
                                                                                  (pct(wn / (CPA * (T3 - T5))), "Reheat adds heat too: q<sub>in</sub> includes c<sub>p</sub>(T<sub>3</sub> − T<sub>4</sub>) for the second turbine.")]),
             part("d", "Simple Brayton efficiency", "%", pct(eta_simple), 0.005, 6, [])]
    steps = [self_step("Find the stage exit temperature, back work ratio and efficiency of a Brayton cycle with two-stage intercooling, two-stage reheat and regeneration, and compare it with the simple cycle. Plan: equal stage ratios √r<sub>p</sub>; each stage is a small Brayton step."),
             mc(2, "Sketch the T-s diagram. Which is right?",
                ["Two short isentropic compression steps separated by cooling back to T<sub>1</sub>; two short expansion steps separated by reheating to T<sub>3</sub>; the regenerator moves heat from the turbine exhaust to the compressed air",
                 "One long compression and one long expansion", "Intercooling between the turbines", "The regenerator heats the air before the first compressor"],
                0, "Splitting compression and expansion into stages moves the cycle toward Ericsson. It raises the back work ratio's denominator and lowers its numerator."),
             assume([f"r<sub>p</sub> = {rp}, two equal stages each side", f"T<sub>1</sub> = {T1} K, T<sub>3</sub> = {T3} K", f"Regenerator ε = {eps:g}"], ["T<sub>2</sub> (K)", "r<sub>bw</sub> (%)", "η<sub>th</sub> (%)", "η<sub>simple</sub> (%)"],
                    [("open", True, "Every device is a control volume."), ("steady", True, "Steady operation."), ("coldair", True, "Given (rule 4)."), ("isen", True, "Ideal compressors and turbines.", "Every compressor and turbine stage is isentropic."),
                     ("pic", True, "Given."), ("equalr", True, "Given."), ("lowke", True, "Small KE changes."), ("nope", True, "Same height."), ("airstd", False, "Given cold-air-standard.")]),
             multi([("Each stage: T<sub>out</sub>/T<sub>in</sub> = (√r<sub>p</sub>)<sup>±(k−1)/k</sup>", True, ""), ("w<sub>c</sub> = 2c<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>); w<sub>t</sub> = 2c<sub>p</sub>(T<sub>3</sub> − T<sub>4</sub>)", True, ""),
                    ("q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>5</sub>) + c<sub>p</sub>(T<sub>3</sub> − T<sub>4</sub>); T<sub>5</sub> = T<sub>2</sub> + ε(T<sub>4</sub> − T<sub>2</sub>)", True, ""), (FIRST_SF, True, ""),
                    ("η = 1 − 1/r<sub>p</sub><sup>(k−1)/k</sup>", False, "Only for the simple cycle.")], FIRST_SF),
             sf_single({"Qin": (["isen"], "Isentropic, so adiabatic."), "Qout": (["isen"], "Isentropic, so adiabatic."), "Wout": (["dir"], "Work goes into a compressor."),
                        "mke1": (["lowke"], "Small KE."), "mke2": (["lowke"], "Small KE."), "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."), "dE": (["steady"], "Steady.")},
                       "Each compressor stage: w<sub>c,stage</sub> = c<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>)", p="Apply the steady-flow first law to one compressor stage. Cross out every term that drops."),
             props([("c<sub>p</sub> for air", CPA, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("k for air", 1.4, "", "A-2a", 0.003, "300 K")]),
             calc([f"Stage ratio √{rp} = {sg(x, 4)}; T<sub>2</sub> = {T1}({sg(x, 4)})<sup>0.2857</sup> = <b>{sg(Tc)} K</b>; T<sub>4</sub> = {T3}/({sg(x, 4)})<sup>0.2857</sup> = {sg(Tt)} K",
                   f"w<sub>c</sub> = 2(1.005)({sg(Tc)} − {T1}) = {sg(wc)}; w<sub>t</sub> = 2(1.005)({T3} − {sg(Tt)}) = {sg(wt)} kJ/kg; r<sub>bw</sub> = <b>{pct(bwr):.1f}%</b>",
                   f"T<sub>5</sub> = {sg(Tc)} + {eps:g}({sg(Tt)} − {sg(Tc)}) = {sg(T5)} K; q<sub>in</sub> = 1.005({T3} − {sg(T5)}) + 1.005({T3} − {sg(Tt)}) = {sg(qin)} kJ/kg",
                   f"η<sub>th</sub> = {sg(wn)}/{sg(qin)} = <b>{pct(eta):.1f}%</b>",
                   f"Simple Brayton: η = 1 − 1/{rp}<sup>0.2857</sup> = <b>{pct(eta_simple):.1f}%</b>, r<sub>bw</sub> = {pct(bwr_simple):.1f}%"]),
             mc(8, "Compare with the simple cycle. What pattern should you see?",
                ["Intercooling and reheat cut the back work ratio and raise net work; without a good regenerator they can lower the efficiency, because the exhaust leaves hotter and more heat goes in at reheat",
                 "Intercooling always raises the efficiency on its own", "The simple cycle always wins", "The efficiencies should be equal"],
                0, "Intercooling and reheat pay off only with regeneration: they make the turbine exhaust hotter and the compressor exit colder, which is exactly what a regenerator can use. That's the Ericsson limit again.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== F9: where a Rankine plant generates entropy
@ftemplate("F9", "Where does a steam plant generate entropy?", 10, "R", 24, "challenge", "Old Final (F24) entropy-production problem, applied to a whole cycle")
def F9(rng):
    P3 = rng.choice([3000, 4000, 5000, 6000, 8000]); T3 = rng.choice([t for t in W.SH[P3] if 400 <= t <= 550]); Pc = rng.choice([10, 15, 20]); eT = rng.choice([0.80, 0.85, 0.88, 0.90])
    TH = rng.choice([1200, 1400, 1600, 1800]); TLc = rng.choice([10, 15, 20]); TL = TLc + 273.15
    s3 = W.sh(P3, T3); st1, wp = pump(Pc, P3); h2 = st1["hf"] + wp; s2 = st1["sf"]
    x4s, h4s, stc = dome_x(Pc, s3["s"]); h4 = s3["h"] - eT * (s3["h"] - h4s); x4 = (h4 - stc["hf"]) / stc["hfg"]; s4 = stc["sf"] + x4 * stc["sfg"]
    qin = s3["h"] - h2; qout = h4 - st1["hf"]
    sgT = s4 - s3["s"]; sgB = s3["s"] - s2 - qin / TH; sgC = st1["sf"] - s4 + qout / TL; tot = sgT + sgB + sgC
    assert TLc + 5 < stc["T"]
    stem = (f"A Rankine plant has steam entering the turbine at {fP(P3)} and {fT(T3)}, a condenser at {fP(Pc)}, an ideal pump and a turbine with an isentropic efficiency of {int(round(eT * 100))}%. "
            f"The boiler receives heat from combustion gases treated as a reservoir at {TH} K, and the condenser rejects heat to a lake at {fT(TLc)}. Per kilogram of steam, determine the entropy generated "
            "(a) in the turbine, (b) in the boiler, counting the hot source, (c) in the condenser, counting the lake, and (d) in the whole plant.")
    parts = [part("a", "Turbine, s<sub>gen,T</sub>", "kJ/kg·K", sgT, 0.02, 5, [(0.0, "A real turbine generates entropy: s<sub>4</sub> − s<sub>3</sub>.")]),
             part("b", "Boiler, s<sub>gen,B</sub>", "kJ/kg·K", sgB, 0.02, 6, [(s3["s"] - s2, "Heat enters from the source, which loses q<sub>in</sub>/T<sub>H</sub>: subtract it."), (s3["s"] - s2 - qin / (TH - 273.15), "T<sub>H</sub> is already in kelvins.")]),
             part("c", "Condenser, s<sub>gen,C</sub>", "kJ/kg·K", sgC, 0.02, 6, [(st1["sf"] - s4, "The lake gains q<sub>out</sub>/T<sub>L</sub>: add it."), (st1["sf"] - s4 + qout / TLc, "Use kelvins for the lake.")]),
             part("d", "Whole plant, s<sub>gen</sub>", "kJ/kg·K", tot, 0.02, 7, [(sgT + sgC, "Include the boiler, the biggest piece.")])]
    steps = [self_step("Split a steam plant's entropy generation device by device, including the hot source and the cold lake. Plan: fix the four states; for each device, s<sub>gen</sub> = (s<sub>out</sub> − s<sub>in</sub>) + q<sub>out</sub>/T<sub>sink</sub> − q<sub>in</sub>/T<sub>source</sub>."),
             mc(2, "Where should each boundary go?",
                ["Boiler: around the boiler and the hot gas at T<sub>H</sub>. Condenser: around the condenser and the lake at T<sub>L</sub>. Turbine: around the turbine alone (adiabatic)",
                 "Each boundary on the steam side only", "One boundary around the whole plant only", "The pump generates the most entropy"],
                0, "Pushing the boundary out to the reservoir counts the entropy made by heat crossing big temperature gaps, which is where most of a plant's losses hide."),
             rk_assume([f"Turbine in: {fP(P3)}, {fT(T3)}", f"Condenser: {fP(Pc)}", f"η<sub>T</sub> = {eT}, ideal pump", f"Source {TH} K, lake {fT(TLc)}"],
                       ["s<sub>gen,T</sub>", "s<sub>gen,B</sub>", "s<sub>gen,C</sub>", "s<sub>gen</sub> (kJ/kg·K)"], [("reservoir", True, "The combustion gas and the lake stay at their temperatures.", "The hot gas and the lake act as reservoirs.")]),
             multi([(SGEN_SF + " (per kg)", True, ""), ("q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub>; q<sub>out</sub> = h<sub>4</sub> − h<sub>1</sub>", True, ""), ("Ideal pump: s<sub>2</sub> = s<sub>1</sub>", True, ""), (FIRST_SF, True, ""),
                    ("s<sub>gen</sub> = q<sub>out</sub>/T<sub>L</sub> − q<sub>in</sub>/T<sub>H</sub> for the whole plant", True, ""), ("s<sub>gen,B</sub> = s<sub>3</sub> − s<sub>2</sub>", False, "That ignores the source's entropy loss.")], FIRST_SF),
             turb_strike(3, 4),
             props([("h<sub>1</sub>, s<sub>1</sub>: h<sub>f</sub>", st1["hf"], "kJ/kg", "A-5", 0.003, fP(Pc)), ("s<sub>f</sub> at P<sub>c</sub>", stc["sf"], "kJ/kg·K", "A-5", 0.003, fP(Pc)), ("v<sub>f</sub> at P<sub>c</sub>", st1["vf"], "m³/kg", "A-5", 0.003, fP(Pc)),
                    ("h<sub>fg</sub> at P<sub>c</sub>", stc["hfg"], "kJ/kg", "A-5", 0.003, fP(Pc)), ("s<sub>fg</sub> at P<sub>c</sub>", stc["sfg"], "kJ/kg·K", "A-5", 0.003, fP(Pc)),
                    ("h<sub>3</sub>", s3["h"], "kJ/kg", "A-6", 0.003, f"{fP(P3)} block, {fT(T3)} row"), ("s<sub>3</sub>", s3["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(P3)} block, {fT(T3)} row")]),
             calc([f"Pump: h<sub>2</sub> = {num(st1['hf'], 2)} + ({st1['vf']})({P3} − {Pc}) = {sg(h2, 5)} kJ/kg; s<sub>2</sub> = s<sub>1</sub> = {num(s2, 4)}",
                   f"Turbine: h<sub>4s</sub> = {sg(h4s, 5)}; h<sub>4</sub> = {sg(h4, 5)} kJ/kg; x<sub>4</sub> = {sg(x4, 4)}; s<sub>4</sub> = {sg(s4, 5)} kJ/kg·K",
                   f"s<sub>gen,T</sub> = s<sub>4</sub> − s<sub>3</sub> = <b>{sg(sgT, 3)} kJ/kg·K</b>",
                   f"q<sub>in</sub> = {sg(qin)} kJ/kg; s<sub>gen,B</sub> = ({num(s3['s'], 4)} − {num(s2, 4)}) − {sg(qin)}/{TH} = <b>{sg(sgB, 3)} kJ/kg·K</b>",
                   f"q<sub>out</sub> = {sg(qout)} kJ/kg; s<sub>gen,C</sub> = ({num(st1['sf'], 4)} − {sg(s4, 5)}) + {sg(qout)}/{num(TL, 2)} = <b>{sg(sgC, 3)} kJ/kg·K</b>",
                   f"Total = <b>{sg(tot, 3)} kJ/kg·K</b> (check: q<sub>out</sub>/T<sub>L</sub> − q<sub>in</sub>/T<sub>H</sub> = {sg(qout / TL - qin / TH, 3)})"]),
             mc(8, "Which device dominates, and what does that suggest?",
                ["The boiler: heat falls from over a thousand kelvins in the flame to a few hundred in the steam. Hotter steam (higher pressure, superheat, reheat) or combined cycles attack exactly that loss",
                 "The turbine, so better blades are the main fix", "The pump", "They're all about equal"],
                0, "The entropy check at the end ties back to the whole-plant boundary: the device pieces must add up to q<sub>out</sub>/T<sub>L</sub> − q<sub>in</sub>/T<sub>H</sub>. Turbine losses matter, but the big gap is in the boiler.")]
    return stem, parts, steps, None, prm(locals())

# ---------------------------------------------------------------- build
def build_new(nvar=24, seed=20261111):
    out = []
    for T in FT:
        rng = random.Random(seed + sum(map(ord, T["id"])) * 11)
        seen, vs, tries = set(), [], 0
        while len(vs) < nvar and tries < 8000:
            tries += 1
            try:
                stem, parts, steps, ctx, p = T["fn"](rng)
            except (AssertionError, ValueError, IndexError, ZeroDivisionError, KeyError):
                continue
            if stem in seen: continue
            seen.add(stem)
            steps = [GE.shuffle_mc(s, rng) for s in steps]
            assert [s["n"] for s in steps] == list(range(1, 9)), (T["id"], [s["n"] for s in steps])
            vs.append({"stem": stem, "fig": None, "parts": parts, "steps": steps, "ctx": ctx, "_p": p})
        assert len(vs) == nvar, (T["id"], len(vs), tries)
        out.append({k: T[k] for k in ("id", "title", "ch", "slot", "pts", "tier", "grp", "note") if T.get(k) is not None} | {"v": vs})
    return out

if __name__ == "__main__":
    new = build_new()
    held = [t for t in GC.build() if t.get("hold") == "final"]
    for t in held: t["grp"] = "final"; t["note"] = t.get("note") or "Pulled from the Exam 2 site on Nov 11 (Brayton is off Exam 2)"
    json.dump({"new": new, "held_challenge": held}, open(os.path.join(HERE, "final_templates.json"), "w"), ensure_ascii=False)
    print(len(new), [(t["id"], len(t["v"])) for t in new], "| held:", [t["id"] for t in held])
