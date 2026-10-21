"""Second patch: Exam 2 guided problems and the Exam 2 practice exam (runs after patch_site.py)."""
import json, sys
SRC, DST = sys.argv[1], sys.argv[2]
G = "/tmp/claude-0/-home-claude/146417c8-8d3c-5b91-94f8-ad9df4b6a0c2/scratchpad/gen/"
html = open(SRC, encoding="utf-8").read()
tpls = json.load(open(G + "exam2_templates.json"))
for t in tpls:
    for v in t["v"]: v.pop("_p", None)
b3 = json.dumps({"templates": tpls}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

def rep(old, new, count=1):
    global html
    n = html.count(old)
    assert n == count, (n, old[:140])
    html = html.replace(old, new)

# ---------- data
i = html.index("<script>const BANK2 = "); j = html.index("</script>", i) + len("</script>")
html = html[:j] + "\n<script>const BANK3 = " + b3 + ";</script>" + html[j:]

rep("Your printed tables may differ in the last digit, and answers accept small differences from your own interpolation.</div>",
    "Air values (Table A-17) come from air's ideal-gas specific heat, anchored to the book's 300 K row; they agree with the printed table to within about 0.05%. Your printed tables may differ in the last digit, and answers accept small differences from your own interpolation.</div>")
rep("    const j = judge(inp.value, st.answer, tolEff(st), st.diag, PUNIT[st.ask]);\n    ph.parentElement",
    "    const j = judge(inp.value, st.answer, tolEff(st), st.diag, PUNIT[st.ask]);\n    if (!j.ok && j.code === \"off\" && st.atol && st.atol > st.tol * Math.abs(st.answer)) j.msg = `Not within \u00b1${st.atol} ${PUNIT[st.ask]} of the answer. Recheck the step this number comes from.`;\n    ph.parentElement")
# ---------- CSS for the new sketches
rep("svg.dia text.axl{fill:var(--muted);font-style:italic;font-size:13px}",
    "svg.dia text.axl{fill:var(--muted);font-style:italic;font-size:13px}\nsvg.dia .dash{stroke:var(--accent-text);stroke-width:2.2;fill:none;stroke-dasharray:5 4}\nsvg.dia .iso{stroke:var(--muted);stroke-width:1.2;fill:none;stroke-dasharray:3 3}\n.exsw{display:flex;gap:6px;flex-wrap:wrap}")

# ---------- templates, chapters, tables
rep("const TPL = {}; BANK.templates.forEach(t => TPL[t.id] = t);\nconst ORDER = BANK.templates.map(t => t.id);",
    "const TPL = {}; BANK.templates.concat(BANK3.templates).forEach(t => TPL[t.id] = t);\nconst ORDER2 = BANK3.templates.map(t => t.id), ORDER1 = BANK.templates.map(t => t.id);\nconst ORDER = ORDER2.concat(ORDER1);\n"
    "const TABLES = [\"A-1\",\"A-2a\",\"A-3\",\"A-4\",\"A-5\",\"A-6\",\"A-7\",\"A-11\",\"A-12\",\"A-13\",\"A-17\",\"Given / computed\"];")
rep('const CHNAME = {1:"Ch. 1 · Pressure and basic concepts", 2:"Ch. 2 · Energy and energy transfer", 3:"Ch. 3 · Properties of pure substances", 4:"Ch. 4 · Closed systems"};',
    'const CHNAME = {1:"Ch. 1 · Pressure and basic concepts", 2:"Ch. 2 · Energy and energy transfer", 3:"Ch. 3 · Properties of pure substances", 4:"Ch. 4 · Closed systems", 5:"Ch. 5 · Mass and energy in control volumes", 6:"Ch. 6 · The second law", 7:"Ch. 7 · Entropy", 9:"Ch. 9 · Gas power cycles"};')
rep("${BANK.tables.map(t => `<option>${t}</option>`).join(\"\")}", "${TABLES.map(t => `<option>${t}</option>`).join(\"\")}")

# ---------- new sketches (T-s and P-v cycles)
rep("function smooth(pts){", r"""function pwr(v1, P1, v2, P2, n = 16){ const k = Math.log(P2 / P1) / Math.log(v1 / v2), o = []; for (let i = 0; i <= n; i++){ const v = v1 + (v2 - v1) * i / n; o.push([v, P1 * Math.pow(v1 / v, k)]); } return o; }
function dPts(X, Y, pts){ return "M" + pts.map(p => X(p[0]).toFixed(1) + "," + Y(p[1]).toFixed(1)).join(" L"); }
function sk(X, Y, m, segs, dashed, isos, labels){
  const mm = m + "s";
  let s = `<defs><marker id="${mm}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path class="arrow" d="M0,0 L10,5 L0,10 z"/></marker></defs>`;
  (isos || []).forEach(p => { s += `<path class="iso" d="${p.length > 3 ? smooth(p.map(q => [X(q[0]), Y(q[1])])) : dPts(X, Y, p)}"/>`; });
  segs.forEach(p => { s += `<path class="path" d="${dPts(X, Y, p)}" marker-end="url(#${mm})"/>`; });
  (dashed || []).forEach(p => { s += `<path class="dash" d="${dPts(X, Y, p)}" marker-end="url(#${mm})"/>`; });
  labels.forEach(([x, y, t, dx, dy]) => { s += `<circle class="pt" cx="${X(x).toFixed(1)}" cy="${Y(y).toFixed(1)}" r="2.8"/><text x="${(X(x) + (dx || 5)).toFixed(1)}" y="${(Y(y) + (dy || -5)).toFixed(1)}">${t}</text>`; });
  return s;
}
const LOWP = [[.12,.14],[.35,.22],[.6,.34],[.92,.52]], HIGHP = [[.12,.50],[.35,.70],[.48,.79],[.66,.94]];
Object.assign(KINDS, {
  ts_turb:{ax:"Ts", dome:true, lbl:"Straight down to 2s; actual 2a to the right of 2s", draw:(X, Y, m) => sk(X, Y, m, [[[.70,.86],[.70,.24]]], [[[.70,.86],[.79,.24]]], [[[domeX(.24,"L"),.24],[domeX(.24,"R"),.24]]], [[.70,.86,"1"],[.70,.24,"2s",-16,14],[.79,.24,"2a",2,14]])},
  ts_turb_left:{ax:"Ts", dome:true, lbl:"Straight down to 2s; actual 2a to the left of 2s", draw:(X, Y, m) => sk(X, Y, m, [[[.70,.86],[.70,.24]]], [[[.70,.86],[.58,.24]]], [[[domeX(.24,"L"),.24],[domeX(.24,"R"),.24]]], [[.70,.86,"1"],[.70,.24,"2s",4,14],[.58,.24,"2a",-18,14]])},
  ts_turb_isoT:{ax:"Ts", dome:true, lbl:"Horizontal: temperature stays constant", draw:(X, Y, m) => sk(X, Y, m, [[[.62,.70],[.92,.70]]], [], [], [[.62,.70,"1"],[.92,.70,"2",-10,-6]])},
  ts_comp_dome:{ax:"Ts", dome:true, lbl:"Straight up from inside the dome", draw:(X, Y, m) => sk(X, Y, m, [[[.45,.24],[.45,.80]]], [], [], [[.45,.24,"1"],[.45,.80,"2"]])},
  ts_comp:{ax:"Ts", dome:false, lbl:"Straight up to 2s; actual 2a to the right of 2s", draw:(X, Y, m) => sk(X, Y, m, [[[.35,.22],[.35,.70]]], [[[.35,.22],[.48,.79]]], [LOWP, HIGHP], [[.35,.22,"1"],[.35,.70,"2s",-18,-4],[.48,.79,"2a",4,0]])},
  ts_comp_left:{ax:"Ts", dome:false, lbl:"Straight up to 2s; actual 2a to the left of 2s", draw:(X, Y, m) => sk(X, Y, m, [[[.35,.22],[.35,.70]]], [[[.35,.22],[.22,.60]]], [LOWP, HIGHP], [[.35,.22,"1"],[.35,.70,"2s",4,10],[.22,.60,"2a",-18,-4]])},
  ts_turb_gas:{ax:"Ts", dome:false, lbl:"Straight down from the high-pressure line", draw:(X, Y, m) => sk(X, Y, m, [[[.48,.79],[.48,.28]]], [], [LOWP, HIGHP], [[.48,.79,"1"],[.48,.28,"2",4,12]])},
  ts_comp_isoP:{ax:"Ts", dome:false, lbl:"Along the low-pressure line", draw:(X, Y, m) => sk(X, Y, m, [[[.35,.22],[.6,.34],[.85,.48]]], [], [LOWP, HIGHP], [[.35,.22,"1"],[.85,.48,"2",-6,-8]])},
  ts_rcomp:{ax:"Ts", dome:true, lbl:"From the vapor line straight up to 2s; 2a to the right", draw:(X, Y, m) => sk(X, Y, m, [[[domeX(.30,"R"),.30],[domeX(.30,"R"),.72]]], [[[domeX(.30,"R"),.30],[domeX(.30,"R") + .08,.77]]], [[[domeX(.6,"R"),.6],[domeX(.30,"R"),.72],[domeX(.30,"R") + .08,.77],[.98,.82]]], [[domeX(.30,"R"),.30,"1",5,10],[domeX(.30,"R"),.72,"2s",-18,-4],[domeX(.30,"R") + .08,.77,"2a",4,-4]])},
  ts_rcomp_left:{ax:"Ts", dome:true, lbl:"From the vapor line straight up to 2s; 2a to the left", draw:(X, Y, m) => sk(X, Y, m, [[[domeX(.30,"R"),.30],[domeX(.30,"R"),.72]]], [[[domeX(.30,"R"),.30],[domeX(.30,"R") - .08,.67]]], [[[domeX(.6,"R"),.6],[domeX(.30,"R") - .08,.67],[domeX(.30,"R"),.72],[.98,.82]]], [[domeX(.30,"R"),.30,"1",5,10],[domeX(.30,"R"),.72,"2s",4,-4],[domeX(.30,"R") - .08,.67,"2a",-18,-4]])},
  ts_rcomp_dome:{ax:"Ts", dome:true, lbl:"From the vapor line into the dome", draw:(X, Y, m) => sk(X, Y, m, [[[domeX(.30,"R"),.30],[.45,.55]]], [], [], [[domeX(.30,"R"),.30,"1",5,10],[.45,.55,"2"]])},
  pv_otto:{ax:"PV", dome:false, lbl:"Two constant-volume lines between two isentropes", draw:(X, Y, m) => sk(X, Y, m, [pwr(.85,.10,.18,.45), [[.18,.45],[.18,.92]], pwr(.18,.92,.85,.25), [[.85,.25],[.85,.10]]], [], [], [[.85,.10,"1",4,-4],[.18,.45,"2",-12,4],[.18,.92,"3",6,4],[.85,.25,"4",4,-4]])},
  pv_diesel:{ax:"PV", dome:false, lbl:"Heat in at constant pressure, out at constant volume", draw:(X, Y, m) => sk(X, Y, m, [pwr(.85,.10,.15,.80), [[.15,.80],[.34,.80]], pwr(.34,.80,.85,.28), [[.85,.28],[.85,.10]]], [], [], [[.85,.10,"1",4,-4],[.15,.80,"2",-12,4],[.34,.80,"3",4,-6],[.85,.28,"4",4,-4]])},
  pv_dual:{ax:"PV", dome:false, lbl:"Heat in partly at constant volume, partly at constant pressure", draw:(X, Y, m) => sk(X, Y, m, [pwr(.85,.10,.17,.55), [[.17,.55],[.17,.86]], [[.17,.86],[.32,.86]], pwr(.32,.86,.85,.27), [[.85,.27],[.85,.10]]], [], [], [[.85,.10,"1",4,-4],[.17,.55,"2",-12,4],[.17,.86,"x",-12,0],[.32,.86,"3",4,-6],[.85,.27,"4",4,-4]])},
  pv_brayton:{ax:"PV", dome:false, lbl:"Two constant-pressure lines between two isentropes", draw:(X, Y, m) => sk(X, Y, m, [pwr(.50,.12,.18,.80), [[.18,.80],[.45,.80]], pwr(.45,.80,.95,.12), [[.95,.12],[.50,.12]]], [], [], [[.50,.12,"1",-4,14],[.18,.80,"2",-12,4],[.45,.80,"3",4,-6],[.95,.12,"4",-12,-6]])}
});
function smooth(pts){""")
rep('const ax = K.ax === "Tv" ? ["v", "T"] : K.ax === "PV" ? ["V", "P"] : ["v", "P"];',
    'const ax = K.ax === "Tv" ? ["v", "T"] : K.ax === "PV" ? ["v", "P"] : K.ax === "Ts" ? ["s", "T"] : ["v", "P"];')
rep("  if (K.point){ const [x, y] = K.point(); s += `<circle class=\"pt\" cx=\"${X(x)}\" cy=\"${Y(y)}\" r=\"5\"/>`; }",
    "  if (K.point){ const [x, y] = K.point(); s += `<circle class=\"pt\" cx=\"${X(x)}\" cy=\"${Y(y)}\" r=\"5\"/>`; }\n  if (K.draw) s += K.draw(X, Y, id);")

# ---------- guided list: Exam 2 chapters first
rep("""  app.append(el(`<section><h2>Guided problems</h2><p class="muted" style="margin-top:4px">Exam-style problems from Ch. 1–4, each with new numbers every attempt. Every solution follows your eight problem-solving steps.</p></section>`));
  for (const ch of [1, 2, 3, 4]){""",
    """  app.append(el(`<section><h2>Guided problems</h2><p class="muted" style="margin-top:4px">Exam-style problems with new numbers every attempt. Every solution follows your eight problem-solving steps. Exam 2 problems come first; Exam 1 problems are below for review.</p></section>`));
  for (const ch of [5, 6, 7, 9, 1, 2, 3, 4]){
    if (ch === 5) app.append(el(`<div class="eyebrow" style="font-size:.85rem;color:var(--accent-text)">Exam 2 · Ch. 5–7 and 9</div>`));
    if (ch === 1) app.append(el(`<div class="eyebrow" style="font-size:.85rem;color:var(--accent-text);margin-top:10px">Exam 1 review · Ch. 1–4</div>`));""")
rep("    BANK.templates.filter(t => t.ch === ch).forEach(t => {", "    BANK.templates.concat(BANK3.templates).filter(t => t.ch === ch).forEach(t => {")

# ---------- home track: Exam 2 stations, lit when two problems are solid
rep("""const STATIONS = [
  {name:"Pressure", ids:["T1","T2"]}, {name:"Energy", ids:["T3","T4"]}, {name:"Tables", ids:["LOC"]},""",
    """const STATIONS_E1 = [
  {name:"Pressure", ids:["T1","T2"]}, {name:"Energy", ids:["T3","T4"]}, {name:"Tables", ids:["LOC"]},""")
rep("""{name:"Closed: gases & liquids", ids:["T11","T12","T13"]}, {name:"Which table?", ids:["MDL"]}
];""", """{name:"Closed: gases & liquids", ids:["T11","T12","T13"]}
];
const STATIONS = [{name:"Properties", ids:["LOC"]}, {name:"Which table?", ids:["MDL"]}, {name:"Devices", ids:["E1","E2","E3","E4","E5"]},
  {name:"Exchangers & mixing", ids:["E6","E7","E8","E9"]}, {name:"Second law", ids:["E10","E11","E12"]}, {name:"Entropy", ids:["E13","E14","E15"]}, {name:"Cycles", ids:["E16","E17","E18","E19","E20"]}];
const stationLit = st => st.ids.filter(skillSolid).length >= Math.min(2, st.ids.length);""")
rep("  const all = STATIONS.flatMap(s => s.ids);\n  const frac = all.filter(skillSolid).length / all.length;",
    "  const frac = STATIONS.filter(stationLit).length / STATIONS.length;")
rep("    const lit = st.ids.every(skillSolid);", "    const lit = stationLit(st);")
rep("A guided skill is solid after two clean solves, one of them Solo. Properties turn solid at 80% over 15 states, and Which table? at 80% over 20 cards.",
    "A station lights up when two of its problems are solid; a problem is solid after two clean solves, one of them Solo. Properties turn solid at 80% over 15 states, and Which table? at 80% over 20 cards.")
rep("  const solid = ORDER.filter(id => status(id) === \"solid\").length;", "  const solid = ORDER2.filter(id => status(id) === \"solid\").length;")
rep('<div class="stat"><span class="small muted">Guided skills solid</span><b>${solid} / ${ORDER.length}</b></div>',
    '<div class="stat"><span class="small muted">Exam 2 problems solid</span><b>${solid} / ${ORDER2.length}</b></div>')
rep("  const best = S.exams.length ? Math.max(...S.exams.map(x => x.total)) : null;",
    "  const ex2 = S.exams.filter(x => x.which === \"e2\"); const best = ex2.length ? Math.max(...ex2.map(x => x.total)) : null;")
rep('<div class="stat"><span class="small muted">Best practice exam</span><b>${best == null ? "–" : best.toFixed(0) + " / 100"}</b><span class="small muted">${S.exams.length} taken</span></div>',
    '<div class="stat"><span class="small muted">Best Exam 2 practice</span><b>${best == null ? "–" : best.toFixed(0) + " / 100"}</b><span class="small muted">${ex2.length} taken</span></div>')
rep('<div><b>Practice exam</b><p class="small muted">Six problems, two hours, scored against the exam\'s point split.</p></div>',
    '<div><b>Practice exam</b><p class="small muted">Six problems, two hours, 100 points: Exam 2 by default, Exam 1 for review.</p></div>')

# ---------- practice exam
rep('const SLOTS = [["T1","T2"],["T3","T4"],"TABLE",["T6","T7","T8"],["T9","T10"],["T11","T12","T13"]];',
    """const SLOTS = [["T1","T2"],["T3","T4"],"TABLE",["T6","T7","T8"],["T9","T10"],["T11","T12","T13"]];
const SLOTS2 = ["TABLE2", ["E1","E2","E3","E4","E5"], ["E6","E7","E8","E9"], ["E10","E11","E12"], ["E13","E14","E15"], ["E16","E17","E18","E19","E20"]];
const EXDEF = {
  e1:{name:"Exam 1", covers:"Ch. 1–4", intro:"Six problems shaped like Exam 1: pressure, energy, a table fill-in, properties, and two closed-system problems.", tables:"Çengel tables (A-1 to A-6)"},
  e2:{name:"Exam 2", covers:"Ch. 5–7 and Ch. 9 through Brayton", intro:"Six problems for Exam 2: a water and R-134a table fill-in, a steady-flow device, a heat exchanger or mixing chamber, a second-law problem, an isentropic-efficiency problem, and a gas power cycle.", tables:"Çengel tables (A-1, A-2a, A-4 to A-7, A-11 to A-13, A-17)"}
};
function tabState(ri){ return LSTATES[ri]; }
function pickRows2(){
  const pool = LSTATES.map((s, i) => i).filter(i => i >= BANK.locator.states.length && !LSTATES[i].tags.includes("device") && !LSTATES[i].tags.includes("double"));
  const want = shuffle([["w","cl"],["r","mix"],["w", Math.random() < .5 ? "mix" : "sh"],["r","sh"]]);
  const rows = [], used = new Set();
  want.forEach(([fl, ph]) => { const c = pool.filter(i => LSTATES[i].fluid === fl && LSTATES[i].phase === ph && !used.has(i)); const i = c[rnd(c.length)]; used.add(i); rows.push(i); });
  return rows;
}""")
rep("""function newExam(){
  const probs = SLOTS.map(sl => sl === "TABLE" ? {k:"tab", rows:pickRows(), pts:15} : (() => { const tid = sl[rnd(sl.length)]; return {k:"tpl", tid, vi:rnd(TPL[tid].v.length), pts:TPL[tid].pts}; })());
  return {id:Date.now(), probs, ans:{}, self:{}, left:120 * 60, paused:false, cur:0, graded:false};
}""", """function newExam(which){
  which = which || S.exsel || "e2";
  const slots = which === "e2" ? SLOTS2 : SLOTS;
  const probs = slots.map(sl => sl === "TABLE" ? {k:"tab", rows:pickRows(), pts:15} : sl === "TABLE2" ? {k:"tab", rows:pickRows2(), pts:12} : (() => { const tid = sl[rnd(sl.length)]; return {k:"tpl", tid, vi:rnd(TPL[tid].v.length), pts:TPL[tid].pts}; })());
  return {id:Date.now(), which, probs, ans:{}, self:{}, left:120 * 60, paused:false, cur:0, graded:false};
}""")
rep("""  app.append(el(`<section><h2>Practice exam</h2><p class="muted" style="margin-top:4px">Six problems shaped like Exam 1: pressure, energy, a table fill-in, properties, and two closed-system problems. Two hours, 100 points. Work on paper, enter final answers here, then score your setup against the worked solutions.</p></section>`));
  const info = el(`<section class="grid2">
      <div class="card list"><div class="eyebrow">Have ready</div><ul class="clean"><li>Çengel tables (A-1 to A-6)</li><li>Calculator</li><li>Your formula sheet</li><li>Paper, with each problem worked in the eight steps</li></ul>""",
    """  const X = S.exsel || "e2", D = EXDEF[X];
  app.append(el(`<section><h2>Practice exam</h2><p class="muted" style="margin-top:4px">${D.intro} Two hours, 100 points. Work on paper, enter final answers here, then score your setup against the worked solutions.</p></section>`));
  const sw = el(`<div class="filters" role="group" aria-label="Which exam">${Object.entries(EXDEF).reverse().map(([k, d]) => `<button data-x="${k}" aria-pressed="${k === X}">${d.name} practice · ${d.covers}</button>`).join("")}</div>`);
  $$("button", sw).forEach(b => b.onclick = () => { S.exsel = b.dataset.x; save(); route(); });
  app.append(sw);
  const info = el(`<section class="grid2">
      <div class="card list"><div class="eyebrow">Have ready</div><ul class="clean"><li>${D.tables}</li><li>Calculator</li><li>Your formula sheet</li><li>Paper, with each problem worked in the eight steps</li></ul>""")
rep("""      <details class="card"><summary>Check your formula sheet</summary><div class="list small" style="margin-top:10px">
        <p class="muted">Make your own sheet; writing it is part of studying. Does yours cover these?</p>
        <ul class="clean"><li>P<sub>abs</sub>""", """      <details class="card"><summary>Check your formula sheet</summary><div class="list small" style="margin-top:10px">
        <p class="muted">Make your own sheet; writing it is part of studying. Does yours cover these?</p>
        ${X === "e2" ? `<ul class="clean"><li>Mass balance: ∑ṁ<sub>in</sub> = ∑ṁ<sub>out</sub>; ṁ = ρAV = AV/v; V̇ = ṁv</li>
        <li>Steady-flow first law: Q̇<sub>in</sub> + Ẇ<sub>in</sub> + ∑ṁ(h + V²/2 + gz)<sub>in</sub> − Q̇<sub>out</sub> − Ẇ<sub>out</sub> − ∑ṁ(h + V²/2 + gz)<sub>out</sub> = dE<sub>cv</sub>/dt, and which terms each device keeps</li>
        <li>V²/2 in kJ/kg: divide m²/s² by 1000; throttle: h<sub>2</sub> = h<sub>1</sub></li>
        <li>η<sub>th</sub> = W<sub>net</sub>/Q<sub>H</sub>; COP<sub>R</sub> = Q<sub>L</sub>/W; COP<sub>HP</sub> = Q<sub>H</sub>/W; Carnot limits in kelvins</li>
        <li>Entropy: S<sub>gen</sub> ≥ 0; steady flow Ṡ<sub>gen</sub> = ∑ṁs<sub>out</sub> − ∑ṁs<sub>in</sub> − ∑Q̇<sub>k</sub>/T<sub>k</sub>; reservoirs ΔS = Q/T</li>
        <li>Ideal-gas Δs with constant c and with s° from A-17; incompressible Δs = c ln(T<sub>2</sub>/T<sub>1</sub>)</li>
        <li>Isentropic: s<sub>2</sub> = s<sub>1</sub> in tables; k-relations for constant c; P<sub>r</sub> and v<sub>r</sub> in A-17</li>
        <li>Isentropic efficiencies for turbines, compressors and nozzles (which way the ratio goes)</li>
        <li>Otto, Diesel, dual and Brayton: state relations, q<sub>in</sub>, q<sub>out</sub>, η, back work ratio, MEP</li>
        <li>Your property-model rules: which table, and when ideal gas and constant c are allowed</li></ul>` : `<ul class="clean"><li>P<sub>abs</sub>""")
rep("""        <li>Δu = c<sub>v</sub>ΔT, Δh = c<sub>p</sub>ΔT, c<sub>p</sub> = c<sub>v</sub> + R; incompressible: Δu = cΔT</li>
        <li>Your default assumptions list</li></ul></div></details>""", """        <li>Δu = c<sub>v</sub>ΔT, Δh = c<sub>p</sub>ΔT, c<sub>p</sub> = c<sub>v</sub> + R; incompressible: Δu = cΔT</li>
        <li>Your default assumptions list</li></ul>`}</div></details>""")
rep("  $(\"#start\", info).onclick = () => { S.exam = newExam(); save(); route(); };\n  $(\"#paper\", info).onclick = () => paperView(app, newExam());",
    "  $(\"#start\", info).onclick = () => { S.exam = newExam(X); save(); route(); };\n  $(\"#paper\", info).onclick = () => paperView(app, newExam(X));")
rep("<thead><tr><th>Date</th><th>Answers</th><th>Setup (self-scored)</th><th>Total</th></tr></thead><tbody>${S.exams.slice().reverse().map(x => `<tr><td>${new Date(x.date).toLocaleDateString(\"en-US\", {month:\"short\", day:\"numeric\"})}</td>",
    "<thead><tr><th>Date</th><th>Exam</th><th>Answers</th><th>Setup (self-scored)</th><th>Total</th></tr></thead><tbody>${S.exams.slice().reverse().map(x => `<tr><td>${new Date(x.date).toLocaleDateString(\"en-US\", {month:\"short\", day:\"numeric\"})}</td><td>${x.which === \"e2\" ? \"2\" : \"1\"}</td>")
# table fill-in: use the merged state list
rep("""    const L = BANK.locator.states;
    box.append(el(`<p class="stem">For each state of water, give the phase and the requested property. Name the table and row you used in your written work.</p>`));""",
    """    box.append(el(`<p class="stem">For each state${E.which === "e2" ? " of water or R-134a" : " of water"}, give the phase and the requested property. Name the table and row you used in your written work.</p>`));""")
rep("      const st = L[ri];\n      t.querySelector(\"tbody\")", "      const st = tabState(ri);\n      t.querySelector(\"tbody\")")
rep("""        const st = BANK.locator.states[ri];
        const ph = E.ans[`${i}-r${k}-ph`] || "", okP = ph === st.phase;
        const j = judge(E.ans[`${i}-r${k}-v`] || "", st.answer, st.tol, st.diag, PUNIT[st.ask]);""",
    """        const st = tabState(ri);
        const ph = E.ans[`${i}-r${k}-ph`] || "", okP = ph === st.phase;
        const j = judge(E.ans[`${i}-r${k}-v`] || "", st.answer, tolEff(st), st.diag, PUNIT[st.ask]);""")
rep("const st = BANK.locator.states[ri]; return `<div class=\"panel\">", "const st = tabState(ri); return `<div class=\"panel\">")
rep("const st = BANK.locator.states[ri]; return `${String.fromCharCode(65 + k)}.", "const st = tabState(ri); return `${String.fromCharCode(65 + k)}.")
rep("${p.k === \"tab\" ? \"Drill the State locator\" : \"Practice this problem guided\"}", "${p.k === \"tab\" ? \"Drill Properties\" : \"Practice this problem guided\"}")
rep("S.exams.push({date:Date.now(), auto:t.auto, self:t.self, total:t.total});", "S.exams.push({date:Date.now(), which:E.which || \"e1\", auto:t.auto, self:t.self, total:t.total});")
rep("""  const paper = el(`<section class="paper"><div><div class="eyebrow">ENGR&amp;224 · Exam 1 practice · version ${String(E.id).slice(-5)}</div><h2>Practice exam: Ch. 1–4</h2>""",
    """  const D = EXDEF[E.which || "e1"];
  const paper = el(`<section class="paper"><div><div class="eyebrow">ENGR&amp;224 · ${D.name} practice · version ${String(E.id).slice(-5)}</div><h2>Practice exam: ${D.covers}</h2>""")
rep("""  $("#another", top).onclick = () => paperView(app, newExam());""", """  $("#another", top).onclick = () => paperView(app, newExam(E.which));""")
rep("""  $("#newex", head).onclick = () => { S.exam = newExam(); save(); go("exam"); };""", """  $("#newex", head).onclick = () => { S.exam = newExam(E.which || "e1"); save(); go("exam"); };""")

rep("        r.max += 3; r.earned += (okP ? 1 : 0) + (j.ok ? 2 : 0);", "        const per = ansPts(p) / p.rows.length; r.max += per; r.earned += per * ((okP ? 1 : 0) + (j.ok ? 2 : 0)) / 3;")
open(DST, "w", encoding="utf-8").write(html)
print("ok", len(html))
