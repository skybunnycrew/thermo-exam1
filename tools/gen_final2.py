"""Exam-level problems for the final (Nov 23, 2026). Same eight-step format as the Exam 2 guided problems.

Modeled on the Weeks 9-11 WAMAP sets (Nov 1 revision) and Matthew's old Finals, at exam difficulty
(the challenge-tier final set lives in gen_final.py). X1-X8, 24 versions each:
  X1 Diesel with variable specific heats (A-17, v_r)        W9-C1, F24 Final Diesel
  X2 Regenerative Brayton, cold-air, US units (A-2Ea)       W9-P1
  X3 Turbojet thrust and propulsive efficiency               W10-P3
  X4 Ideal Rankine cycle                                     W10-C2, F24/F25 Finals
  X5 Ideal reheat Rankine, US units (A-5E, A-6E)            W11-P1, F23 Final
  X6 Regenerative Rankine with a closed feedwater heater     W11-P3
  X7 Cogeneration with an extraction turbine                 W11-C4
  X8 Carnot cycle with steam: why nobody builds one          W10-P4, W10-M1
Run: python3 gen_final2.py   (writes final2_templates.json)
"""
import json, math, os, random
import CoolProp.CoolProp as CP
import gen_final as GF                      # extends W.SH with the Rankine blocks, adds Rankine assumptions
from gen_final import at_Ps, dome_x, pump, rk_assume, turb_strike, TS_RANKINE
from gen_challenge import *                  # W, a17, AIR, E, prm, multi_terms, a17where, SGEN_SF, ...
import gen_exam2 as GE
from gen_exam2 import brayton_strike

HERE = os.path.dirname(os.path.abspath(__file__))

ec.LIB.update({
    "cfwh":   ("Closed feedwater heater: feedwater leaves at the drain's T<sub>sat</sub>", "Ideal closed feedwater heater: the feedwater leaves at the saturation temperature of the bled steam, and as a compressed liquid its h ≈ h<sub>f</sub> at that temperature."),
    "drain":  ("Drain leaves as saturated liquid", "The bled steam leaves the closed heater as saturated liquid at the bleed pressure."),
    "trap":   ("Drain throttled to the condenser", "The drain passes through a trap (a throttle) into the condenser: h<sub>out</sub> = h<sub>in</sub>."),
    "nozzP":  ("Nozzle expands to outside pressure", "The nozzle is isentropic and expands the gas all the way to the outside pressure."),
    "fuelm":  ("Fuel mass is small", "The fuel's mass flow is small next to the air's, so the same ṁ flows in and out."),
    "inside": ("Heat added and rejected inside the dome", "Both heat transfers happen inside the saturation dome, so they are isothermal at T<sub>sat</sub>."),
    "regenE": ("Regenerator effectiveness", "Regenerator effectiveness ε = (T<sub>5</sub> − T<sub>2</sub>)/(T<sub>4</sub> − T<sub>2</sub>), with constant c<sub>p</sub>."),
    "mix":    ("Feedwater streams mix adiabatically", "The two pumped feedwater streams mix in an insulated chamber before the boiler."),
    "usE":    ("English steam tables", "Water properties from the English steam tables (A-4E to A-6E)."),
})

XT = []
def xtemplate(tid, title, ch, slot, pts, us=False, note=None):
    def deco(fn):
        XT.append(dict(id=tid, title=title, ch=ch, slot=slot, pts=pts, tier="exam", grp="final", us=us, note=note, fn=fn))
        return fn
    return deco

PV = ["pv_otto", "pv_diesel", "pv_dual", "pv_brayton"]

# =================================================================== X1: Diesel with A-17
@xtemplate("X1", "Diesel cycle with variable specific heats", 9, "G", 22, note="Like the Week 9 WAMAP Diesel and the F24 Final's Diesel problem")
def X1(rng):
    r = rng.choice([16, 18, 20, 22]); rc = rng.choice([1.6, 1.8, 2.0, 2.2]); T1 = rng.choice([290, 300, 310]); P1 = rng.choice([90, 95, 100])
    r1 = a17.row(T1)
    vr2 = r1["vr"] / r; s2, (a, b), f2 = a17.by("vr", vr2); T2, h2 = s2["T"], s2["h"]
    T3 = rc * T2; s3, br3 = a17.at_T(T3); h3, vr3 = s3["h"], s3["vr"]
    vr4 = vr3 * r / rc; s4, (c, d), f4 = a17.by("vr", vr4); u4 = s4["u"]
    qin = h3 - h2; qout = u4 - r1["u"]; w = qin - qout; eta = w / qin
    v1 = 0.287 * T1 / P1; v2 = v1 / r; mep = w / (v1 - v2)
    cold_eta = 1 - (rc ** 1.4 - 1) / (1.4 * (rc - 1) * r ** 0.4)
    where3 = f"T<sub>3</sub> = {sg(T3, 5)} K: " + (f"the {sg(T3, 4)} K row of A-17" if br3 is None else f"between the {br3[0]['T']} K and {br3[1]['T']} K rows, so interpolate")
    stem = (f"An ideal Diesel cycle has a compression ratio of {r} and a cutoff ratio of {rc}. At the start of compression, air is at {P1} kPa and {T1} K. "
            "Accounting for the variation of specific heats with temperature, determine (a) the temperature after compression, (b) the heat added per kilogram, "
            "(c) the thermal efficiency, and (d) the mean effective pressure.")
    parts = [part("a", "T<sub>2</sub>", "K", T2, 0.006, 5, [(T1 * r ** 0.4, "That's the cold-air shortcut T<sub>1</sub>r<sup>k−1</sup>. With variable specific heats, use v<sub>r2</sub> = v<sub>r1</sub>/r in A-17.")]),
             part("b", "Heat added, q<sub>in</sub>", "kJ/kg", qin, 0.012, 6, [(s3["u"] - s2["u"], "Diesel heat goes in at constant pressure, so the boundary work folds in: q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub>, not Δu."),
                                                                         (1.005 * (T3 - T2), "That's constant c<sub>p</sub>. The problem asks for variable specific heats: h from A-17.")]),
             part("c", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.012, 5, [(pct(1 - r ** -0.4), "That's the Otto formula. Diesel needs w<sub>net</sub>/q<sub>in</sub>."),
                                                                                     (pct(cold_eta), "That's the cold-air-standard Diesel formula. Use the A-17 values: η = 1 − q<sub>out</sub>/q<sub>in</sub>."),
                                                                                     (pct(1 - (s4["h"] - r1["h"]) / qin), "Heat leaves at constant volume (4→1): q<sub>out</sub> = u<sub>4</sub> − u<sub>1</sub>, not Δh.")]),
             part("d", "Mean effective pressure, MEP", "kPa", mep, 0.015, 6, [(w / v1, "MEP divides by the displacement, v<sub>1</sub> − v<sub>2</sub>, not v<sub>1</sub>."), (qin / (v1 - v2), "MEP uses the net work, not the heat added.")])]
    steps = [self_step("Find T<sub>2</sub>, q<sub>in</sub>, η and MEP for an ideal Diesel cycle, with air properties from Table A-17. Plan: v<sub>r</sub> carries you along each isentrope; constant pressure sets T<sub>3</sub> = r<sub>c</sub>T<sub>2</sub>."),
             dia("Which P-v diagram is the Diesel cycle?", PV, 1, "Diesel: isentropic compression, heat added at constant pressure (horizontal), isentropic expansion, heat rejected at constant volume."),
             cyc_assume([f"r = {r}, r<sub>c</sub> = {rc}", f"P<sub>1</sub> = {P1} kPa, T<sub>1</sub> = {T1} K"], ["T<sub>2</sub> (K)", "q<sub>in</sub> (kJ/kg)", "η<sub>th</sub> (%)", "MEP (kPa)"],
                        [("airstd", True, f"Rule 4: the air goes from {T1} K to about {sg(T3, 2)} K, a large ΔT, and the problem asks for variable specific heats."),
                         ("intrev", True, "Ideal cycle: compression and expansion are isentropic."), ("constP", True, "Diesel heat addition happens at constant pressure.", "Heat addition (2→3) happens at constant pressure."),
                         ("stationary", True, "Standard for cycles."), ("coldair", False, "The problem asks for variable specific heats."), ("constv", False, "That's Otto's heat addition.")]),
             multi([("v<sub>r2</sub> = v<sub>r1</sub>/r and v<sub>r4</sub> = v<sub>r3</sub>(v<sub>4</sub>/v<sub>3</sub>) = v<sub>r3</sub>(r/r<sub>c</sub>)", True, ""), ("T<sub>3</sub> = r<sub>c</sub>T<sub>2</sub> (ideal gas at constant P)", True, ""),
                    ("q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub>; q<sub>out</sub> = u<sub>4</sub> − u<sub>1</sub>", True, ""), ("MEP = w<sub>net</sub>/(v<sub>1</sub> − v<sub>2</sub>), v<sub>1</sub> = RT<sub>1</sub>/P<sub>1</sub>", True, ""),
                    (FIRST_CL + " (per kg, for each process)", True, ""), ("P<sub>r2</sub> = P<sub>r1</sub>r", False, "P<sub>r</sub> goes with pressure ratios (Brayton). Volume ratios use v<sub>r</sub>.")], FIRST_CL),
             strike_custom([term("qin", "q<sub>in</sub>", "L", "+"), term("win", "w<sub>b,in</sub>", "L", "+", True, ["dir"], "The gas expands, so boundary work goes out."),
                            term("qout", "q<sub>out</sub>", "L", "−", True, ["dir"], "Heat comes in during 2→3."), term("wout", "w<sub>b,out</sub>", "L", "−"),
                            term("du", "Δu", "R", ""), term("dke", "Δke", "R", "+", True, ["stationary"], ""), term("dpe", "Δpe", "R", "+", True, ["stationary"], "")],
                           "Process 2→3: q<sub>in</sub> − P(v<sub>3</sub> − v<sub>2</sub>) = u<sub>3</sub> − u<sub>2</sub>, so q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub>",
                           p="Apply the first law to the heat-addition process, 2→3. Cross out every term that drops."),
             props([("u<sub>1</sub>", r1["u"], "kJ/kg", "A-17", 0.003, f"{T1} K"), ("v<sub>r1</sub>", r1["vr"], "", "A-17", 0.004, f"{T1} K"), ("h<sub>1</sub>", r1["h"], "kJ/kg", "A-17", 0.003, f"{T1} K"),
                    ("R for air", 0.287, "kJ/kg·K", "A-1", 0.003, "air")]),
             calc([f"v<sub>r2</sub> = {sg(r1['vr'], 4)}/{r} = {sg(vr2, 4)}: {a17where(a, b, f2)}; T<sub>2</sub> = <b>{sg(T2, 4)} K</b>, h<sub>2</sub> = {sg(h2, 5)} kJ/kg",
                   f"T<sub>3</sub> = r<sub>c</sub>T<sub>2</sub> = ({rc})({sg(T2, 4)}) = {sg(T3, 4)} K; {where3}: h<sub>3</sub> = {sg(h3, 5)} kJ/kg, v<sub>r3</sub> = {sg(vr3, 4)}",
                   f"q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub> = {sg(h3, 5)} − {sg(h2, 5)} = <b>{sg(qin)} kJ/kg</b>",
                   f"v<sub>r4</sub> = v<sub>r3</sub>(r/r<sub>c</sub>) = {sg(vr3, 4)}({r}/{rc}) = {sg(vr4, 4)}: {a17where(c, d, f4)}; u<sub>4</sub> = {sg(u4, 5)} kJ/kg",
                   f"q<sub>out</sub> = u<sub>4</sub> − u<sub>1</sub> = {sg(u4, 5)} − {num(r1['u'], 2)} = {sg(qout)} kJ/kg; w<sub>net</sub> = {sg(w)} kJ/kg",
                   f"η<sub>th</sub> = w<sub>net</sub>/q<sub>in</sub> = <b>{pct(eta):.1f}%</b>",
                   f"v<sub>1</sub> = RT<sub>1</sub>/P<sub>1</sub> = (0.287)({T1})/{P1} = {sg(v1, 4)} m³/kg; v<sub>2</sub> = v<sub>1</sub>/r = {sg(v2, 4)} m³/kg",
                   f"MEP = w<sub>net</sub>/(v<sub>1</sub> − v<sub>2</sub>) = {sg(w)}/{sg(v1 - v2, 4)} = <b>{sg(mep)} kPa</b>"]),
             mc(8, f"The cold-air-standard formula gives {pct(cold_eta):.1f}% for these ratios. How does your answer compare?",
                ["Lower: air's specific heats grow with temperature, and the cold-air value always runs a few points high", "Higher: variable specific heats always help",
                 "Exactly equal, since both are ideal cycles", "Lower by half: the cold-air formula is wrong for Diesel"],
                0, "Variable specific heats lower the temperature ratios at high T, so the efficiency drops a few points. If your number came out above the cold-air value, look for a v<sub>r</sub> multiplied where it should be divided.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== X2: regenerative Brayton, US units
R0 = 459.67; CPE = 0.240
@xtemplate("X2", "Regenerative gas turbine (US units)", 9, "G", 22, us=True, note="Like the Week 9 WAMAP regenerative gas turbine")
def X2(rng):
    rp = rng.choice([6, 7, 8, 9, 10]); T1F = rng.choice([40, 50, 60, 70, 80]); T3F = rng.choice([1400, 1500, 1600, 1800, 2000]); eps = rng.choice([0.70, 0.75, 0.80, 0.85, 0.90])
    T1, T3 = T1F + R0, T3F + R0
    T2 = T1 * rp ** E; T4 = T3 / rp ** E; assert T4 - T2 > 150
    T5 = T2 + eps * (T4 - T2); T6 = T4 - (T5 - T2)
    wc = CPE * (T2 - T1); wt = CPE * (T3 - T4); wn = wt - wc; qin = CPE * (T3 - T5); eta = wn / qin; eta0 = 1 - rp ** -E
    F = lambda TR: TR - R0
    stem = (f"A gas turbine with a regenerator runs on air with a pressure ratio of {rp}. Air enters the compressor at {T1F} °F and the turbine at {T3F} °F. "
            f"The compressor and turbine are isentropic, and the regenerator has an effectiveness of {int(round(eps * 100))}%. Using cold-air-standard assumptions, determine "
            "(a) the compressor exit temperature, (b) the turbine exit temperature, (c) the temperature of the air entering the combustor, and (d) the thermal efficiency.")
    parts = [part("a", "Compressor exit, T<sub>2</sub>", "°F", F(T2), 0.006, 4, [(T1F * rp ** E, "Temperature ratios need absolute temperature: convert to rankine (°F + 459.67) first."),
                                                                                (F(T1 * rp ** 0.4), "With a pressure ratio, the exponent is (k − 1)/k = 0.2857.")]),
             part("b", "Turbine exit, T<sub>4</sub>", "°F", F(T4), 0.006, 4, [(T3F / rp ** E, "Convert to rankine first.")]),
             part("c", "Combustor inlet, T<sub>5</sub>", "°F", F(T5), 0.006, 6, [(F(T4 - eps * (T4 - T2)), "That's the temperature of the exhaust leaving the regenerator. The compressed air leaves at T<sub>5</sub> = T<sub>2</sub> + ε(T<sub>4</sub> − T<sub>2</sub>)."),
                                                                                (F(T2 + eps * (T3 - T2)), "The regenerator can heat the air only up to the turbine exhaust temperature T<sub>4</sub>, not T<sub>3</sub>.")]),
             part("d", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 8, [(pct(eta0), "That's the simple cycle without the regenerator. The regenerator cuts q<sub>in</sub> to c<sub>p</sub>(T<sub>3</sub> − T<sub>5</sub>)."),
                                                                                    (pct(wn / (CPE * (T3 - T2))), "Heat from fuel starts at T<sub>5</sub>, after the regenerator: q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>5</sub>)."),
                                                                                    (pct(1 - T1 / T3), "That's Carnot between T<sub>1</sub> and T<sub>3</sub>, the upper limit.")])]
    steps = [self_step("Find the compressor and turbine exit temperatures, the combustor inlet temperature and the efficiency of a regenerative Brayton cycle. Plan: rankine for every ratio; the regenerator effectiveness gives T<sub>5</sub>; then w<sub>net</sub>/q<sub>in</sub>."),
             mc(2, "Where does the regenerator sit, and which streams pass through it?",
                ["Between the compressor and the combustor on the cold side, with the turbine exhaust on the hot side: the exhaust (4→6) preheats the compressed air (2→5)",
                 "Between the turbine and the compressor, heating the air before it is compressed", "Inside the combustor", "After the turbine, heating the outside air"],
                0, "Sketch it on T-s: 2→5 rises along the high-pressure line, 4→6 falls along the low-pressure line. The heat the exhaust gives up is the heat the fuel no longer has to supply."),
             assume([f"r<sub>p</sub> = {rp}", f"T<sub>1</sub> = {T1F} °F, T<sub>3</sub> = {T3F} °F", f"ε = {eps}"], ["T<sub>2</sub> (°F)", "T<sub>4</sub> (°F)", "T<sub>5</sub> (°F)", "η<sub>th</sub> (%)"],
                    [("open", True, "Each device is a control volume."), ("steady", True, "Steady operation."), ("coldair", True, "The problem says so (rule 4); constant c<sub>p</sub> = 0.240 Btu/lbm·R, k = 1.4 from A-2Ea.", "Cold-air-standard: air is an ideal gas with constant c<sub>p</sub> = 0.240 Btu/lbm·R and k = 1.4 (Table A-2Ea)."),
                     ("isen", True, "Given: isentropic compressor and turbine.", "The compressor and turbine are isentropic."), ("regen", True, "Standard for regenerators."), ("regenE", True, "Given."),
                     ("lowke", True, "Small KE changes."), ("nope", True, "Same height."), ("noshaft", True, "The regenerator has no shaft or wires.", "The regenerator and combustor have no shaft or wires."), ("closed", False, "Gas turbines are steady-flow devices.")]),
             multi([("T<sub>2</sub>/T<sub>1</sub> = r<sub>p</sub><sup>(k−1)/k</sup>; T<sub>3</sub>/T<sub>4</sub> = r<sub>p</sub><sup>(k−1)/k</sup> (absolute T)", True, ""), ("T<sub>5</sub> = T<sub>2</sub> + ε(T<sub>4</sub> − T<sub>2</sub>)", True, ""),
                    ("q<sub>in</sub> = c<sub>p</sub>(T<sub>3</sub> − T<sub>5</sub>); w<sub>net</sub> = c<sub>p</sub>[(T<sub>3</sub> − T<sub>4</sub>) − (T<sub>2</sub> − T<sub>1</sub>)]", True, ""), (FIRST_SF, True, ""),
                    ("η = 1 − 1/r<sub>p</sub><sup>(k−1)/k</sup>", False, "That's the simple cycle. A regenerator changes q<sub>in</sub>, so use w<sub>net</sub>/q<sub>in</sub>.")], FIRST_SF),
             multi_terms(["ṁh<sub>2</sub>", "ṁh<sub>4</sub>"], ["ṁh<sub>5</sub>", "ṁh<sub>6</sub>"], "Regenerator: h<sub>5</sub> − h<sub>2</sub> = h<sub>4</sub> − h<sub>6</sub> (same ṁ on both sides)", qr="regen",
                         p="Apply the steady-flow first law to the whole regenerator (both streams inside). Cross out every term that drops."),
             props([("c<sub>p</sub> for air", CPE, "Btu/lbm·R", "A-2Ea", 0.003, "air, 80 °F"), ("k for air", 1.4, "", "A-2Ea", 0.003, "air, 80 °F")]),
             calc([f"T<sub>1</sub> = {T1F} + 459.67 = {num(T1, 2)} R; T<sub>3</sub> = {T3F} + 459.67 = {num(T3, 2)} R",
                   f"T<sub>2</sub> = ({num(T1, 2)})({rp})<sup>0.2857</sup> = {sg(T2)} R = <b>{sg(F(T2))} °F</b>",
                   f"T<sub>4</sub> = {num(T3, 2)}/{rp}<sup>0.2857</sup> = {sg(T4)} R = <b>{sg(F(T4))} °F</b>",
                   f"T<sub>5</sub> = T<sub>2</sub> + ε(T<sub>4</sub> − T<sub>2</sub>) = {sg(T2)} + {eps}({sg(T4)} − {sg(T2)}) = {sg(T5)} R = <b>{sg(F(T5))} °F</b>",
                   f"w<sub>net</sub> = 0.240[({num(T3, 2)} − {sg(T4)}) − ({sg(T2)} − {num(T1, 2)})] = {sg(wn)} Btu/lbm; q<sub>in</sub> = 0.240({num(T3, 2)} − {sg(T5)}) = {sg(qin)} Btu/lbm",
                   f"η<sub>th</sub> = {sg(wn)}/{sg(qin)} = <b>{pct(eta):.1f}%</b> (simple cycle: 1 − 1/{rp}<sup>0.2857</sup> = {pct(eta0):.1f}%)"]),
             mc(8, f"Without the regenerator, this cycle would reach {pct(eta0):.1f}%. What would happen at a much higher pressure ratio?",
                ["The regenerator helps less and less: T<sub>2</sub> climbs toward T<sub>4</sub>, and once T<sub>2</sub> &gt; T<sub>4</sub> it would heat the exhaust instead",
                 "The regenerator helps more at every pressure ratio", "Nothing changes; the regenerator's gain doesn't depend on r<sub>p</sub>", "The turbine exit gets hotter"],
                0, "Regeneration pays off at low pressure ratios, where the exhaust is much hotter than the compressed air. That's why regenerative gas turbines run modest r<sub>p</sub>.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== X3: turbojet thrust and propulsive efficiency
CPA = AIR["cp"]
@xtemplate("X3", "Turbojet: thrust and propulsive efficiency", 9, "J", 18, note="Like the Week 10 WAMAP thrust problem")
def X3(rng):
    V1 = rng.choice([200, 220, 240, 260, 280]); P0 = rng.choice([30, 35, 40, 45]); T0 = rng.choice([220, 230, 240, 250]); rp = rng.choice([8, 10, 12, 14])
    T4 = rng.choice([1100, 1200, 1300, 1400]); m = rng.choice([20, 30, 40, 50, 60])
    T1 = T0 + V1 ** 2 / 2000 / CPA; P1 = P0 * (T1 / T0) ** (1 / E); T3 = T1 * rp ** E; P3 = rp * P1
    T5 = T4 - (T3 - T1); P5 = P3 * (T5 / T4) ** (1 / E); assert P5 > 1.4 * P0
    T5r, P5r = round(T5), float(f"{P5:.3g}"); T3r = round(T3)
    T6 = T5r * (P0 / P5r) ** E; V6 = math.sqrt(2000 * CPA * (T5r - T6)); assert V6 > V1 * 2
    Fk = m * (V6 - V1) / 1000; Wp = m * (V6 - V1) * V1 / 1000; Qin = m * CPA * (T4 - T3r); etap = Wp / Qin
    stem = (f"A turbojet flies at {V1} m/s where the air is at {P0} kPa and {T0} K, with {m} kg/s of air through the engine. Test data show the compressor delivering air at {T3r} K, "
            f"the combustor heating it to {T4} K, and the gas leaving the turbine at {T5r} K and {P5r:g} kPa. The nozzle is isentropic and expands the gas to the outside pressure. "
            "Using cold-air-standard assumptions, determine (a) the jet velocity, (b) the thrust, (c) the propulsive power, and (d) the propulsive efficiency.")
    parts = [part("a", "Jet velocity, V<sub>6</sub>", "m/s", V6, 0.01, 5, [(math.sqrt(2 * CPA * (T5r - T6)), "Multiply by 1000 to turn kJ/kg into m²/s²."),
                                                                         (math.sqrt(2000 * CPA * (T4 - T4 * (P0 / P5r) ** E)), "The nozzle starts at the turbine exit, state 5, not the turbine inlet.")]),
             part("b", "Thrust, F", "kN", Fk, 0.012, 4, [(m * V6 / 1000, "Thrust is the momentum gain: ṁ(V<sub>exit</sub> − V<sub>inlet</sub>). The air comes in at the flight speed.")]),
             part("c", "Propulsive power, Ẇ<sub>P</sub>", "kW", Wp, 0.012, 4, [(m * (V6 ** 2 - V1 ** 2) / 2000, "That's the gain in the jet's kinetic energy. Propulsive power is thrust times flight speed: FV<sub>aircraft</sub>."),
                                                                             (m * V6 * V1 / 1000, "Use the thrust ṁ(V<sub>6</sub> − V<sub>1</sub>), not ṁV<sub>6</sub>.")]),
             part("d", "Propulsive efficiency, η<sub>P</sub>", "%", pct(etap), 0.015, 5, [(pct(Wp / (m * CPA * (T4 - T1))), "The combustor heats from the compressor exit, T<sub>3</sub>, not the diffuser exit."),
                                                                                        (pct(2 * V1 / (V6 + V1)), "That's the Froude ratio 2V<sub>1</sub>/(V<sub>6</sub> + V<sub>1</sub>). In Çengel, η<sub>P</sub> = Ẇ<sub>P</sub>/Q̇<sub>in</sub>.")])]
    steps = [self_step("Find the jet velocity, thrust, propulsive power and propulsive efficiency of a turbojet from test data. Plan: the nozzle's energy balance gives V<sub>6</sub>; thrust is the momentum change; Ẇ<sub>P</sub> = FV<sub>1</sub>; η<sub>P</sub> = Ẇ<sub>P</sub>/Q̇<sub>in</sub>."),
             mc(2, "What kind of system is the nozzle, and what does the engine as a whole do with the air?",
                ["The nozzle is a steady-flow control volume that turns enthalpy into velocity; the engine takes air in at the flight speed and throws it out faster",
                 "The nozzle is a closed system", "The engine's net shaft work is its useful output", "The nozzle raises the pressure"],
                0, "A turbojet's useful output isn't shaft work: the turbine only drives the compressor. The output is the push from speeding up the air."),
             assume([f"V<sub>1</sub> = {V1} m/s, P<sub>0</sub> = {P0} kPa, T<sub>0</sub> = {T0} K", f"ṁ = {m} kg/s", f"T<sub>3</sub> = {T3r} K, T<sub>4</sub> = {T4} K", f"T<sub>5</sub> = {T5r} K, P<sub>5</sub> = {P5r:g} kPa"],
                    ["V<sub>6</sub> (m/s)", "F (kN)", "Ẇ<sub>P</sub> (kW)", "η<sub>P</sub> (%)"],
                    [("open", True, "Each device is a control volume."), ("steady", True, "Steady operation."), ("coldair", True, "The problem says so; c<sub>p</sub> = 1.005 kJ/kg·K, k = 1.4."),
                     ("nozzP", True, "Given."), ("lowv1", True, "The gas enters the nozzle slowly next to its exit velocity.", "The nozzle inlet velocity is small next to its exit velocity."), ("fuelm", True, "Standard for turbojets."),
                     ("adiabatic", True, "Nozzles are adiabatic.", "The nozzle is adiabatic."), ("noshaft", True, "No shaft in a nozzle.", "The nozzle has no shaft or wires."), ("nope", True, "Same height."), ("closed", False, "Gas flows through.")]),
             multi([("T<sub>6</sub> = T<sub>5</sub>(P<sub>0</sub>/P<sub>5</sub>)<sup>(k−1)/k</sup>", True, ""), ("V<sub>6</sub> = √(2c<sub>p</sub>(T<sub>5</sub> − T<sub>6</sub>))", True, ""),
                    ("F = ṁ(V<sub>6</sub> − V<sub>1</sub>); Ẇ<sub>P</sub> = FV<sub>1</sub>", True, ""), ("η<sub>P</sub> = Ẇ<sub>P</sub>/Q̇<sub>in</sub>, Q̇<sub>in</sub> = ṁc<sub>p</sub>(T<sub>4</sub> − T<sub>3</sub>)", True, ""), (FIRST_SF, True, ""),
                    ("Ẇ<sub>P</sub> = Ẇ<sub>turbine</sub> − Ẇ<sub>compressor</sub>", False, "In a turbojet those are equal; the useful output is thrust.")], FIRST_SF),
             sf_single({"Qin": (["adiabatic"], "Adiabatic."), "Qout": (["adiabatic"], "Adiabatic."), "Win": (["noshaft"], "No work in a nozzle."), "Wout": (["noshaft"], "No work in a nozzle."),
                        "mke1": (["lowv1"], "Slow at the inlet."), "mpe1": (["nope"], "Same height."), "mpe2": (["nope"], "Same height."), "dE": (["steady"], "Steady.")},
                       "Nozzle: V<sub>6</sub>²/2 = h<sub>5</sub> − h<sub>6</sub> = c<sub>p</sub>(T<sub>5</sub> − T<sub>6</sub>)", p="Apply the steady-flow first law to the nozzle (5→6; the template labels inlet 1 and exit 2). Cross out every term that drops."),
             props([("c<sub>p</sub> for air", CPA, "kJ/kg·K", "A-2a", 0.003, "300 K"), ("k for air", 1.4, "", "A-2a", 0.003, "300 K")]),
             calc([f"T<sub>6</sub> = T<sub>5</sub>(P<sub>0</sub>/P<sub>5</sub>)<sup>0.2857</sup> = {T5r}({P0}/{P5r:g})<sup>0.2857</sup> = {sg(T6)} K",
                   f"V<sub>6</sub> = √(2 × 1.005 × ({T5r} − {sg(T6)}) × 1000) = <b>{sg(V6)} m/s</b>",
                   f"F = ṁ(V<sub>6</sub> − V<sub>1</sub>) = {m}({sg(V6)} − {V1}) = {sg(Fk * 1000)} N = <b>{sg(Fk)} kN</b>",
                   f"Ẇ<sub>P</sub> = FV<sub>1</sub> = ({sg(Fk)} kN)({V1} m/s) = <b>{sg(Wp)} kW</b>",
                   f"Q̇<sub>in</sub> = ṁc<sub>p</sub>(T<sub>4</sub> − T<sub>3</sub>) = {m}(1.005)({T4} − {T3r}) = {sg(Qin)} kW; η<sub>P</sub> = <b>{pct(etap):.1f}%</b>"]),
             mc(8, "Most of the fuel's energy does not become propulsive power. Where does the rest go?",
                ["Out the back: the jet leaves much faster and hotter than the air came in, and that kinetic energy and enthalpy are left in the atmosphere",
                 "Into the compressor, which uses up most of the energy", "It's destroyed, which breaks the first law", "Into the aircraft's weight"],
                0, "Propulsive efficiency is low when the jet is much faster than the plane. Turbofans move more air more slowly, which is why every modern airliner uses one.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== X4: ideal Rankine
@xtemplate("X4", "Ideal Rankine cycle", 10, "R", 20, note="Like the Week 10 WAMAP Rankine problems and the F24/F25 Finals")
def X4(rng):
    Pb = rng.choice([3000, 5000, 8000, 10000]); T3 = rng.choice([t for t in W.SH[Pb] if 350 <= t <= 600]); Pc = rng.choice([10, 15, 20, 50]); Wmw = rng.choice([50, 100, 150, 250])
    s3 = W.sh(Pb, T3); st1, wp = pump(Pc, Pb); h1 = st1["hf"]; h2 = h1 + wp
    x4, h4, stc = dome_x(Pc, s3["s"]); assert x4 < 0.97
    wt = s3["h"] - h4; wn = wt - wp; qin = s3["h"] - h2; eta = wn / qin; m = Wmw * 1000 / wn
    etaC = 1 - (stc["T"] + 273.15) / (T3 + 273.15)
    stem = (f"A steam power plant runs on the ideal Rankine cycle and makes {Wmw} MW of net power. Steam enters the turbine at {fP(Pb)} and {fT(T3)} and is condensed at {fP(Pc)}. "
            "Determine (a) the pump work per kilogram, (b) the quality at the turbine exit, (c) the thermal efficiency, and (d) the steam mass flow rate.")
    parts = [part("a", "Pump work, w<sub>p</sub>", "kJ/kg", wp, 0.02, 4, [(st1["vf"] * (Pb - Pc) / 1000, "v(ΔP) with v in m³/kg and P in kPa is already kJ/kg; don't divide by 1000."),
                                                                         (wp * 1000, "Use kPa, not MPa or Pa: v<sub>1</sub>(P<sub>2</sub> − P<sub>1</sub>) in m³/kg × kPa = kJ/kg.")]),
             part("b", "Turbine exit quality, x<sub>4</sub>", "", x4, 0.008, 5, [((s3["s"] - stc["sf"]) / (stc["sg"]), "Divide by s<sub>fg</sub>, not s<sub>g</sub>."), ((s3["h"] - stc["hf"]) / stc["hfg"], "The turbine is isentropic: match entropy, s<sub>4</sub> = s<sub>3</sub>, not enthalpy.")]),
             part("c", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 6, [(pct(wt / qin), "Subtract the pump work: w<sub>net</sub> = w<sub>T</sub> − w<sub>p</sub>."), (pct(etaC), "That's Carnot between the condenser and turbine-inlet temperatures, an upper limit.")]),
             part("d", "Steam mass flow, ṁ", "kg/s", m, 0.012, 5, [(Wmw * 1000 / wt, "Divide by the net work, not the turbine work."), (Wmw / wn, "MW to kW: multiply by 1000.")])]
    ctx = {"t": "Where the cooling water comes from",
           "b": "Every Rankine plant has to reject heat, and most do it into water. The USGS found that in 2015 thermoelectric plants accounted for 41% of all water withdrawn in the United States, more than any other use, though only about 3% of what they withdrew was consumed (evaporated) rather than returned warmer to the river, lake or sea.",
           "q": "Your plant rejects q<sub>out</sub> = h<sub>4</sub> − h<sub>1</sub> for every kilogram of steam. When a river runs low and warm in a drought, who should get the water first: the plant, farms, fish, or the town downstream? Who decides now?",
           "src": ["USGS: Thermoelectric power water use", "https://www.usgs.gov/mission-areas/water-resources/science/thermoelectric-power-water-use"]}
    steps = [self_step("Find the pump work, turbine exit quality, efficiency and steam flow of an ideal Rankine cycle. Plan: four states in order (1 condenser exit, 2 pump exit, 3 turbine inlet, 4 turbine exit), then w<sub>net</sub>/q<sub>in</sub>, and the power sets ṁ."),
             mc(2, "Sketch the ideal Rankine cycle on T-s. Which description is right?", [TS_RANKINE, "A rectangle inside the dome, like a Carnot cycle", "The pump runs along the saturated-liquid line", "The turbine exit sits on the saturated-vapor line"],
                0, "In the ideal cycle the turbine expansion is a vertical line from 3 down to 4 at the condenser pressure; here it lands inside the dome, so 4 is a wet mixture."),
             rk_assume([f"Turbine in: {fP(Pb)}, {fT(T3)}", f"Condenser: {fP(Pc)}", f"Ẇ<sub>net</sub> = {Wmw} MW", "Ideal cycle"], ["w<sub>p</sub> (kJ/kg)", "x<sub>4</sub>", "η<sub>th</sub> (%)", "ṁ (kg/s)"],
                       [("isen", True, "Ideal cycle: the pump and turbine are isentropic.", "Ideal cycle: the pump and turbine are isentropic, so s<sub>2</sub> = s<sub>1</sub> and s<sub>4</sub> = s<sub>3</sub>.")], real=False),
             multi([("w<sub>p</sub> = v<sub>1</sub>(P<sub>2</sub> − P<sub>1</sub>); h<sub>2</sub> = h<sub>1</sub> + w<sub>p</sub>", True, ""), ("s<sub>4</sub> = s<sub>3</sub>; x<sub>4</sub> = (s<sub>4</sub> − s<sub>f</sub>)/s<sub>fg</sub>", True, ""),
                    ("η<sub>th</sub> = (w<sub>T</sub> − w<sub>p</sub>)/q<sub>in</sub>, q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub>", True, ""), ("ṁ = Ẇ<sub>net</sub>/w<sub>net</sub>", True, ""), (FIRST_SF, True, ""),
                    ("η = 1 − T<sub>L</sub>/T<sub>H</sub>", False, "That's Carnot, an upper limit, not the Rankine efficiency.")], FIRST_SF),
             turb_strike(3, 4),
             props([("h<sub>1</sub> = h<sub>f</sub>", h1, "kJ/kg", "A-5", 0.003, fP(Pc)), ("v<sub>1</sub> = v<sub>f</sub>", st1["vf"], "m³/kg", "A-5", 0.003, fP(Pc)),
                    ("h<sub>3</sub>", s3["h"], "kJ/kg", "A-6", 0.003, f"{fP(Pb)} block, {fT(T3)} row"), ("s<sub>3</sub>", s3["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(Pb)} block, {fT(T3)} row"),
                    ("s<sub>f</sub> at P<sub>c</sub>", stc["sf"], "kJ/kg·K", "A-5", 0.003, fP(Pc)), ("s<sub>fg</sub> at P<sub>c</sub>", stc["sfg"], "kJ/kg·K", "A-5", 0.003, fP(Pc)),
                    ("h<sub>fg</sub> at P<sub>c</sub>", stc["hfg"], "kJ/kg", "A-5", 0.003, fP(Pc))]),
             calc([f"w<sub>p</sub> = v<sub>1</sub>(P<sub>2</sub> − P<sub>1</sub>) = ({st1['vf']})({Pb} − {Pc:g}) = <b>{sg(wp, 3)} kJ/kg</b>; h<sub>2</sub> = {num(h1, 2)} + {sg(wp, 3)} = {sg(h2, 5)} kJ/kg",
                   f"x<sub>4</sub> = (s<sub>3</sub> − s<sub>f</sub>)/s<sub>fg</sub> = ({num(s3['s'], 4)} − {num(stc['sf'], 4)})/{num(stc['sfg'], 4)} = <b>{sg(x4, 4)}</b>",
                   f"h<sub>4</sub> = h<sub>f</sub> + x<sub>4</sub>h<sub>fg</sub> = {num(stc['hf'], 2)} + ({sg(x4, 4)})({num(stc['hfg'], 2)}) = {sg(h4, 5)} kJ/kg",
                   f"w<sub>T</sub> = {num(s3['h'], 1)} − {sg(h4, 5)} = {sg(wt)} kJ/kg; w<sub>net</sub> = {sg(wt)} − {sg(wp, 3)} = {sg(wn)} kJ/kg",
                   f"q<sub>in</sub> = {num(s3['h'], 1)} − {sg(h2, 5)} = {sg(qin)} kJ/kg; η<sub>th</sub> = {sg(wn)}/{sg(qin)} = <b>{pct(eta):.1f}%</b>",
                   f"ṁ = {Wmw * 1000}/{sg(wn)} = <b>{sg(m)} kg/s</b>"]),
             mc(8, f"The pump needs only {sg(wp, 2)} kJ/kg while the turbine makes {sg(wt, 3)} kJ/kg. Why is the back work ratio so small?",
                ["The pump moves liquid, whose specific volume is about a thousand times smaller than the steam's, and w = ∫v dP",
                 "Pumps are more efficient than turbines", "The pump works at a lower pressure difference", "It isn't small; it's about 40%, like a gas turbine"],
                0, "Steady-flow work is ∫v dP. Condensing the steam before raising its pressure is the Rankine cycle's big advantage over a gas turbine, which has to compress a gas.")]
    return stem, parts, steps, ctx, prm(locals())

# =================================================================== X5: ideal reheat Rankine, US units
PSI = 6894.757
def _w(o, *a): return CP.PropsSI(o, *a, "Water")
def satPE(P):
    g = lambda o, q: _w(o, "P", P * PSI, "Q", q)
    hf, hg = round(g("H", 0) / 2326, 2), round(g("H", 1) / 2326, 1); sf, sgv = round(g("S", 0) / 4186.8, 5), round(g("S", 1) / 4186.8, 5)
    return {"P": P, "T": round(g("T", 0) * 1.8 - 459.67, 2), "vf": float(f"{16.0185 / g('D', 0):.5f}"), "hf": hf, "hfg": round(hg - hf, 1), "hg": hg,
            "sf": sf, "sfg": round(sgv - sf, 5), "sg": sgv}
def shE(P, TF):
    T = (TF + 459.67) / 1.8
    return {"h": round(_w("H", "P", P * PSI, "T", T) / 2326, 1), "s": round(_w("S", "P", P * PSI, "T", T) / 4186.8, 4)}
FT_BTU = 5.404                               # psia·ft³ per Btu

@xtemplate("X5", "Reheat Rankine cycle (US units)", 10, "R", 22, us=True, note="Like the Week 11 WAMAP reheat problem and the F23 Final")
def X5(rng):
    P3 = rng.choice([600, 800, 1000, 1500]); T3 = rng.choice([800, 900, 1000]); P4 = rng.choice([40, 60, 80, 100, 120]); T5 = rng.choice([t for t in (800, 900, 1000) if t <= T3])
    Pc = rng.choice([1, 2, 3, 5])
    s3, s5 = shE(P3, T3), shE(P4, T5); st4, stc = satPE(P4), satPE(Pc)
    assert s3["s"] < st4["sg"] - 0.004
    x4 = (s3["s"] - st4["sf"]) / st4["sfg"]; h4 = st4["hf"] + x4 * st4["hfg"]
    x6 = (s5["s"] - stc["sf"]) / stc["sfg"]; assert x6 < 0.99; h6 = stc["hf"] + x6 * stc["hfg"]
    wp = stc["vf"] * (P3 - Pc) / FT_BTU; h2 = stc["hf"] + wp
    qin = (s3["h"] - h2) + (s5["h"] - h4); wt = (s3["h"] - h4) + (s5["h"] - h6); wn = wt - wp; eta = wn / qin
    xnr = (s3["s"] - stc["sf"]) / stc["sfg"]; hnr = stc["hf"] + xnr * stc["hfg"]; eta_nr = ((s3["h"] - hnr) - wp) / (s3["h"] - h2)
    stem = (f"An ideal reheat Rankine cycle has steam entering the high-pressure turbine at {P3} psia and {T3} °F. It expands to {P4} psia, is reheated to {T5} °F, "
            f"and expands in the low-pressure turbine to the condenser at {Pc} psia. Determine (a) the enthalpy leaving the high-pressure turbine, (b) the quality leaving the "
            "low-pressure turbine, (c) the total heat added per pound-mass, and (d) the thermal efficiency.")
    parts = [part("a", "h<sub>4</sub>, high-pressure turbine exit", "Btu/lbm", h4, 0.005, 5, [(st4["hg"], "Check the phase: s<sub>4</sub> = s<sub>3</sub> is below s<sub>g</sub> at this pressure, so state 4 is a wet mixture, not saturated vapor.")]),
             part("b", "x<sub>6</sub>, low-pressure turbine exit", "", x6, 0.008, 5, [(xnr, "That's the exit quality without reheat. The LP turbine starts at state 5, after reheating: s<sub>6</sub> = s<sub>5</sub>.")]),
             part("c", "q<sub>in</sub>, boiler plus reheater", "Btu/lbm", qin, 0.006, 6, [(s3["h"] - h2, "Add the reheater's heat too: q<sub>in</sub> = (h<sub>3</sub> − h<sub>2</sub>) + (h<sub>5</sub> − h<sub>4</sub>)."),
                                                                                       ((s3["h"] - stc["hf"]) + (s5["h"] - h4), "The boiler water enters after the pump, at h<sub>2</sub>.") if wp / qin > 0.0012 else (None, "")]),
             part("d", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.01, 6, [(pct(wt / qin), "Subtract the pump work."), (pct(eta_nr), "That's the simple cycle without reheat."),
                                                                                    (pct((wt - stc["vf"] * (P3 - Pc)) / qin), "psia·ft³/lbm isn't Btu/lbm: divide v(ΔP) by 5.404.")])]
    steps = [self_step("Find the HP turbine exit enthalpy, LP exit quality, heat input and efficiency of an ideal reheat Rankine cycle, in English units. Plan: six states in order; s stays constant across each turbine and the pump; two boiler heats, two turbine works."),
             mc(2, "Sketch the T-s diagram. Which description is right?",
                ["1 on the liquid line at P<sub>c</sub>; tiny pump step to 2; boiler to 3; HP turbine straight down to 4 at P<sub>4</sub>; reheat along P<sub>4</sub> to 5; LP turbine straight down to 6 at P<sub>c</sub>; condenser back to 1",
                 "Reheat happens after the LP turbine", "Reheat runs at the boiler pressure", "Both turbines end on the saturated-vapor line"],
                0, "Reheat shifts the LP expansion to the right on T-s, so the steam leaves the last turbine stage drier."),
             rk_assume([f"HP turbine in: {P3} psia, {T3} °F", f"Reheat: {P4} psia to {T5} °F", f"Condenser: {Pc} psia", "Ideal cycle"], ["h<sub>4</sub> (Btu/lbm)", "x<sub>6</sub>", "q<sub>in</sub> (Btu/lbm)", "η<sub>th</sub> (%)"],
                       [("isen", True, "Ideal cycle: s<sub>4</sub> = s<sub>3</sub>, s<sub>6</sub> = s<sub>5</sub>, s<sub>2</sub> = s<sub>1</sub>.", "Ideal cycle: both turbines and the pump are isentropic."),
                        ("usE", True, "Rule 1, in English units.")], real=False),
             multi([("w<sub>p</sub> = v<sub>1</sub>(P<sub>2</sub> − P<sub>1</sub>)/5.404 (psia·ft³/lbm to Btu/lbm)", True, ""), ("s<sub>4</sub> = s<sub>3</sub>, s<sub>6</sub> = s<sub>5</sub>; x = (s − s<sub>f</sub>)/s<sub>fg</sub>", True, ""),
                    ("q<sub>in</sub> = (h<sub>3</sub> − h<sub>2</sub>) + (h<sub>5</sub> − h<sub>4</sub>)", True, ""), ("η<sub>th</sub> = [(h<sub>3</sub> − h<sub>4</sub>) + (h<sub>5</sub> − h<sub>6</sub>) − w<sub>p</sub>]/q<sub>in</sub>", True, ""), (FIRST_SF, True, ""),
                    ("q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub>", False, "That misses the reheater.")], FIRST_SF),
             turb_strike(5, 6),
             props([("h<sub>3</sub>", s3["h"], "Btu/lbm", "A-6E", 0.003, f"{P3} psia, {T3} °F"), ("s<sub>3</sub>", s3["s"], "Btu/lbm·R", "A-6E", 0.003, f"{P3} psia, {T3} °F"),
                    ("s<sub>f</sub> at P<sub>4</sub>", st4["sf"], "Btu/lbm·R", "A-5E", 0.003, f"{P4} psia"), ("s<sub>fg</sub> at P<sub>4</sub>", st4["sfg"], "Btu/lbm·R", "A-5E", 0.003, f"{P4} psia"),
                    ("h<sub>f</sub> at P<sub>4</sub>", st4["hf"], "Btu/lbm", "A-5E", 0.003, f"{P4} psia"), ("h<sub>fg</sub> at P<sub>4</sub>", st4["hfg"], "Btu/lbm", "A-5E", 0.003, f"{P4} psia"),
                    ("h<sub>5</sub>", s5["h"], "Btu/lbm", "A-6E", 0.003, f"{P4} psia, {T5} °F"), ("s<sub>5</sub>", s5["s"], "Btu/lbm·R", "A-6E", 0.003, f"{P4} psia, {T5} °F"),
                    ("h<sub>f</sub> at P<sub>c</sub>", stc["hf"], "Btu/lbm", "A-5E", 0.003, f"{Pc} psia"), ("v<sub>f</sub> at P<sub>c</sub>", stc["vf"], "ft³/lbm", "A-5E", 0.003, f"{Pc} psia"),
                    ("s<sub>f</sub> at P<sub>c</sub>", stc["sf"], "Btu/lbm·R", "A-5E", 0.003, f"{Pc} psia"), ("s<sub>fg</sub> at P<sub>c</sub>", stc["sfg"], "Btu/lbm·R", "A-5E", 0.003, f"{Pc} psia"),
                    ("h<sub>fg</sub> at P<sub>c</sub>", stc["hfg"], "Btu/lbm", "A-5E", 0.003, f"{Pc} psia")]),
             calc([f"Pump: w<sub>p</sub> = ({stc['vf']})({P3} − {Pc})/5.404 = {sg(wp, 3)} Btu/lbm; h<sub>2</sub> = {num(stc['hf'], 2)} + {sg(wp, 3)} = {sg(h2, 5)} Btu/lbm",
                   f"HP turbine: s<sub>3</sub> = {num(s3['s'], 4)} &lt; s<sub>g</sub> = {num(st4['sg'], 5)} at {P4} psia, so state 4 is wet: x<sub>4</sub> = ({num(s3['s'], 4)} − {num(st4['sf'], 5)})/{num(st4['sfg'], 5)} = {sg(x4, 4)}",
                   f"h<sub>4</sub> = {num(st4['hf'], 2)} + ({sg(x4, 4)})({num(st4['hfg'], 1)}) = <b>{sg(h4, 5)} Btu/lbm</b>",
                   f"LP turbine: x<sub>6</sub> = ({num(s5['s'], 4)} − {num(stc['sf'], 5)})/{num(stc['sfg'], 5)} = <b>{sg(x6, 4)}</b>; h<sub>6</sub> = {sg(h6, 5)} Btu/lbm",
                   f"q<sub>in</sub> = ({num(s3['h'], 1)} − {sg(h2, 5)}) + ({num(s5['h'], 1)} − {sg(h4, 5)}) = <b>{sg(qin)} Btu/lbm</b>",
                   f"w<sub>T</sub> = ({num(s3['h'], 1)} − {sg(h4, 5)}) + ({num(s5['h'], 1)} − {sg(h6, 5)}) = {sg(wt)} Btu/lbm; w<sub>net</sub> = {sg(wn)} Btu/lbm",
                   f"η<sub>th</sub> = {sg(wn)}/{sg(qin)} = <b>{pct(eta):.1f}%</b>"]),
             mc(8, f"Without reheat, the steam would leave the turbine at x ≈ {sg(xnr, 3)} and the efficiency would be {pct(eta_nr):.1f}%. What did reheat buy?",
                [f"Mostly drier steam at the turbine exit (x<sub>6</sub> = {sg(x6, 3)}), which protects the last blades, plus more work per pound-mass; the efficiency changes only a little",
                 "A large jump in efficiency, which is the main reason plants reheat", "A lower condenser pressure", "Nothing; reheat only costs fuel"],
                0, "Turbine blades erode when the exit quality drops below about 90%. Reheat lets designers raise the boiler pressure (good for efficiency) without wrecking the low-pressure turbine.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== X6: closed feedwater heater, drain trapped to the condenser
@xtemplate("X6", "Regenerative Rankine with a closed feedwater heater", 10, "R", 22, note="Like the Week 11 WAMAP closed feedwater heater")
def X6(rng):
    Pb = rng.choice([6000, 8000, 10000, 12500, 15000]); T4 = rng.choice([t for t in W.SH[Pb] if 450 <= t <= 600]); Pf = rng.choice([400, 600, 800, 1000, 1200]); Pc = rng.choice([10, 15, 20])
    s4 = W.sh(Pb, T4); stc, wp = pump(Pc, Pb); h1 = stc["hf"]; h2 = h1 + wp
    stf = W.satP(Pf); h3 = stf["hf"]; h7 = stf["hf"]
    h5, how5, wet5 = at_Ps(Pf, s4["s"]); x6, h6, _ = dome_x(Pc, s4["s"]); assert x6 < 0.95
    y = (h3 - h2) / (h5 - h7); qin = s4["h"] - h3; wt = (s4["h"] - h5) + (1 - y) * (h5 - h6); wn = wt - wp; eta = wn / qin
    eta_s = ((s4["h"] - h6) - wp) / (s4["h"] - h2)
    stem = (f"An ideal regenerative Rankine cycle uses one closed feedwater heater. Steam enters the turbine at {fP(Pb)} and {fT(T4)}; some is bled at {fP(Pf)} to the closed heater, "
            f"and the rest expands to the condenser at {fP(Pc)}. The bled steam leaves the heater as saturated liquid and is throttled (trapped) into the condenser. The feedwater, pumped from the "
            "condenser to the boiler pressure, leaves the heater at the bled steam's saturation temperature. Per kilogram of steam through the boiler, determine (a) the fraction bled, "
            "(b) the heat added in the boiler, (c) the net work, and (d) the thermal efficiency.")
    parts = [part("a", "Fraction bled, y", "", y, 0.01, 6, [((h3 - h2) / (h5 - h2), "That's the open-heater form. In a closed heater the streams don't mix: the bled steam leaves as saturated liquid at h<sub>7</sub>, so y = (h<sub>3</sub> − h<sub>2</sub>)/(h<sub>5</sub> − h<sub>7</sub>)."),
                                                       ((h5 - h7) / (h3 - h2), "Upside down: y(h<sub>5</sub> − h<sub>7</sub>) = h<sub>3</sub> − h<sub>2</sub>.")]),
             part("b", "q<sub>in</sub>", "kJ/kg", qin, 0.005, 4, [(s4["h"] - h2, "The feedwater reaches the boiler already preheated, at h<sub>3</sub>.")]),
             part("c", "w<sub>net</sub>", "kJ/kg", wn, 0.01, 6, [((s4["h"] - h6) - wp, "Only (1 − y) of the steam expands below the bleed point."), (wt, "Subtract the pump work.")]),
             part("d", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.008, 6, [(pct(eta_s), "That's the simple Rankine cycle without the heater.")])]
    steps = [self_step("Find the bled fraction, heat in, net work and efficiency of an ideal Rankine cycle with one closed feedwater heater whose drain is trapped to the condenser. Plan: number the states, fix each, then let the heater's energy balance set y; everything per kg through the boiler."),
             mc(2, "How is a closed feedwater heater different from an open one?",
                ["It's a heat exchanger: the bled steam and the feedwater never mix, so they can be at different pressures; the condensed bled steam (the drain) goes back to the condenser through a trap",
                 "The bled steam mixes with the feedwater, so both leave at the bleed pressure", "It needs a pump after it for every stream", "It heats the steam after the boiler"],
                0, "Number it: 1 condenser exit, 2 pump exit, 3 feedwater leaving the heater, 4 turbine inlet, 5 bleed, 6 turbine exit, 7 drain leaving the heater, 8 after the trap. One pump handles all the water."),
             rk_assume([f"Turbine in: {fP(Pb)}, {fT(T4)}", f"Bleed: {fP(Pf)}", f"Condenser: {fP(Pc)}", "Ideal cycle"], ["y", "q<sub>in</sub> (kJ/kg)", "w<sub>net</sub> (kJ/kg)", "η<sub>th</sub> (%)"],
                       [("isen", True, "Ideal cycle.", "Ideal cycle: turbine and pump are isentropic."), ("cfwh", True, "Given."), ("drain", True, "Given."), ("trap", True, "Given."), ("shell", True, "Standard for heat exchangers.", "The closed heater is insulated: all the heat the bled steam gives up goes into the feedwater."),
                        ("fwhsat", False, "That's an open heater's exit, where the streams mix.")], real=False),
             multi([("Closed heater: y(h<sub>5</sub> − h<sub>7</sub>) = h<sub>3</sub> − h<sub>2</sub>", True, ""), ("q<sub>in</sub> = h<sub>4</sub> − h<sub>3</sub>", True, ""),
                    ("w<sub>T</sub> = (h<sub>4</sub> − h<sub>5</sub>) + (1 − y)(h<sub>5</sub> − h<sub>6</sub>)", True, ""), ("w<sub>p</sub> = v<sub>1</sub>(P<sub>b</sub> − P<sub>c</sub>) for all the water", True, ""), (FIRST_SF, True, ""),
                    ("yh<sub>5</sub> + (1 − y)h<sub>2</sub> = h<sub>3</sub>", False, "That's an open (mixing) heater.")], FIRST_SF),
             multi_terms(["yh<sub>5</sub>", "(1)h<sub>2</sub>"], ["yh<sub>7</sub>", "(1)h<sub>3</sub>"], "Closed heater, per kg through the boiler: y(h<sub>5</sub> − h<sub>7</sub>) = h<sub>3</sub> − h<sub>2</sub>", qr="shell",
                         p="Apply the steady-flow first law to the closed feedwater heater (both streams inside). Cross out every term that drops."),
             props([("h<sub>1</sub> = h<sub>f</sub> at P<sub>c</sub>", h1, "kJ/kg", "A-5", 0.003, fP(Pc)), ("v<sub>1</sub> = v<sub>f</sub> at P<sub>c</sub>", stc["vf"], "m³/kg", "A-5", 0.003, fP(Pc)),
                    ("h<sub>3</sub> ≈ h<sub>7</sub> = h<sub>f</sub> at P<sub>f</sub>", h3, "kJ/kg", "A-5", 0.003, fP(Pf)),
                    ("h<sub>4</sub>", s4["h"], "kJ/kg", "A-6", 0.003, f"{fP(Pb)} block, {fT(T4)} row"), ("s<sub>4</sub>", s4["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(Pb)} block, {fT(T4)} row"),
                    ("h<sub>5</sub> (s = s<sub>4</sub>)", h5, "kJ/kg", "A-5" if wet5 else "A-6", 0.004, fP(Pf)),
                    ("s<sub>f</sub> at P<sub>c</sub>", stc["sf"], "kJ/kg·K", "A-5", 0.003, fP(Pc)), ("s<sub>fg</sub> at P<sub>c</sub>", stc["sfg"], "kJ/kg·K", "A-5", 0.003, fP(Pc)),
                    ("h<sub>fg</sub> at P<sub>c</sub>", stc["hfg"], "kJ/kg", "A-5", 0.003, fP(Pc))]),
             calc([f"Pump: w<sub>p</sub> = ({stc['vf']})({Pb} − {Pc}) = {sg(wp, 3)} kJ/kg; h<sub>2</sub> = {sg(h2, 5)} kJ/kg",
                   f"Heater exits: h<sub>3</sub> ≈ h<sub>f</sub> at T<sub>sat</sub>({fP(Pf)}) = {num(h3, 2)} kJ/kg (compressed liquid ≈ saturated liquid at T); drain h<sub>7</sub> = h<sub>f</sub> at {fP(Pf)} = {num(h7, 2)} kJ/kg",
                   f"Bleed: {how5}; h<sub>5</sub> = {sg(h5, 5)} kJ/kg",
                   f"Turbine exit: x<sub>6</sub> = ({num(s4['s'], 4)} − {num(stc['sf'], 4)})/{num(stc['sfg'], 4)} = {sg(x6, 4)}; h<sub>6</sub> = {sg(h6, 5)} kJ/kg",
                   f"y = (h<sub>3</sub> − h<sub>2</sub>)/(h<sub>5</sub> − h<sub>7</sub>) = ({num(h3, 2)} − {sg(h2, 5)})/({sg(h5, 5)} − {num(h7, 2)}) = <b>{sg(y, 4)}</b>",
                   f"q<sub>in</sub> = h<sub>4</sub> − h<sub>3</sub> = {num(s4['h'], 1)} − {num(h3, 2)} = <b>{sg(qin)} kJ/kg</b>",
                   f"w<sub>T</sub> = ({num(s4['h'], 1)} − {sg(h5, 5)}) + (1 − {sg(y, 4)})({sg(h5, 5)} − {sg(h6, 5)}) = {sg(wt)} kJ/kg; w<sub>net</sub> = <b>{sg(wn)} kJ/kg</b>",
                   f"η<sub>th</sub> = {sg(wn)}/{sg(qin)} = <b>{pct(eta):.1f}%</b> (without the heater: {pct(eta_s):.1f}%)"]),
             mc(8, f"The heater raised the efficiency from {pct(eta_s):.1f}% to {pct(eta):.1f}% even though less steam reaches the condenser to make work. Why?",
                ["The boiler no longer heats cold feedwater: the coldest, least useful part of the heat addition is done by bled steam instead, so the average temperature of heat addition goes up",
                 "Bleeding steam makes the turbine more efficient", "The pump work drops to zero", "The condenser runs at a lower pressure"],
                0, "Regeneration attacks the same weakness Carnot points to: heat added at low temperature. The drain sent back to the condenser wastes a little, which is why real plants often pump it forward instead.")]
    return stem, parts, steps, None, prm(locals())

# =================================================================== X7: cogeneration with an extraction turbine
@xtemplate("X7", "Cogeneration plant with an extraction turbine", 10, "K", 22, note="Like the Week 11 WAMAP cogeneration problem")
def X7(rng):
    Pb = rng.choice([4000, 6000, 7000, 8000]); T5 = rng.choice([t for t in W.SH[Pb] if 400 <= t <= 600]); Pp = rng.choice([300, 400, 600, 800]); Pc = rng.choice([10, 15, 20])
    m = rng.choice([10, 15, 20, 25, 30]); f = rng.choice([0.2, 0.25, 0.3, 0.4, 0.5])
    s5 = W.sh(Pb, T5); h6, how6, wet6 = at_Ps(Pp, s5["s"]); x7, h7, stc = dome_x(Pc, s5["s"]); assert x7 < 0.97
    stp = W.satP(Pp); mp = f * m; mc_ = m - mp
    wpc = stc["vf"] * (Pb - Pc); wpp = stp["vf"] * (Pb - Pp); h2 = stc["hf"] + wpc; h9 = stp["hf"] + wpp
    Qp = mp * (h6 - stp["hf"]); Wt = m * (s5["h"] - h6) + mc_ * (h6 - h7); Wp = mc_ * wpc + mp * wpp; Wn = Wt - Wp
    h3 = (mc_ * h2 + mp * h9) / m; Qin = m * (s5["h"] - h3); eu = (Wn + Qp) / Qin
    stem = (f"A cogeneration plant sends {m} kg/s of steam into its turbine at {fP(Pb)} and {fT(T5)}. A fraction {f:g} of the steam is extracted at {fP(Pp)} and sent to a process heater, "
            f"which it leaves as saturated liquid; the rest expands to the condenser at {fP(Pc)}. Each liquid stream is pumped to {fP(Pb)}, and the two mix before the boiler. "
            "All turbines and pumps are isentropic. Determine (a) the rate of process heat, (b) the net power, (c) the rate of heat input in the boiler, and (d) the utilization factor.")
    parts = [part("a", "Process heat, Q̇<sub>p</sub>", "kW", Qp, 0.01, 5, [(mp * (h6 - stc["hf"]), "The process steam leaves as saturated liquid at the process pressure: h<sub>f</sub> at P<sub>p</sub>."),
                                                                           (m * (h6 - stp["hf"]), "Only the extracted fraction goes to the process heater.")]),
             part("b", "Net power, Ẇ<sub>net</sub>", "kW", Wn, 0.012, 6, [(m * (s5["h"] - h7) - Wp, "Only (1 − f)ṁ expands below the extraction pressure."), (Wt, "Subtract both pumps' power.")]),
             part("c", "Boiler heat input, Q̇<sub>in</sub>", "kW", Qin, 0.008, 5, [(m * (s5["h"] - h2), "The boiler water is a mix of both pumped streams; the process return is much warmer."),
                                                                                  (m * (s5["h"] - stc["hf"]), "The feedwater enters after the pumps, at the mixed h<sub>3</sub>.")]),
             part("d", "Utilization factor, ε<sub>u</sub>", "%", pct(eu), 0.01, 6, [(pct(Wn / Qin), "That's the thermal efficiency. The utilization factor also counts the process heat: (Ẇ<sub>net</sub> + Q̇<sub>p</sub>)/Q̇<sub>in</sub>.")])]
    ctx = {"t": "Keeping the lights on when the grid goes down",
           "b": "When Superstorm Sandy knocked out power across New York in 2012, Co-op City in the Bronx, a cooperative of roughly 50,000 to 60,000 residents, kept its electricity, heat and hot water running from its own 40 MW combined heat and power plant. After the storm, the U.S. Departments of Energy and Housing and Urban Development and the EPA put out a guide urging cogeneration for hospitals, shelters and other critical buildings.",
           "q": "A campus, hospital or housing co-op that can afford a cogeneration plant can ride out a blackout; the neighborhood next door may not. Which buildings in Everett would you want to keep heat and power in a week-long outage, and who should pay for it?",
           "src": ["U.S. DOE, HUD and EPA: Guide to Using Combined Heat and Power for Enhancing Reliability and Resiliency in Buildings (2013)", "https://www.energy.gov/sites/prod/files/2013/11/f4/chp_for_reliability_guidance.pdf"]}
    steps = [self_step("Find the process heat, net power, boiler heat and utilization factor of a cogeneration plant whose turbine feeds a process heater and a condenser. Plan: fix the states, split the flow, then add up powers and heats in kW."),
             mc(2, "Why judge this plant by its utilization factor instead of its thermal efficiency?",
                ["Because the process heat is a product too: ε<sub>u</sub> = (Ẇ<sub>net</sub> + Q̇<sub>p</sub>)/Q̇<sub>in</sub> counts both useful outputs",
                 "Because cogeneration plants make no net work", "Because the thermal efficiency is always higher", "They're the same thing"],
                0, "A cogeneration plant sells heat as well as electricity. Its thermal efficiency looks low, but much of the heat a power plant would dump into a river goes to work here."),
             rk_assume([f"Turbine in: {fP(Pb)}, {fT(T5)}, ṁ = {m} kg/s", f"Extraction: f = {f:g} at {fP(Pp)}", f"Condenser: {fP(Pc)}", "Ideal turbine and pumps"], ["Q̇<sub>p</sub> (kW)", "Ẇ<sub>net</sub> (kW)", "Q̇<sub>in</sub> (kW)", "ε<sub>u</sub> (%)"],
                       [("isen", True, "Given.", "The turbine and pumps are isentropic."), ("procsat", True, "Given."), ("mix", True, "Standard.")], real=False),
             multi([("Q̇<sub>p</sub> = ṁ<sub>p</sub>(h<sub>6</sub> − h<sub>f,p</sub>)", True, ""), ("Ẇ<sub>T</sub> = ṁ(h<sub>5</sub> − h<sub>6</sub>) + ṁ<sub>c</sub>(h<sub>6</sub> − h<sub>7</sub>)", True, ""),
                    ("Q̇<sub>in</sub> = ṁh<sub>5</sub> − ṁ<sub>c</sub>h<sub>2</sub> − ṁ<sub>p</sub>h<sub>9</sub>", True, ""), ("ε<sub>u</sub> = (Ẇ<sub>net</sub> + Q̇<sub>p</sub>)/Q̇<sub>in</sub>", True, ""), (FIRST_SF, True, ""),
                    ("ε<sub>u</sub> = Ẇ<sub>net</sub>/Q̇<sub>in</sub>", False, "That's thermal efficiency; it leaves out the process heat.")], FIRST_SF),
             multi_terms(["ṁ<sub>p</sub>h<sub>6</sub>"], ["ṁ<sub>p</sub>h<sub>8</sub>"], "Process heater: Q̇<sub>p</sub> = ṁ<sub>p</sub>(h<sub>6</sub> − h<sub>8</sub>)", keepQout=True,
                         p="Apply the steady-flow first law to the process heater (steam side only; Q̇<sub>p</sub> leaves to the process). Cross out every term that drops."),
             props([("h<sub>5</sub>", s5["h"], "kJ/kg", "A-6", 0.003, f"{fP(Pb)} block, {fT(T5)} row"), ("s<sub>5</sub>", s5["s"], "kJ/kg·K", "A-6", 0.003, f"{fP(Pb)} block, {fT(T5)} row"),
                    ("h<sub>6</sub> (s = s<sub>5</sub>)", h6, "kJ/kg", "A-5" if wet6 else "A-6", 0.004, fP(Pp)),
                    ("h<sub>8</sub> = h<sub>f</sub> at P<sub>p</sub>", stp["hf"], "kJ/kg", "A-5", 0.003, fP(Pp)), ("v<sub>f</sub> at P<sub>p</sub>", stp["vf"], "m³/kg", "A-5", 0.003, fP(Pp)),
                    ("h<sub>1</sub> = h<sub>f</sub> at P<sub>c</sub>", stc["hf"], "kJ/kg", "A-5", 0.003, fP(Pc)), ("v<sub>f</sub> at P<sub>c</sub>", stc["vf"], "m³/kg", "A-5", 0.003, fP(Pc)),
                    ("s<sub>f</sub> at P<sub>c</sub>", stc["sf"], "kJ/kg·K", "A-5", 0.003, fP(Pc)), ("s<sub>fg</sub> at P<sub>c</sub>", stc["sfg"], "kJ/kg·K", "A-5", 0.003, fP(Pc)),
                    ("h<sub>fg</sub> at P<sub>c</sub>", stc["hfg"], "kJ/kg", "A-5", 0.003, fP(Pc))]),
             calc([f"ṁ<sub>p</sub> = {f:g}({m}) = {sg(mp, 3)} kg/s; ṁ<sub>c</sub> = {sg(mc_, 3)} kg/s",
                   f"Extraction: {how6}; h<sub>6</sub> = {sg(h6, 5)} kJ/kg. Condenser inlet: x<sub>7</sub> = {sg(x7, 4)}, h<sub>7</sub> = {sg(h7, 5)} kJ/kg",
                   f"Q̇<sub>p</sub> = {sg(mp, 3)}({sg(h6, 5)} − {num(stp['hf'], 2)}) = <b>{sg(Qp)} kW</b>",
                   f"Pumps: w<sub>p,c</sub> = ({stc['vf']})({Pb} − {Pc}) = {sg(wpc, 3)} kJ/kg, h<sub>2</sub> = {sg(h2, 5)}; w<sub>p,p</sub> = ({stp['vf']})({Pb} − {Pp}) = {sg(wpp, 3)} kJ/kg, h<sub>9</sub> = {sg(h9, 5)}",
                   f"Ẇ<sub>T</sub> = {m}({num(s5['h'], 1)} − {sg(h6, 5)}) + {sg(mc_, 3)}({sg(h6, 5)} − {sg(h7, 5)}) = {sg(Wt)} kW; Ẇ<sub>p</sub> = {sg(Wp, 3)} kW; Ẇ<sub>net</sub> = <b>{sg(Wn)} kW</b>",
                   f"Q̇<sub>in</sub> = {m}({num(s5['h'], 1)}) − {sg(mc_, 3)}({sg(h2, 5)}) − {sg(mp, 3)}({sg(h9, 5)}) = <b>{sg(Qin)} kW</b>",
                   f"ε<sub>u</sub> = ({sg(Wn)} + {sg(Qp)})/{sg(Qin)} = <b>{pct(eu):.1f}%</b> (thermal efficiency alone: {pct(Wn / Qin):.1f}%)"]),
             mc(8, "What would make the utilization factor reach 100%?",
                ["Sending all the steam to the process heater (no condenser): then every bit of the boiler's heat leaves as either work or process heat",
                 "Making the turbine isentropic, which it already is", "Raising the condenser pressure", "Nothing; 100% breaks the second law"],
                0, "The utilization factor isn't capped by Carnot, because process heat counts as useful. The condenser is the only place energy is thrown away here.")]
    return stem, parts, steps, ctx, prm(locals())

# =================================================================== X8: Carnot cycle with steam
@xtemplate("X8", "Carnot cycle with steam: why nobody builds one", 10, "J", 18, note="Like the Week 10 WAMAP Carnot-with-steam problem")
def X8(rng):
    PH = rng.choice([1000, 2000, 3000, 4000, 5000, 6000]); PL = rng.choice([10, 15, 20, 50, 100])
    H, L = W.satP(PH), W.satP(PL); TH, TL = H["T"] + 273.15, L["T"] + 273.15
    eta = 1 - TL / TH; qin = H["hfg"]; wn = eta * qin
    x3 = (H["sg"] - L["sf"]) / L["sfg"]; x4 = (H["sf"] - L["sf"]) / L["sfg"]; assert x3 < 0.95
    stem = (f"A Carnot cycle runs with water inside the saturation dome. Heat is added at {fP(PH)}, turning saturated liquid into saturated vapor; the vapor expands isentropically "
            f"in a turbine to {fP(PL)}; heat is rejected at {fP(PL)}; and a compressor returns the wet mixture isentropically to saturated liquid at {fP(PH)}. Determine (a) the thermal efficiency, "
            "(b) the heat added per kilogram, (c) the quality at the turbine exit, and (d) the quality at the compressor inlet.")
    parts = [part("a", "Thermal efficiency, η<sub>th</sub>", "%", pct(eta), 0.006, 4, [(pct(1 - L["T"] / H["T"]), "Carnot needs absolute temperatures: add 273.15 to each.")]),
             part("b", "Heat added, q<sub>in</sub>", "kJ/kg", qin, 0.005, 4, [(H["hg"], "From saturated liquid to saturated vapor, the heat is h<sub>fg</sub>, not h<sub>g</sub>.")]),
             part("c", "Turbine exit quality, x<sub>3</sub>", "", x3, 0.008, 5, [((H["sg"] - L["sf"]) / L["sg"], "Divide by s<sub>fg</sub>, not s<sub>g</sub>."), ((H["hg"] - L["hf"]) / L["hfg"], "Isentropic: match s, not h.")]),
             part("d", "Compressor inlet quality, x<sub>4</sub>", "", x4, 0.012, 5, [((H["sf"] - L["sf"]) / L["sg"], "Divide by s<sub>fg</sub>, not s<sub>g</sub>.")])]
    steps = [self_step("Find the efficiency, heat input and the qualities leaving the turbine and entering the compressor of a Carnot cycle inside the steam dome. Plan: inside the dome, constant pressure is constant temperature; vertical lines on T-s are isentropes."),
             mc(2, "Sketch the cycle on T-s. Which description is right?",
                ["A rectangle inside the dome: 1→2 across at T<sub>H</sub> (liquid line to vapor line), 2→3 straight down, 3→4 across at T<sub>L</sub>, 4→1 straight up to the liquid line",
                 "Like Rankine: the pump starts on the saturated-liquid line at T<sub>L</sub>", "A rectangle that extends into the superheated region", "Two vertical lines and two curved isobars outside the dome"],
                0, "Inside the dome, heat transfer at constant P is isothermal, which is exactly what Carnot needs. The trouble is at the corners: state 4 is a wet mixture that has to be compressed."),
             assume([f"Heat in at {fP(PH)}", f"Heat out at {fP(PL)}", "Isentropic turbine and compressor"], ["η<sub>th</sub> (%)", "q<sub>in</sub> (kJ/kg)", "x<sub>3</sub>", "x<sub>4</sub>"],
                    [("open", True, "Each device is a control volume."), ("steady", True, "Steady."), ("steam", True, "Rule 1."), ("isen", True, "Given.", "Turbine and compressor are isentropic."),
                     ("inside", True, "Given: both heat transfers happen in the dome."), ("noshaft", True, "Boiler and condenser have no shaft.", "The boiler and condenser have no shaft or wires."), ("lowke", True, "Small KE."), ("nope", True, "Small PE."), ("steamideal", False, "Rule 1: never ideal gas for steam.")]),
             multi([("η<sub>Carnot</sub> = 1 − T<sub>L</sub>/T<sub>H</sub> (kelvins)", True, ""), ("q<sub>in</sub> = h<sub>fg</sub> at P<sub>H</sub>", True, ""),
                    ("x = (s − s<sub>f</sub>)/s<sub>fg</sub> at P<sub>L</sub>, with s<sub>3</sub> = s<sub>g,H</sub> and s<sub>4</sub> = s<sub>f,H</sub>", True, ""), (FIRST_SF, True, ""),
                    ("w<sub>p</sub> = v<sub>f</sub>ΔP", False, "That's for pumping liquid. State 4 is a wet mixture, so the compressor's work is much larger.")], FIRST_SF),
             multi_terms(["ṁh<sub>1</sub>"], ["ṁh<sub>2</sub>"], "Boiler: q<sub>in</sub> = h<sub>2</sub> − h<sub>1</sub> = h<sub>g</sub> − h<sub>f</sub> = h<sub>fg</sub>", keepQin=True,
                         p="Apply the steady-flow first law to the boiler (1→2). Cross out every term that drops."),
             props([("T<sub>sat</sub> at P<sub>H</sub>", H["T"], "°C", "A-5", 0.003, fP(PH)), ("h<sub>fg</sub> at P<sub>H</sub>", H["hfg"], "kJ/kg", "A-5", 0.003, fP(PH)),
                    ("s<sub>f</sub> at P<sub>H</sub>", H["sf"], "kJ/kg·K", "A-5", 0.003, fP(PH)), ("s<sub>g</sub> at P<sub>H</sub>", H["sg"], "kJ/kg·K", "A-5", 0.003, fP(PH)),
                    ("T<sub>sat</sub> at P<sub>L</sub>", L["T"], "°C", "A-5", 0.003, fP(PL)), ("s<sub>f</sub> at P<sub>L</sub>", L["sf"], "kJ/kg·K", "A-5", 0.003, fP(PL)),
                    ("s<sub>fg</sub> at P<sub>L</sub>", L["sfg"], "kJ/kg·K", "A-5", 0.003, fP(PL))]),
             calc([f"T<sub>H</sub> = {num(H['T'], 2)} + 273.15 = {num(TH, 2)} K; T<sub>L</sub> = {num(L['T'], 2)} + 273.15 = {num(TL, 2)} K",
                   f"η<sub>th</sub> = 1 − {num(TL, 2)}/{num(TH, 2)} = <b>{pct(eta):.1f}%</b>",
                   f"q<sub>in</sub> = h<sub>fg</sub> at {fP(PH)} = <b>{num(qin, 2)} kJ/kg</b>; w<sub>net</sub> = ηq<sub>in</sub> = {sg(wn)} kJ/kg",
                   f"x<sub>3</sub> = ({num(H['sg'], 4)} − {num(L['sf'], 4)})/{num(L['sfg'], 4)} = <b>{sg(x3, 4)}</b>",
                   f"x<sub>4</sub> = ({num(H['sf'], 4)} − {num(L['sf'], 4)})/{num(L['sfg'], 4)} = <b>{sg(x4, 4)}</b>"]),
             mc(8, f"The compressor must take in a mixture that is {pct(1 - x4):.0f}% liquid by mass and squeeze it to saturated liquid. Why don't real plants run this cycle?",
                ["Compressing a two-phase mixture is very hard on machinery, the turbine exhaust is wet enough to erode blades, and the top temperature is capped by the critical point; Rankine fixes the first by condensing completely and pumping liquid",
                 "Because Carnot efficiency is lower than Rankine's between the same temperatures", "Because steam can't be used in a Carnot cycle", "Because the heat added inside the dome isn't isothermal"],
                0, "The Rankine cycle gives up a little ideal efficiency to get machines that work: a pump on pure liquid, and superheat (or reheat) to keep the turbine exit dry.")]
    return stem, parts, steps, None, prm(locals())

# ---------------------------------------------------------------- build
def build(nvar=24, seed=20261123):
    out = []
    for T in XT:
        rng = random.Random(seed + sum(map(ord, T["id"])) * 13)
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
        out.append({k: T[k] for k in ("id", "title", "ch", "slot", "pts", "tier", "grp", "note", "us") if T.get(k)} | {"v": vs})
    return out

if __name__ == "__main__":
    tpls = build()
    json.dump(tpls, open(os.path.join(HERE, "final2_templates.json"), "w"), ensure_ascii=False)
    print(len(tpls), [(t["id"], len(t["v"])) for t in tpls])
