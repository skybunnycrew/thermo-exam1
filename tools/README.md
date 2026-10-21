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
