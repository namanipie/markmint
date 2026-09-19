"""
Precision enhancements to declarative JSON taxonomy definitions for:
- Course 16: ACCA (21MAB102T)
- Course 17: OODP (21CSC102J)
- Course 18: ESPCB (21ECC101J)
- Course 13: SPCM (21PYB102J)
- Course 14: EEE (21EEB101J)
- Course 15: English (21LEH101T)
"""

import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEF_DIR = os.path.join(BASE_DIR, "backend", "services", "taxonomy_registry", "definitions")


def enhance_acca():
    path = os.path.join(DEF_DIR, "course_16_acca.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for unit in data["units"]:
        for t in unit["topics"]:
            tid = t["id"]
            strong = t.setdefault("strong_phrases", [])
            specific = t.setdefault("specific_keywords", [])

            if tid == 315:  # Double Integrals and Change of Variables
                strong.extend([
                    "evaluation of double integral", "region bounded by x 0 y 0",
                    "double integral limits", "double integral dxdy", "iint limits",
                    "double integral over r"
                ])
                specific.extend(["double integral dxdy", "region bounded by"])
            elif tid == 318:  # Area and Volume as Multiple Integrals
                strong.extend([
                    "area of an ellipse", "area of the ellipse", "area of ellipse is",
                    "area between the curves", "area of cardioid"
                ])
                specific.extend(["area of an ellipse", "area of the ellipse"])
            elif tid == 320:  # Gradient & Directional Derivative
                strong.extend([
                    "unit vector normal to the surface", "unit normal to the surface x^2",
                    "normal to the surface at", "unit normal vector to the surface"
                ])
                specific.extend(["unit vector normal", "unit normal to the surface"])
            elif tid == 321:  # Divergence and Curl
                strong.extend([
                    "divergence vec r", "divergence of position vector", "curl vec f",
                    "nabla cdot vec r", "divergence is zero is called solenoidal",
                    "curl is zero is called irrotational"
                ])
                specific.extend(["divergence vec r", "curl vec f", "nabla cdot"])
            elif tid == 324:  # Laplace Transforms Elementary
                strong.extend([
                    "laplace transforms does not exists", "laplace transform of e^",
                    "laplace transform does not exist", "mathcal l e^",
                    "laplace transform of unit step"
                ])
                specific.extend(["laplace transform does not exist", "mathcal l"])
            elif tid == 329:  # Analytic Functions & CR Equations
                strong.extend([
                    "function f z u+iv is analytic if", "analytic function with constant modulus",
                    "curves u c1 and v c2", "analytic if u_x v_y",
                    "real and imaginary parts of analytic function", "constant modulus is constant"
                ])
                specific.extend(["function f z is analytic", "constant modulus"])
            elif tid == 332:  # Conformal Mapping
                strong.extend([
                    "transformation w cz", "transformation w = cz", "transformation w 1 z",
                    "conformal transformation w", "bilinear transformation maps"
                ])
                specific.extend(["transformation w cz", "transformation w 1 z"])
            elif tid == 335:  # Cauchy's Integral Theorem and Formula
                strong.extend([
                    "f z is analytic inside and on c", "int c f z z-a dz",
                    "cauchy's integral formula evaluate", "value of int c f z"
                ])
                specific.extend(["f z is analytic inside and on c", "int c f z"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Enhanced ACCA")


def enhance_oodp():
    path = os.path.join(DEF_DIR, "course_17_oodp.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for unit in data["units"]:
        for t in unit["topics"]:
            tid = t["id"]
            strong = t.setdefault("strong_phrases", [])
            specific = t.setdefault("specific_keywords", [])

            if tid == 340:  # Classes & Encapsulation
                strong.extend([
                    "access specifiers is used in a class definition by default",
                    "default access specifier in class", "private by default in class",
                    "an operation can be described as object behavior",
                    "data hiding and encapsulation in c++"
                ])
                specific.extend(["default access specifier", "access specifiers is used"])
            elif tid == 342:  # Constructors & Destructors
                strong.extend([
                    "destructor of base class should always be virtual",
                    "destructor of base class", "virtual destructor in base class",
                    "find the o p of the following code class cube",
                    "parameterized constructor in c++", "copy constructor syntax"
                ])
                specific.extend(["destructor of base class", "class cube public int side"])
            elif tid == 344:  # Operator Overloading
                strong.extend([
                    "program using operator overloading for", "operator overloading for class time",
                    "overload binary + operator", "overload stream insertion operator"
                ])
                specific.extend(["operator overloading for", "operator+ overloading"])
            elif tid == 349:  # Packages & Architecture
                strong.extend([
                    "collection of model elements called uml packages",
                    "uml package members", "package diagram in uml"
                ])
                specific.extend(["uml packages", "collection of model elements"])
            elif tid == 351:  # State Machines & Activity
                strong.extend([
                    "reactive system uml diagrams statechart", "model life time of a reactive system",
                    "statechart diagram in uml", "combines two concurrent activities fork join",
                    "activity diagram merge and join"
                ])
                specific.extend(["reactive system uml", "statechart diagrams", "concurrent activities"])
            elif tid == 359:  # Templates
                strong.extend([
                    "syntax for template function", "template class t return type",
                    "template <class t>", "template <typename t>", "template <int i>",
                    "generic programming using template", "template specialization in c++"
                ])
                specific.extend(["syntax for template", "template <class", "template <int", "template function"])
            elif tid == 360:  # Exception Handling
                strong.extend([
                    "try catch throw", "catch all handler catch", "try catch block in c++",
                    "rethrowing an exception", "custom exception in c++", "catch int param"
                ])
                specific.extend(["try throw catch", "catch int param", "catch ..."])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Enhanced OODP")


def enhance_espcb():
    path = os.path.join(DEF_DIR, "course_18_espcb.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for unit in data["units"]:
        for t in unit["topics"]:
            tid = t["id"]
            strong = t.setdefault("strong_phrases", [])
            specific = t.setdefault("specific_keywords", [])

            if tid == 364:  # Classification of Semiconductors and Doping
                strong.extend([
                    "doped with donor impurities", "intrinsic carrier concentration of silicon",
                    "donor impurity concentration", "acceptor impurity concentration"
                ])
                specific.extend(["doped with donor", "intrinsic carrier concentration"])
            elif tid == 365:  # Energy Bands & Fermi Level
                strong.extend([
                    "define fermi energy and fermi energy level", "fermi energy level position",
                    "fermi level for intrinsic p-type and n-type", "forbidden energy gap of silicon",
                    "forbidden energy gap of germanium", "energy band diagram of semiconductor"
                ])
                specific.extend(["fermi energy level position", "forbidden energy gap of silicon"])
            elif tid == 367:  # JFET & MOSFET
                strong.extend([
                    "construction of n channel e-mosfet", "e-mosfet operation and applications",
                    "drain characteristics of jfet", "gate oxide isolates gate terminal",
                    "fin structure double gate effective width"
                ])
                specific.extend(["n channel e-mosfet", "e-mosfet", "gate oxide isolates"])
            elif tid == 368:  # BJT
                strong.extend([
                    "difference between npn and pnp transistor", "npn and pnp transistor",
                    "eb junction and cb junction reverse biased", "transistor in active cut-off saturation",
                    "current gain alpha and beta of bjt"
                ])
                specific.extend(["difference between npn and pnp", "npn and pnp transistor"])
            elif tid == 371:  # Thyristor & SCR
                strong.extend([
                    "turn on the scr we need to provide gate current", "latching current and holding current",
                    "minimum current required to trigger the device from off to on",
                    "vi characteristics of scr", "two transistor analogy of scr"
                ])
                specific.extend(["turn on the scr", "latching current and holding", "trigger the device from off to on"])
            elif tid == 372:  # Power BJT & MOSFET
                strong.extend([
                    "salient features of power transistor", "power bjt switching characteristics",
                    "safe operating area of power transistor", "switching losses in power mosfet"
                ])
                specific.extend(["salient features of power transistor", "power bjt switching"])
            elif tid == 376:  # SMPS
                strong.extend([
                    "main switching element in a switched-mode power supply",
                    "switched mode power supply operating in 20 khz",
                    "block diagram of smps", "advantages of smps over linear power supply"
                ])
                specific.extend(["switched-mode power supply", "switched mode power supply operating"])
            elif tid == 378:  # Electronic Measurement
                strong.extend([
                    "purpose of electron gun in cro", "electron gun in cro is to produce electron beam",
                    "cathode ray oscilloscope time base generator", "deflection sensitivity of cro"
                ])
                specific.extend(["electron gun in cro", "cathode ray oscilloscope cro"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Enhanced ESPCB")


def enhance_spcm():
    path = os.path.join(DEF_DIR, "course_13_spcm.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for unit in data["units"]:
        for t in unit["topics"]:
            tid = t["id"]
            strong = t.setdefault("strong_phrases", [])
            specific = t.setdefault("specific_keywords", [])

            if tid == 261:  # Band Theory & Kronig-Penney
                strong.extend([
                    "behaviour of electron in a periodic potential", "kroing penny model",
                    "kronig-penney model in detail", "bloch theorem electron in periodic"
                ])
                specific.extend(["electron in a periodic potential", "kroing penny", "kronig-penney"])
            elif tid == 262:  # Brillouin Zones & Band Gaps
                strong.extend([
                    "differentiate direct band gap and indirect band gap",
                    "direct band gap and indirect band gap semiconductor",
                    "e-k diagram and band gaps"
                ])
                specific.extend(["direct band gap and indirect", "direct and indirect band gap"])
            elif tid == 263:  # Density of States
                strong.extend([
                    "derive an expression for density of states for a semiconductor",
                    "density of states in 3d conduction band", "density of states derivation"
                ])
                specific.extend(["density of states for a semiconductor", "derive an expression for density of states"])
            elif tid == 264:  # Fermi Level
                strong.extend([
                    "fermi level is an average value", "velocity of the electron at the fermi level",
                    "fermi level for potassium", "fermi energy and work function"
                ])
                specific.extend(["velocity of the electron at the fermi", "fermi level for potassium"])
            elif tid == 268:  # Carrier Generation & Recombination
                strong.extend([
                    "process directly involves absorption and emission of photons",
                    "optical absorption and emission of photons",
                    "carrier lifetime and continuity equation"
                ])
                specific.extend(["absorption and emission of photons", "carrier generation and recombination"])
            elif tid == 269:  # Joint Density of States
                strong.extend([
                    "optical transition rate due to electron-photon interaction",
                    "fermi's golden rule for transition rate", "fermi golden rule transition"
                ])
                specific.extend(["optical transition rate", "fermi's golden rule", "electron-photon interaction"])
            elif tid == 272:  # Hall Effect & Four Point Probe
                strong.extend([
                    "four-point probe technique", "four point probe technique-linear method",
                    "hall coefficient and carrier concentration", "measurement of resistivity four point probe"
                ])
                specific.extend(["four-point probe", "four point probe technique", "hall effect measurement"])
            elif tid == 273:  # LED & Photodetectors
                strong.extend([
                    "principle construction and working of led", "working of led with merits and demerits",
                    "light emitting diode led working", "photodetector responsivity and quantum efficiency"
                ])
                specific.extend(["working of led with merits", "construction and working of led"])
            elif tid == 277:  # CVD & PVD
                strong.extend([
                    "chemical vapour deposition method", "chemical vapor deposition cvd",
                    "synthesis of material by chemical vapour deposition", "physical vapor deposition pvd sputtering"
                ])
                specific.extend(["chemical vapour deposition method", "synthesis of material by chemical"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Enhanced SPCM")


def enhance_eee():
    path = os.path.join(DEF_DIR, "course_14_eee.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for unit in data["units"]:
        for t in unit["topics"]:
            tid = t["id"]
            strong = t.setdefault("strong_phrases", [])
            specific = t.setdefault("specific_keywords", [])

            if tid == 280:  # Network Theorems
                strong.extend([
                    "maximum power transfer theorem find the maximum power consumed",
                    "thevenin's equivalent circuit across terminals",
                    "norton's theorem find short circuit current",
                    "superposition theorem find current flowing"
                ])
                specific.extend(["maximum power transfer theorem find", "thevenin s equivalent"])
            elif tid == 291:  # Digital Logic & Boolean Algebra
                strong.extend([
                    "output of a logic gate is 1 when all its input is at logic 0",
                    "simplify the following boolean expression y a b c",
                    "de morgan's laws verification", "universal gates nand and nor"
                ])
                specific.extend(["output of a logic gate is", "boolean expression y a b c"])
            elif tid == 296:  # Power Devices & Choppers
                strong.extend([
                    "chopper is a device that converts", "chopper converts fixed dc to variable dc",
                    "vi characteristics of scr in eee", "scr forward blocking mode"
                ])
                specific.extend(["chopper is a device that converts", "chopper converts"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Enhanced EEE")


def enhance_eng():
    path = os.path.join(DEF_DIR, "course_15_eng.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for unit in data["units"]:
        for t in unit["topics"]:
            tid = t["id"]
            strong = t.setdefault("strong_phrases", [])
            specific = t.setdefault("specific_keywords", [])

            if tid == 299:  # Intro to Communication & Barriers
                strong.extend([
                    "unclarified assumptions in a communication can lead to",
                    "barriers to communication physical and psychological",
                    "horizontal communication and grapevine", "process of communication sender receiver"
                ])
                specific.extend(["unclarified assumptions in a communication", "barriers to communication"])
            elif tid == 300:  # Grammar in Context
                strong.extend([
                    "fill in the blanks with appropriate verb forms", "subject verb agreement error",
                    "active and passive voice conversion", "prepositions and concord"
                ])
                specific.extend(["fill in the blanks with appropriate verb", "subject verb agreement"])
            elif tid == 304:  # Email & Digital Media
                strong.extend([
                    "send a mail to your team appreciating the successful", "email etiquette in professional",
                    "role of online communication in post-truth world", "cyber bullying in social media and its impacts"
                ])
                specific.extend(["send a mail to your team", "role of online communication"])
            elif tid == 308:  # Essay Writing
                strong.extend([
                    "write an essay of about 200 words on topics given below",
                    "essay on the impact of social media", "argumentative essay structure"
                ])
                specific.extend(["write an essay of about 200 words", "impact of social media on"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Enhanced English")


if __name__ == "__main__":
    enhance_acca()
    enhance_oodp()
    enhance_espcb()
    enhance_spcm()
    enhance_eee()
    enhance_eng()
