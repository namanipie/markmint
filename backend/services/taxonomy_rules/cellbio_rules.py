"""
Taxonomy classification rules for Course 9: Cell Biology (21BTC102J / 21BTB105T).
Derived directly from the official SRM IST Biotechnology Syllabus and course materials.

Unit 1 (id=9):  Overview of Cells and Cell Research (Topics 200-203)
Unit 2 (id=70): Cell Structure and Function: Organelles (Topics 204-207)
Unit 3 (id=71): Cytoskeleton and Cellular Transport (Topics 208-211)
Unit 4 (id=72): Cell Signaling and Transduction Pathways (Topics 212-215)
Unit 5 (id=73): Cell Regulation, Cancer, and Stem Cells (Topics 216-219)
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

CELLBIO_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------
    # UNIT 1: OVERVIEW OF CELLS AND CELL RESEARCH
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=200,
        topic_name="Origin, Evolution, and Organization of Prokaryotic and Eukaryotic Cells",
        unit_id=9,
        unit_name="Overview of Cells and Cell Research",
        strong_phrases=[
            "origin and evolution of cells", "prokaryotic cells does not contain",
            "prokaryotic cells", "eukaryotic cells", "bacterial cell possess",
            "chemical evolution", "origin of universe"
        ],
        specific_keywords=["prokaryotic", "eukaryotic", "prokaryote", "eukaryote", "mesosomes", "fimbriae"],
        negative_guards=["actin", "flagella", "axoneme", "intermediate filaments"]
    ),
    TaxonomyTopicRule(
        topic_id=201,
        topic_name="Experimental Model Organisms and Microscopy Tools in Cell Biology",
        unit_id=9,
        unit_name="Overview of Cells and Cell Research",
        strong_phrases=[
            "model for studying", "squid is used as a model", "stained with gfp",
            "dark field microscope", "fluorescence microscope", "phase contrast microscope",
            "model organisms", "microscopy tools"
        ],
        specific_keywords=["model organism", "squid", "gfp", "microscope"],
        negative_guards=["oncogene", "cell signaling"]
    ),
    TaxonomyTopicRule(
        topic_id=202,
        topic_name="Molecular Composition of Cells: Macromolecules and Water",
        unit_id=9,
        unit_name="Overview of Cells and Cell Research",
        strong_phrases=[
            "molecular composition of cells", "macromolecules in cells",
            "fats are stored in the form of", "fats are stored"
        ],
        specific_keywords=["molecular composition", "macromolecules"],
        negative_guards=["membrane fluidity", "semipermeable membrane", "plasma membrane", "caveolin"]
    ),
    TaxonomyTopicRule(
        topic_id=203,
        topic_name="Structure, Composition, and Dynamics of the Plasma Membrane",
        unit_id=9,
        unit_name="Overview of Cells and Cell Research",
        strong_phrases=[
            "cell membrane fluidity", "structure, composition and function of semipermeable membrane",
            "semipermeable membrane in cells", "plasma membrane", "fluid mosaic model",
            "membrane fluidity", "caveolin interacts with", "caveolin"
        ],
        specific_keywords=["plasma membrane", "membrane fluidity", "caveolin", "semipermeable membrane"],
        negative_guards=["nuclear envelope", "symport", "antiport"]
    ),

    # -------------------------------------------------------------
    # UNIT 2: CELL STRUCTURE AND FUNCTION: ORGANELLES
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=204,
        topic_name="Nuclear Structure, Nuclear Envelope, and Nucleolus",
        unit_id=70,
        unit_name="Cell Structure and Function: Organelles",
        strong_phrases=[
            "nucleopore complex", "nuclear envelope", "sub-compartments of nucleus",
            "structure that separates the nucleus from cytoplasm", "coilin is present in",
            "cajal bodies", "nuclear speckle", "nucleolus"
        ],
        specific_keywords=["nucleopore", "nuclear envelope", "nucleolus", "coilin", "cajal bodies", "nuclear pore"],
        negative_guards=["mitochondrial matrix", "endoplasmic reticulum"]
    ),
    TaxonomyTopicRule(
        topic_id=205,
        topic_name="Endoplasmic Reticulum and Golgi Apparatus in Protein Processing",
        unit_id=70,
        unit_name="Cell Structure and Function: Organelles",
        strong_phrases=[
            "endoplasmic reticulum", "golgi apparatus", "golgi complex",
            "protein sorting and folding in er", "vesicle docking and fusion",
            "rough er", "smooth er", "detoxification of toxic compound phenobarbital",
            "phenobarbital"
        ],
        specific_keywords=["endoplasmic reticulum", "golgi", "phenobarbital", "vesicle docking", "protein sorting"],
        negative_guards=["nucleopore complex", "nuclear envelope"]
    ),
    TaxonomyTopicRule(
        topic_id=206,
        topic_name="Lysosomes, Peroxisomes, and Endocytic Sorting",
        unit_id=70,
        unit_name="Cell Structure and Function: Organelles",
        strong_phrases=[
            "enzymes present in lysosomes", "acid hydrolases", "lysosomal proteases",
            "process of endocytosis and how it is related to lysosome",
            "peroxisomes", "endocytic sorting"
        ],
        specific_keywords=["lysosomal", "peroxisome", "peroxisomes", "acid hydrolases", "endocytosis"],
        negative_guards=["nuclear envelope", "optic neuropathy"]
    ),
    TaxonomyTopicRule(
        topic_id=207,
        topic_name="Bioenergetics of Mitochondria and Chloroplasts",
        unit_id=70,
        unit_name="Cell Structure and Function: Organelles",
        strong_phrases=[
            "mitochondrial matrix", "genetic systems, and functions of mitochondria",
            "bioenergetics of mitochondria", "chloroplasts", "atp producing structures",
            "leber's hereditary optic neuropathy"
        ],
        specific_keywords=["mitochondria", "mitochondrial", "chloroplast", "chloroplasts", "bioenergetics", "optic neuropathy"],
        negative_guards=["endoplasmic reticulum", "nucleopore"]
    ),

    # -------------------------------------------------------------
    # UNIT 3: CYTOSKELETON AND CELLULAR TRANSPORT
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=208,
        topic_name="Actin and Myosin Filaments: Structure and Muscle Contraction",
        unit_id=71,
        unit_name="Cytoskeleton and Cellular Transport",
        strong_phrases=[
            "actin and myosin", "mechanism of muscle contraction", "muscle contraction",
            "prokaryotic ancestor of actin", "actin filaments", "mre b"
        ],
        specific_keywords=["actin", "myosin", "muscle contraction", "mre b"],
        negative_guards=["microtubules", "axoneme", "tubulin"]
    ),
    TaxonomyTopicRule(
        topic_id=209,
        topic_name="Microtubules, Centrosomes, and Intermediate Filaments",
        unit_id=71,
        unit_name="Cytoskeleton and Cellular Transport",
        strong_phrases=[
            "assembly, organization, and functions of microtubules", "cilia and flagella are made up of",
            "microtubule axoneme", "basic structure of cilia", "lamins are",
            "intermediate filaments", "microtubules", "centrosome"
        ],
        specific_keywords=["microtubule", "microtubules", "cilia", "flagella", "axoneme", "intermediate filament", "intermediate filaments", "lamins", "tubulin"],
        negative_guards=["symport", "antiport", "muscle contraction"]
    ),
    TaxonomyTopicRule(
        topic_id=210,
        topic_name="Passive and Active Membrane Transport and Ion Channels",
        unit_id=71,
        unit_name="Cytoskeleton and Cellular Transport",
        strong_phrases=[
            "na+-k+ pump", "symport, uniport and antiport", "smaller molecules can be transported across cell membrane without energy",
            "passive and active membrane transport", "ion channels", "defective channel",
            "life threatening lung disorder"
        ],
        specific_keywords=["na+-k+ pump", "symport", "uniport", "antiport", "active transport", "passive transport", "ion channel"],
        negative_guards=["g-protein", "map kinase pathway", "second messenger"]
    ),
    TaxonomyTopicRule(
        topic_id=211,
        topic_name="Cell-Cell Interactions: Adhesion, Tight Junctions, and Gap Junctions",
        unit_id=71,
        unit_name="Cytoskeleton and Cellular Transport",
        strong_phrases=[
            "cell junctions that prevent small molecules", "tight junctions",
            "gap junctions", "cell junctions are present in", "cell-cell interactions",
            "cell adhesion molecules", "desmosomes"
        ],
        specific_keywords=["cell junctions", "tight junction", "gap junction", "tight junctions", "gap junctions", "desmosomes", "cell adhesion"],
        negative_guards=["mitochondrial matrix", "map kinase pathway"]
    ),

    # -------------------------------------------------------------
    # UNIT 4: CELL SIGNALING AND TRANSDUCTION PATHWAYS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=212,
        topic_name="Principles and Modes of Intercellular Signaling: Autocrine, Paracrine, Endocrine",
        unit_id=72,
        unit_name="Cell Signaling and Transduction Pathways",
        strong_phrases=[
            "signaling molecule carried through the circulation to act on target cells",
            "autocrine, paracrine, endocrine", "modes of intercellular signaling",
            "intercellular signaling", "endocrine signaling", "paracrine signaling"
        ],
        specific_keywords=["intercellular signaling", "autocrine", "paracrine", "endocrine"],
        negative_guards=["retroviral oncogenes", "adenyl cyclase"]
    ),
    TaxonomyTopicRule(
        topic_id=213,
        topic_name="Cell Surface Receptors and Ligand Binding Mechanisms",
        unit_id=72,
        unit_name="Cell Signaling and Transduction Pathways",
        strong_phrases=[
            "cell surface receptor", "does not interact with cell surface receptor",
            "receptors activates the signal transduction pathways by dimerization",
            "ligand binding", "receptor dimerization"
        ],
        specific_keywords=["cell surface receptor", "surface receptor", "ligand binding"],
        negative_guards=["map kinase pathway", "second messenger"]
    ),
    TaxonomyTopicRule(
        topic_id=214,
        topic_name="G-Protein Coupled Receptor (GPCR) Pathways and Second Messengers",
        unit_id=72,
        unit_name="Cell Signaling and Transduction Pathways",
        strong_phrases=[
            "g-protein coupled receptor", "adenyl cyclase", "adenylate cyclase",
            "second messenger", "adenyl cyclase is responsible for", "ip3 acts to release",
            "adenyl cyclase catalyzes the atp conversion to second messenger"
        ],
        specific_keywords=["gpcr", "adenyl cyclase", "second messenger", "ip3", "camp", "g-protein"],
        negative_guards=["map kinase pathway", "stem cells"]
    ),
    TaxonomyTopicRule(
        topic_id=215,
        topic_name="Receptor Tyrosine Kinases and MAPK Signaling Cascades",
        unit_id=72,
        unit_name="Cell Signaling and Transduction Pathways",
        strong_phrases=[
            "map kinase pathway", "mapk signaling", "receptor tyrosine kinases",
            "describe map kinase pathway", "does not belong to map kinase pathway",
            "mapk pathway", "tyrosine kinase"
        ],
        specific_keywords=["map kinase", "mapk", "tyrosine kinase", "rtk"],
        negative_guards=["cell cycle checkpoints", "cyclins"]
    ),

    # -------------------------------------------------------------
    # UNIT 5: CELL REGULATION, CANCER, AND STEM CELLS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=216,
        topic_name="Cell Cycle Checkpoints, Cyclins, and CDKs",
        unit_id=73,
        unit_name="Cell Regulation, Cancer, and Stem Cells",
        strong_phrases=[
            "cell cycle checkpoints", "cyclins and cdks", "different phases of cell cycle",
            "protein mechanism in different phases of cell cycle", "cell cycle regulation"
        ],
        specific_keywords=["cell cycle", "cyclins", "cdk", "cyclin-dependent kinase", "checkpoints"],
        negative_guards=["mitosis", "meiosis", "hallmark of cancer", "apoptosis"]
    ),
    TaxonomyTopicRule(
        topic_id=217,
        topic_name="Mechanisms of Mitosis, Meiosis, and Chromosome Segregation",
        unit_id=73,
        unit_name="Cell Regulation, Cancer, and Stem Cells",
        strong_phrases=[
            "mechanisms of mitosis", "meiosis", "chromosome segregation",
            "mitotic spindle", "prophase", "metaphase", "anaphase", "telophase"
        ],
        specific_keywords=["mitosis", "meiosis", "chromosome segregation", "metaphase", "anaphase"],
        negative_guards=["cell cycle checkpoints", "cyclins"]
    ),
    TaxonomyTopicRule(
        topic_id=218,
        topic_name="Programmed Cell Death: Apoptosis vs Necrosis Pathways",
        unit_id=73,
        unit_name="Cell Regulation, Cancer, and Stem Cells",
        strong_phrases=[
            "programmed cell death", "apoptosis vs necrosis", "write a note on necroptosis",
            "necroptosis", "apoptosis", "cell death expresses", "phosphatidyl serine"
        ],
        specific_keywords=["apoptosis", "necroptosis", "cell death", "caspase", "caspases", "phosphatidyl serine"],
        negative_guards=["lung cancer", "breast cancer", "solid tumors", "hallmark of cancer"]
    ),
    TaxonomyTopicRule(
        topic_id=219,
        topic_name="Molecular Biology of Cancer, Oncogenes, and Stem Cell Therapeutics",
        unit_id=73,
        unit_name="Cell Regulation, Cancer, and Stem Cells",
        strong_phrases=[
            "hallmark of cancer", "solid tumors in connective tissues", "herceptin is used for the treatment",
            "retroviral oncogenes", "etiology, stages, diagnosis, and treatment of lung cancer",
            "genes that mutated during cancer formation", "tumors caused by hpv",
            "neurodegenerative disorders", "disorders of neurons", "stem cells and its applications",
            "stem cells give rise to all type of cells", "lcis represents", "aromatase inhibitors",
            "tangles of neurodegenerative disorder", "mesenchymal origin"
        ],
        specific_keywords=[
            "cancer", "oncogene", "oncogenes", "tumor", "tumors", "carcinoma", "sarcoma",
            "herceptin", "stem cell", "stem cells", "neurodegenerative", "piebaldism"
        ],
        negative_guards=["cell cycle checkpoints"]
    ),
]
