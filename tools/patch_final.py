"""Fifth patch (Nov 23, 2026): the final exam. Runs on the current index.html in place, after patch_challenge.py.
Adds a "Final exam" tab with
  - exam-level problems: X1-X8 (gen_final2.py) plus E19, E20 (Brayton, held off the Exam 2 page on Nov 11)
  - harder problems: F1-F9 (gen_final.py) plus C10-C12 (held off the Exam 2 page on Nov 11)
a Final practice exam (five problems, 110 minutes, 100 points), a final-exam progress track on the home page,
and the final's date and scope in the countdown.
Usage: python3 patch_final.py ../index.html final2_templates.json final_templates.json"""
import json, sys
import gen_exam2 as GE
DST, X2, F1 = sys.argv[1:4]
html = open(DST, encoding="utf-8").read()
assert "const BANK5" not in html, "already patched"

def rep(old, new, count=1):
    global html
    n = html.count(old)
    assert n == count, (n, old[:140])
    html = html.replace(old, new)

xs = json.load(open(X2, encoding="utf-8")); fs = json.load(open(F1, encoding="utf-8"))
e1920 = [dict(t, tier="exam", grp="final") for t in GE.build() if t["id"] in ("E19", "E20")]
tpls = xs[:3] + e1920 + xs[3:] + fs["new"] + fs["held_challenge"]
for t in tpls:
    t["grp"] = "final"
    if t["id"] in ("C10", "C11", "C12"): t.pop("note", None)   # "pulled from the Exam 2 site" is history, not something students need
    for v in t["v"]: v.pop("_p", None)
assert len({t["id"] for t in tpls}) == len(tpls) == 22
b5 = json.dumps({"templates": tpls}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

# ---------- data, after BANK4
k = html.index("<script>const BANK4 = "); k = html.index("</script>", k) + len("</script>")
html = html[:k] + "\n<script>const BANK5 = " + b5 + ";</script>" + html[k:]

# ---------- CSS
rep(".pill.hardest{background:var(--accent);color:var(--accent-ink);border-color:transparent}",
    ".pill.hardest{background:var(--accent);color:var(--accent-ink);border-color:transparent}\n.pill.exam{background:var(--surface);color:var(--text);border-color:var(--line)}\n.hero > *{min-width:0}\n#app{grid-template-columns:minmax(0,1fr)}")
rep("  .hero{grid-template-columns:1fr}", "  .hero{grid-template-columns:minmax(0,1fr)}")

# ---------- config: the final's date and scope
rep('{name:"Final exam", date:"2026-12-08", time:"10:00–11:50 a.m.", where:"finals week", covers:"the whole course", ready:false}',
    '{name:"Final exam", date:"2026-12-08", time:"10:00–11:50 a.m.", where:"finals week", covers:"the Ch. 9 and 10 cycles after Exam 2, built on the Ch. 5–7 skills", ready:true}')

# ---------- registry
rep("const TPL = {}; BANK.templates.concat(BANK3.templates, BANK4.templates).forEach(t => TPL[t.id] = t);",
    "const TPL = {}; BANK.templates.concat(BANK3.templates, BANK4.templates, BANK5.templates).forEach(t => TPL[t.id] = t);\n"
    "const ORDER5 = BANK5.templates.map(t => t.id), ORDER5X = BANK5.templates.filter(t => t.tier === \"exam\").map(t => t.id);\n"
    "const pillCls = t => t.tier === \"hardest\" ? \"hardest\" : t.tier === \"exam\" ? \"exam\" : \"tier\";")
rep('const TIER = {challenge:"Challenge", hardest:"Hardest"};', 'const TIER = {challenge:"Challenge", hardest:"Hardest", exam:"Exam level"};')
rep("const ORDER = ORDER2.concat(ORDER1);", "const ORDER = ORDER5X.concat(ORDER2, ORDER1);")
rep('9:"Ch. 9 · Gas power cycles"};', '9:"Ch. 9 · Gas power cycles", 10:"Ch. 10 · Vapor and combined power cycles"};')
rep('"A-4E","A-11E","Given / computed"];', '"A-4E","A-5E","A-6E","A-11E","Given / computed"];')

# ---------- nav and router
rep('    <a href="#home" data-tab="home">Home</a>\n', '    <a href="#home" data-tab="home">Home</a>\n    <a href="#final" data-tab="final">Final exam</a>\n')
rep("const VIEWS = {home:viewHome, guided:viewGuided, challenge:viewChallenge,", "const VIEWS = {home:viewHome, final:viewFinal, guided:viewGuided, challenge:viewChallenge,")
rep('go(TPL[tid] && TPL[tid].tier ? "challenge" : "guided"); }', 'go(TPL[tid] && TPL[tid].grp === "final" ? "final" : TPL[tid] && TPL[tid].tier ? "challenge" : "guided"); }')
rep('${t.tier ? ` · <span class="pill ${t.tier === "hardest" ? "hardest" : "tier"}">${TIER[t.tier]}</span>` : ""}</div></div>',
    '${t.tier ? ` · <span class="pill ${pillCls(t)}">${TIER[t.tier]}</span>` : ""}${t.us ? ` · <span class="pill">US units</span>` : ""}</div></div>')

# ---------- guided tab heading: Exam 2 material is still on the final
rep('Exam 2 problems come first; Exam 1 problems are below for review.', 'Ch. 5–7 and 9 problems come first (the final builds on them); Exam 1 problems are below for review. The final\'s new cycle problems are on the Final exam tab.')
rep('<div class="eyebrow" style="font-size:.85rem;color:var(--accent-text)">Exam 2 · Ch. 5–7 and 9</div>', '<div class="eyebrow" style="font-size:.85rem;color:var(--accent-text)">Exam 2 material · Ch. 5–7 and 9</div>')

# ---------- final tab
rep("function pickVariant(tid){", r"""function viewFinal(app){
  G = null;
  const ex = BANK5.templates.filter(t => t.tier === "exam"), hard = BANK5.templates.filter(t => t.tier !== "exam");
  const solid = ORDER5X.filter(id => status(id) === "solid").length;
  app.append(el(`<section><h2>Final exam practice</h2><p class="muted" style="margin-top:4px">The cycles taught after Exam 2: Diesel, Brayton and its improvements, jet propulsion, Stirling and Ericsson, the Rankine cycle with reheat and regeneration, cogeneration, and combined gas-steam plants. Every one is still a set of Ch. 5 control volumes, a property table and a Ch. 6–7 limit, so the Exam 2 problems on the Guided problems tab are review for the final too. Same eight steps, same Worked, Guided and Solo modes, new numbers every time. Check Canvas for the final exam topics list.</p></section>`));
  app.append(el(`<section class="grid2">
      <div class="card list"><div class="eyebrow">How to use this tab</div>
        <ul class="clean small"><li>Start with the <b>exam-level</b> problems: Worked first, then Guided, then Solo.</li>
        <li>Rankine problems live in the steam tables. Do a round of the Properties drill if lookups feel slow.</li>
        <li>Then climb to the <b>Challenge</b> and <b>Hardest</b> problems, shaped like the hardest problems on past finals.</li>
        <li>A few days before the final, take the timed Final practice exam.</li></ul></div>
      <div class="card list"><div class="eyebrow">Three levels</div>
        <p class="small"><span class="pill exam">Exam level</span> The size of one final exam problem. About 15 to 25 minutes.</p>
        <p class="small"><span class="pill tier">Challenge</span> One or two steps past an exam problem. About 20 to 30 minutes.</p>
        <p class="small"><span class="pill hardest">Hardest</span> Several ideas at once. Give yourself 30 to 45 minutes.</p>
        <p class="small muted">${solid} of ${ORDER5X.length} exam-level problems solid on this device.</p>
        <div class="row"><button class="btn primary" id="fex">Final practice exam</button></div></div>
    </section>`));
  $("#fex", app).onclick = () => { S.exsel = "fin"; save(); go("exam"); };
  const card = t => {
    const st = status(t.id);
    const c = el(`<div class="card" style="display:grid;gap:10px"><div class="row" style="justify-content:space-between;align-items:flex-start"><b>${esc(t.title)}</b><span class="row" style="gap:6px"><span class="pill ${pillCls(t)}">${TIER[t.tier]}</span>${t.us ? `<span class="pill">US units</span>` : ""}<span class="pill ${st}">${STATUS_LABEL[st]}</span></span></div>
      ${t.note ? `<div class="small muted">${esc(t.note)}</div>` : ""}
      <div class="row"><button class="btn" data-m="worked">Worked</button><button class="btn primary" data-m="guided">Guided</button><button class="btn" data-m="solo">Solo</button></div></div>`);
    $$("button", c).forEach(b => b.onclick = () => openProblem(t.id, b.dataset.m));
    return c;
  };
  const block = (title, list, blurb) => {
    app.append(el(`<div class="eyebrow" style="font-size:.85rem;color:var(--accent-text);margin-top:6px">${title}</div>`));
    if (blurb) app.append(el(`<p class="small muted" style="margin:-4px 0 0">${blurb}</p>`));
    for (const ch of [9, 10]){
      const these = list.filter(t => t.ch === ch); if (!these.length) continue;
      const sec = el(`<section class="list"><div class="eyebrow">${CHNAME[ch]}</div><div class="grid2"></div></section>`);
      these.forEach(t => $(".grid2", sec).append(card(t)));
      app.append(sec);
    }
  };
  block("Exam level", ex, "Two are in US units (°F, psia, Btu), as old finals were; the English tables have an E after the number.");
  block("Harder than the final: Challenge and Hardest", hard, "Several are remade from past ENGR&amp;224 finals with new numbers.");
  const rev = el(`<section class="card list"><div class="eyebrow">Review from Exam 2</div><p class="small">The Diesel and dual cycles (Otto too) and the Ch. 5–7 devices, second-law and entropy problems are on the Guided problems tab. The Exam 2 debrief habits still apply: name the system, write the full balance and cross out terms, and justify the property model.</p><div class="row"><button class="btn" id="tog">Guided problems</button><button class="btn" id="toc">Challenge problems</button></div></section>`);
  $("#tog", rev).onclick = () => go("guided"); $("#toc", rev).onclick = () => go("challenge");
  app.append(rev);
}
function pickVariant(tid){""")

# ---------- home: final card, final track, stats
rep("""  app.append(el(`<section class="card exam2 list"><div class="eyebrow">New for Exam 2</div>""",
    """  app.append(el(`<section class="card exam2 list"><div class="eyebrow">New for the final</div>
      <p><b>Final exam tab:</b> ${ORDER5X.length} exam-level problems on Diesel and Brayton cycles, jet propulsion, the Rankine cycle with reheat and feedwater heaters, cogeneration and the steam Carnot cycle, plus ${ORDER5.length - ORDER5X.length} harder ones (combined cycles, Stirling and Ericsson, and remakes of past finals), each with a full worked solution in the eight steps.</p>
      <p class="small muted">Then take the Final practice exam: five problems, 110 minutes, like the real slot.</p>
      <div class="row"><button class="btn primary" data-go="final">Final exam problems</button><button class="btn" id="hfex">Final practice exam</button></div></section>`));
  app.append(el(`<section class="card exam2 list"><div class="eyebrow">Exam 2 drills, still useful</div>""")
rep("  $$(\"[data-go]\", app).forEach(b => b.onclick = () => go(b.dataset.go));",
    "  $$(\"[data-go]\", app).forEach(b => b.onclick = () => go(b.dataset.go));\n  $(\"#hfex\", app).onclick = () => { S.exsel = \"fin\"; save(); go(\"exam\"); };")
rep("""const STATIONS = [{name:"Properties", ids:["LOC"]}, {name:"Which table?", ids:["MDL"]}, {name:"Devices", ids:["E1","E2","E3","E4","E5"]},
  {name:"Exchangers & mixing", ids:["E6","E7","E8","E9"]}, {name:"Second law", ids:["E10","E11","E12"]}, {name:"Entropy", ids:["E13","E14","E15"]}, {name:"Cycles", ids:["E16","E17","E18"]}];""",
    """const STATIONS_E2 = [{name:"Properties", ids:["LOC"]}, {name:"Which table?", ids:["MDL"]}, {name:"Devices", ids:["E1","E2","E3","E4","E5"]},
  {name:"Exchangers & mixing", ids:["E6","E7","E8","E9"]}, {name:"Second law", ids:["E10","E11","E12"]}, {name:"Entropy", ids:["E13","E14","E15"]}, {name:"Cycles", ids:["E16","E17","E18"]}];
/* Final exam track (Nov 23): exam-level problems only, so the harder sets never block the picture */
const STATIONS = [{name:"Properties", ids:["LOC"]}, {name:"Diesel & Brayton", ids:["E17","X1","E19","E20","X2"]}, {name:"Jet propulsion", ids:["X3"]},
  {name:"Rankine", ids:["X4","X8"]}, {name:"Reheat & regeneration", ids:["X5","X6"]}, {name:"Cogeneration", ids:["X7"]}, {name:"Entropy review", ids:["E13","E14","E15"]}];""")
rep("const stationLit = st => st.ids.filter(skillSolid).length >= Math.min(2, st.ids.length);",
    "const stationLit = st => st.ids.filter(skillSolid).length >= Math.min(2, st.ids.length);")
rep("  const solid = ORDER2.filter(id => status(id) === \"solid\").length;\n  const ex2 = S.exams.filter(x => x.which === \"e2\");",
    "  const solid = ORDER5X.filter(id => status(id) === \"solid\").length;\n  const ex2 = S.exams.filter(x => x.which === \"fin\");")
rep('<div class="stat"><span class="small muted">Exam 2 problems solid</span><b>${solid} / ${ORDER2.length}</b></div>',
    '<div class="stat"><span class="small muted">Final exam-level problems solid</span><b>${solid} / ${ORDER5X.length}</b></div>')
rep('<div class="stat"><span class="small muted">Best Exam 2 practice</span>', '<div class="stat"><span class="small muted">Best Final practice</span>')
rep("The bunny eats a lettuce once two of that topic's problems are solid, then hops on to the next one;",
    "The bunny is working toward the final now. It eats a lettuce once two of that topic's exam-level problems are solid (one, where a topic has only one), then hops on to the next;")
rep("Properties turn solid at 80% over 15 states, and Which table? at 80% over 20 cards.", "Properties turn solid at 80% over 15 states.")
rep('<p class="small muted">Six problems, two hours, 100 points: Exam 2 by default, Exam 1 for review.</p>',
    '<p class="small muted">The Final by default: five problems, 110 minutes, 100 points. Exams 1 and 2 stay for review.</p>')

# ---------- practice exam: the Final
rep('const SLOTS3 = ', 'const SLOTS5 = [{ids:["E17","X1","E19","E20","X2"], pts:20}, {ids:["X4","X5"], pts:20}, {ids:["X6","X7","F3"], pts:22}, {ids:["X3","X8","F6","F7"], pts:18}, {ids:["E3","E6","E7","E10","E11","E13","E14"], pts:20}];\nconst SLOTS3 = ')
rep('const EXDEF = {\n', 'const EXDEF = {\n'
    '  fin:{name:"Final", covers:"Ch. 9 and 10, built on Ch. 5–7", mins:110, intro:"Five problems shaped like a final: a gas power cycle (Diesel or Brayton), a Rankine cycle, an improved Rankine cycle or cogeneration plant, a jet engine, steam Carnot, Stirling or Ericsson problem, and one Ch. 5–7 review problem (a device, a second-law claim, or entropy).", tables:"Çengel tables (A-1, A-2a, A-4 to A-6, A-17, and A-2Ea, A-4E to A-6E for US units)"},\n')
rep("function newExam(which){\n  which = which || S.exsel || \"e2\";",
    "function newExam(which){\n  which = which || S.exsel || \"fin\";\n  if (which === \"fin\") return {id:Date.now(), which, probs:SLOTS5.map(sl => { const tid = sl.ids[rnd(sl.ids.length)]; return {k:\"tpl\", tid, vi:rnd(TPL[tid].v.length), pts:sl.pts}; }), ans:{}, self:{}, left:110 * 60, paused:false, cur:0, graded:false};")
rep('  const X = S.exsel || "e2", D = EXDEF[X];', '  const X = S.exsel || "fin", D = EXDEF[X];')
rep('${D.intro} Two hours, 100 points.', '${D.intro} ${D.mins ? D.mins + " minutes" : "Two hours"}, 100 points.')
rep('${["e2", "ec", "e1"].map(k => [k, EXDEF[k]])', '${["fin", "e2", "ec", "e1"].map(k => [k, EXDEF[k]])')
rep('<td>${x.which === "e2" ? "2" : x.which === "ec" ? "Challenge" : "1"}</td>', '<td>${x.which === "fin" ? "Final" : x.which === "e2" ? "2" : x.which === "ec" ? "Challenge" : "1"}</td>')
rep('<p class="muted">Two hours. Tables, calculator, and your formula sheet allowed. Show every problem in the eight steps.</p>',
    '<p class="muted">${D.mins ? D.mins + " minutes" : "Two hours"}. Tables, calculator, and your formula sheet allowed. Show every problem in the eight steps.</p>')
rep('        ${X !== "e1" ? `<ul class="clean"><li>Mass balance',
    '''        ${X === "fin" ? `<ul class="clean"><li>Steady-flow first law for every device in a cycle, with the terms each keeps; mass splits at extractions and feedwater heaters</li>
        <li>Diesel and dual: T<sub>3</sub> = r<sub>c</sub>T<sub>2</sub>, q<sub>in</sub> = h<sub>3</sub> − h<sub>2</sub>, q<sub>out</sub> = u<sub>4</sub> − u<sub>1</sub>; MEP = w<sub>net</sub>/(v<sub>1</sub> − v<sub>2</sub>); v<sub>r</sub> for volume ratios, P<sub>r</sub> for pressure ratios</li>
        <li>Brayton: T<sub>2</sub>/T<sub>1</sub> = r<sub>p</sub><sup>(k−1)/k</sup>; back work ratio; regenerator effectiveness ε = (T<sub>5</sub> − T<sub>2</sub>)/(T<sub>4</sub> − T<sub>2</sub>); intercooling and reheat</li>
        <li>Jet propulsion: turbine work = compressor work; V = √(2Δh) with Δh in J/kg; F = ṁ(V<sub>exit</sub> − V<sub>inlet</sub>); Ẇ<sub>P</sub> = FV<sub>aircraft</sub>; η<sub>P</sub> = Ẇ<sub>P</sub>/Q̇<sub>in</sub></li>
        <li>Stirling and Ericsson: isothermal heat transfer, q = RT ln(ratio); what an ideal regenerator does</li>
        <li>Rankine: w<sub>p</sub> = vΔP (and the 5.404 psia·ft³/Btu bridge in US units); x = (s − s<sub>f</sub>)/s<sub>fg</sub>; η<sub>T</sub>, η<sub>P</sub>; reheat adds a second q<sub>in</sub> and w<sub>T</sub></li>
        <li>Feedwater heaters: open (mixing) and closed (no mixing, drain pumped forward or trapped back) energy balances for y</li>
        <li>Cogeneration: utilization factor ε<sub>u</sub> = (Ẇ<sub>net</sub> + Q̇<sub>p</sub>)/Q̇<sub>in</sub>; combined cycles: the heat-recovery steam generator balance links the two loops</li>
        <li>Carnot limit in kelvins; entropy generation in each device and at each reservoir</li>
        <li>Your property-model rules: steam tables for water in every phase; A-17 or cold-air-standard for air, as the problem says</li></ul>` : X !== "e1" ? `<ul class="clean"><li>Mass balance''')

open(DST, "w", encoding="utf-8").write(html)
print("ok", len(html), [t["id"] for t in tpls])
