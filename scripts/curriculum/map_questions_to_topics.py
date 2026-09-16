"""
Deterministic topic mapping for Course 1 (Calculus) and Course 2 (Chemistry).
Connects unmapped questions in questions table to their canonical syllabus topics via question_topic.
Preserves existing mappings and maintains corpus invariants.
"""
import sqlite3

def run_mapping():
    conn = sqlite3.connect('production_corpus.db')
    c = conn.cursor()

    # 1. Course 1 specific mappings for unmapped questions
    course1_mappings = [
        (9, 14),   # dy/dx -> Partial Derivatives
        (10, 14),  # Euler's theorem partial derivatives -> Partial Derivatives
        (13, 5),   # (D^2 + 6D + 9) y -> Second-Order ODE
        (15, 34),  # Rectangular box max capacity -> Extrema and Optimization
        (16, 5),   # (D^2 + 3D + 2) y -> Second-Order ODE
        (20, 36),  # Stoke's theorem -> Vector Calculus
        (22, 5),   # y'' + 2y' - 3y = sin t -> Second-Order ODE
        (23, 37),  # Harmonic conjugate -> Complex Variables and Analytic Functions
        (24, 38),  # Conformal mapping transformation -> Conformal Mapping
        # Newly ingested historical exam questions (Exams 10, 11, 12, 13)
        (224, 33), # Quadratic form index/signature -> Quadratic Forms
        (225, 1),  # Eigen values of A -> Eigenvalues and Eigenvectors
        (226, 2),  # Orthogonal matrix -> Matrix Operations
        (227, 1),  # Sum and product of eigen values -> Eigenvalues and Eigenvectors
        (228, 14), # Implicit function dy/dx -> Partial Derivatives
        (229, 14), # Partial derivatives of f(x,y) -> Partial Derivatives
        (230, 14), # Jacobian functionally dependent -> Partial Derivatives
        (231, 5),  # (D^2 + 4)y = 0 -> Second-Order ODE
        (232, 5),  # (D^2 + 5D + 4)y = 0 -> Second-Order ODE
        (233, 5),  # Particular Integral of (D^2 - 4)y -> Second-Order ODE
        (234, 14), # Curvature of straight line -> Partial Derivatives
        (235, 14), # Envelope of family of curves -> Partial Derivatives
        (236, 14), # Radius of curvature in polar coordinates -> Partial Derivatives
        (237, 11), # Series convergence tests -> Convergence Tests
        (238, 11), # Absolutely/conditionally convergent series -> Convergence Tests
        (239, 5),  # Variation of parameters (D^2+2D+1)y -> Second-Order ODE
        (240, 11), # Test convergence of series -> Convergence Tests
        (241, 33), # Reduce quadratic form to canonical -> Quadratic Forms
        (242, 34), # Box of maximum capacity -> Extrema and Optimization
        (243, 5),  # y'' + 4y = 4tan 2x variation of parameters -> Second-Order ODE
        (244, 1),  # Eigen values of matrix -> Eigenvalues and Eigenvectors
        (245, 1),  # Inverse of eigen values -> Eigenvalues and Eigenvectors
        (246, 14), # Functional dependence Jacobian -> Partial Derivatives
        (247, 14), # Envelope and curvature -> Partial Derivatives
        (248, 33), # Deduce quadratic form to canonical -> Quadratic Forms
        (249, 11), # Test convergence of series -> Convergence Tests
        (250, 1),  # Characteristic equation of matrix -> Eigenvalues and Eigenvectors
        (251, 11), # Comparison test for series -> Convergence Tests
        (252, 17), # Gamma function Gamma(n+1) -> Double Integrals
        (253, 14), # Jacobian of polar coordinates -> Partial Derivatives
        (254, 35), # Maclaurin series -> Taylor Series
        (255, 5),  # (D^2 + 4)y = 0 -> Second-Order ODE
        (256, 5),  # Particular integral of ODE -> Second-Order ODE
        (257, 32), # Cayley-Hamilton theorem -> Cayley-Hamilton Theorem
        (258, 14), # Radius of curvature & Jacobian -> Partial Derivatives
        (259, 1),  # Curvature & eigenvalues -> Eigenvalues and Eigenvectors
    ]

    for q_id, t_id in course1_mappings:
        c.execute("INSERT OR IGNORE INTO question_topic (question_id, topic_id) VALUES (?, ?)", (q_id, t_id))

    # 2. Course 2 topic rules
    topic_rules = {
        46: ['particle in a box', 'one dimensional box', '1d box', 'eigen value by solving the equ', 'box'],
        47: ['radial and angular wave', 'hydrogen atom', 'radial wave', '1s orbital of hydrogen', 'bohr'],
        45: ['schrodinger', 'uncertainty principle', 'de-broglie', 'de broglie', 'quantum mechanics', 'wave function', 'quantum number', 'black body', 'photoelectric', 'orbital are distinguished by'],
        48: ['molecular orbital', 'mo theory', 'lcao', 'bond order', 'bonding and anti-bonding', 'o_2 molecule', 'h_2 molecule', 'homonuclear diatomic', 'paramagnetic', 'diamagnetic', 'mo concept', 'overlapping of p-p', 'everlaping of p-p', 's-s orbitals', 'overlap of s and p', 'h_2^+'],
        49: ['aromaticity', 'pi molecular', 'benzene', 'huckel', 'arenes', 'butadiene', 'aromatic', 'non-aromatic', 'anti-aromatic'],
        51: ['crystal field', 'cft', 'cfse', 'splitting in octahedral', 'splitting in a tetrahedral', 'high spin and low spin', 'd^6, low spin', 'spectrochemical series', 'octahedral field', 'tetrahedral complexes'],
        52: ['isomerism in transition', 'optical isomerism', 'linkage isomerism', 'coordination isomerism', 'geometrical isomerism', 'isomerism exhibited'],
        50: ['coordination', 'chelate', 'ligand', 'complex', 'edta', 'werner', 'coordination number', 'chelation', 'chelating', 'c.n 4'],
        53: ['plane of symmetry', 'axis of symmetry', 'symmetry element', 'center of symmetry', 'point group'],
        54: ['electromagnetic radiation', 'regions of electromagnetic', 'selection rule in spectroscopy', 'beer-lambert', 'absorption of radiation', 'spectroscopy fundamentals'],
        55: ['uv- vis', 'uv-visible', 'electronic transitions', 'chromophore', 'auxochrome', 'bathochromic', 'hypsochromic', 'selection rule for h atom in electronic', 'selection rule for many electron atom'],
        56: ['rotational spectrum', 'rotational spect', 'rigid rotor', 'selection rule for rotational', 'microwave radiation', 'microwave active'],
        57: ['vibrational', 'infrared', ' ir ', 'ir region', 'simple harmonic', 'selection rule for vibrational', "hooke's law", 'stretching frequency', 'degrees of freedom for vibration', 'fingerprint region'],
        58: ['nmr', 'nuclear magnetic', 'chemical shift', 'spin-spin coupling', 'radio frequency', 'tms', 'shielding and deshielding', 'splitting of signals', 'larmor frequency'],
        59: ['photoelectron', 'xps', 'photo-electron', 'ejected photoelectron', 'binding energy in xps', 'esca'],
        60: ['bragg', 'miller indices', 'diffraction of crystals', 'crystal structure', 'lattice', 'interplanar spacing', 'cubic system', 'x-ray diffraction', 'bravais'],
        61: ['gibbs', 'helmhotz', 'helmholtz', 'entropy', 'first law of thermodynamics', 'thermodynamic', 'free energy', 'carnot', 'maxwell relations', 'internal energy', 'joule-thomson', 'spontaneity', '-\\delta a = w_{max}'],
        62: ['hard and soft acids', 'hsab', 'pearson', 'hard acid', 'soft base'],
        63: ['intermolecular forces', 'van der waals', 'vander waal', 'hydrogen bonding', 'dipole-dipole', 'london dispersion'],
        64: ['real gases', 'van der waals equation', 'critical state', 'critical constants', 'liquefaction of gases', 'critical temperature', 'critical volume'],
        65: ['nernst', 'pourbaix', 'electrode potential', 'electrochemical', 'corrosion', 'cell emf', 'redox', 'galvanic', 'reference electrode', 'calomel', 'glass electrode', 'cell potential', 'standard potential'],
        66: ['solubility product', 'common ion effect', 'precipitation equilibrium'],
        68: ['conformational analysis', 'n-butane', 'conformations of cyclohexane', 'newmann projection', 'sawhorse', 'staggered', 'eclipsed', 'chair conformation', 'torsional strain'],
        69: ['fischer projection', 'newman projection', 'convert the following fischer'],
        26: ['stereoisomer', 'enantiomer', 'diastereomer', 'chirality', 'chiral', 'r/s configuration', 'cip sequence', 'optical activity', 'enantiomeric', 'structural isomerism'],
        27: ['reaction mechanism', 'sn1', 'sn2', 'e1 mechanism', 'e2 mechanism', 'e_1 mechanism', 'electrophilic addition', 'elimination reaction', 'nucleophilic substitution', 'carbocation intermediate', 'electrophilic mechanism of addition', 'nucleophilic mechanism', 'free radical mechanism'],
        70: ['nucleophile', 'electrophile', 'markovnikov', 'saytzeff', 'leaving group', 'electrophilic reagents', 'nucleophilic reagents'],
        71: ['oxidation', 'reduction', 'nabh4', 'kmno4', 'clemmensen', 'wolf kishner', 'reducing agent', 'oxidizing agent', 'alkenes are oxidized using kmno_4'],
        72: ['dieckmann', 'aldol', 'cannizzaro', 'condensation', 'synthesis of', 'wittig', 'grignard'],
        28: ['polymer', 'bakelite', 'teflon', 'pvc', 'thermoplastic', 'thermosetting', 'tacticity', 'isotactic', 'atactic', 'syndiotactic', 'vulcanization', 'nylon', 'conducting polymer'],
        29: ['polymerization', 'chain growth', 'step growth', 'addition polymerization', 'condensation polymerization', 'free radical polymerization', 'initiator'],
        30: ['stress-strain', "young's modulus", 'composite', 'ceramic matrix', 'yield point', 'tensile strength', 'viscosity', 'lubricant', 'ductility', 'hardness', 'toughness'],
        31: ['corrosion resistance', 'pilling-bedworth', 'sacrificial anode', 'cathodic protection', 'passivity'],
        20: ['periodic', 'periodicity', 'mendeleev', 'modern periodic'],
        21: ['atomic radius', 'atomic radii', 'variation in atomic'],
        22: ['ionization energy', 'ionization potential', 'first ionization', 'second ionization'],
        40: ['electron affinity', 'electron gain enthalpy'],
        41: ['electronegativity', 'pauling', 'mulliken'],
        42: ['ionic radius', 'lanthanide contraction', 'ionic size', 'cationic and anionic'],
        43: ['effective nuclear charge', 'slater', 'screening constant', 'shielding'],
        44: ['polarizability', 'fajans', 'polarizing power', "fajan's rule"]
    }

    questions_c2 = c.execute('''
        SELECT q.id, q.original_text 
        FROM questions q 
        JOIN sections s ON q.section_id = s.id 
        JOIN exams e ON s.exam_id = e.id 
        WHERE e.course_id = 2
    ''').fetchall()

    c2_mapped = 0
    for q_id, q_text in questions_c2:
        txt_lower = q_text.lower()
        matched_topics = []
        for t_id, kws in topic_rules.items():
            if any(kw in txt_lower for kw in kws):
                matched_topics.append(t_id)
        if matched_topics:
            t_id = matched_topics[0]
            c.execute("INSERT OR IGNORE INTO question_topic (question_id, topic_id) VALUES (?, ?)", (q_id, t_id))
            c2_mapped += 1

    conn.commit()
    print(f"Course 1: Added {len(course1_mappings)} mappings.")
    print(f"Course 2: Mapped {c2_mapped} of {len(questions_c2)} questions.")

    total_qt = c.execute("SELECT count(*) FROM question_topic").fetchone()[0]
    print(f"Total question_topic links now in DB: {total_qt}")
    conn.close()

if __name__ == '__main__':
    run_mapping()
