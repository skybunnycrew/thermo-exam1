"""Sixth patch (Nov 24, 2026): the Setup tab. Quick setup-only drills from setup_bank.json (gen_setup.py), whole course.
Runs on the current index.html in place, after patch_final.py.
Usage: python3 patch_setup.py ../index.html setup_bank.json"""
import json, sys
DST, BANKF = sys.argv[1:3]
html = open(DST, encoding="utf-8").read()
assert "const SETUP" not in html, "already patched"
def rep(old, new, count=1):
    global html
    n = html.count(old); assert n == count, (n, old[:140]); html = html.replace(old, new)

cards = json.load(open(BANKF, encoding="utf-8"))
data = json.dumps(cards, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
k = html.index("<script>const BANK5 = "); k = html.index("</script>", k) + len("</script>")
html = html[:k] + "\n<script>const SETUP = " + data + ";</script>" + html[k:]

rep(".tf{display:grid;grid-template-columns:1fr 1fr;gap:10px}",
    ".tf{display:grid;grid-template-columns:1fr 1fr;gap:10px}\n"
    ".suq{display:grid;gap:6px}.suq .why{font-size:.92rem;color:var(--muted);border-left:3px solid var(--line);padding-left:10px}"
    "@media (min-width:700px){nav.tabs a{padding:10px 8px 8px}nav.tabs .wrap{gap:2px}}"
    ".suq .why.ok{border-left-color:var(--ok)}.suq .why.bad{border-left-color:var(--bad)}.trap{border:1px dashed var(--accent);border-radius:10px;padding:8px 12px}")
rep('    <a href="#triage" data-tab="triage">Triage</a>\n', '    <a href="#setup" data-tab="setup">Setup</a>\n    <a href="#triage" data-tab="triage">Triage</a>\n')
rep("triage:viewTriage, exam:viewExam};", "triage:viewTriage, setup:viewSetup, exam:viewExam};")
rep("tri:{n:0, ok:0}, mdl:{n:0, ok:0}, exams:[], exam:null, optout:false}, store.get());",
    "tri:{n:0, ok:0}, mdl:{n:0, ok:0}, su:{n:0, ok:0, last:{}}, exams:[], exam:null, optout:false}, store.get());")
rep("tri:{n:0, ok:0}, mdl:{n:0, ok:0}, exams:[], exam:null, optout:keep};", "tri:{n:0, ok:0}, mdl:{n:0, ok:0}, su:{n:0, ok:0, last:{}}, exams:[], exam:null, optout:keep};")
rep('      <div class="stat"><span class="small muted">Triage</span>',
    '      <div class="stat"><span class="small muted">Setup drills</span><b>${S.su.n ? Math.round(100 * S.su.ok / S.su.n) + "%" : "–"}</b><span class="small muted">${S.su.n} cards</span></div>\n      <div class="stat"><span class="small muted">Triage</span>')

# home card
rep("""  app.append(el(`<section class="card exam2 list"><div class="eyebrow">Exam 2 drills, still useful</div>""",
    """  app.append(el(`<section class="card exam2 list"><div class="eyebrow">New: setup drills</div>
      <p><b>Setup tab:</b> ${SETUP.length} quick problems from the whole course where you don't solve anything. Pick the system, the terms that stay in the balance, where the properties come from, and the working equation. ${SETUP.filter(c => c.tr).length} are marked <b>tricky</b>: each hides a trap that shows up on exams.</p>
      <div class="row"><button class="btn primary" data-go="setup">Setup drills</button></div></section>`));
  app.append(el(`<section class="card exam2 list"><div class="eyebrow">Exam 2 drills, still useful</div>""")

rep("/* ---------- practice exam ---------- */", r"""/* ---------- setup drills (Nov 24) ---------- */
let SU = null;
const SUGRP = [["All", []], ["Ch. 1–4", [1, 2, 3, 4]], ["Ch. 5", [5]], ["Ch. 6–7", [6, 7]], ["Ch. 9", [9]], ["Ch. 10", [10]]];
function viewSetup(app){
  app.append(el(`<section><h2>Setup drills</h2><p class="muted" style="margin-top:4px">Set the problem up, don't solve it: no arithmetic. For each card, pick the system, the terms that stay in the balance, where the properties come from, and the working equation. This is the part that decides most exam points. Eight cards a round, about two minutes each. Cards marked <span class="pill hardest">Tricky</span> hide one trap that catches students on exams.</p></section>`));
  const f = el(`<div class="filters" role="group" aria-label="Chapters">${SUGRP.map(([n], i) => `<button data-g="${i}" aria-pressed="${i === 0}">${n}</button>`).join("")}<button data-t="1" aria-pressed="false">Tricky only</button></div>`);
  let g = 0, tr = false;
  $$("[data-g]", f).forEach(b => b.onclick = () => { g = +b.dataset.g; $$("[data-g]", f).forEach(x => x.setAttribute("aria-pressed", x === b)); newSetup(g, tr); });
  const tb = $("[data-t]", f); tb.onclick = () => { tr = !tr; tb.setAttribute("aria-pressed", tr); newSetup(g, tr); };
  app.append(f);
  app.append(el(`<section id="subox" class="list"></section>`));
  newSetup(0, false);
}
function newSetup(g, tr){
  const chs = SUGRP[g][1];
  let pool = SETUP.filter(c => (!chs.length || chs.includes(c.ch)) && (!tr || c.tr));
  // cards missed last time come back first, then ones not seen yet, then the rest
  const rank = c => S.su.last[c.id] === 0 ? 0 : S.su.last[c.id] === undefined ? 1 : 2;
  pool = shuffle(pool.slice()).sort((a, b) => rank(a) - rank(b)).slice(0, 8);
  SU = {cards:shuffle(pool), i:0, ok:0, qok:0, qn:0, missed:[], g, tr};
  showSetup();
}
function showSetup(){
  const box = $("#subox"); if (!box) return; box.innerHTML = "";
  if (!SU.cards.length){ box.append(el(`<section class="card"><p>No cards match that filter.</p></section>`)); return; }
  if (SU.i >= SU.cards.length){
    const res = el(`<section class="card list"><div class="eyebrow">Round done</div><div class="score num">${SU.ok} / ${SU.cards.length} cards</div><p class="small muted">${SU.qok} of ${SU.qn} questions right.</p>
      ${SU.missed.length ? `<div><b>Worth another look</b> (they come back first next round)<ul class="clean">${SU.missed.map(m => `<li>${m.s}${m.trap ? `<br><span class="small muted"><b>The trap:</b> ${m.trap}</span>` : ""}</li>`).join("")}</ul></div>` : "<p>Clean round.</p>"}
      <div class="row"><button class="btn primary">New round</button></div></section>`);
    $("button", res).onclick = () => newSetup(SU.g, SU.tr);
    box.append(res); return;
  }
  const c = SU.cards[SU.i];
  const card = el(`<section class="card list"><div class="row" style="justify-content:space-between"><span class="eyebrow">Card ${SU.i + 1} of ${SU.cards.length} · Ch. ${c.ch}${c.tr ? ` · <span class="pill hardest">Tricky</span>` : ""}</span><span class="small muted">${SU.ok} right</span></div>
    <p class="stem">${c.s}</p><div class="qs list"></div><div class="fb" aria-live="polite"></div><div class="row acts"></div></section>`);
  box.append(card);
  const qs = $(".qs", card), acts = $(".acts", card);
  // single-answer options are shuffled each time; term lists keep their order
  const views = c.qs.map(q => { const ord = q.m ? q.o.map((_, j) => j) : shuffle(q.o.map((_, j) => j)); return {q, ord}; });
  views.forEach(({q, ord}, qi) => {
    const nm = uid("su");
    const w = el(`<div class="suq"><p class="p" style="font-weight:700;margin:0">${q.q}${q.m ? ` <span class="small muted" style="font-weight:400">(pick all that apply)</span>` : ""}</p>
      <div class="opts">${ord.map(j => `<label class="opt"><input type="${q.m ? "checkbox" : "radio"}" name="${nm}" value="${j}"><span>${q.o[j]}</span></label>`).join("")}</div><div class="why" hidden></div></div>`);
    w.dataset.qi = qi; qs.append(w);
  });
  const chk = el(`<button class="btn primary">Check</button>`); acts.append(chk);
  chk.onclick = () => {
    const ws = $$("[data-qi]", qs);
    if (ws.some(w => !$$("input", w).some(x => x.checked))) return setFb(card, "info", "Answer every question first.");
    let nright = 0;
    ws.forEach(w => {
      const q = c.qs[+w.dataset.qi];
      const picked = $$("input", w).filter(x => x.checked).map(x => +x.value);
      const want = q.m ? q.a.slice() : [q.a];
      const ok = picked.length === want.length && want.every(v => picked.includes(v));
      if (ok) nright++;
      $$(".opt", w).forEach(lab => { const j = +$("input", lab).value; if (want.includes(j)) lab.classList.add("right"); else if (picked.includes(j)) lab.classList.add("wrong"); });
      const why = $(".why", w); why.hidden = false; why.classList.add(ok ? "ok" : "bad"); why.innerHTML = `<b>${ok ? "Right." : "Not quite."}</b> ${q.w}`;
    });
    $$("input", qs).forEach(x => x.disabled = true);
    const all = nright === c.qs.length;
    SU.i++; SU.qn += c.qs.length; SU.qok += nright; if (all) SU.ok++; else SU.missed.push({s:c.s, trap:c.trap});
    S.su.n++; if (all) S.su.ok++; S.su.last[c.id] = all ? 1 : 0; save();
    track({m:"su", t:c.id, ti:"Setup: " + c.s.replace(/<[^>]+>/g, "").slice(0, 40), n:"card", ok:all ? 1 : 0, d:""});
    setFb(card, all ? "ok" : "bad", `<div><b class="tag">${all ? "All right." : nright + " of " + c.qs.length + " right."}</b>${c.trap ? `</div><div class="trap" style="margin-top:8px"><b>The trap:</b> ${c.trap}` : ""}</div>`);
    acts.innerHTML = ""; const n = el(`<button class="btn primary">${SU.i >= SU.cards.length ? "See results" : "Next card"}</button>`); n.onclick = showSetup; acts.append(n); n.focus({preventScroll:true});
  };
}

/* ---------- practice exam ---------- */""")
open(DST, "w", encoding="utf-8").write(html)
print("ok", len(cards), "cards")
