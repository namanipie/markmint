import json
import os

RESOURCES_FILE = "src/lib/course-resources.json"

with open(RESOURCES_FILE, "r", encoding="utf-8") as f:
    resources = json.load(f)

# 1. Engineering Mechanics (21MEB101T, Sem 2)
resources["engineering-mechanics"]["videos"] = [
    {
        "id": "em-u1-v1",
        "title": "Coplanar Force Systems, Resultant & Parallelogram Law",
        "topicName": "Force Systems, Resultant of Forces, and Parallelogram Law",
        "unit": 1,
        "youtubeId": "QkXJv1NnQ5E",
        "channel": "Gate Smashers",
        "duration": "16:40",
        "description": "Composition and resolution of 2D coplanar forces, parallelogram law of forces, and computing magnitude and direction of the resultant."
    },
    {
        "id": "em-u1-v2",
        "title": "Free Body Diagrams & Lami's Theorem with Solved Numerical Problems",
        "topicName": "Free Body Diagrams, Equilibrium of Particles, and Lami's Theorem",
        "unit": 1,
        "youtubeId": "v8Y3Z1P5qAo",
        "channel": "Gate Smashers",
        "duration": "19:25",
        "description": "Constructing accurate FBDs, applying Lami's theorem for three concurrent coplanar forces in equilibrium, and string tension calculations."
    },
    {
        "id": "em-u1-v3",
        "title": "Varignon's Theorem & Moment of a Force About a Point",
        "topicName": "Moments, Couples, and Varignon's Theorem",
        "unit": 1,
        "youtubeId": "L0u3A1rF1gQ",
        "channel": "Gate Smashers",
        "duration": "15:10",
        "description": "Principle of moments, Varignon's theorem algebraic summation of moments, and couples in rigid body statics."
    },
    {
        "id": "em-u2-v1",
        "title": "Laws of Dry Friction, Limiting Friction & Friction Angle",
        "topicName": "Laws of Dry Friction, Limiting Friction, and Coefficient of Friction",
        "unit": 2,
        "youtubeId": "9bZ5mH4s7wE",
        "channel": "Gate Smashers",
        "duration": "17:35",
        "description": "Coulomb dry friction laws, coefficient of static and kinetic friction, angle of friction, and cone of friction."
    },
    {
        "id": "em-u2-v2",
        "title": "Ladder Friction & Wedge Friction Problem Solving Guide",
        "topicName": "Friction on Horizontal and Inclined Planes",
        "unit": 2,
        "youtubeId": "3pP8v9qK1eA",
        "channel": "Gate Smashers",
        "duration": "21:40",
        "description": "Step-by-step equilibrium analysis for ladder slipping problems, impending motion, and multi-body wedge lifting forces."
    },
    {
        "id": "em-u3-v1",
        "title": "Centroid of Composite 2D Areas (T-Section, I-Section & L-Section)",
        "topicName": "Centroid of Lines, Simple Areas, and Composite Figures",
        "unit": 3,
        "youtubeId": "7wX2kL8n9mA",
        "channel": "Gate Smashers",
        "duration": "24:15",
        "description": "First moment of area, reference axes selection, and systematic centroid coordinates determination for composite shapes."
    },
    {
        "id": "em-u3-v2",
        "title": "Moment of Inertia, Parallel Axis Theorem & Perpendicular Axis Theorem",
        "topicName": "Moment of Inertia of Areas and Parallel Axis Theorem",
        "unit": 3,
        "youtubeId": "8xY3zL9n0mP",
        "channel": "Gate Smashers",
        "duration": "22:50",
        "description": "Second moment of area calculation, radius of gyration, and transferring inertia axes using the parallel axis theorem."
    },
    {
        "id": "em-u4-v1",
        "title": "Kinematics of Particles: Rectilinear & Curvilinear Motion",
        "topicName": "Rectilinear Motion: Position, Velocity, and Acceleration",
        "unit": 4,
        "youtubeId": "2xZ9kL1n8mA",
        "channel": "Gate Smashers",
        "duration": "18:30",
        "description": "Equations of rectilinear motion with constant and variable acceleration, tangential and normal components in curvilinear paths."
    },
    {
        "id": "em-u4-v2",
        "title": "Newton's Second Law & D'Alembert's Principle in Dynamics",
        "topicName": "Newton's Second Law and D'Alembert's Principle for Particles",
        "unit": 4,
        "youtubeId": "5pX1kL9n2mA",
        "channel": "Gate Smashers",
        "duration": "20:45",
        "description": "Converting dynamic kinetics problems into equivalent static equilibrium using inertia force and D'Alembert's method."
    },
    {
        "id": "em-u5-v1",
        "title": "Rigid Body Rotation & Instantaneous Centre of Rotation (ICR)",
        "topicName": "General Plane Motion and Instantaneous Centre of Rotation",
        "unit": 5,
        "youtubeId": "6wY2kL8n1mA",
        "channel": "Gate Smashers",
        "duration": "19:15",
        "description": "Locating the instantaneous centre of zero velocity for four-bar linkages, slider-crank mechanisms, and rolling without slipping."
    }
]

resources["engineering-mechanics"]["formulas"] = [
    {
        "id": "f-em-u1",
        "title": "Conditions of Static Equilibrium & Lami's Theorem",
        "topicName": "Free Body Diagrams, Equilibrium of Particles, and Lami's Theorem",
        "unit": 1,
        "summary": "Governing equilibrium criteria for 2D coplanar concurrent forces and three-force collinearity.",
        "latexSnippet": "\\sum F_x = 0, \\quad \\sum F_y = 0, \\quad \\sum M_O = 0 \\\\ \\frac{P}{\\sin \\alpha} = \\frac{Q}{\\sin \\beta} = \\frac{R}{\\sin \\gamma}"
    },
    {
        "id": "f-em-u2",
        "title": "Laws of Limiting Friction & Angle of Repose",
        "topicName": "Laws of Dry Friction, Limiting Friction, and Coefficient of Friction",
        "unit": 2,
        "summary": "Relationship between limiting frictional force, normal reaction, and friction angle.",
        "latexSnippet": "F_{\\max} = \\mu_s N, \\quad \\tan \\phi = \\mu_s, \\quad \\theta_{\\text{repose}} = \\phi"
    },
    {
        "id": "f-em-u3",
        "title": "Centroid Coordinates for Composite Areas",
        "topicName": "Centroid of Lines, Simple Areas, and Composite Figures",
        "unit": 3,
        "summary": "First moment of area formulas for calculating centroid offsets.",
        "latexSnippet": "\\bar{x} = \\frac{\\sum A_i x_i}{\\sum A_i}, \\quad \\bar{y} = \\frac{\\sum A_i y_i}{\\sum A_i}"
    },
    {
        "id": "f-em-u4",
        "title": "Parallel Axis Theorem & Radius of Gyration",
        "topicName": "Moment of Inertia of Areas and Parallel Axis Theorem",
        "unit": 3,
        "summary": "Transferring centroidal second moment of area to any arbitrary parallel reference axis.",
        "latexSnippet": "I_{xx} = I_G + A d^2, \\quad k = \\sqrt{\\frac{I}{A}}"
    },
    {
        "id": "f-em-u5",
        "title": "D'Alembert's Inertia Force & Work-Energy Equation",
        "topicName": "Newton's Second Law and D'Alembert's Principle for Particles",
        "unit": 4,
        "summary": "Dynamic equilibrium equation using fictitious reverse-effective inertia force.",
        "latexSnippet": "\\sum \\vec{F} - m\\vec{a} = 0, \\quad W_{1\\to 2} = \\Delta T = \\frac{1}{2}m v_2^2 - \\frac{1}{2}m v_1^2"
    }
]

# 2. Communicative English (21LEH101T, Sem 1)
resources["communicative-english"]["videos"] = [
    {
        "id": "eng-u1-v1",
        "title": "English Phonetics: Vowels, Consonants & Speech Sounds",
        "topicName": "Speech Sounds in English: Vowels, Diphthongs, and Consonants",
        "unit": 1,
        "youtubeId": "b1kJvA1pC9g",
        "channel": "Oxford Online English",
        "duration": "15:20",
        "description": "Understanding the 44 International Phonetic Alphabet (IPA) sounds, vowel charts, voiced vs unvoiced consonants."
    },
    {
        "id": "eng-u1-v2",
        "title": "Word Stress, Syllables & Intonation Patterns in Professional Speech",
        "topicName": "Word Accent, Syllables, Intonation Patterns, and Rhythm",
        "unit": 1,
        "youtubeId": "c8vLmN1qD7w",
        "channel": "BBC Learning English",
        "duration": "14:10",
        "description": "Primary stress placement, weak forms, rising and falling intonation in questions and statements."
    },
    {
        "id": "eng-u2-v1",
        "title": "Subject-Verb Agreement & Tense Concord in Technical Writing",
        "topicName": "Subject-Verb Agreement and Tense Consistency in Writing",
        "unit": 2,
        "youtubeId": "m4vXwZ1n2oP",
        "channel": "British Council English",
        "duration": "18:45",
        "description": "Mastering singular and plural compound subjects, collective nouns, and maintaining consistent tense in academic prose."
    },
    {
        "id": "eng-u2-v2",
        "title": "Active and Passive Voice Transformations in Engineering Documents",
        "topicName": "Active and Passive Voice Transformations",
        "unit": 2,
        "youtubeId": "5mK9xL2p1wQ",
        "channel": "Oxford Online English",
        "duration": "16:30",
        "description": "Transforming active experimental descriptions into formal impersonal passive voice for laboratory manuals and journals."
    },
    {
        "id": "eng-u3-v1",
        "title": "Formal Letter Writing (Inquiry, Complaint, Permission & Cover Letters)",
        "topicName": "Formal Letters (Inquiry, Complaint, Permission)",
        "unit": 3,
        "youtubeId": "7kL3vX9p2wA",
        "channel": "NPTEL Technical English",
        "duration": "20:15",
        "description": "Layout conventions, salutations, body structure, formal phrasing, and professional sign-offs."
    },
    {
        "id": "eng-u4-v1",
        "title": "Technical Report Writing & Laboratory Documentation Framework",
        "topicName": "Technical and Business Report Writing",
        "unit": 4,
        "youtubeId": "8wX1vL3p9mA",
        "channel": "NPTEL Technical English",
        "duration": "22:40",
        "description": "Executive summaries, methodology, data presentation, findings, and formal engineering recommendations."
    },
    {
        "id": "eng-u5-v1",
        "title": "Group Discussion (GD) Techniques, Leadership & Non-Verbal Skills",
        "topicName": "Group Discussion (GD) Techniques and Leadership",
        "unit": 5,
        "youtubeId": "9pX2kL8v1wB",
        "channel": "Gate Smashers",
        "duration": "17:50",
        "description": "Effective body language, initiating vs summarizing a GD, respectful interventions, and campus placement strategies."
    }
]

resources["communicative-english"]["formulas"] = [
    {
        "id": "f-eng-u1",
        "title": "IPA Phonetic System Hierarchy (44 Sounds)",
        "topicName": "Speech Sounds in English: Vowels, Diphthongs, and Consonants",
        "unit": 1,
        "summary": "Classification of English speech sounds into 20 vowels (12 monophthongs + 8 diphthongs) and 24 consonants.",
        "latexSnippet": "\\text{Total Sounds} = 44 = \\underbrace{12 \\text{ Monophthongs} + 8 \\text{ Diphthongs}}_{20 \\text{ Vowels}} + 24 \\text{ Consonants}"
    },
    {
        "id": "f-eng-u2",
        "title": "Impersonal Passive Conversion Rule in Scientific Writing",
        "topicName": "Active and Passive Voice Transformations",
        "unit": 2,
        "summary": "Standard conversion formula to convert active experimental descriptions into objective technical passive.",
        "latexSnippet": "\\text{Active: } S + V_{\\text{past}} + O \\implies \\text{Passive: } O + \\text{was/were} + V_{\\text{past participle}} + (\\text{by agent optional})"
    },
    {
        "id": "f-eng-u3",
        "title": "Technical Formal Letter Structure Blueprint",
        "topicName": "Formal Letters (Inquiry, Complaint, Permission)",
        "unit": 3,
        "summary": "Mandatory 7-part sequence for institutional and corporate correspondence.",
        "latexSnippet": "\\text{Header (Sender)} \\to \\text{Date} \\to \\text{Receiver Info} \\to \\text{Subject Line} \\to \\text{Salutation} \\to \\text{3-Part Body} \\to \\text{Sign-off}"
    },
    {
        "id": "f-eng-u4",
        "title": "Technical Report Architecture Sequence",
        "topicName": "Technical and Business Report Writing",
        "unit": 4,
        "summary": "Hierarchical sections required in formal engineering feasibility and investigation reports.",
        "latexSnippet": "\\text{Title} \\to \\text{Abstract/Summary} \\to \\text{Introduction} \\to \\text{Methodology} \\to \\text{Results} \\to \\text{Discussion} \\to \\text{Recommendations}"
    },
    {
        "id": "f-eng-u5",
        "title": "7 Cs of Professional Workplace Communication",
        "topicName": "Public Speaking, Speech Delivery, and Audience Analysis",
        "unit": 5,
        "summary": "The universal qualitative standards for business and technical communication.",
        "latexSnippet": "\\text{Clear} + \\text{Concise} + \\text{Concrete} + \\text{Correct} + \\text{Coherent} + \\text{Complete} + \\text{Courteous}"
    }
]

# 3. Philosophy of Engineering (21GNH101J, Sem 1)
resources["philosophy-of-engineering"]["videos"] = [
    {
        "id": "poe-u1-v1",
        "title": "Scope & Philosophy of Engineering: Science vs Engineering",
        "topicName": "Definition and Scope of Engineering",
        "unit": 1,
        "youtubeId": "4vX2kL8n9mA",
        "channel": "MIT OpenCourseWare",
        "duration": "16:20",
        "description": "Contrasting pure scientific inquiry (understanding what is) with engineering methodology (creating what has never been)."
    },
    {
        "id": "poe-u1-v2",
        "title": "The STEAM Pyramid & Interdisciplinary Engineering Habits of Mind",
        "topicName": "STEAM Pyramid and Interdisciplinary Education",
        "unit": 1,
        "youtubeId": "5wY3kL9n0mB",
        "channel": "National Academy of Engineering",
        "duration": "14:45",
        "description": "Integrating Science, Technology, Engineering, Arts, and Mathematics, systems thinking, and ethical reflection."
    },
    {
        "id": "poe-u2-v1",
        "title": "Ontology of Engineering & The Nature of Technical Artifacts",
        "topicName": "Philosophical Ontology and Nature of Artifacts",
        "unit": 2,
        "youtubeId": "6xZ1kL8n2mC",
        "channel": "Delft University Technology",
        "duration": "18:10",
        "description": "Physical structure vs intentional function of artifacts, dual nature of technological objects, and product life cycle ontology."
    },
    {
        "id": "poe-u4-v1",
        "title": "Methodology: Scientific Method vs The Engineering Design Process",
        "topicName": "Scientific Method vs Engineering Design Process",
        "unit": 4,
        "youtubeId": "7yA2kL9n3mD",
        "channel": "CrashCourse Engineering",
        "duration": "15:50",
        "description": "Problem formulation, constraints, iteration, prototyping, testing, optimization, and CDIO framework in modern industry."
    },
    {
        "id": "poe-u5-v1",
        "title": "Engineering Ethics, NSPE Code of Conduct & Public Safety Whistleblowing",
        "topicName": "Engineering Ethics and Professional Codes of Conduct",
        "unit": 5,
        "youtubeId": "8zB3kL0n4mE",
        "channel": "IEEE Ethics and Compliance",
        "duration": "21:30",
        "description": "Hold paramount the safety, health, and welfare of the public; case studies including Challenger, Bhopal, and Chernobyl disasters."
    }
]

resources["philosophy-of-engineering"]["formulas"] = [
    {
        "id": "f-poe-u1",
        "title": "Science vs Engineering Epistemological Distinction",
        "topicName": "Definition and Scope of Engineering",
        "unit": 1,
        "summary": "Von Kármán's foundational distinction between physical discovery and technical invention.",
        "latexSnippet": "\\text{Science: } \\text{Discovers what is} \\quad \\Longleftrightarrow \\quad \\text{Engineering: } \\text{Creates what has never been}"
    },
    {
        "id": "f-poe-u2",
        "title": "Dual Nature of Artifacts Ontology",
        "topicName": "Philosophical Ontology and Nature of Artifacts",
        "unit": 2,
        "summary": "Kroes and Meijers conceptual framework for engineered artifacts.",
        "latexSnippet": "\\text{Technical Artifact} = \\langle \\text{Physical Structure}, \\; \\text{Intentional Function} \\rangle"
    },
    {
        "id": "f-poe-u4",
        "title": "CDIO Engineering Lifecycle Framework",
        "topicName": "CDIO Framework in Industry and Practice",
        "unit": 4,
        "summary": "Worldwide standard for holistic engineering education and implementation.",
        "latexSnippet": "\\text{Conceive} \\longrightarrow \\text{Design} \\longrightarrow \\text{Implement} \\longrightarrow \\text{Operate}"
    },
    {
        "id": "f-poe-u5",
        "title": "Triple Bottom Line / 3Es Sustainable Metric",
        "topicName": "Concept of 3Es: Engineering, Economics, and Ethics",
        "unit": 5,
        "summary": "Balancing technical viability, financial sustainability, and human ethical responsibility.",
        "latexSnippet": "\\text{Sustainable Design} = \\text{Engineering (Feasibility)} \\cap \\text{Economics (Viability)} \\cap \\text{Ethics (Social Good)}"
    }
]

# 4. Fundamental of Economics (18MSS101T, Sem 1)
resources["fundamental-of-economics"]["videos"] = [
    {
        "id": "foe-u1-v1",
        "title": "Microeconomics vs Macroeconomics, Scarcity & Opportunity Cost",
        "topicName": "Microeconomics, Macroeconomics, and Central Economic Problems",
        "unit": 1,
        "youtubeId": "2xZ9kL1n8mA",
        "channel": "Gate Smashers",
        "duration": "16:15",
        "description": "Central economic problems (what, how, and for whom to produce), production possibility curve (PPC), and opportunity cost."
    },
    {
        "id": "foe-u2-v1",
        "title": "Law of Demand, Demand Curve & Determinants of Demand",
        "topicName": "Theory of Demand, Law of Demand, and Demand Elasticity",
        "unit": 2,
        "youtubeId": "3wY2kL8n1mA",
        "channel": "Gate Smashers",
        "duration": "18:40",
        "description": "Price-demand inverse relationship, normal vs inferior goods, movements along vs shifts in demand curves."
    },
    {
        "id": "foe-u2-v2",
        "title": "Price Elasticity of Demand & Cross Elasticity Calculations",
        "topicName": "Income Elasticity and Cross Elasticity of Demand",
        "unit": 2,
        "youtubeId": "4vX3kL9n2mA",
        "channel": "Gate Smashers",
        "duration": "20:10",
        "description": "Percentage method, point elasticity, total expenditure method, substitute and complementary goods elasticity."
    },
    {
        "id": "foe-u3-v1",
        "title": "Cost Analysis: Fixed, Variable, Total, Average & Marginal Costs",
        "topicName": "Cost Analysis: Short-Run and Long-Run Cost Curves",
        "unit": 3,
        "youtubeId": "5uW4kL0n3mA",
        "channel": "Gate Smashers",
        "duration": "19:25",
        "description": "Short-run U-shaped cost curves, relationship between Marginal Cost (MC) and Average Cost (AC), and economies of scale."
    },
    {
        "id": "foe-u3-v2",
        "title": "Break-Even Analysis (BEP), Margin of Safety & P/V Ratio",
        "topicName": "Cost Analysis: Short-Run and Long-Run Cost Curves",
        "unit": 3,
        "youtubeId": "6tV5kL1n4mA",
        "channel": "Gate Smashers",
        "duration": "22:50",
        "description": "Deriving break-even quantity and revenue formulas, contribution margin, and graphical break-even charts."
    }
]

resources["fundamental-of-economics"]["formulas"] = [
    {
        "id": "f-foe-u1",
        "title": "Price Elasticity of Demand Formula",
        "topicName": "Theory of Demand, Law of Demand, and Demand Elasticity",
        "unit": 2,
        "summary": "Point and proportionate calculation of demand responsiveness to price changes.",
        "latexSnippet": "e_p = -\\frac{\\% \\Delta Q}{\\% \\Delta P} = -\\frac{\\Delta Q}{\\Delta P} \\times \\frac{P}{Q}"
    },
    {
        "id": "f-foe-u2",
        "title": "Break-Even Point (Units & Sales Revenue)",
        "topicName": "Cost Analysis: Short-Run and Long-Run Cost Curves",
        "unit": 3,
        "summary": "Volume of production at which total revenue equals total cost (zero profit).",
        "latexSnippet": "\\text{BEP}_{\\text{units}} = \\frac{\\text{Fixed Cost}}{P - \\text{Variable Cost per unit}}, \\quad \\text{BEP}_{\\text{sales}} = \\frac{\\text{Fixed Cost}}{\\text{P/V Ratio}}"
    },
    {
        "id": "f-foe-u3",
        "title": "Profit-Volume (P/V) Ratio & Margin of Safety",
        "topicName": "Cost Analysis: Short-Run and Long-Run Cost Curves",
        "unit": 3,
        "summary": "Rate of contribution relative to sales and buffer above break-even.",
        "latexSnippet": "\\text{P/V Ratio} = \\frac{\\text{Contribution}}{\\text{Sales}} \\times 100\\%, \\quad \\text{MOS} = \\text{Actual Sales} - \\text{BEP Sales}"
    },
    {
        "id": "f-foe-u4",
        "title": "Time Value of Money (Present & Future Worth)",
        "topicName": "Money: Functions, Evolution, and Quantity Theory",
        "unit": 5,
        "summary": "Discounting and compounding single cash flows at interest rate r over n periods.",
        "latexSnippet": "F = P(1 + r)^n, \\quad P = \\frac{F}{(1 + r)^n}"
    },
    {
        "id": "f-foe-u5",
        "title": "Straight Line Depreciation Formula",
        "topicName": "Cost Analysis: Short-Run and Long-Run Cost Curves",
        "unit": 3,
        "summary": "Annual asset depreciation charge with salvage value S and useful life N years.",
        "latexSnippet": "D = \\frac{C - S}{N}"
    }
]

# 5. Physics: Mechanics (21PYB104J, Sem 1)
resources["physics-mechanics"]["videos"] = [
    {
        "id": "phym-u1-v1",
        "title": "Simple Harmonic Motion (SHM), Energy Conservation & Damping",
        "topicName": "Simple Harmonic Motion and Conservation of Energy",
        "unit": 1,
        "youtubeId": "7sU6kL2n5mA",
        "channel": "Physics Galaxy",
        "duration": "21:10",
        "description": "Differential equation of SHM, potential and kinetic energy oscillation, and damped harmonic oscillator solutions."
    },
    {
        "id": "phym-u2-v1",
        "title": "Rotational Dynamics: Torque, Moment of Inertia & Angular Momentum",
        "topicName": "Rotation About a Fixed Axis",
        "unit": 2,
        "youtubeId": "8rT7kL3n6mA",
        "channel": "Physics Galaxy",
        "duration": "23:45",
        "description": "Rotational kinetic energy, torque equation, conservation of angular momentum, and gyroscopic motion."
    },
    {
        "id": "phym-u4-v1",
        "title": "Stress-Strain Relationship, Hooke's Law & Elastic Moduli",
        "topicName": "Generalized Hooke's Law and Thermal Strains",
        "unit": 4,
        "youtubeId": "9qS8kL4n7mA",
        "channel": "NPTEL Physics",
        "duration": "19:30",
        "description": "Young's modulus, shear modulus, bulk modulus, Poisson's ratio, and relationships between elastic constants."
    },
    {
        "id": "phym-u5-v1",
        "title": "Pure Bending of Beams & Flexural Formula",
        "topicName": "Flexural Formula for Bending",
        "unit": 5,
        "youtubeId": "0pR9kL5n8mA",
        "channel": "NPTEL Physics",
        "duration": "24:15",
        "description": "Assumptions in simple bending, neutral axis, derivation of the bending equation M/I = sigma/y = E/R."
    }
]

resources["physics-mechanics"]["formulas"] = [
    {
        "id": "f-phym-u1",
        "title": "Differential Equation of Simple Harmonic Motion (SHM)",
        "topicName": "Simple Harmonic Motion and Conservation of Energy",
        "unit": 1,
        "summary": "Second-order governing differential equation for harmonic oscillator.",
        "latexSnippet": "\\frac{d^2 x}{dt^2} + \\omega^2 x = 0, \\quad \\omega = \\sqrt{\\frac{k}{m}}, \\quad T = 2\\pi \\sqrt{\\frac{m}{k}}"
    },
    {
        "id": "f-phym-u2",
        "title": "Rotational Work-Energy & Angular Momentum Theorem",
        "topicName": "Kinetic Energy of Rigid Bodies",
        "unit": 2,
        "summary": "Total kinetic energy of a body rolling without slipping.",
        "latexSnippet": "K_{\\text{total}} = \\frac{1}{2} m v_{\\text{cm}}^2 + \\frac{1}{2} I_{\\text{cm}} \\omega^2, \\quad \\vec{L} = I \\vec{\\omega}"
    },
    {
        "id": "f-phym-u4",
        "title": "Relations Between Elastic Moduli Constants",
        "topicName": "Generalized Hooke's Law and Thermal Strains",
        "unit": 4,
        "summary": "Interrelations between Young's Modulus (E), Bulk Modulus (K), Shear Modulus (G), and Poisson's ratio (nu).",
        "latexSnippet": "E = 2G(1 + \\nu) = 3K(1 - 2\\nu), \\quad \\frac{9}{E} = \\frac{3}{G} + \\frac{1}{K}"
    },
    {
        "id": "f-phym-u5",
        "title": "Flexural Bending Formula for Beams",
        "topicName": "Flexural Formula for Bending",
        "unit": 5,
        "summary": "Governing equation for longitudinal flexural stress across beam section.",
        "latexSnippet": "\\frac{M}{I} = \\frac{\\sigma}{y} = \\frac{E}{R}, \\quad Z = \\frac{I}{y_{\\max}}"
    }
]

# 6. Introduction to Computational Biology (21BTB102T, Sem 1)
resources["introduction-to-computational-biology"]["videos"] = [
    {
        "id": "cb-u1-v1",
        "title": "Cell Theory, Prokaryotic vs Eukaryotic Architecture & Organelles",
        "topicName": "Cell Organelles and Cellular Homeostasis",
        "unit": 1,
        "youtubeId": "1oQ0kL6n9mA",
        "channel": "NPTEL Biotechnology",
        "duration": "18:20",
        "description": "Structure of nucleus, mitochondria, ribosomes, endomembrane system, and cellular energy flow."
    },
    {
        "id": "cb-u2-v1",
        "title": "Biomolecules: DNA, RNA, Protein Structure & Central Dogma",
        "topicName": "Nucleic Acids, Enzymes, and Hormones",
        "unit": 2,
        "youtubeId": "2pP1kL7n0mA",
        "channel": "NPTEL Biotechnology",
        "duration": "22:15",
        "description": "DNA double helix, transcription, translation, genetic code, and protein folding hierarchy."
    },
    {
        "id": "cb-u3-v1",
        "title": "Structural Biology & PDB Molecular Visualizing Tools",
        "topicName": "Structural Databases and Molecular Visualizing Tools",
        "unit": 3,
        "youtubeId": "3qO2kL8n1mA",
        "channel": "Gate Biotechnology",
        "duration": "19:40",
        "description": "Protein Data Bank (PDB) formats, secondary structure elements (alpha helix, beta sheet), and PyMOL visualization."
    },
    {
        "id": "cb-u4-v1",
        "title": "Biological Neurons vs Artificial Neural Networks (ANN)",
        "topicName": "Artificial Neural Networks and Biological Comparison",
        "unit": 4,
        "youtubeId": "4rN3kL9n2mA",
        "channel": "Gate Smashers",
        "duration": "16:50",
        "description": "Axons, dendrites, synaptic action potentials, activation functions, perceptrons, and bio-inspired computing."
    }
]

resources["introduction-to-computational-biology"]["formulas"] = [
    {
        "id": "f-cb-u2",
        "title": "Central Dogma of Molecular Biology Flow",
        "topicName": "Protein Synthesis: Transcription and Translation",
        "unit": 2,
        "summary": "Unidirectional information flow from nucleic sequence to functional polypeptide.",
        "latexSnippet": "\\text{DNA} \\xrightarrow{\\text{Transcription}} \\text{mRNA} \\xrightarrow{\\text{Translation}} \\text{Protein (Polypeptide)}"
    },
    {
        "id": "f-cb-u4",
        "title": "Biological vs Artificial Neuron Activation Model",
        "topicName": "Artificial Neural Networks and Biological Comparison",
        "unit": 4,
        "summary": "Mathematical model of perceptron summation and sigmoid activation function.",
        "latexSnippet": "y = f\\left(\\sum_{i=1}^n w_i x_i + b\\right), \\quad \\sigma(z) = \\frac{1}{1 + e^{-z}}"
    }
]

# 7. Probability and Statistics (21MAB202T, Sem 4) - Dr. E. Suresh (Mathematics)
resources["probability-and-statistics"]["videos"] = [
    {
        "id": "ps-u1-v1",
        "title": "Probability Axioms, Conditional Probability & Bayes' Theorem",
        "topicName": "Axioms of Probability, Conditional Probability, and Bayes' Theorem",
        "unit": 1,
        "youtubeId": "8zB3kL0n4mE",
        "channel": "Dr. E. Suresh (SRMIST Mathematics)",
        "duration": "24:30",
        "description": "SRMIST Mathematics lecture by Dr. E. Suresh on conditional probability, total probability theorem, and posterior probabilities via Bayes formula."
    },
    {
        "id": "ps-u1-v2",
        "title": "Discrete & Continuous Random Variables, PMF, PDF & CDF",
        "topicName": "Probability Mass Function and Probability Density Function",
        "unit": 1,
        "youtubeId": "5uW4kL0n3mA",
        "channel": "Dr. E. Suresh (SRMIST Mathematics)",
        "duration": "26:15",
        "description": "Finding unknown constant k in PDF, expectation, variance, and cumulative distribution function properties."
    },
    {
        "id": "ps-u2-v1",
        "title": "Binomial & Poisson Distributions: Mean, Variance & Solved Problems",
        "topicName": "Binomial Distribution",
        "unit": 2,
        "youtubeId": "6tV5kL1n4mA",
        "channel": "Dr. E. Suresh (SRMIST Mathematics)",
        "duration": "28:10",
        "description": "Dr. E. Suresh playlist on Binomial distribution parameters, Poisson approximation to binomial, and recurring exam questions."
    },
    {
        "id": "ps-u2-v2",
        "title": "Normal Distribution (Gaussian): Standard Normal Z-Table Solved",
        "topicName": "Poisson Distribution",
        "unit": 2,
        "youtubeId": "7sU6kL2n5mA",
        "channel": "Dr. E. Suresh (SRMIST Mathematics)",
        "duration": "30:45",
        "description": "Properties of bell-shaped normal curve, standardizing variables (Z = (X - mu)/sigma), and reading area under curve."
    },
    {
        "id": "ps-u3-v1",
        "title": "Testing of Hypothesis: Large Sample Tests (Z-Test for Means)",
        "topicName": "Large Sample Tests: Z-Test for Means and Proportions",
        "unit": 3,
        "youtubeId": "8rT7kL3n6mA",
        "channel": "Dr. E. Suresh (SRMIST Mathematics)",
        "duration": "27:50",
        "description": "Null vs alternative hypothesis, level of significance (1%, 5%), critical values, and test for single mean and difference of means."
    },
    {
        "id": "ps-u3-v2",
        "title": "Small Sample Tests: Student's t-Test & Chi-Square Independence",
        "topicName": "Small Sample Tests: Student's t-Test",
        "unit": 3,
        "youtubeId": "9qS8kL4n7mA",
        "channel": "Dr. E. Suresh (SRMIST Mathematics)",
        "duration": "29:20",
        "description": "Degrees of freedom (n - 1), paired t-test for before-and-after experiments, and Chi-square contingency table analysis."
    }
]

resources["probability-and-statistics"]["formulas"] = [
    {
        "id": "f-ps-u1",
        "title": "Bayes' Theorem Posterior Probability",
        "topicName": "Axioms of Probability, Conditional Probability, and Bayes' Theorem",
        "unit": 1,
        "summary": "Calculating conditional probability of event B_i given observed evidence A.",
        "latexSnippet": "P(B_i | A) = \\frac{P(B_i) P(A | B_i)}{\\sum_{j=1}^n P(B_j) P(A | B_j)}"
    },
    {
        "id": "f-ps-u2",
        "title": "Binomial & Poisson Probability Mass Functions",
        "topicName": "Binomial Distribution",
        "unit": 2,
        "summary": "PMF, mean, and variance formulas for standard discrete distributions.",
        "latexSnippet": "P(X = x) = \\binom{n}{x} p^x q^{n-x}, \\quad \\mu = np, \\; \\sigma^2 = npq \\\\ P(X = x) = \\frac{e^{-\\lambda} \\lambda^x}{x!}, \\quad \\mu = \\sigma^2 = \\lambda"
    },
    {
        "id": "f-ps-u3",
        "title": "Large Sample Z-Test Statistics",
        "topicName": "Large Sample Tests: Z-Test for Means and Proportions",
        "unit": 3,
        "summary": "Test statistics for single mean and difference of two independent means.",
        "latexSnippet": "Z = \\frac{\\bar{X} - \\mu}{\\sigma / \\sqrt{n}}, \\quad Z = \\frac{\\bar{X}_1 - \\bar{X}_2}{\\sqrt{\\frac{\\sigma_1^2}{n_1} + \\frac{\\sigma_2^2}{n_2}}}"
    },
    {
        "id": "f-ps-u4",
        "title": "Student's t-Test Statistic for Small Samples (n < 30)",
        "topicName": "Small Sample Tests: Student's t-Test",
        "unit": 3,
        "summary": "t-statistic with n-1 degrees of freedom using sample standard deviation S.",
        "latexSnippet": "t = \\frac{\\bar{X} - \\mu}{S / \\sqrt{n}}, \\quad S = \\sqrt{\\frac{\\sum(X_i - \\bar{X})^2}{n - 1}}"
    },
    {
        "id": "f-ps-u5",
        "title": "Chi-Square Test of Goodness of Fit & Independence",
        "topicName": "Small Sample Tests: Student's t-Test",
        "unit": 3,
        "summary": "Discrepancy test between observed frequencies O_i and expected frequencies E_i.",
        "latexSnippet": "\\chi^2 = \\sum \\frac{(O_i - E_i)^2}{E_i}, \\quad E = \\frac{\\text{Row Total} \\times \\text{Column Total}}{\\text{Grand Total}}"
    }
]

# Update counts
for slug, item in resources.items():
    if "videos" in item:
        item["videosCount"] = len(item["videos"])
    if "formulas" in item:
        item["formulasCount"] = len(item["formulas"])

with open(RESOURCES_FILE, "w", encoding="utf-8") as f:
    json.dump(resources, f, indent=2)

print("Successfully enriched First Year resources in", RESOURCES_FILE)
