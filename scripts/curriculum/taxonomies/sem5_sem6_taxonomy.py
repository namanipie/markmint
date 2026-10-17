"""
Authoritative Curriculum Taxonomy and Classification Rules for SRMIST Regulation 2021:
- Course 32: Discrete Mathematics (SEM5-DM / 21MAB301T)
- Course 33: Formal Languages and Automata (SEM5-FLA / 21CSC301T)
- Course 34: Computer Networks (SEM5-CN / 21CSC302J)
- Course 35: Software Engineering and Project Management (SEM6-SEPM / 21CSC303J)
- Course 36: Compiler Design (SEM6-CD / 21CSC305J)
- Course 37: Data Science (SEM6-DS / 21CSC304P)
"""

COURSES_TAXONOMY = [
    {
        "id": 32,
        "name": "Discrete Mathematics",
        "code": "SEM5-DM",
        "canonical_code": "21MAB301T",
        "regulation_year": 2021,
        "department": "Mathematics",
        "semester": 5,
        "description": "Discrete Mathematics covers mathematical logic, propositional calculus, combinatorics, counting techniques, relations, functions, algebraic structures, lattices, and graph theory under SRMIST Regulation 2021.",
        "units": [
            {
                "number": 1,
                "name": "Mathematical Logic and Propositional Calculus",
                "topics": [
                    "Propositional Logic and Connectives",
                    "Truth Tables and Logical Equivalences",
                    "Normal Forms (PCNF and PDNF)",
                    "Predicates and Quantifiers",
                    "Rules of Inference and Proof Techniques"
                ]
            },
            {
                "number": 2,
                "name": "Combinatorics and Counting Techniques",
                "topics": [
                    "Mathematical Induction",
                    "Pigeonhole Principle and Inclusion-Exclusion",
                    "Permutations and Combinations",
                    "Generating Functions",
                    "Recurrence Relations and Characteristic Roots"
                ]
            },
            {
                "number": 3,
                "name": "Set Theory, Relations, and Functions",
                "topics": [
                    "Sets and Set Operations",
                    "Binary Relations and Equivalence Relations",
                    "Partitions and Equivalence Classes",
                    "Partial Ordering Relations and Hasse Diagrams",
                    "Functions, Injections, Surjections, and Bijections"
                ]
            },
            {
                "number": 4,
                "name": "Algebraic Structures",
                "topics": [
                    "Semigroups and Monoids",
                    "Groups, Subgroups, and Abelian Groups",
                    "Cyclic Groups and Cosets",
                    "Lagrange's Theorem",
                    "Group Homomorphism and Normal Subgroups"
                ]
            },
            {
                "number": 5,
                "name": "Lattices and Graph Theory",
                "topics": [
                    "Lattices as Posets and Properties of Lattices",
                    "Boolean Algebra and Karnaugh Maps",
                    "Graphs, Subgraphs, and Degree Sequences",
                    "Eulerian and Hamiltonian Graphs",
                    "Trees, Spanning Trees, and Graph Isomorphism"
                ]
            }
        ],
        "mapping_keywords": ["discrete mathematics", "discrete structures", "discrete math"],
        "curriculum_filter": lambda name: "discrete" in name.lower() and "math" in name.lower()
    },
    {
        "id": 33,
        "name": "Formal Languages and Automata",
        "code": "SEM5-FLA",
        "canonical_code": "21CSC301T",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 5,
        "description": "Formal Languages and Automata covers finite state machines, regular expressions, context-free languages, pushdown automata, Turing machines, decidability, and computational complexity under SRMIST Regulation 2021.",
        "units": [
            {
                "number": 1,
                "name": "Finite Automata and Regular Expressions",
                "topics": [
                    "Deterministic Finite Automata (DFA)",
                    "Nondeterministic Finite Automata (NFA) and Equivalence",
                    "Regular Expressions and Regular Languages",
                    "Pumping Lemma for Regular Languages",
                    "Equivalence and Minimization of Finite Automata"
                ]
            },
            {
                "number": 2,
                "name": "Grammars and Chomsky Hierarchy",
                "topics": [
                    "Chomsky Hierarchy of Formal Languages",
                    "Context-Free Grammars (CFG) and Parse Trees",
                    "Ambiguity in Context-Free Grammars",
                    "Simplification of Grammars (Useless, Epsilon, Unit)",
                    "Chomsky Normal Form (CNF) and Greibach Normal Form (GNF)"
                ]
            },
            {
                "number": 3,
                "name": "Pushdown Automata (PDA)",
                "topics": [
                    "Pushdown Automata Formal Definition and Configurations",
                    "Deterministic vs Nondeterministic Pushdown Automata",
                    "Equivalence of PDA and Context-Free Grammars",
                    "Pumping Lemma for Context-Free Languages",
                    "Closure Properties of Context-Free Languages"
                ]
            },
            {
                "number": 4,
                "name": "Turing Machines",
                "topics": [
                    "Turing Machine Formal Definition and State Transition Diagrams",
                    "Techniques for Turing Machine Construction",
                    "Multi-tape and Nondeterministic Turing Machines",
                    "Church-Turing Thesis and Computability",
                    "Universal Turing Machine"
                ]
            },
            {
                "number": 5,
                "name": "Undecidability and Complexity Theory",
                "topics": [
                    "Decidable and Undecidable Problems",
                    "Halting Problem and Rice's Theorem",
                    "Post Correspondence Problem (PCP)",
                    "Recursive and Recursively Enumerable Languages",
                    "Computational Complexity Classes (P, NP, NP-Complete)"
                ]
            }
        ],
        "mapping_keywords": ["formal language", "automata", "theory of computation"],
        "curriculum_filter": lambda name: "automata" in name.lower() or "formal language" in name.lower() or "computation theory" in name.lower()
    },
    {
        "id": 34,
        "name": "Computer Networks",
        "code": "SEM5-CN",
        "canonical_code": "21CSC302J",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 5,
        "description": "Computer Networks provides foundational and practical principles of network architectures, physical and link protocols, IP routing, TCP/UDP transport mechanics, and application-layer services under SRMIST Regulation 2021.",
        "units": [
            {
                "number": 1,
                "name": "Physical and Data Link Layer",
                "topics": [
                    "OSI Reference Model and TCP/IP Architecture",
                    "Framing, Flow Control, and Error Detection (CRC, Checksum)",
                    "Sliding Window Protocols (Go-Back-N, Selective Repeat)",
                    "Multiple Access Protocols (ALOHA, CSMA/CD, CSMA/CA)",
                    "Ethernet Standards and IEEE 802.11 Wireless LAN"
                ]
            },
            {
                "number": 2,
                "name": "Network Layer: Data Plane and Addressing",
                "topics": [
                    "IPv4 and IPv6 Addressing and Subnetting",
                    "Classless Inter-Domain Routing (CIDR) and VLSM",
                    "NAT, DHCP, and ICMP Protocols",
                    "Packet Switching and Datagram Forwarding",
                    "Address Resolution Protocol (ARP and RARP)"
                ]
            },
            {
                "number": 3,
                "name": "Network Layer: Control Plane and Routing",
                "topics": [
                    "Routing Principles and Graph Abstractions",
                    "Distance Vector Routing and RIP Protocol",
                    "Link State Routing and OSPF Protocol",
                    "Border Gateway Protocol (BGP) and Inter-AS Routing",
                    "Software-Defined Networking (SDN) Fundamentals"
                ]
            },
            {
                "number": 4,
                "name": "Transport Layer",
                "topics": [
                    "Transport Layer Services and Multiplexing/Demultiplexing",
                    "User Datagram Protocol (UDP) Principles",
                    "TCP Connection Management (3-Way Handshake and Teardown)",
                    "Principles of Reliable Data Transfer (Stop-and-Wait, Pipelining)",
                    "TCP Congestion Control, Slow Start, and Flow Control"
                ]
            },
            {
                "number": 5,
                "name": "Application Layer and Network Security",
                "topics": [
                    "Domain Name System (DNS) Architecture and Operation",
                    "Web Architecture and HTTP/HTTPS Protocols",
                    "Electronic Mail Protocols (SMTP, POP3, IMAP)",
                    "Cryptography Basics (Symmetric and Asymmetric Encryption)",
                    "Network Security Protocols (SSL/TLS, IPsec, Firewalls)"
                ]
            }
        ],
        "mapping_keywords": ["computer network", "computer networks", "data communication and networks"],
        "curriculum_filter": lambda name: "computer network" in name.lower() or ("network" in name.lower() and "neural" not in name.lower() and "wireless" not in name.lower())
    },
    {
        "id": 35,
        "name": "Software Engineering and Project Management",
        "code": "SEM6-SEPM",
        "canonical_code": "21CSC303J",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 6,
        "description": "Software Engineering and Project Management covers software process models, agile principles, requirements elicitation, architectural design, verification and testing, risk analysis, and project metrics under SRMIST Regulation 2021.",
        "units": [
            {
                "number": 1,
                "name": "Software Process Models and Agile Methodologies",
                "topics": [
                    "Software Process Models (Waterfall, Incremental, RAD, Spiral)",
                    "Agile Development Philosophy and Agile Manifesto",
                    "Scrum Framework, Sprints, and Roles",
                    "Extreme Programming (XP) and Kanban",
                    "DevOps Concepts and Continuous Integration/Continuous Deployment"
                ]
            },
            {
                "number": 2,
                "name": "Requirements Engineering and Modeling",
                "topics": [
                    "Requirements Elicitation, Analysis, and Validation",
                    "Software Requirements Specification (SRS) Guidelines",
                    "Use Case Modeling and Actor Identification",
                    "UML Structural and Behavioral Diagrams",
                    "Data Flow Diagrams (DFD) and State Transition Diagrams"
                ]
            },
            {
                "number": 3,
                "name": "Architectural and Detailed Design",
                "topics": [
                    "Software Design Concepts and Modularity (Cohesion and Coupling)",
                    "Architectural Styles and Patterns (Layered, Client-Server, Microservices)",
                    "Object-Oriented Design Principles (SOLID)",
                    "Component-Level Design and Interface Specifications",
                    "User Interface Design Principles and Usability Engineering"
                ]
            },
            {
                "number": 4,
                "name": "Software Testing and Quality Assurance",
                "topics": [
                    "Verification and Validation Principles",
                    "White-Box Testing (Basis Path, Control Structure)",
                    "Black-Box Testing (Equivalence Partitioning, Boundary Value)",
                    "Integration, System, and Regression Testing Strategies",
                    "Software Quality Attributes, SQA Plans, and CMMI Levels"
                ]
            },
            {
                "number": 5,
                "name": "Software Project Management and Maintenance",
                "topics": [
                    "Project Planning, Scheduling, and Work Breakdown Structure (WBS)",
                    "Software Cost and Effort Estimation (COCOMO I & II, Function Points)",
                    "Risk Management, RMMM Plan, and Contingency Planning",
                    "Software Configuration Management (SCM) and Version Control",
                    "Software Maintenance, Reverse Engineering, and Re-engineering"
                ]
            }
        ],
        "mapping_keywords": ["software engineering", "software engineering and project management", "sepm"],
        "curriculum_filter": lambda name: "software engineering" in name.lower()
    },
    {
        "id": 36,
        "name": "Compiler Design",
        "code": "SEM6-CD",
        "canonical_code": "21CSC305J",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 6,
        "description": "Compiler Design covers the architecture of language translators, lexical tokenization, context-free parsing algorithms, syntax-directed translation, symbol tables, intermediate code representation, and code optimization under SRMIST Regulation 2021.",
        "units": [
            {
                "number": 1,
                "name": "Introduction to Compilers and Lexical Analysis",
                "topics": [
                    "Phases of a Compiler and Compiler Construction Tools",
                    "Lexical Analysis and Token Recognition",
                    "Input Buffering Techniques (One-Buffer, Two-Buffer)",
                    "Regular Expressions to Finite Automata (Thompson Construction)",
                    "Lexical Analyzer Generators (LEX / Flex)"
                ]
            },
            {
                "number": 2,
                "name": "Syntax Analysis: Top-Down and Bottom-Up Parsing",
                "topics": [
                    "Context-Free Grammars and Ambiguity in Parsing",
                    "Top-Down Parsing and LL(1) Grammars (First and Follow Sets)",
                    "Recursive Descent and Non-Recursive Predictive Parsers",
                    "Bottom-Up Parsing and Shift-Reduce Conflicts",
                    "LR Parsers (SLR, Canonical LR, LALR) and YACC"
                ]
            },
            {
                "number": 3,
                "name": "Syntax-Directed Translation and Intermediate Code",
                "topics": [
                    "Syntax-Directed Definitions (Synthesized and Inherited Attributes)",
                    "Evaluation Orders for SDDs and Dependency Graphs",
                    "Intermediate Code Representations (Syntax Trees, DAGs, Three-Address Code)",
                    "Translation of Expressions, Boolean Statements, and Control Flow",
                    "Backpatching for Boolean Expressions and Flow-of-Control"
                ]
            },
            {
                "number": 4,
                "name": "Type Checking and Runtime Storage Environments",
                "topics": [
                    "Type Systems and Type Checking Rules",
                    "Equivalence of Type Expressions and Type Conversions",
                    "Runtime Storage Organization and Memory Allocation",
                    "Activation Records and Stack Allocation Strategy",
                    "Heap Management, Parameter Passing, and Garbage Collection"
                ]
            },
            {
                "number": 5,
                "name": "Code Optimization and Code Generation",
                "topics": [
                    "Principal Sources of Optimization (Common Subexpression, Dead Code)",
                    "Basic Blocks and Flow Graphs Construction",
                    "Loop Optimization (Code Motion, Induction Variables)",
                    "Data-Flow Analysis Frameworks",
                    "Code Generator Design, Target Code Issues, and Register Allocation"
                ]
            }
        ],
        "mapping_keywords": ["compiler design", "compilers", "compiler construction"],
        "curriculum_filter": lambda name: "compiler" in name.lower()
    },
    {
        "id": 37,
        "name": "Data Science",
        "code": "SEM6-DS",
        "canonical_code": "21CSC304P",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 6,
        "description": "Data Science covers the full data science lifecycle, exploratory statistical analysis, supervised prediction, clustering, dimensionality reduction, distributed big data architectures, and ethical data governance under SRMIST Regulation 2021.",
        "units": [
            {
                "number": 1,
                "name": "Data Science Foundations and Data Wrangling",
                "topics": [
                    "Data Science Lifecycle and Workflow",
                    "NumPy for High-Performance Vector Computations",
                    "Pandas DataFrames and Series Operations",
                    "Data Cleaning, Missing Value Imputation, and Normalization",
                    "Data Transformation, Reshaping, and Feature Extraction"
                ]
            },
            {
                "number": 2,
                "name": "Exploratory Data Analysis and Statistical Inference",
                "topics": [
                    "Descriptive Statistics and Measures of Dispersion",
                    "Exploratory Visualization with Matplotlib and Seaborn",
                    "Probability Distributions in Data Analysis (Normal, Binomial)",
                    "Hypothesis Testing, P-Values, and Confidence Intervals",
                    "Correlation, Covariance, and Bivariate Analysis"
                ]
            },
            {
                "number": 3,
                "name": "Supervised Learning and Model Evaluation",
                "topics": [
                    "Linear Regression and Polynomial Regression",
                    "Logistic Regression for Binary and Multi-Class Classification",
                    "Model Evaluation Metrics (Confusion Matrix, Precision, Recall, ROC-AUC)",
                    "Cross-Validation Strategies (K-Fold, Stratified)",
                    "Overfitting, Regularization (Ridge, Lasso), and Bias-Variance Tradeoff"
                ]
            },
            {
                "number": 4,
                "name": "Unsupervised Learning and Dimensionality Reduction",
                "topics": [
                    "K-Means Clustering and Cluster Quality (Elbow, Silhouette)",
                    "Hierarchical Clustering (Agglomerative, Dendrograms)",
                    "Principal Component Analysis (PCA) and Eigen-Decomposition",
                    "Singular Value Decomposition (SVD)",
                    "Association Rule Mining and Apriori Algorithm"
                ]
            },
            {
                "number": 5,
                "name": "Big Data Frameworks and Data Ethics",
                "topics": [
                    "Big Data Characteristics (Volume, Velocity, Variety)",
                    "Hadoop Architecture, HDFS, and MapReduce Paradigm",
                    "Apache Spark Fundamentals and Resilient Distributed Datasets (RDDs)",
                    "Data Privacy, Security Regulations, and GDPR",
                    "Model Fairness, Algorithmic Bias, and Ethical AI Governance"
                ]
            }
        ],
        "mapping_keywords": ["data science", "introduction to data science"],
        "curriculum_filter": lambda name: "data science" in name.lower() and "hydrology" not in name.lower()
    }
]

TOPIC_CLASSIFICATION_RULES = {
    # Course 32: Discrete Mathematics
    32: [
        # Unit 1: Mathematical Logic and Propositional Calculus
        (1, "Propositional Logic and Connectives", [r"proposition", r"connective", r"truth value", r"conditional statement", r"biconditional", r"negation", r"conjunction", r"disjunction"]),
        (1, "Truth Tables and Logical Equivalences", [r"truth table", r"tautolog", r"contradiction", r"logical equivalence", r"de morgan", r"distributive law"]),
        (1, "Normal Forms (PCNF and PDNF)", [r"pcnf", r"pdnf", r"principal conjunctive", r"principal disjunctive", r"conjunctive normal", r"disjunctive normal", r"minterm", r"maxterm"]),
        (1, "Predicates and Quantifiers", [r"predicate", r"quantifier", r"existential", r"universal quantifier", r"free variable", r"bound variable"]),
        (1, "Rules of Inference and Proof Techniques", [r"rule of inference", r"modus ponens", r"modus tollens", r"hypothetical syllogism", r"direct proof", r"indirect proof", r"proof by contradiction"]),

        # Unit 2: Combinatorics and Counting Techniques
        (2, "Mathematical Induction", [r"mathematical induction", r"inductive step", r"basis step", r"strong induction"]),
        (2, "Pigeonhole Principle and Inclusion-Exclusion", [r"pigeonhole", r"inclusion[- ]exclusion", r"generalized pigeonhole"]),
        (2, "Permutations and Combinations", [r"permutation", r"combination", r"binomial coefficient", r"multinomial"]),
        (2, "Generating Functions", [r"generating function", r"ordinary generating", r"coefficient of x\^", r"closed form of generating"]),
        (2, "Recurrence Relations and Characteristic Roots", [r"recurrence relation", r"characteristic root", r"characteristic equation", r"homogeneous recurrence", r"fibonacci", r"particular solution.*recurrence"]),

        # Unit 3: Set Theory, Relations, and Functions
        (3, "Sets and Set Operations", [r"set theory", r"power set", r"cartesian product", r"venn diagram", r"subset"]),
        (3, "Binary Relations and Equivalence Relations", [r"binary relation", r"reflexive", r"symmetric", r"transitive", r"equivalence relation", r"antisymmetric"]),
        (3, "Partitions and Equivalence Classes", [r"equivalence class", r"partition of a set", r"quotient set"]),
        (3, "Partial Ordering Relations and Hasse Diagrams", [r"partial order", r"poset", r"hasse diagram", r"maximal element", r"minimal element", r"greatest lower bound", r"least upper bound", r"glb", r"lub"]),
        (3, "Functions, Injections, Surjections, and Bijections", [r"injective", r"surjective", r"bijective", r"one[- ]to[- ]one", r"onto", r"composition of function", r"inverse function"]),

        # Unit 4: Algebraic Structures
        (4, "Semigroups and Monoids", [r"semigroup", r"monoid", r"associativity", r"identity element"]),
        (4, "Groups, Subgroups, and Abelian Groups", [r"\bgroup\b", r"abelian group", r"subgroup", r"inverse element", r"order of an element", r"order of a group"]),
        (4, "Cyclic Groups and Cosets", [r"cyclic group", r"generator of cyclic", r"coset", r"left coset", r"right coset"]),
        (4, "Lagrange's Theorem", [r"lagrange'?s theorem", r"order of subgroup divides"]),
        (4, "Group Homomorphism and Normal Subgroups", [r"homomorphism", r"isomorphism", r"kernel of homomorphism", r"normal subgroup", r"quotient group"]),

        # Unit 5: Lattices and Graph Theory
        (5, "Lattices as Posets and Properties of Lattices", [r"lattice", r"distributive lattice", r"complemented lattice", r"sublattice", r"modular lattice"]),
        (5, "Boolean Algebra and Karnaugh Maps", [r"boolean algebra", r"boolean function", r"boolean expression", r"karnaugh map", r"k[- ]map", r"sop", r"pos"]),
        (5, "Graphs, Subgraphs, and Degree Sequences", [r"graph", r"subgraph", r"degree sequence", r"handshaking lemma", r"regular graph", r"bipartite graph", r"complete graph"]),
        (5, "Eulerian and Hamiltonian Graphs", [r"euler", r"eulerian path", r"eulerian circuit", r"hamilton", r"hamiltonian cycle", r"hamiltonian graph", r"dirac'?s theorem"]),
        (5, "Trees, Spanning Trees, and Graph Isomorphism", [r"tree", r"spanning tree", r"graph isomorphism", r"isomorphic graph", r"binary tree", r"chromatic number", r"graph coloring"])
    ],

    # Course 33: Formal Languages and Automata
    33: [
        # Unit 1: Finite Automata and Regular Expressions
        (1, "Deterministic Finite Automata (DFA)", [r"\bdfa\b", r"deterministic finite", r"dfa transition", r"string accepted by dfa"]),
        (1, "Nondeterministic Finite Automata (NFA) and Equivalence", [r"\bnfa\b", r"nondeterministic finite", r"epsilon[- ]nfa", r"\b[εe][- ]closure\b", r"convert.*nfa.*dfa"]),
        (1, "Regular Expressions and Regular Languages", [r"regular expression", r"regular language", r"regular set", r"regex", r"arden'?s theorem"]),
        (1, "Pumping Lemma for Regular Languages", [r"pumping lemma for regular", r"pumping lemma.*not regular", r"show that.*is not regular"]),
        (1, "Equivalence and Minimization of Finite Automata", [r"minimization of dfa", r"myhill[- ]nerode", r"table filling algorithm", r"equivalent states"]),

        # Unit 2: Grammars and Chomsky Hierarchy
        (2, "Chomsky Hierarchy of Formal Languages", [r"chomsky hierarchy", r"type[- ][0-3] grammar", r"unrestricted grammar", r"context[- ]sensitive"]),
        (2, "Context-Free Grammars (CFG) and Parse Trees", [r"context[- ]free grammar", r"\bcfg\b", r"derivation tree", r"parse tree", r"leftmost derivation", r"rightmost derivation"]),
        (2, "Ambiguity in Context-Free Grammars", [r"ambiguous grammar", r"ambiguity", r"inherently ambiguous"]),
        (2, "Simplification of Grammars (Useless, Epsilon, Unit)", [r"useless symbol", r"unit production", r"epsilon production", r"null production", r"simplification of cfg"]),
        (2, "Chomsky Normal Form (CNF) and Greibach Normal Form (GNF)", [r"chomsky normal form", r"\bcnf\b", r"greibach normal form", r"\bgnf\b", r"convert.*to cnf", r"convert.*to gnf"]),

        # Unit 3: Pushdown Automata (PDA)
        (3, "Pushdown Automata Formal Definition and Configurations", [r"pushdown automata", r"\bpda\b", r"instantaneous description", r"transition function.*pda", r"stack operation"]),
        (3, "Deterministic vs Nondeterministic Pushdown Automata", [r"\bdpda\b", r"\bnpda\b", r"deterministic pda", r"acceptance by final state", r"acceptance by empty stack"]),
        (3, "Equivalence of PDA and Context-Free Grammars", [r"pda to cfg", r"cfg to pda", r"equivalence of pda"]),
        (3, "Pumping Lemma for Context-Free Languages", [r"pumping lemma for cfl", r"pumping lemma.*context[- ]free", r"show that.*is not context[- ]free"]),
        (3, "Closure Properties of Context-Free Languages", [r"closure property.*cfl", r"cfl is closed under", r"decision properties of cfl"]),

        # Unit 4: Turing Machines
        (4, "Turing Machine Formal Definition and State Transition Diagrams", [r"turing machine", r"\btm\b", r"transition table.*tm", r"design a turing machine", r"tm to compute"]),
        (4, "Techniques for Turing Machine Construction", [r"storage in state", r"multiple tracks", r"subroutines.*tm", r"shifting over"]),
        (4, "Multi-tape and Nondeterministic Turing Machines", [r"multi[- ]tape turing", r"nondeterministic turing", r"multi[- ]head tm", r"two[- ]way infinite tape"]),
        (4, "Church-Turing Thesis and Computability", [r"church[- ]turing thesis", r"computability", r"turing computable"]),
        (4, "Universal Turing Machine", [r"universal turing machine", r"\butm\b", r"encoding of turing machine"]),

        # Unit 5: Undecidability and Complexity Theory
        (5, "Decidable and Undecidable Problems", [r"undecidable", r"decidable", r"decision problem", r"halting problem", r"diagonalization language"]),
        (5, "Halting Problem and Rice's Theorem", [r"halting problem", r"rice'?s theorem"]),
        (5, "Post Correspondence Problem (PCP)", [r"post correspondence problem", r"\bpcp\b", r"modified pcp", r"\bmpcp\b"]),
        (5, "Recursive and Recursively Enumerable Languages", [r"recursively enumerable", r"recursive language", r"\bre\b language", r"non[- ]recursively enumerable"]),
        (5, "Computational Complexity Classes (P, NP, NP-Complete)", [r"complexity class", r"\bnp[- ]complete\b", r"\bnp[- ]hard\b", r"\bp\b and \bnp\b", r"cook'?s theorem", r"polynomial time reduction"])
    ],

    # Course 34: Computer Networks
    34: [
        # Unit 1: Physical and Data Link Layer
        (1, "OSI Reference Model and TCP/IP Architecture", [r"osi model", r"tcp/ip model", r"osi reference", r"layers of osi", r"encapsulation"]),
        (1, "Framing, Flow Control, and Error Detection (CRC, Checksum)", [r"framing", r"bit stuffing", r"byte stuffing", r"crc", r"cyclic redundancy check", r"checksum", r"parity check", r"hamming code"]),
        (1, "Sliding Window Protocols (Go-Back-N, Selective Repeat)", [r"sliding window", r"go[- ]back[- ]n", r"selective repeat", r"stop[- ]and[- ]wait", r"arq", r"piggybacking"]),
        (1, "Multiple Access Protocols (ALOHA, CSMA/CD, CSMA/CA)", [r"multiple access", r"aloha", r"slotted aloha", r"pure aloha", r"csma/cd", r"csma/ca", r"collision detection", r"collision avoidance", r"exponential backoff"]),
        (1, "Ethernet Standards and IEEE 802.11 Wireless LAN", [r"ethernet", r"ieee 802\.11", r"wireless lan", r"wifi", r"mac sublayer", r"bridge", r"switch"]),

        # Unit 2: Network Layer: Data Plane and Addressing
        (2, "IPv4 and IPv6 Addressing and Subnetting", [r"ipv4", r"ipv6", r"subnetting", r"subnet mask", r"classful addressing", r"classless addressing", r"ip header"]),
        (2, "Classless Inter-Domain Routing (CIDR) and VLSM", [r"cidr", r"vlsm", r"prefix length", r"supernetting", r"address allocation"]),
        (2, "NAT, DHCP, and ICMP Protocols", [r"\bnat\b", r"network address translation", r"dhcp", r"dynamic host", r"icmp", r"ping", r"traceroute"]),
        (2, "Packet Switching and Datagram Forwarding", [r"packet switching", r"circuit switching", r"datagram forwarding", r"virtual circuit", r"router architecture"]),
        (2, "Address Resolution Protocol (ARP and RARP)", [r"\barp\b", r"\brarp\b", r"address resolution protocol", r"arp table", r"arp cache", r"mac to ip"]),

        # Unit 3: Network Layer: Control Plane and Routing
        (3, "Routing Principles and Graph Abstractions", [r"routing algorithm", r"shortest path", r"dijkstra", r"bellman[- ]ford", r"flooding"]),
        (3, "Distance Vector Routing and RIP Protocol", [r"distance vector", r"\brip\b protocol", r"count[- ]to[- ]infinity", r"poison reverse"]),
        (3, "Link State Routing and OSPF Protocol", [r"link state", r"\bospf\b", r"lsa", r"area in ospf"]),
        (3, "Border Gateway Protocol (BGP) and Inter-AS Routing", [r"\bbgp\b", r"border gateway protocol", r"inter[- ]as", r"autonomous system", r"path vector"]),
        (3, "Software-Defined Networking (SDN) Fundamentals", [r"software[- ]defined", r"\bsdn\b", r"openflow", r"control plane separation"]),

        # Unit 4: Transport Layer
        (4, "Transport Layer Services and Multiplexing/Demultiplexing", [r"transport layer", r"multiplexing", r"demultiplexing", r"port number", r"socket"]),
        (4, "User Datagram Protocol (UDP) Principles", [r"\budp\b", r"user datagram protocol", r"connectionless transport", r"udp header"]),
        (4, "TCP Connection Management (3-Way Handshake and Teardown)", [r"three[- ]way handshake", r"tcp connection", r"connection teardown", r"syn", r"ack", r"fin"]),
        (4, "Principles of Reliable Data Transfer (Stop-and-Wait, Pipelining)", [r"reliable data transfer", r"rdt", r"sequence number", r"acknowledgement number"]),
        (4, "TCP Congestion Control, Slow Start, and Flow Control", [r"congestion control", r"slow start", r"congestion avoidance", r"fast retransmit", r"fast recovery", r"flow control", r"receive window"]),

        # Unit 5: Application Layer and Network Security
        (5, "Domain Name System (DNS) Architecture and Operation", [r"dns", r"domain name system", r"dns query", r"dns resolver", r"root server", r"authoritative dns"]),
        (5, "Web Architecture and HTTP/HTTPS Protocols", [r"http", r"https", r"persistent connection", r"web caching", r"cookies", r"rest"]),
        (5, "Electronic Mail Protocols (SMTP, POP3, IMAP)", [r"smtp", r"pop3", r"imap", r"mime", r"mail user agent"]),
        (5, "Cryptography Basics (Symmetric and Asymmetric Encryption)", [r"cryptography", r"symmetric key", r"asymmetric key", r"\brsa\b", r"\baes\b", r"\bdes\b", r"public key", r"private key"]),
        (5, "Network Security Protocols (SSL/TLS, IPsec, Firewalls)", [r"ssl", r"tls", r"ipsec", r"firewall", r"packet filter", r"digital signature", r"message authentication"])
    ],

    # Course 35: Software Engineering and Project Management
    35: [
        # Unit 1: Software Process Models and Agile Methodologies
        (1, "Software Process Models (Waterfall, Incremental, RAD, Spiral)", [r"waterfall", r"incremental model", r"spiral model", r"rad model", r"v[- ]model", r"prototyping model"]),
        (1, "Agile Development Philosophy and Agile Manifesto", [r"agile", r"agile manifesto", r"agile principles", r"user story"]),
        (1, "Scrum Framework, Sprints, and Roles", [r"scrum", r"sprint", r"product owner", r"scrum master", r"product backlog", r"sprint backlog", r"burndown chart"]),
        (1, "Extreme Programming (XP) and Kanban", [r"extreme programming", r"\bxp\b", r"pair programming", r"test[- ]driven development", r"tdd", r"kanban"]),
        (1, "DevOps Concepts and Continuous Integration/Continuous Deployment", [r"devops", r"continuous integration", r"continuous delivery", r"continuous deployment", r"ci/cd"]),

        # Unit 2: Requirements Engineering and Modeling
        (2, "Requirements Elicitation, Analysis, and Validation", [r"requirements engineering", r"elicitation", r"functional requirement", r"non[- ]functional requirement"]),
        (2, "Software Requirements Specification (SRS) Guidelines", [r"srs", r"software requirements specification", r"ieee 830"]),
        (2, "Use Case Modeling and Actor Identification", [r"use case", r"actor", r"use case diagram", r"include relationship", r"extend relationship"]),
        (2, "UML Structural and Behavioral Diagrams", [r"uml", r"class diagram", r"sequence diagram", r"activity diagram", r"state machine diagram", r"package diagram"]),
        (2, "Data Flow Diagrams (DFD) and State Transition Diagrams", [r"dfd", r"data flow diagram", r"level 0 dfd", r"context diagram", r"data dictionary"]),

        # Unit 3: Architectural and Detailed Design
        (3, "Software Design Concepts and Modularity (Cohesion and Coupling)", [r"cohesion", r"coupling", r"modularity", r"abstraction", r"information hiding", r"high cohesion", r"loose coupling"]),
        (3, "Architectural Styles and Patterns (Layered, Client-Server, Microservices)", [r"architectural style", r"layered architecture", r"client[- ]server architecture", r"microservices", r"mvc", r"repository pattern"]),
        (3, "Object-Oriented Design Principles (SOLID)", [r"solid principles", r"single responsibility", r"open[- ]closed", r"liskov", r"interface segregation", r"dependency inversion"]),
        (3, "Component-Level Design and Interface Specifications", [r"component[- ]level design", r"interface design", r"design pattern"]),
        (3, "User Interface Design Principles and Usability Engineering", [r"ui design", r"user interface design", r"golden rules", r"usability"]),

        # Unit 4: Software Testing and Quality Assurance
        (4, "Verification and Validation Principles", [r"verification and validation", r"v&v", r"inspection", r"walkthrough"]),
        (4, "White-Box Testing (Basis Path, Control Structure)", [r"white[- ]box testing", r"basis path", r"cyclomatic complexity", r"control flow graph", r"branch coverage", r"statement coverage"]),
        (4, "Black-Box Testing (Equivalence Partitioning, Boundary Value)", [r"black[- ]box testing", r"equivalence partitioning", r"boundary value analysis", r"bva", r"cause[- ]effect graphing"]),
        (4, "Integration, System, and Regression Testing Strategies", [r"unit testing", r"integration testing", r"top[- ]down integration", r"bottom[- ]up integration", r"system testing", r"regression testing", r"acceptance testing"]),
        (4, "Software Quality Attributes, SQA Plans, and CMMI Levels", [r"sqa", r"software quality", r"cmmi", r"iso 9001", r"six sigma", r"quality metric"]),

        # Unit 5: Software Project Management and Maintenance
        (5, "Project Planning, Scheduling, and Work Breakdown Structure (WBS)", [r"project planning", r"wbs", r"work breakdown structure", r"gantt chart", r"pert", r"cpm", r"critical path"]),
        (5, "Software Cost and Effort Estimation (COCOMO I & II, Function Points)", [r"cocomo", r"constructive cost model", r"function point", r"fpa", r"effort estimation", r"kloc"]),
        (5, "Risk Management, RMMM Plan, and Contingency Planning", [r"risk management", r"rmmm", r"risk identification", r"risk projection", r"risk mitigation"]),
        (5, "Software Configuration Management (SCM) and Version Control", [r"scm", r"software configuration management", r"baseline", r"version control", r"git", r"change control"]),
        (5, "Software Maintenance, Reverse Engineering, and Re-engineering", [r"software maintenance", r"corrective maintenance", r"adaptive maintenance", r"perfective maintenance", r"reverse engineering", r"re[- ]engineering"])
    ],

    # Course 36: Compiler Design
    36: [
        # Unit 1: Introduction to Compilers and Lexical Analysis
        (1, "Phases of a Compiler and Compiler Construction Tools", [r"phases of compiler", r"compiler construction", r"front end", r"back end", r"interpreter vs compiler"]),
        (1, "Lexical Analysis and Token Recognition", [r"lexical analy", r"token", r"lexeme", r"pattern", r"role of lexical"]),
        (1, "Input Buffering Techniques (One-Buffer, Two-Buffer)", [r"input buffer", r"sentinel", r"buffer pair", r"lookahead"]),
        (1, "Regular Expressions to Finite Automata (Thompson Construction)", [r"thompson construction", r"regex to nfa", r"regular expression.*automata"]),
        (1, "Lexical Analyzer Generators (LEX / Flex)", [r"\blex\b", r"\bflex\b", r"lex specification", r"lex program"]),

        # Unit 2: Syntax Analysis: Top-Down and Bottom-Up Parsing
        (2, "Context-Free Grammars and Ambiguity in Parsing", [r"cfg in parsing", r"ambiguous grammar.*parse", r"handle in parsing"]),
        (2, "Top-Down Parsing and LL(1) Grammars (First and Follow Sets)", [r"top[- ]down parsing", r"first and follow", r"ll\(1\)", r"predictive parsing table", r"left recursion", r"left factoring"]),
        (2, "Recursive Descent and Non-Recursive Predictive Parsers", [r"recursive descent", r"non[- ]recursive predictive", r"parsing table construction"]),
        (2, "Bottom-Up Parsing and Shift-Reduce Conflicts", [r"bottom[- ]up parsing", r"shift[- ]reduce", r"reduce[- ]reduce", r"handle pruning", r"operator precedence"]),
        (2, "LR Parsers (SLR, Canonical LR, LALR) and YACC", [r"\blr\b parser", r"\bslr\b", r"\bclr\b", r"\blalr\b", r"canonical collection of lr", r"yacc"]),

        # Unit 3: Syntax-Directed Translation and Intermediate Code
        (3, "Syntax-Directed Definitions (Synthesized and Inherited Attributes)", [r"syntax[- ]directed definition", r"\bsdd\b", r"synthesized attribute", r"inherited attribute"]),
        (3, "Evaluation Orders for SDDs and Dependency Graphs", [r"dependency graph", r"s[- ]attributed", r"l[- ]attributed", r"topological sort.*sdd"]),
        (3, "Intermediate Code Representations (Syntax Trees, DAGs, Three-Address Code)", [r"intermediate code", r"syntax tree", r"\bdag\b", r"three[- ]address code", r"quadruple", r"triple", r"indirect triple"]),
        (3, "Translation of Expressions, Boolean Statements, and Control Flow", [r"translation of expression", r"boolean expression.*translation", r"control flow translation"]),
        (3, "Backpatching for Boolean Expressions and Flow-of-Control", [r"backpatching", r"makelist", r"merge", r"backpatch"]),

        # Unit 4: Type Checking and Runtime Storage Environments
        (4, "Type Systems and Type Checking Rules", [r"type system", r"type checking", r"type expression", r"static type", r"dynamic type"]),
        (4, "Equivalence of Type Expressions and Type Conversions", [r"type equivalence", r"type conversion", r"type coercion", r"type error"]),
        (4, "Runtime Storage Organization and Memory Allocation", [r"runtime storage", r"memory organization", r"static allocation", r"stack allocation", r"heap allocation"]),
        (4, "Activation Records and Stack Allocation Strategy", [r"activation record", r"stack frame", r"control link", r"access link", r"display in runtime"]),
        (4, "Heap Management, Parameter Passing, and Garbage Collection", [r"heap management", r"parameter passing", r"call by value", r"call by reference", r"garbage collection"]),

        # Unit 5: Code Optimization and Code Generation
        (5, "Principal Sources of Optimization (Common Subexpression, Dead Code)", [r"code optimization", r"common subexpression", r"dead code elimination", r"copy propagation", r"constant folding"]),
        (5, "Basic Blocks and Flow Graphs Construction", [r"basic block", r"flow graph", r"leader", r"dominator", r"control flow analysis"]),
        (5, "Loop Optimization (Code Motion, Induction Variables)", [r"loop optimization", r"code motion", r"induction variable", r"reduction in strength", r"loop unrolling"]),
        (5, "Data-Flow Analysis Frameworks", [r"data[- ]flow analysis", r"reaching definitions", r"live variable analysis", r"available expressions"]),
        (5, "Code Generator Design, Target Code Issues, and Register Allocation", [r"code generation", r"target code", r"register allocation", r"register assignment", r"instruction selection", r"peephole optimization"])
    ],

    # Course 37: Data Science
    37: [
        # Unit 1: Data Science Foundations and Data Wrangling
        (1, "Data Science Lifecycle and Workflow", [r"data science lifecycle", r"crisp[- ]dm", r"data science process", r"data collection", r"data pipeline"]),
        (1, "NumPy for High-Performance Vector Computations", [r"numpy", r"ndarray", r"broadcasting", r"vectorization", r"array indexing"]),
        (1, "Pandas DataFrames and Series Operations", [r"pandas", r"dataframe", r"series in pandas", r"groupby", r"merging and joining", r"loc and iloc"]),
        (1, "Data Cleaning, Missing Value Imputation, and Normalization", [r"data cleaning", r"missing value", r"imputation", r"outlier detection", r"z[- ]score", r"min[- ]max scaling", r"standardization"]),
        (1, "Data Transformation, Reshaping, and Feature Extraction", [r"data transformation", r"one[- ]hot encoding", r"label encoding", r"feature extraction", r"binning"]),

        # Unit 2: Exploratory Data Analysis and Statistical Inference
        (2, "Descriptive Statistics and Measures of Dispersion", [r"descriptive statistics", r"mean", r"median", r"mode", r"standard deviation", r"variance", r"skewness", r"kurtosis", r"iqr", r"interquartile"]),
        (2, "Exploratory Visualization with Matplotlib and Seaborn", [r"matplotlib", r"seaborn", r"histogram", r"box plot", r"scatter plot", r"heatmap", r"bar chart"]),
        (2, "Probability Distributions in Data Analysis (Normal, Binomial)", [r"probability distribution", r"normal distribution", r"gaussian distribution", r"binomial distribution", r"poisson distribution"]),
        (2, "Hypothesis Testing, P-Values, and Confidence Intervals", [r"hypothesis testing", r"null hypothesis", r"p[- ]value", r"t[- ]test", r"z[- ]test", r"anova", r"chi[- ]square test", r"confidence interval"]),
        (2, "Correlation, Covariance, and Bivariate Analysis", [r"correlation", r"pearson correlation", r"spearman", r"covariance", r"scatter matrix"]),

        # Unit 3: Supervised Learning and Model Evaluation
        (3, "Linear Regression and Polynomial Regression", [r"linear regression", r"ordinary least squares", r"ols", r"multiple linear regression", r"polynomial regression", r"r[- ]squared", r"rmse"]),
        (3, "Logistic Regression for Binary and Multi-Class Classification", [r"logistic regression", r"sigmoid function", r"log[- ]odds", r"binary classification", r"multi[- ]class"]),
        (3, "Model Evaluation Metrics (Confusion Matrix, Precision, Recall, ROC-AUC)", [r"confusion matrix", r"precision", r"recall", r"f1[- ]score", r"roc curve", r"auc", r"true positive", r"false positive"]),
        (3, "Cross-Validation Strategies (K-Fold, Stratified)", [r"cross[- ]validation", r"k[- ]fold", r"stratified k[- ]fold", r"train[- ]test split", r"hyperparameter tuning", r"grid search"]),
        (3, "Overfitting, Regularization (Ridge, Lasso), and Bias-Variance Tradeoff", [r"overfitting", r"underfitting", r"bias[- ]variance", r"regularization", r"ridge regression", r"l2 regularization", r"lasso regression", r"l1 regularization"]),

        # Unit 4: Unsupervised Learning and Dimensionality Reduction
        (4, "K-Means Clustering and Cluster Quality (Elbow, Silhouette)", [r"k[- ]means", r"clustering", r"centroid", r"elbow method", r"silhouette score", r"wcss"]),
        (4, "Hierarchical Clustering (Agglomerative, Dendrograms)", [r"hierarchical clustering", r"agglomerative", r"dendrogram", r"linkage method"]),
        (4, "Principal Component Analysis (PCA) and Eigen-Decomposition", [r"principal component analysis", r"pca", r"dimensionality reduction", r"eigenvalue", r"eigenvector", r"scree plot", r"variance explained"]),
        (4, "Singular Value Decomposition (SVD)", [r"singular value decomposition", r"svd", r"matrix factorization"]),
        (4, "Association Rule Mining and Apriori Algorithm", [r"association rule", r"apriori algorithm", r"support and confidence", r"lift", r"frequent itemset"]),

        # Unit 5: Big Data Frameworks and Data Ethics
        (5, "Big Data Characteristics (Volume, Velocity, Variety)", [r"big data", r"5 v'?s of big data", r"volume velocity variety", r"veracity", r"distributed systems"]),
        (5, "Hadoop Architecture, HDFS, and MapReduce Paradigm", [r"hadoop", r"hdfs", r"namenode", r"datanode", r"mapreduce", r"map and reduce"]),
        (5, "Apache Spark Fundamentals and Resilient Distributed Datasets (RDDs)", [r"apache spark", r"spark", r"rdd", r"resilient distributed", r"spark dataframe", r"transformations and actions"]),
        (5, "Data Privacy, Security Regulations, and GDPR", [r"data privacy", r"gdpr", r"data security", r"anonymization", r"differential privacy"]),
        (5, "Model Fairness, Algorithmic Bias, and Ethical AI Governance", [r"algorithmic bias", r"fairness in ai", r"model interpretability", r"shap", r"lime", r"ethical data"])
    ]
}

