"""Third patch: the home-page progress track becomes a bunny eating a lettuce at each marker; eaten lettuces disappear (runs after patch_exam2.py)."""
import sys
SRC, DST = sys.argv[1], sys.argv[2]
html = open(SRC, encoding="utf-8").read()

def rep(old, new, count=1):
    global html
    n = html.count(old)
    assert n == count, (n, old[:120])
    html = html.replace(old, new)

# color tokens (light, then the two dark blocks)
rep("--track:#cfc6c5;", "--track:#cfc6c5; --leaf:#2f8a4c; --leaf2:#86c56f;")
rep("--track:#4a4242;", "--track:#4a4242; --leaf:#3e9c5c; --leaf2:#9bd88a;", 2)

# styles
i = html.index(".track .rail{stroke:var(--track)}"); j = html.index(".track .puff{fill:var(--surface-2)}") + len(".track .puff{fill:var(--surface-2)}")
html = html[:i] + """.track .ground{stroke:var(--track);stroke-width:3;stroke-linecap:round}
.track .hops{stroke:var(--track);stroke-width:2;fill:none;stroke-dasharray:3 5;stroke-linecap:round}
.track .lettuce .l1{fill:var(--leaf);stroke:var(--bg);stroke-width:1.2}
.track .lettuce .l2{fill:var(--leaf2);stroke:var(--bg);stroke-width:1.2}
.track .lettuce .vein{stroke:var(--leaf);stroke-width:1.2;fill:none;stroke-linecap:round}
.track .crumb{fill:var(--leaf2)}
.track text.eaten{fill:var(--ok);font-weight:700}
.track text{fill:var(--muted);font-size:12px;font-family:var(--font)}
.track .bunny .fur{fill:#fffdf9;stroke:#2b2324;stroke-width:2;stroke-linejoin:round}
.track .bunny .ear-in{fill:#f6c9c4}
.track .bunny .ink{fill:#2b2324}
.track .bunny .nose{fill:#d9534f}
.track .bunny .scarf{fill:#c00000;stroke:#2b2324;stroke-width:1}
.track .bunny .cap{fill:#35507a;stroke:#2b2324;stroke-width:1.4;stroke-linejoin:round} .track .bunny .stripe{stroke:#fffdf9;stroke-width:1.6;stroke-linecap:round}
.track .bunny .head{transform-box:fill-box;transform-origin:30% 70%;animation:nibble 1.1s ease-in-out infinite}
.track .bunny.full .head{animation:none}
@keyframes nibble{0%,100%{transform:rotate(0)}25%{transform:rotate(6deg)}50%{transform:rotate(0)}75%{transform:rotate(5deg)}}
@media (prefers-reduced-motion: reduce){.track .bunny .head{animation:none}}
.trackwrap{overflow-x:auto;scrollbar-width:thin}
@media (max-width:640px){svg.track{min-width:560px}}""" + html[j:]

# drawing
i = html.index("function trackSVG(){"); j = html.index("function viewHome(app){")
html = html[:i] + r"""function lettuceSVG(x, y){
  return `<g class="lettuce"><circle class="l1" cx="${x - 7}" cy="${y + 4}" r="7"/><circle class="l1" cx="${x + 7}" cy="${y + 4}" r="7"/>
    <circle class="l1" cx="${x}" cy="${y - 2}" r="8.5"/><circle class="l2" cx="${x - 2}" cy="${y + 3}" r="6"/><circle class="l2" cx="${x + 4}" cy="${y + 1}" r="5"/>
    <path class="vein" d="M${x - 2},${y + 8} Q${x - 1},${y + 2} ${x + 2},${y - 3} M${x + 5},${y + 6} Q${x + 5},${y + 2} ${x + 7},${y - 1}"/></g>`;
}
function bunnySVG(full){
  // Original drawing: the course bunny in an engineer's cap and red neckerchief, nose at x = 53, feet at y = 46.
  return `<g class="bunny${full ? " full" : ""}">
    <circle class="fur" cx="6" cy="27" r="5"/>
    <ellipse class="fur" cx="23" cy="31" rx="17" ry="13"/>
    <ellipse class="fur" cx="17" cy="42" rx="11" ry="4.5"/>
    <g class="head">
      <g transform="rotate(-12 38 6)"><ellipse class="fur" cx="38" cy="-3" rx="4" ry="11"/><ellipse class="ear-in" cx="38" cy="-2" rx="1.8" ry="7.5"/></g>
      <g transform="rotate(14 46 7)"><ellipse class="fur" cx="46" cy="-2" rx="4" ry="11"/><ellipse class="ear-in" cx="46" cy="-1" rx="1.8" ry="7.5"/></g>
      <circle class="fur" cx="42" cy="17" r="10.5"/>
      <path class="cap" d="M31,12 Q31,2 42,2 Q52,2 52,10 L58,12 Q46,13 31,12 Z"/><path class="stripe" d="M36,4.5 L35.5,11 M41,3 L41,11.5 M46,3.5 L46.5,11.5"/>
      <circle class="ink" cx="46" cy="16" r="1.8"/>
      <circle class="nose" cx="52.3" cy="19.5" r="1.6"/>
    </g>
    <path class="scarf" d="M33,25 Q41,30 49,24 L44,34 Z"/>
    <ellipse class="fur" cx="39" cy="43" rx="5" ry="3.5"/>
  </g>`;
}
function trackSVG(){
  const W = 640, H = 136, x0 = 30, x1 = W - 40, y = 86;
  const xs = STATIONS.map((st, i) => x0 + (x1 - x0) * (i + 1) / STATIONS.length);
  const eaten = STATIONS.map(stationLit), n = eaten.filter(Boolean).length;
  const next = eaten.indexOf(false);                       // the bunny sits at the first lettuce not yet eaten
  const bx = next < 0 ? x1 - 50 : xs[next] - 15 - 53;
  let s = `<svg class="track" data-bx="${(bx / W).toFixed(3)}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Progress: the bunny has eaten ${n} of ${STATIONS.length} lettuces${next < 0 ? ", every topic is solid" : ", and is working on " + esc(STATIONS[next].name)}">`;
  s += `<path class="ground" d="M${x0 - 20},${y + 12} H${x1 + 20}"/>`;
  let hops = "";
  for (let x = x0 - 20; x + 30 <= bx + 10; x += 30) hops += `M${x},${y + 8} Q${x + 15},${y - 14} ${x + 30},${y + 8} `;
  if (hops) s += `<path class="hops" d="${hops}"/>`;
  STATIONS.forEach((st, i) => {
    const x = xs[i];
    s += eaten[i] ? `<circle class="crumb" cx="${x - 4}" cy="${y + 10}" r="1.6"/><circle class="crumb" cx="${x + 3}" cy="${y + 11}" r="1.3"/>` : lettuceSVG(x, y);
    s += `<text class="${eaten[i] ? "eaten" : ""}" x="${i === STATIONS.length - 1 ? x + 10 : x}" y="${y + (i % 2 ? 44 : 29)}" text-anchor="${i === STATIONS.length - 1 ? "end" : "middle"}">${eaten[i] ? "✓ " : ""}${esc(st.name)}</text>`;
  });
  s += `<g transform="translate(${bx.toFixed(1)},${y + 10 - 46})">${bunnySVG(next < 0)}</g>`;
  return s + "</svg>";
}
""" + html[j:]

rep("<section class=\"panel\">${trackSVG()}<p", "<section class=\"panel\"><div class=\"trackwrap\">${trackSVG()}</div><p")
rep("  $$(\"[data-go]\", app).forEach(b => b.onclick = () => go(b.dataset.go));", "  $$(\"[data-go]\", app).forEach(b => b.onclick = () => go(b.dataset.go));\n  requestAnimationFrame(() => { const w = $(\".trackwrap\", app), t = w && $(\"svg.track\", w); if (t && w.scrollWidth > w.clientWidth) w.scrollLeft = Math.max(0, +t.dataset.bx * w.scrollWidth - w.clientWidth / 3); });")
rep("The engine moves as skills turn solid. A station lights up when two of its problems are solid;",
    "The bunny eats a lettuce once two of that topic's problems are solid, then hops on to the next one;")

open(DST, "w", encoding="utf-8").write(html)
print("ok", len(html))
