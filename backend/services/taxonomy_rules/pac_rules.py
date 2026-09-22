"""
Taxonomy classification rules for Course 11: Physical And Analytical Chemistry (21CHC101J).
Derived directly from the official SRM IST Department of Chemistry Syllabus.

Unit 1 (id=11): Properties of Solutions (Topics 240-243)
Unit 2 (id=78): Chemical Equilibrium (Topics 244-247)
Unit 3 (id=79): Phase Equilibrium (Topics 248-251)
Unit 4 (id=80): Colloids and Photochemistry (Topics 252-255)
Unit 5 (id=81): Instrumental Methods of Analysis (Topics 256-259)
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

PAC_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------
    # UNIT 1: PROPERTIES OF SOLUTIONS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=240,
        topic_name="Ideal and Non-Ideal Solutions: Raoult's Law and Deviations",
        unit_id=11,
        unit_name="Properties of Solutions",
        strong_phrases=[
            "ideal solutions is false", "ideal solutions obey raoult", "non-ideal solutions",
            "raoult's law for ideal solutions", "raoult's law", "deviations from ideality",
            "completely miscible binary solutions"
        ],
        specific_keywords=["raoult", "non-ideal solutions", "ideal solutions"],
        negative_guards=["steam distillation", "phase diagram", "dew point"]
    ),
    TaxonomyTopicRule(
        topic_id=241,
        topic_name="Vapor Pressure-Composition and Boiling Point Phase Diagrams",
        unit_id=11,
        unit_name="Properties of Solutions",
        strong_phrases=[
            "bubble point and corresponding dew point", "pxy phase diagram",
            "boiling point-composition curves", "vapor pressure-composition",
            "azeotropic mixtures", "lever rule"
        ],
        specific_keywords=["bubble point", "dew point", "pxy", "lever rule"],
        negative_guards=["steam distillation", "triple point"]
    ),
    TaxonomyTopicRule(
        topic_id=242,
        topic_name="Distillation Techniques: Fractional, Immiscible, and Steam Distillation",
        unit_id=11,
        unit_name="Properties of Solutions",
        strong_phrases=[
            "distillation is the use of a third component", "steam distilled with water",
            "concept of steam distillation", "steam distillation", "fractional distillation",
            "distillation of immiscible liquids"
        ],
        specific_keywords=["steam distillation", "fractional distillation", "immiscible liquid"],
        negative_guards=["spectroscopy", "chromatography"]
    ),
    TaxonomyTopicRule(
        topic_id=243,
        topic_name="Colligative Properties and Molecular Weight Determination",
        unit_id=11,
        unit_name="Properties of Solutions",
        strong_phrases=[
            "colligative properties", "elevation in boiling point", "depression in freezing point",
            "relative lowering of vapour pressure", "osmosis and osmotic pressure",
            "determination of molecular weight from colligative properties"
        ],
        specific_keywords=["colligative", "osmotic pressure", "freezing point depression", "boiling point elevation"],
        negative_guards=["spectroscopy", "chemical equilibrium"]
    ),

    # -------------------------------------------------------------
    # UNIT 2: CHEMICAL EQUILIBRIUM
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=244,
        topic_name="Gibbs Free Energy, Chemical Potential, and Reaction Spontaneity",
        unit_id=78,
        unit_name="Chemical Equilibrium",
        strong_phrases=[
            "tend towards states of", "states of minimum gibbs free energy", "states of maximum gibbs", "feasible reaction is always spontaneous",
            "derive the expression delta g = - rt ln k", "gibbs free energy",
            "chemical potential", "free energy of a spontaneous reaction", "spontaneous reaction"
        ],
        specific_keywords=["chemical potential", "reaction spontaneity", "gibbs free energy"],
        negative_guards=["phase rule", "degrees of freedom"]
    ),
    TaxonomyTopicRule(
        topic_id=245,
        topic_name="Law of Mass Action and Thermodynamic Equilibrium Constants (Kp, Kc, Kx)",
        unit_id=78,
        unit_name="Chemical Equilibrium",
        strong_phrases=[
            "rate of forward reaction equals backward reaction", "rate of forward reaction",
            "calculate kp/kc for the following reactions", "relationship between kp, kc",
            "equilibrium constants: kp, kc", "law of mass action", "law of chemical equilibrium",
            "equilibrium constant k_p for the reaction"
        ],
        specific_keywords=["law of mass action", "equilibrium constant", "kp", "kc", "kx"],
        negative_guards=["van't hoff", "le chatelier"]
    ),
    TaxonomyTopicRule(
        topic_id=246,
        topic_name="Temperature and Pressure Dependence: Van't Hoff Equation",
        unit_id=78,
        unit_name="Chemical Equilibrium",
        strong_phrases=[
            "van't hoff equation", "temperature dependence of equilibrium constant",
            "pressure dependence of equilibrium constants", "van't hoff isochore"
        ],
        specific_keywords=["van't hoff", "isochore"],
        negative_guards=["le chatelier"]
    ),
    TaxonomyTopicRule(
        topic_id=247,
        topic_name="Le Chatelier's Principle and Dynamic Physical-Chemical Equilibria",
        unit_id=78,
        unit_name="Chemical Equilibrium",
        strong_phrases=[
            "le chatlier's principle states", "le chatelier's principle",
            "effect of change in concentration, temperature, and pressure",
            "le chatelier"
        ],
        specific_keywords=["le chatelier", "chatelier", "chatlier"],
        negative_guards=["phase rule", "spectroscopy"]
    ),

    # -------------------------------------------------------------
    # UNIT 3: PHASE EQUILIBRIUM
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=248,
        topic_name="Gibbs Phase Rule: Phases, Components, and Degrees of Freedom",
        unit_id=79,
        unit_name="Phase Equilibrium",
        strong_phrases=[
            "equilibrium for two phases", "thermodynamic equilibrium for two phases",
            "number of components is given mathematically by", "two degree of freedom is termed as",
            "degree of freedom", "gibbs phase rule", "conditions for equilibrium between phases",
            "bivariant system", "univariant system", "invariant system"
        ],
        specific_keywords=["degree of freedom", "degrees of freedom", "phase rule", "components is given"],
        negative_guards=["spectroscopy", "beer lamberts"]
    ),
    TaxonomyTopicRule(
        topic_id=249,
        topic_name="One-Component Systems: Water, CO2, and Sulphur Phase Diagrams",
        unit_id=79,
        unit_name="Phase Equilibrium",
        strong_phrases=[
            "at triple point; water exists in equilibrium", "triple point of water",
            "water system, co2 system, sulphur system", "one component systems",
            "triple point", "sulphur system", "water system phase diagram"
        ],
        specific_keywords=["triple point", "one-component", "one component system", "sulphur system"],
        negative_guards=["nernst distribution", "spectroscopy"]
    ),
    TaxonomyTopicRule(
        topic_id=250,
        topic_name="Three-Component Systems and Triangular Phase Diagrams",
        unit_id=79,
        unit_name="Phase Equilibrium",
        strong_phrases=[
            "three component systems", "triangular phase diagram",
            "acetic acid-chloroform-water system", "two salts and water system",
            "tie lines in triangular diagram"
        ],
        specific_keywords=["triangular phase diagram", "three component", "chloroform-water"],
        negative_guards=["nernst distribution law"]
    ),
    TaxonomyTopicRule(
        topic_id=251,
        topic_name="Nernst Distribution Law and Solute Association/Dissociation",
        unit_id=79,
        unit_name="Phase Equilibrium",
        strong_phrases=[
            "distribution of an organic solute between water", "association of molecules in organic phase",
            "nernst distribution law", "distribution co-efficient", "partition coefficient",
            "dissociation of the solute in one of the solvents"
        ],
        specific_keywords=["nernst distribution", "distribution coefficient", "partition coefficient", "distribution law"],
        negative_guards=["triple point", "spectroscopy"]
    ),

    # -------------------------------------------------------------
    # UNIT 4: COLLOIDS AND PHOTOCHEMISTRY
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=252,
        topic_name="Colloidal Dispersions: Classification, Tyndall Effect, and Brownian Movement",
        unit_id=80,
        unit_name="Colloids and Photochemistry",
        strong_phrases=[
            "smoke is an example of", "property of colloids that does not depend on the electrical charge",
            "dispersion medium in paint is", "tyndall effect and brownian movement",
            "tyndall effect", "brownian movement", "colloidal dispersions", "gels and emulsions"
        ],
        specific_keywords=["tyndall effect", "brownian movement", "dispersion medium", "colloids", "emulsions"],
        negative_guards=["zeta potential", "electrophoresis", "photochemistry"]
    ),
    TaxonomyTopicRule(
        topic_id=253,
        topic_name="Electrical and Electrokinetic Properties: Zeta Potential and Electrophoresis",
        unit_id=80,
        unit_name="Colloids and Photochemistry",
        strong_phrases=[
            "electrical double layer", "zeta potential", "electrokinetic properties of colloids",
            "electrophoresis and electro-osmosis", "electro-osmosis", "helmholtz electrical double layer"
        ],
        specific_keywords=["zeta potential", "electrophoresis", "electro-osmosis", "electrical double layer"],
        negative_guards=["quantum yield", "spectroscopy"]
    ),
    TaxonomyTopicRule(
        topic_id=254,
        topic_name="Laws of Photochemistry and Quantum Yield",
        unit_id=80,
        unit_name="Colloids and Photochemistry",
        strong_phrases=[
            "photochemical law that deals with photochemical equivalence", "three laws of photochemistry",
            "laws of photochemistry", "quantum yield", "grothus draper law", "stark-einstein law",
            "beer lambert's law", "photochemical equivalence"
        ],
        specific_keywords=["quantum yield", "photochemistry", "photochemical equivalence", "grothus draper", "stark-einstein"],
        negative_guards=["hydrogen-chlorine", "hydrogen-bromine"]
    ),
    TaxonomyTopicRule(
        topic_id=255,
        topic_name="Photochemical Kinetics: Hydrogen-Chlorine and Hydrogen-Bromine Reactions",
        unit_id=80,
        unit_name="Colloids and Photochemistry",
        strong_phrases=[
            "kinetics of hydrogen-chlorine reaction", "kinetics of hydrogen-bromine reaction",
            "hydrogen-chlorine reaction", "hydrogen-bromine reaction", "chain photochemical reaction",
            "photochemical rate law"
        ],
        specific_keywords=["hydrogen-chlorine", "hydrogen-bromine", "photochemical kinetics"],
        negative_guards=["colloids", "chromatography"]
    ),

    # -------------------------------------------------------------
    # UNIT 5: INSTRUMENTAL METHODS OF ANALYSIS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=256,
        topic_name="Analytical Measurement Errors, Accuracy, Precision, and Calibration",
        unit_id=81,
        unit_name="Instrumental Methods of Analysis",
        strong_phrases=[
            "difference between the measured value and the true value", "absolute error",
            "accuracy, precision, common errors", "calibration curves", "systematic errors and random errors"
        ],
        specific_keywords=["accuracy", "precision", "calibration curve", "measured value and the true value", "absolute error"],
        negative_guards=["spectroscopy", "chromatography"]
    ),
    TaxonomyTopicRule(
        topic_id=257,
        topic_name="Molecular Spectroscopy: UV-Vis and Infrared (IR) Spectroscopy",
        unit_id=81,
        unit_name="Instrumental Methods of Analysis",
        strong_phrases=[
            "uv spectroscopy uses the wavelength range", "ir spectroscopy is also termed as",
            "working of double beam uv spectrophotometer", "uv-vis spectroscopy",
            "infra-red spectroscopy", "vibrational spectroscopy", "double beam uv"
        ],
        specific_keywords=["uv-vis", "uv spectroscopy", "ir spectroscopy", "vibrational spectroscopy", "spectrophotometer"],
        negative_guards=["atomic absorption spectroscopy", "chromatography"]
    ),
    TaxonomyTopicRule(
        topic_id=258,
        topic_name="Atomic Absorption Spectroscopy and Optical Instrumentation",
        unit_id=81,
        unit_name="Instrumental Methods of Analysis",
        strong_phrases=[
            "atomic absorption spectroscopy is used for analysis of", "atomic absorption spectroscopy",
            "hollow cathode lamp", "optical methods (light source/monochromator",
            "flame atomization"
        ],
        specific_keywords=["atomic absorption", "atomic absorption spectroscopy", "monochromator"],
        negative_guards=["chromatography", "ir spectroscopy"]
    ),
    TaxonomyTopicRule(
        topic_id=259,
        topic_name="Chromatographic Separation Techniques: TLC, GC, and HPLC",
        unit_id=81,
        unit_name="Instrumental Methods of Analysis",
        strong_phrases=[
            "list at least two chromatographic methods", "chromatographic techniques",
            "column chromatography", "paper chromatography", "thin layer chromatography",
            "gas chromatography", "high performance liquid chromatography", "hplc", "tlc"
        ],
        specific_keywords=["chromatography", "chromatographic", "hplc", "gas chromatography"],
        negative_guards=["spectroscopy", "photochemistry"]
    ),
]
