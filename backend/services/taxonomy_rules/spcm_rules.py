"""
Structured, data-driven taxonomy classification rules for Course 13: Semiconductor Physics and Computational Methods.
Maps 27 syllabus topics across 5 units using deterministic domain terminology.
Derived strictly from the official SRM IST Department of Physics & Nanotechnology Lesson Plan (21PYB102J),
course instructor slide decks (Dr. Venkata Ravindra A), and KTR campus module question banks.
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

SPCM_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------------------
    # Unit 1 (id=45): Free Electron Theory and Energy Bands
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=73,
        topic_name="Classical Free Electron Theory",
        unit_id=45,
        unit_name="Free Electron Theory and Energy Bands",
        strong_phrases=[
            "classical free electron theory", "drude and lorentz", "drude-lorentz",
            "drude model", "drude theory", "lorentz theory", "wiedemann-franz law",
            "wiedemann franz", "success of classical free electron", "postulates of classical free electron",
            "failures of classical free electron", "failure of classical free electron"
        ],
        specific_keywords=["drude"],
        negative_guards=["sommerfeld", "quantum free electron", "fermi-dirac", "schrodinger", "quantum well"]
    ),
    TaxonomyTopicRule(
        topic_id=74,
        topic_name="Quantum Free Electron Theory",
        unit_id=45,
        unit_name="Free Electron Theory and Energy Bands",
        strong_phrases=[
            "quantum free electron theory", "sommerfeld model", "sommerfeld theory",
            "fermi-dirac distribution", "density of states in 3d", "density of states for a given material is",
            "fermi-dirac statistics", "probability of occupation in a given energy level",
            "postulates of quantum free electron", "success of quantum free electron",
            "fermi energy of electron", "fermi temperature", "fermi velocity"
        ],
        specific_keywords=["sommerfeld", "fermi-dirac"],
        negative_guards=["classical free electron", "drude", "low dimensional", "joint density of states", "quantum well", "quantum wire", "quantum dot"]
    ),
    TaxonomyTopicRule(
        topic_id=75,
        topic_name="Band Theory and Kronig-Penney Model",
        unit_id=45,
        unit_name="Free Electron Theory and Energy Bands",
        strong_phrases=[
            "kronig-penney model", "kronig penney model", "kronig-penney", "kronig penney",
            "bloch theorem", "periodic potential", "splitting energy band in solids",
            "energy band in solids", "allowed and forbidden bands", "allowed and forbidden energy",
            "effective mass of an electron", "effective mass of electron",
            "band theory of solids", "zero band gap", "periodic field of 1d crystal",
            "movement of electron in periodic potential"
        ],
        specific_keywords=["kronig-penney", "bloch theorem", "periodic potential", "band theory of solids"],
        negative_guards=["direct band gap", "indirect band gap", "e-k diagram"]
    ),
    TaxonomyTopicRule(
        topic_id=76,
        topic_name="Brillouin Zones and Band Gaps",
        unit_id=45,
        unit_name="Free Electron Theory and Energy Bands",
        strong_phrases=[
            "brillouin zone", "brillouin zones", "e-k diagram", "e k diagram", "e-k diagrams",
            "direct and indirect band gap", "direct band gap semiconductor", "indirect band gap semiconductor",
            "concept of phonons", "concept of brillouin zone", "first brillouin zone"
        ],
        specific_keywords=["brillouin zone", "direct bandgap", "indirect bandgap", "phonons"],
        negative_guards=["recombination", "spontaneous emission", "photocurrent", "solar cell"]
    ),
    TaxonomyTopicRule(
        topic_id=77,
        topic_name="Fermi Surface and Computational Band Structure",
        unit_id=45,
        unit_name="Free Electron Theory and Energy Bands",
        strong_phrases=[
            "fermi surface of a metal", "fermi surface of cu", "computational determination of band structure",
            "tight binding approximation", "lcao approximation", "quantum espresso", "vasp",
            "computational band structure", "fermi surface"
        ],
        specific_keywords=["fermi surface", "tight binding", "lcao", "quantum espresso", "vasp"],
        negative_guards=["fermi's golden rule", "fermi golden rule", "fermi level in intrinsic", "fermi level in extrinsic"]
    ),

    # -------------------------------------------------------------------------
    # Unit 2 (id=46): Semiconductor Physics and Carrier Transport
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=78,
        topic_name="Intrinsic Semiconductors",
        unit_id=46,
        unit_name="Semiconductor Physics and Carrier Transport",
        strong_phrases=[
            "intrinsic semiconductor", "intrinsic semiconductors", "intrinsic carrier concentration",
            "carrier concentration in intrinsic semiconductor", "intrinsic fermi level",
            "pure silicon and pure germanium", "pure crystal of silicon", "pure germanium crystal"
        ],
        specific_keywords=["intrinsic semiconductor", "intrinsic semiconductors", "intrinsic carrier"],
        negative_guards=["extrinsic", "donor", "acceptor", "doping", "p-n junction", "schottky", "n-type", "p-type"]
    ),
    TaxonomyTopicRule(
        topic_id=79,
        topic_name="Extrinsic Semiconductors and Doping",
        unit_id=46,
        unit_name="Semiconductor Physics and Carrier Transport",
        strong_phrases=[
            "extrinsic semiconductor", "extrinsic semiconductors", "n-type semiconductor",
            "p-type semiconductor", "n type semiconductor", "p type semiconductor",
            "donor energy level", "acceptor energy level", "donor impurities", "acceptor impurities",
            "fermi level in p-type", "fermi level in n-type", "degenerate semiconductor",
            "difference between p-type and n-type"
        ],
        specific_keywords=["extrinsic semiconductor", "extrinsic semiconductors", "donor impurities", "acceptor impurities"],
        negative_guards=["p-n junction", "pn junction", "photodiode", "schottky", "two point probe", "four point probe", "band theory of solids", "zero band gap", "periodic potential", "optical absorption"]
    ),
    TaxonomyTopicRule(
        topic_id=80,
        topic_name="Carrier Generation, Recombination, and Continuity",
        unit_id=46,
        unit_name="Semiconductor Physics and Carrier Transport",
        strong_phrases=[
            "continuity equation", "continuity equation for electron", "continuity equation for hole",
            "carrier generation and recombination", "shockley-read-hall", "srh recombination",
            "srh carrier generation", "auger recombination", "auger transitions", "impact ionization",
            "carrier lifetime", "diffusion length of carriers"
        ],
        specific_keywords=["continuity equation", "srh recombination", "auger transition", "auger transitions", "impact ionization"],
        negative_guards=["optical absorption process", "spontaneous emission", "stimulated emission", "joint density of states"]
    ),
    TaxonomyTopicRule(
        topic_id=81,
        topic_name="Carrier Transport: Drift and Diffusion",
        unit_id=46,
        unit_name="Semiconductor Physics and Carrier Transport",
        strong_phrases=[
            "drift current", "diffusion current", "drift current density", "diffusion current density",
            "carrier transport", "einstein relation", "einstein's relation", "drift velocity and mobility"
        ],
        specific_keywords=["drift current", "diffusion current", "einstein relation"],
        negative_guards=["four probe", "two probe", "hall effect", "van der pauw", "boltzmann transport"]
    ),
    TaxonomyTopicRule(
        topic_id=82,
        topic_name="P-N Junction and Biasing",
        unit_id=46,
        unit_name="Semiconductor Physics and Carrier Transport",
        strong_phrases=[
            "p-n junction", "pn junction", "built-in potential", "built in potential", "depletion layer",
            "depletion width", "forward bias condition", "reverse bias condition", "junction capacitance",
            "vi characteristics of p-n junction", "p-n junction diode", "pn junction diode"
        ],
        specific_keywords=["built-in potential", "depletion layer", "forward bias", "reverse bias"],
        negative_guards=["schottky", "metal-semiconductor", "photodiode", "light emitting diode", "led", "oled", "solar cell", "extrinsic semiconductor"]
    ),
    TaxonomyTopicRule(
        topic_id=83,
        topic_name="Metal-Semiconductor Contacts",
        unit_id=46,
        unit_name="Semiconductor Physics and Carrier Transport",
        strong_phrases=[
            "metal-semiconductor junction", "metal-semiconductor contact", "schottky barrier",
            "schottky diode", "schottky junction", "ohmic contact", "non-rectifying contact",
            "rectifying junction", "rectifying contact"
        ],
        specific_keywords=["schottky barrier", "ohmic contact", "schottky junction", "non-rectifying contact"],
        negative_guards=["p-n junction", "pn junction diode", "solar cell", "photodiode"]
    ),
    TaxonomyTopicRule(
        topic_id=84,
        topic_name="Optoelectronic Devices and LEDs",
        unit_id=46,
        unit_name="Semiconductor Physics and Carrier Transport",
        strong_phrases=[
            "light emitting diode", "light emitting diodes", "organic light emitting diode",
            "organic light emitting diodes", "oled", "optoelectronic integrated circuit",
            "optoelectronic integrated circuits", "oeic", "photocurrent in a p-n junction",
            "photodiode photocurrent", "compound semiconductor for optoelectronic",
            "optoelectronic devices", "materials of interest for optoelectronic devices"
        ],
        specific_keywords=["light emitting diode", "light emitting diodes", "oled", "oeic", "photodiode"],
        negative_guards=["solar cell", "photovoltaic effect", "photovoltaics", "laser source"]
    ),

    # -------------------------------------------------------------------------
    # Unit 3 (id=47): Optical Processes and Photovoltaic Devices
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=85,
        topic_name="Optical Transitions and Absorption",
        unit_id=47,
        unit_name="Optical Processes and Photovoltaic Devices",
        strong_phrases=[
            "optical transitions in bulk", "optical absorption process", "absorption coefficient of semiconductor",
            "band to band transition", "impurity level to band transition", "impurity to band transition",
            "interband optical transition", "optical absorption in semiconductor"
        ],
        specific_keywords=["absorption coefficient", "band to band transition", "impurity to band transition"],
        negative_guards=["spontaneous emission", "stimulated emission", "solar cell", "photovoltaic effect", "uv-vis", "uv vis"]
    ),
    TaxonomyTopicRule(
        topic_id=86,
        topic_name="Radiative Recombination and Emission",
        unit_id=47,
        unit_name="Optical Processes and Photovoltaic Devices",
        strong_phrases=[
            "spontaneous emission", "stimulated emission", "einstein coefficient", "einstein's coefficient",
            "einstein coefficients", "einstein's coefficients", "einstein a and b", "optical recombination process",
            "radiative recombination", "population inversion"
        ],
        specific_keywords=["spontaneous emission", "stimulated emission", "einstein coefficients", "radiative recombination"],
        negative_guards=["srh recombination", "auger recombination", "impact ionization", "solar cell", "photovoltaic effect"]
    ),
    TaxonomyTopicRule(
        topic_id=87,
        topic_name="Joint Density of States and Transition Rates",
        unit_id=47,
        unit_name="Optical Processes and Photovoltaic Devices",
        strong_phrases=[
            "joint density of states", "optical joint density of states", "density of states for photons",
            "fermi's golden rule", "fermi golden rule", "transition rate per unit volume",
            "transition rates in semiconductor"
        ],
        specific_keywords=["joint density of states", "fermi's golden rule", "fermi golden rule"],
        negative_guards=["classical free electron", "sommerfeld", "quantum well", "quantum wire", "quantum dot"]
    ),
    TaxonomyTopicRule(
        topic_id=88,
        topic_name="Computational Optics and Optical Loss",
        unit_id=47,
        unit_name="Optical Processes and Photovoltaic Devices",
        strong_phrases=[
            "numerical computation of optical loss", "computation of optical loss", "optical loss",
            "finite element method to calculate photon density", "optical excitation in bn",
            "optical excitations in boron nitride"
        ],
        specific_keywords=["optical loss", "photon density of states"],
        negative_guards=["fermi's golden rule", "solar cell", "photovoltaic effect"]
    ),
    TaxonomyTopicRule(
        topic_id=89,
        topic_name="Solar Cells and Photovoltaics",
        unit_id=47,
        unit_name="Optical Processes and Photovoltaic Devices",
        strong_phrases=[
            "photovoltaic effect", "efficiency of a pv cell", "efficiency of a solar cell",
            "solar cell converts", "fill factor of solar cell", "short circuit current and open circuit voltage",
            "inverse square law of light using a photo cell", "v-i characteristics of a solar cell",
            "v-r characteristics of a solar cell", "photovoltaics", "pv cell", "photovoltaic cell", "photovoltaic cells"
        ],
        specific_keywords=["photovoltaic effect", "solar cell", "photovoltaics", "pv cell", "fill factor", "photovoltaic cell"],
        negative_guards=["photodiode", "light emitting diode", "led", "oled", "einstein", "optical transition", "optical transitions", "density of states of photon"]
    ),

    # -------------------------------------------------------------------------
    # Unit 4 (id=48): Semiconductor Measurements and Transport Equations
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=90,
        topic_name="Two-Point and Four-Point Probe Measurements",
        unit_id=48,
        unit_name="Semiconductor Measurements and Transport Equations",
        strong_phrases=[
            "two-point probe", "two point probe", "four-point probe", "four point probe",
            "van der pauw method", "van der pauw", "linear four probe", "linear method four probe",
            "sheet resistance measurement", "resistivity measurement by four probe",
            "resistivity determined using two probe", "advantages of four point probe"
        ],
        specific_keywords=["two-point probe", "four-point probe", "van der pauw", "four probe", "two probe"],
        negative_guards=["hall effect", "c-v measurement", "hot probe", "hot-point probe", "hot point probe"]
    ),
    TaxonomyTopicRule(
        topic_id=91,
        topic_name="Hall Effect and Carrier Mobility",
        unit_id=48,
        unit_name="Semiconductor Measurements and Transport Equations",
        strong_phrases=[
            "hall effect", "hall coefficient", "hall voltage", "hall mobility",
            "determine hall coefficient", "lorentz force in semiconductor", "hall probe",
            "carrier density and hall mobility", "hall coefficient of semiconductor"
        ],
        specific_keywords=["hall effect", "hall coefficient", "hall voltage", "hall mobility"],
        negative_guards=["van der pauw", "two point probe", "c-v measurement", "capacitance-voltage"]
    ),
    TaxonomyTopicRule(
        topic_id=92,
        topic_name="Hot-Point Probe and Capacitance-Voltage Measurements",
        unit_id=48,
        unit_name="Semiconductor Measurements and Transport Equations",
        strong_phrases=[
            "hot-point probe", "hot point probe", "hot probe method", "capacitance-voltage measurement",
            "capacitance-voltage measurements", "c-v measurement", "c-v measurements",
            "thermoelectric probe", "c-v profiling",
            "determining quickly whether a semiconductor sample is n type",
            "determine quickly whether a semiconductor sample is n type"
        ],
        specific_keywords=["hot-point probe", "hot point probe", "hot probe", "c-v measurement", "c-v measurements"],
        negative_guards=["hall effect", "four point probe", "van der pauw"]
    ),
    TaxonomyTopicRule(
        topic_id=93,
        topic_name="Diode Parameter Extraction and TCAD",
        unit_id=48,
        unit_name="Semiconductor Measurements and Transport Equations",
        strong_phrases=[
            "extraction of parameters in a diode", "diode parameter extraction", "introduction of tcad",
            "technology cad", "tcad simulation", "ideality factor of diode", "extraction of parameters in diode"
        ],
        specific_keywords=["tcad", "diode parameter extraction", "parameter extraction in a diode"],
        negative_guards=["vi characteristics of p-n junction", "built-in potential"]
    ),
    TaxonomyTopicRule(
        topic_id=94,
        topic_name="Boltzmann Transport Equation and Monte Carlo Method",
        unit_id=48,
        unit_name="Semiconductor Measurements and Transport Equations",
        strong_phrases=[
            "boltzmann transport equation", "boltzmann transport", "monte carlo method for solution of bte",
            "monte carlo methods for solution of bte", "monte carlo method", "monte carlo simulation",
            "scattering mechanisms in semiconductors", "boltzmann equation"
        ],
        specific_keywords=["boltzmann transport equation", "boltzmann transport", "monte carlo method", "bte"],
        negative_guards=["classical free electron", "drude"]
    ),

    # -------------------------------------------------------------------------
    # Unit 5 (id=49): Nanostructures and Characterization
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=95,
        topic_name="Low-Dimensional Systems and Density of States",
        unit_id=49,
        unit_name="Nanostructures and Characterization",
        strong_phrases=[
            "density of states in 2d 1d and 0d", "density of states in 2d", "density of states in 1d",
            "density of states in 0d", "density of states in lower-dimensional", "quantum well",
            "quantum wire", "quantum dot", "quantum dots", "quantum wells", "quantum wires",
            "low dimensional systems", "low-dimensional systems", "quantum confinement",
            "example of 0d material", "0d material", "1d material", "2d material", "nanoparticle", "nanowire", "nanosheet"
        ],
        specific_keywords=["quantum well", "quantum wire", "quantum dot", "low dimensional systems", "quantum dots", "quantum wells", "0d material", "nanoparticle", "nanowire"],
        negative_guards=["carbon nanotube", "cnt", "sem", "tem", "afm", "xrd"]
    ),
    TaxonomyTopicRule(
        topic_id=96,
        topic_name="Carbon Nanotubes (CNT)",
        unit_id=49,
        unit_name="Nanostructures and Characterization",
        strong_phrases=[
            "carbon nanotube", "carbon nanotubes", "cnt", "cnts", "armchair carbon nanotube",
            "zigzag carbon nanotube", "chiral carbon nanotube", "chiral vector of cnt",
            "swcnt", "mwcnt", "properties and synthesis of cnt", "applications of cnts",
            "applications of cnt", "nanotube", "nanotubes"
        ],
        specific_keywords=["carbon nanotube", "carbon nanotubes", "cnt", "swcnt", "mwcnt", "cnts", "nanotubes"],
        negative_guards=["quantum well", "quantum wire", "c-v measurement"]
    ),
    TaxonomyTopicRule(
        topic_id=97,
        topic_name="Nanofabrication Techniques",
        unit_id=49,
        unit_name="Nanostructures and Characterization",
        strong_phrases=[
            "chemical vapor deposition", "physical vapor deposition", "chemical vapour deposition",
            "physical vapour deposition", "cvd technique", "pvd technique", "cvd synthesis", "pvd synthesis",
            "thermal evaporation", "sputtering technique", "nanofabrication technique",
            "fabrication technique-cvd", "cvd and pvd", "cvd, pvd"
        ],
        specific_keywords=["chemical vapor deposition", "physical vapor deposition", "chemical vapour deposition", "physical vapour deposition", "cvd", "pvd"],
        negative_guards=["sem", "tem", "afm", "xrd", "microscopy"]
    ),
    TaxonomyTopicRule(
        topic_id=98,
        topic_name="Electron Microscopy and Surface Characterization",
        unit_id=49,
        unit_name="Nanostructures and Characterization",
        strong_phrases=[
            "scanning electron microscopy", "transmission electron microscopy", "atomic force microscopy",
            "atomic force microscope", "powder xrd", "lattice parameters using powder xrd",
            "scanning electron microscope", "transmission electron microscope", "afm",
            "x-ray diffraction for lattice parameters", "electron microscope"
        ],
        specific_keywords=["scanning electron microscopy", "transmission electron microscopy", "atomic force microscopy", "atomic force microscope", "sem", "tem", "afm", "electron microscope"],
        negative_guards=["cvd", "pvd", "chemical vapor deposition", "chemical vapour deposition", "physical vapor deposition", "physical vapour deposition", "cnt", "carbon nanotube", "carbon nano tubes", "nanotubes", "optical absorption"]
    ),
    TaxonomyTopicRule(
        topic_id=99,
        topic_name="Computational Image Processing for Nanomaterials",
        unit_id=49,
        unit_name="Nanostructures and Characterization",
        strong_phrases=[
            "computational and machine learning approach for electron microscopy",
            "machine learning approach for electron microscopy", "electron microscopy image processing",
            "microscopy image processing", "image processing of graphene", "example of graphene image processing"
        ],
        specific_keywords=["microscopy image processing", "electron microscopy image processing"],
        negative_guards=["quantum well", "cnt synthesis", "cvd"]
    ),
]
