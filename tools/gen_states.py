"""Generate Exam 2 property-drill states for water and R-134a (with entropy, tricky and in-device items)."""
import json, random, math
import CoolProp.CoolProp as CP
from tables import WATER, R, fmt, fmt_P, fmt_T, rdec, rsig

random.seed(20261120)

UNIT = {"v": "m³/kg", "u": "kJ/kg", "h": "kJ/kg", "s": "kJ/kg·K", "T": "°C", "P": "kPa", "x": ""}
SYM = {"v": "v", "u": "u", "h": "h", "s": "s", "T": "T", "P": "P", "x": "x"}
def f_(k): return f"{k}<sub>f</sub>"
def g_(k): return f"{k}<sub>g</sub>"
def fg_(k): return f"{k}<sub>fg</sub>"
def lin(x, x0, x1, y0, y1): return y0 + (x - x0) / (x1 - x0) * (y1 - y0)
def U(k): return " " + UNIT[k] if UNIT[k] else ""
def M(s): return s.replace("-", "−")

def tolfor(ask, interp, double=False):
    if ask == "x": return 0.01
    if double: return 0.015
    return 0.01 if interp else 0.005

def atolfor(ask):
    return {"T": 1.0, "x": 0.004, "s": 0.002, "u": 0.3, "h": 0.3, "v": 0.0, "P": 0.0}[ask]

def true_pt(F, P=None, T=None, q=None):
    """Point for the T-v plot (true values)."""
    if q is not None and P is not None:
        Tt = F.Tsat_true(P); v = 1 / CP.PropsSI("D", "P", P * 1e3, "Q", q, F.cp)
        return {"T": round(Tt, 3), "v": float(f"{v:.6g}")}
    if q is not None and T is not None:
        v = 1 / CP.PropsSI("D", "T", T + 273.15, "Q", q, F.cp)
        return {"T": round(T, 3), "v": float(f"{v:.6g}")}
    v = 1 / CP.PropsSI("D", "T", T + 273.15, "P", P * 1e3, F.cp)
    return {"T": round(T, 3), "v": float(f"{v:.6g}")}

def pkey(P):
    return (f"{P:.4f}".rstrip("0").rstrip("."))

ITEMS = []
def add(F, **kw):
    it = dict(fluid=F.key, ctx="", tags=[], interp=False)
    it.update(kw)
    it.setdefault("atol", atolfor(it["ask"]))
    it.setdefault("tol", tolfor(it["ask"], it["interp"]))
    it["pk"] = pkey(it["P"])
    skip = it.pop("skip", [])
    if skip:
        d = min(abs(v - it["answer"]) for v in skip)
        rel = 0.5 * d / abs(it["answer"])
        assert rel >= 0.0015, "shortcut too close to answer"
        it["tol"] = min(it["tol"], rel)
        it["atol"] = min(it["atol"], 0.5 * d)
    # drop diagnoses that are indistinguishable from the answer
    a = it["answer"]; t = max(it["tol"] * abs(a), it["atol"])
    seen = []
    keep = []
    for d in it.get("diag", []):
        if abs(d["v"] - a) <= max(2 * t, 0.012 * abs(a)): continue
        if any(abs(d["v"] - s) <= 1e-9 for s in seen): continue
        seen.append(d["v"]); keep.append(d)
    it["diag"] = keep
    ITEMS.append(it)
    return it

def sat_word(F, by):
    return f"Table {F.TT}" if by == "T" else f"Table {F.PT}"

# ------------------------------------------------------------------ superheated helpers
def sh_rows(F, P):
    """Rows of a superheated block: Sat row first, then the grid temperatures."""
    rows = [dict(F.shsat(P), sat=True)]
    for T in F.SH[P]:
        rows.append(dict(F.sh(P, T), sat=False))
    return rows

def bracket(rows, key, val):
    for a, b in zip(rows, rows[1:]):
        if (val - a[key]) * (val - b[key]) <= 0 and a[key] != b[key]:
            return a, b
    return None

def rowname(F, r):
    return "saturated-vapor (Sat.) row" if r.get("sat") else f"{fmt_T(r['T'])} row"

def blockname(F, P):
    return f"the P = {fmt_P(P)} block" + (f" (T<sub>sat</sub> = {fmt(F.satP(P)['T'], 2)} °C)" if True else "")

# =================================================================== A: given T and P
def item_TP(F, P, T, ask, tags=(), ctx="", ctxwhy=None):
    sat = F.satP(P) if P in F.P_GRID else None
    Ts_true = F.Tsat_true(P)
    why = list(ctxwhy or [])
    if T < Ts_true - 0.5:
        # compressed liquid
        if F is WATER and P >= 5000 and P in WATER.CL_P and T in WATER.CL_T:
            row = WATER.cl(P, T)
            why += [f"Compare T = {fmt_T(T)} with T<sub>sat</sub> at {fmt_P(P)} = {fmt(WATER.satP(P)['T'], 2)} °C (Table A-5).",
                    "T &lt; T<sub>sat</sub>, so the water is a <b>compressed liquid</b>.",
                    f"At {fmt_P(P)} the compressed-liquid table has this state: use Table A-7, the P = {fmt_P(P)} block, {fmt_T(T)} row: {ask} = {WATER.pf(ask, row[ask], 'A-7')}{U(ask)}."]
            st = WATER.satT(T)
            diag = [{"v": st[ask + "f"], "m": f"That is {f_(ask)} at {fmt_T(T)} (Table A-4), the low-pressure shortcut. At {fmt_P(P)}, Table A-7 has the actual compressed-liquid value: use it."}]
            if ask == "h":
                pass
            sp = WATER.satP(P)
            diag.append({"v": sp[ask + "f"], "m": f"That is {f_(ask)} at the pressure. A compressed liquid is set by its temperature: read Table A-7 at {fmt_T(T)}."})
            return add(F, given=[["T", T, "°C"], ["P", P, "kPa"]], phase="cl", table="A-7", ask=ask,
                       answer=row[ask], why=why, diag=diag, P=P, pt=true_pt(F, P=P, T=T), tags=list(tags) + ["a7"], ctx=ctx)
        st = F.satT(T)
        tsatP = fmt(sat["T"], 2) if sat else fmt(Ts_true, 2)
        why += [f"Compare T = {fmt_T(T)} with T<sub>sat</sub> at {fmt_P(P)} = {tsatP} °C (Table {F.PT}).",
                f"T &lt; T<sub>sat</sub>, so the {F.label if F is R else 'water'} is a <b>compressed liquid</b>."]
        if F is WATER:
            why.append(f"Below 5 MPa, treat it as saturated liquid at the same <b>temperature</b>: {ask} ≈ {f_(ask)}@{fmt_T(T)} = {F.pf(ask, st[ask + 'f'], F.TT)}{U(ask)} (Table A-4).")
        else:
            why.append(f"R-134a has no compressed-liquid table, so treat it as saturated liquid at the same <b>temperature</b>: {ask} ≈ {f_(ask)}@{fmt_T(T)} = {F.pf(ask, st[ask + 'f'], F.TT)}{U(ask)} (Table A-11).")
        diag = []
        if sat:
            diag.append({"v": sat[ask + "f"], "m": f"That is {f_(ask)} at the <b>pressure</b>. For a compressed liquid, use the saturated-liquid value at the <b>temperature</b> (Table {F.TT})."})
            diag.append({"v": sat[ask + "g"], "m": f"That is {g_(ask)} at the pressure, a vapor value. T &lt; T<sub>sat</sub> means liquid."})
        diag.append({"v": st[ask + "g"], "m": f"That is {g_(ask)}@{fmt_T(T)}, the saturated-<b>vapor</b> value. This state is liquid: use {f_(ask)}."})
        tol = 0.015 if ask == "h" else 0.005
        return add(F, given=[["T", T, "°C"], ["P", P, "kPa"]], phase="cl", table=F.TT, ask=ask,
                   answer=st[ask + "f"], tol=tol, why=why, diag=diag, P=P, pt=true_pt(F, P=P, T=T), tags=list(tags), ctx=ctx)
    # superheated
    rows = sh_rows(F, P)
    why += [f"Compare T = {fmt_T(T)} with T<sub>sat</sub> at {fmt_P(P)} = {fmt(rows[0]['T'], 2)} °C (Table {F.PT}).",
            f"T &gt; T<sub>sat</sub>, so the {'water' if F is WATER else 'R-134a'} is <b>superheated vapor</b>: go to Table {F.SHT}, the P = {fmt_P(P)} block."]
    exact = [r for r in rows if not r["sat"] and r["T"] == T]
    sp = F.satP(P) if P in F.P_GRID else None
    g = rows[0]
    diag = [{"v": g[ask], "m": f"That is {g_(ask)}, the saturated-vapor value. This vapor is hotter than T<sub>sat</sub>, so it is superheated (Table {F.SHT})."}]
    if exact:
        r = exact[0]; ans = r[ask]; interp = False
        why.append(f"Read the {fmt_T(T)} row: {ask} = {F.pf(ask, ans, F.SHT)}{U(ask)}.")
    else:
        a, b = bracket(rows, "T", T)
        ans = lin(T, a["T"], b["T"], a[ask], b[ask]); interp = True
        why.append(f"{fmt_T(T)} sits between the {fmt_T(a['T']) if not a['sat'] else 'Sat. (' + fmt(a['T'], 2) + ' °C)'} and {fmt_T(b['T'])} rows ({ask} = {F.pf(ask, a[ask], F.SHT)} and {F.pf(ask, b[ask], F.SHT)}). "
                   f"Interpolate: {ask} = {F.pf(ask, a[ask], F.SHT)} + ({M(fmt(T, 2 if T % 1 else 0))} − {M(fmt(a['T'], 2 if a['T'] % 1 else 0))})/({M(fmt(b['T'], 0))} − {M(fmt(a['T'], 2 if a['T'] % 1 else 0))}) × ({F.pf(ask, b[ask], F.SHT)} − {F.pf(ask, a[ask], F.SHT)}) = {F.pf(ask, ans, F.SHT) if ask != 'v' else fmt(ans, n=5)}{U(ask)}.")
        near = min((a, b), key=lambda r: abs(r["T"] - T))
        diag.append({"v": near[ask], "m": f"That is the nearest row's value. {fmt_T(T)} is between two rows: interpolate."})
    skip = [] if exact else [a[ask], b[ask]]
    if F is R:
        st = F.satT(T) if T in F.T_GRID else None
        if st: diag.append({"v": st[ask + "g"], "m": f"That is {g_(ask)} at {fmt_T(T)} (Table A-11). At this pressure the R-134a is superheated: use Table A-13."})
    return add(F, given=[["T", T, "°C"], ["P", P, "kPa"]], phase="sh", table=F.SHT, ask=ask, answer=ans,
               interp=interp, why=why, diag=diag, P=P, pt=true_pt(F, P=P, T=T), tags=list(tags), ctx=ctx, skip=skip)

# =================================================================== B: quality given
def item_x(F, by, val, x, ask, tags=(), ctx="", ctxwhy=None):
    st = F.satT(val) if by == "T" else F.satP(val)
    tbl = F.TT if by == "T" else F.PT
    P = st["P"] if by == "T" else val
    lab = fmt_T(val) if by == "T" else fmt_P(val)
    why = list(ctxwhy or [])
    why += [f"0 &lt; x &lt; 1, so the state is a <b>saturated mixture</b>. Go to Table {tbl} at {lab}."]
    diag = []
    if ask in ("T", "P"):
        k = "P" if by == "T" else "T"
        ans = st[k]
        why.append(f"In a mixture, T and P are tied together: {'P = P<sub>sat</sub>' if k == 'P' else 'T = T<sub>sat</sub>'}@{lab} = {F.pf(k, ans, tbl)}{U(k)}. The quality doesn't change it.")
        given = [[by, val, UNIT[by]], ["x", x, ""]]
        return add(F, given=given, phase="mix", table=tbl, ask=ask, answer=ans, why=why, diag=diag, P=P,
                   pt=true_pt(F, P=P, q=x) if by == "P" else true_pt(F, T=val, q=x), tags=list(tags), ctx=ctx)
    yf, yg = st[ask + "f"], st[ask + "g"]
    yfg = st[ask + "fg"] if ask != "v" else yg - yf
    ans = yf + x * yfg
    if ask == "v":
        why.append(f"v = v<sub>f</sub> + x(v<sub>g</sub> − v<sub>f</sub>) = {F.pf('v', yf, tbl)} + {x}({F.pf('v', yg, tbl)} − {F.pf('v', yf, tbl)}) = {fmt(ans, n=4)} m³/kg.")
    else:
        why.append(f"{ask} = {f_(ask)} + x{fg_(ask)} = {F.pf(ask, yf, tbl)} + {x}({F.pf(ask, yfg, tbl)}) = {F.pf(ask, ans, tbl) if ask != 's' else fmt(ans, 4)}{U(ask)}.")
    diag = [{"v": x * yg, "m": f"That is x·{g_(ask)}. The liquid part carries {f_(ask)} too: {ask} = {f_(ask)} + x{fg_(ask)}."},
            {"v": yf + (1 - x) * yfg, "m": f"That uses 1 − x. Quality is the <b>vapor</b> mass fraction, so x multiplies {fg_(ask)}."},
            {"v": yf + x * yg, "m": f"That adds x·{g_(ask)} instead of x·{fg_(ask)}."}]
    other = F.satP(val) if by == "T" and val in F.P_GRID else None
    given = [[by, val, UNIT[by]], ["x", x, ""]]
    return add(F, given=given, phase="mix", table=tbl, ask=ask, answer=ans, why=why, diag=diag, P=P,
               pt=true_pt(F, P=P, q=x) if by == "P" else true_pt(F, T=val, q=x), tags=list(tags), ctx=ctx)

# =================================================================== C: in-dome property given, find x
def item_mix_from(F, by, val, gk, gval, ask, tags=(), ctx="", ctxwhy=None, given_disp=None):
    st = F.satT(val) if by == "T" else F.satP(val)
    tbl = F.TT if by == "T" else F.PT
    P = st["P"] if by == "T" else val
    lab = fmt_T(val) if by == "T" else fmt_P(val)
    yf, yg = st[gk + "f"], st[gk + "g"]
    yfg = st[gk + "fg"] if gk != "v" else yg - yf
    x = (gval - yf) / yfg
    assert 0 < x < 1, (F.key, by, val, gk, gval)
    why = list(ctxwhy or [])
    why += [f"Compare {gk} = {gval} with Table {tbl} at {lab}: {f_(gk)} = {F.pf(gk, yf, tbl)}, {g_(gk)} = {F.pf(gk, yg, tbl)}.",
            f"{f_(gk)} &lt; {gk} &lt; {g_(gk)}, so the state is a <b>saturated mixture</b>.",
            f"x = ({gk} − {f_(gk)})/{fg_(gk)} = ({gval} − {F.pf(gk, yf, tbl)})/{F.pf(gk, yfg, tbl) if gk != 'v' else fmt(yfg, n=5)} = {fmt(x, 4)}."]
    diag = [{"v": 1 - x, "m": "That is 1 − x, the liquid mass fraction."},
            {"v": gval / yg, "m": f"That is {gk}/{g_(gk)}. Subtract {f_(gk)} first and divide by {fg_(gk)}."},
            {"v": (gval - yf) / yg, "m": f"Divide by {fg_(gk)}, not {g_(gk)}."}]
    if ask == "x":
        ans = x
    elif ask in ("T", "P"):
        k = ask
        ans = st[k]
        why = why[:len(ctxwhy or []) + 2] + [f"In a mixture, {'P = P<sub>sat</sub>' if k == 'P' else 'T = T<sub>sat</sub>'}@{lab} = {F.pf(k, ans, tbl)}{U(k)}."]
        diag = []
    else:
        af, ag = st[ask + "f"], st[ask + "g"]
        afg = st[ask + "fg"] if ask != "v" else ag - af
        ans = af + x * afg
        why.append(f"Then {ask} = {f_(ask)} + x{fg_(ask)} = {F.pf(ask, af, tbl)} + ({fmt(x, 4)})({F.pf(ask, afg, tbl) if ask != 'v' else fmt(afg, n=5)}) = {fmt(ans, 4) if ask == 's' else (fmt(ans, n=4) if ask == 'v' else fmt(ans, 1))}{U(ask)}.")
        diag = [{"v": af + (1 - x) * afg, "m": "That uses 1 − x where x belongs."},
                {"v": ag, "m": f"That is {g_(ask)}. The state is a mixture: find x first, then {ask} = {f_(ask)} + x{fg_(ask)}."}]
        tags = list(tags) + ["two-step"]
    given = [[by, val, UNIT[by]], [gk, gval, UNIT[gk]]]
    q = x
    return add(F, given=given, phase="mix", table=tbl, ask=ask, answer=ans, why=why, diag=diag, P=P,
               pt=true_pt(F, P=P, q=q) if by == "P" else true_pt(F, T=val, q=q), tags=list(tags), ctx=ctx)

# =================================================================== D: saturated liquid / vapor
def item_satstate(F, by, val, which, ask, tags=(), ctx="", ctxwhy=None):
    st = F.satT(val) if by == "T" else F.satP(val)
    tbl = F.TT if by == "T" else F.PT
    P = st["P"] if by == "T" else val
    lab = fmt_T(val) if by == "T" else fmt_P(val)
    fg = "f" if which == "liquid" else "g"
    why = list(ctxwhy or [])
    if ask in ("T", "P"):
        ans = st[ask]
        why += [f"Saturated {which} sits on the dome, so T and P are tied: read Table {tbl} at {lab}.",
                f"{'P<sub>sat</sub>' if ask == 'P' else 'T<sub>sat</sub>'} = {F.pf(ask, ans, tbl)}{U(ask)}."]
        diag = []
    else:
        ans = st[ask + fg]
        why += [f"Saturated {which}: go to Table {tbl} at {lab}.",
                f"Read the {'liquid' if fg == 'f' else 'vapor'} column: {ask}<sub>{fg}</sub> = {F.pf(ask, ans, tbl)}{U(ask)}."]
        other = "g" if fg == "f" else "f"
        diag = [{"v": st[ask + other], "m": f"That is {ask}<sub>{other}</sub>, the saturated-{'vapor' if other == 'g' else 'liquid'} value. This state is saturated {which}."}]
        if ask != "v":
            diag.append({"v": st[ask + "fg"], "m": f"That is {fg_(ask)}, the change from liquid to vapor, not the value itself."})
    given = [[by, val, UNIT[by]], ["state", f"saturated {which}", ""]]
    q = 0 if which == "liquid" else 1
    return add(F, given=given, phase="sl" if q == 0 else "sv", table=tbl, ask=ask, answer=ans, why=why, diag=diag, P=P,
               pt=true_pt(F, P=P, q=q) if by == "P" else true_pt(F, T=val, q=q), tags=list(tags), ctx=ctx)

# =================================================================== E: superheated inverse (P and one of v,u,h,s)
def item_sh_inverse(F, P, gk, gval, ask, tags=(), ctx="", ctxwhy=None):
    rows = sh_rows(F, P)
    g = rows[0]
    br = bracket(rows, gk, gval)
    assert br, (F.key, P, gk, gval)
    a, b = br
    T = lin(gval, a[gk], b[gk], a["T"], b["T"])
    tbl = F.SHT
    why = list(ctxwhy or [])
    sp = F.satP(P) if P in F.P_GRID else None
    why += [f"Compare {gk} = {gval} with {g_(gk)} at {fmt_P(P)} = {F.pf(gk, g[gk], F.PT)} (Table {F.PT}).",
            f"{gk} &gt; {g_(gk)}, so it is <b>superheated vapor</b>: go to Table {tbl}, the P = {fmt_P(P)} block, and find where {gk} = {gval} falls.",
            f"It sits between the {'Sat.' if a['sat'] else fmt_T(a['T'])} row ({gk} = {F.pf(gk, a[gk], tbl)}) and the {fmt_T(b['T'])} row ({gk} = {F.pf(gk, b[gk], tbl)})."]
    frac = (gval - a[gk]) / (b[gk] - a[gk])
    if ask == "T":
        ans = T
        why.append(f"Interpolate for T: T = {M(fmt(a['T'], 2 if a['T'] % 1 else 0))} + ({gval} − {F.pf(gk, a[gk], tbl)})/({F.pf(gk, b[gk], tbl)} − {F.pf(gk, a[gk], tbl)}) × ({fmt(b['T'], 0)} − {fmt(a['T'], 2 if a['T'] % 1 else 0)}) = {fmt(T, 1)} °C.")
        near = min((a, b), key=lambda r: abs(r[gk] - gval))
        skip = [a["T"], b["T"]]
        diag = [{"v": near["T"], "m": "That is the nearest row's temperature. Interpolate between the two rows."},
                {"v": g["T"], "m": "That is T<sub>sat</sub>. The state is superheated, so T is above it."}]
    else:
        ans = a[ask] + frac * (b[ask] - a[ask])
        why.append(f"Use the same fraction, ({gval} − {F.pf(gk, a[gk], tbl)})/({F.pf(gk, b[gk], tbl)} − {F.pf(gk, a[gk], tbl)}) = {fmt(frac, 3)}, for {ask}: {ask} = {F.pf(ask, a[ask], tbl)} + {fmt(frac, 3)} × ({F.pf(ask, b[ask], tbl)} − {F.pf(ask, a[ask], tbl)}) = {fmt(ans, n=4) if ask == 'v' else (fmt(ans, 4) if ask == 's' else fmt(ans, 1))}{U(ask)}.")
        diag = [{"v": g[ask], "m": f"That is {g_(ask)}. The state is past the saturated-vapor line: it's superheated."}]
        near = min((a, b), key=lambda r: abs(r[gk] - gval))
        diag.append({"v": near[ask], "m": "That is the nearest row's value. Interpolate between the two rows."})
        skip = [a[ask], b[ask]]
        tags = list(tags) + ["two-step"]
    Tt = CP.PropsSI("T", "P", P * 1e3, {"h": "H", "s": "S", "u": "U", "v": "D"}[gk], (gval * 1e3 if gk != "v" else 1 / gval), F.cp) - 273.15
    given = [["P", P, "kPa"], [gk, gval, UNIT[gk]]]
    return add(F, given=given, phase="sh", table=tbl, ask=ask, answer=ans, interp=True, why=why, diag=diag, P=P,
               pt=true_pt(F, P=P, T=Tt), tags=list(tags) + ["inverse"], ctx=ctx, skip=skip)

# =================================================================== F: T and v superheated, find P (across blocks)
def item_Tv_findP(F, T, v, Pa, Pb):
    ra, rb = F.sh(Pa, T), F.sh(Pb, T)
    assert (v - ra["v"]) * (v - rb["v"]) < 0
    P = lin(v, ra["v"], rb["v"], Pa, Pb)
    why = [f"At {fmt_T(T)}, check the dome first: v<sub>g</sub>@{fmt_T(T)} is far smaller than {v} m³/kg{' (Table A-4)' if F is WATER else ' (Table A-11)'}, so the state is <b>superheated vapor</b>." if T in F.T_GRID else
           f"T = {fmt_T(T)} is above the temperature where v = {v} m³/kg could be saturated at any table pressure near here, so the state is <b>superheated vapor</b> (check: at {fmt_P(Pa)}, T<sub>sat</sub> = {fmt(F.satP(Pa)['T'], 2)} °C).",
           f"In Table {F.SHT}, look across the blocks at the {fmt_T(T)} row: at {fmt_P(Pa)}, v = {F.pf('v', ra['v'], F.SHT)}; at {fmt_P(Pb)}, v = {F.pf('v', rb['v'], F.SHT)}.",
           f"v = {v} falls between them. Interpolate in P: P = {fmt(Pa, 0)} + ({v} − {F.pf('v', ra['v'], F.SHT)})/({F.pf('v', rb['v'], F.SHT)} − {F.pf('v', ra['v'], F.SHT)}) × ({fmt(Pb, 0)} − {fmt(Pa, 0)}) = {fmt(P, n=4)} kPa.",
           "Interpolating across pressure blocks is rougher than within one block, so expect a bit more spread in answers."]
    diag = [{"v": Pa, "m": "That is one of the bracketing block pressures. Interpolate between the blocks."},
            {"v": Pb, "m": "That is one of the bracketing block pressures. Interpolate between the blocks."}]
    Ptrue = CP.PropsSI("P", "T", T + 273.15, "D", 1 / v, F.cp) / 1e3
    return add(F, given=[["T", T, "°C"], ["v", v, UNIT["v"]]], phase="sh", table=F.SHT, ask="P", answer=P, tol=0.02,
               interp=True, why=why, diag=diag, P=round(Ptrue, 2), pt=true_pt(F, P=Ptrue, T=T), tags=["tricky", "inverse", "across-blocks"])

# =================================================================== G: double interpolation
def item_double(F, P, Pa, Pb, T, ask):
    def at(Pblk):
        rows = sh_rows(F, Pblk)
        ex = [r for r in rows if not r["sat"] and r["T"] == T]
        if ex: return ex[0][ask], f"read the {fmt_T(T)} row"
        a, b = bracket(rows, "T", T)
        return lin(T, a["T"], b["T"], a[ask], b[ask]), f"interpolate to {fmt_T(T)}, between the {fmt_T(a['T'])} and {fmt_T(b['T'])} rows"
    ya, la = at(Pa); yb, lb = at(Pb)
    ans = lin(P, Pa, Pb, ya, yb)
    why = [f"T<sub>sat</sub> at {fmt_P(P)} is below {fmt_T(T)}, so the state is <b>superheated vapor</b>. But {fmt_P(P)} has no block in Table {F.SHT}.",
           f"Step 1: in the {fmt_P(Pa)} block, {la}: {ask} = {fmt(ya, n=5) if ask == 'v' else fmt(ya, 4 if ask == 's' else 2)}.",
           f"Step 2: in the {fmt_P(Pb)} block, {lb}: {ask} = {fmt(yb, n=5) if ask == 'v' else fmt(yb, 4 if ask == 's' else 2)}.",
           f"Step 3: interpolate between the blocks in P: {ask} = {fmt(ya, n=5) if ask == 'v' else fmt(ya, 4 if ask == 's' else 2)} + ({fmt(P, 0)} − {fmt(Pa, 0)})/({fmt(Pb, 0)} − {fmt(Pa, 0)}) × ({fmt(yb, n=5) if ask == 'v' else fmt(yb, 4 if ask == 's' else 2)} − {fmt(ya, n=5) if ask == 'v' else fmt(ya, 4 if ask == 's' else 2)}) = {fmt(ans, n=4) if ask == 'v' else fmt(ans, 4 if ask == 's' else 1)}{U(ask)}."]
    diag = [{"v": ya, "m": f"That is the {fmt_P(Pa)} block's value. {fmt_P(P)} is between blocks: interpolate in P too."},
            {"v": yb, "m": f"That is the {fmt_P(Pb)} block's value. {fmt_P(P)} is between blocks: interpolate in P too."}]
    return add(F, given=[["T", T, "°C"], ["P", P, "kPa"]], phase="sh", table=F.SHT, ask=ask, answer=ans, tol=0.015,
               interp=True, why=why, diag=diag, P=P, pt=true_pt(F, P=P, T=T), tags=["tricky", "double"], skip=[ya, yb])

# =================================================================== builders
def pick(seq): return random.choice(seq)

def gen_regular(F, n_target):
    asks_sh = ["v", "u", "h", "s"]
    out0 = len(ITEMS)
    Tg = [t for t in F.T_GRID if (F is WATER and 10 <= t <= 300) or (F is R and -30 <= t <= 44)]
    Pg = [p for p in F.P_GRID if (F is WATER and 10 <= p <= 8000) or (F is R and 80 <= p <= 1600)]
    tries = 0
    while len(ITEMS) - out0 < n_target and tries < 20000:
        tries += 1
        kind = random.choices(["cl", "sh", "shi", "xP", "xT", "mixP", "mixT", "sat"], [2, 4, 3, 2, 2, 3, 2, 2])[0]
        try:
            if kind == "cl":
                T = pick([t for t in Tg if t <= (200 if F is WATER else 44)])
                Ps = F.Psat_true(T)
                cands = [p for p in Pg if p > Ps * 1.25 and (F is R or p < 5000)]
                if not cands: continue
                P = pick(cands); item_TP(F, P, T, pick(["v", "u", "h", "s"]))
            elif kind in ("sh", "shi"):
                P = pick(list(F.SH.keys()))
                rows = F.SH[P]
                if F is R and P == 60: rows = [t for t in rows if t >= -10]
                if kind == "sh":
                    T = pick(rows[1:] if len(rows) > 1 else rows)
                else:
                    i = random.randrange(1, len(rows) - 1)
                    lo, hi = rows[i], rows[i + 1]
                    step = 1 if F is R else 5
                    opts = [t for t in range(lo + step, hi, step) if t % (2 if F is R else 5) == 0 and t not in (lo, hi)]
                    if not opts: continue
                    T = pick(opts)
                item_TP(F, P, T, pick(asks_sh))
            elif kind == "xP":
                P = pick(Pg); x = pick([0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.88, 0.9, 0.92, 0.95, 0.97])
                item_x(F, "P", P, x, pick(["v", "u", "h", "s", "s", "T"]))
            elif kind == "xT":
                T = pick(Tg); x = pick([0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 0.95])
                item_x(F, "T", T, x, pick(["v", "u", "h", "s", "P"]))
            elif kind in ("mixP", "mixT"):
                by = "P" if kind == "mixP" else "T"
                val = pick(Pg) if by == "P" else pick(Tg)
                st = F.satP(val) if by == "P" else F.satT(val)
                gk = pick(["v", "u", "h", "s", "s", "h"])
                x = random.uniform(0.08, 0.93)
                yf, yg = st[gk + "f"], st[gk + "g"]
                gval = yf + x * (yg - yf)
                gval = float(fmt(gval, 4 if gk == "s" else (1 if gk in "uh" else None), n=(4 if gk == "v" else None)).replace(",", "").replace("−", "-")) if gk != "v" else rsig(gval, 4)
                ask = random.choices(["x", "x", "x", "s" if gk != "s" else "h", "T" if by == "P" else "P"], [3, 3, 3, 2, 1])[0]
                item_mix_from(F, by, val, gk, gval, ask)
            elif kind == "sat":
                by = pick(["T", "P"]); val = pick(Tg) if by == "T" else pick(Pg)
                item_satstate(F, by, val, pick(["liquid", "vapor"]), pick(["v", "u", "h", "s", "s", "T" if by == "P" else "P"]))
        except AssertionError:
            continue

def gen_sh_inverse(F, n):
    k0 = len(ITEMS)
    while len(ITEMS) - k0 < n:
        P = pick(list(F.SH.keys()))
        rows = sh_rows(F, P)
        if F is R and P == 60: rows = [r for r in rows if r["sat"] or r["T"] >= -10]
        rows = rows[1:]  # stay away from the Sat row in inverse lookups
        if len(rows) < 3: continue
        i = random.randrange(0, len(rows) - 1)
        a, b = rows[i], rows[i + 1]
        gk = pick(["h", "s", "u", "h", "s", "v"])
        f = random.uniform(0.15, 0.85)
        gv = a[gk] + f * (b[gk] - a[gk])
        gv = round(gv, 4 if gk == "s" else (1 if gk in "uh" else 6))
        if gk == "v": gv = rsig(gv, 4)
        ask = random.choices(["T", "h" if gk != "h" else "s", "v" if gk != "v" else "u"], [5, 2, 1])[0]
        try:
            item_sh_inverse(F, P, gk, gv, ask)
        except AssertionError:
            pass

# ---------------- device contexts ----------------
def water_turbine(n):
    k0 = len(ITEMS)
    while len(ITEMS) - k0 < n:
        P1 = pick([3000, 5000, 8000, 10000]); T1 = pick([t for t in WATER.SH[P1] if t >= 400 and t <= 700])
        r1 = WATER.sh(P1, T1); s1 = r1["s"]
        P2 = pick([10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200, 300, 400, 600, 800, 1000, 1200, 1400])
        sp = WATER.satP(P2)
        ctx = f"Steam enters an adiabatic, reversible (isentropic) turbine at {fmt_P(P1)} and {fmt_T(T1)} and leaves at {fmt_P(P2)}."
        cw = [f"Inlet: superheated at {fmt_P(P1)}, {fmt_T(T1)} (Table A-6): s<sub>1</sub> = {fmt(s1, 4)} kJ/kg·K.",
              f"Isentropic means s<sub>2</sub> = s<sub>1</sub> = {fmt(s1, 4)} kJ/kg·K. The exit state is fixed by P<sub>2</sub> and s<sub>2</sub>."]
        try:
            if s1 < sp["sg"]:
                item_mix_from(WATER, "P", P2, "s", s1, pick(["x", "h", "h"]), tags=["tricky", "device"], ctx=ctx, ctxwhy=cw)
            elif P2 in WATER.SH:
                item_sh_inverse(WATER, P2, "s", s1, pick(["T", "h"]), tags=["tricky", "device"], ctx=ctx, ctxwhy=cw)
        except AssertionError:
            pass

def water_throttle(n):
    k0 = len(ITEMS)
    while len(ITEMS) - k0 < n:
        kind = pick(["liq", "liq", "calor"])
        if kind == "liq":
            P1 = pick([1000, 1200, 1400, 1500, 2000, 3000, 4000]); s1 = WATER.satP(P1); h1 = s1["hf"]
            P2 = pick([100, 125, 150, 200, 250, 300, 400, 500])
            ctx = f"Saturated liquid water at {fmt_P(P1)} is throttled through a valve to {fmt_P(P2)}."
            cw = [f"Inlet: saturated liquid at {fmt_P(P1)}: h<sub>1</sub> = h<sub>f</sub> = {fmt(h1, 2)} kJ/kg (Table A-5).",
                  "A throttling valve has no work, negligible heat transfer and negligible ΔKE, so the first law gives h<sub>2</sub> = h<sub>1</sub>."]
            item_mix_from(WATER, "P", P2, "h", h1, pick(["x", "x", "T", "s"]), tags=["tricky", "device"], ctx=ctx, ctxwhy=cw)
        else:
            P1 = pick([2000, 3000, 4000, 5000]); x1 = pick([0.95, 0.96, 0.97, 0.98, 0.99]); s1 = WATER.satP(P1)
            h1 = round(s1["hf"] + x1 * s1["hfg"], 1)
            P2 = 100
            ctx = f"A throttling calorimeter samples wet steam from a {fmt_P(P1)} line (x = {x1}). The steam leaves the valve at {fmt_P(P2)}."
            cw = [f"Inlet: h<sub>1</sub> = h<sub>f</sub> + x h<sub>fg</sub> = {fmt(s1['hf'], 2)} + {x1}({fmt(s1['hfg'], 2)}) = {fmt(h1, 1)} kJ/kg (Table A-5).",
                  "Throttling: no work, negligible heat and ΔKE, so h<sub>2</sub> = h<sub>1</sub>."]
            if h1 > WATER.satP(P2)["hg"]:
                try: item_sh_inverse(WATER, P2, "h", h1, "T", tags=["tricky", "device"], ctx=ctx, ctxwhy=cw)
                except AssertionError: pass

def water_tank(n):
    k0 = len(ITEMS)
    while len(ITEMS) - k0 < n:
        P1 = pick([200, 300, 400, 600, 800, 1000, 1200, 1400]); T1 = pick([t for t in WATER.SH[P1] if t <= 500 and t not in (WATER.SH[P1][0],)])
        v1 = WATER.sh(P1, T1)["v"]
        T2 = pick([t for t in WATER.T_GRID if 50 <= t <= 150])
        st = WATER.satT(T2)
        if not (st["vf"] < v1 < st["vg"]): continue
        ctx = f"A rigid, sealed tank holds steam at {fmt_P(P1)} and {fmt_T(T1)}. It cools until it reaches {fmt_T(T2)}."
        cw = [f"State 1 is superheated (Table A-6): v<sub>1</sub> = {fmt(v1, n=5)} m³/kg.",
              "Rigid and sealed: V and m don't change, so v<sub>2</sub> = v<sub>1</sub>. State 2 is fixed by T<sub>2</sub> and v<sub>2</sub>."]
        item_mix_from(WATER, "T", T2, "v", v1, pick(["x", "x", "P", "u"]), tags=["tricky", "device"], ctx=ctx, ctxwhy=cw)

def water_misc(n):
    k0 = len(ITEMS)
    opts = []
    while len(ITEMS) - k0 < n:
        kind = pick(["cond", "pump", "boiler", "cold", "a7", "lowsh"])
        if kind == "cond":
            P = pick([10, 15, 20, 25, 50, 75])
            item_satstate(WATER, "P", P, "liquid", pick(["h", "s", "T"]), tags=["device"],
                          ctx=f"Water leaves a power-plant condenser as saturated liquid at {fmt_P(P)}.")
        elif kind == "pump":
            P = pick([10, 15, 20, 50, 75, 100])
            item_satstate(WATER, "P", P, "liquid", "v", tags=["device"],
                          ctx=f"A pump takes in saturated liquid water at {fmt_P(P)}. You need v<sub>1</sub> for the pump work, w = vΔP.")
        elif kind == "boiler":
            P = pick([1000, 2000, 3000, 4000, 5000, 8000, 10000])
            item_satstate(WATER, "P", P, "vapor", pick(["h", "s", "T"]), tags=["device"],
                          ctx=f"Water leaves a boiler as saturated vapor at {fmt_P(P)}.")
        elif kind == "cold":
            T = pick([10, 15, 20, 25, 30]); P = pick([200, 300, 400, 500])
            item_TP(WATER, P, T, pick(["h", "u", "s"]), tags=["device"],
                    ctx=f"Cooling water enters a heat exchanger at {fmt_P(P)} and {fmt_T(T)}.")
        elif kind == "a7":
            P = pick(WATER.CL_P); T = pick([t for t in WATER.CL_T if t <= 240 and t < WATER.Tsat_true(P) - 10])
            item_TP(WATER, P, T, pick(["v", "u", "h", "s"]), tags=["tricky"])
        elif kind == "lowsh":
            P, T = pick([(10, 50), (10, 100), (50, 100), (100, 100.0), (10, 150)])
            if T == 100.0 and P == 100: T = 150
            item_TP(WATER, P, T, pick(["v", "h", "s"]), tags=["tricky", "surprise"])

def r_compressor(n):
    k0 = len(ITEMS)
    while len(ITEMS) - k0 < n:
        by = pick(["P", "T"])
        if by == "P":
            P1 = pick([100, 120, 140, 160, 180, 200, 240, 280, 320]); s1 = R.satP(P1)["sg"]; lab = f"{fmt_P(P1)}"; tbl = "A-12"
        else:
            T1 = pick([-26, -24, -20, -18, -16, -12, -10, -8, -4, 0, 4]); st = R.satT(T1); s1 = st["sg"]; lab = f"{fmt_T(T1)}"; tbl = "A-11"
        P2 = pick([600, 700, 800, 900, 1000, 1200, 1400])
        ctx = f"R-134a enters an adiabatic, reversible (isentropic) compressor as saturated vapor at {lab} and leaves at {fmt_P(P2)}."
        cw = [f"Inlet: saturated vapor at {lab}: s<sub>1</sub> = s<sub>g</sub> = {fmt(s1, 5)} kJ/kg·K (Table {tbl}).",
              f"Isentropic means s<sub>2</sub> = s<sub>1</sub>. Round to the table's precision: s<sub>2</sub> = {fmt(s1, 4)} kJ/kg·K."]
        try:
            item_sh_inverse(R, P2, "s", round(s1, 4), pick(["T", "T", "h"]), tags=["tricky", "device"], ctx=ctx, ctxwhy=cw)
        except AssertionError:
            pass

def r_throttle(n):
    k0 = len(ITEMS)
    while len(ITEMS) - k0 < n:
        kind = pick(["satliq", "subcool"])
        P2 = pick([100, 120, 140, 160, 180, 200, 240, 280, 320])
        if kind == "satliq":
            P1 = pick([600, 700, 800, 900, 1000, 1200, 1400]); h1 = R.satP(P1)["hf"]
            ctx = f"Saturated liquid R-134a at {fmt_P(P1)} passes through an expansion valve to {fmt_P(P2)}."
            cw = [f"Inlet: saturated liquid at {fmt_P(P1)}: h<sub>1</sub> = h<sub>f</sub> = {fmt(h1, 2)} kJ/kg (Table A-12).",
                  "A valve: no work, negligible heat and ΔKE, so h<sub>2</sub> = h<sub>1</sub>."]
        else:
            P1 = pick([800, 900, 1000, 1200]); Ts = R.Tsat_true(P1)
            T1 = pick([t for t in R.T_GRID if Ts - 14 <= t <= Ts - 3])
            h1 = R.satT(T1)["hf"]
            ctx = f"R-134a leaves a condenser at {fmt_P(P1)} and {fmt_T(T1)}, then passes through an expansion valve to {fmt_P(P2)}."
            cw = [f"Inlet: T<sub>1</sub> = {fmt_T(T1)} is below T<sub>sat</sub>@{fmt_P(P1)} = {fmt(R.satP(P1)['T'], 2)} °C, so it is compressed (subcooled) liquid: h<sub>1</sub> ≈ h<sub>f</sub>@{fmt_T(T1)} = {fmt(h1, 2)} kJ/kg (Table A-11).",
                  "A valve: no work, negligible heat and ΔKE, so h<sub>2</sub> = h<sub>1</sub>."]
        try:
            item_mix_from(R, "P", P2, "h", h1, pick(["x", "x", "T", "s"]), tags=["tricky", "device"], ctx=ctx, ctxwhy=cw)
        except AssertionError:
            pass

def r_tank(n):
    k0 = len(ITEMS)
    while len(ITEMS) - k0 < n:
        P1 = pick([400, 500, 600, 700, 800, 1000]); T1 = pick([t for t in R.SH[P1][1:] if t <= 90])
        v1 = R.sh(P1, T1)["v"]
        T2 = pick([t for t in R.T_GRID if -30 <= t <= 30])
        st = R.satT(T2)
        if not (st["vf"] < v1 < st["vg"]): continue
        ctx = f"A rigid, sealed tank holds R-134a at {fmt_P(P1)} and {fmt_T(T1)}. It cools until it reaches {fmt_T(T2)}."
        cw = [f"State 1 is superheated (Table A-13): v<sub>1</sub> = {fmt(v1, n=5)} m³/kg.",
              "Rigid and sealed: v<sub>2</sub> = v<sub>1</sub>. State 2 is fixed by T<sub>2</sub> and v<sub>2</sub>."]
        item_mix_from(R, "T", T2, "v", v1, pick(["x", "x", "P", "u"]), tags=["tricky", "device"], ctx=ctx, ctxwhy=cw)

def r_misc(n):
    k0 = len(ITEMS)
    while len(ITEMS) - k0 < n:
        kind = pick(["evapsat", "evapsh", "condcl", "room"])
        if kind == "evapsat":
            T = pick([-26, -24, -20, -18, -14, -10, -6, -4, 0]);
            item_satstate(R, "T", T, "vapor", pick(["h", "s", "P"]), tags=["device"],
                          ctx=f"R-134a leaves an evaporator as saturated vapor at {fmt_T(T)}.")
        elif kind == "evapsh":
            P = pick([100, 140, 180, 200, 240, 280]); T = R.SH[P][1] if P != 60 else 0
            item_TP(R, P, T, pick(["h", "s"]), tags=["device", "tricky"],
                    ctx=f"R-134a leaves an evaporator at {fmt_P(P)} and {fmt_T(T)}, about {round(T - R.Tsat_true(P))} \u00b0C above its saturation temperature.")
        elif kind == "condcl":
            P = pick([800, 900, 1000, 1200, 1400]); Ts = R.Tsat_true(P)
            T = pick([t for t in R.T_GRID if Ts - 14 <= t <= Ts - 2])
            item_TP(R, P, T, pick(["h", "u", "v", "s"]), tags=["device", "tricky"],
                    ctx=f"R-134a leaves a condenser at {fmt_P(P)} and {fmt_T(T)}.")
        elif kind == "room":
            P, T = pick([(100, 20), (140, 20), (200, 30), (240, 20), (280, 30), (320, 30), (400, 30)])
            item_TP(R, P, T, pick(["v", "h", "s"]), tags=["tricky", "surprise"])

def gen_findP(F, n):
    k0 = len(ITEMS); tries = 0
    blocks = sorted(F.SH.keys())
    while len(ITEMS) - k0 < n and tries < 2000:
        tries += 1
        i = random.randrange(0, len(blocks) - 1); Pa, Pb = blocks[i], blocks[i + 1]
        common = [t for t in F.SH[Pa] if t in F.SH[Pb][1:]]
        if F is R: common = [t for t in common if t >= 0]
        if not common: continue
        T = pick(common)
        va, vb = F.sh(Pa, T)["v"], F.sh(Pb, T)["v"]
        v = rsig(va + random.uniform(0.25, 0.75) * (vb - va), 4)
        try: item_Tv_findP(F, T, v, Pa, Pb)
        except AssertionError: pass

def gen_double(F, n):
    k0 = len(ITEMS); tries = 0
    blocks = sorted(F.SH.keys())
    while len(ITEMS) - k0 < n and tries < 2000:
        tries += 1
        i = random.randrange(0, len(blocks) - 1); Pa, Pb = blocks[i], blocks[i + 1]
        if Pb - Pa < 40: continue
        P = (Pa + Pb) / 2 if random.random() < 0.6 else Pa + (Pb - Pa) * pick([0.25, 0.75])
        P = round(P)
        common = [t for t in F.SH[Pa][1:] if t in F.SH[Pb][1:]]
        if len(common) < 3: continue
        j = random.randrange(0, len(common) - 1)
        lo, hi = common[j], common[j + 1]
        T = (lo + hi) // 2 if random.random() < 0.5 else lo
        if T <= F.Tsat_true(P) + 5: continue
        try: item_double(F, P, Pa, Pb, T, pick(["v", "h", "s", "u"]))
        except AssertionError: pass

def not_independent_note():
    pass

# ---------------------------------------------------------------- run
gen_regular(R, 230)
gen_sh_inverse(R, 45)
r_compressor(28)
r_throttle(28)
r_tank(16)
r_misc(30)
gen_double(R, 10)

w0 = len(ITEMS)
gen_regular(WATER, 120)
gen_sh_inverse(WATER, 40)
water_turbine(34)
water_throttle(22)
water_tank(16)
water_misc(40)
gen_double(WATER, 10)

# dedupe identical (fluid, given, ask)
seen = set(); out = []
for it in ITEMS:
    key = (it["fluid"], json.dumps(it["given"]), it["ask"], it["ctx"][:40])
    if key in seen: continue
    seen.add(key); out.append(it)
ITEMS = out
for i, it in enumerate(ITEMS):
    it["id"] = ("R" if it["fluid"] == "r" else "W") + f"{i + 1:03d}"
    if any(g[0] == "s" for g in it["given"]) or it["ask"] == "s":
        it["tags"].append("s")
    it["answer"] = float(f"{it['answer']:.6g}")
    for d in it["diag"]:
        d["v"] = float(f"{d['v']:.6g}")
    it["tags"] = sorted(set(it["tags"]))

json.dump(ITEMS, open("states2.json", "w"), ensure_ascii=False)
from collections import Counter
print(len(ITEMS), Counter(i["fluid"] for i in ITEMS), Counter(i["phase"] for i in ITEMS))
print(Counter(t for i in ITEMS for t in i["tags"]))
print(Counter((i["fluid"], i["ask"]) for i in ITEMS))
