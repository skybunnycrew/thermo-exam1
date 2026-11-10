# Generators for the Exam 2 content

These scripts built the Exam 2 additions to `index.html` (Oct 2026). They are not loaded by the site.

- `tables.py` emulates Çengel & Boles Tables A-4 to A-7 (water, IAPWS-95) and A-11 to A-13 (R-134a, ASHRAE reference: h = s = 0 for saturated liquid at −40 °C), rounded as printed.
- `gen_states.py` builds the property-drill states (`states2.json`), with step-by-step explanations and wrong-answer diagnoses.
- `check_states.py states2.json states2_final.json` recomputes every answer straight from the equation of state and drops any item whose table-interpolated answer strays past 70% of its tolerance.
- `gen_curves.py` builds the isobars and the R-134a dome for the T-v plots.
- `model_cards.py` holds the "Which table?" cards and the decision rules (`model.json`).
- `patch_site.py` injects everything into the page.

Requires `pip install CoolProp numpy scipy`. Paths in `patch_site.py` point at the build folder and need editing before a rerun.

## Exam 2 guided problems and practice exam (Oct 21, 2026)

- `a17.py` emulates Table A-17 (air) by integrating air's ideal-gas c_p, anchored to the 300 K row; plus the A-2a constants used.
- `exam2_common.py` holds the shared eight-step pieces: assumption library, first-law term lists in the course's in/out form, and `part()`, which tightens each answer's tolerance to half the distance to any listed wrong answer so a known slip is never marked right.
- `gen_exam2.py` builds the 20 Exam 2 templates (24 versions each): devices (E1–E5), heat exchangers and mixing (E6–E9), second law (E10–E12), isentropic efficiency and entropy generation (E13–E15), Otto/Diesel/dual/Brayton (E16–E20). Writes `exam2_templates.json`.
- `check_exam2.py` re-solves every version independently (CoolProp for water and R-134a, analytic ideal gases, direct c_p integration for air) and flags any answer more than 70% of its tolerance away.
- `patch_exam2.py` runs after `patch_site.py` and adds the templates, the T-s and P-v sketches, the Exam 1/Exam 2 switch on the practice exam, and the Exam 2 home track.

## Bunny progress track (Oct 21, 2026)

- `patch_bunny.py` runs after `patch_exam2.py`. It replaces the locomotive on the home page with the course bunny (engineer's cap, red neckerchief), which sits nibbling at the first lettuce whose topic isn't solid yet. A lettuce disappears (leaving a few crumbs and a green check on its label) once two of that topic's problems are solid. On phones the track keeps its size and scrolls sideways to the bunny.

## Challenge problems, harder than Exam 2 (Nov 9, 2026)

- `gen_challenge.py` builds 16 templates (24 versions each) in the same eight-step format, tagged `tier: "challenge"` or `"hardest"`: C1 turbine + bypass valve + mixer with total S_gen (shape of the old Final's Problem 3), C2 turbine with extraction and heat loss, C3 compressor + aftercooler with A-17 and total S_gen, C4 two metal blocks, C5 rigid steam tank cooling to the room, C6 R-134a heated at constant P by a reservoir, C7 engine-driven heat pump, C8 heat-driven vaccine cooler (three reservoirs; about 40% of versions are impossible claims), C9 hot-gas nozzle with η and A-17, C10 jet engine core with ram inlet (the old exam's gas generator), C11 gas turbine with real devices and A-17, C12 regenerative peaker plant on natural gas vs hydrogen (old Final's two-fuel Brayton), C13 Otto with v_r and u from A-17, C14 Diesel genset power from displacement and rpm, C15 desuperheater, C16 expansion valve + evaporator with S_gen in each. Four carry "Beyond the numbers" cards with sources (C8, C10, C12, C14). Writes `challenge_templates.json`.
- `check_challenge.py` re-solves every version independently (CoolProp for water and R-134a, direct c_p integration for air, analytic otherwise). Nov 9 run: 1464 answers, none past 0.38 of its tolerance.
- `patch_challenge.py ../index.html challenge_templates.json` patches the current page in place: a Challenge tab, a home card, tier labels, and a third practice-exam option (Challenge: table fill-in + one problem per Exam 2 slot from the challenge set). It refuses to run twice.
