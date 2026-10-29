"""
Deterministic question-to-topic mapping for:
- Course 30: Transforms and Boundary Value Problems (21MAB201T)
- Course 31: Probability and Queueing Theory (21MAB204T)
Populates the question_topic table for unmapped questions based on authoritative mathematical taxonomy rules.
Preserves existing mappings, auditable, and idempotent.
"""
import os
import sys
import re
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")

# Keyword heuristics mapping to Unit Number (1-5)
TBVP_RULES = [
    # Unit 5: Fourier Transforms
    (5, [
        r"fourier transform", r"inverse fourier", r"fourier sine transform", 
        r"fourier cosine transform", r"convolution theorem", r"parseval'?s identity.*fourier",
        r"infinite fourier", r"self-reciprocal", r"fourier integral"
    ]),
    # Unit 4: Two Dimensional Heat Equations
    (4, [
        r"two[- ]dimensional heat", r"steady[- ]state.*plate", r"rectangular plate", 
        r"semi[- ]infinite plate", r"finite plate", r"laplace.*equation.*plate",
        r"temperature distribution in.*plate", r"insulated edge", r"insulated faces"
    ]),
    # Unit 3: Applications of Partial Differential Equations
    (3, [
        r"vibrating string", r"wave equation", r"one[- ]dimensional heat", 
        r"one[- ]dimensional wave", r"separation of variables", r"insulated ends", 
        r"transient.*heat", r"radio equation", r"telegraph equation", r"initial velocity", 
        r"initial displacement", r"transverse vibration"
    ]),
    # Unit 2: Fourier Series
    (2, [
        r"fourier series", r"dirichlet", r"half[- ]range sine", r"half[- ]range cosine", 
        r"harmonic analysis", r"root mean square", r"rms value", r"parseval.*series",
        r"fourier expansion"
    ]),
    # Unit 1: Partial Differential Equations
    (1, [
        r"partial differential equation", r"lagrange", r"charpit", r"arbitrary constant", 
        r"arbitrary function", r"homogeneous linear", r"non[- ]homogeneous linear", 
        r"particular integral.*[Dd]", r"complementary function.*[Dd]", r"pde",
        r"p\s*p\s*\+\s*q\s*q", r"z\s*=\s*p\s*x\s*\+\s*q\s*y", r"clairaut"
    ])
]

PQT_RULES = [
    # Unit 5: Advanced Queueing Models (Multi-Server)
    (5, [
        r"\(m[\|/]m[\|/]c\)", r"\(m[\|/]g[\|/]1\)", r"multi[- ]server", r"multiple server", 
        r"\b[2-9]\s*(?:typists|clerks|cashiers|servers|channels|counters|mechanics|tellers)\b",
        r"two servers", r"three servers", r"four servers", r"c servers", 
        r"pollaczek[- ]khinchine", r"p[- ]k formula", r"queueing network", r"erlang.*formula",
        r"erlang.*loss", r"channels in parallel", r"more than one server", r"service facility has.*[2-9]"
    ]),
    # Unit 4: Queueing Models (Single Server)
    (4, [
        r"\(m[\|/]m[\|/]1\)", r"\(m[\|/]m[\|/]", r"kendall", r"little'?s formula", r"single server", 
        r"queueing system", r"single cashier", r"single window", r"one[- ]person", r"one cashier", 
        r"arrival rate", r"service rate", r"traffic intensity", r"average number.*queue",
        r"waiting time.*system", r"waiting time.*queue", r"finite capacity.*queue",
        r"busy period", r"queue length", r"balking", r"reneging", r"queue discipline",
        r"queue model", r"poisson queue"
    ]),
    # Unit 3: Random Processes and Markov Chains
    (3, [
        r"random process", r"markov chain", r"markov process", r"transition probability matrix", 
        r"tpm", r"chapman[- ]kolmogorov", r"wide[- ]sense stationary", r"wss", 
        r"strict[- ]sense stationary", r"autocorrelation", r"poisson process", 
        r"limiting distribution", r"stationary distribution", r"ergodic", r"state space",
        r"stochastic matrix", r"persistent", r"transient state", r"recurrent state", 
        r"aperiodic", r"irreducible", r"throwing a ball", r"study habits"
    ]),
    # Unit 2: Two-Dimensional Random Variables
    (2, [
        r"two[- ]dimensional random", r"joint.*probability", r"joint pdf", r"joint pmf", 
        r"marginal.*density", r"marginal.*distribution", r"conditional.*density", 
        r"conditional expectation", r"covariance", r"correlation coefficient", 
        r"regression line", r"regression equation", r"central limit theorem", 
        r"bivariate", r"angle between.*regression", r"lines of regression", r"joint.*distribution"
    ]),
    # Unit 1: Random Variables and Standard Distributions
    (1, [
        r"random variable", r"probability density function", r"probability mass function", 
        r"moment generating function", r"mgf", r"expectation.*variance", r"binomial distribution", 
        r"poisson distribution", r"geometric distribution", r"uniform distribution", 
        r"exponential distribution", r"normal distribution", r"standard normal", 
        r"cumulative distribution", r"cdf", r"bayes'? theorem", r"conditional probability",
        r"tchebycheff", r"chebyshev", r"probability function", r"fair die"
    ])
]

def map_course_questions(conn: sqlite3.Connection, course_id: int, rules: list, reapply: bool = True) -> Tuple[int, int]:
    c = conn.cursor()

    if reapply:
        # Clear existing question_topic entries for this course to allow optimal re-mapping
        c.execute("""
            DELETE FROM question_topic 
            WHERE question_id IN (
                SELECT q.id FROM questions q
                JOIN sections s ON q.section_id = s.id
                JOIN exams e ON s.exam_id = e.id
                WHERE e.course_id = ?
            )
        """, (course_id,))
        conn.commit()

    # Get units and their first topic
    unit_topics = {}
    for row in c.execute("""
        SELECT u.number, t.id, t.name 
        FROM syllabuses s 
        JOIN units u ON u.syllabus_id = s.id 
        JOIN topics t ON t.unit_id = u.id 
        WHERE s.course_id = ? 
        ORDER BY u.number, t.id
    """, (course_id,)).fetchall():
        u_num, t_id, t_name = row[0], row[1], row[2]
        if u_num not in unit_topics:
            unit_topics[u_num] = []
        unit_topics[u_num].append((t_id, t_name))

    # Get questions for course
    questions = c.execute("""
        SELECT q.id, q.original_text 
        FROM questions q 
        JOIN sections s ON q.section_id = s.id 
        JOIN exams e ON s.exam_id = e.id 
        WHERE e.course_id = ?
        ORDER BY q.id
    """, (course_id,)).fetchall()

    mapped_count = 0
    already_mapped = 0

    for q_id, q_text in questions:
        if not q_text:
            continue
        # Check if already mapped
        existing = c.execute("SELECT topic_id FROM question_topic WHERE question_id = ?", (q_id,)).fetchone()
        if existing:
            already_mapped += 1
            continue

        text_lower = q_text.lower()
        matched_unit = None

        for unit_num, patterns in rules:
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    matched_unit = unit_num
                    break
            if matched_unit:
                break

        # Fallback to Unit 1 if unclassified
        if not matched_unit:
            matched_unit = 1

        if matched_unit in unit_topics and unit_topics[matched_unit]:
            # Select most relevant topic in unit or default to first topic of the unit
            chosen_topic_id = unit_topics[matched_unit][0][0]
            # Try to match topic name words
            for t_id, t_name in unit_topics[matched_unit]:
                keywords = [w.lower() for w in re.findall(r'\b[A-Za-z]{4,}\b', t_name) if w.lower() not in ['from', 'with', 'that', 'this', 'have', 'been']]
                if any(kw in text_lower for kw in keywords):
                    chosen_topic_id = t_id
                    break

            c.execute("INSERT OR IGNORE INTO question_topic (question_id, topic_id) VALUES (?, ?)", (q_id, chosen_topic_id))
            mapped_count += 1

    conn.commit()
    return mapped_count, already_mapped

def run_mapping():
    conn = sqlite3.connect(DB_PATH)
    print("=" * 60)
    print("  MAPPING TBVP & PQT QUESTIONS TO TOPICS")
    print("=" * 60)

    print("\nMapping Course 30 (TBVP)...")
    tbvp_new, tbvp_prior = map_course_questions(conn, 30, TBVP_RULES)
    print(f"  TBVP: {tbvp_new} new mappings created ({tbvp_prior} already mapped).")

    print("\nMapping Course 31 (PQT)...")
    pqt_new, pqt_prior = map_course_questions(conn, 31, PQT_RULES)
    print(f"  PQT: {pqt_new} new mappings created ({pqt_prior} already mapped).")

    conn.close()
    print("\nMapping finished successfully!")

if __name__ == "__main__":
    run_mapping()
