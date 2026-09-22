"""
Taxonomy classification rules for Course 4: Introduction To Computational Biology (21BTB102T).
Derived directly from the official SRM Biotechnology Syllabus (2021 Regulation)
and validated against historical exam papers.

Unit 1 (id=54): Cell and Evolution (Topics 120-123)
Unit 2 (id=4):  Basics in Biochemistry (Topics 124-127)
Unit 3 (id=55): Structure Biology (Topics 128-131)
Unit 4 (id=56): Neurobiology (Topics 132-135)
Unit 5 (id=57): Immunobiology (Topics 136-139)
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

ICB_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------
    # UNIT 1: CELL AND EVOLUTION
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=120,
        topic_name="Cell Theory and Whittaker's Kingdom Classification",
        unit_id=54,
        unit_name="Cell and Evolution",
        strong_phrases=[
            "cell theory", "five kingdom classification", "kingdom classification",
            "whittaker", "r.h.whittaker", "unicellular eukaryotic",
            "prokaryotes and eukaryotes", "prokaryotic cells and eukaryotic",
            "differences between prokaryotes and eukaryotes"
        ],
        specific_keywords=["whittaker", "hooke", "robert hooke"],
        negative_guards=["stem cell", "organelles", "mitosis", "meiosis", "blastocyst"]
    ),
    TaxonomyTopicRule(
        topic_id=121,
        topic_name="Cell Organelles and Cellular Homeostasis",
        unit_id=54,
        unit_name="Cell and Evolution",
        strong_phrases=[
            "cell organelles", "plant cell organelles", "cellular homeostasis",
            "organelles present in the eukaryotic", "structure and function of plant cell organelles",
            "oxidation of glucose takes place", "endoplasmic reticulum", "homeostasis"
        ],
        specific_keywords=["organelle", "organelles", "mitochondria", "nucleolus"],
        negative_guards=["translation", "transcription", "blastocyst", "genetic algorithm"]
    ),
    TaxonomyTopicRule(
        topic_id=122,
        topic_name="Cell Division, Replication, and Tissue Differentiation",
        unit_id=54,
        unit_name="Cell and Evolution",
        strong_phrases=[
            "cell division", "sister chromatids", "sister chromatid",
            "cytoplasm division", "cytokinesis", "mitosis", "meiosis",
            "sister chromatids separate", "meiosis produces", "diploid daughter cells",
            "haploid daughter cells", "homologous pair of chromosomes"
        ],
        specific_keywords=["cytokinesis", "meiosis", "mitosis", "chromatids", "diploid", "haploid"],
        negative_guards=["blastocyst", "stem cell", "genetic algorithm"]
    ),
    TaxonomyTopicRule(
        topic_id=123,
        topic_name="Stem Cells and Genetic Algorithms in Evolution",
        unit_id=54,
        unit_name="Cell and Evolution",
        strong_phrases=[
            "stem cell", "stem cells", "genetic algorithm", "genetic algorithms",
            "pluripotent stem cells", "pluripotent stem cell", "inner cell mass",
            "blastocyst", "blastocysts", "fitness score", "stem cell technology"
        ],
        specific_keywords=["stem cells", "stem cell", "pluripotent", "blastocyst", "genetic algorithm", "genetic algorithms"],
        negative_guards=["cell theory", "mitosis", "meiosis", "organelle"]
    ),

    # -------------------------------------------------------------
    # UNIT 2: BASICS IN BIOCHEMISTRY
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=124,
        topic_name="Biomolecules: Carbohydrates, Lipids, and Proteins",
        unit_id=4,
        unit_name="Basics in Biochemistry",
        strong_phrases=[
            "carbohydrates in life processes", "types and importance of carbohydrates",
            "biochemistry of carbohydrates", "carbohydrates with illustrated examples",
            "disaccharide", "disaccharides", "polysaccharide", "polysaccharides",
            "cholesterol is a", "cellulose", "glycogen"
        ],
        specific_keywords=["carbohydrate", "carbohydrates", "disaccharide", "disaccharides", "polysaccharide", "cholesterol"],
        negative_guards=["nucleic acid", "transcription", "translation", "blast"]
    ),
    TaxonomyTopicRule(
        topic_id=125,
        topic_name="Nucleic Acids, Enzymes, and Hormones",
        unit_id=4,
        unit_name="Basics in Biochemistry",
        strong_phrases=[
            "nucleic acids", "nucleic acid", "enzymes and hormones",
            "cofactor is", "production of glucagon", "nucleoside",
            "nitrogenous base that is not present in dna", "sugar in dna molecules"
        ],
        specific_keywords=["cofactor", "glucagon", "nucleoside", "nucleic acids", "nucleic acid"],
        negative_guards=["secondary structure", "transcription", "translation", "blast", "genbank"]
    ),
    TaxonomyTopicRule(
        topic_id=126,
        topic_name="Human Genome Project and Genomics",
        unit_id=4,
        unit_name="Basics in Biochemistry",
        strong_phrases=[
            "human genome project", "comparative genomics", "genomics with a special note",
            "study of how genes and intergenic regions of the genome"
        ],
        specific_keywords=["genomics", "human genome project", "hgp"],
        negative_guards=["blast", "pymol", "vaccine", "ann"]
    ),
    TaxonomyTopicRule(
        topic_id=127,
        topic_name="Sequence Databases and BLAST Search Tool",
        unit_id=4,
        unit_name="Basics in Biochemistry",
        strong_phrases=[
            "blast algorithm", "blast search", "blastn", "blastp",
            "sequence database for proteins", "nucleic acid database",
            "genbank is a", "uniprotkb", "biological databases and how is blast"
        ],
        specific_keywords=["blast", "blastn", "blastp", "genbank", "uniprotkb", "uniprot"],
        negative_guards=["pdb", "pymol", "rasmol", "neural network"]
    ),

    # -------------------------------------------------------------
    # UNIT 3: STRUCTURE BIOLOGY
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=128,
        topic_name="Protein Synthesis: Transcription and Translation",
        unit_id=55,
        unit_name="Structure Biology",
        strong_phrases=[
            "steps involved in translation", "translation in detail with neat diagrams",
            "anticodon for acu", "start codon", "codon uga", "codon aug",
            "removal of introns from pre-mrna", "process of removal of introns",
            "transport of amino acids at the site of protein synthesis", "splicing"
        ],
        specific_keywords=["anticodon", "transcription", "translation", "splicing", "start codon", "trna"],
        negative_guards=["pymol", "rasmol", "pdb", "secondary structure prediction", "ann"]
    ),
    TaxonomyTopicRule(
        topic_id=129,
        topic_name="Protein Secondary and Tertiary Structure",
        unit_id=55,
        unit_name="Structure Biology",
        strong_phrases=[
            "classification and structure of protein", "structural and functional classification of proteins",
            "two-dimensional structure of proteins", "crucial for the primary structure of protein",
            "alpha helix", "beta sheet", "helix and sheet formation",
            "bonds between amino acids", "polypeptide called protein"
        ],
        specific_keywords=["alpha helix", "beta sheet", "peptide bond"],
        negative_guards=["predict", "prediction", "tools", "pymol", "rasmol", "pdb", "blast"]
    ),
    TaxonomyTopicRule(
        topic_id=130,
        topic_name="Structural Databases and Molecular Visualizing Tools",
        unit_id=55,
        unit_name="Structure Biology",
        strong_phrases=[
            "molecular visualization tool", "structure visualization",
            "protein data bank", "pdb was established", "different structure databases",
            "protein visualization tools with examples", "pymol", "rasmol",
            "contains the information about 3d structure of proteins"
        ],
        specific_keywords=["pymol", "rasmol", "pdb", "rcsb"],
        negative_guards=["blast", "genbank", "ann", "svm"]
    ),
    TaxonomyTopicRule(
        topic_id=131,
        topic_name="Secondary Structure Prediction Algorithms",
        unit_id=55,
        unit_name="Structure Biology",
        strong_phrases=[
            "predict protein secondary structure", "prediction of secondary structure in proteins",
            "secondary structure prediction tools", "secondary structure prediction methods",
            "chou-fasman", "chou fasman", "gor method",
            "determines the propensity or intrinsic tendency of each residue",
            "protein structures can be predicted computationally"
        ],
        specific_keywords=["chou-fasman", "gor", "propensity"],
        negative_guards=["pymol", "rasmol", "blast", "genbank"]
    ),

    # -------------------------------------------------------------
    # UNIT 4: NEUROBIOLOGY
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=132,
        topic_name="Neuronal Anatomy, Glial Cells, and Brain Organization",
        unit_id=56,
        unit_name="Neurobiology",
        strong_phrases=[
            "type of glial cells and their functions", "star shaped brain cells",
            "surround axons in the pns and form myelin sheath", "myelin sheath",
            "astrocytes", "microglia", "loss of dopaminergic neurons",
            "alzheimer's is caused by", "alzheimer's disease", "parkinson's disease with respect to neurons"
        ],
        specific_keywords=["astrocytes", "microglia", "glial", "alzheimer", "alzheimer's", "parkinson", "parkinson's"],
        negative_guards=["artificial neural network", "ann", "vaccine", "immune"]
    ),
    TaxonomyTopicRule(
        topic_id=133,
        topic_name="Biological Neural Mechanisms and Synaptic Transmission",
        unit_id=56,
        unit_name="Neurobiology",
        strong_phrases=[
            "transmission of electrical signal from one neuron to next",
            "transmission of an electrical signal from one neuron",
            "released at the synapse", "resting potential for a neuron",
            "spiking event in the neuron", "depolarization", "refractory period",
            "transmission of a nerve impulse from one neuron"
        ],
        specific_keywords=["synapse", "neurotransmitter", "neurotransmitters", "resting potential", "refractory"],
        negative_guards=["artificial neural network", "ann", "machine learning"]
    ),
    TaxonomyTopicRule(
        topic_id=134,
        topic_name="Artificial Neural Networks and Biological Comparison",
        unit_id=56,
        unit_name="Neurobiology",
        strong_phrases=[
            "artificial neural networks", "artificial neural network", "ann does not contain",
            "what is ann", "weights in a neural network", "input units in an artificial neuron",
            "neural networks? how is it applied in biology", "artificial neuron"
        ],
        specific_keywords=["ann", "artificial neural network", "artificial neural networks"],
        negative_guards=["vaccine", "epitope", "blast"]
    ),
    TaxonomyTopicRule(
        topic_id=135,
        topic_name="Machine Learning and Data Mining in Biology",
        unit_id=56,
        unit_name="Neurobiology",
        strong_phrases=[
            "machine learning and data mining in biology", "knowledge discovery in databases",
            "machine learning in biology", "uses of machine learning in biology",
            "clustering is a type of", "machine learning algorithm to classify",
            "machine learning methods for biology"
        ],
        specific_keywords=["data mining", "machine learning", "kdd"],
        negative_guards=["vaccine", "epitope", "cell division"]
    ),

    # -------------------------------------------------------------
    # UNIT 5: IMMUNOBIOLOGY
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=136,
        topic_name="Elements of the Immune System and Immune Responses",
        unit_id=57,
        unit_name="Immunobiology",
        strong_phrases=[
            "humoral immune response", "cell-mediated immunity", "cell mediated immunity",
            "composition of blood and different types of leukocytes",
            "different immune cells and their characteristics", "contribute 60% of the wbc",
            "agranular leukocyte", "rich in immune cells", "plasma-like liquid carried by lymphatic circulation"
        ],
        specific_keywords=["humoral", "leukocyte", "leukocytes", "neutrophil", "lymphatic", "lymph"],
        negative_guards=["vaccine", "vaccination", "epitope", "netmhc"]
    ),
    TaxonomyTopicRule(
        topic_id=137,
        topic_name="Active and Passive Immunity and Antibodies",
        unit_id=57,
        unit_name="Immunobiology",
        strong_phrases=[
            "innate and acquired immunity", "active and passive immunity", "natural passive immunity",
            "active acquired immunity", "antibodies are made from", "makes antibodies",
            "inability of the immune system to distinguish self", "autoimmune disease",
            "mother's antibodies"
        ],
        specific_keywords=["antibodies", "antibody", "autoimmune", "acquired immunity", "passive immunity", "active immunity"],
        negative_guards=["epitope", "netmhc", "netmhcpan", "vaccine"]
    ),
    TaxonomyTopicRule(
        topic_id=138,
        topic_name="Immunoinformatics and Epitope Prediction",
        unit_id=57,
        unit_name="Immunobiology",
        strong_phrases=[
            "t cell and b-cell epitopes prediction tools", "t cell epitope prediction method",
            "epitope prediction method", "netmhc", "netmhcpan", "predicts binding of peptides to any known mhc",
            "epitope is present on", "computational methods help in immunology"
        ],
        specific_keywords=["epitope", "epitopes", "netmhc", "netmhcpan", "immunoinformatics"],
        negative_guards=["polio", "live attenuated", "killed vaccine"]
    ),
    TaxonomyTopicRule(
        topic_id=139,
        topic_name="Computational Vaccine Design and Target Discovery",
        unit_id=57,
        unit_name="Immunobiology",
        strong_phrases=[
            "vaccines and its types", "vaccine is administered to the body",
            "development of vaccines for sars-cov2", "polio drops are",
            "polio vaccine is a type of", "live attenuated vaccine",
            "inactivated vaccine", "diphtheria and tetanus are developed as"
        ],
        specific_keywords=["vaccine", "vaccines", "vaccination", "polio"],
        negative_guards=["epitope", "netmhc", "blast"]
    ),
]
