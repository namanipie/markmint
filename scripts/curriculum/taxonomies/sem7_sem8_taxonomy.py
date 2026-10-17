"""
Authoritative Curriculum Taxonomy, Blueprints, and Classification Heuristics
for MarkMint Semesters 7 & 8 Core & Professional Elective Courses (Regulation 2021):

1. Course 38: Internet of Things (SEM7-IOT / 21CSC401T) - Semester 7
2. Course 39: Digital Image Processing (SEM7-DIP / 21CSC402T) - Semester 7
3. Course 40: Security Governance, Risk and Compliance (SEM7-GRC / 21CSS401T) - Semester 7
4. Course 41: Security Risk Management and Principles (SEM7-SRMP / 21CSC403T) - Semester 7
5. Course 42: Information Security (SEM7-IS / 21CSC404T) - Semester 7
6. Course 43: Digital Signal Processing (SEM8-DSP / 21ECC302J) - Semester 8
"""

import re
from typing import Dict, List, Any, Callable

COURSES_TAXONOMY: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # COURSE 38: Internet of Things (SEM7-IOT / 21CSC401T)
    # -------------------------------------------------------------
    {
        "id": 38,
        "name": "Internet of Things",
        "code": "SEM7-IOT",
        "canonical_code": "21CSC401T",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 7,
        "description": "Architectures, sensing, microcontroller interfacing, low-power wireless networking, cloud telemetry, edge computing, and real-world industrial IoT deployments.",
        "studique_key": "Internet of Things (IoT)",
        "curriculum_filter": lambda s: bool(re.search(r"\b(internet of things|iot|embedded systems and iot)\b", s, re.I)),
        "units": [
            {
                "number": 1,
                "name": "Introduction to IoT Architecture and Design Principles",
                "topics": [
                    "Definition and Characteristics of Internet of Things",
                    "Physical Design of IoT: Things and Protocols",
                    "Logical Design of IoT: Functional Blocks and Communication Models",
                    "IoT Enabling Technologies: Sensors, Actuators, Wireless Sensor Networks",
                    "IoT Levels and Deployment Templates"
                ]
            },
            {
                "number": 2,
                "name": "IoT Hardware, Microcontrollers, and Interfacing",
                "topics": [
                    "Sensors: Temperature, Humidity, Pressure, Optical, and Motion Sensors",
                    "Actuators and Drive Circuits: Relays, Servos, Stepper Motors",
                    "Embedded Microcontrollers: Arduino, ESP8266, ESP32, and Raspberry Pi",
                    "Interfacing Interfaces: GPIO, I2C, SPI, UART, and ADC/DAC",
                    "Power Management and Energy Harvesting in IoT Nodes"
                ]
            },
            {
                "number": 3,
                "name": "IoT Networking and Communication Protocols",
                "topics": [
                    "Link Layer Protocols: IEEE 802.15.4, ZigBee, Bluetooth Low Energy (BLE)",
                    "Long-Range Wireless: LoRaWAN, Sigfox, NB-IoT, and 5G IoT",
                    "Network and Transport: 6LoWPAN, RPL, UDP, and DTLS",
                    "Application Layer Protocols: MQTT Architecture, Publish/Subscribe, and QoS",
                    "CoAP (Constrained Application Protocol), HTTP/REST, and WebSockets in IoT"
                ]
            },
            {
                "number": 4,
                "name": "Cloud Computing, Edge Intelligence, and IoT Data Analytics",
                "topics": [
                    "IoT Cloud Platforms: AWS IoT Core, Microsoft Azure IoT Hub, Google Cloud IoT",
                    "Data Telemetry, Ingestion Pipelines, and Time-Series Databases",
                    "Edge Computing and Fog Computing Architectures in IoT",
                    "Real-Time Stream Processing and Anomaly Detection in IoT Streams",
                    "Integration of Machine Learning Models on Edge Microcontrollers (TinyML)"
                ]
            },
            {
                "number": 5,
                "name": "IoT Security, Privacy, and Domain Applications",
                "topics": [
                    "IoT Security Vulnerabilities, Threat Modeling, and Attack Vectors",
                    "Cryptographic Solutions for Constrained Devices (AES-CCM, Lightweight Ciphers)",
                    "Smart Cities, Smart Transportation, and Traffic Management Systems",
                    "Industrial IoT (IIoT), Predictive Maintenance, and SCADA Integration",
                    "Healthcare IoT (IoMT), Smart Agriculture, and Environmental Monitoring"
                ]
            }
        ]
    },

    # -------------------------------------------------------------
    # COURSE 39: Digital Image Processing (SEM7-DIP / 21CSC402T)
    # -------------------------------------------------------------
    {
        "id": 39,
        "name": "Digital Image Processing",
        "code": "SEM7-DIP",
        "canonical_code": "21CSC402T",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 7,
        "description": "Visual perception, spatial and frequency domain filtering, image restoration, color processing, morphological algorithms, segmentation, and feature extraction.",
        "studique_key": "Digital Image Processing (DIP)",
        "curriculum_filter": lambda s: bool(re.search(r"\b(digital image processing|image processing|dip)\b", s, re.I)),
        "units": [
            {
                "number": 1,
                "name": "Digital Image Fundamentals and Visual Perception",
                "topics": [
                    "Elements of Visual Perception, Eye Structure, and Brightness Adaptation",
                    "Image Sensing, Acquisition, Sampling, and Quantization",
                    "Representing Digital Images, Spatial and Gray-Level Resolution",
                    "Pixel Relationships: Neighbors, Adjacency, Connectivity, and Distance Measures",
                    "Basic Mathematical Operations on Digital Images (Arithmetic, Logical, Geometric)"
                ]
            },
            {
                "number": 2,
                "name": "Spatial Domain Image Enhancement and Filtering",
                "topics": [
                    "Intensity Transformations: Negative, Log, Power-Law (Gamma), Piecewise-Linear",
                    "Histogram Processing: Histogram Equalization, Specification, and Local Histograms",
                    "Spatial Filtering Fundamentals: Correlation and Convolution Operations",
                    "Smoothing Spatial Filters: Linear Box Filters, Gaussian Filters, Non-linear Median Filters",
                    "Sharpening Spatial Filters: First and Second Derivatives, Laplacian, Unsharp Masking"
                ]
            },
            {
                "number": 3,
                "name": "Frequency Domain Filtering and Image Restoration",
                "topics": [
                    "2D Discrete Fourier Transform (DFT) and Frequency Domain Properties",
                    "Frequency Domain Filtering Pipeline: Ideal, Butterworth, and Gaussian Lowpass Filters",
                    "Frequency Domain Highpass Filters and High-Frequency Emphasis Filtering",
                    "Image Degradation and Restoration Model, Noise Probability Density Functions",
                    "Restoration in Presence of Noise Only: Mean, Order-Statistics, Wiener Filtering"
                ]
            },
            {
                "number": 4,
                "name": "Color Image Processing, Wavelets, and Morphological Operations",
                "topics": [
                    "Color Models: RGB, CMY/CMYK, HSI/HSV, and Color Transformations",
                    "Pseudocolor and Full-Color Image Processing and Sharpening",
                    "Morphological Image Processing: Dilation, Erosion, Opening, and Closing",
                    "Hit-or-Miss Transformation, Boundary Extraction, Hole Filling, and Thinning",
                    "Image Pyramids, Subband Coding, and Discrete Wavelet Transform (DWT)"
                ]
            },
            {
                "number": 5,
                "name": "Image Segmentation, Feature Representation, and Object Detection",
                "topics": [
                    "Point, Line, and Edge Detection: Sobel, Prewitt, Laplacian, and Canny Edge Detector",
                    "Hough Transform for Line and Circle Detection",
                    "Thresholding Techniques: Global, Adaptive, and Otsu's Optimum Global Thresholding",
                    "Region-Based Segmentation: Region Growing, Region Splitting and Merging",
                    "Feature Representation: Boundary Descriptors, Topological Descriptors, and Moments"
                ]
            }
        ]
    },

    # -------------------------------------------------------------
    # COURSE 40: Security Governance, Risk and Compliance (SEM7-GRC / 21CSS401T)
    # -------------------------------------------------------------
    {
        "id": 40,
        "name": "Security Governance, Risk and Compliance",
        "code": "SEM7-GRC",
        "canonical_code": "21CSS401T",
        "regulation_year": 2021,
        "department": "Computational Intelligence",
        "semester": 7,
        "description": "Enterprise security governance frameworks, risk assessment methodologies, security policies, regulatory audits, compliance architectures, and business continuity.",
        "studique_key": "Security Governance, Risk and Compliance (GRC)",
        "curriculum_filter": lambda s: bool(re.search(r"\b(security governance|grc|governance.*risk.*compliance|compliance.*risk)\b", s, re.I)),
        "units": [
            {
                "number": 1,
                "name": "Information Security Governance and Strategic Alignment",
                "topics": [
                    "Foundations of Information Security Governance and Executive Oversight",
                    "Governance Frameworks: COBIT, ISO/IEC 27014, and NIST Cybersecurity Framework (CSF)",
                    "Strategic Alignment: Aligning Information Security with Business Objectives",
                    "Roles and Responsibilities: Board of Directors, CISO, Security Steering Committee",
                    "Security Metrics and Key Performance Indicators (KPIs/KRIs)"
                ]
            },
            {
                "number": 2,
                "name": "Risk Management Frameworks and Threat Identification",
                "topics": [
                    "Information Security Risk Concepts: Assets, Threats, Vulnerabilities, and Impact",
                    "Risk Assessment Methodologies: ISO 27005, NIST SP 800-30, and OCTAVE",
                    "Asset Identification, Valuation, and Classification Schemes",
                    "Threat Profiling, Vulnerability Assessment, and Threat Intelligence Integration",
                    "Risk Appetite, Tolerance, and Risk Treatment Strategies (Mitigate, Transfer, Accept, Avoid)"
                ]
            },
            {
                "number": 3,
                "name": "Information Security Policies, Standards, and Architecture",
                "topics": [
                    "Security Policy Hierarchy: Policies, Standards, Baselines, Guidelines, and Procedures",
                    "Developing Enterprise Information Security Policy (EISP) and Issue-Specific Policies (ISSP)",
                    "Access Control and Data Protection Policies (Need-to-Know, Least Privilege)",
                    "Vendor and Third-Party Risk Management Policies (Supply Chain Cybersecurity)",
                    "Security Awareness, Education, and Training Programs (SETA)"
                ]
            },
            {
                "number": 4,
                "name": "Regulatory Compliance, Auditing, and Privacy Frameworks",
                "topics": [
                    "Legal, Regulatory, and Industry Mandates: GDPR, HIPAA, Sarbanes-Oxley (SOX), PCI-DSS",
                    "ISO/IEC 27001 Certification, Statement of Applicability (SoA), and ISO 27002 Controls",
                    "Internal and External Security Auditing: Audit Planning, Fieldwork, and Reporting",
                    "SOC 1, SOC 2, and SOC 3 Compliance and Trust Services Criteria",
                    "Data Privacy Principles, Cross-Border Data Transfers, and Data Subject Rights"
                ]
            },
            {
                "number": 5,
                "name": "Incident Management, Business Continuity, and Disaster Recovery",
                "topics": [
                    "Incident Response Life Cycle: NIST SP 800-61 Preparation, Detection, Containment, Recovery",
                    "Computer Security Incident Response Teams (CSIRT) and Digital Forensics Readiness",
                    "Business Impact Analysis (BIA), Maximum Tolerable Downtime (MTD), RTO, and RPO",
                    "Business Continuity Planning (BCP) and Disaster Recovery Planning (DRP)",
                    "Crisis Communication, Exercise Testing (Tabletop, Parallel, Full Interruption), and Post-Mortem"
                ]
            }
        ]
    },

    # -------------------------------------------------------------
    # COURSE 41: Security Risk Management and Principles (SEM7-SRMP / 21CSC403T)
    # -------------------------------------------------------------
    {
        "id": 41,
        "name": "Security Risk Management and Principles",
        "code": "SEM7-SRMP",
        "canonical_code": "21CSC403T",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 7,
        "description": "Threat modeling, quantitative and qualitative risk analysis, defense-in-depth, security controls selection, residual risk management, and enterprise cyber resilience.",
        "studique_key": "Security Risk Management and Principles (SRMP)",
        "curriculum_filter": lambda s: bool(re.search(r"\b(security risk management|srmp|risk management and principles)\b", s, re.I)),
        "units": [
            {
                "number": 1,
                "name": "Fundamentals of Security Risk and Threat Environments",
                "topics": [
                    "Principles of Information Security: CIA Triad, Non-Repudiation, and Authenticity",
                    "The Threat Landscape: Nation-State Actors, Cybercriminals, Insiders, and APTs",
                    "Cyber Kill Chain and MITRE ATT&CK Framework Mapping",
                    "Vulnerability Management: CVE, NVD, and CVSS v3.1 Scoring Mechanics",
                    "Risk Terminology: Inherent Risk, Control Effectiveness, and Residual Risk"
                ]
            },
            {
                "number": 2,
                "name": "Threat Modeling and System Security Analysis",
                "topics": [
                    "Threat Modeling Methodologies: STRIDE, DREAD, PASTA, and VAST",
                    "Data Flow Diagrams (DFDs) for Trust Boundaries and Security Analysis",
                    "Attack Trees, Attack Graphs, and Exploitation Probability Calculation",
                    "Systemic Weakness Identification in Software Architectures and Cloud Infrastructures",
                    "Security Architecture Review and Security Defect Prioritization"
                ]
            },
            {
                "number": 3,
                "name": "Qualitative and Quantitative Risk Analysis Methodologies",
                "topics": [
                    "Qualitative Risk Analysis: Risk Matrices, Probability-Impact Ratings, Heat Maps",
                    "Quantitative Risk Analysis: Single Loss Expectancy (SLE), Annualized Rate of Occurrence (ARO)",
                    "Annualized Loss Expectancy (ALE) and Return on Security Investment (ROSI)",
                    "Factor Analysis of Information Risk (FAIR) Framework and Monte Carlo Simulations",
                    "Evaluating Uncertainty, Biases, and Confidence Intervals in Risk Estimates"
                ]
            },
            {
                "number": 4,
                "name": "Security Controls, Mitigation, and Architecture",
                "topics": [
                    "Security Control Categories: Technical, Operational, Management, and Physical",
                    "Control Types: Preventive, Detective, Corrective, Deterrent, and Compensating",
                    "NIST SP 800-53 Control Catalog and Baseline Selection",
                    "Defense-in-Depth, Zero Trust Architecture (ZTA), and Least Privilege Implementation",
                    "Cost-Benefit Analysis for Risk Mitigation and Security Controls"
                ]
            },
            {
                "number": 5,
                "name": "Residual Risk, Cyber Insurance, and Enterprise Governance",
                "topics": [
                    "Managing Residual Risk and Formal Risk Acceptance Procedures",
                    "Risk Transfer Strategies: Cyber Liability Insurance Underwriting and Policy Exclusions",
                    "Third-Party Vendor Risk Assessments (SOC Reports, SIG, CAIQ)",
                    "Continuous Monitoring, Key Risk Indicators (KRIs), and Dynamic Risk Dashboards",
                    "Legal, Regulatory Penalties, and Corporate Board Risk Communication"
                ]
            }
        ]
    },

    # -------------------------------------------------------------
    # COURSE 42: Information Security (SEM7-IS / 21CSC404T)
    # -------------------------------------------------------------
    {
        "id": 42,
        "name": "Information Security",
        "code": "SEM7-IS",
        "canonical_code": "21CSC404T",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 7,
        "description": "Cryptographic foundations, public key infrastructure, digital signatures, authentication protocols, network perimeter security, firewalls, and intrusion detection systems.",
        "studique_key": "Information Security (IS)",
        "curriculum_filter": lambda s: bool(re.search(r"\b(information security|network security|computer communication and network security)\b", s, re.I)),
        "units": [
            {
                "number": 1,
                "name": "Cryptographic Foundations and Classical Encryption",
                "topics": [
                    "Security Attacks, Services, and Mechanisms (X.800 Architecture)",
                    "Classical Encryption Techniques: Substitution Ciphers (Caesar, Playfair, Vigenère)",
                    "Transposition Techniques and Steganography Principles",
                    "Block Ciphers vs Stream Ciphers: Shannon's Principles of Confusion and Diffusion",
                    "Data Encryption Standard (DES), Triple DES (3DES), and Differential Cryptanalysis Overview"
                ]
            },
            {
                "number": 2,
                "name": "Symmetric Encryption and Advanced Encryption Standard",
                "topics": [
                    "Advanced Encryption Standard (AES) Structure, SubBytes, ShiftRows, MixColumns, AddRoundKey",
                    "Block Cipher Modes of Operation: ECB, CBC, CFB, OFB, and CTR",
                    "Galois/Counter Mode (GCM) and Authenticated Encryption",
                    "Random Number Generation and Pseudorandom Generators (PRNGs)",
                    "Stream Ciphers: RC4 and ChaCha20 Algorithms"
                ]
            },
            {
                "number": 3,
                "name": "Asymmetric Cryptography and Key Management",
                "topics": [
                    "Mathematical Foundations: Fermat's and Euler's Theorems, Modular Arithmetic, GCD",
                    "RSA Algorithm: Key Generation, Encryption, Decryption, and Security Analysis",
                    "Diffie-Hellman Key Exchange Algorithm and Man-in-the-Middle Vulnerability",
                    "Elliptic Curve Cryptography (ECC) Fundamentals and ECDH",
                    "Key Distribution Centers (KDC), Public Key Authorities, and X.509 Certificates"
                ]
            },
            {
                "number": 4,
                "name": "Cryptographic Hashes, Digital Signatures, and Authentication",
                "topics": [
                    "Cryptographic Hash Functions: Properties, Collision Resistance, MD5, SHA-256, SHA-3",
                    "Message Authentication Codes (MAC) and HMAC Construction",
                    "Digital Signature Standard (DSS) and RSA Digital Signatures",
                    "Mutual Authentication Protocols: Kerberos Authentication Architecture (Tickets, TGS)",
                    "Public Key Infrastructure (PKI), Certification Authorities (CA), and CRL/OCSP"
                ]
            },
            {
                "number": 5,
                "name": "Network Security Protocols and Defense Systems",
                "topics": [
                    "IP Security (IPSec): Architecture, AH, ESP, and IKE Protocol Modes (Transport vs Tunnel)",
                    "Transport Layer Security (TLS/SSL): Handshake Protocol, Record Protocol, and Ciphersuites",
                    "Email Security: PGP (Pretty Good Privacy) and S/MIME Protocol",
                    "Firewall Technologies: Packet Filtering, Stateful Inspection, and Next-Gen Firewalls (NGFW)",
                    "Intrusion Detection and Prevention Systems (IDS/IPS): Signature vs Anomaly Based"
                ]
            }
        ]
    },

    # -------------------------------------------------------------
    # COURSE 43: Digital Signal Processing (SEM8-DSP / 21ECC302J)
    # -------------------------------------------------------------
    {
        "id": 43,
        "name": "Digital Signal Processing",
        "code": "SEM8-DSP",
        "canonical_code": "21ECC302J",
        "regulation_year": 2021,
        "department": "Electronics and Communication",
        "semester": 8,
        "description": "Discrete-time signals and systems, Z-transforms, DFT/FFT algorithms, IIR and FIR digital filter synthesis, finite wordlength effects, and DSP architectures.",
        "studique_key": "Digital Signal Processing (DSP)",
        "curriculum_filter": lambda s: bool(re.search(r"\b(digital signal processing|dsp|signal processing)\b", s, re.I)),
        "units": [
            {
                "number": 1,
                "name": "Discrete-Time Signals, Systems, and Z-Transforms",
                "topics": [
                    "Classification of Discrete-Time Signals and Systems (Linearity, Causality, Stability)",
                    "Linear Time-Invariant (LTI) Systems, Convolution Sum, and Difference Equations",
                    "Z-Transform Definition, Region of Convergence (ROC), and Key Properties",
                    "Inverse Z-Transform: Partial Fraction Expansion, Power Series, and Contour Integration",
                    "System Function H(z), Frequency Response, Pole-Zero Plots, and Stability Analysis"
                ]
            },
            {
                "number": 2,
                "name": "Discrete Fourier Transform (DFT) and Fast Fourier Transform (FFT)",
                "topics": [
                    "Discrete Fourier Transform (DFT) Definition and Inverse DFT (IDFT)",
                    "Properties of DFT: Linearity, Periodicity, Circular Convolution, and Parseval's Theorem",
                    "Linear Filtering via DFT: Overlap-Add and Overlap-Save Methods",
                    "Fast Fourier Transform (FFT): Decimation-in-Time (DIT-FFT) Radix-2 Algorithm",
                    "Decimation-in-Frequency (DIF-FFT) Radix-2 Algorithm and Computational Complexity"
                ]
            },
            {
                "number": 3,
                "name": "Infinite Impulse Response (IIR) Digital Filter Design",
                "topics": [
                    "Analog Filter Approximations: Butterworth and Chebyshev Filter Responses",
                    "IIR Filter Design by Impulse Invariance Method and Aliasing Issues",
                    "IIR Filter Design by Bilinear Transformation Method and Frequency Warping",
                    "Spectral Frequency Transformations for Lowpass, Highpass, Bandpass, and Bandstop",
                    "Realization of IIR Filters: Direct Form I, Direct Form II, Cascade, and Parallel Structures"
                ]
            },
            {
                "number": 4,
                "name": "Finite Impulse Response (FIR) Digital Filter Design",
                "topics": [
                    "Symmetric and Antisymmetric FIR Filters and Linear Phase Characteristics",
                    "FIR Filter Design using Windowing Techniques (Rectangular, Hamming, Hanning, Blackman)",
                    "Kaiser Window Design and Parameter Optimization",
                    "Frequency Sampling Method for FIR Filter Synthesis",
                    "Realization of FIR Filters: Direct Form, Cascade Form, and Lattice Structures"
                ]
            },
            {
                "number": 5,
                "name": "Finite Wordlength Effects and DSP Hardware Architectures",
                "topics": [
                    "Number Representations: Fixed-Point, Floating-Point, and Quantization Errors",
                    "ADC Quantization Noise Analysis and Signal-to-Quantization Noise Ratio (SQNR)",
                    "Coefficient Quantization Effects on Pole Locations in IIR/FIR Filters",
                    "Limit Cycle Oscillations and Overflow Limit Cycles in Recursive Systems",
                    "Architecture of Digital Signal Processors (Harvard Architecture, MAC Unit, Pipelining)"
                ]
            }
        ]
    }
]

# -------------------------------------------------------------
# TOPIC CLASSIFICATION RULES & KEYWORD HEURISTICS FOR SEM 7 & 8
# -------------------------------------------------------------
TOPIC_CLASSIFICATION_RULES: Dict[int, List[Dict[str, Any]]] = {
    # COURSE 38: Internet of Things
    38: [
        {"regex": r"architecture|functional block|communication model|characteristic|physical design|iot level", "unit": 1},
        {"regex": r"sensor|actuator|arduino|esp8266|esp32|raspberry pi|gpio|adc|dac|i2c|spi|uart|stepper|relay|servo", "unit": 2},
        {"regex": r"mqtt|coap|zigbee|lorawan|ble|bluetooth|802\.15\.4|6lowpan|rpl|dtls|rest|websocket|publish.*subscribe", "unit": 3},
        {"regex": r"cloud|aws iot|azure iot|telemetry|edge|fog|stream|tinyml|anomaly|time-series", "unit": 4},
        {"regex": r"security|vulnerability|cryptograph|smart city|iiot|industrial|predictive maintenance|scada|healthcare|agriculture", "unit": 5},
    ],
    # COURSE 39: Digital Image Processing
    39: [
        {"regex": r"perception|eye|sampling|quantization|spatial resolution|gray-level|pixel|neighbor|adjacency|connectivity|euclidean", "unit": 1},
        {"regex": r"spatial domain|histogram|equalization|specification|negative|gamma|power-law|contrast|laplacian|unsharp|smoothing|box filter|median filter", "unit": 2},
        {"regex": r"frequency domain|fourier|dft|fft|lowpass|highpass|butterworth|gaussian|wiener|degradation|restoration|noise", "unit": 3},
        {"regex": r"color|rgb|cmy|hsi|hsv|pseudocolor|morpholog|dilation|erosion|opening|closing|hit-or-miss|wavelet|dwt", "unit": 4},
        {"regex": r"segmentation|edge|sobel|prewitt|canny|hough|threshold|otsu|region growing|split.*merge|descriptor|boundary", "unit": 5},
    ],
    # COURSE 40: Security Governance, Risk and Compliance
    40: [
        {"regex": r"governance|cobit|27014|ciso|steering committee|kpi|kri|board of directors|strategic alignment|oversight", "unit": 1},
        {"regex": r"risk assessment|27005|sp 800-30|octave|asset valuation|threat profiling|risk appetite|tolerance|treatment|mitigate|transfer|accept", "unit": 2},
        {"regex": r"policy|policies|standard|baseline|procedure|eisp|issp|least privilege|need-to-know|vendor|supply chain|seta|awareness", "unit": 3},
        {"regex": r"compliance|gdpr|hipaa|sox|pci-dss|27001|27002|soa|audit|soc 1|soc 2|privacy|data protection", "unit": 4},
        {"regex": r"incident|csirt|forensic|800-61|bia|business impact|recovery|bcp|drp|rto|rpo|tabletop|disaster", "unit": 5},
    ],
    # COURSE 41: Security Risk Management and Principles
    41: [
        {"regex": r"cia triad|non-repudiation|threat landscape|apt|kill chain|mitre att&ck|cve|cvss|inherent risk|residual risk", "unit": 1},
        {"regex": r"threat model|stride|dread|pasta|dfd|trust boundar|attack tree|attack graph|defect|architecture review", "unit": 2},
        {"regex": r"qualitative|quantitative|sle|aro|ale|rosi|matrix|heat map|fair|monte carlo|loss expectancy", "unit": 3},
        {"regex": r"control|preventive|detective|corrective|800-53|defense in depth|zero trust|least privilege|cost-benefit", "unit": 4},
        {"regex": r"residual|acceptance|cyber insurance|underwriting|third-party|continuous monitoring|dashboard|board", "unit": 5},
    ],
    # COURSE 42: Information Security
    42: [
        {"regex": r"x\.800|attack|service|mechanism|classical|substitution|transposition|caesar|playfair|vigenere|steganograph|des|3des|diffusion|confusion", "unit": 1},
        {"regex": r"aes|subbytes|shiftrows|mixcolumns|addroundkey|mode of operation|ecb|cbc|cfb|ofb|ctr|gcm|rc4|chacha", "unit": 2},
        {"regex": r"asymmetric|fermat|euler|rsa|diffie-hellman|ecc|elliptic|kdc|x\.509|certificate|key exchange", "unit": 3},
        {"regex": r"hash|md5|sha|hmac|mac|digital signature|dss|kerberos|pki|ca|crl|ocsp|authentication", "unit": 4},
        {"regex": r"ipsec|ah|esp|ike|vpn|tls|ssl|pgp|s/mime|firewall|ngfw|packet filtering|ids|ips|intrusion", "unit": 5},
    ],
    # COURSE 43: Digital Signal Processing
    43: [
        {"regex": r"discrete-time|lti|convolution sum|difference equation|z-transform|roc|inverse z|system function|h\(z\)|pole-zero|stability", "unit": 1},
        {"regex": r"dft|idft|circular convolution|dit|dif|fft|radix-2|overlap-add|overlap-save|parseval", "unit": 2},
        {"regex": r"iir|butterworth|chebyshev|impulse invariance|bilinear transformation|frequency warping|direct form|cascade|parallel", "unit": 3},
        {"regex": r"fir|linear phase|window|hamming|hanning|blackman|kaiser|frequency sampling|symmetric", "unit": 4},
        {"regex": r"wordlength|fixed-point|floating-point|quantization|sqnr|limit cycle|dsp processor|harvard|mac unit", "unit": 5},
    ]
}
