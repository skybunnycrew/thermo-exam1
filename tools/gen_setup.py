"""Quick setup drills (Nov 24, 2026). Setup only, no arithmetic: the system, the terms that survive, where the
properties come from, and the working equation. Written in the style of the weekly "setup sprint, setup only, no
arithmetic" prompts in the class agendas, the WAMAP sets, and Çengel's chapter problems (original wording and numbers;
nothing from the solutions manual). About 40% are tagged tricky: each hides one trap students fall into on exams,
and the card's "The trap" line names it.

Balance convention (Matthew): in terms − out terms = change, every term a positive magnitude.
Run: python3 gen_setup.py   (writes setup_bank.json)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

CARDS = []
def card(id, ch, stem, qs, trap=None, tricky=False, src=None):
    CARDS.append(dict(id=id, ch=ch, s=stem, qs=qs, trap=trap, tr=tricky, src=src))
def q(prompt, opts, a, why, multi=False):
    return dict(q=prompt, o=opts, a=a, w=why, m=multi)

SYS = ["Closed system (a fixed mass)", "Control volume, steady flow", "Control volume, unsteady (the mass inside changes)", "A cycle (the fluid returns to its starting state)"]
def sysq(a, why, opts=SYS): return q("What kind of system?", opts, a, why)

sub = lambda s, k: f"{s}<sub>{k}</sub>"
Qin, Qout, Win, Wout = "Q<sub>in</sub>", "Q<sub>out</sub>", "W<sub>in</sub>", "W<sub>out</sub>"
qQin, qQout, qWin, qWout = "Q̇<sub>in</sub>", "Q̇<sub>out</sub>", "Ẇ<sub>in</sub>", "Ẇ<sub>out</sub>"
SFTERMS = [qQin, qQout, qWin, qWout, "ṁ(h<sub>2</sub> − h<sub>1</sub>)", "ṁ(V<sub>2</sub>² − V<sub>1</sub>²)/2", "ṁg(z<sub>2</sub> − z<sub>1</sub>)"]
CLTERMS = [Qin, Qout, Win + " (paddle, electric, shaft)", Wout + " (paddle, electric, shaft)", "W<sub>b</sub> (boundary work)", "ΔU", "ΔKE", "ΔPE"]

# ======================================================================= Ch. 1
card("S101", 1, "A U-tube manometer on a natural-gas line shows the mercury 40 cm higher in the leg open to the room. The gas column is short.",
     [q("Which pressure does the manometer reading give directly?", ["The gauge pressure of the gas", "The absolute pressure of the gas", "The vacuum pressure", "The atmospheric pressure"], 0,
        "An open leg compares the gas with the room, so ρgh is the gauge pressure. Add P<sub>atm</sub> for absolute."),
      q("Which term can you usually drop?", ["ρgh of the gas column", "ρgh of the mercury", "P<sub>atm</sub>", "None"], 0,
        "A gas is about 10,000 times less dense than mercury, so a short gas column adds almost nothing."),
      q("Working equation", ["P<sub>gas</sub> = P<sub>atm</sub> + ρ<sub>Hg</sub>gh", "P<sub>gas</sub> = P<sub>atm</sub> − ρ<sub>Hg</sub>gh", "P<sub>gas</sub> = ρ<sub>Hg</sub>gh", "P<sub>gas</sub> = P<sub>atm</sub> + ρ<sub>gas</sub>gh"], 0,
        "Walk from the open end down to the level of the gas side: going down adds ρgh. Mercury pushed up on the open side means the gas is above atmospheric.")])
card("S102", 1, "A diver works 30 m down in a freshwater lake at sea level.",
     [q("What pressure does she feel on her eardrums?", ["Absolute: P<sub>atm</sub> + ρgh", "Gauge: ρgh only", "Atmospheric only", "ρgh − P<sub>atm</sub>"], 0,
        "Her body feels everything pressing on it: the air above the lake and the water. A gauge on her tank would read the gauge part, ρgh."),
      q("Which density?", ["Fresh water, about 1000 kg/m³", "Seawater, about 1025 kg/m³", "Air", "Mercury"], 0, "A lake is fresh water. Seawater only if the problem says ocean.")])
card("S103", 1, "A frictionless piston of mass 20 kg and area 0.01 m² holds gas in a vertical cylinder open to the atmosphere above. A 40 kg block sits on the piston.",
     [q("What sets the gas pressure?", ["A force balance on the piston: gas pushes up, atmosphere + piston weight + block weight push down", "The gas temperature", "The ideal-gas law alone", "Only the block"], 0,
        "Draw the free-body diagram of the piston. Pressure comes from mechanics, not from the gas."),
      q("Working equation", ["P = P<sub>atm</sub> + (m<sub>p</sub> + m<sub>block</sub>)g/A", "P = (m<sub>p</sub> + m<sub>block</sub>)g/A", "P = P<sub>atm</sub> − (m<sub>p</sub> + m<sub>block</sub>)g/A", "P = P<sub>atm</sub> + m<sub>block</sub>g/A"], 0,
        "The atmosphere above the piston pushes down too. Dropping it gives a gauge pressure."),
      q("If the gas is heated slowly and the piston rises freely, the pressure…", ["Stays the same", "Rises", "Falls", "Doubles"], 0,
        "Nothing in the force balance changed, so P stays put. That's why a free piston means a constant-pressure process.")],
     trap="Forgetting P<sub>atm</sub> above the piston gives a gauge pressure where the problem wants absolute.", tricky=True)

# ======================================================================= Ch. 2
card("S201", 2, "A rigid, insulated tank of air has a resistance heater inside. The heater runs from a wall outlet for 10 minutes. System: the air and the heater.",
     [sysq(0, "Nothing crosses the boundary but electricity."),
      q("How does the energy cross the boundary?", ["As electrical work in", "As heat in", "As boundary work", "It doesn't; the tank is insulated"], 0,
        "With the heater inside the system, electrons crossing the wall are work. Heat only crosses because of a temperature difference."),
      q("Which terms stay?", CLTERMS, [2, 5], "Insulated: no Q. Rigid: no boundary work. Not moving: no ΔKE or ΔPE. W<sub>e,in</sub> = ΔU.", multi=True)],
     trap="Calling the heater's energy 'heat' when the heater is inside your boundary.", tricky=True, src="Class setup sprint")
card("S202", 2, "A 1500 kg car brakes from 60 mph to rest on a level road. System: the car.",
     [q("Which energy term changes most?", ["ΔKE (it goes to zero)", "ΔPE", "Boundary work", "Flow work"], 0, "Level road: no ΔPE. The kinetic energy has to go somewhere."),
      q("Where does it go?", ["Into internal energy of the brakes, then out as heat to the air", "It's destroyed", "Into potential energy", "Into boundary work"], 0,
        "Energy is conserved: friction warms the brake discs (ΔU), and they cool by losing heat to the air.")], src="Class setup sprint")
card("S203", 2, "A water pump's motor draws 15 kW of electricity and is 90% efficient. Find the power the pump gives the water. You draw the boundary around the pump only, then around the motor and pump together.",
     [q("Pump only: what crosses the boundary as work?", ["The shaft power from the motor, 0.90 × 15 kW", "The full 15 kW of electricity", "The water's KE", "Nothing"], 0,
        "With only the pump inside, the motor's losses happen outside your system; the pump receives the shaft power."),
      q("Motor + pump: which efficiency describes the whole unit?", ["Overall: η<sub>motor</sub> × η<sub>pump</sub>", "η<sub>motor</sub> only", "η<sub>pump</sub> only", "The Carnot efficiency"], 0,
        "Efficiencies in series multiply. Where you draw the boundary decides which one you're computing.")],
     trap="Using the electrical input as the pump's shaft work.", tricky=True, src="Class setup sprint")

# ======================================================================= Ch. 3
card("S301", 3, "R-134a at 200 kPa with a quality of 0.4.",
     [q("Which table?", ["A-12 (saturated R-134a, by pressure)", "A-11 (saturated, by temperature)", "A-13 (superheated)", "Ideal gas"], 0,
        "A quality means a saturated mixture, and you're given P, so the pressure table."),
      q("How do you get v?", ["v = v<sub>f</sub> + x(v<sub>g</sub> − v<sub>f</sub>)", "v = xv<sub>g</sub>", "v = v<sub>g</sub>", "v = RT/P"], 0, "Weight the two phases by mass."),
      q("The temperature is…", ["T<sub>sat</sub> at 200 kPa, read from the table", "Unknown until you know v", "200 K", "Room temperature"], 0, "Inside the dome, P and T are tied.")], src="Class setup sprint")
card("S302", 3, "Steam at 15 MPa and 350 °C.",
     [q("Ideal gas, compressibility chart, or table?", ["Steam table: check the phase first", "Ideal gas: it's steam", "Compressibility chart", "Any of them"], 0,
        "Rule 1: tables first, and never ideal gas for water vapor."),
      q("Compare T with T<sub>sat</sub> at 15 MPa (342.2 °C). The phase is…", ["Superheated vapor (just barely)", "Compressed liquid", "Saturated mixture", "Supercritical"], 0,
        "T &gt; T<sub>sat</sub> at that P means superheated. Look in A-6, 15 MPa block.")],
     trap="Picking ideal gas for 'steam'. Near the dome at 15 MPa it's off by about 30%.", tricky=True, src="Class setup sprint")
card("S303", 3, "A rigid tank of R-134a is heated from 200 kPa to 800 kPa.",
     [q("Which property is the same at both states?", ["Specific volume v", "Temperature", "Quality", "Enthalpy"], 0, "Rigid and sealed: fixed mass and fixed volume, so v<sub>2</sub> = v<sub>1</sub>."),
      q("How do you fix state 2?", ["P<sub>2</sub> = 800 kPa and v<sub>2</sub> = v<sub>1</sub>", "P<sub>2</sub> and T<sub>1</sub>", "P<sub>2</sub> alone", "T<sub>2</sub> = T<sub>1</sub>"], 0,
        "Two independent properties fix the state. Compare v<sub>2</sub> with v<sub>g</sub> at 800 kPa to find the phase.")], src="Class setup sprint")
card("S304", 3, "1 lbm of water fills 2.649 ft³ at 400 °F under a weighted piston. It cools until the piston rests on stops, then keeps cooling.",
     [q("While the piston floats, what is constant?", ["Pressure", "Volume", "Temperature", "Quality"], 0, "Weighted, free piston: the force balance fixes P."),
      q("After it lands on the stops, what is constant?", ["Volume (so v)", "Pressure", "Temperature", "Nothing"], 0, "Stops fix the volume. Two processes, two different constants."),
      q("First move with the numbers?", ["v = 2.649 ft³/lbm at 400 °F, then find the phase in A-4E/A-6E", "Use the ideal-gas law", "Assume saturated vapor", "Use c<sub>p</sub>ΔT"], 0,
        "v and T fix state 1. Compare with v<sub>g</sub> at 400 °F to see where you start.")],
     trap="Treating the whole process as constant pressure, past the moment the piston hits the stops.", tricky=True, src="Class setup sprint")
card("S305", 3, "Liquid water at 80 °C and 5 MPa.",
     [q("Where is h?", ["h ≈ h<sub>f</sub> at 80 °C (A-4), or A-7 if you need precision", "A-6 superheated at 5 MPa", "h<sub>f</sub> at 5 MPa (A-5)", "c<sub>p</sub>T"], 0,
        "Compressed liquid behaves like saturated liquid at the same temperature. Using h<sub>f</sub> at the pressure is the classic slip."),
      q("How do you know it's compressed liquid?", ["T = 80 °C is below T<sub>sat</sub> at 5 MPa (264 °C)", "P is high", "It says liquid, so it's saturated", "v is small"], 0, "Below T<sub>sat</sub> for its pressure: compressed liquid.")],
     trap="Reading h<sub>f</sub> at 5 MPa instead of at 80 °C.", tricky=True)
card("S306", 3, "A nitrogen tank leaks slowly from 600 kPa to 400 kPa while staying at room temperature. Find the fraction of the gas that escaped.",
     [q("Property model?", ["Ideal gas: room temperature is far above N<sub>2</sub>'s critical temperature (126 K)", "Steam tables", "Compressibility chart required", "Incompressible"], 0,
        "Check T<sub>R</sub> and P<sub>R</sub>: T<sub>R</sub> ≈ 2.4, P<sub>R</sub> ≈ 0.2. Ideal gas is excellent."),
      q("What's held constant?", ["V and T, so m ∝ P", "m and V", "P/T", "Nothing"], 0, "PV = mRT with V and T fixed: m<sub>2</sub>/m<sub>1</sub> = P<sub>2</sub>/P<sub>1</sub>.")], src="Class setup sprint")

# ======================================================================= Ch. 4
card("S401", 4, "An insulated piston-cylinder holds air at constant pressure. A paddle wheel stirs it and a resistor heats it at the same time.",
     [sysq(0, "Fixed mass of air."),
      q("Which terms stay?", CLTERMS, [2, 4, 5], "Insulated: no Q. Paddle and electrical work in. The piston rises, so boundary work goes out. No KE or PE change.", multi=True),
      q("Working equation", ["W<sub>pw,in</sub> + W<sub>e,in</sub> − W<sub>b,out</sub> = ΔU, so W<sub>pw,in</sub> + W<sub>e,in</sub> = m(h<sub>2</sub> − h<sub>1</sub>)", "W<sub>pw,in</sub> + W<sub>e,in</sub> = m(u<sub>2</sub> − u<sub>1</sub>)", "Q<sub>in</sub> = mc<sub>v</sub>ΔT", "W<sub>pw,in</sub> = W<sub>b,out</sub>"], 0,
        "At constant P, W<sub>b</sub> = PΔV folds into ΔU to make ΔH. Leaving W<sub>b</sub> out is the common slip.")],
     trap="Forgetting the boundary work when other work is going in.", tricky=True, src="Class setup sprint")
card("S402", 4, "A rigid tank of steam cools from 300 °C to room temperature. Find the heat lost.",
     [sysq(0, "Fixed mass in a sealed tank."),
      q("Which terms stay?", CLTERMS, [1, 5], "Rigid: no boundary work. No paddle. Heat out, ΔU.", multi=True),
      q("How do you fix state 2?", ["v<sub>2</sub> = v<sub>1</sub> and T<sub>2</sub> = room temperature", "P<sub>2</sub> = P<sub>1</sub>", "Saturated vapor at room temperature", "Ideal gas"], 0,
        "Rigid means v carries over. At room temperature v<sub>2</sub> will sit inside the dome: find x<sub>2</sub> from v."),
      q("Working equation", ["Q<sub>out</sub> = m(u<sub>1</sub> − u<sub>2</sub>)", "Q<sub>out</sub> = m(h<sub>1</sub> − h<sub>2</sub>)", "Q<sub>out</sub> = mc<sub>p</sub>ΔT", "Q<sub>out</sub> = PΔV"], 0, "Constant volume: internal energy, not enthalpy.")],
     trap="Using h (constant-pressure thinking) in a rigid tank.", tricky=True)
card("S403", 4, "A partition splits an insulated rigid tank: one side holds air, the other is a vacuum. The partition breaks.",
     [q("Boundary work done by the air?", ["Zero: it expands into nothing", "PΔV", "mRΔT", "It depends on the final pressure"], 0, "Nothing resists the expansion, so no work. Volume growing doesn't by itself mean work."),
      q("What happens to T for an ideal gas?", ["It stays the same: Q = 0, W = 0, so ΔU = 0", "It drops, because the gas expanded", "It rises", "It depends on the volume ratio"], 0,
        "ΔU = 0 and u depends only on T for an ideal gas."),
      q("Is the process reversible?", ["No: entropy is generated; s rises even though T doesn't", "Yes, since Q = 0", "Yes, since T is constant", "Can't tell"], 0, "Free expansion is the textbook irreversible process. Δs = R ln(V<sub>2</sub>/V<sub>1</sub>) &gt; 0.")],
     trap="Writing W<sub>b</sub> = PΔV because the volume changed.", tricky=True)
card("S404", 4, "Saturated water vapor at 400 kPa is cooled at constant pressure in a piston-cylinder until it is saturated liquid.",
     [q("Sketch on T-v. The path is…", ["A horizontal line across the dome, right to left", "A vertical line", "A curve down the saturated-vapor line", "Outside the dome"], 0, "Constant P inside the dome is also constant T."),
      q("Heat out per kg?", ["h<sub>fg</sub> at 400 kPa", "u<sub>fg</sub> at 400 kPa", "c<sub>p</sub>ΔT", "Zero: T doesn't change"], 0,
        "W<sub>b,in</sub> − Q<sub>out</sub> = ΔU with W<sub>b,in</sub> = P(V<sub>1</sub> − V<sub>2</sub>), so q<sub>out</sub> = h<sub>1</sub> − h<sub>2</sub> = h<sub>fg</sub>. Constant T doesn't mean no heat.")],
     trap="Thinking no temperature change means no heat transfer.", tricky=True, src="Class setup sprint")
card("S405", 4, "Air in a piston-cylinder is compressed polytropically, PV<sup>1.3</sup> = constant, from 100 kPa to 800 kPa.",
     [q("Boundary work?", ["W<sub>b</sub> = (P<sub>2</sub>V<sub>2</sub> − P<sub>1</sub>V<sub>1</sub>)/(1 − n), negative here, so it is work in", "W<sub>b</sub> = P(V<sub>2</sub> − V<sub>1</sub>)", "W<sub>b</sub> = mRT ln(V<sub>2</sub>/V<sub>1</sub>)", "W<sub>b</sub> = 0"], 0,
        "Polytropic with n ≠ 1. The log form is only for n = 1 (isothermal ideal gas)."),
      q("How do you get T<sub>2</sub>?", ["T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(n−1)/n</sup>", "T<sub>2</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>", "T<sub>2</sub> = T<sub>1</sub>", "Ideal gas law with V<sub>1</sub>"], 0,
        "Use the process's own exponent n. The k form is the isentropic special case."),
      q("Is there heat transfer?", ["Yes, in general: get it from the first law after finding W<sub>b</sub> and ΔU", "No: polytropic means adiabatic", "Only if n = k", "Only if T rises"], 0, "Polytropic is not adiabatic unless n = k.")],
     trap="Using k in place of n, or assuming polytropic means adiabatic.", tricky=True)
card("S406", 4, "Air at 300 K is heated to 1000 K in a rigid tank. Find the heat added per kg.",
     [q("Property model?", ["Ideal gas with A-17 (large ΔT)", "Constant c<sub>v</sub> from A-2a at 300 K", "Steam tables", "Compressibility chart"], 0,
        "Rule 4: air with a large ΔT uses A-17. A 700 K rise is large."),
      q("Working equation", ["Q<sub>in</sub> = m(u<sub>2</sub> − u<sub>1</sub>)", "Q<sub>in</sub> = m(h<sub>2</sub> − h<sub>1</sub>)", "Q<sub>in</sub> = mc<sub>p</sub>ΔT", "Q<sub>in</sub> = mRΔT"], 0, "Rigid: no boundary work, so Q = ΔU; read u from A-17.")])
card("S407", 4, "A 2 kg aluminum block at 200 °C is dropped into an insulated tank holding 10 kg of water at 20 °C. Find the final temperature.",
     [q("Best system?", ["Block + water together: insulated, so Q = 0 across the boundary", "The block alone", "The water alone", "A control volume"], 0,
        "Put both inside and the heat between them is internal. One equation, one unknown."),
      q("Working equation", ["0 = m<sub>Al</sub>c<sub>Al</sub>(T<sub>f</sub> − 200) + m<sub>w</sub>c<sub>w</sub>(T<sub>f</sub> − 20)", "m<sub>Al</sub>c<sub>Al</sub>(200 − T<sub>f</sub>) = m<sub>w</sub>(h<sub>g</sub> − h<sub>f</sub>)", "T<sub>f</sub> = (200 + 20)/2", "Q = mc<sub>p</sub>ΔT for the block"], 0,
        "ΔU<sub>Al</sub> + ΔU<sub>water</sub> = 0. For liquid water and solids, c is fine (or u<sub>f</sub> at T from A-4 for the water)."),
      q("Where's c for aluminum?", ["A-3 (0.902 kJ/kg·K)", "A-2a", "A-17", "A-1"], 0, "Solids and liquids: A-3.")])
card("S408", 4, "Air in a closed tank rides on a truck that speeds up from rest to 25 m/s while the air is also heated.",
     [sysq(0, "Same mass of air the whole time, even though it moves."),
      q("Which terms stay?", CLTERMS, [0, 5, 6], "The system itself moves, so ΔKE belongs in the closed-system balance. The truck does no boundary work on rigid air.", multi=True)],
     trap="Thinking KE only matters for flowing streams. A closed system can move.", tricky=True)

# ======================================================================= Ch. 5
card("S501", 5, "Steam expands in a nozzle from 800 kPa to 200 kPa and loses 25 kW of heat to the surroundings. The inlet velocity is small.",
     [sysq(1, "Steam flows through steadily."),
      q("Which terms stay?", SFTERMS, [1, 4, 5], "Heat out (given), no work (no shaft), Δh and ΔKE. Same height.", multi=True),
      q("Working equation", ["ṁh<sub>1</sub> − Q̇<sub>out</sub> − ṁ(h<sub>2</sub> + V<sub>2</sub>²/2) = 0", "0 = ṁ(h<sub>2</sub> − h<sub>1</sub>)", "Ẇ<sub>out</sub> = ṁ(h<sub>1</sub> − h<sub>2</sub>)", "V<sub>2</sub> = √(2(h<sub>1</sub> − h<sub>2</sub>))"], 0,
        "With a heat loss, the plain √(2Δh) is wrong: some of the enthalpy drop leaves as heat."),
      q("Units check before you add h and V²/2?", ["Divide V² by 1000 to get kJ/kg", "Nothing needed", "Multiply h by 1000", "Convert kPa to Pa"], 0, "1 kJ/kg = 1000 m²/s².")],
     trap="Using V<sub>2</sub> = √(2Δh) when heat is leaving.", tricky=True, src="Class setup sprint")
card("S502", 5, "Helium is compressed from 100 kPa, 300 K to 600 kPa. The compressor takes 220 kW and loses 15 kW of heat.",
     [q("Which terms stay?", SFTERMS, [1, 2, 4], "Work in, heat out, Δh. KE and PE small.", multi=True),
      q("Property model?", ["Ideal gas, constant c<sub>p</sub> (noble gas)", "A-17", "Helium tables", "Compressibility chart"], 0, "Monatomic gases have constant c<sub>p</sub> = 5.1926 kJ/kg·K at all temperatures."),
      q("With every term a positive magnitude, the balance reads…", ["Ẇ<sub>in</sub> − Q̇<sub>out</sub> = ṁc<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>)", "Ẇ<sub>in</sub> + Q̇<sub>out</sub> = ṁc<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>)", "−Ẇ − Q̇ = ṁΔh", "Ẇ<sub>in</sub> = ṁc<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>)"], 0,
        "In terms minus out terms equals the change. 15 kW is a magnitude; its direction is in the subscript.")],
     src="Class setup sprint")
card("S503", 5, "R-134a enters an expansion valve as saturated liquid at 1.0 MPa and leaves at 140 kPa.",
     [q("Which terms stay?", SFTERMS, [4], "Throttles: adiabatic (small, fast), no work, small ΔKE. Only Δh remains.", multi=True),
      q("What's the working equation?", ["h<sub>2</sub> = h<sub>1</sub>", "s<sub>2</sub> = s<sub>1</sub>", "T<sub>2</sub> = T<sub>1</sub>", "P<sub>2</sub>v<sub>2</sub> = P<sub>1</sub>v<sub>1</sub>"], 0, "A throttle is isenthalpic, not isentropic."),
      q("How do you find the exit quality?", ["x<sub>2</sub> = (h<sub>1</sub> − h<sub>f</sub>)/h<sub>fg</sub> at 140 kPa", "x<sub>2</sub> = 0", "x<sub>2</sub> = (s<sub>1</sub> − s<sub>f</sub>)/s<sub>fg</sub>", "x<sub>2</sub> = 1"], 0, "Same h, lower pressure: part of the liquid flashes to vapor.")],
     trap="Treating the valve as isentropic.", tricky=True)
card("S504", 5, "A condenser: steam condenses on the outside of tubes; lake water flows through them. Find the lake water's flow rate.",
     [q("How many systems could you draw, and which is fastest here?", ["The whole condenser (Q̇ = 0 across its insulated shell): steam's loss = water's gain", "Only the steam side", "Only the water side", "The lake"], 0,
        "With both streams inside, the heat between them is internal. Draw one stream alone only when the problem asks for that heat rate."),
      q("Which terms stay for the whole condenser?", ["ṁ<sub>s</sub>(h<sub>s,out</sub> − h<sub>s,in</sub>) and ṁ<sub>w</sub>(h<sub>w,out</sub> − h<sub>w,in</sub>) only", "Q̇ and Ẇ", "KE terms", "Ẇ<sub>in</sub> from the pump"], 0, "No work, no heat across the outer shell, small KE and PE."),
      q("Lake water h?", ["h<sub>f</sub> at each temperature (A-4)", "c<sub>p</sub>ΔT with c<sub>p</sub> = 1.005", "h<sub>g</sub>", "A-6"], 0, "Tables first for liquid water: h<sub>f</sub> at T. (1.005 is air's c<sub>p</sub>.)")],
     src="Class setup sprint")
card("S505", 5, "An insulated mixing chamber: hot water (stream 1) and cold water (stream 2) mix and leave as one stream (3). Find the hot-water flow.",
     [q("What goes first?", ["The mass balance: ṁ<sub>3</sub> = ṁ<sub>1</sub> + ṁ<sub>2</sub>", "The entropy balance", "The ideal-gas law", "Bernoulli"], 0, "Two unknown flows need two equations; mass is the free one."),
      q("Energy balance", ["ṁ<sub>1</sub>h<sub>1</sub> + ṁ<sub>2</sub>h<sub>2</sub> = ṁ<sub>3</sub>h<sub>3</sub>", "h<sub>3</sub> = (h<sub>1</sub> + h<sub>2</sub>)/2", "ṁ<sub>1</sub>h<sub>1</sub> = ṁ<sub>2</sub>h<sub>2</sub>", "T<sub>3</sub> = (T<sub>1</sub> + T<sub>2</sub>)/2"], 0,
        "Averaging works only for equal flows. Weight by mass.")], src="Class setup sprint")
card("S506", 5, "A steam turbine: inlet 6 MPa, 500 °C, 50 m/s; exit 20 kPa, x = 0.95, 180 m/s, 2 m lower. It loses 30 kJ/kg of heat.",
     [q("Which terms stay?", SFTERMS, [1, 3, 4, 5, 6], "Everything given matters: heat out, work out, Δh, ΔKE, and ΔPE (small, but given).", multi=True),
      q("Per kg, the work out is…", ["w<sub>out</sub> = (h<sub>1</sub> − h<sub>2</sub>) + (V<sub>1</sub>² − V<sub>2</sub>²)/2 + g(z<sub>1</sub> − z<sub>2</sub>) − q<sub>out</sub>", "w<sub>out</sub> = h<sub>1</sub> − h<sub>2</sub>", "w<sub>out</sub> = h<sub>1</sub> − h<sub>2</sub> + q<sub>out</sub>", "w<sub>out</sub> = (V<sub>2</sub>² − V<sub>1</sub>²)/2"], 0,
        "The heat loss comes out of the work. Adding it is a direction slip.")],
     trap="Adding the heat loss to the work instead of subtracting it.", tricky=True)
card("S507", 5, "A jet engine diffuser slows air from 250 m/s to nearly zero.",
     [q("Which terms stay?", SFTERMS, [4, 5], "Adiabatic, no work, Δh and ΔKE.", multi=True),
      q("What does the temperature do?", ["Rises: the KE becomes enthalpy", "Falls", "Stays the same", "Drops to zero"], 0, "h<sub>2</sub> = h<sub>1</sub> + V<sub>1</sub>²/2. Ram heating.")])
card("S508", 5, "Exhaust gas (treat as air) cools from 800 K to 400 K in a heat-recovery unit that warms water for a school.",
     [q("Property model for the exhaust?", ["Ideal gas with A-17 (large ΔT)", "Constant c<sub>p</sub> at 300 K", "Steam tables", "Incompressible"], 0, "A 400 K swing is large: A-17."),
      q("For the water side?", ["h<sub>f</sub> at T from A-4", "A-17", "Ideal gas", "c<sub>p</sub> = 1.005"], 0, "Liquid water: tables first.")])
card("S509", 5, "A hydroelectric plant: water falls from a reservoir 90 m above the turbine and leaves into a river at about the same speed it entered.",
     [q("What drives the work?", ["ΔPE: ṁg(z<sub>1</sub> − z<sub>2</sub>)", "Δh", "Heat from the sun", "ΔKE"], 0, "Liquid water at nearly constant T: Δh is tiny next to the drop in height."),
      q("Units: g(z<sub>1</sub> − z<sub>2</sub>) in m²/s² is…", ["J/kg: divide by 1000 for kJ/kg", "Already kJ/kg", "kW", "kPa"], 0, "9.81 × 90 = 883 J/kg = 0.883 kJ/kg.")], src="Class setup sprint")
card("S510", 5, "A water pump raises liquid water from 100 kPa to 2 MPa. Find the pump work per kg.",
     [q("Which terms stay?", SFTERMS, [2, 4], "Work in and Δh. Liquid: small KE change, adiabatic.", multi=True),
      q("Fastest route to w<sub>in</sub>?", ["w<sub>in</sub> = vΔP with v ≈ v<sub>f</sub>", "c<sub>p</sub>ΔT", "Look up h<sub>2</sub> in A-6", "Zero: liquids are incompressible"], 0,
        "Incompressible doesn't mean zero work: it means w = ∫v dP ≈ vΔP.")],
     trap="Saying an incompressible liquid needs no work to pump.", tricky=True)

# ======================================================================= Ch. 6
card("S601", 6, "A home heat pump delivers 12 kW to a house at 21 °C when it is 0 °C outside, using 3 kW of electricity.",
     [q("Which COP?", ["COP<sub>HP</sub> = Q̇<sub>H</sub>/Ẇ<sub>in</sub>", "COP<sub>R</sub> = Q̇<sub>L</sub>/Ẇ<sub>in</sub>", "η = Ẇ/Q̇<sub>H</sub>", "Q̇<sub>L</sub>/Q̇<sub>H</sub>"], 0, "A heat pump's product is the heat delivered: Q̇<sub>H</sub>."),
      q("Its Carnot limit uses…", ["T<sub>H</sub> = 294.15 K, T<sub>L</sub> = 273.15 K: COP = T<sub>H</sub>/(T<sub>H</sub> − T<sub>L</sub>)", "21 and 0 °C directly", "T<sub>L</sub>/(T<sub>H</sub> − T<sub>L</sub>)", "1 − T<sub>L</sub>/T<sub>H</sub>"], 0,
        "Kelvins, and the heat-pump form. With 0 °C in Celsius you'd divide by zero.")],
     trap="Plugging Celsius into a Carnot formula.", tricky=True)
card("S602", 6, "An inventor claims an engine takes 500 kJ from a 600 °C source, rejects 200 kJ to a 30 °C river, and produces 300 kJ.",
     [q("Fastest check?", ["Compare η = 300/500 = 60% with η<sub>Carnot</sub> = 1 − 303.15/873.15", "Check the first law only", "Check that W &lt; Q<sub>H</sub>", "Use the ideal-gas law"], 0,
        "The first law balances (500 = 300 + 200); the second law decides. Carnot is 65.3%, so 60% is possible but very ambitious."),
      q("Another way to judge it?", ["S<sub>gen</sub> = Q<sub>L</sub>/T<sub>L</sub> − Q<sub>H</sub>/T<sub>H</sub>: negative means impossible", "Δh across the engine", "COP", "Check it's isothermal"], 0, "Over a cycle the engine's own Δs is zero; only the reservoirs count.")],
     src="Class setup sprint")
card("S603", 6, "A refrigerator runs in a sealed, insulated kitchen with its door wide open.",
     [q("What happens to the kitchen's temperature?", ["It rises: the electrical work ends up as heat in the room", "It falls", "It stays the same", "It depends on the COP"], 0,
        "Take the whole kitchen as the system: insulated, so the only energy crossing is the electricity in. ΔU &gt; 0."),
      q("The best system for this question?", ["The whole kitchen, fridge included", "The refrigerant", "The freezer compartment", "The compressor"], 0, "A big boundary makes the answer obvious.")],
     trap="Thinking an open fridge cools the room.", tricky=True, src="Class setup sprint")
card("S604", 6, "A walk-in cooler at a food bank stays at 2 °C in a 25 °C room. Heat leaks in at 4 kW. Find the least power that could run it.",
     [q("Which device and COP?", ["Refrigerator: COP<sub>R</sub> = Q̇<sub>L</sub>/Ẇ<sub>in</sub>", "Heat pump: Q̇<sub>H</sub>/Ẇ", "Engine: Ẇ/Q̇<sub>H</sub>", "None"], 0, "To hold temperature, it must remove the 4 kW leaking in: Q̇<sub>L</sub> = 4 kW."),
      q("Least power means…", ["Reversible: COP<sub>R,max</sub> = T<sub>L</sub>/(T<sub>H</sub> − T<sub>L</sub>) in kelvins", "COP = 1", "Ẇ = Q̇<sub>L</sub>", "Ẇ = 0"], 0, "The Carnot refrigerator sets the floor on power.")])

# ======================================================================= Ch. 7
card("S701", 7, "Argon is compressed from 14 psia to 200 psia in a compressor with 87% isentropic efficiency.",
     [q("What do you compute first?", ["T<sub>2s</sub>, the isentropic exit temperature: T<sub>2s</sub>/T<sub>1</sub> = (P<sub>2</sub>/P<sub>1</sub>)<sup>(k−1)/k</sup>", "T<sub>2</sub> actual", "The work directly", "s<sub>2</sub>"], 0,
        "Efficiency compares the real device with the ideal one, so build the ideal first."),
      q("Compressor efficiency is…", ["η<sub>C</sub> = (h<sub>2s</sub> − h<sub>1</sub>)/(h<sub>2</sub> − h<sub>1</sub>)", "η<sub>C</sub> = (h<sub>2</sub> − h<sub>1</sub>)/(h<sub>2s</sub> − h<sub>1</sub>)", "η<sub>C</sub> = T<sub>2s</sub>/T<sub>2</sub>", "η<sub>C</sub> = h<sub>2s</sub>/h<sub>2</sub>"], 0,
        "Ideal over actual for a compressor (actual over ideal for a turbine). Write it so the answer is below 1."),
      q("k for argon?", ["1.667 (monatomic)", "1.4", "1.3", "From A-17"], 0, "Noble gases: k = 5/3 at any temperature.")],
     trap="Flipping the compressor efficiency ratio.", tricky=True, src="Class setup sprint")
card("S702", 7, "CO<sub>2</sub> in a rigid tank is heated by a resistor.",
     [q("Which term of the ideal-gas Δs drops out?", ["R ln(v<sub>2</sub>/v<sub>1</sub>): the volume doesn't change", "c<sub>v</sub> ln(T<sub>2</sub>/T<sub>1</sub>)", "Both", "Neither"], 0, "Δs = c<sub>v</sub> ln(T<sub>2</sub>/T<sub>1</sub>) + R ln(v<sub>2</sub>/v<sub>1</sub>); rigid makes the second zero."),
      q("If ΔT is large, better to use…", ["The CO<sub>2</sub> table (A-20): s° values", "A-17 (that's air)", "Steam tables", "Constant c<sub>v</sub> regardless"], 0, "CO<sub>2</sub> has its own ideal-gas table.")], src="Class setup sprint")
card("S703", 7, "A tank of hot water loses heat to 300 K surroundings until it cools to 300 K. Find the total entropy generated.",
     [q("Which systems?", ["The water (ΔS<sub>water</sub> &lt; 0) plus the surroundings as a reservoir (ΔS<sub>surr</sub> = Q/T<sub>0</sub>)", "The water only", "The surroundings only", "A control volume"], 0,
        "The water's entropy falls; the surroundings gain more. S<sub>gen</sub> = ΔS<sub>water</sub> + Q<sub>out</sub>/T<sub>0</sub> &gt; 0."),
      q("ΔS<sub>water</sub>?", ["m(s<sub>2</sub> − s<sub>1</sub>), s from A-4 (or mc ln(T<sub>2</sub>/T<sub>1</sub>))", "Q/T<sub>water</sub>", "Zero", "mc<sub>p</sub>ΔT/T"], 0, "Entropy is a property: get it from the end states.")],
     trap="Calling the water's negative ΔS a violation of the second law.", tricky=True, src="Class setup sprint")
card("S704", 7, "Steam expands in an adiabatic turbine from 8 MPa, 500 °C to 10 kPa. The turbine is 85% efficient.",
     [q("Where does s<sub>2s</sub> come from?", ["s<sub>2s</sub> = s<sub>1</sub> (A-6), then find x<sub>2s</sub> at 10 kPa", "s<sub>g</sub> at 10 kPa", "Ideal gas", "s<sub>1</sub> + q/T"], 0, "The ideal turbine is isentropic."),
      q("Then h<sub>2</sub> actual?", ["h<sub>2</sub> = h<sub>1</sub> − η<sub>T</sub>(h<sub>1</sub> − h<sub>2s</sub>)", "h<sub>2</sub> = h<sub>2s</sub>/η<sub>T</sub>", "h<sub>2</sub> = η<sub>T</sub>h<sub>2s</sub>", "h<sub>2</sub> = h<sub>1</sub> − (h<sub>1</sub> − h<sub>2s</sub>)/η<sub>T</sub>"], 0,
        "The real turbine extracts less work: the real drop is η times the ideal drop."),
      q("Is the real exit state at s<sub>1</sub>?", ["No: adiabatic but irreversible, so s<sub>2</sub> &gt; s<sub>1</sub>", "Yes, it's adiabatic", "Only if the exit is wet", "Can't tell"], 0, "Adiabatic is isentropic only when reversible.")],
     trap="Assuming adiabatic means isentropic for the real turbine.", tricky=True, src="Class setup sprint")
card("S705", 7, "Air is compressed isentropically from 100 kPa, 300 K to 1.2 MPa. Use variable specific heats.",
     [q("Which A-17 column carries you along the isentrope?", ["P<sub>r</sub>: P<sub>r2</sub> = P<sub>r1</sub>(P<sub>2</sub>/P<sub>1</sub>)", "v<sub>r</sub>", "s°", "u"], 0, "Pressure ratio → P<sub>r</sub>. Volume ratio (Otto, Diesel) → v<sub>r</sub>."),
      q("Then the work per kg is…", ["h<sub>2</sub> − h<sub>1</sub> from A-17", "u<sub>2</sub> − u<sub>1</sub>", "c<sub>p</sub>(T<sub>2</sub> − T<sub>1</sub>) at 300 K", "RT ln(P<sub>2</sub>/P<sub>1</sub>)"], 0, "Steady-flow compressor: enthalpy.")])
card("S706", 7, "Heat leaks at 200 W through a window from a 21 °C room to 0 °C outside, in steady state.",
     [q("Entropy generated in the glass?", ["Ṡ<sub>gen</sub> = Q̇(1/T<sub>out</sub> − 1/T<sub>in</sub>), in kelvins", "Zero: steady state", "Q̇/ΔT", "Q̇(1/T<sub>in</sub> − 1/T<sub>out</sub>)"], 0,
        "Steady: the glass's own S doesn't change, so the entropy leaving exceeds the entropy entering by Ṡ<sub>gen</sub>."),
      q("Which sign should you expect?", ["Positive", "Negative", "Zero", "It depends on the glass"], 0, "Heat flowing down a temperature difference always generates entropy.")],
     trap="Steady state means S of the glass is constant, not that S<sub>gen</sub> = 0.", tricky=True)

# ======================================================================= Ch. 9
card("S901", 9, "An Otto cycle with r = 10.5 runs at 2500 cycles per minute and produces 90 kW.",
     [q("What do you find before Q̇<sub>in</sub>?", ["η<sub>th</sub> = 1 − 1/r<sup>k−1</sup>, then Q̇<sub>in</sub> = Ẇ/η", "MEP", "T<sub>3</sub>", "The displacement"], 0, "Cold-air Otto efficiency depends only on r."),
      q("Heat added at constant volume, per kg:", ["q<sub>in</sub> = c<sub>v</sub>(T<sub>3</sub> − T<sub>2</sub>)", "c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)", "h<sub>3</sub> − h<sub>2</sub>", "RT ln(v<sub>3</sub>/v<sub>2</sub>)"], 0, "Constant volume: no boundary work, so q = Δu.")], src="Class setup sprint")
card("S902", 9, "A Diesel cycle: compression ratio 18, cutoff ratio 2. Cold-air-standard.",
     [q("Heat added per kg:", ["c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)", "c<sub>v</sub>(T<sub>3</sub> − T<sub>2</sub>)", "c<sub>v</sub>(T<sub>4</sub> − T<sub>1</sub>)", "w<sub>net</sub>"], 0, "Heat goes in at constant pressure, so the boundary work folds in: Δh."),
      q("Heat rejected per kg:", ["c<sub>v</sub>(T<sub>4</sub> − T<sub>1</sub>)", "c<sub>p</sub>(T<sub>4</sub> − T<sub>1</sub>)", "c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)", "Zero"], 0, "The exhaust stroke is modeled at constant volume: Δu."),
      q("T<sub>3</sub>?", ["T<sub>3</sub> = r<sub>c</sub>T<sub>2</sub>", "T<sub>3</sub> = rT<sub>2</sub>", "T<sub>3</sub> = T<sub>2</sub>r<sub>c</sub><sup>k−1</sup>", "Given"], 0, "Ideal gas at constant P: T ∝ v.")],
     trap="Using c<sub>v</sub> for heat added and c<sub>p</sub> for heat rejected (Otto habits) in a Diesel.", tricky=True)
card("S903", 9, "A simple Brayton cycle has a pressure ratio of 12. Cold-air-standard.",
     [q("T<sub>2</sub>/T<sub>1</sub> = ?", ["r<sub>p</sub><sup>(k−1)/k</sup>", "r<sub>p</sub><sup>k−1</sup>", "r<sub>p</sub>", "r<sub>p</sub><sup>k</sup>"], 0,
        "Pressure ratio: (k − 1)/k = 0.2857. The k − 1 power belongs to a volume ratio (Otto)."),
      q("Net work per kg:", ["c<sub>p</sub>[(T<sub>3</sub> − T<sub>4</sub>) − (T<sub>2</sub> − T<sub>1</sub>)]", "c<sub>v</sub>[(T<sub>3</sub> − T<sub>4</sub>) − (T<sub>2</sub> − T<sub>1</sub>)]", "c<sub>p</sub>(T<sub>3</sub> − T<sub>4</sub>)", "c<sub>p</sub>(T<sub>3</sub> − T<sub>2</sub>)"], 0,
        "Steady-flow devices: Δh, so c<sub>p</sub>. Subtract the compressor.")],
     trap="Using the Otto exponent k − 1 with a pressure ratio.", tricky=True)
card("S904", 9, "A turbojet flies at 280 m/s. Air passes a diffuser, compressor, combustor, turbine and nozzle.",
     [q("Which energy term does the flight speed add at the inlet?", ["Kinetic energy, V<sub>1</sub>²/2, which the diffuser turns into enthalpy", "Potential energy", "Heat", "Shaft work"], 0, "In the engine's frame the air arrives at 280 m/s."),
      q("Turbine work equals…", ["The compressor work (it only drives the compressor)", "The net output", "Zero", "The heat in"], 0, "A turbojet's useful output is thrust, not shaft work."),
      q("Thrust is…", ["ṁ(V<sub>exit</sub> − V<sub>inlet</sub>)", "ṁV<sub>exit</sub>", "ṁV<sub>exit</sub>²/2", "Ẇ<sub>turbine</sub>/V"], 0, "Momentum change of the air.")], src="Class setup sprint")
card("S905", 9, "An Otto engine's mean effective pressure is needed.",
     [q("Which two volumes go in the denominator?", ["v<sub>1</sub> − v<sub>2</sub>: the displacement (BDC minus TDC)", "v<sub>1</sub>", "v<sub>2</sub>", "v<sub>1</sub> + v<sub>2</sub>"], 0, "MEP = w<sub>net</sub>/(v<sub>max</sub> − v<sub>min</sub>)."),
      q("Numerator?", ["w<sub>net</sub>", "q<sub>in</sub>", "w<sub>compression</sub>", "P<sub>3</sub>"], 0, "MEP is the steady pressure that would do the net work over one stroke.")], src="Class setup sprint")
card("S906", 9, "An ideal Stirling cycle with a perfect regenerator runs between 300 K and 900 K.",
     [q("Where does outside heat go in?", ["Only during the isothermal expansion at 900 K", "During both constant-volume processes", "During compression", "Everywhere"], 0,
        "The regenerator supplies the constant-volume heating from the heat stored during constant-volume cooling."),
      q("Its efficiency is…", ["Carnot: 1 − 300/900", "Less than Otto", "1 − 1/r<sup>k−1</sup>", "50%"], 0, "Isothermal heat in and out at the extreme temperatures, with a perfect regenerator: Carnot."),
      q("Heat in per kg?", ["q<sub>in</sub> = RT<sub>H</sub> ln(v<sub>max</sub>/v<sub>min</sub>)", "c<sub>v</sub>(T<sub>H</sub> − T<sub>L</sub>)", "c<sub>p</sub>(T<sub>H</sub> − T<sub>L</sub>)", "Zero"], 0, "Isothermal ideal gas: q = w = RT ln(v ratio).")],
     trap="Counting the regenerator's heat as heat from the fuel.", tricky=True)

# ======================================================================= Ch. 10
card("S1001", 10, "A simple ideal Rankine cycle: boiler at 8 MPa, condenser at 10 kPa.",
     [sysq(3, "The water returns to its starting state, but analyze each device as a steady-flow control volume."),
      q("Match each device to what stays constant:", ["Pump and turbine: s; boiler and condenser: P", "Pump and turbine: P; boiler and condenser: s", "All four: P", "All four: T"], 0, "Ideal pump and turbine are isentropic; heat exchangers run at constant pressure."),
      q("Before you can find h<sub>2</sub> (pump exit), you need…", ["h<sub>1</sub> = h<sub>f</sub> and v<sub>1</sub> = v<sub>f</sub> at 10 kPa, then w<sub>p</sub> = v<sub>1</sub>(P<sub>2</sub> − P<sub>1</sub>)", "T<sub>2</sub>", "s<sub>2</sub> in A-6", "The turbine work"], 0, "State 1 is saturated liquid at the condenser pressure.")],
     src="Class setup sprint")
card("S1002", 10, "In the same cycle, steam leaves the turbine at 10 kPa.",
     [q("Which number tells you whether the blades are in trouble?", ["The quality x<sub>4</sub> from s<sub>4</sub> = s<sub>3</sub>", "T<sub>4</sub>", "P<sub>4</sub>", "h<sub>g</sub>"], 0, "Below about 0.90 the droplets erode the last-stage blades."),
      q("How do you get it?", ["x<sub>4</sub> = (s<sub>3</sub> − s<sub>f</sub>)/s<sub>fg</sub> at 10 kPa", "x<sub>4</sub> = (h<sub>3</sub> − h<sub>f</sub>)/h<sub>fg</sub>", "x<sub>4</sub> = 1", "x<sub>4</sub> = s<sub>3</sub>/s<sub>g</sub>"], 0, "Isentropic: match entropy, and divide by s<sub>fg</sub>.")],
     trap="Matching h instead of s across an ideal turbine.", tricky=True, src="Class setup sprint")
card("S1003", 10, "A reheat Rankine cycle: high-pressure turbine, reheater, low-pressure turbine.",
     [q("How many heat additions?", ["Two: the boiler (2→3) and the reheater (4→5)", "One", "Three", "None"], 0, "q<sub>in</sub> = (h<sub>3</sub> − h<sub>2</sub>) + (h<sub>5</sub> − h<sub>4</sub>)."),
      q("Where does the LP turbine start?", ["At state 5, after reheating: s<sub>6</sub> = s<sub>5</sub>", "At state 3", "At state 4", "At the condenser"], 0, "Using s<sub>3</sub> for the LP turbine erases the reheat.")],
     trap="Leaving the reheater out of q<sub>in</sub>.", tricky=True, src="Class setup sprint")
card("S1004", 10, "An open feedwater heater: bled steam (fraction y) mixes with feedwater and leaves as saturated liquid at the heater pressure.",
     [q("Energy balance per kg leaving:", ["yh<sub>6</sub> + (1 − y)h<sub>2</sub> = h<sub>3</sub>", "y(h<sub>6</sub> − h<sub>7</sub>) = h<sub>3</sub> − h<sub>2</sub>", "h<sub>6</sub> = h<sub>3</sub>", "y = 0.5"], 0, "Open means mixing. The closed-heater form keeps the streams apart."),
      q("h<sub>3</sub> (heater exit)?", ["h<sub>f</sub> at the heater pressure", "h<sub>f</sub> at the boiler pressure", "h<sub>g</sub>", "h<sub>6</sub>"], 0, "It leaves as saturated liquid at the heater pressure."),
      q("How many pumps?", ["Two: condenser to heater, and heater to boiler", "One", "None", "Three"], 0, "Mixing needs equal pressures, so a pump on each side.")], src="Class setup sprint")
card("S1005", 10, "A cogeneration plant makes electricity and sends steam to a process heater.",
     [q("What goes in the numerator of the utilization factor?", ["Ẇ<sub>net</sub> + Q̇<sub>process</sub>", "Ẇ<sub>net</sub> only", "Q̇<sub>process</sub> only", "Q̇<sub>in</sub>"], 0, "Both products count."),
      q("The utilization factor can be…", ["Much higher than the thermal efficiency, up to 100%", "Never above Carnot", "Always equal to η<sub>th</sub>", "Negative"], 0, "Process heat isn't limited by Carnot.")], src="Class setup sprint")
card("S1006", 10, "A combined cycle: gas-turbine exhaust heats steam in a heat-recovery steam generator (HRSG). Find the steam flow.",
     [q("Which boundary makes the link easiest?", ["Around the whole HRSG: its heat is internal", "Around the gas turbine", "Around the steam turbine", "Around the condenser"], 0, "One insulated heat exchanger, two streams."),
      q("Working equation", ["ṁ<sub>gas</sub>(h<sub>in</sub> − h<sub>out</sub>)<sub>gas</sub> = ṁ<sub>steam</sub>(h<sub>out</sub> − h<sub>in</sub>)<sub>steam</sub>", "ṁ<sub>gas</sub> = ṁ<sub>steam</sub>", "Ẇ<sub>gas</sub> = Ẇ<sub>steam</sub>", "Q̇<sub>HRSG</sub> = Ẇ<sub>net</sub>"], 0, "Energy given up by the gas goes into the water."),
      q("Property models?", ["Gas: ideal gas (c<sub>p</sub> or A-17); water: steam tables", "Both ideal gas", "Both steam tables", "Gas: steam tables"], 0, "Never ideal gas for the steam.")], src="Class setup sprint")
card("S1007", 10, "A closed feedwater heater: bled steam condenses on tubes and leaves as saturated liquid, which is trapped back to the condenser. Feedwater passes through the tubes.",
     [q("Energy balance (per kg through the boiler):", ["y(h<sub>bleed</sub> − h<sub>drain</sub>) = h<sub>fw,out</sub> − h<sub>fw,in</sub>", "yh<sub>bleed</sub> + (1 − y)h<sub>fw,in</sub> = h<sub>fw,out</sub>", "h<sub>bleed</sub> = h<sub>fw,out</sub>", "y = 0"], 0, "No mixing: two streams, one heat exchanger."),
      q("The trap to the condenser is modeled as…", ["A throttle: h<sub>out</sub> = h<sub>in</sub>", "A pump", "Isentropic", "A turbine"], 0, "A steam trap is a throttling valve.")],
     trap="Writing the open (mixing) heater balance for a closed heater.", tricky=True)

def check():
    ids = [c["id"] for c in CARDS]; assert len(ids) == len(set(ids))
    for c in CARDS:
        for qq in c["qs"]:
            n = len(qq["o"])
            if qq["m"]: assert qq["a"] and all(0 <= i < n for i in qq["a"]), (c["id"], qq["q"])
            else: assert isinstance(qq["a"], int) and 0 <= qq["a"] < n, (c["id"], qq["q"])
            assert qq["w"], c["id"]
        if c["tr"]: assert c["trap"], c["id"]

if __name__ == "__main__":
    check()
    json.dump(CARDS, open(os.path.join(HERE, "setup_bank.json"), "w"), ensure_ascii=False)
    from collections import Counter
    print(len(CARDS), "cards;", sum(c["tr"] for c in CARDS), "tricky;", dict(Counter(c["ch"] for c in CARDS)))
