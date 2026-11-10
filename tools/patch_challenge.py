"""Fourth patch (Nov 2026): Challenge problems, harder than Exam 2. Runs on the current index.html in place.
Usage: python3 patch_challenge.py ../index.html challenge_templates.json"""
import json, sys
DST, SRC = sys.argv[1], sys.argv[2]
html = open(DST, encoding="utf-8").read()
assert "const BANK4" not in html, "already patched"
tpls = json.load(open(SRC, encoding="utf-8"))
for t in tpls:
    for v in t["v"]: v.pop("_p", None)
b4 = json.dumps({"templates": tpls}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

def rep(old, new, count=1):
    global html
    n = html.count(old)
    assert n == count, (n, old[:140])
    html = html.replace(old, new)

# ---------- data, after BANK3
i = html.index("<script>const BANK3 = "); j = html.index("</script>", i) + len("</script>")
html = html[:j] + "\n<script>const BANK4 = " + b4 + ";</script>" + html[j:]

# ---------- CSS
rep(".pill.practicing{background:var(--near-bg);color:var(--near);border-color:transparent}",
    ".pill.practicing{background:var(--near-bg);color:var(--near);border-color:transparent}\n.pill.tier{background:var(--accent-soft);color:var(--accent-text);border-color:transparent}\n.pill.hardest{background:var(--accent);color:var(--accent-ink);border-color:transparent}")

# ---------- English tables for the US-unit problems
rep('const TABLES = ["A-1","A-2a","A-3","A-4","A-5","A-6","A-7","A-11","A-12","A-13","A-17","Given / computed"];',
    'const TABLES = ["A-1","A-2a","A-3","A-4","A-5","A-6","A-7","A-11","A-12","A-13","A-17","A-1E","A-2Ea","A-4E","A-11E","Given / computed"];')

# ---------- nav
rep('    <a href="#guided" data-tab="guided">Guided problems</a>\n',
    '    <a href="#guided" data-tab="guided">Guided problems</a>\n    <a href="#challenge" data-tab="challenge">Challenge</a>\n')

# ---------- registry and router
rep("const TPL = {}; BANK.templates.concat(BANK3.templates).forEach(t => TPL[t.id] = t);",
    "const TPL = {}; BANK.templates.concat(BANK3.templates, BANK4.templates).forEach(t => TPL[t.id] = t);\nconst ORDER4 = BANK4.templates.map(t => t.id);\nconst TIER = {challenge:\"Challenge\", hardest:\"Hardest\"};")
rep("const VIEWS = {home:viewHome, guided:viewGuided, locator:viewLocator, model:viewModel, triage:viewTriage, exam:viewExam};",
    "const VIEWS = {home:viewHome, guided:viewGuided, challenge:viewChallenge, locator:viewLocator, model:viewModel, triage:viewTriage, exam:viewExam};")
rep('function openFrom(tid, mode){ PENDING = () => openProblem(tid, mode); go("guided"); }',
    'function openFrom(tid, mode){ PENDING = () => openProblem(tid, mode); go(TPL[tid] && TPL[tid].tier ? "challenge" : "guided"); }')

# ---------- problem header shows the tier
rep('<div class="small muted">${CHNAME[t.ch]} · version ${vi + 1} of ${t.v.length}</div>',
    '<div class="small muted">${CHNAME[t.ch]} · version ${vi + 1} of ${t.v.length}${t.tier ? ` · <span class="pill ${t.tier === "hardest" ? "hardest" : "tier"}">${TIER[t.tier]}</span>` : ""}</div>')

# ---------- challenge list view
rep("function pickVariant(tid){", r"""function viewChallenge(app){
  G = null;
  const solid = ORDER4.filter(id => status(id) === "solid").length;
  app.append(el(`<section><h2>Challenge problems</h2><p class="muted" style="margin-top:4px">These are harder than Exam 2 on purpose: several devices in one problem, an entropy balance on top of the energy balance, or a cycle you have to build from the pieces. Same eight steps, same Worked, Guided and Solo modes, new numbers every time. They're ungraded practice, so getting stuck here costs nothing and teaches the most.</p></section>`));
  app.append(el(`<section class="grid2">
      <div class="card list"><div class="eyebrow">How to use them</div>
        <ul class="clean small"><li>Get the matching exam-level problem to Solid on the Guided problems tab first.</li>
        <li>Stuck? Open the problem in <b>Worked</b> mode and predict each step before you reveal it. That's practice, not cheating.</li>
        <li>Then <b>Guided</b> with new numbers, then <b>Solo</b>.</li>
        <li>Work with a classmate. Explaining why a term drops out is the fastest way to find out whether you know it.</li></ul></div>
      <div class="card list"><div class="eyebrow">Two levels</div>
        <p class="small"><span class="pill tier">Challenge</span> One or two steps past an exam problem. About 20 to 30 minutes.</p>
        <p class="small"><span class="pill hardest">Hardest</span> Several ideas at once, shaped like the hardest problems on past finals. Give yourself 30 to 45 minutes.</p>
        <p class="small muted">${solid} of ${ORDER4.length} solid on this device.</p>
        <div class="row"><button class="btn" id="cex">Challenge practice exam</button></div></div>
    </section>`));
  $("#cex", app).onclick = () => { S.exsel = "ec"; save(); go("exam"); };
  const card = t => {
      const st = status(t.id);
      const c = el(`<div class="card" style="display:grid;gap:10px"><div class="row" style="justify-content:space-between;align-items:flex-start"><b>${esc(t.title)}</b><span class="row" style="gap:6px"><span class="pill ${t.tier === "hardest" ? "hardest" : "tier"}">${TIER[t.tier]}</span>${t.us ? `<span class="pill">US units</span>` : ""}<span class="pill ${st}">${STATUS_LABEL[st]}</span></span></div>
        ${t.note ? `<div class="small muted">${esc(t.note)} · ${CHNAME[t.ch].split(" · ")[0]}</div>` : ""}
        <div class="row"><button class="btn" data-m="worked">Worked</button><button class="btn primary" data-m="guided">Guided</button><button class="btn" data-m="solo">Solo</button></div></div>`);
      $$("button", c).forEach(b => b.onclick = () => openProblem(t.id, b.dataset.m));
      return c;
  };
  const past = el(`<section class="list"><div class="eyebrow">Remade from past exams</div><p class="small muted" style="margin:4px 0 10px">New numbers and fixes on problems from earlier ENGR&amp;224 exams and finals. Three use US units (°F, psia, lbm, Btu), as old exams did; the English tables are in your book's appendix with an E after the number.</p><div class="grid2"></div></section>`);
  BANK4.templates.filter(t => t.grp === "past").forEach(t => $(".grid2", past).append(card(t)));
  app.append(past);
  for (const ch of [5, 6, 7, 9]){
    const sec = el(`<section class="list"><div class="eyebrow">${CHNAME[ch]}</div><div class="grid2"></div></section>`);
    BANK4.templates.filter(t => t.ch === ch && t.grp !== "past").forEach(t => {
      const st = status(t.id);
      const c = el(`<div class="card" style="display:grid;gap:10px"><div class="row" style="justify-content:space-between;align-items:flex-start"><b>${esc(t.title)}</b><span class="row" style="gap:6px"><span class="pill ${t.tier === "hardest" ? "hardest" : "tier"}">${TIER[t.tier]}</span><span class="pill ${st}">${STATUS_LABEL[st]}</span></span></div>
        <div class="row"><button class="btn" data-m="worked">Worked</button><button class="btn primary" data-m="guided">Guided</button><button class="btn" data-m="solo">Solo</button></div></div>`);
      $$("button", c).forEach(b => b.onclick = () => openProblem(t.id, b.dataset.m));
      $(".grid2", sec).append(c);
    });
    app.append(sec);
  }
}
function pickVariant(tid){""")

# ---------- home card
rep("""      <div class="row"><button class="btn primary" data-go="locator">Property drill</button><button class="btn" data-go="model">Which table?</button></div></section>`));""",
    """      <div class="row"><button class="btn primary" data-go="locator">Property drill</button><button class="btn" data-go="model">Which table?</button></div></section>`));
  app.append(el(`<section class="card exam2 list"><div class="eyebrow">New: harder than the exam</div>
      <p><b>Challenge problems:</b> ${ORDER4.length} problems built to be tougher than Exam 2, each with a full worked solution in the eight steps: a turbine and bypass valve feeding a mixer, a jet engine core, a regenerative gas turbine on two fuels, a heat-driven vaccine cooler, plus nine remade from past exams, some in US units.</p>
      <p class="small muted">Practice that's harder than the test pays off on the test. Start with the exam-level problems, then climb.</p>
      <div class="row"><button class="btn primary" data-go="challenge">Challenge problems</button></div></section>`));""")

# ---------- practice exam: a third option
rep('const SLOTS2 = ["TABLE2", ["E1","E2","E3","E4","E5"], ["E6","E7","E8","E9"], ["E10","E11","E12"], ["E13","E14","E15"], ["E16","E17","E18","E19","E20"]];',
    'const SLOTS2 = ["TABLE2", ["E1","E2","E3","E4","E5"], ["E6","E7","E8","E9"], ["E10","E11","E12"], ["E13","E14","E15"], ["E16","E17","E18","E19","E20"]];\n'
    'const SLOTS3 = ["TABLE2", ["C2","C15","P3"], ["C16","C3","P1"], ["C7","C8","P2","P9"], ["C1","C4","C5","C6","C9","P4","P5","P6","P7","P8"], ["C10","C11","C12","C13","C14"]];')
rep('  e2:{name:"Exam 2", covers:"Ch. 5–7 and Ch. 9 through Brayton",',
    '  ec:{name:"Challenge", covers:"Ch. 5–7 and 9, harder than Exam 2", intro:"Six problems built to be harder than Exam 2: a water and R-134a table fill-in, then a multi-stream device, a heat exchanger with entropy generation, a second-law problem, an entropy problem and a cycle, all from the Challenge set. Most people won\'t finish in two hours; take it a few days before the exam, then study the worked solutions for whatever you didn\'t reach.", tables:"Çengel tables (A-1 to A-7, A-11 to A-13, A-17)"},\n'
    '  e2:{name:"Exam 2", covers:"Ch. 5–7 and Ch. 9 through Brayton",')
rep('  const slots = which === "e2" ? SLOTS2 : SLOTS;', '  const slots = which === "e2" ? SLOTS2 : which === "ec" ? SLOTS3 : SLOTS;')
rep('${Object.entries(EXDEF).reverse().map(([k, d]) =>', '${["e2", "ec", "e1"].map(k => [k, EXDEF[k]]).map(([k, d]) =>')
rep('        ${X === "e2" ? `<ul class="clean"><li>Mass balance', '        ${X !== "e1" ? `<ul class="clean"><li>Mass balance')
rep('<td>${x.which === "e2" ? "2" : "1"}</td>', '<td>${x.which === "e2" ? "2" : x.which === "ec" ? "Challenge" : "1"}</td>')
rep('For each state${E.which === "e2" ? " of water or R-134a" : " of water"}', 'For each state${E.which === "e2" || E.which === "ec" ? " of water or R-134a" : " of water"}')

open(DST, "w", encoding="utf-8").write(html)
print("ok", len(html))
