# Generators for the Exam 2 content

These scripts built the Exam 2 additions to `index.html` (Oct 2026). They are not loaded by the site.

- `tables.py` emulates Çengel & Boles Tables A-4 to A-7 (water, IAPWS-95) and A-11 to A-13 (R-134a, ASHRAE reference: h = s = 0 for saturated liquid at −40 °C), rounded as printed.
- `gen_states.py` builds the property-drill states (`states2.json`), with step-by-step explanations and wrong-answer diagnoses.
- `check_states.py states2.json states2_final.json` recomputes every answer straight from the equation of state and drops any item whose table-interpolated answer strays past 70% of its tolerance.
- `gen_curves.py` builds the isobars and the R-134a dome for the T-v plots.
- `model_cards.py` holds the "Which table?" cards and the decision rules (`model.json`).
- `patch_site.py` injects everything into the page.

Requires `pip install CoolProp numpy scipy`. Paths in `patch_site.py` point at the build folder and need editing before a rerun.
