"""
Taxonomy classification rules for Course 10: Microbiology (21BTC201T / 21BTB103T).
Derived directly from the official SRM IST Department of Biotechnology Syllabus.

Unit 1 (id=10): Cell: Basic Unit of Life (Topics 220-223)
Unit 2 (id=74): Macromolecules and Metabolism (Topics 224-227)
Unit 3 (id=75): Microbiology in Human Life (Topics 228-231)
Unit 4 (id=76): Basics of Biosensors and Molecular Motors (Topics 232-235)
Unit 5 (id=77): Basics of Biomaterial and its Applications (Topics 236-239)
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

MICROBIO_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------
    # UNIT 1: CELL: BASIC UNIT OF LIFE
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=220,
        topic_name="Cell Structure and Organelles: Organization and Functions",
        unit_id=10,
        unit_name="Cell: Basic Unit of Life",
        strong_phrases=[
            "various cell organelles present in animal cells", "organelles of cells",
            "endoplasmic reticulum is absent in", "cell membrane is",
            "nucleus and other organelles enclosed within membranes",
            "water in plant cell is stored in", "compare the animal cell and plant cell",
            "plasma membrane and explain how they are involved", "organelle found within an eukaryotic cell",
            "animal cell and plant cell"
        ],
        specific_keywords=["organelles", "endoplasmic reticulum", "vacuoles", "stomata"],
        negative_guards=["meiosis", "stem cells", "differentiation", "glucose sensor", "antibiotics"]
    ),
    TaxonomyTopicRule(
        topic_id=221,
        topic_name="Cell Cycle, Division, and Meiotic Recombination",
        unit_id=10,
        unit_name="Cell: Basic Unit of Life",
        strong_phrases=[
            "crossing over occurs in meiosis", "cell cycle does growth occur",
            "meiotic recombination", "phases of the cell cycle", "cell division",
            "protein required for replication is synthesized in",
            "dna replication occurs during which phase of the cell cycle",
            "prophase", "metaphase", "anaphase", "telophase", "cytokinesis",
            "g1 phase", "s phase", "g2 phase", "m phase"
        ],
        specific_keywords=["meiosis", "mitosis", "cell cycle", "crossing over", "interphase"],
        negative_guards=["stem cells", "differentiation", "biosensors", "biomaterials"]
    ),
    TaxonomyTopicRule(
        topic_id=222,
        topic_name="Cell Differentiation and Stem Cell Biology",
        unit_id=10,
        unit_name="Cell: Basic Unit of Life",
        strong_phrases=[
            "undifferentiated cells are called", "cells that differentiate into only one type",
            "heart muscle cells are derived from", "pluripotent", "totipotent", "unipotent", "multipotent",
            "cell differentiation", "embryonic stem cells are called"
        ],
        specific_keywords=["undifferentiated", "pluripotent", "totipotent", "unipotent", "multipotent", "endoderm", "ectoderm", "mesoderm"],
        negative_guards=["ethical issues", "disagreement among public"]
    ),
    TaxonomyTopicRule(
        topic_id=223,
        topic_name="Stem Cell Applications and Ethical Considerations",
        unit_id=10,
        unit_name="Cell: Basic Unit of Life",
        strong_phrases=[
            "disagreement among public using embryonic stem cells", "embryonic stem cells for medical treatments",
            "stem cell therapy and its various ethical issues", "ethical issues with respect to india",
            "stem cells and its important in stem cells research", "stem cell applications",
            "therapeutic applications of stem cells"
        ],
        specific_keywords=["embryonic stem cells", "stem cell ethics", "stem cell therapy"],
        negative_guards=["crossing over", "cell membrane is"]
    ),

    # -------------------------------------------------------------
    # UNIT 2: MACROMOLECULES AND METABOLISM
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=224,
        topic_name="Carbohydrate Structure, Classification, and Glucose Metabolism",
        unit_id=74,
        unit_name="Macromolecules and Metabolism",
        strong_phrases=[
            "simplest form of carbohydrates", "monosaccharides and its classifications",
            "in carbohydrates, monosaccharides are joined by", "metabolism of glucose",
            "converts glucose into pyruvate", "glycolysis", "sugar molecule",
            "glycogen is a", "maltose"
        ],
        specific_keywords=["monosaccharide", "monosaccharides", "glycosidic bond", "glucose metabolism", "glycolysis"],
        negative_guards=["glucose sensor", "glucose electrode", "glucose oxidase", "biosensor"]
    ),
    TaxonomyTopicRule(
        topic_id=225,
        topic_name="Lipids and Fatty Acid Metabolism",
        unit_id=74,
        unit_name="Macromolecules and Metabolism",
        strong_phrases=[
            "which one is not lipid", "fatty acid metabolism", "structure of lipids",
            "metabolism of fatty acid", "beta oxidation of fatty acid",
            "saturated fatty acids"
        ],
        specific_keywords=["lipid", "lipids", "fats", "waxes", "fatty acid", "fatty acids", "beta oxidation"],
        negative_guards=["glucose sensor", "amino acids"]
    ),
    TaxonomyTopicRule(
        topic_id=226,
        topic_name="Amino Acids, Protein Architecture, and Enzymes",
        unit_id=74,
        unit_name="Macromolecules and Metabolism",
        strong_phrases=[
            "proteins are made up of", "how many amino acids make up a protein",
            "enzymes generally have", "protein architecture", "enzyme kinetics",
            "metabolism of amino acids", "bond between amino acid to form a polymer protein"
        ],
        specific_keywords=["amino acid", "amino acids", "protein structure", "enzymes", "enzyme kinetics"],
        negative_guards=["glucose sensor", "glucose oxidase", "biosensors", "nucleic acids (dna and rna)"]
    ),
    TaxonomyTopicRule(
        topic_id=227,
        topic_name="Nucleic Acids (DNA and RNA) and Photosynthesis",
        unit_id=74,
        unit_name="Macromolecules and Metabolism",
        strong_phrases=[
            "phosphate group is attached to which carbon of pentose sugar",
            "structure of dna and rna", "primary transcript in eukaryotes",
            "energy from the sun transported within chloroplast", "light reaction, the light energy electron excites",
            "photosystem i", "photosystem ii", "photosynthesis", "pentose sugar",
            "exons and introns"
        ],
        specific_keywords=["pentose sugar", "photosynthesis", "photosystem", "chloroplast", "exons and introns"],
        negative_guards=["biomaterials", "biosensors", "proteins are made up of"]
    ),

    # -------------------------------------------------------------
    # UNIT 3: MICROBIOLOGY IN HUMAN LIFE
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=228,
        topic_name="Pathogenic Microorganisms: Bacteria and Viruses",
        unit_id=75,
        unit_name="Microbiology in Human Life",
        strong_phrases=[
            "virulence factor will not help the pathogenic bacteria", "pathogenic microorganisms",
            "pathogenic bacteria", "pathogenic virus", "pathogens are", "zoonosis means",
            "food borne bacteria", "influenza disease is caused by", "siderophores",
            "exotoxins", "endotoxins"
        ],
        specific_keywords=["virulence", "siderophores", "exotoxins", "endotoxins", "zoonosis", "pathogen", "pathogens"],
        negative_guards=["antibiotics", "biosensors", "vaccines"]
    ),
    TaxonomyTopicRule(
        topic_id=229,
        topic_name="Antibiotics and Antibiotic Resistance Mechanisms",
        unit_id=75,
        unit_name="Microbiology in Human Life",
        strong_phrases=[
            "antibiotic used to treat anaphylactic reaction to penicillin", "cannot be treated with antibiotics resistance",
            "various antibiotics and its applications", "antibiotic resistance", "penicillin",
            "broad spectrum antibiotics", "mode of action of antibiotics"
        ],
        specific_keywords=["antibiotic", "antibiotics", "penicillin", "antibiotic resistance", "erythromycin", "meropenem"],
        negative_guards=["biosensors", "biomaterials", "vaccine"]
    ),
    TaxonomyTopicRule(
        topic_id=230,
        topic_name="Vaccines and Communicable Disease Control Strategies",
        unit_id=75,
        unit_name="Microbiology in Human Life",
        strong_phrases=[
            "doctors are advising to use mask to prevent communicable diseases",
            "various control strategies", "communicable diseases", "hib vaccine is an example",
            "mrna vaccines", "toxoid vaccine", "attenuated vaccine", "types of vaccines",
            "vaccination", "disease prevention"
        ],
        specific_keywords=["vaccine", "vaccines", "communicable diseases", "vaccination", "immunization"],
        negative_guards=["glucose sensor", "biomaterials"]
    ),
    TaxonomyTopicRule(
        topic_id=231,
        topic_name="Environmental and Industrial Microbiology",
        unit_id=75,
        unit_name="Microbiology in Human Life",
        strong_phrases=[
            "environmental microbiology", "industrial microbiology", "methanotrophs uses",
            "optimum for biodegradation", "biosparging is", "microbial fermentation",
            "bioremediation", "microbial production of ethanol"
        ],
        specific_keywords=["environmental microbiology", "industrial microbiology", "bioremediation", "biosparging", "biodegradation", "methanotrophs"],
        negative_guards=["stem cells", "biomaterials"]
    ),

    # -------------------------------------------------------------
    # UNIT 4: BASICS OF BIOSENSORS AND MOLECULAR MOTORS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=232,
        topic_name="Biosensors: Components, Transducers, and Principles",
        unit_id=76,
        unit_name="Basics of Biosensors and Molecular Motors",
        strong_phrases=[
            "biosensors use the movement of electrons produced during redox reactions",
            "types of biosensors", "components of biosensors", "amperometric biosensors",
            "potentiometric biosensors", "pregnancy kit detects", "pregnancy test"
        ],
        specific_keywords=["biosensor", "biosensors", "amperometric", "potentiometric", "pregnancy kit", "pregnancy test"],
        negative_guards=["glucose sensor", "glucose electrode", "linear motors", "rotary motors"]
    ),
    TaxonomyTopicRule(
        topic_id=233,
        topic_name="Glucose Sensors and Clinical Diagnostic Applications",
        unit_id=76,
        unit_name="Basics of Biosensors and Molecular Motors",
        strong_phrases=[
            "glucose electrode, glucose oxidase has been coupled", "how does glucose sensor work",
            "glucose sensor", "glucose oxidase", "glucose electrode", "clinical diagnostic applications of biosensors"
        ],
        specific_keywords=["glucose sensor", "glucose electrode", "glucose oxidase"],
        negative_guards=["metabolism of glucose", "monosaccharides"]
    ),
    TaxonomyTopicRule(
        topic_id=234,
        topic_name="Linear Molecular Motors: Actin and Myosin Systems",
        unit_id=76,
        unit_name="Basics of Biosensors and Molecular Motors",
        strong_phrases=[
            "linear motors: actin and myosin", "actin and myosin motors",
            "linear molecular motors", "kinesin and dynein motor transport",
            "kinesin and dynein", "actin myosine movement", "actin myosin"
        ],
        specific_keywords=["linear motors", "actin and myosin", "kinesin", "dynein"],
        negative_guards=["flagellar motor", "rotatory motors", "atpase"]
    ),
    TaxonomyTopicRule(
        topic_id=235,
        topic_name="Rotary Molecular Motors: Flagellar Motor and ATPase",
        unit_id=76,
        unit_name="Basics of Biosensors and Molecular Motors",
        strong_phrases=[
            "rotatory motors: flagella motor and atpase", "flagellar motor",
            "f0 develops rotary torque", "molecular machines work in the scale of",
            "structure and function of atp synthase", "f0f1 atp motor",
            "f0f1 atpase", "atp synthase motor"
        ],
        specific_keywords=["flagellar motor", "rotatory motors", "rotary motors", "molecular machines", "atp synthase"],
        negative_guards=["glucose sensor", "biomaterials"]
    ),

    # -------------------------------------------------------------
    # UNIT 5: BASICS OF BIOMATERIAL AND ITS APPLICATIONS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=236,
        topic_name="Classification and Characterization of Biomaterials",
        unit_id=77,
        unit_name="Basics of Biomaterial and its Applications",
        strong_phrases=[
            "classes of biomaterials used in biological applications", "various classes of biomaterials",
            "properties of biomaterials", "types of biomaterials", "biomedical applications, which property is very important",
            "natural polymer? (a) chitosan"
        ],
        specific_keywords=["chitosan", "polymeric biomaterials", "ceramic biomaterials", "metallic biomaterials"],
        negative_guards=["biocompatibility", "scaffold", "organ replacement", "bone cements", "joint replacement"]
    ),
    TaxonomyTopicRule(
        topic_id=237,
        topic_name="Biocompatibility and Mechanical Properties of Scaffolds",
        unit_id=77,
        unit_name="Basics of Biomaterial and its Applications",
        strong_phrases=[
            "biocompatibility of a material is", "compressive strength of scaffold",
            "mechanical properties of scaffolds", "tissue engineering scaffolds"
        ],
        specific_keywords=["biocompatibility", "scaffold", "scaffolds", "compressive strength"],
        negative_guards=["organ replacement", "bone cements", "joint replacement"]
    ),
    TaxonomyTopicRule(
        topic_id=238,
        topic_name="Biomaterials for Organ Replacement and Medical Devices",
        unit_id=77,
        unit_name="Basics of Biomaterial and its Applications",
        strong_phrases=[
            "biomaterials used for organ replacement", "not an example of biomaterial application in medical devices",
            "metal is not used in joint replacement", "biomaterial used on intraocular lenses",
            "joint replacement", "intraocular lenses", "artificial organs"
        ],
        specific_keywords=["organ replacement", "joint replacement", "intraocular lenses", "prosthetics"],
        negative_guards=["bone cements", "biomimetics"]
    ),
    TaxonomyTopicRule(
        topic_id=239,
        topic_name="Biomimetic Materials in Dental and Bone Applications",
        unit_id=77,
        unit_name="Basics of Biomaterial and its Applications",
        strong_phrases=[
            "biomimetics in dental and bone applications", "bone plates",
            "bone cements", "dental applications", "concept of biomiminetics",
            "primary benefit of biomimetics", "biomaterials used for bone replacement",
            "bone replacement"
        ],
        specific_keywords=["biomimetic", "biomimetics", "biomiminetics", "bone plates", "bone cements", "dental"],
        negative_guards=["organ replacement", "molecular motors"]
    ),
]
