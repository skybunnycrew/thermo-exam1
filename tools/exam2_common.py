"""Shared pieces for the Exam 2 guided-problem templates (eight-step format, Matthew's first-law convention)."""
import math

def num(x, d):
    s = f"{x:,.{d}f}" if abs(x) >= 10000 else f"{x:.{d}f}"
    return s.replace("-", "−")

def sg(x, n=4):
    if x == 0: return "0"
    d = max(0, n - 1 - int(math.floor(math.log10(abs(x)))))
    return num(x, d)

def K(Tc): return Tc + 273.15

# ---------------------------------------------------------------- assumptions
LIB = {
    "open":      ("Open system", "Control volume: mass crosses the boundary."),
    "closed":    ("Closed system", "Closed system: no mass crosses the boundary."),
    "steady":    ("Steady flow", "Steady operation: nothing inside the control volume changes with time, so dE<sub>cv</sub>/dt = 0 and the mass flow in equals the mass flow out."),
    "adiabatic": ("Adiabatic", "No heat crosses the boundary (insulated, or the fluid passes through too fast to exchange much heat)."),
    "noshaft":   ("No work", "No shaft, electrical or boundary work crosses the control-volume boundary."),
    "lowke":     ("Negligible ΔKE", "Velocities are low, or about the same in and out, so the kinetic-energy terms drop out."),
    "lowv1":     ("Small inlet velocity", "The inlet velocity is small next to the exit velocity, so its kinetic energy is negligible."),
    "nope":      ("Negligible ΔPE", "Inlet and exit are at about the same height, so the gz terms cancel."),
    "ideal":     ("Ideal gas", "Ideal gas: Pv = RT."),
    "constc":    ("Constant c", "Constant specific heats at room temperature (Table A-2a)."),
    "noble":     ("Noble gas, constant c", "A noble (monatomic) gas: its c<sub>p</sub> and c<sub>v</sub> are constant at any temperature (Table A-2a)."),
    "a17":       ("Variable c, Table A-17", "Large temperature change: air properties from the ideal-gas table, A-17."),
    "steam":     ("Steam tables", "Water properties from the steam tables (A-4 to A-6), in every phase."),
    "r134":      ("R-134a tables", "R-134a properties from its own tables (A-11 to A-13)."),
    "liqT":      ("Liquid ≈ saturated liquid at T", "Liquid water below 5 MPa: h ≈ h<sub>f</sub> at the same temperature (Table A-4)."),
    "liqTr":     ("Liquid ≈ saturated liquid at T", "Subcooled R-134a: h ≈ h<sub>f</sub> at the same temperature (Table A-11)."),
    "shell":     ("No heat to the surroundings", "All the heat leaving one stream goes into the other; none is lost to the surroundings."),
    "isen":      ("Isentropic (ideal) process", "The ideal process is reversible and adiabatic, so s<sub>2s</sub> = s<sub>1</sub>."),
    "cycle":     ("Cyclic device", "The device runs in a cycle: after each cycle it's back where it started, so ΔE<sub>cycle</sub> = 0."),
    "reservoir": ("Thermal reservoirs", "The hot and cold sides act as thermal reservoirs at fixed temperatures."),
    "coldair":   ("Cold-air-standard", "Cold-air-standard assumptions: air is an ideal gas with constant specific heats at 25 °C (k = 1.4)."),
    "airstd":    ("Air-standard, variable c", "Air-standard assumptions with variable specific heats: air is an ideal gas, properties from Table A-17."),
    "intrev":    ("Internally reversible", "Every process in the ideal cycle is internally reversible."),
    "stationary":("Stationary", "Stationary system, so ΔKE = ΔPE = 0."),
    "constv":    ("Constant volume", "Heat addition happens at constant volume, so no boundary work."),
    "constP":    ("Constant pressure", "This process happens at constant pressure."),
    # common wrong ones
    "steamideal":("Steam is an ideal gas", "Steam behaves as an ideal gas: Pv = RT."),
    "r134ideal": ("R-134a is an ideal gas", "R-134a vapor behaves as an ideal gas."),
    "unsteady":  ("Unsteady", "The mass inside changes with time."),
    "isothermal":("Isothermal", "The temperature stays constant."),
    "rev":       ("Reversible device", "The real device is reversible."),
    "cpwater":   ("Water: cΔT", "Liquid water: Δh = cΔT with c = 4.18 kJ/kg·K."),
    "constc_big":("Constant c", "Constant specific heats at room temperature (Table A-2a)."),
}

def assume(givens, finds, opts):
    """opts: list of (id, ok, why) or (id, ok, why, text override)."""
    o = []
    for t in opts:
        aid, ok, w = t[:3]
        s, txt = LIB[aid]
        if len(t) > 3 and t[3]: txt = t[3]
        o.append({"id": aid, "s": s, "t": txt, "ok": ok, "w": w})
    return {"n": 3, "k": "assume", "g": givens, "f": finds, "o": o}

# ---------------------------------------------------------------- energy-balance terms
FIRST_SF = ("Q̇<sub>in</sub> + Ẇ<sub>in</sub> + ∑ṁ(h + V²/2 + gz)<sub>in</sub> − Q̇<sub>out</sub> − Ẇ<sub>out</sub> "
            "− ∑ṁ(h + V²/2 + gz)<sub>out</sub> = dE<sub>cv</sub>/dt")
FIRST_CL = "Q<sub>in</sub> + W<sub>in</sub> − Q<sub>out</sub> − W<sub>out</sub> = ΔU + ΔKE + ΔPE"
FIRST_CYC = "Q̇<sub>in</sub> + Ẇ<sub>in</sub> − Q̇<sub>out</sub> − Ẇ<sub>out</sub> = dE/dt"

def term(id_, h, side, sign, strike=False, ok=(), w=""):
    return {"id": id_, "h": h, "side": side, "sign": sign, "strike": strike, "ok": list(ok), "w": w}

def sf_single(spec, res, p="Cross out every term your assumptions remove, and pick the reason for each."):
    """Single-stream steady-flow balance. spec maps term id -> (reason ids, why) for struck terms."""
    labels = [("Qin", "Q̇<sub>in</sub>", "L", "+"), ("Win", "Ẇ<sub>in</sub>", "L", "+"),
              ("mh1", "ṁh<sub>1</sub>", "L", "+"), ("mke1", "ṁV<sub>1</sub>²/2", "L", "+"), ("mpe1", "ṁgz<sub>1</sub>", "L", "+"),
              ("Qout", "Q̇<sub>out</sub>", "L", "−"), ("Wout", "Ẇ<sub>out</sub>", "L", "−"),
              ("mh2", "ṁh<sub>2</sub>", "L", "−"), ("mke2", "ṁV<sub>2</sub>²/2", "L", "−"), ("mpe2", "ṁgz<sub>2</sub>", "L", "−"),
              ("dE", "dE<sub>cv</sub>/dt", "R", "")]
    terms = []
    for i, h, side, sign in labels:
        if i in spec:
            ok, w = spec[i]; terms.append(term(i, h, side, sign, True, ok, w))
        else:
            terms.append(term(i, h, side, sign))
    return {"n": 5, "k": "strike", "p": p, "terms": terms, "res": res}

def strike_custom(terms, res, p="Cross out every term your assumptions remove, and pick the reason for each."):
    return {"n": 5, "k": "strike", "p": p, "terms": terms, "res": res}

def self_step(m):
    return {"n": 1, "k": "self", "p": "In one sentence: what are you finding, and for which system?", "m": m}

def mc(n, p, o, a, w):
    return {"n": n, "k": "mc", "p": p, "o": o, "a": a, "w": w}

def dia(p, kinds, a, w):
    return {"n": 2, "k": "dia", "p": p, "o": [{"kind": k} for k in kinds], "a": a, "w": w}

def multi(opts, m, p="Select every equation you will need."):
    return {"n": 4, "k": "multi", "p": p, "o": [{"t": t, "ok": ok, "w": w} for t, ok, w in opts], "m": m}

def props(rows):
    return {"n": 6, "k": "props", "rows": [{"h": h, "v": v, "u": u, "t": t, "tol": tol, **({"r": r} if r else {})} for h, v, u, t, tol, r in rows]}

def calc(lines):
    return {"n": 7, "k": "calc", "m": lines}

def part(id_, q, u, ans, tol, pts, diag=(), key=(), floor=0.003):
    """Tolerance is tightened to half the distance to any listed wrong answer, so a known slip is
    never marked right. `key` slips must be distinguishable or the variant is rejected."""
    a = abs(ans)
    for v in key:
        rel = abs(v - ans) / a
        assert rel / 2 >= floor, ("trap too close", id_, rel)
        tol = min(tol, rel / 2)
    d = []
    for v, m in diag:
        if v is None or not math.isfinite(v): continue
        rel = abs(v - ans) / a
        if rel / 2 < floor: continue
        if any(abs(v - x["v"]) <= 1e-9 * max(1, abs(v)) for x in d): continue
        tol = min(tol, rel / 2)
        d.append({"v": float(f"{v:.6g}"), "m": m})
    return {"id": id_, "q": q, "u": u, "ans": float(f"{ans:.6g}"), "tol": round(tol, 4), "pts": pts, "kind": "num", "diag": d}

OPEN_MC = ["Open, steady flow: mass crosses the boundary, and nothing inside changes with time",
           "Closed: the device has fixed walls, so no mass crosses",
           "Open, unsteady: the mass inside builds up over time",
           "Isolated: neither mass nor energy crosses"]
def open_step(dev):
    return mc(2, f"What kind of system is the {dev}?", OPEN_MC, 0,
              f"Mass crosses the boundary, so the {dev} is a control volume (open system). Walls don't decide it; mass does. "
              "It runs at a steady condition, so nothing inside changes with time.")
