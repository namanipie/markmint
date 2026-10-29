"""
Seed authoritative 5-unit syllabus topics for:
- Course 30: Transforms and Boundary Value Problems (21MAB201T)
- Course 31: Probability and Queueing Theory (21MAB204T)
Into production_corpus.db under units 186-190 and 191-195.
Also updates course_30_tbvp.json and course_31_pqt.json definitions.
"""
import os
import sys
import json
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")

TBVP_TOPICS = {
    186: [  # Unit 1: Partial Differential Equations
        "Formation of PDEs by Elimination of Arbitrary Constants and Functions",
        "Lagrange's Linear Partial Differential Equations",
        "Non-Linear First Order PDEs and Charpit's Method",
        "Homogeneous Linear PDEs with Constant Coefficients",
        "Non-Homogeneous Linear PDEs with Constant Coefficients"
    ],
    187: [  # Unit 2: Fourier Series
        "Dirichlet's Conditions and General Fourier Series Expansion",
        "Half-Range Fourier Sine and Cosine Series",
        "Parseval's Identity and Root Mean Square Value",
        "Harmonic Analysis and Practical Fourier Analysis"
    ],
    188: [  # Unit 3: Applications of Partial Differential Equations
        "Classification of Second-Order PDEs and Separation of Variables",
        "One-Dimensional Wave Equation and Vibrating String",
        "One-Dimensional Heat Conduction Equation",
        "Transient Heat Flow with Insulated and Non-Insulated Ends"
    ],
    189: [  # Unit 4: Two Dimensional Heat Equations
        "Steady-State Two-Dimensional Heat Conduction in Cartesian Coordinates",
        "Boundary Value Problems for Finite Rectangular Plates",
        "Steady-State Heat Flow in Semi-Infinite Plates",
        "Dirichlet and Neumann Boundary Value Problems for Laplace Equation"
    ],
    190: [  # Unit 5: Fourier Transforms
        "Fourier Integral Theorem and Complex Fourier Transform",
        "Fourier Sine and Cosine Transforms",
        "Properties of Fourier Transforms and Convolution Theorem",
        "Parseval's Identity for Fourier Transforms and Evaluation of Integrals"
    ]
}

PQT_TOPICS = {
    191: [  # Unit 1: Random Variables and Standard Distributions
        "Discrete and Continuous Random Variables and Probability Distributions",
        "Moment Generating Functions, Expectation, and Variance",
        "Binomial, Poisson, and Geometric Distributions",
        "Uniform, Exponential, and Normal Distributions"
    ],
    192: [  # Unit 2: Two-Dimensional Random Variables
        "Joint, Marginal, and Conditional Distributions",
        "Covariance and Karl Pearson's Correlation Coefficient",
        "Regression Lines and Equations of Two Variables",
        "Transformation of Bivariate Random Variables and Central Limit Theorem"
    ],
    193: [  # Unit 3: Random Processes and Markov Chains
        "Classification of Random Processes and Wide-Sense Stationarity",
        "Markov Chains and Transition Probability Matrix",
        "Chapman-Kolmogorov Equations and Limiting Distributions",
        "Poisson Process and Memoryless Property"
    ],
    194: [  # Unit 4: Queueing Models (Single Server)
        "Characteristics of Queueing Systems, Kendall's Notation, and Little's Formula",
        "(M/M/1) : (Infinity / FCFS) Single-Server Infinite Capacity Queue",
        "(M/M/1) : (k / FCFS) Single-Server Finite Capacity Queue",
        "Queue Length, Waiting Time, and Busy Period Distributions"
    ],
    195: [  # Unit 5: Advanced Queueing Models (Multi-Server)
        "(M/M/c) : (Infinity / FCFS) Multi-Server Infinite Capacity Queue",
        "(M/M/c) : (k / FCFS) Multi-Server Finite Capacity Queue",
        "Non-Markovian (M/G/1) Queue and Pollaczek-Khinchine Formula",
        "Queueing Networks and System Performance Analysis"
    ]
}

def seed_topics():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("Seeding Course 30 (TBVP) topics...")
    tbvp_inserted = 0
    tbvp_json_units = []
    for unit_id, topics in TBVP_TOPICS.items():
        unit_row = c.execute("SELECT number, name FROM units WHERE id = ?", (unit_id,)).fetchone()
        u_num, u_name = unit_row[0], unit_row[1]
        u_topics = []
        for t_name in topics:
            existing = c.execute("SELECT id FROM topics WHERE unit_id = ? AND name = ?", (unit_id, t_name)).fetchone()
            if not existing:
                c.execute("INSERT INTO topics (name, unit_id) VALUES (?, ?)", (t_name, unit_id))
                t_id = c.lastrowid
                tbvp_inserted += 1
            else:
                t_id = existing[0]
            u_topics.append({"id": t_id, "name": t_name})
        tbvp_json_units.append({"id": unit_id, "number": u_num, "name": u_name, "topics": u_topics})

    print("Seeding Course 31 (PQT) topics...")
    pqt_inserted = 0
    pqt_json_units = []
    for unit_id, topics in PQT_TOPICS.items():
        unit_row = c.execute("SELECT number, name FROM units WHERE id = ?", (unit_id,)).fetchone()
        u_num, u_name = unit_row[0], unit_row[1]
        u_topics = []
        for t_name in topics:
            existing = c.execute("SELECT id FROM topics WHERE unit_id = ? AND name = ?", (unit_id, t_name)).fetchone()
            if not existing:
                c.execute("INSERT INTO topics (name, unit_id) VALUES (?, ?)", (t_name, unit_id))
                t_id = c.lastrowid
                pqt_inserted += 1
            else:
                t_id = existing[0]
            u_topics.append({"id": t_id, "name": t_name})
        pqt_json_units.append({"id": unit_id, "number": u_num, "name": u_name, "topics": u_topics})

    conn.commit()
    conn.close()
    print(f"Database topics seeded: TBVP={tbvp_inserted} new, PQT={pqt_inserted} new.")

    # Update JSON taxonomy files
    tbvp_json_path = os.path.join(BASE_DIR, "backend", "services", "taxonomy_registry", "definitions", "course_30_tbvp.json")
    if os.path.exists(tbvp_json_path):
        with open(tbvp_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["units"] = tbvp_json_units
        with open(tbvp_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Updated course_30_tbvp.json")

    pqt_json_path = os.path.join(BASE_DIR, "backend", "services", "taxonomy_registry", "definitions", "course_31_pqt.json")
    if os.path.exists(pqt_json_path):
        with open(pqt_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["units"] = pqt_json_units
        with open(pqt_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Updated course_31_pqt.json")

if __name__ == "__main__":
    seed_topics()
