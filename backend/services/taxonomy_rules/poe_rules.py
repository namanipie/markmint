"""
Structured, data-driven taxonomy classification rules for Course 3: Philosophy Of Engineering (21GNH101J).
Maps 20 syllabus topics across 5 units using deterministic domain terminology.
Derived strictly from the official SRM IST Department of General Engineering Syllabus (21GNH101J),
faculty unit decks, end-semester exam pattern guides, and Ramapuram/KTR MCQ banks.
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

POE_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------------------
    # Unit 1 (id=3): Introduction to Philosophy of Engineering
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=100,
        topic_name="Definition and Scope of Engineering",
        unit_id=3,
        unit_name="Introduction to Philosophy of Engineering",
        strong_phrases=[
            "discipline and profession of applying technical and scientific knowledge",
            "applying technical and scientific knowledge and utilizing natural laws",
            "american engineers council for professional development",
            "ecpd", "definition of engineering", "focus of engineering",
            "solving practical problems", "scope of engineering"
        ],
        specific_keywords=["ecpd"],
        negative_guards=["habits of mind", "steam pyramid", "steam framework", "riasec", "addie", "cdio"]
    ),
    TaxonomyTopicRule(
        topic_id=101,
        topic_name="STEAM Pyramid and Interdisciplinary Education",
        unit_id=3,
        unit_name="Introduction to Philosophy of Engineering",
        strong_phrases=[
            "steam pyramid", "steam framework", "a in steam", "integration of arts into stem",
            "steam education", "pyramid of steam", "stem to steam", "arts into stem",
            "arts in the steam framework"
        ],
        specific_keywords=["steam"],
        negative_guards=["riasec", "cdio", "addie", "product life cycle"]
    ),
    TaxonomyTopicRule(
        topic_id=102,
        topic_name="Engineering Habits of Mind and Professional Attributes",
        unit_id=3,
        unit_name="Introduction to Philosophy of Engineering",
        strong_phrases=[
            "engineering habits of mind", "habits of mind", "desired attributes of an engineer",
            "attributes of an engineer", "systems thinking and collaboration",
            "essential skills for citizens in the 21st century", "creative problem solver"
        ],
        specific_keywords=["habits of mind"],
        negative_guards=["steam pyramid", "ontology", "epistemology", "axiology"]
    ),
    TaxonomyTopicRule(
        topic_id=103,
        topic_name="Historical Evolution and Eras of Engineering",
        unit_id=3,
        unit_name="Introduction to Philosophy of Engineering",
        strong_phrases=[
            "renaissance era", "ancient era", "middle era", "modern era",
            "history of engineering", "historical evolution of engineering",
            "evolution of engineering", "industrial revolution in engineering"
        ],
        specific_keywords=["renaissance era"],
        negative_guards=["product life cycle", "epistemology", "ontology"]
    ),

    # -------------------------------------------------------------------------
    # Unit 2 (id=50): Ontology of Engineering
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=104,
        topic_name="Philosophical Ontology and Nature of Artifacts",
        unit_id=50,
        unit_name="Ontology of Engineering",
        strong_phrases=[
            "science of being", "nature of artifacts", "engineered artifacts",
            "study of existence and reality", "branch of philosophy that studies concepts such as existence",
            "ontology of engineering", "philosophical ontology", "technical artifacts"
        ],
        specific_keywords=["science of being"],
        negative_guards=["reference ontology", "application ontology", "product life cycle", "epistemology", "axiology"]
    ),
    TaxonomyTopicRule(
        topic_id=105,
        topic_name="Reference Ontology and Application Ontology",
        unit_id=50,
        unit_name="Ontology of Engineering",
        strong_phrases=[
            "reference ontology", "application ontology", "viewpoint of an end-user in a particular domain",
            "reference ontologies", "application ontologies", "ro and ao",
            "end-user in a particular domain"
        ],
        specific_keywords=["reference ontology", "application ontology"],
        negative_guards=["product life cycle", "scientific method", "ethics"]
    ),
    TaxonomyTopicRule(
        topic_id=106,
        topic_name="Product Life Cycle and Developmental Stages",
        unit_id=50,
        unit_name="Ontology of Engineering",
        strong_phrases=[
            "product life cycle", "plc with diagram", "stages of product life cycle",
            "average selling price during the product life cycle", "decline stage",
            "maturity stage", "growth stage", "introduction stage of product"
        ],
        specific_keywords=["product life cycle"],
        negative_guards=["steam", "addie", "cdio", "riasec"]
    ),
    TaxonomyTopicRule(
        topic_id=107,
        topic_name="System Classification and Domain Modeling",
        unit_id=50,
        unit_name="Ontology of Engineering",
        strong_phrases=[
            "interoperability between engineering systems", "domain categorization",
            "domain modeling", "classification of engineering systems",
            "categorization of technical systems"
        ],
        specific_keywords=[],
        negative_guards=["four dimensions", "riasec", "ethics"]
    ),

    # -------------------------------------------------------------------------
    # Unit 3 (id=51): Epistemology of Engineering
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=108,
        topic_name="Relations Between Science, Technology, and Engineering",
        unit_id=51,
        unit_name="Epistemology of Engineering",
        strong_phrases=[
            "relationship between science, technology, and engineering",
            "relationship between science technology and engineering",
            "scientists study the world as it is", "engineers create the world that has never been",
            "differences between science, engineering, and technology",
            "differences between science engineering and technology",
            "sum of all engineered tools, devices and process"
        ],
        specific_keywords=["von karman"],
        negative_guards=["scientific method and engineering design process", "addie", "cdio", "four dimensions"]
    ),
    TaxonomyTopicRule(
        topic_id=109,
        topic_name="Four Dimensions of Engineering Practice",
        unit_id=51,
        unit_name="Epistemology of Engineering",
        strong_phrases=[
            "four dimensions of engineering", "4 dimensions of engineering",
            "completed job, which stands before the world",
            "dimensions of engineering with diagram", "technical knowledge and creativity dimensions"
        ],
        specific_keywords=["four dimensions of engineering"],
        negative_guards=["steam pyramid", "addie", "riasec", "plc"]
    ),
    TaxonomyTopicRule(
        topic_id=110,
        topic_name="RIASEC Model and Engineering Typology",
        unit_id=51,
        unit_name="Epistemology of Engineering",
        strong_phrases=[
            "riasec model", "riasec framework", "riasec vocational", "holland codes",
            "realistic, investigative, artistic, social, enterprising, conventional",
            "riasec model with diagram"
        ],
        specific_keywords=["riasec"],
        negative_guards=["steam", "addie", "cdio", "product life cycle"]
    ),
    TaxonomyTopicRule(
        topic_id=111,
        topic_name="Design Epistemology and Engineering Knowledge Base",
        unit_id=51,
        unit_name="Epistemology of Engineering",
        strong_phrases=[
            "design as epistemology", "design epistemology", "engineering knowledge base",
            "nature and complexity of the knowledge base in engineering",
            "rigour in engineering design", "tacit knowledge in engineering"
        ],
        specific_keywords=["design epistemology"],
        negative_guards=["addie", "cdio", "scientific method vs"]
    ),

    # -------------------------------------------------------------------------
    # Unit 4 (id=52): Methodology of Engineering
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=112,
        topic_name="Scientific Method vs Engineering Design Process",
        unit_id=52,
        unit_name="Methodology of Engineering",
        strong_phrases=[
            "scientific method and engineering design", "scientific method vs engineering design",
            "difference between scientific method and engineering design process",
            "difference between scientific method and engineering design",
            "scientists perform experiments using scientific method",
            "creativity-based engineering design process"
        ],
        specific_keywords=["scientific method vs engineering"],
        negative_guards=["addie", "cdio", "relationship between science, technology"]
    ),
    TaxonomyTopicRule(
        topic_id=113,
        topic_name="ADDIE Model and Instructional System Design",
        unit_id=52,
        unit_name="Methodology of Engineering",
        strong_phrases=[
            "addie model", "addie framework", "analysis, design, development, implementation, evaluation",
            "formative and summative evaluation", "addie model with diagram",
            "how addie model is useful"
        ],
        specific_keywords=["addie"],
        negative_guards=["cdio", "riasec", "steam", "product life cycle"]
    ),
    TaxonomyTopicRule(
        topic_id=114,
        topic_name="CDIO Framework in Industry and Practice",
        unit_id=52,
        unit_name="Methodology of Engineering",
        strong_phrases=[
            "cdio framework", "cdio methodology", "conceive, design, implement, operate",
            "cdio engineering", "full form of cdio", "cdio process",
            "cdio in industry with diagram"
        ],
        specific_keywords=["cdio"],
        negative_guards=["addie", "riasec", "steam"]
    ),
    TaxonomyTopicRule(
        topic_id=115,
        topic_name="Engineering Modeling and Problem Formulation",
        unit_id=52,
        unit_name="Methodology of Engineering",
        strong_phrases=[
            "engineering design process", "engineering modeling",
            "operational factors in system design", "problem formulation in engineering",
            "stages of engineering design process"
        ],
        specific_keywords=[],
        negative_guards=["scientific method", "addie", "cdio", "riasec"]
    ),

    # -------------------------------------------------------------------------
    # Unit 5 (id=53): Axiology of Engineering
    # -------------------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=116,
        topic_name="Engineering Ethics and Professional Codes of Conduct",
        unit_id=53,
        unit_name="Axiology of Engineering",
        strong_phrases=[
            "engineers code of ethics", "code of ethics", "faithful agents or trustees",
            "engineering ethics", "ethical considerations in engineering",
            "whistleblowing in engineering", "public safety, health, and welfare"
        ],
        specific_keywords=["code of ethics"],
        negative_guards=["3es", "sustainable development", "addie", "cdio"]
    ),
    TaxonomyTopicRule(
        topic_id=117,
        topic_name="Sustainable Development and Ecological Stewardship",
        unit_id=53,
        unit_name="Axiology of Engineering",
        strong_phrases=[
            "sustainable development", "aspect of sustainability",
            "environmental sustainability in engineering", "ecological stewardship",
            "case studies on sustainable development", "environmental compliance"
        ],
        specific_keywords=["sustainable development"],
        negative_guards=["concept of 3es", "code of ethics", "steam"]
    ),
    TaxonomyTopicRule(
        topic_id=118,
        topic_name="Concept of 3Es: Engineering, Economics, and Ethics",
        unit_id=53,
        unit_name="Axiology of Engineering",
        strong_phrases=[
            "concept of 3es", "3es with diagram", "engineering, economics, and ethics",
            "engineering economics and ethics", "3 es in engineering", "three es"
        ],
        specific_keywords=["3es", "three es"],
        negative_guards=["steam", "addie", "cdio"]
    ),
    TaxonomyTopicRule(
        topic_id=119,
        topic_name="Professional Engineering Societies and Social Responsibility",
        unit_id=53,
        unit_name="Axiology of Engineering",
        strong_phrases=[
            "professional engineering organizations", "professional organisation for engineering",
            "engineering and society", "socio-politics of technology",
            "social justice frameworks for engineering", "professional societies"
        ],
        specific_keywords=["professional engineering organizations"],
        negative_guards=["code of ethics", "3es", "scientific method"]
    ),
]
