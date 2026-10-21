"""Patch the exam-prep page: add Exam 2 data (BANK2), the upgraded Properties drill, and the Which table? deck."""
import json, sys
SRC, DST = sys.argv[1], sys.argv[2]
G = "/tmp/claude-0/-home-claude/146417c8-8d3c-5b91-94f8-ad9df4b6a0c2/scratchpad/gen/"
html = open(SRC, encoding="utf-8").read()

states = json.load(open(G + "states2_final.json"))
curves = json.load(open(G + "curves2.json"))
model = json.load(open(G + "model.json"))
bank2 = {"version": "Exam 2 · Ch. 5–7, 9 · fall 2026", "states": states, "iso": curves["iso"], "rdome": curves["rdome"], "model": model}
b2 = json.dumps(bank2, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

def rep(old, new, count=1):
    global html
    n = html.count(old)
    assert n == count, (n, old[:120])
    html = html.replace(old, new)

# ---------- data
marker = "<script>const BANK = "
i = html.index(marker); j = html.index("</script>", i) + len("</script>")
html = html[:j] + "\n<script>const BANK2 = " + b2 + ";</script>" + html[j:]

# ---------- CSS
rep("@media (max-width:640px){\n  .stemwrap", """.ctx{background:var(--surface);border-left:4px solid var(--accent);border-radius:6px;padding:8px 12px}
.fluidtag{display:inline-block;font-size:.74rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;border-radius:999px;padding:2px 10px;background:var(--accent-soft);color:var(--accent-text)}
ol.wsteps{margin:4px 0 0;padding-left:1.3em;display:grid;gap:4px}
details.rules summary{cursor:pointer;font-weight:700;min-height:28px}
details.rules dl{display:grid;gap:10px;margin:12px 0 0}
details.rules dt{font-weight:700}
details.rules dd{margin:2px 0 0}
.exam2{border-color:var(--accent)}
@media (max-width:640px){
  .stemwrap""")

# ---------- nav
rep("""    <a href="#guided" data-tab="guided">Guided problems</a>
    <a href="#locator" data-tab="locator">State locator</a>
    <a href="#triage" data-tab="triage">Triage</a>""",
    """    <a href="#locator" data-tab="locator">Properties</a>
    <a href="#model" data-tab="model">Which table?</a>
    <a href="#guided" data-tab="guided">Guided problems</a>
    <a href="#triage" data-tab="triage">Triage</a>""")

# ---------- footer
rep("""    <div>Property values follow Çengel &amp; Boles, <i>Thermodynamics: An Engineering Approach</i>, Tables A-1 to A-6, generated from the same IAPWS-95 formulation the book's steam tables use. Answers accept small differences from your own interpolation.</div>""",
    """    <div>Property values follow Çengel &amp; Boles, <i>Thermodynamics: An Engineering Approach</i>. Steam values (Tables A-4 to A-7) come from the IAPWS-95 formulation the book's steam tables use. R-134a values (Tables A-11 to A-13) come from the Tillner-Roth and Baehr equation of state the book's tables are built on, with h and s set to zero for saturated liquid at −40 °C, as in the book. Your printed tables may differ in the last digit, and answers accept small differences from your own interpolation.</div>""")

# ---------- config
rep('{name:"Exam 2", date:"2026-11-20", time:"10:00 a.m.–12:00 p.m.", where:"in person", covers:"Ch. 5–7 and Ch. 9 through Brayton", ready:false}',
    '{name:"Exam 2", date:"2026-11-20", time:"10:00 a.m.–12:00 p.m.", where:"in person", covers:"Ch. 5–7 and Ch. 9 through Brayton", ready:true}')
rep("const VER = BANK.version;", "const VER = BANK2.version;")
rep('const PNAME = {v:"specific volume, v", u:"internal energy, u", h:"enthalpy, h", T:"temperature, T", P:"pressure, P", x:"quality, x"};\nconst PUNIT = {v:"m³/kg", u:"kJ/kg", h:"kJ/kg", T:"°C", P:"kPa", x:""};',
    'const PNAME = {v:"specific volume, v", u:"internal energy, u", h:"enthalpy, h", s:"entropy, s", T:"temperature, T", P:"pressure, P", x:"quality, x"};\nconst PUNIT = {v:"m³/kg", u:"kJ/kg", h:"kJ/kg", s:"kJ/kg·K", T:"°C", P:"kPa", x:""};\nconst LOCTF = {w:["A-4","A-5","A-6","A-7"], r:["A-11","A-12","A-13"]};\nconst FLN = {w:"Water", r:"R-134a"};')
rep("loc:{n:0, ok:0, streak:0, best:0}, tri:{n:0, ok:0}, exams:[], exam:null, optout:false}, store.get());",
    "loc:{n:0, ok:0, streak:0, best:0}, tri:{n:0, ok:0}, mdl:{n:0, ok:0}, exams:[], exam:null, optout:false}, store.get());")
rep("S = {mastery:{}, seen:{}, loc:{n:0, ok:0, streak:0, best:0}, tri:{n:0, ok:0}, exams:[], exam:null, optout:keep};",
    "S = {mastery:{}, seen:{}, loc:{n:0, ok:0, streak:0, best:0}, tri:{n:0, ok:0}, mdl:{n:0, ok:0}, exams:[], exam:null, optout:keep};")

# ---------- T-v plot (both fluids)
i = html.index("function tvPlot(st){"); j = html.index("function fmtP(p)")
html = html[:i] + r"""const TVCFG = {
  w:{vmin:-3.15, vmax:2.35, Tmin:0, Tmax:850, vt:[0.001, 0.01, 0.1, 1, 10, 100], Tt:[0, 200, 400, 600, 800], name:"water",
     lab:[["mixture", 0.06, 90, "middle"], ["superheated vapor", 15, 560, "middle"], ["compressed liquid", 0.00105, 700, "start"]]},
  r:{vmin:-3.25, vmax:-0.2, Tmin:-50, Tmax:180, vt:[0.001, 0.01, 0.1], Tt:[-40, 0, 40, 80, 120, 160], name:"R-134a",
     lab:[["mixture", 0.004, 40, "middle"], ["superheated vapor", 0.09, 150, "middle"], ["compressed liquid", 0.00062, 160, "start"]]}
};
const ISO_W = Object.assign({}, BANK.locator.isobars, BANK2.iso.w);
function tvPlot(st){
  const c = TVCFG[st.fluid === "r" ? "r" : "w"];
  const W = 520, H = 310, L = 50, R = 14, T = 16, B = 42;
  const X = v => L + (Math.log10(v) - c.vmin) / (c.vmax - c.vmin) * (W - L - R);
  const Y = t => H - B - (t - c.Tmin) / (c.Tmax - c.Tmin) * (H - T - B);
  const dome = st.fluid === "r" ? BANK2.rdome : BANK.locator.dome;
  const pts = dome.liq.map(p => [X(p[1]), Y(p[0])]).concat(dome.vap.slice().reverse().map(p => [X(p[1]), Y(p[0])]));
  let s = `<svg class="tv" viewBox="0 0 ${W} ${H}" role="img" aria-label="T-v diagram for ${c.name} with the saturation dome, the isobar through the state, and the state point">`;
  for (const v of c.vt){ const x = X(v); s += `<path class="grid" d="M${x},${T} V${H - B}"/><text x="${x}" y="${H - B + 16}" text-anchor="middle">${v}</text>`; }
  for (const t of c.Tt){ const y = Y(t); s += `<path class="grid" d="M${L},${y} H${W - R}"/><text x="${L - 6}" y="${y + 4}" text-anchor="end">${String(t).replace("-", "−")}</text>`; }
  s += `<path class="ax" d="M${L},${T} V${H - B} H${W - R}"/>`;
  s += `<text x="${W - R}" y="${H - 6}" text-anchor="end">v, m³/kg (log scale)</text><text x="${L + 6}" y="${T + 12}" text-anchor="start">T, °C</text>`;
  s += `<path class="dome" d="M${pts.map(p => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" L")} Z"/>`;
  for (const [t, v, temp, a] of c.lab) s += `<text class="reg" x="${X(v) + (a === "start" ? 4 : 0)}" y="${Y(temp)}" text-anchor="${a}">${t}</text>`;
  const bar = (st.fluid === "r" ? BANK2.iso.r : ISO_W)[st.pk];
  if (bar){
    const bp = bar.filter(p => p[0] <= c.Tmax && p[0] >= c.Tmin && p[1] > 0).map(p => [X(p[1]), Y(p[0])]).filter(p => p[0] >= L && p[0] <= W - R);
    if (bp.length > 1) s += `<path class="bar" d="M${bp.map(p => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" L")}"/>`;
  }
  const px = X(st.pt.v), py = Y(st.pt.T);
  s += `<circle class="pt" cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="7"/>`;
  const lab = `P = ${fmtP(st.P)}`;
  const lx = Math.min(px + 12, W - R - 120);
  s += `<text class="lab" x="${lx.toFixed(1)}" y="${(py - 14).toFixed(1)}">${lab}</text>`;
  return s + "</svg>";
}
""" + html[j:]

# ---------- router, track, home
rep("const VIEWS = {home:viewHome, guided:viewGuided, locator:viewLocator, triage:viewTriage, exam:viewExam};",
    "const VIEWS = {home:viewHome, guided:viewGuided, locator:viewLocator, model:viewModel, triage:viewTriage, exam:viewExam};")
rep("""{name:"Closed: gases & liquids", ids:["T11","T12","T13"]}
];""", """{name:"Closed: gases & liquids", ids:["T11","T12","T13"]}, {name:"Which table?", ids:["MDL"]}
];""")
rep('function skillSolid(id){ return id === "LOC" ? locSolid() : status(id) === "solid"; }',
    'function mdlSolid(){ return S.mdl.n >= 20 && S.mdl.ok / S.mdl.n >= 0.8; }\nfunction skillSolid(id){ return id === "LOC" ? locSolid() : id === "MDL" ? mdlSolid() : status(id) === "solid"; }')
rep('aria-label="Progress: ${Math.round(frac * 100)}% of Exam 1 skills solid"', 'aria-label="Progress: ${Math.round(frac * 100)}% of skills solid"')
rep("""  app.append(el(`<section class="panel">${trackSVG()}<p class="small muted" style="margin-top:6px">The engine moves as skills turn solid. A guided skill is solid after two clean solves, one of them Solo. Tables turn solid at 80% over 15 states.</p></section>`));""",
    """  app.append(el(`<section class="card exam2 list"><div class="eyebrow">New for Exam 2</div>
      <p><b>Properties:</b> water and R-134a states, entropy included, with tricky ones and states inside turbines, compressors, valves and tanks.</p>
      <p><b>Which table?</b> Decide before you solve: steam or R-134a tables, constant c<sub>v</sub> or c<sub>p</sub>, the air table, a gas's own table, or the Z chart.</p>
      <div class="row"><button class="btn primary" data-go="locator">Property drill</button><button class="btn" data-go="model">Which table?</button></div></section>`));
  $$("[data-go]", app).forEach(b => b.onclick = () => go(b.dataset.go));
  app.append(el(`<section class="panel">${trackSVG()}<p class="small muted" style="margin-top:6px">The engine moves as skills turn solid. A guided skill is solid after two clean solves, one of them Solo. Properties turn solid at 80% over 15 states, and Which table? at 80% over 20 cards.</p></section>`));""")
rep("""      <div class="stat"><span class="small muted">State locator</span><b>${S.loc.n ? Math.round(100 * S.loc.ok / S.loc.n) + "%" : "–"}</b><span class="small muted">${S.loc.n} states · best streak ${S.loc.best}</span></div>""",
    """      <div class="stat"><span class="small muted">Properties</span><b>${S.loc.n ? Math.round(100 * S.loc.ok / S.loc.n) + "%" : "–"}</b><span class="small muted">${S.loc.n} states · best streak ${S.loc.best}</span></div>
      <div class="stat"><span class="small muted">Which table?</span><b>${S.mdl.n ? Math.round(100 * S.mdl.ok / S.mdl.n) + "%" : "–"}</b><span class="small muted">${S.mdl.n} cards</span></div>""")
rep("Mix in the State locator and Triage drills: table lookups and recognizing what kind of problem you're facing are where most exam points go.",
    "Mix in the Properties, Which table? and Triage drills: table lookups and recognizing what kind of problem you're facing are where most exam points go.")

# ---------- properties drill (locator)
i = html.index("const LOC = {filter:\"all\", recent:[]};"); j = html.index("/* ---------- triage ---------- */")
html = html[:i] + r"""const LOC = {filter:"all", fluid:"both", recent:[]};
const LFILT = [["all","All states"],["tricky","Tricky & in a device"],["s","Entropy"],["cl","Compressed liquid"],["mix","Mixtures"],["sh","Superheated"],["sat","Saturated liquid or vapor"],["interp","Needs interpolation"]];
const LFLUID = [["both","Water + R-134a"],["w","Water"],["r","R-134a"]];
const LSTATES = BANK.locator.states.map(s => Object.assign({fluid:"w", tags:[], ctx:"", atol:0}, s)).concat(BANK2.states);
function locPool(){
  const f = LOC.filter, fl = LOC.fluid;
  return LSTATES.filter(s => (fl === "both" || s.fluid === fl) &&
    (f === "all" || (f === "sat" ? (s.phase === "sl" || s.phase === "sv") : f === "interp" ? s.interp : f === "tricky" ? (s.tags.includes("tricky") || s.tags.includes("device")) : f === "s" ? s.tags.includes("s") : s.phase === f)));
}
function fmtT(v){ if (v === 0) return "0"; let s = sig(v, 5); if (s.includes(".")) s = s.replace(/0+$/, "").replace(/\.$/, ""); return s; }
function givenText(st){
  const g = st.given;
  const part = ([k, val, u]) => k === "T" ? `T = ${fmtT(val)} °C` : k === "P" ? `P = ${fmtP(val)}` : k === "x" ? `x = ${val}` : `${k} = ${String(val).replace("-", "−")} ${u}`;
  if (g[1][0] === "state") return `Saturated ${g[1][1].split(" ")[1]} ${st.fluid === "r" ? "R-134a" : "water"} at ${part(g[0])}`;
  return `${FLN[st.fluid]} at ${part(g[0])} and ${part(g[1])}`;
}
function tolEff(st){ return Math.max(st.tol, st.atol && st.answer ? st.atol / Math.abs(st.answer) : 0); }
function tolText(st){ return st.atol && st.atol > st.tol * Math.abs(st.answer) ? `within ±${st.atol} ${PUNIT[st.ask]}` : `within ${fmtTol(st.tol)}`; }
function viewLocator(app){
  app.append(el(`<section><h2>Property tables drill</h2><p class="muted" style="margin-top:4px">Water (Tables A-4 to A-7) and R-134a (Tables A-11 to A-13), mixed the way an exam mixes them. Find the phase, the table, and the value with your own Çengel tables.</p>
    <p class="small muted" style="margin-top:6px">Compressed liquid water: below 5 MPa, use saturated liquid at the same temperature (A-4); at 5 MPa and above, use A-7 when the state is on its grid. R-134a has no compressed-liquid table, so use saturated liquid at the same temperature (A-11).</p></section>`));
  const ff = el(`<div class="filters" role="group" aria-label="Fluid">${LFLUID.map(([k, l]) => `<button data-f="${k}" aria-pressed="${LOC.fluid === k}">${l}</button>`).join("")}</div>`);
  $$("button", ff).forEach(b => b.onclick = () => { LOC.fluid = b.dataset.f; $$("button", ff).forEach(x => x.setAttribute("aria-pressed", x === b)); nextState(); });
  app.append(ff);
  const f = el(`<div class="filters" role="group" aria-label="Filter states">${LFILT.map(([k, l]) => `<button data-f="${k}" aria-pressed="${LOC.filter === k}">${l}</button>`).join("")}</div>`);
  $$("button", f).forEach(b => b.onclick = () => { LOC.filter = b.dataset.f; $$("button", f).forEach(x => x.setAttribute("aria-pressed", x === b)); nextState(); });
  app.append(f);
  app.append(el(`<div class="small muted" id="locstats"></div>`));
  app.append(el(`<section id="locbox" class="list"></section>`));
  nextState();
}
function locStats(){ const b = $("#locstats"); if (b) b.textContent = `${S.loc.n} state${S.loc.n === 1 ? "" : "s"} · ${S.loc.n ? Math.round(100 * S.loc.ok / S.loc.n) : 0}% fully right · streak ${S.loc.streak} · best ${S.loc.best}`; }
function nextState(){
  locStats();
  const pool = locPool();
  const box = $("#locbox"); box.innerHTML = "";
  if (!pool.length){ box.append(el(`<p class="muted">No states match that combination. Try another filter.</p>`)); return; }
  let cands = pool.filter(s => !LOC.recent.includes(s.id)); if (!cands.length) cands = pool;
  const st = cands[rnd(cands.length)];
  LOC.recent = [st.id].concat(LOC.recent).slice(0, 60);
  const nm = uid("ph"), tn = uid("tb"), vid = uid("lv");
  const card = el(`<section class="card list">
      <div><span class="fluidtag">${FLN[st.fluid]}</span></div>
      ${st.ctx ? `<p class="ctx">${st.ctx}</p>` : ""}
      <div class="given">${givenText(st)}</div>
      <div class="muted">Find the ${PNAME[st.ask]}.</div>
      <div class="locq">
        <div><span class="eyebrow">1 · Phase</span><div class="seg">${Object.entries(PHASE).map(([k, l]) => `<label><input type="radio" name="${nm}" value="${k}">${l}</label>`).join("")}</div></div>
        <div><span class="eyebrow">2 · Table you read the value from</span><div class="seg">${LOCTF[st.fluid].map(t => `<label><input type="radio" name="${tn}" value="${t}">${t}</label>`).join("")}</div></div>
        <div><label class="eyebrow" for="${vid}">3 · ${PNAME[st.ask]}</label><div class="row"><input class="n" id="${vid}" inputmode="decimal" autocomplete="off" style="width:10rem"><span>${PUNIT[st.ask]}</span><span class="small muted">${tolText(st)}</span></div></div>
      </div>
      <div class="fb" aria-live="polite"></div>
      <div class="row"><button class="btn primary" id="lchk">Check</button><button class="btn" id="lnext">Skip</button></div>
    </section>`);
  box.append(card);
  $("#lnext", card).onclick = nextState;
  $("#lchk", card).onclick = () => {
    const ph = $(`input[name="${nm}"]:checked`, card), tb = $(`input[name="${tn}"]:checked`, card), inp = $("#" + vid, card);
    if (!ph || !tb || !inp.value.trim()) return setFb(card, "info", "Answer all three parts first.");
    const okP = ph.value === st.phase, okT = tb.value === st.table;
    const j = judge(inp.value, st.answer, tolEff(st), st.diag, PUNIT[st.ask]);
    ph.parentElement.classList.add(okP ? "right" : "wrong"); tb.parentElement.classList.add(okT ? "right" : "wrong");
    if (!okP) $$(`input[name="${nm}"]`, card).find(x => x.value === st.phase).parentElement.classList.add("right");
    if (!okT) $$(`input[name="${tn}"]`, card).find(x => x.value === st.table).parentElement.classList.add("right");
    inp.classList.add(j.ok ? "right" : "wrong");
    const all = okP && okT && j.ok;
    S.loc.n++; if (all){ S.loc.ok++; S.loc.streak++; S.loc.best = Math.max(S.loc.best, S.loc.streak); } else S.loc.streak = 0; save(); locStats();
    const ti = `Properties ${FLN[st.fluid]} ${st.phase}${st.interp ? " interp" : ""}${st.tags.includes("device") ? " device" : ""}`;
    track({m:"loc", t:"LOC", ti, n:"phase", ok:okP ? 1 : 0, d:okP ? "" : ph.value});
    track({m:"loc", t:"LOC", ti, n:"table", ok:okT ? 1 : 0, d:okT ? "" : tb.value});
    track({m:"loc", t:"LOC", ti, n:"value " + st.ask, ok:j.ok ? 1 : 0, d:j.ok ? "" : j.code});
    $$("input", card).forEach(x => x.disabled = true);
    const lines = [`<span class="mark ${okP ? "ok" : "bad"}">${okP ? "✓" : "✕"} Phase:</span> ${PHASE[st.phase]}`,
                   `<span class="mark ${okT ? "ok" : "bad"}">${okT ? "✓" : "✕"} Table:</span> ${st.table}`,
                   `<span class="mark ${j.ok ? "ok" : "bad"}">${j.ok ? "✓" : "✕"} Value:</span> ${withU(st.answer, PUNIT[st.ask])}${j.ok ? "" : ". " + j.msg}`];
    setFb(card, all ? "ok" : "bad", `<div><b class="tag">${all ? "All three right." : "Not quite."}</b></div><div>${lines.join("<br>")}</div>`);
    const ex = el(`<div class="list" style="gap:10px"><div class="panel"><div class="eyebrow">How to find it</div><ol style="margin:6px 0 0;padding-left:1.2em;display:grid;gap:4px">${st.why.map(w => `<li>${w}</li>`).join("")}</ol></div><div class="plotbox">${tvPlot(st)}</div><p class="small muted">The dashed line is the ${fmtP(st.P)} isobar for ${FLN[st.fluid] === "Water" ? "water" : "R-134a"}. Not on the course's table grid? It's drawn from the same equation of state.</p></div>`);
    $(".fb", card).after(ex);
    const b = $("#lchk", card); b.remove(); const n = $("#lnext", card); n.textContent = "Next state"; n.classList.add("primary"); n.focus({preventScroll:true});
  };
}

/* ---------- which table? ---------- */
const MCAT = [["all","All cards"],["fluid","Water & R-134a"],["gas","Which gas model"],["cvcp","c<sub>v</sub> or c<sub>p</sub>"],["isen","Isentropic"],["state","Is the state fixed?"]];
let MD = null;
function viewModel(app){
  app.append(el(`<section><h2>Which table?</h2><p class="muted" style="margin-top:4px">Ten cards a round. Don't solve anything: decide where the property values come from, which specific heat the energy balance needs, or whether the state is even fixed. Every answer comes with the reasoning, step by step.</p></section>`));
  app.append(el(`<details class="rules panel"><summary>The decision rules, in order</summary><dl>${BANK2.model.rules.map((r, i) => `<div><dt>${i + 1}. ${r.h}</dt><dd>${r.t}</dd></div>`).join("")}</dl></details>`));
  const f = el(`<div class="filters" role="group" aria-label="Card types">${MCAT.map(([k, l], i) => `<button data-c="${k}" aria-pressed="${i === 0}">${l}</button>`).join("")}</div>`);
  $$("button", f).forEach(b => b.onclick = () => { $$("button", f).forEach(x => x.setAttribute("aria-pressed", x === b)); mdlRound(b.dataset.c); });
  app.append(f);
  app.append(el(`<div class="small muted" id="mdlstats"></div>`));
  app.append(el(`<section id="mdbox" class="list"></section>`));
  mdlRound("all");
}
function mdlStats(){ const b = $("#mdlstats"); if (b) b.textContent = `${S.mdl.n} cards · ${S.mdl.n ? Math.round(100 * S.mdl.ok / S.mdl.n) : 0}% right`; }
function mdlRound(cat){
  const pool = BANK2.model.cards.filter(c => cat === "all" || c.cat === cat);
  MD = {cards:shuffle(pool.slice()).slice(0, 10), i:0, ok:0, missed:[], cat};
  mdlCard();
}
function mdlCard(){
  mdlStats();
  const box = $("#mdbox"); if (!box) return; box.innerHTML = "";
  if (MD.i >= MD.cards.length){
    const res = el(`<section class="card list"><div class="eyebrow">Round done</div><div class="score num">${MD.ok} / ${MD.cards.length}</div>
      ${MD.missed.length ? `<div><b>Worth another look</b><ul class="clean">${MD.missed.map(c => `<li>${c.s}${c.rule ? ` <span class="small muted">(rule ${c.rule})</span>` : ""}</li>`).join("")}</ul></div>` : "<p>Clean round.</p>"}
      <div class="row"><button class="btn primary">New round</button></div></section>`);
    $("button", res).onclick = () => mdlRound(MD.cat);
    box.append(res); return;
  }
  const c = MD.cards[MD.i];
  const card = el(`<section class="card list"><div class="row" style="justify-content:space-between"><span class="eyebrow">Card ${MD.i + 1} of ${MD.cards.length}</span><span class="small muted">${MD.ok} right</span></div><p class="stem">${c.s}</p><div class="qs list"></div><div class="fb" aria-live="polite"></div><div class="row acts"></div></section>`);
  box.append(card);
  const qs = $(".qs", card), acts = $(".acts", card);
  c.qs.forEach((q, qi) => {
    const nm = uid("mq"), order = shuffle(q.o.map((_, j) => j));
    const w = el(`<div><p style="font-weight:700;margin-bottom:6px">${q.q}</p><div class="opts">${order.map(j => `<label class="opt"><input type="${q.m ? "checkbox" : "radio"}" name="${nm}" value="${j}"><span>${q.o[j]}</span></label>`).join("")}</div></div>`);
    w.dataset.qi = qi; qs.append(w);
  });
  const chk = el(`<button class="btn primary">Check</button>`); acts.append(chk);
  chk.onclick = () => {
    let all = true, answered = true;
    $$("[data-qi]", qs).forEach(w => {
      const q = c.qs[+w.dataset.qi];
      const picked = $$("input", w).filter(x => x.checked).map(x => +x.value);
      if (!picked.length) answered = false;
      const want = q.m ? q.a.slice() : [q.a];
      const ok = picked.length === want.length && want.every(v => picked.includes(v));
      if (!ok) all = false;
      $$(".opt", w).forEach(lab => { const j = +$("input", lab).value; if (want.includes(j)) lab.classList.add("right"); else if (picked.includes(j)) lab.classList.add("wrong"); });
    });
    if (!answered){ $$(".opt", qs).forEach(l => l.classList.remove("right", "wrong")); return setFb(card, "info", "Answer every question first."); }
    $$("input", qs).forEach(x => x.disabled = true);
    MD.i++; if (all) MD.ok++; else MD.missed.push(c);
    S.mdl.n++; if (all) S.mdl.ok++; save(); mdlStats();
    track({m:"mdl", t:c.id, ti:"Which table: " + plain(c.s).slice(0, 40), n:"card", ok:all ? 1 : 0, d:""});
    setFb(card, all ? "ok" : "bad", `<div><b class="tag">${all ? "Right." : "Not quite."}</b>${c.rule ? ` <span class="small muted">Rule ${c.rule}</span>` : ""}</div>${c.w}`);
    acts.innerHTML = ""; const n = el(`<button class="btn primary">${MD.i >= MD.cards.length ? "See results" : "Next card"}</button>`); n.onclick = mdlCard; acts.append(n); n.focus({preventScroll:true});
  };
}

""" + html[j:]

open(DST, "w", encoding="utf-8").write(html)
print("ok", len(html))
