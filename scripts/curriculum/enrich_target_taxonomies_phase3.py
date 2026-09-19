"""
Phase 3: Systematic Declarative Taxonomy Enrichment across 8 target courses.

Updates the declarative JSON taxonomy definitions:
  - course_13_spcm.json
  - course_14_eee.json
  - course_15_eng.json
  - course_16_acca.json
  - course_17_oodp.json
  - course_18_espcb.json
  - course_05_pps.json
  - course_01_calculus.json

Preserves existing taxonomy structure, exact IDs, units, and canonical names.
Adds specific, authoritative phrases matching real unmapped question stems and
negative guardrails to eliminate ambiguous collisions.
"""

import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEF_DIR = os.path.join(BASE_DIR, "backend", "services", "taxonomy_registry", "definitions")


def update_json_file(filename: str, updates: dict):
    path = os.path.join(DEF_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for unit in data["units"]:
        for topic in unit["topics"]:
            tid = topic["id"]
            if tid in updates:
                up = updates[tid]
                # Merge strong phrases
                existing_strong = topic.setdefault("strong_phrases", [])
                for p in up.get("strong_phrases", []):
                    if p not in existing_strong:
                        existing_strong.append(p)
                # Merge specific keywords
                existing_spec = topic.setdefault("specific_keywords", [])
                for k in up.get("specific_keywords", []):
                    if k not in existing_spec:
                        existing_spec.append(k)
                # Merge negative guards
                existing_guards = topic.setdefault("negative_guards", [])
                for g in up.get("negative_guards", []):
                    if g not in existing_guards:
                        existing_guards.append(g)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Updated {filename} successfully.")


def enrich_spcm():
    # Course 13: Topics 73..99
    updates = {
        73: {
            "strong_phrases": [
                "assumptions of classical free electron theory", "merits and demerits of classical free electron",
                "postulates of classical free electron theory", "classical free electron theory of metals",
                "classical free electron theory write any two merits"
            ],
            "specific_keywords": ["classical free electron theory", "drude-lorentz theory"]
        },
        74: {
            "strong_phrases": [
                "the fermi level is", "fermi level for potassium", "velocity of the electron at the fermi",
                "density of states for a semiconductor", "expression for density of states for a metal",
                "density of states for a free electron", "sommerfeld quantum free electron",
                "derive an expression for density of states for a 3d", "derive an expression for density of states for a metal"
            ],
            "specific_keywords": ["sommerfeld model", "fermi-dirac distribution", "density of states in 3d"]
        },
        75: {
            "strong_phrases": [
                "behaviour of electron in a periodic potential", "kroing penny model",
                "kronig penney model origin of band gaps", "origin of energy bands in solids",
                "movement of electron in a periodic potential", "electron in a periodic potential and hence"
            ],
            "specific_keywords": ["kroing penny", "kronig-penney", "periodic potential"]
        },
        76: {
            "strong_phrases": [
                "differentiate direct band gap and indirect band gap",
                "differentiate neatly direct band gap and indirect band gap",
                "direct band gap and indirect band gap semiconductor",
                "e-k diagram and band gaps"
            ],
            "specific_keywords": ["direct and indirect band gap", "direct bandgap", "indirect bandgap"]
        },
        77: {
            "strong_phrases": [
                "uses primitive cell approach to compute electronic band",
                "primitive cell approach to compute electronic band structure",
                "fermi surface of copper", "fermi surface of noble metals"
            ],
            "specific_keywords": ["primitive cell approach", "fermi surface", "tight-binding method"]
        },
        78: {
            "strong_phrases": [
                "intrinsic carrier concentration derivation", "variation of fermi level in intrinsic",
                "law of mass action in intrinsic semiconductor"
            ],
            "negative_guards": ["extrinsic", "n-type", "p-type", "doping", "donor", "acceptor"]
        },
        79: {
            "strong_phrases": [
                "fermi level in a n-type semi conductor", "fermi level in an n-type semiconductor",
                "variation of fermi level with carrier concentration and temperature in n-type",
                "variation of fermi level in n-type", "variation of fermi level in p-type"
            ],
            "negative_guards": [
                "hall effect", "hall coefficient", "four-point probe", "two-point probe",
                "hot-point probe", "four point probe", "two point probe", "optical absorption",
                "led", "light emitting diode", "solar cell"
            ]
        },
        80: {
            "strong_phrases": [
                "carrier generation and recombination rate", "electron hole pair generation",
                "continuity equation for electrons and holes", "carrier lifetime and recombination"
            ],
            "specific_keywords": ["continuity equation", "electron-hole pair recombination"]
        },
        81: {
            "strong_phrases": [
                "drift and diffusion currents in semiconductor", "einstein relation between mobility and diffusivity",
                "carrier mobility and drift velocity", "drift current density and diffusion current density"
            ],
            "specific_keywords": ["drift and diffusion", "einstein relation"]
        },
        82: {
            "strong_phrases": [
                "p-n junction under forward and reverse bias", "built-in potential of p-n junction",
                "depletion width and junction capacitance of pn junction"
            ],
            "negative_guards": ["led", "solar cell", "photodiode"]
        },
        84: {
            "strong_phrases": [
                "principle construction and working of led", "working of led with merits and demerits",
                "explain the principle construction and working of led", "light emitting diode with merits and demerits",
                "emission of light from led", "organic light emitting diode oled"
            ],
            "specific_keywords": ["light emitting diode", "oled", "working of led"]
        },
        85: {
            "strong_phrases": [
                "optical absorption in semiconductors", "direct and indirect optical transitions",
                "absorption coefficient as a function of photon energy", "interband optical transitions"
            ],
            "specific_keywords": ["optical absorption", "absorption coefficient"]
        },
        86: {
            "strong_phrases": [
                "spontaneous and stimulated emission of radiation", "einstein coefficients a and b relation",
                "radiative and non-radiative recombination processes"
            ],
            "specific_keywords": ["spontaneous emission", "einstein coefficients"]
        },
        87: {
            "strong_phrases": [
                "optical transition rate due to electron-photon interaction",
                "derive an expression for optical transition rate",
                "optical transition rate using fermi golden rule",
                "joint density of states derivation", "optical joint density of states"
            ],
            "specific_keywords": ["optical transition rate", "joint density of states", "fermi's golden rule"]
        },
        89: {
            "strong_phrases": [
                "open circuit voltage and short circuit current of solar cell",
                "fill factor and efficiency of a solar cell",
                "i-v characteristics of solar cell", "working principle of photovoltaic solar cell"
            ],
            "specific_keywords": ["solar cell", "photovoltaic cell", "fill factor"]
        },
        90: {
            "strong_phrases": [
                "explain the four-point probe technique-linear method", "four-point probe technique-linear method",
                "four point collinear probe method", "discuss the four point collinear probe method",
                "four-point probe method for resistivity measurement", "two-point and four-point probe methods"
            ],
            "specific_keywords": ["four-point probe", "four point collinear", "collinear probe", "linear four probe"]
        },
        91: {
            "strong_phrases": [
                "explain the hall effect with necessary diagram", "hall effect with necessary diagram",
                "derive the expression for hall coefficient", "derive the expression for hall coefficient of an n-type",
                "determine hall coefficient and carrier concentration", "hall coefficient derivation"
            ],
            "specific_keywords": ["hall effect", "hall coefficient", "hall voltage"]
        },
        92: {
            "strong_phrases": [
                "determining quickly whether a semiconductor sample is n type",
                "hot point probe method to determine type of semiconductor",
                "hot-point probe method", "capacitance voltage cv measurement of semiconductor"
            ],
            "specific_keywords": ["hot-point probe", "hot point probe"]
        },
        95: {
            "strong_phrases": [
                "nanostructures have sizes in between", "density of states in 2d 1d and 0d nanostructures",
                "quantum well quantum wire and quantum dot density of states",
                "density of states in low dimensional systems"
            ],
            "specific_keywords": ["quantum well", "quantum wire", "quantum dot", "low-dimensional systems"]
        },
        96: {
            "strong_phrases": [
                "carbon nanotubes structure and properties", "single walled and multi walled carbon nanotubes",
                "applications of carbon nanotubes cnt", "armchair zigzag and chiral carbon nanotubes"
            ],
            "specific_keywords": ["carbon nanotube", "carbon nanotubes", "swcnt", "mwcnt"],
            "negative_guards": ["chemical vapour deposition method", "physical vapour deposition method"]
        },
        97: {
            "strong_phrases": [
                "with neat sketch explain the synthesis of material by chemical vapour deposition",
                "explain the working concept of physical vapour deposition method (pvd)",
                "synthesis of material by chemical vapour deposition method",
                "in chemical vapour deposition the precessors are introduced",
                "chemical vapour deposition method (cvd)", "physical vapour deposition method (pvd)"
            ],
            "specific_keywords": ["chemical vapour deposition", "physical vapour deposition", "cvd method", "pvd method"]
        },
        98: {
            "strong_phrases": [
                "working principle of scanning electron microscope sem",
                "transmission electron microscopy tem working principle",
                "atomic force microscopy afm principle and instrumentation"
            ],
            "specific_keywords": ["scanning electron microscopy", "transmission electron microscopy", "atomic force microscopy"]
        }
    }
    update_json_file("course_13_spcm.json", updates)


def enrich_eee():
    # Course 14: Topics 280..314
    updates = {
        280: {
            "strong_phrases": [
                "using mesh analysis find the current", "using mesh analysis find current",
                "using nodal analysis find the voltage", "thevenin's equivalent circuit across terminals",
                "norton's theorem across terminals", "maximum power transfer theorem find the maximum power consumed",
                "maximum power transfer theorem find the value of rl", "find current through omega resistor using"
            ],
            "specific_keywords": ["mesh analysis", "nodal analysis", "thevenin's theorem", "norton's theorem", "maximum power transfer"]
        },
        282: {
            "strong_phrases": [
                "current power factor and active power", "find the current power factor",
                "impedance power factor and power consumed", "series rlc circuit resonance condition",
                "power factor of an ac circuit"
            ],
            "specific_keywords": ["power factor", "rlc series", "resonant frequency"]
        },
        283: {
            "strong_phrases": [
                "relation between line and phase quantities in star and delta",
                "three phase star connected balanced load", "three phase delta connected balanced load",
                "two wattmeter method to measure three phase power"
            ],
            "specific_keywords": ["star and delta", "two wattmeter method", "three phase power"]
        },
        285: {
            "strong_phrases": [
                "construction and working principle of single phase transformer",
                "emf equation of a single phase transformer", "losses and efficiency of a single phase transformer",
                "equivalent circuit of single phase transformer", "open circuit and short circuit test of transformer"
            ],
            "specific_keywords": ["single phase transformer", "emf equation of transformer", "transformer losses"]
        },
        287: {
            "strong_phrases": [
                "construction and working principle of dc motor", "back emf and torque equation of a dc motor",
                "characteristics of dc shunt and series motors", "speed control of dc shunt motor"
            ],
            "specific_keywords": ["dc motor", "back emf", "torque equation of dc motor"]
        },
        289: {
            "strong_phrases": [
                "construction and working principle of three phase induction motor",
                "slip ring and squirrel cage induction motor", "torque slip characteristics of induction motor",
                "starting methods of three phase induction motor"
            ],
            "specific_keywords": ["three phase induction motor", "squirrel cage", "slip ring induction"]
        },
        291: {
            "strong_phrases": [
                "output of a logic gate is 1 when all its input is at logic 0",
                "simplify the following boolean expression using k map",
                "simplify the following boolean expression", "de morgan's laws verification using logic gates",
                "universal logic gates nand and nor"
            ],
            "specific_keywords": ["logic gate", "boolean expression", "karnaugh map", "universal gates"]
        },
        293: {
            "strong_phrases": [
                "ideal characteristics of operational amplifier op-amp",
                "inverting and non-inverting operational amplifier",
                "op-amp as summing amplifier and difference amplifier",
                "op-amp as integrator and differentiator"
            ],
            "specific_keywords": ["operational amplifier", "inverting amplifier", "non-inverting amplifier", "op-amp"]
        },
        296: {
            "strong_phrases": [
                "chopper is a device that converts fixed dc to variable dc",
                "step up and step down chopper operation", "principle of operation of dc chopper",
                "buck and boost converters in power electronics"
            ],
            "specific_keywords": ["dc chopper", "step-up chopper", "buck converter"]
        },
        300: {
            "strong_phrases": [
                "construction and working of permanent magnet moving coil (pmmc)",
                "moving iron attraction and repulsion type instruments",
                "dynamometer type wattmeter construction and working",
                "extension of range of ammeter and voltmeter"
            ],
            "specific_keywords": ["pmmc instrument", "moving iron instrument", "wattmeter"]
        },
        314: {
            "strong_phrases": [
                "conversion of solar radiation into electrical energy",
                "solar photovoltaic pv system components and working",
                "grid connected and standalone solar pv systems",
                "wind energy conversion system block diagram and working"
            ],
            "specific_keywords": ["solar radiation into", "solar photovoltaic", "wind energy conversion"]
        }
    }
    update_json_file("course_14_eee.json", updates)


def enrich_eng():
    # Course 15: Topics 464..488
    updates = {
        464: {
            "strong_phrases": [
                "decoding process in communication", "encoding and decoding in the communication process",
                "communication process sender message channel receiver feedback",
                "linear and transactional models of communication", "flow of communication in an organization"
            ],
            "specific_keywords": ["decoding process", "encoding process", "models of communication"]
        },
        465: {
            "strong_phrases": [
                "unclarified assumptions in communication", "physical psychological and semantic barriers to communication",
                "cross-cultural barriers to effective communication", "overcoming barriers to effective communication",
                "noise and filters in the communication process"
            ],
            "specific_keywords": ["barriers to communication", "unclarified assumptions", "semantic barriers"]
        },
        467: {
            "strong_phrases": [
                "read the following passage and draw the flow chart", "read the passage and answer the questions",
                "skimming and scanning reading techniques", "note-taking methods cornell and outline"
            ],
            "specific_keywords": ["reading comprehension", "skimming and scanning", "note-taking"]
        },
        469: {
            "strong_phrases": [
                "fill in the blanks with appropriate tense form of the verb", "subject verb agreement in sentences",
                "reported speech conversion direct to indirect", "active to passive voice conversion",
                "she said that she had", "he asked whether"
            ],
            "specific_keywords": ["subject-verb agreement", "reported speech", "active and passive voice"]
        },
        475: {
            "strong_phrases": [
                "write an essay of about 200 words on the impact of social media",
                "write an essay of about 200 words on artificial intelligence",
                "write an essay of about 200 words on online education",
                "write an essay of about 200 words on topics given below",
                "write an essay of about 200 words", "topic sentence and paragraph coherence",
                "précis writing with a suitable title"
            ],
            "specific_keywords": ["write an essay of about 200 words", "précis writing", "paragraph development"]
        },
        476: {
            "strong_phrases": [
                "write a letter to the municipal commissioner complaining about",
                "letter of inquiry regarding product specifications",
                "formal letter seeking permission for industrial visit",
                "format of formal business letters"
            ],
            "specific_keywords": ["formal letter", "letter of complaint", "letter of inquiry"]
        },
        477: {
            "strong_phrases": [
                "draft an email to the editor of the hindu", "draft an email to the editor",
                "email etiquette in professional correspondence", "netiquette rules in the digital age",
                "subject line and tone in professional email"
            ],
            "specific_keywords": ["draft an email", "email etiquette", "netiquette"]
        },
        478: {
            "strong_phrases": [
                "prepare a resume and covering letter for the post of software engineer",
                "curriculum vitae cv format and components", "job application letter with resume"
            ],
            "specific_keywords": ["resume and covering letter", "curriculum vitae", "job application letter"]
        },
        480: {
            "strong_phrases": [
                "write a report on the industrial visit to", "assume that you are the director of student affairs",
                "technical report writing structure and format", "investigation report on lab safety"
            ],
            "specific_keywords": ["technical report writing", "report on industrial visit", "progress report"]
        },
        482: {
            "strong_phrases": [
                "transcode the information given in the bar graph into a paragraph",
                "write a passage presenting the information contained in the bar graph",
                "convert the pie chart into text description", "information transfer from charts to text"
            ],
            "specific_keywords": ["information transfer", "transcoding", "bar graph into text"]
        }
    }
    update_json_file("course_15_eng.json", updates)


def enrich_acca():
    # Course 16: Topics 315..338
    updates = {
        315: {
            "strong_phrases": [
                "evaluate the double integral over the region", "double integral dxdy region bounded",
                "evaluation of double integral int int", "double integral over the rectangular region"
            ],
            "specific_keywords": ["double integral dxdy", "double integral over the region"]
        },
        316: {
            "strong_phrases": [
                "change the order of integration and evaluate", "by changing the order of integration evaluate",
                "change the order of integration in the double integral"
            ],
            "specific_keywords": ["change the order of integration", "changing the order of integration"]
        },
        317: {
            "strong_phrases": [
                "evaluate the triple integral dxdydz", "triple integral over the sphere",
                "volume of the tetrahedron using triple integration"
            ],
            "specific_keywords": ["triple integral dxdydz", "triple integration"]
        },
        318: {
            "strong_phrases": [
                "find the area of the ellipse using double integration", "area of the cardioid using double integrals",
                "volume under the paraboloid using double integrals"
            ],
            "specific_keywords": ["area of the ellipse", "area using double integration"]
        },
        319: {
            "strong_phrases": [
                "directional derivative of phi at the point", "unit normal vector to the surface at",
                "maximum directional derivative of scalar potential", "gradient of scalar function phi"
            ],
            "specific_keywords": ["directional derivative", "unit normal vector", "gradient of phi"]
        },
        320: {
            "strong_phrases": [
                "divergence of position vector r", "curl of vector field is zero show that",
                "prove that the vector field is solenoidal", "vector field is irrotational find potential",
                "divergence and curl of vector field"
            ],
            "specific_keywords": ["solenoidal vector", "irrotational vector", "divergence of vec", "curl of vec"]
        },
        321: {
            "strong_phrases": [
                "verify green's theorem in a plane for", "evaluate using green's theorem in a plane",
                "apply green's theorem to evaluate line integral"
            ],
            "specific_keywords": ["green's theorem in a plane", "green's theorem"]
        },
        322: {
            "strong_phrases": [
                "verify stokes' theorem for the vector field", "evaluate by stokes' theorem around the curve",
                "apply stokes' theorem to evaluate surface integral"
            ],
            "specific_keywords": ["stokes' theorem", "stokes theorem"]
        },
        323: {
            "strong_phrases": [
                "verify gauss divergence theorem for the vector", "evaluate by gauss divergence theorem over the closed",
                "apply divergence theorem to evaluate flux"
            ],
            "specific_keywords": ["gauss divergence theorem", "divergence theorem"]
        },
        324: {
            "strong_phrases": [
                "laplace transform of t^n e^{at}", "find the laplace transform of sin(at)",
                "first shifting theorem of laplace transform", "laplace transform of periodic functions"
            ],
            "specific_keywords": ["laplace transform of", "shifting theorem"]
        },
        326: {
            "strong_phrases": [
                "find the inverse laplace transform using partial fractions",
                "inverse laplace transform of s/((s^2+a^2)^2)", "inverse laplace transform of logarithmic"
            ],
            "specific_keywords": ["inverse laplace transform", "inverse laplace"]
        },
        327: {
            "strong_phrases": [
                "using convolution theorem find the inverse laplace", "apply convolution theorem to evaluate",
                "convolution theorem for inverse laplace transform"
            ],
            "specific_keywords": ["convolution theorem for laplace", "convolution theorem"]
        },
        329: {
            "strong_phrases": [
                "cauchy-riemann equations in cartesian and polar", "show that the function is analytic using cr",
                "cauchy riemann equations satisfaction", "analytic function f(z) = u + iv"
            ],
            "specific_keywords": ["cauchy-riemann equations", "cr equations", "analytic function"]
        },
        330: {
            "strong_phrases": [
                "show that u is harmonic and find its harmonic conjugate", "find the harmonic conjugate v(x,y)",
                "orthogonal trajectories of family of curves"
            ],
            "specific_keywords": ["harmonic conjugate", "harmonic function", "orthogonal trajectories"]
        },
        331: {
            "strong_phrases": [
                "construct an analytic function f(z) using milne-thomson method",
                "by milne-thomson method find f(z)", "milne thomson method"
            ],
            "specific_keywords": ["milne-thomson method", "milne thomson"]
        },
        332: {
            "strong_phrases": [
                "find the image of the circle under the transformation w = 1/z",
                "conformal transformation w = z^2", "magnification and rotation in conformal mapping"
            ],
            "specific_keywords": ["conformal transformation", "conformal mapping"]
        },
        333: {
            "strong_phrases": [
                "find the bilinear transformation which maps the points",
                "bilinear transformation cross ratio invariant property", "mobius transformation mapping"
            ],
            "specific_keywords": ["bilinear transformation", "cross ratio", "mobius transformation"]
        },
        334: {
            "strong_phrases": [
                "evaluate the integral using cauchy's integral formula", "by cauchy's integral formula evaluate",
                "cauchy integral theorem for closed contour"
            ],
            "specific_keywords": ["cauchy's integral formula", "cauchy's integral theorem"]
        },
        336: {
            "strong_phrases": [
                "find the residues at the poles of f(z)", "residue of function at simple and multiple poles",
                "isolated essential singularity and pole"
            ],
            "specific_keywords": ["residue at the pole", "residues at the poles", "singularities and poles"]
        },
        337: {
            "strong_phrases": [
                "evaluate using cauchy's residue theorem", "by cauchy residue theorem evaluate the contour integral",
                "apply residue theorem to evaluate integral around unit circle"
            ],
            "specific_keywords": ["cauchy's residue theorem", "cauchy residue theorem"]
        }
    }
    update_json_file("course_16_acca.json", updates)


def enrich_oodp():
    # Course 17: Topics 339..363
    updates = {
        340: {
            "strong_phrases": [
                "data encapsulation and data abstraction in c++", "class and object instantiation in c++",
                "memory allocation for objects of a class"
            ],
            "specific_keywords": ["data encapsulation", "class definition", "object instantiation"]
        },
        341: {
            "strong_phrases": [
                "which access specifier is used by default in a class", "public private and protected member access",
                "member functions inside and outside class definition", "static member variables and static functions"
            ],
            "specific_keywords": ["access specifier", "access specifiers", "member functions"]
        },
        342: {
            "strong_phrases": [
                "draw the class diagram for library management system", "class diagram showing generalization and association",
                "aggregation and composition in uml class diagrams"
            ],
            "specific_keywords": ["class diagram", "uml class diagram", "aggregation and composition"]
        },
        343: {
            "strong_phrases": [
                "draw use case diagram for online examination system", "include and extend relationships in use case diagram",
                "actor and system boundary in use case modeling"
            ],
            "specific_keywords": ["use case diagram", "use case relationships", "include and extend"]
        },
        344: {
            "strong_phrases": [
                "destructor of base class should always be virtual", "order of execution of constructors and destructors",
                "copy constructor and deep copy vs shallow copy", "destructor cannot take arguments"
            ],
            "specific_keywords": ["virtual destructor", "constructors and destructors", "destructor of base class"]
        },
        346: {
            "strong_phrases": [
                "function overloading and constructor overloading", "constructor overloading in c++ with example",
                "overloaded functions with different parameter types"
            ],
            "specific_keywords": ["constructor overloading", "function overloading"]
        },
        347: {
            "strong_phrases": [
                "overload binary plus operator using friend function", "overload stream insertion and extraction operators",
                "operator overloading unary minus operator", "friend function accessing private members of class"
            ],
            "specific_keywords": ["operator overloading", "friend function", "overload binary"]
        },
        348: {
            "strong_phrases": [
                "draw sequence diagram for atm cash withdrawal", "sequence diagram showing lifelines and synchronous messages",
                "collaboration diagram showing objects and numbered links", "uml interaction diagrams sequence and communication"
            ],
            "specific_keywords": ["sequence diagram", "collaboration diagram", "uml interaction diagram"]
        },
        350: {
            "strong_phrases": [
                "virtual base class to avoid diamond problem", "multiple inheritance ambiguity in c++",
                "multilevel and hierarchical inheritance with code example", "modes of inheritance public protected private"
            ],
            "specific_keywords": ["virtual base class", "diamond problem", "multiple inheritance"]
        },
        352: {
            "strong_phrases": [
                "pure virtual function and abstract base class", "runtime polymorphism dynamic binding using virtual functions",
                "vtable and vptr mechanism in c++", "late binding vs early binding"
            ],
            "specific_keywords": ["pure virtual function", "abstract base class", "runtime polymorphism", "vtable"]
        },
        353: {
            "strong_phrases": [
                "draw state chart diagram for order fulfillment process", "state chart diagram states transitions and events",
                "activity diagram showing fork join and swimlanes"
            ],
            "specific_keywords": ["state chart diagram", "activity diagram", "behavioral modeling"]
        },
        354: {
            "strong_phrases": [
                "function template to swap two variables of any type", "generic programming using function templates in c++",
                "function template with multiple parameters"
            ],
            "specific_keywords": ["function template", "generic programming", "template function"]
        },
        356: {
            "strong_phrases": [
                "exception handling mechanism using try throw and catch", "re-throwing an exception in c++",
                "standard exceptions in c++ exception hierarchy", "catching all exceptions using catch block"
            ],
            "specific_keywords": ["try throw catch", "exception handling", "catch block"]
        },
        358: {
            "strong_phrases": [
                "draw deployment diagram for three tier web application", "component diagram showing interfaces and dependencies",
                "package diagram showing subsystems and dependencies"
            ],
            "specific_keywords": ["deployment diagram", "component diagram", "package diagram"]
        },
        360: {
            "strong_phrases": [
                "std::vector sequence container push_back pop_back", "std::list doubly linked list operations in stl",
                "std::deque double ended queue in c++ stl"
            ],
            "specific_keywords": ["std::vector", "sequence container", "std::deque"]
        },
        361: {
            "strong_phrases": [
                "std::map associative container key value pairs", "std::set unique elements in sorted order",
                "container adapters std::stack and std::queue"
            ],
            "specific_keywords": ["std::map", "std::set", "associative container", "container adapters"]
        },
        362: {
            "strong_phrases": [
                "iterators are used to iterate over elements of a container", "forward bidirectional and random access iterators",
                "std::sort std::find stl algorithms", "functors function objects in c++ stl"
            ],
            "specific_keywords": ["stl iterators", "stl algorithms", "iterators are used"]
        }
    }
    update_json_file("course_17_oodp.json", updates)


def enrich_espcb():
    # Course 18: Topics 364..388
    updates = {
        367: {
            "strong_phrases": [
                "operation of npn transistor in active saturation and cutoff",
                "input and output characteristics of common emitter configuration",
                "relation between current gains alpha and beta in bjt",
                "working principle of enhancement and depletion mosfet"
            ],
            "specific_keywords": ["npn transistor", "common emitter", "current gain alpha and beta", "mosfet characteristics"]
        },
        370: {
            "strong_phrases": [
                "working principle and vi characteristics of gunn diode", "gunn effect and transferred electron mechanism",
                "impatt diode working and applications in microwaves", "schottky barrier diode construction and characteristics"
            ],
            "specific_keywords": ["gunn diode", "impatt diode", "schottky diode", "gunn effect"]
        },
        371: {
            "strong_phrases": [
                "two transistor analogy of silicon controlled rectifier scr", "vi characteristics of thyristor scr",
                "latching current and holding current in scr", "turn-on and turn-off methods of scr"
            ],
            "specific_keywords": ["silicon controlled rectifier", "scr characteristics", "latching current", "holding current"]
        },
        374: {
            "strong_phrases": [
                "full wave bridge rectifier with capacitor filter circuit", "ripple factor and efficiency of full wave rectifier",
                "half wave and full wave rectifier working and waveforms", "regulated power supply block diagram and components"
            ],
            "specific_keywords": ["full wave rectifier", "bridge rectifier", "ripple factor", "regulated power supply"]
        },
        375: {
            "strong_phrases": [
                "zener diode shunt voltage regulator circuit and working", "line regulation and load regulation definitions",
                "three terminal fixed voltage regulators ic 7805 7905", "adjustable voltage regulator lm317 working"
            ],
            "specific_keywords": ["zener voltage regulator", "line regulation", "load regulation", "ic 7805"]
        },
        377: {
            "strong_phrases": [
                "astable multivibrator using 555 timer circuit and waveforms", "monostable multivibrator using ic 555 timer",
                "positive and negative clipper and clamper circuits", "schmitt trigger circuit using op-amp"
            ],
            "specific_keywords": ["astable multivibrator", "555 timer", "clipper and clamper", "monostable multivibrator"]
        },
        379: {
            "strong_phrases": [
                "single sided double sided and multilayer printed circuit boards", "manufacturing steps of printed circuit boards (pcb)",
                "etching and electroplating processes in pcb manufacturing", "fr4 material and substrate selection in pcb"
            ],
            "specific_keywords": ["printed circuit board", "printed circuit boards", "pcb manufacturing", "multilayer pcb"]
        },
        380: {
            "strong_phrases": [
                "schematic capture and netlist generation in pcb design", "design rule check (drc) and electrical rule check (erc)",
                "component footprint creation and library management in pcb"
            ],
            "specific_keywords": ["schematic capture", "design rule check", "netlist generation"]
        },
        382: {
            "strong_phrases": [
                "surface mount technology (smt) vs through hole technology (tht)",
                "wave soldering and reflow soldering techniques in pcb", "solder paste application and stencil printing"
            ],
            "specific_keywords": ["surface mount technology", "smt vs tht", "wave soldering", "reflow soldering"]
        },
        386: {
            "strong_phrases": [
                "cross-talk and electromagnetic interference emi in pcb layout",
                "signal integrity issues ground bounce and reflections in pcb",
                "decoupling capacitors and power plane impedance"
            ],
            "specific_keywords": ["signal integrity", "cross-talk in pcb", "electromagnetic interference"]
        }
    }
    update_json_file("course_18_espcb.json", updates)


def enrich_pps():
    # Course 5: Topics 140..159
    updates = {
        140: {
            "strong_phrases": [
                "draw a flowchart to find the largest of three numbers", "algorithm to calculate factorial of a number",
                "flowchart symbols start stop decision process", "steps in problem solving process using computers"
            ],
            "specific_keywords": ["flowchart to find", "algorithm to find", "flowchart symbols"]
        },
        144: {
            "strong_phrases": [
                "check whether a given number is armstrong number or not", "check whether a number is palindrome or not",
                "check whether a given year is leap year or not", "roots of a quadratic equation using if-else",
                "menu driven program using switch case in c", "check whether a number is even or odd"
            ],
            "specific_keywords": ["armstrong number", "leap year", "switch case", "roots of a quadratic"]
        },
        145: {
            "strong_phrases": [
                "program to print fibonacci series up to n terms", "program to print prime numbers between 1 and n",
                "check whether a number is prime or not using loop", "sum of digits of a number using while loop",
                "print the following star pattern using nested loops"
            ],
            "specific_keywords": ["fibonacci series up to", "prime numbers between", "sum of digits of a number"]
        },
        146: {
            "strong_phrases": [
                "program to multiply two matrices in c", "program to find transpose of a matrix",
                "find the largest and smallest element in an array", "addition of two matrices in c",
                "linear search and binary search in an array"
            ],
            "specific_keywords": ["multiply two matrices", "transpose of a matrix", "element in an array"]
        },
        147: {
            "strong_phrases": [
                "swap two numbers using call by reference pointers", "pointer to an array and array of pointers in c",
                "pointer arithmetic and dereferencing in c", "dynamic memory allocation malloc calloc realloc free"
            ],
            "specific_keywords": ["call by reference pointers", "pointer arithmetic", "malloc and calloc"]
        },
        148: {
            "strong_phrases": [
                "string handling functions strlen strcpy strcat strcmp in c", "check whether string is palindrome without using string",
                "count vowels consonants digits and special characters", "concatenate two strings without using strcat"
            ],
            "specific_keywords": ["string handling functions", "strlen strcpy", "palindrome string"]
        },
        150: {
            "strong_phrases": [
                "factorial of a number using recursion in c", "tower of hanoi problem using recursive function",
                "fibonacci series using recursion in c", "gcd of two numbers using recursion"
            ],
            "specific_keywords": ["using recursion in c", "tower of hanoi", "recursive function in c"]
        },
        154: {
            "strong_phrases": [
                "python list tuple set and dictionary differences", "list comprehension in python with examples",
                "python dictionary keys values and items methods", "set operations union intersection in python"
            ],
            "specific_keywords": ["list comprehension", "python dictionary", "tuple set and dictionary"]
        },
        156: {
            "strong_phrases": [
                "create a numpy array using np.array and np.arange", "numpy array indexing slicing and reshaping",
                "two dimensional numpy array operations"
            ],
            "specific_keywords": ["numpy array", "np.arange", "numpy indexing"]
        },
        158: {
            "strong_phrases": [
                "create a pandas dataframe from dictionary in python", "pandas series and dataframe differences",
                "pandas dataframe head tail and describe methods"
            ],
            "specific_keywords": ["pandas dataframe", "pandas series", "dataframe from dictionary"]
        }
    }
    update_json_file("course_05_pps.json", updates)


def enrich_calculus():
    # Course 1: Topics 1..39
    updates = {
        1: {
            "strong_phrases": [
                "find the eigenvalues and eigenvectors of the matrix", "eigen values and eigen vectors of the matrix",
                "find eigenvalues and corresponding eigenvectors"
            ],
            "specific_keywords": ["eigenvalues and eigenvectors", "eigen values and eigen vectors"]
        },
        32: {
            "strong_phrases": [
                "verify cayley-hamilton theorem for the matrix", "using cayley-hamilton theorem find a^{-1}",
                "find a^4 and a^{-1} using cayley hamilton"
            ],
            "specific_keywords": ["cayley-hamilton theorem", "cayley hamilton"]
        },
        33: {
            "strong_phrases": [
                "reduce the quadratic form to canonical form by orthogonal", "nature index and signature of quadratic form",
                "orthogonal transformation of quadratic form"
            ],
            "specific_keywords": ["quadratic form to canonical", "orthogonal reduction"]
        },
        4: {
            "strong_phrases": [
                "solve the exact differential equation", "integrating factor of the differential equation",
                "solve the first order linear differential equation dy/dx", "bernoulli's differential equation solve"
            ],
            "specific_keywords": ["exact differential equation", "integrating factor", "bernoulli's differential"]
        },
        5: {
            "strong_phrases": [
                "solve by method of variation of parameters", "method of variation of parameters solve",
                "solve cauchy's homogeneous linear differential equation", "second order linear differential equation with constant"
            ],
            "specific_keywords": ["variation of parameters", "cauchy's homogeneous", "second order linear differential"]
        },
        11: {
            "strong_phrases": [
                "test the convergence of the series using d'alembert's ratio test",
                "cauchy's root test test convergence of series", "raabe's test for series convergence"
            ],
            "specific_keywords": ["d'alembert's ratio test", "cauchy's root test", "convergence of the series"]
        },
        34: {
            "strong_phrases": [
                "find the maximum and minimum values of f(x,y)", "find the maxima and minima of the function",
                "lagrange's method of undetermined multipliers find extrema", "saddle points of function of two variables"
            ],
            "specific_keywords": ["maxima and minima", "lagrange's method of undetermined", "saddle points"]
        }
    }
    update_json_file("course_01_calculus.json", updates)


def main():
    print("Beginning Phase 3 Declarative Taxonomy Enrichment...")
    enrich_spcm()
    enrich_eee()
    enrich_eng()
    enrich_acca()
    enrich_oodp()
    enrich_espcb()
    enrich_pps()
    enrich_calculus()
    print("All 8 target courses enriched successfully.")


if __name__ == "__main__":
    main()
