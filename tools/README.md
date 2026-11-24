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
- Remade from past exams (added the same day, after Matthew sent his old Exam 2s and Finals): P1 lake-source heat pump with an R-134a evaporator (US units; the F24 original had the refrigerant warmer than the lake), P2 most power a river can carry away (US units; exact entropy-balance limit vs the quick Carnot estimate), P3 turbine with velocities where q_out comes from the first law, P4 vortex-tube claim (US units; about a quarter impossible), P5 two compartments of air mixing (A-17), P6 polytropic compression with heat loss, P7 two-stage compression with intercooling, P8 paddle wheel in a rigid steam tank, P9 coldest outdoor temperature for a heat pump in an Everett house. Tagged `grp: "past"`, with `note` and `us`. US-unit water and R-134a values come straight from CoolProp in English units (same reference states as A-4E and A-11E).
- None of the Nov 9 Exam 2 bank problems (Drive, 12 Exam 2 Fall 2026) are on this public site, on purpose.
- `check_challenge.py` re-solves every version independently (CoolProp for water and R-134a, direct c_p integration for air, analytic otherwise). Nov 9 run: 2208 answers (25 templates), none past 0.63 of its tolerance.
- `patch_challenge.py ../index.html challenge_templates.json` patches the current page in place: a Challenge tab (with a "Remade from past exams" section), a home card, tier and US-units labels, the English tables in the table picker, and a third practice-exam option (Challenge: table fill-in + one problem per Exam 2 slot from the challenge set). It refuses to run twice.

## Exam 2 scope pass (Nov 11, 2026)
- Brayton came off Exam 2 (Matthew, Nov 9), and he wants only Exam 2 material on the public page for now. `patch_challenge.py` now drops E19 and E20 from BANK3 (guided list, Cycles track station, Exam 2 practice-exam cycle slot), and drops every challenge template tagged `hold: "final"` (C10 jet core, C11 real-device gas turbine, C12 regenerative peaker) before writing BANK4, so they are not in the page at all. Exam dates/covers and the formula checklist now say Otto, Diesel and dual. Which-table card M43 now uses an air compressor instead of a Brayton cycle.
- New C17 "Otto engine read from its pressure sensor" (cold-air Otto worked backward from a measured peak pressure, then MEP and four-stroke power; Beyond the numbers on small-engine exhaust and landscaping workers, CARB 2021). The challenge practice exam's cycle slot is now C13, C14, C17.
- The final-exam challenge set (Rankine and the held Brayton problems) lives in the private Thermo repo until Matthew says to publish it.

## Cycle animations (Nov 23, 2026)
- `cycles.html`: Thermo Cycle Quest, an NES-style page with every course cycle animated (Otto, Diesel, Dual, Stirling, Ericsson, Brayton with an optional ideal regenerator, turbojet, a 'Carnot vapor?' level showing why nobody builds it, and Rankine ideal and with an 85% turbine). Each device moves in step with its state point on P-v and T-s, with a COMPARE screen. One self-contained file (fonts and data embedded). Source and data generator: private Thermo repo, `02 Lecture Decks and Activities/Interactive - Thermo Cycle Quest (Nov 24)` and `09 Build Source/Week 10 live lecture (Nov 24)`.
- `otto-diesel.html`: the Nov 17 Otto and Diesel page (engine cross-section, P-v, ideal vs. real models, 2- and 4-stroke), with a back link added.
- `index.html` gets one new nav link, 'Cycle animations', to `cycles.html`. Matthew asked for these to be public (Nov 23), after Exam 2. (The final-exam problems were published later the same day; see below.)
## The final exam (Nov 23, 2026)
Matthew asked for final-exam problems on the site, guided by the homework and past exams. The held-back final set is now public, plus a new exam-level set.
- `gen_final2.py` builds 8 exam-level templates (24 versions each), modeled on the Weeks 9-11 WAMAP sets and the old finals: X1 Diesel with A-17 (v_r), X2 regenerative gas turbine (US, A-2Ea), X3 turbojet thrust and propulsive efficiency, X4 ideal Rankine (Beyond the numbers: USGS thermoelectric water withdrawals), X5 ideal reheat Rankine (US, A-5E/A-6E from CoolProp in English units, rounded as printed; the HP exit is always wet so only A-5E is needed there), X6 regenerative Rankine with a closed feedwater heater (drain trapped to the condenser), X7 cogeneration with an extraction turbine (Beyond the numbers: Co-op City CHP during Sandy, DOE/HUD/EPA guide), X8 Carnot cycle with steam. Writes `final2_templates.json`.
- `check_final2.py` re-solves every version (CoolProp, direct c_p integration for X1). Nov 23: 768 answers, worst 0.21 of tolerance.
- `gen_final.py` / `check_final.py`: the challenge-tier final set (F1-F9) that was held in the private Thermo repo since Nov 11; unchanged (864 answers, worst 0.19).
- `patch_final.py ../index.html final2_templates.json final_templates.json` runs after `patch_challenge.py`: BANK5 (X1-X8, E19, E20, F1-F9, C10-C12), a "Final exam" tab, Ch. 10 name, A-5E/A-6E in the table picker, a final-exam home card and bunny track (exam-level problems only), the final's countdown text, a Final practice exam (cumulative since Nov 24: six problems, 110 minutes, 100 points: gas cycle 18, Rankine 18, improved Rankine or cogeneration 20, jet/Carnot/Stirling/Ericsson 14, Ch. 4 closed system 15, Ch. 5-7 review 15) with its own formula-sheet checklist and paper version, and a phone-width fix for the home page grid. It refuses to run twice.
- QA: headless Chrome walked all 22 final templates through Worked, a full first-try Guided walk, and Solo with every listed wrong answer rejected; the Final practice exam timed, scored and printed; no console errors.
