"""
Taxonomy classification rules for Course 12: Biochemistry (21BTC101T).
Derived directly from the official SRM IST Department of Biotechnology Syllabus.

Unit 1 (id=12): Introduction to Biochemistry (Topics 260-263)
Unit 2 (id=82): Introduction to Metabolism, Bioenergetics and Photosynthesis (Topics 264-267)
Unit 3 (id=83): Carbohydrate Metabolism (Topics 268-271)
Unit 4 (id=84): Protein Turnover and Amino Acids Metabolism (Topics 272-275)
Unit 5 (id=85): Fatty Acid and Nucleic Acids Metabolisms (Topics 276-279)
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

BIOCHEM_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------
    # UNIT 1: INTRODUCTION TO BIOCHEMISTRY
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=260,
        topic_name="Chemical Bonds, pH, Buffers, and Water in Biological Systems",
        unit_id=12,
        unit_name="Introduction to Biochemistry",
        strong_phrases=[
            "shared electrons among atoms", "ionic bonds", "covalent bonds",
            "van der waals", "hydrogen bonding", "ph and buffers", "henderson-hasselbalch",
            "lewis base", "lewis acid", "lone pair donor", "action of enzymes"
        ],
        specific_keywords=["covalent bonds", "ionic bonds", "buffers", "chemical bonds", "lewis base"],
        negative_guards=["glycolysis", "tca cycle", "beta-oxidation"]
    ),
    TaxonomyTopicRule(
        topic_id=261,
        topic_name="Carbohydrate Architecture: Monosaccharides, Polysaccharides, and Glycoproteins",
        unit_id=12,
        unit_name="Introduction to Biochemistry",
        strong_phrases=[
            "anomeric hydroxyl groups of two sugars", "cellulose polysaccharide is hydrolyzed",
            "reactions of monosaccharides", "monosaccharides, oligosaccharides and polysaccharides",
            "glycoproteins and lectins", "boat and chair", "pyranose sugar", "furanose sugar"
        ],
        specific_keywords=["monosaccharides", "oligosaccharides", "polysaccharides", "glycoproteins", "lectins", "anomeric", "pyranose"],
        negative_guards=["glycolysis", "gluconeogenesis", "tca cycle", "diabetes"]
    ),
    TaxonomyTopicRule(
        topic_id=262,
        topic_name="Amino Acids and Protein Organization: Primary to Quaternary Structure",
        unit_id=12,
        unit_name="Introduction to Biochemistry",
        strong_phrases=[
            "levels of protein organization", "amino acid in the provided list belongs to the aromatic group",
            "protein composition and structures", "quaternary structure of protein",
            "different structures of protein", "describe the protein structure with four levels",
            "collagen : plasma proteins", "glutathione", "plasma proteins", "zwitterion"
        ],
        specific_keywords=["protein organization", "amino acid structure", "zwitterion", "quaternary structure", "collagen", "histones", "glutathione"],
        negative_guards=["transamination", "urea cycle", "pest sequence", "amino acids metabolic disorders"]
    ),
    TaxonomyTopicRule(
        topic_id=263,
        topic_name="Lipids, Biological Membranes, and Nucleic Acid Structure",
        unit_id=12,
        unit_name="Introduction to Biochemistry",
        strong_phrases=[
            "cetyl alcohols is most commonly found in", "nucleotides are made up of except",
            "types of lipids with examples", "lipids and cell membrane", "phospholipids",
            "unsaturated fatty acids exhibit geometric isomerism", "how lipids are classified with example",
            "chemical properties of fats and oils", "structure of dna and rna", "waxes and triglycerides"
        ],
        specific_keywords=["cetyl alcohol", "phospholipids", "sphingolipids", "geometric isomerism", "fats and oils"],
        negative_guards=["beta-oxidation", "fatty acid release", "purine and pyrimidine"]
    ),

    # -------------------------------------------------------------
    # UNIT 2: INTRODUCTION TO METABOLISM, BIOENERGETICS AND PHOTOSYNTHESIS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=264,
        topic_name="Bioenergetics, High Energy Compounds, and Thermodynamics of Metabolism",
        unit_id=82,
        unit_name="Introduction to Metabolism, Bioenergetics and Photosynthesis",
        strong_phrases=[
            "with respect to anabolism except", "reaction to occur spontaneously",
            "delta g must be negative", "high energy compounds", "bioenergetics",
            "free energy change", "atp hydrolysis"
        ],
        specific_keywords=["anabolism", "catabolism", "bioenergetics", "high energy compounds"],
        negative_guards=["photosynthesis", "light reaction", "glycolysis"]
    ),
    TaxonomyTopicRule(
        topic_id=265,
        topic_name="Mitochondrial Electron Transport Chain and Complexes",
        unit_id=82,
        unit_name="Introduction to Metabolism, Bioenergetics and Photosynthesis",
        strong_phrases=[
            "nadh serves as a carrier of which of the following", "structure and functions of electron transport complexes",
            "electron transport chain in mitochondria", "cytochrome c oxidase", "structure of electron transport system",
            "electron transport system", "complex i", "complex ii", "complex iii", "complex iv"
        ],
        specific_keywords=["electron transport chain", "electron transport complexes", "cytochrome oxidase", "electron transport system"],
        negative_guards=["photosystem", "chloroplast", "glycolysis"]
    ),
    TaxonomyTopicRule(
        topic_id=266,
        topic_name="Oxidative Phosphorylation, Chemiosmotic Theory, and Shuttle Pathways",
        unit_id=82,
        unit_name="Introduction to Metabolism, Bioenergetics and Photosynthesis",
        strong_phrases=[
            "oxidative phosphorylation", "chemiosmotic theory", "chemisosmotic theory",
            "glycerol phosphate shuttle", "malate aspartate shuttle", "malate-aspartate shuttle",
            "explain any one of the shuttle pathway", "shuttle pathways", "atp synthase complex"
        ],
        specific_keywords=["oxidative phosphorylation", "chemiosmotic", "chemisosmotic", "malate aspartate shuttle", "glycerol phosphate shuttle", "shuttle pathway"],
        negative_guards=["photosynthesis", "light reaction", "tca cycle"]
    ),
    TaxonomyTopicRule(
        topic_id=267,
        topic_name="Photosynthesis: Light Reactions, Photophosphorylation, and Carbon Fixation",
        unit_id=82,
        unit_name="Introduction to Metabolism, Bioenergetics and Photosynthesis",
        strong_phrases=[
            "fixes carbondioxide is to organic form", "discuss the light reaction in plants",
            "photorespiration", "calvin cycle", "light and dark reactions",
            "z-scheme", "photophosphorylation", "photosystem i and photosystem ii"
        ],
        specific_keywords=["photosynthesis", "light reaction", "photorespiration", "calvin cycle", "rubisco", "photophosphorylation"],
        negative_guards=["glycolysis", "tca cycle", "urea cycle"]
    ),

    # -------------------------------------------------------------
    # UNIT 3: CARBOHYDRATE METABOLISM
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=268,
        topic_name="Glycolysis and Pyruvate Dehydrogenase Complex",
        unit_id=83,
        unit_name="Carbohydrate Metabolism",
        strong_phrases=[
            "enzyme reactions is not reversible in glycolysis", "arsenate binds to",
            "roles of five different cofactors / coenzymes requires for pyruvate",
            "pyruvate in the transition reaction", "compound that enters a mitochondrion is",
            "pathway of glycolysis", "hexokinase", "phosphofructokinase", "pyruvate kinase"
        ],
        specific_keywords=["glycolysis", "hexokinase", "phosphofructokinase", "pyruvate dehydrogenase"],
        negative_guards=["tca cycle", "citric acid cycle", "glycogen"]
    ),
    TaxonomyTopicRule(
        topic_id=269,
        topic_name="Citric Acid Cycle (TCA Cycle) and Amphibolic Nature",
        unit_id=83,
        unit_name="Carbohydrate Metabolism",
        strong_phrases=[
            "tca cycle enzymes nadp+ as a coenzyme", "illustrate the tca cycle with three regulatory steps",
            "citric acid cycle", "krebs cycle", "tca cycle", "amphibolic nature of tca cycle",
            "anaplerotic reactions"
        ],
        specific_keywords=["tca cycle", "citric acid cycle", "krebs cycle", "amphibolic"],
        negative_guards=["gluconeogenesis", "glycogen"]
    ),
    TaxonomyTopicRule(
        topic_id=270,
        topic_name="Gluconeogenesis and Glycogen Metabolism (Glycogenesis and Glycogenolysis)",
        unit_id=83,
        unit_name="Carbohydrate Metabolism",
        strong_phrases=[
            "breakdown of glycogen to form glucose", "glycogen oxidation to release glucose",
            "glycogen metabolism", "gluconeogenesis", "glycogenesis", "glycogenolysis",
            "muscle use of glycogen", "cori cycle"
        ],
        specific_keywords=["gluconeogenesis", "glycogenesis", "glycogenolysis", "glycogen metabolism", "cori cycle"],
        negative_guards=["diabetes mellitus", "insulin regulation", "islet cells"]
    ),
    TaxonomyTopicRule(
        topic_id=271,
        topic_name="Hormonal Regulation of Blood Glucose: Insulin, Glucagon, and Diabetes",
        unit_id=83,
        unit_name="Carbohydrate Metabolism",
        strong_phrases=[
            "significance of carbohydrates in the development of diabetes mellitus",
            "blood glucose levels regulation by insulin", "islet cells in langerhans",
            "improves insulin's ability to move glucose", "somatostatin",
            "insulin and glucagon", "diabetes mellitus", "hyperglycemia"
        ],
        specific_keywords=["diabetes mellitus", "blood glucose", "insulin regulation", "langerhans", "somatostatin", "metformin"],
        negative_guards=["tca cycle", "glycolysis"]
    ),

    # -------------------------------------------------------------
    # UNIT 4: PROTEIN TURNOVER AND AMINO ACIDS METABOLISM
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=272,
        topic_name="Protein Turnover, Proteolysis, and PEST Sequences",
        unit_id=84,
        unit_name="Protein Turnover and Amino Acids Metabolism",
        strong_phrases=[
            "pest sequence are rapidly degraded", "protein turnover",
            "ubiquitin proteasome system", "proteolysis", "lysosomal protein degradation",
            "pest sequence"
        ],
        specific_keywords=["pest sequence", "protein turnover", "ubiquitin", "proteasome"],
        negative_guards=["urea cycle", "transamination"]
    ),
    TaxonomyTopicRule(
        topic_id=273,
        topic_name="Transamination, Deamination, and Decarboxylation of Amino Acids",
        unit_id=84,
        unit_name="Protein Turnover and Amino Acids Metabolism",
        strong_phrases=[
            "transaminases require plp a coenzyme", "oxidative deamination of the amino acids alanine",
            "transaminase enzymes are present in", "transamination", "deamination",
            "decarboxylation of amino acids", "pyridoxal phosphate", "glutamate dehydrogenase"
        ],
        specific_keywords=["transamination", "deamination", "transaminases", "transaminase", "pyridoxal phosphate", "plp"],
        negative_guards=["urea cycle", "phenylketonuria"]
    ),
    TaxonomyTopicRule(
        topic_id=274,
        topic_name="Urea Cycle, Ammonia Toxicity, and Inborn Errors of Metabolism",
        unit_id=84,
        unit_name="Protein Turnover and Amino Acids Metabolism",
        strong_phrases=[
            "characteristics of phenyl ketonuria", "give an account of urea synthesis",
            "amino acids metabolic disorders", "covalently bind to ammonia, transport it",
            "urea cycle", "urea synthesis", "metabolism of ammonia", "phenylketonuria",
            "carbamoyl phosphate synthetase", "hyperammonemia"
        ],
        specific_keywords=["urea cycle", "urea synthesis", "phenylketonuria", "phenyl ketonuria", "ammonia toxicity"],
        negative_guards=["pest sequence"]
    ),
    TaxonomyTopicRule(
        topic_id=275,
        topic_name="Biosynthesis and Degradation of Essential and Non-Essential Amino Acids",
        unit_id=84,
        unit_name="Protein Turnover and Amino Acids Metabolism",
        strong_phrases=[
            "aromatic amino acid(s) biosynthesis from phosphoenolpyruvate",
            "compounds is not synthesized by tryptophan", "biosynthesis of amino acids",
            "feedback inhibition regulations", "shikimate pathway", "essential amino acids synthesis"
        ],
        specific_keywords=["amino acid biosynthesis", "shikimate pathway", "aromatic amino acid", "tryptophan"],
        negative_guards=["urea cycle", "pest sequence"]
    ),

    # -------------------------------------------------------------
    # UNIT 5: FATTY ACID AND NUCLEIC ACIDS METABOLISMS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=276,
        topic_name="Mobilization of Lipids and Beta-Oxidation of Fatty Acids",
        unit_id=85,
        unit_name="Fatty Acid and Nucleic Acids Metabolisms",
        strong_phrases=[
            "fatty acid release from adipose tissue", "oxidation of palmitic acid (c16)",
            "beta-oxidation", "fatty acid oxidation", "carnitine shuttle",
            "hormones signal the release of fatty acids"
        ],
        specific_keywords=["fatty acid release", "palmitic acid", "beta-oxidation", "fatty acid oxidation", "carnitine"],
        negative_guards=["ketone bodies", "purine"]
    ),
    TaxonomyTopicRule(
        topic_id=277,
        topic_name="Ketogenesis, Ketone Bodies, and Lipid Metabolism Disorders",
        unit_id=85,
        unit_name="Fatty Acid and Nucleic Acids Metabolisms",
        strong_phrases=[
            "describe the disorders of lipid metabolism", "ketone bodies & ketogenesis",
            "amino acids are ketogenic substances", "disorders of lipid metabolism",
            "ketogenesis", "ketone bodies", "ketosis", "diabetic ketoacidosis"
        ],
        specific_keywords=["ketone bodies", "ketogenesis", "disorders of lipid metabolism", "ketosis", "ketogenic substances"],
        negative_guards=["beta-oxidation", "purine"]
    ),
    TaxonomyTopicRule(
        topic_id=278,
        topic_name="Biosynthesis of Fatty Acids, Cholesterol, Eicosanoids, and Lipoproteins",
        unit_id=85,
        unit_name="Fatty Acid and Nucleic Acids Metabolisms",
        strong_phrases=[
            "biosynthesis of fatty acids", "cholesterol biosynthesis",
            "fatty acid synthesis in the cytosol", "fatty acid biosynthesis with enzymatic pathway",
            "27 carbon atoms of cholesterol are derived from", "cholesterol affect cardiovascular health",
            "eicosanoids", "lipoproteins", "fatty acid synthase", "hmg-coa reductase", "ldl, hdl, vldl"
        ],
        specific_keywords=["cholesterol biosynthesis", "fatty acid synthase", "fatty acid biosynthesis", "eicosanoids", "lipoproteins", "hmg-coa", "ldl", "hdl"],
        negative_guards=["beta-oxidation", "purine and pyrimidine"]
    ),
    TaxonomyTopicRule(
        topic_id=279,
        topic_name="Purine and Pyrimidine Nucleotide Biosynthesis and Degradation",
        unit_id=85,
        unit_name="Fatty Acid and Nucleic Acids Metabolisms",
        strong_phrases=[
            "donor of activated ribose group for nucleotide biosynthesis",
            "biosynthesis of inosine monophosphate", "biosynthesis and degradation of purine and pyrimidine",
            "purine and pyrimidine", "salvage pathway", "de novo synthesis of purine",
            "prpp", "gout", "uric acid"
        ],
        specific_keywords=["purine", "pyrimidine", "inosine monophosphate", "salvage pathway", "prpp", "uric acid"],
        negative_guards=["fatty acid synthase", "cholesterol biosynthesis"]
    ),
]
