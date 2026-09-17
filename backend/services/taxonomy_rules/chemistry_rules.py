"""
Structured, data-driven taxonomy classification rules for Course 2: Chemistry.
Maps 45 syllabus topics across 12 units using deterministic domain terminology.
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

CHEMISTRY_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------------------
    # Unit 1 (id=20): Periodic Properties
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=20,
        topic_name="Periodic Trends",
        unit_id=20,
        unit_name="Periodic Properties",
        strong_phrases=[
            "periodic trends", "periodic table", "periodicity in properties",
            "modern periodic", "mendeleev periodic", "periodic variation"
        ],
        specific_keywords=["periodicity"],
        negative_guards=["electron affinity", "ionization energy", "electronegativity", "polarizability"]
    ),
    TaxonomyTopicRule(
        topic_id=21,
        topic_name="Atomic Radius",
        unit_id=20,
        unit_name="Periodic Properties",
        strong_phrases=[
            "atomic radius", "atomic radii", "covalent radius", "covalent radii",
            "van der waals radius", "variation in atomic radii", "variation of atomic radii"
        ],
        specific_keywords=[],
        negative_guards=["radial wave function", "radial probability", "schrodinger", "wavefunction", "ionic radius"]
    ),
    TaxonomyTopicRule(
        topic_id=22,
        topic_name="Ionization Energy",
        unit_id=20,
        unit_name="Periodic Properties",
        strong_phrases=[
            "ionization energy", "ionization potential", "first ionization",
            "second ionization", "successive ionization", "factors affecting ionization"
        ],
        specific_keywords=["ionization energy", "ionisation energy"],
        negative_guards=["polarizability", "fajan", "photoelectron", "xps"]
    ),
    TaxonomyTopicRule(
        topic_id=40,
        topic_name="Electron Affinity",
        unit_id=20,
        unit_name="Periodic Properties",
        strong_phrases=[
            "electron affinity", "electron gain enthalpy", "factors affecting electron affinity",
            "successive electron affinities"
        ],
        specific_keywords=["electron affinity"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=41,
        topic_name="Electronegativity",
        unit_id=20,
        unit_name="Periodic Properties",
        strong_phrases=[
            "electronegativity", "pauling scale", "mulliken scale",
            "pauling's scale", "electronegative scale", "allred-rochow"
        ],
        specific_keywords=["electronegativity", "electronegativities"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=42,
        topic_name="Ionic Radius",
        unit_id=20,
        unit_name="Periodic Properties",
        strong_phrases=[
            "ionic radius", "ionic radii", "lanthanide contraction",
            "cationic radius", "anionic radius", "isoelectronic species",
            "isoelectronic ions", "variation of ionic radii"
        ],
        specific_keywords=["ionic radii"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=43,
        topic_name="Effective Nuclear Charge and Screening",
        unit_id=20,
        unit_name="Periodic Properties",
        strong_phrases=[
            "effective nuclear charge", "slater rule", "slater's rule",
            "screening constant", "shielding constant", "slater rules",
            "shielding effect", "calculate effective nuclear charge"
        ],
        specific_keywords=["z_eff", "zeff"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=44,
        topic_name="Polarizability and Polarizing Power",
        unit_id=20,
        unit_name="Periodic Properties",
        strong_phrases=[
            "polarizability", "polarizing power", "fajan's rule",
            "fajan rule", "fajans rule", "covalent character in ionic",
            "fajan's rules", "fajan rules"
        ],
        specific_keywords=["polarizability", "fajan"],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 2 (id=21): Chemical Equilibria
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=23,
        topic_name="Equilibrium Constant",
        unit_id=21,
        unit_name="Chemical Equilibria",
        strong_phrases=[
            "equilibrium constant", "law of chemical equilibrium", "kp and kc",
            "relation between kp and kc", "k_p and k_c", "reaction quotient",
            "equilibrium concentrations"
        ],
        specific_keywords=[],
        negative_guards=["solubility product", "common ion", "precipitation"]
    ),
    TaxonomyTopicRule(
        topic_id=24,
        topic_name="Le Chatelier Principle",
        unit_id=21,
        unit_name="Chemical Equilibria",
        strong_phrases=[
            "le chatelier", "le-chatelier", "le chatelier's principle",
            "effect of temperature on equilibrium", "effect of pressure on equilibrium",
            "chatelier's principle"
        ],
        specific_keywords=["chatelier"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=25,
        topic_name="Free Energy in Equilibria",
        unit_id=21,
        unit_name="Chemical Equilibria",
        strong_phrases=[
            "free energy and equilibrium", "vant hoff isotherm", "van't hoff isotherm",
            "van't hoff isochore", "standard free energy change and equilibrium",
            "delta g and equilibrium", "free energy change in equilibrium"
        ],
        specific_keywords=[],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 3 (id=22): Stereo Chemistry And Organic Reactions
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=26,
        topic_name="Stereoisomers",
        unit_id=22,
        unit_name="Stereo Chemistry And Organic Reactions",
        strong_phrases=[
            "stereoisomer", "stereoisomerism", "geometrical isomerism",
            "cis-trans", "cis trans", "diastereomer", "diastereomers",
            "structural isomerism", "constitutional isomerism"
        ],
        specific_keywords=["stereoisomers"],
        negative_guards=[
            "coordination isomerism", "linkage isomerism", "hydrate isomerism",
            "crystal field", "coordination compounds", "co-ordination isomerism",
            "co-ordination", "coordination compound"
        ]
    ),
    TaxonomyTopicRule(
        topic_id=27,
        topic_name="Organic Reaction Mechanisms",
        unit_id=22,
        unit_name="Stereo Chemistry And Organic Reactions",
        strong_phrases=[
            "sn1", "sn2", "e1 mechanism", "e2 mechanism", "e1cb",
            "nucleophilic substitution", "electrophilic addition", "carbocation intermediate",
            "mechanism of sn1", "mechanism of sn2", "mechanism of e1", "mechanism of e2",
            "elimination reaction", "bimolecular nucleophilic", "unimolecular nucleophilic"
        ],
        specific_keywords=[],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=67,
        topic_name="Optical Activity and Chirality",
        unit_id=22,
        unit_name="Stereo Chemistry And Organic Reactions",
        strong_phrases=[
            "optical activity", "chirality", "chiral center", "asymmetric carbon",
            "enantiomer", "enantiomers", "racemic mixture", "racemization",
            "r/s configuration", "r and s configuration", "cip rule", "cip sequence",
            "specific rotation", "plane polarized light", "chiral molecule", "chiral molecules"
        ],
        specific_keywords=["chiral", "enantiomer", "enantiomers", "racemic"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=68,
        topic_name="Conformational Analysis",
        unit_id=22,
        unit_name="Stereo Chemistry And Organic Reactions",
        strong_phrases=[
            "conformational analysis", "conformations of cyclohexane", "conformation of cyclohexane",
            "conformations of ethane", "conformation of ethane", "conformations of n-butane",
            "conformation of n-butane", "chair conformation", "boat conformation",
            "torsional strain", "eclipsed and staggered", "conformation of butane",
            "staggered conformation", "eclipsed conformation", "skew conformation",
            "potential energy of n-butane"
        ],
        specific_keywords=["staggered", "eclipsed"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=69,
        topic_name="Stereochemical Projections",
        unit_id=22,
        unit_name="Stereo Chemistry And Organic Reactions",
        strong_phrases=[
            "fischer projection", "newman projection", "sawhorse projection",
            "flying wedge projection", "convert the following fischer", "fischer to newman"
        ],
        specific_keywords=["sawhorse", "newman projection", "fischer projection"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=70,
        topic_name="Organic Reagents and Reaction Types",
        unit_id=22,
        unit_name="Stereo Chemistry And Organic Reactions",
        strong_phrases=[
            "nucleophile and electrophile", "electrophilic reagents", "nucleophilic reagents",
            "markovnikov's rule", "markovnikov rule", "anti-markovnikov",
            "saytzeff rule", "zaitsev rule", "leaving group ability"
        ],
        specific_keywords=["markovnikov", "saytzeff", "zaitsev"],
        negative_guards=["clemmensen", "wolff kishner", "oxidation using kmno4", "aldol condensation"]
    ),
    TaxonomyTopicRule(
        topic_id=71,
        topic_name="Organic Oxidation and Reduction",
        unit_id=22,
        unit_name="Stereo Chemistry And Organic Reactions",
        strong_phrases=[
            "clemmensen reduction", "wolff-kishner", "wolff kishner",
            "reduction of carbonyl", "oxidation of alcohol", "kmno4 oxidation",
            "nabh4 reduction", "liaih4 reduction", "oxidation using kmno4",
            "reduction with nabh4", "oxidizing agent and reducing agent"
        ],
        specific_keywords=["clemmensen", "wolff-kishner", "nabh4", "liaih4"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=72,
        topic_name="Organic Synthesis and Condensation",
        unit_id=22,
        unit_name="Stereo Chemistry And Organic Reactions",
        strong_phrases=[
            "aldol condensation", "cannizzaro reaction", "wittig reaction",
            "grignard reagent", "dieckmann condensation", "perkin reaction",
            "claisen condensation", "synthesis of aspirin", "synthesis of paracetamol",
            "synthesis and uses of aspirin", "uses of aspirin"
        ],
        specific_keywords=["cannizzaro", "wittig", "dieckmann", "grignard", "aldol"],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 4 (id=23): Polymers
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=28,
        topic_name="Polymer Types",
        unit_id=23,
        unit_name="Polymers",
        strong_phrases=[
            "thermoplastic", "thermosetting", "tacticity", "isotactic",
            "syndiotactic", "atactic", "bakelite", "teflon", "nylon 6,6",
            "nylon-6,6", "polyvinyl chloride", "pvc polymer", "conducting polymer",
            "conducting polymers", "vulcanization of rubber", "natural and synthetic rubber",
            "biodegradable polymer", "classification of polymers"
        ],
        specific_keywords=["bakelite", "teflon", "tacticity", "isotactic", "syndiotactic", "atactic", "vulcanization"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=29,
        topic_name="Polymerization Processes",
        unit_id=23,
        unit_name="Polymers",
        strong_phrases=[
            "chain growth polymerization", "step growth polymerization",
            "addition polymerization", "condensation polymerization",
            "free radical polymerization", "cationic polymerization",
            "anionic polymerization", "coordination polymerization",
            "ziegler-natta", "ziegler natta", "mechanism of free radical polymerization",
            "degree of polymerization", "degree of polymerisation",
            "free radical polymerisation", "addition polymerisation",
            "condensation polymerisation", "step growth polymerisation",
            "chain growth polymerisation"
        ],
        specific_keywords=["copolymerization", "polymerization mechanism", "polymerisation mechanism"],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 5 (id=24): Advanced Engineering Materials
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=30,
        topic_name="Material Properties",
        unit_id=24,
        unit_name="Advanced Engineering Materials",
        strong_phrases=[
            "stress-strain", "stress strain", "young's modulus", "yield point",
            "tensile strength", "ductility", "brittleness", "hardness test",
            "toughness of materials", "elastic body", "plastic body",
            "ceramic matrix composite", "metal matrix composite", "engineering materials"
        ],
        specific_keywords=["stress-strain"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=31,
        topic_name="Corrosion Resistance",
        unit_id=24,
        unit_name="Advanced Engineering Materials",
        strong_phrases=[
            "corrosion resistance", "sacrificial anode", "cathodic protection",
            "impressed current cathodic", "pilling-bedworth", "pilling bedworth",
            "galvanic corrosion", "pitting corrosion", "stress corrosion",
            "passivation of metals", "passivity of metals", "corrosion control methods",
            "dry and wet corrosion", "wet corrosion", "dry corrosion",
            "mechanism of corrosion", "types of corrosion", "define corrosion",
            "corrosion of metals"
        ],
        specific_keywords=["sacrificial anode", "cathodic protection", "pilling-bedworth"],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 6 (id=27): Quantum and Atomic Structure
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=45,
        topic_name="Quantum Mechanics and Atomic Structure",
        unit_id=27,
        unit_name="Quantum and Atomic Structure",
        strong_phrases=[
            "schrodinger wave equation", "schrodinger equation",
            "time independent schrodinger", "time dependent schrodinger",
            "heisenberg uncertainty", "uncertainty principle", "de-broglie",
            "de broglie", "wave-particle duality", "planck's quantum",
            "photoelectric effect", "black body radiation", "compton effect",
            "wave function physical significance", "born interpretation"
        ],
        specific_keywords=["schrodinger", "schrödinger", "de-broglie"],
        negative_guards=["particle in a box", "one dimensional box", "hydrogen atom", "radial and angular"]
    ),
    TaxonomyTopicRule(
        topic_id=46,
        topic_name="Particle in a Box",
        unit_id=27,
        unit_name="Quantum and Atomic Structure",
        strong_phrases=[
            "particle in a box", "one dimensional box", "1d box",
            "particle in a 1-d box", "particle in one-dimensional box",
            "zero point energy of particle in a box", "energy eigenvalues of particle in a box",
            "wave function for particle in a box"
        ],
        specific_keywords=["particle in a box", "one-dimensional box"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=47,
        topic_name="Hydrogen Atomic Orbitals",
        unit_id=27,
        unit_name="Quantum and Atomic Structure",
        strong_phrases=[
            "radial and angular wave", "radial wave function", "angular wave function",
            "hydrogen atom", "hydrogen atomic orbital", "orbitals of hydrogen",
            "1s orbital of hydrogen", "radial probability distribution", "nodes in hydrogen"
        ],
        specific_keywords=[],
        negative_guards=["molecular orbital", "lcao", "h2 molecule", "h2+ molecule"]
    ),

    # -------------------------------------------------------------------------
    # Unit 7 (id=28): Molecular Orbital Theory
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=48,
        topic_name="Molecular Orbital Theory",
        unit_id=28,
        unit_name="Molecular Orbital Theory",
        strong_phrases=[
            "molecular orbital theory", "mo theory", "molecular orbital diagram",
            "lcao", "linear combination of atomic orbitals", "bond order",
            "bonding and antibonding", "bonding and anti-bonding",
            "homonuclear diatomic", "heteronuclear diatomic", "paramagnetism of o2",
            "paramagnetic nature of o2", "mo energy level diagram", "h2 molecule",
            "h2+ molecule", "overlap of s and p", "overlapping of p-p",
            "sigma and pi molecular", "mo concept"
        ],
        specific_keywords=["bond order", "lcao", "anti-bonding"],
        negative_guards=["crystal field", "cfse", "aromaticity", "huckel"]
    ),
    TaxonomyTopicRule(
        topic_id=49,
        topic_name="Aromaticity and Pi Molecular Orbitals",
        unit_id=28,
        unit_name="Molecular Orbital Theory",
        strong_phrases=[
            "aromaticity", "huckel's rule", "huckel rule", "4n+2",
            "pi molecular orbital", "pi molecular orbitals of benzene",
            "pi molecular orbitals of butadiene", "annulene", "antiaromatic",
            "non-aromatic", "tropylium ion", "cyclopentadienyl anion"
        ],
        specific_keywords=["aromaticity", "huckel", "antiaromatic"],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 8 (id=29): Coordination and Crystal Field Theory
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=50,
        topic_name="Coordination Chemistry",
        unit_id=29,
        unit_name="Coordination and Crystal Field Theory",
        strong_phrases=[
            "werner's theory", "werner theory", "coordination number",
            "chelating ligand", "chelate effect", "edta ligand", "denticity of ligand",
            "monodentate", "bidentate", "polydentate", "coordination sphere",
            "sidgwick ean", "effective atomic number rule"
        ],
        specific_keywords=["werner", "chelate", "chelating", "denticity", "polydentate"],
        negative_guards=["crystal field", "cfse", "splitting in octahedral", "splitting in tetrahedral", "linkage isomerism", "coordination isomerism"]
    ),
    TaxonomyTopicRule(
        topic_id=51,
        topic_name="Crystal Field Theory",
        unit_id=29,
        unit_name="Coordination and Crystal Field Theory",
        strong_phrases=[
            "crystal field theory", "crystal field splitting", "cfse",
            "octahedral splitting", "tetrahedral splitting", "spectrochemical series",
            "high spin and low spin", "pairing energy", "d-d transition",
            "d orbital splitting", "crystal field stabilization energy", "10 dq",
            "splitting of d orbitals", "octahedral field", "tetrahedral field",
            "increasing order of wavelength of light absorbed",
            "wavelength of light absorbed"
        ],
        specific_keywords=["cfse", "spectrochemical series"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=52,
        topic_name="Coordination Isomerism",
        unit_id=29,
        unit_name="Coordination and Crystal Field Theory",
        strong_phrases=[
            "isomerism in coordination", "coordination isomerism", "linkage isomerism",
            "ionization isomerism", "hydrate isomerism", "solvate isomerism",
            "optical isomerism in coordination", "geometrical isomerism in coordination",
            "fac and mer", "facial and meridional", "isomerism exhibited by coordination",
            "isomerism exhibited by the coordination compounds",
            "isomerism exhibited by coordination compounds",
            "isomerism shown by the coordination compounds",
            "isomerism shown by coordination compounds",
            "isomerism exhibited in transition metal",
            "isomerism in transition metal",
            "isomerism in transition metal compounds",
            "co-ordination isomerism"
        ],
        specific_keywords=["linkage isomerism", "ionization isomerism", "hydrate isomerism"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=53,
        topic_name="Molecular Symmetry",
        unit_id=29,
        unit_name="Coordination and Crystal Field Theory",
        strong_phrases=[
            "molecular symmetry", "symmetry element", "symmetry operation",
            "center of inversion", "plane of symmetry", "proper axis of rotation",
            "improper axis of rotation", "point group", "c2v point group",
            "c3v point group", "elements of symmetry"
        ],
        specific_keywords=["point group", "symmetry element", "symmetry operation"],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 9 (id=30): Spectroscopy
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=54,
        topic_name="Spectroscopy Fundamentals",
        unit_id=30,
        unit_name="Spectroscopy",
        strong_phrases=[
            "electromagnetic radiation", "regions of electromagnetic",
            "beer-lambert's law", "beer lambert", "absorption of radiation",
            "selection rules in spectroscopy", "spectroscopic transition",
            "interaction of emr with matter"
        ],
        specific_keywords=["beer-lambert"],
        negative_guards=["uv-vis", "uv visible", "infrared", "nmr", "photoelectron", "xps"]
    ),
    TaxonomyTopicRule(
        topic_id=55,
        topic_name="Electronic and UV-Visible Spectroscopy",
        unit_id=30,
        unit_name="Spectroscopy",
        strong_phrases=[
            "electronic spectroscopy", "uv-visible spectroscopy", "uv-vis spectroscopy",
            "uv vis spectroscopy", "uv-vis", "uv vis", "chromophore", "auxochrome", "bathochromic shift",
            "hypsochromic shift", "hyperchromic", "hypochromic", "woodward-fieser",
            "woodward fieser", "pi to pi*", "n to pi*", "electronic transitions",
            "selection rule for electronic"
        ],
        specific_keywords=["chromophore", "auxochrome", "bathochromic", "hypsochromic"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=56,
        topic_name="Rotational Spectroscopy",
        unit_id=30,
        unit_name="Spectroscopy",
        strong_phrases=[
            "rotational spectroscopy", "rotational spectrum", "microwave spectroscopy",
            "rigid rotor", "selection rule for rotational", "rotational constant",
            "moment of inertia in rotational", "centrifugal distortion", "microwave active"
        ],
        specific_keywords=["rigid rotor", "rotational constant"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=57,
        topic_name="Vibrational and Infrared Spectroscopy",
        unit_id=30,
        unit_name="Spectroscopy",
        strong_phrases=[
            "vibrational spectroscopy", "infrared spectroscopy", "ir spectroscopy",
            "simple harmonic oscillator", "anharmonic oscillator", "hooke's law in ir",
            "stretching and bending vibration", "stretching frequency", "fingerprint region",
            "selection rule for vibrational", "zero point energy of oscillator",
            "degrees of freedom of vibration", "fermi resonance",
            "vibrational spectrum", "vibrational rotational spectrum",
            "infra-red absorption", "absorb in ir region", "absorption in the ir",
            "absorption in ir region", "diatomic molecule undergoing simple harmonic motion",
            "simple harmonic motion"
        ],
        specific_keywords=["fingerprint region", "harmonic oscillator", "infra-red"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=58,
        topic_name="Nuclear Magnetic Resonance",
        unit_id=30,
        unit_name="Spectroscopy",
        strong_phrases=[
            "nuclear magnetic resonance", "nmr spectroscopy", "1h nmr",
            "pmr spectroscopy", "chemical shift", "spin-spin coupling",
            "tetramethylsilane", "tms reference", "shielding and deshielding",
            "splitting of nmr signals", "n+1 rule in nmr", "larmor frequency",
            "gyromagnetic ratio"
        ],
        specific_keywords=["chemical shift", "spin-spin coupling", "tetramethylsilane"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=59,
        topic_name="Photoelectron Spectroscopy",
        unit_id=30,
        unit_name="Spectroscopy",
        strong_phrases=[
            "photoelectron spectroscopy", "x-ray photoelectron spectroscopy",
            "xps spectroscopy", "ultraviolet photoelectron", "ups spectroscopy",
            "binding energy in xps", "esca", "source for xps", "core electron binding energy",
            "principle, instrumentation and applications of xps",
            "principle and instrumentation of xps", "instrumentation of xps",
            "principle of xps"
        ],
        specific_keywords=["photoelectron spectroscopy", "xps", "esca"],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 10 (id=31): Solid State and Diffraction
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=60,
        topic_name="X-ray Diffraction and Crystal Structure",
        unit_id=31,
        unit_name="Solid State and Diffraction",
        strong_phrases=[
            "x-ray diffraction", "bragg's law", "bragg law", "miller indices",
            "interplanar spacing", "bravais lattice", "unit cell dimensions",
            "cubic crystal system", "powder x-ray diffraction", "diffraction of crystals",
            "braggs law"
        ],
        specific_keywords=["bragg's law", "bragg law", "miller indices", "bravais"],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 11 (id=32): Thermodynamics and Intermolecular Forces
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=61,
        topic_name="Chemical Thermodynamics",
        unit_id=32,
        unit_name="Thermodynamics and Intermolecular Forces",
        strong_phrases=[
            "first law of thermodynamics", "second law of thermodynamics",
            "third law of thermodynamics", "carnot cycle", "entropy change",
            "gibbs free energy", "helmholtz free energy", "maxwell relations",
            "maxwell's thermodynamic relations", "joule-thomson effect",
            "clapeyron equation", "clausius-clapeyron", "internal energy and enthalpy",
            "gibbs-helmholtz", "gibbs helmholtz", "gibbs-helmhotz", "gibbs helmhotz",
            "entropy of the universe", "entropy of an isolated system"
        ],
        specific_keywords=["carnot cycle", "maxwell relations", "clausius-clapeyron"],
        negative_guards=["hard and soft", "hsab", "van der waals", "intermolecular"]
    ),
    TaxonomyTopicRule(
        topic_id=62,
        topic_name="Hard and Soft Acids and Bases",
        unit_id=32,
        unit_name="Thermodynamics and Intermolecular Forces",
        strong_phrases=[
            "hard and soft acids and bases", "hsab principle", "hsab theory",
            "pearson's hsab", "pearson hsab", "hard acid", "soft acid",
            "hard base", "soft base", "symbiosis in hsab", "pearson principle",
            "acids and bases as hard and soft", "classification of acids and bases as hard and soft"
        ],
        specific_keywords=["hsab", "pearson"],
        negative_guards=[]
    ),
    TaxonomyTopicRule(
        topic_id=63,
        topic_name="Intermolecular Forces",
        unit_id=32,
        unit_name="Thermodynamics and Intermolecular Forces",
        strong_phrases=[
            "intermolecular forces", "van der waals forces", "van der waals interactions",
            "hydrogen bonding", "dipole-dipole interaction", "london dispersion forces",
            "ion-dipole", "intermolecular hydrogen bond", "intramolecular hydrogen bond",
            "vander waal's", "vander waals interactions", "vander waal interactions", "vander waals forces"
        ],
        specific_keywords=["london dispersion"],
        negative_guards=["van der waals equation", "vander waals equation", "vander waal equation", "equation of state", "critical constants", "real gases"]
    ),
    TaxonomyTopicRule(
        topic_id=64,
        topic_name="Real Gases and Critical Phenomena",
        unit_id=32,
        unit_name="Thermodynamics and Intermolecular Forces",
        strong_phrases=[
            "van der waals equation of state", "real gases", "critical temperature",
            "critical pressure", "critical volume", "critical constants",
            "liquefaction of gases", "compressibility factor", "deviation from ideal gas",
            "van der waals constants", "vander waals equation of state",
            "vander waals equation", "vander waals constants",
            "clausius equation", "berthelot equation"
        ],
        specific_keywords=["compressibility factor"],
        negative_guards=[]
    ),

    # -------------------------------------------------------------------------
    # Unit 12 (id=33): Electrochemistry
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=65,
        topic_name="Electrochemical Cells and Electrode Potentials",
        unit_id=33,
        unit_name="Electrochemistry",
        strong_phrases=[
            "electrochemical cell", "galvanic cell", "nernst equation",
            "standard electrode potential", "reference electrode", "calomel electrode",
            "standard hydrogen electrode", "she electrode", "glass electrode",
            "emf of cell", "pourbaix diagram", "electrochemical series",
            "cell potential and free energy", "nernst cquation"
        ],
        specific_keywords=["nernst equation", "pourbaix", "calomel electrode"],
        negative_guards=["solubility product", "precipitation"]
    ),
    TaxonomyTopicRule(
        topic_id=66,
        topic_name="Solubility Equilibria",
        unit_id=33,
        unit_name="Electrochemistry",
        strong_phrases=[
            "solubility product", "common ion effect", "precipitation titration",
            "ksp and solubility", "solubility equilibrium", "solubility product constant"
        ],
        specific_keywords=["solubility product", "common ion effect"],
        negative_guards=[]
    ),
]
