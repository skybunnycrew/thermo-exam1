"""'Which table?' decision cards. Matthew's rules (Oct 21, 2026):
tables first; ideal gas only for gases, never water vapor or R-134a; constant c for noble gases;
air: constant c for small dT, A-17 for large dT; other gases (N2, O2, CO2, CO, H2): their ideal-gas tables."""
import json

ST = "Steam tables (A-4 to A-7)"
RT = "R-134a tables (A-11 to A-13)"
IGC = "Ideal gas, constant c<sub>p</sub>, c<sub>v</sub> (A-2a)"
A17 = "Air ideal-gas table (A-17)"
IGT = "That gas's own ideal-gas table (A-18 to A-22)"
ZC = "Compressibility chart: PV = ZmRT (A-15)"
CW = "c&#8239;ΔT with c = 4.18 kJ/kg·K (A-3)"
A23 = "The H<sub>2</sub>O ideal-gas table (A-23)"
PVR = "PV = mRT with R from A-1"
CV, CPP = "c<sub>v</sub> (Δu = c<sub>v</sub>ΔT)", "c<sub>p</sub> (Δh = c<sub>p</sub>ΔT)"
SRC = "Where do the property values come from?"
WHICHC = "Which specific heat goes in the energy balance?"

def W(*steps):
    return "<ol class=\"wsteps\">" + "".join(f"<li>{s}</li>" for s in steps) + "</ol>"

def q(text, opts, a, m=False):
    return {"q": text, "o": opts, "a": a, "m": m}

C = []
def card(cat, s, qs, w, rule):
    C.append({"id": f"M{len(C) + 1:02d}", "cat": cat, "s": s, "qs": qs, "w": w, "rule": rule})

# ------------------------------------------------------------------ water and R-134a: tables, always
card("fluid", "A kettle heats 1.5 kg of liquid water from 20 °C to 90 °C at 1 atm. You need the heat added.",
     [q(SRC, [ST, CW, IGC, PVR], 0)],
     W("Rule 1: it's water, so the steam tables are on your desk. Use them.",
       "The water is a compressed liquid at 1 atm, so h ≈ h<sub>f</sub>@T from Table A-4: h<sub>f</sub>@20 °C and h<sub>f</sub>@90 °C.",
       "Q<sub>in</sub> = m(h<sub>2</sub> − h<sub>1</sub>) ≈ 1.5(377.04 − 83.91) ≈ 440 kJ.",
       "cΔT lands close here, which is why it's tempting. The table habit is the one that still works when the water starts to boil."), 1)
card("fluid", "Superheated steam at 10 kPa and 200 °C leaves a turbine. A classmate says steam this dilute is nearly an ideal gas, so PV = mRT is fine.",
     [q(SRC, [ST, PVR, A23, ZC], 0)],
     W("Rule 1: water gets the steam tables in every phase, even dilute vapor.",
       "Table A-6, the 0.01 MPa block, 200 °C row, gives v, u, h and s directly.",
       "The classmate's number would be close at this pressure, but you'd still need u, h and s, and the table has them. A-23 is for combustion products later in the book, not for steam in a cycle."), 1)
card("fluid", "Steam at 1 MPa and 400 °C fills a 0.5 m³ tank. Find its mass.",
     [q(SRC, [ST, PVR, ZC], 0)],
     W("Rule 1: steam tables. Table A-6, the 1 MPa block, 400 °C row: v = 0.30661 m³/kg.",
       "m = V/v = 0.5/0.30661 = 1.63 kg.",
       "PV = mRT would give v = 0.3107 m³/kg, about 1.3% high. Small here, much larger near the dome, and you never have to wonder if you use the table."), 1)
card("fluid", "R-134a vapor at 1 MPa and 60 °C fills a 20 L cylinder. Find the mass.",
     [q(SRC, [RT, PVR, ZC, IGC], 0)],
     W("Rule 1: R-134a has its own tables. Use Table A-13, the 1 MPa block, 60 °C row.",
       "Never treat R-134a vapor as an ideal gas: refrigerants are used close to their dome on purpose.",
       "Here PV = mRT would overpredict v by about 18% (Z ≈ 0.85). The Z chart would be a workaround for a gas with no table; R-134a has one."), 1)
card("fluid", "A rigid tank holds wet steam (x = 0.3) at 200 kPa. It's heated until it's saturated vapor. Find the heat added.",
     [q(SRC, [ST, PVR, CW, IGC], 0)],
     W("Rule 1: it's water, so steam tables, in every phase.",
       "State 1: Table A-5 at 200 kPa, u<sub>1</sub> = u<sub>f</sub> + x u<sub>fg</sub>, and v<sub>1</sub> the same way.",
       "Rigid tank: v<sub>2</sub> = v<sub>1</sub>, and x<sub>2</sub> = 1, so find where v<sub>g</sub> = v<sub>1</sub> in Table A-5 or A-4.",
       "No gas or cΔT shortcut can handle a phase change."), 1)
card("fluid", "In a car A/C evaporator, R-134a at −10 °C goes from quality 0.25 to saturated vapor. Find the heat absorbed per kg.",
     [q(SRC, [RT, "c<sub>p</sub>ΔT with c<sub>p</sub> from A-3", IGC], 0)],
     W("Rule 1: R-134a tables, Table A-11 at −10 °C.",
       "q<sub>in</sub> = h<sub>g</sub> − (h<sub>f</sub> + 0.25 h<sub>fg</sub>) = 0.75 h<sub>fg</sub>.",
       "T doesn't change at all, so any cΔT gives zero. The heat goes into evaporating the liquid, and only the table sees that."), 1)
card("fluid", "Steam at 10 kPa and x = 0.90 condenses to saturated liquid in a power-plant condenser. Find the heat removed per kg.",
     [q(SRC, [ST, CW, IGC], 0)],
     W("Rule 1: steam tables, Table A-5 at 10 kPa.",
       "q<sub>out</sub> = h<sub>1</sub> − h<sub>2</sub> = (h<sub>f</sub> + 0.9 h<sub>fg</sub>) − h<sub>f</sub> = 0.9 h<sub>fg</sub>.",
       "Condensing happens at constant T, so cΔT = 0 and misses all of it."), 1)
card("fluid", "A pump delivers liquid water at 10 MPa and 40 °C. You need h at the pump exit.",
     [q(SRC, [ST + ", A-7 at 10 MPa, 40 °C", ST + ", h<sub>f</sub>@10 MPa (A-5)", CW, PVR], 0)],
     W("Rule 1: steam tables. The water is compressed liquid (40 °C is far below T<sub>sat</sub>@10 MPa = 311 °C).",
       "Use the best table you have: Table A-7 has a 10 MPa block with a 40 °C row.",
       "h<sub>f</sub>@10 MPa is saturated liquid at 311 °C, a completely different state. If the pressure were under 5 MPa, h ≈ h<sub>f</sub>@40 °C (Table A-4) would be the move."), 1)
card("fluid", "R-134a enters a compressor at 0.14 MPa and −10 °C. Find h<sub>1</sub>.",
     [q(SRC, [RT, IGC, PVR], 0)],
     W("Rule 1: R-134a tables.",
       "T<sub>sat</sub>@0.14 MPa = −18.8 °C, so −10 °C is superheated: Table A-13, the 0.14 MPa block, −10 °C row.",
       "It is a vapor, but rule 1 still wins: no ideal-gas model for R-134a."), 1)
card("fluid", "Steam at 15 MPa and 600 °C enters a turbine. Should you check the compressibility chart?",
     [q(SRC, [ST, ZC, PVR], 0)],
     W("Rule 1: the steam tables already include every real-gas effect. Table A-6, 15 MPa block, 600 °C row.",
       "The Z chart is for gases with no table of their own. Here Z ≈ 0.93, so PV = mRT would be about 8% off, and the table makes the question moot."), 1)
card("fluid", "A refrigerator line carries saturated liquid R-134a at 30 °C. Find its density.",
     [q(SRC, [RT, "ρ = 1000 kg/m³", PVR], 0)],
     W("Rule 1: Table A-11 at 30 °C: v<sub>f</sub>.",
       "ρ = 1/v<sub>f</sub> ≈ 1190 kg/m³. R-134a liquid is denser than water, so 1000 kg/m³ is about 16% off."), 1)
card("fluid", "Steam at 300 kPa and 200 °C. Table A-23 lists ideal-gas properties of H<sub>2</sub>O. Can you use it here?",
     [q(SRC, [ST, A23, PVR], 0)],
     W("Rule 1: no. Steam in this course comes from the steam tables: Table A-6, 0.3 MPa block, 200 °C row.",
       "A-23 uses a different reference state (it's built for combustion, Ch. 15). Mixing its h values with steam-table h values gives nonsense differences."), 1)

# ------------------------------------------------------------------ which model for a gas
card("gas", "Helium in a party balloon warms from 20 °C to 60 °C.",
     [q(SRC, [IGC, A17, IGT, ZC], 0)],
     W("Rule 3: helium is a noble (monatomic) gas, so its c<sub>p</sub> and c<sub>v</sub> are constant at every temperature.",
       "Use c<sub>p</sub> = 5.1926 and c<sub>v</sub> = 3.1156 kJ/kg·K from Table A-2a.",
       "A-17 is for air only."), 3)
card("gas", "Argon in a rigid tank is heated from 300 K to 1500 K.",
     [q(SRC, [IGC, A17, IGT, ZC], 0)],
     W("Rule 3: argon is a noble gas. Its c<sub>v</sub> stays constant even across a 1200 K change.",
       "So the big ΔT doesn't push you to a table: Δu = c<sub>v</sub>ΔT with c<sub>v</sub> = 0.3122 kJ/kg·K (A-2a) is exact for an ideal monatomic gas.",
       "Contrast with air, where a ΔT this large needs A-17."), 3)
card("gas", "Air in a bike tire warms from 20 °C to 45 °C in the sun.",
     [q(SRC, [IGC, A17, ZC, IGT], 0)],
     W("Rule 4: air with a small ΔT near room temperature: constant specific heats from A-2a (c<sub>v</sub> = 0.718 kJ/kg·K).",
       "Over 25 °C, c<sub>v</sub> barely changes, so A-17 would give the same answer with more work."), 4)
card("gas", "Air is compressed in a gas-turbine compressor from 300 K to 650 K.",
     [q(SRC, [A17, IGC, IGT, ZC], 0)],
     W("Rule 4: air with a large ΔT: use Table A-17.",
       "c<sub>p</sub> of air rises from about 1.005 at 300 K to about 1.06 kJ/kg·K at 650 K, so a single constant c<sub>p</sub> drifts.",
       "w<sub>in</sub> = h<sub>2</sub> − h<sub>1</sub> with both h values read from A-17."), 4)
card("gas", "Air in a diesel engine cylinder is heated from 900 K to 2000 K during combustion (air-standard model).",
     [q(SRC, [A17, IGC, IGT], 0)],
     W("Rule 4: large ΔT, so A-17.",
       "Between 900 K and 2000 K, air's c<sub>p</sub> climbs about 10%. Use h or u from A-17 at each temperature.",
       "If the problem said \"cold-air-standard\" or \"constant specific heats,\" you'd switch to A-2a."), 4)
card("gas", "Nitrogen in a heat-treating furnace is heated from 300 K to 900 K.",
     [q(SRC, [IGT, A17, IGC, ZC], 0)],
     W("Rule 5: nitrogen has its own ideal-gas table, A-18.",
       "A-18 lists molar values (kJ/kmol). Find ū<sub>2</sub> − ū<sub>1</sub>, then divide by M = 28.013 kg/kmol for kJ/kg.",
       "A-17 is air, not nitrogen: close in molar mass, but not the same gas."), 5)
card("gas", "Carbon dioxide cools from 800 K to 500 K in a nozzle.",
     [q(SRC, [IGT, IGC, A17], 0)],
     W("Rule 5: CO<sub>2</sub> has its own ideal-gas table, A-20.",
       "Read h̄ at 800 K and 500 K, take the difference, and divide by M = 44.01 kg/kmol.",
       "CO<sub>2</sub>'s c<sub>p</sub> rises about 15% over this range, so one constant value would miss."), 5)
card("gas", "A low-pressure oxygen tank (200 kPa) is heated from 25 °C to 225 °C.",
     [q(SRC, [IGT, A17, IGC], 0)],
     W("Rule 5: O<sub>2</sub> uses its ideal-gas table, A-19.",
       "Convert to kelvins first (298 K and 498 K), read ū, divide by M = 31.999."), 5)
card("gas", "Hydrogen flows through a heat exchanger and warms from 300 K to 700 K.",
     [q(SRC, [IGT, IGC, A17], 0)],
     W("Rule 5: H<sub>2</sub> uses its ideal-gas table, A-22.",
       "Steady flow, so you want Δh: h̄<sub>2</sub> − h̄<sub>1</sub> from A-22, divided by M = 2.016 kg/kmol."), 5)
card("gas", "A cryogenic tank holds nitrogen at 10 MPa and 150 K. Find the mass in 0.1 m³.",
     [q(SRC, [ZC, IGC, IGT], 0)],
     W("Rule 2: ideal gas only when the gas behaves like one. Check reduced properties first.",
       "T<sub>R</sub> = 150/126.2 = 1.19 and P<sub>R</sub> = 10/3.39 = 2.95: close to the critical point and well above its pressure.",
       "From A-15, Z ≈ 0.54. PV = mRT alone would put the mass off by nearly a factor of 2. Use m = PV/(ZRT)."), 2)
card("gas", "CO<sub>2</sub> is stored at 7 MPa and 320 K.",
     [q(SRC, [ZC, IGC, IGT], 0)],
     W("Rule 2: check the reduced properties: T<sub>R</sub> = 320/304.2 = 1.05, P<sub>R</sub> = 7/7.39 = 0.95.",
       "That's right next to the critical point. Z ≈ 0.65 (A-15), so PV = mRT would underpredict the mass by about 35%.",
       "Use PV = ZmRT. The CO<sub>2</sub> ideal-gas table (A-20) assumes ideal behavior too, so it can't fix this."), 2)
card("gas", "Air sits in a room at 200 kPa and 25 °C. Do you need the compressibility chart?",
     [q("Do you need Z?", ["No: T<sub>R</sub> ≈ 2.3, P<sub>R</sub> ≈ 0.05, so Z ≈ 1", "Yes: always check Z for air", "Yes: any pressure above 1 atm needs Z"], 0)],
     W("Rule 2: high T<sub>R</sub> and low P<sub>R</sub> mean ideal-gas behavior: Z ≈ 1.000.",
       "Use PV = mRT directly. The chart is for high pressure or temperatures near critical."), 2)
card("gas", "Neon in a sign tube is heated from 300 K to 900 K at constant volume.",
     [q(SRC, [IGC, A17, IGT], 0)],
     W("Rule 3: neon is a noble gas. Constant c<sub>v</sub> = 0.6179 kJ/kg·K (A-2a) at any temperature.",
       "Monatomic gases only store energy as motion, so c<sub>v</sub> = (3/2)R exactly."), 3)
card("gas", "Air in a sealed room is heated from 15 °C to 22 °C.",
     [q(SRC, [IGC, A17, ZC], 0), q(WHICHC, [CV, CPP], 0)],
     W("Rule 4: small ΔT for air: constant specific heats, A-2a.",
       "Rule 6: sealed and rigid means no boundary work, so the first law is Q<sub>in</sub> = ΔU = mc<sub>v</sub>ΔT."), 4)

# ------------------------------------------------------------------ c_v or c_p
card("cvcp", "A rigid tank of air is heated from 20 °C to 70 °C. Find Q.",
     [q(WHICHC, [CV, CPP], 0)],
     W("Rule 6: closed and rigid, so W<sub>b</sub> = 0.",
       "First law: Q<sub>in</sub> = ΔU = mc<sub>v</sub>(T<sub>2</sub> − T<sub>1</sub>), with c<sub>v</sub> = 0.718 kJ/kg·K (small ΔT, A-2a)."), 6)
card("cvcp", "Air in a piston-cylinder is heated at constant pressure from 25 °C to 75 °C. Find Q.",
     [q(WHICHC, [CPP, CV], 0)],
     W("Rule 6: closed system at constant P: Q<sub>in</sub> − W<sub>b,out</sub> = ΔU, and W<sub>b</sub> = PΔV.",
       "ΔU + PΔV = ΔH at constant P, so Q<sub>in</sub> = mc<sub>p</sub>ΔT.",
       "Using c<sub>v</sub> here gets ΔU right but leaves out the boundary work."), 6)
card("cvcp", "Helium accelerates through an adiabatic nozzle (steady flow). You need the exit velocity.",
     [q(WHICHC, [CPP, CV], 0)],
     W("Rule 6: steady flow, so the energy balance uses h: h<sub>1</sub> + V<sub>1</sub>²/2 = h<sub>2</sub> + V<sub>2</sub>²/2.",
       "Helium is a noble gas, so Δh = c<sub>p</sub>ΔT with c<sub>p</sub> = 5.1926 kJ/kg·K is exact."), 6)
card("cvcp", "A hair dryer heats a steady stream of air from 20 °C to 50 °C. Find the heater power.",
     [q(WHICHC, [CPP, CV], 0)],
     W("Rule 6: steady flow: Ẇ<sub>e,in</sub> = ṁ(h<sub>2</sub> − h<sub>1</sub>) = ṁc<sub>p</sub>ΔT.",
       "The duct volume is fixed, but that doesn't make it a c<sub>v</sub> problem: the flow work rides along in h."), 6)
card("cvcp", "A paddle wheel stirs argon in a rigid, insulated tank. Find the temperature rise.",
     [q(WHICHC, [CV, CPP], 0)],
     W("Rule 6: closed, rigid, insulated: W<sub>pw,in</sub> = ΔU = mc<sub>v</sub>ΔT.",
       "Argon is a noble gas (rule 3), so c<sub>v</sub> = 0.3122 kJ/kg·K from A-2a."), 6)
card("cvcp", "Air in a piston-cylinder is compressed polytropically (n = 1.3) from 20 °C to 80 °C while losing some heat. Find Q.",
     [q(WHICHC, [CV, CPP], 0)],
     W("Rule 6: the pressure changes, so boundary work does not fold into ΔH.",
       "First law: W<sub>b,in</sub> − Q<sub>out</sub> = ΔU = mc<sub>v</sub>ΔT. Get W<sub>b</sub> from the polytropic relation, separately.",
       "c<sub>p</sub> only shortcuts a closed system when P is constant."), 6)
card("cvcp", "Two air streams, one at 20 °C and one at 50 °C, mix steadily in an insulated duct. Find the exit temperature.",
     [q(WHICHC, [CPP, CV], 0)],
     W("Rule 6: steady flow: ṁ<sub>1</sub>h<sub>1</sub> + ṁ<sub>2</sub>h<sub>2</sub> = ṁ<sub>3</sub>h<sub>3</sub>.",
       "With constant c<sub>p</sub> (small ΔT, rule 4), the c<sub>p</sub> cancels and T<sub>3</sub> is the mass-weighted average."), 6)
card("cvcp", "A weather balloon's helium is heated by sunlight while the balloon expands at constant pressure.",
     [q(WHICHC, [CPP, CV], 0)],
     W("Rule 6: closed system at constant P, so Q<sub>in</sub> = ΔH = mc<sub>p</sub>ΔT.",
       "Noble gas (rule 3): c<sub>p</sub> = 5.1926 kJ/kg·K."), 6)
card("cvcp", "A rigid tank of nitrogen is heated from 300 K to 800 K. Which property do you read from A-18?",
     [q("Which value from the table?", ["ū (internal energy)", "h̄ (enthalpy)", "s̄°"], 0)],
     W("Rule 5: nitrogen over a large ΔT uses its own table, A-18.",
       "Rule 6: rigid and closed, so Q<sub>in</sub> = ΔU. Read ū at both temperatures, subtract, and divide by M = 28.013.",
       "The c<sub>v</sub>-versus-c<sub>p</sub> choice shows up in the table as ū versus h̄."), 6)

# ------------------------------------------------------------------ isentropic relations
ISO = "Which isentropic relation?"
KREL = "T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>"
KRELV = "T<sub>2</sub>/T<sub>1</sub> = (v<sub>1</sub>/v<sub>2</sub>)<sup>k−1</sup>"
PR = "P<sub>r2</sub> = P<sub>r1</sub>(P<sub>2</sub>/P<sub>1</sub>) from A-17"
VR = "v<sub>r2</sub> = v<sub>r1</sub>(v<sub>2</sub>/v<sub>1</sub>) from A-17"
S21 = "s<sub>2</sub> = s<sub>1</sub>, read from the steam or R-134a tables"
SBAR = "s̄°<sub>2</sub> = s̄°<sub>1</sub> + R<sub>u</sub> ln(P<sub>2</sub>/P<sub>1</sub>) from A-18"
card("isen", "Air is compressed isentropically from 100 kPa and 300 K to 800 kPa. Use cold-air-standard assumptions.",
     [q(ISO, [KREL + ", k = 1.4", PR, S21, "T<sub>2</sub> = T<sub>1</sub>(P<sub>2</sub>/P<sub>1</sub>)"], 0)],
     W("Rule 4: \"cold-air-standard\" means constant specific heats at room temperature, k = 1.4.",
       "Rule 7: constant c gives the k-relation: T<sub>2</sub> = 300(8)<sup>0.4/1.4</sup> = 543 K.",
       "T<sub>2</sub> = T<sub>1</sub>(P<sub>2</sub>/P<sub>1</sub>) would be the ideal-gas law with v held constant, which isn't this process."), 7)
card("isen", "Air expands isentropically in a gas turbine from 1400 K and 1.2 MPa to 100 kPa. Use variable specific heats.",
     [q(ISO, [PR, KREL + ", k = 1.4", VR, S21], 0)],
     W("Rule 4: large ΔT with variable specific heats: A-17.",
       "Rule 7: pressures are given, so use the relative pressure: P<sub>r2</sub> = P<sub>r1</sub>(100/1200). Read P<sub>r1</sub> at 1400 K, then find T<sub>2</sub> and h<sub>2</sub> where P<sub>r</sub> = P<sub>r2</sub>.",
       "v<sub>r</sub> is the volume-ratio version, for when you know v<sub>2</sub>/v<sub>1</sub> instead."), 7)
card("isen", "An Otto cycle compresses air with compression ratio r = 8 from 300 K. Use variable specific heats.",
     [q(ISO, [VR, PR, KRELV + ", k = 1.4"], 0)],
     W("Rule 4: variable specific heats: A-17.",
       "Rule 7: the compression ratio is a <b>volume</b> ratio, so use relative volume: v<sub>r2</sub> = v<sub>r1</sub>/8.",
       "P<sub>r</sub> would need P<sub>2</sub>/P<sub>1</sub>, which you don't know yet."), 7)
card("isen", "Helium is compressed isentropically from 100 kPa and 300 K to 500 kPa.",
     [q(ISO, [KREL + ", k = 1.667", KREL + ", k = 1.4", PR], 0)],
     W("Rule 3: helium is a noble gas, so constant specific heats are exact, with k = 1.667 (A-2a).",
       "Rule 7: T<sub>2</sub> = 300(5)<sup>0.667/1.667</sup> = 571 K.",
       "k = 1.4 is air's value. A-17's P<sub>r</sub> is built only for air."), 7)
card("isen", "Steam expands isentropically in a turbine from 8 MPa, 500 °C to 20 kPa.",
     [q(ISO, [S21, KREL + ", k = 1.3", PR], 0)],
     W("Rule 1: steam tables.",
       "Rule 7: with tables, isentropic simply means s<sub>2</sub> = s<sub>1</sub>. Read s<sub>1</sub> from A-6, then fix state 2 with P<sub>2</sub> = 20 kPa and s<sub>2</sub> in A-5 (it'll be a mixture: find x<sub>2</sub>).",
       "The k-relation assumes an ideal gas with constant c, which steam is not."), 7)
card("isen", "R-134a is compressed isentropically from saturated vapor at −10 °C to 0.8 MPa.",
     [q(ISO, [S21, KREL + ", k = 1.1", PR], 0)],
     W("Rule 1: R-134a tables.",
       "Rule 7: s<sub>2</sub> = s<sub>1</sub> = s<sub>g</sub>@−10 °C (A-11). In A-13's 0.8 MPa block, interpolate to find T<sub>2</sub> and h<sub>2</sub> at that s."), 7)
card("isen", "Nitrogen expands isentropically in a turbine from 1000 K and 1 MPa to 100 kPa.",
     [q(ISO, [SBAR, KREL + ", k = 1.4", PR], 0)],
     W("Rule 5: nitrogen uses its own ideal-gas table, A-18.",
       "Rule 7: s̄°<sub>2</sub> = s̄°<sub>1</sub> + R<sub>u</sub> ln(0.1) with R<sub>u</sub> = 8.314 kJ/kmol·K. Find T<sub>2</sub> where A-18 lists that s̄°.",
       "A-17's P<sub>r</sub> column is computed for air only."), 7)
card("isen", "A Brayton cycle runs with pressure ratio 10 and compressor inlet at 300 K. The problem says \"cold-air-standard.\"",
     [q(ISO, [KREL + ", k = 1.4", PR, S21], 0)],
     W("Rule 4: the problem told you: constant specific heats at room temperature.",
       "Rule 7: T<sub>2s</sub> = 300(10)<sup>0.2857</sup> = 579 K. Same relation for the turbine."), 7)
card("isen", "A Diesel engine compresses air with compression ratio 18 from 300 K. No mention of cold-air-standard.",
     [q(ISO, [VR, KRELV + ", k = 1.4", PR], 0)],
     W("Rule 4: the temperature will climb past 900 K, a large ΔT, so A-17.",
       "Rule 7: compression ratio is a volume ratio: v<sub>r2</sub> = v<sub>r1</sub>/18."), 7)
card("isen", "A fan compresses air isentropically from 100 kPa to 105 kPa at 20 °C.",
     [q(ISO, [KREL + ", k = 1.4", PR, S21], 0)],
     W("Rule 4: the temperature rises only about 4 °C, a small ΔT, so constant specific heats.",
       "Rule 7: k-relation with k = 1.4."), 7)

# ------------------------------------------------------------------ is the state fixed? what carries over?
card("state", "Water at 100 °C and 101.42 kPa. Find h.",
     [q("What can you find?", ["Not enough information", "h<sub>f</sub> = 419.17 kJ/kg", "h<sub>g</sub> = 2675.6 kJ/kg"], 0)],
     W("101.42 kPa is P<sub>sat</sub>@100 °C, so the state is somewhere on the dome.",
       "Inside the dome, T and P are not independent: they're one piece of information. You need a second one, like x, v or h.",
       "State postulate: two <b>independent</b> intensive properties fix a simple compressible system."), 0)
card("state", "R-134a at −10 °C and exactly the saturation pressure for −10 °C (Table A-11). Find v.",
     [q("What can you find?", ["Not enough information", "v<sub>f</sub>", "v<sub>g</sub>"], 0)],
     W("At P<sub>sat</sub>, the state could be anywhere from saturated liquid to saturated vapor.",
       "T and P are dependent in the dome, so you need x or another property."), 0)
card("state", "Water at 500 kPa with v = 0.37483 m³/kg. Find h.",
     [q("What is the state?", ["Saturated vapor: h = h<sub>g</sub>", "Not enough information", "Superheated: use A-6", "Saturated liquid"], 0)],
     W("Compare with Table A-5 at 500 kPa: v<sub>g</sub> = 0.37483 m³/kg.",
       "v = v<sub>g</sub> exactly, so x = 1: saturated vapor, h = h<sub>g</sub> = 2748.1 kJ/kg.",
       "v and P are independent, so the state is fixed."), 0)
card("state", "Which pairs fix the state of a saturated water mixture? Choose all that work.",
     [q("Choose all that fix the state:", ["P and T", "P and x", "T and x", "T and v"], [1, 2, 3], True)],
     W("In the dome, P and T are tied together (one is the other's saturation value), so they count as one property.",
       "Any pairing of P or T with x, v, u, h or s fixes the state."), 0)
card("state", "Superheated R-134a at 0.8 MPa and 50 °C. Is the state fixed?",
     [q("Is it fixed?", ["Yes: outside the dome, T and P are independent", "No: you also need x", "No: you need v"], 0)],
     W("T<sub>sat</sub>@0.8 MPa = 31.3 °C, so 50 °C is superheated.",
       "Outside the dome, T and P vary independently, so the pair fixes the state: Table A-13, 0.8 MPa block, 50 °C row.",
       "Quality has no meaning for superheated vapor."), 0)
card("state", "A sealed rigid tank of water is heated. Which property is the same at both states?",
     [q("What carries over?", ["v", "P", "T", "x"], 0)],
     W("Rigid: V fixed. Sealed: m fixed. So v = V/m is the same before and after.",
       "State 2 is then fixed by v<sub>2</sub> = v<sub>1</sub> plus one more property (the final T or P)."), 0)
card("state", "Steam passes through a throttling valve. Which property is the same at inlet and exit?",
     [q("What carries over?", ["h", "s", "T", "u"], 0)],
     W("A valve has no work, negligible heat transfer and negligible ΔKE and ΔPE.",
       "The steady-flow energy balance leaves h<sub>1</sub> = h<sub>2</sub>. The exit state is fixed by P<sub>2</sub> and h<sub>2</sub>.",
       "T is <b>not</b> constant: wet steam cools as it throttles, and a throttled refrigerant drops sharply."), 0)
card("state", "Steam expands in an isentropic turbine. Which pair fixes the exit state?",
     [q("Exit state from:", ["P<sub>2</sub> and s<sub>2</sub> = s<sub>1</sub>", "P<sub>2</sub> and h<sub>2</sub> = h<sub>1</sub>", "T<sub>2</sub> = T<sub>1</sub> and P<sub>2</sub>"], 0)],
     W("Isentropic means s<sub>2</sub> = s<sub>1</sub>.",
       "Look up s<sub>1</sub> at the inlet, then fix state 2 with P<sub>2</sub> and s<sub>2</sub>. Compare s<sub>2</sub> with s<sub>f</sub> and s<sub>g</sub> at P<sub>2</sub> to find the phase.",
       "h<sub>2</sub> = h<sub>1</sub> is the throttle, where no work comes out."), 0)
card("state", "Liquid water at 300 kPa and 40 °C. Which value is h?",
     [q("h ≈", ["h<sub>f</sub>@40 °C (A-4)", "h<sub>f</sub>@300 kPa (A-5)", "h<sub>g</sub>@300 kPa (A-5)"], 0)],
     W("T<sub>sat</sub>@300 kPa = 133.5 °C, and 40 °C is below it: compressed liquid.",
       "Below 5 MPa, a compressed liquid is approximately saturated liquid at the same <b>temperature</b>: h ≈ h<sub>f</sub>@40 °C = 167.53 kJ/kg.",
       "h<sub>f</sub>@300 kPa is saturated liquid at 133.5 °C, a much hotter state."), 0)

RULES = [
    ("Water or R-134a?", "Use its own tables in every phase: steam A-4 to A-7, R-134a A-11 to A-13. Never PV = mRT, never cΔT, never the Z chart."),
    ("A gas?", "Ideal gas only when it acts like one. If P is high or T is near the critical temperature, check Z on the compressibility chart (A-15)."),
    ("Noble gas (He, Ar, Ne)?", "Constant c<sub>p</sub> and c<sub>v</sub> from A-2a, at any temperature. k = 1.667."),
    ("Air?", "Small ΔT near room temperature: constant c from A-2a (k = 1.4). Large ΔT: Table A-17. If the problem says \"constant specific heats\" or \"cold-air-standard,\" use constant c."),
    ("N₂, O₂, CO₂, CO, H₂?", "Their own ideal-gas tables, A-18 to A-22. Values are per kmol: divide by M."),
    ("c<sub>v</sub> or c<sub>p</sub>?", "With constant c: Δu = c<sub>v</sub>ΔT and Δh = c<sub>p</sub>ΔT. With a table (A-17 to A-22), read u or h instead. Closed and rigid: Δu. Closed at constant P: Δh. Steady flow: Δh."),
    ("Isentropic?", "Tables: s<sub>2</sub> = s<sub>1</sub>. Constant c: k-relations. A-17: P<sub>r</sub> for a pressure ratio, v<sub>r</sub> for a volume ratio. A-18 to A-22: s̄°<sub>2</sub> = s̄°<sub>1</sub> + R<sub>u</sub> ln(P<sub>2</sub>/P<sub>1</sub>)."),
]

json.dump({"cards": C, "rules": [{"h": h, "t": t} for h, t in RULES]}, open("model.json", "w"), ensure_ascii=False)
from collections import Counter
print(len(C), Counter(c["cat"] for c in C))
