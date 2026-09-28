"""
Comprehensive test suite for DeterministicCognitiveDemandClassifier.

Verifies:
A. Clear recall/concept examples
B. Clear procedural/numerical examples
C. Clear proof/derivation examples
D. Clear programming implementation examples
E. Clear design examples
F. Ambiguous questions
G. Mathematical "evaluate" examples
H. "Design" engineering examples
I. Multi-part questions
J. OCR-corrupted text
K. Very short questions
L. Long scenario questions
M. Existing question_type conflicts
N. Questions with missing marks (invariance)
O. Questions with no unit/topic
"""

import json
import pytest

from backend.services.cognitive_demand_classifier import (
    CognitiveDemand,
    DemandConfidence,
    DeterministicCognitiveDemandClassifier,
)


class TestCognitiveDemandClassifier:

    # ------------------------------------------------------------------
    # A. Clear Recall / Concept Examples
    # ------------------------------------------------------------------
    def test_recall_and_concept_definitions(self):
        text = "Define eigenvalues and eigenvectors of a square matrix."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Short Answer / Definition")
        assert res.demand == CognitiveDemand.RECALL_AND_CONCEPT
        assert res.confidence == DemandConfidence.HIGH
        assert any("definition" in s or "short_answer" in s for s in res.signals)

    def test_recall_and_concept_state_law(self):
        text = "State the principle of superposition in quantum mechanics."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Short Answer / Definition")
        assert res.demand == CognitiveDemand.RECALL_AND_CONCEPT
        assert res.confidence == DemandConfidence.HIGH

    def test_recall_and_concept_listing(self):
        text = "List four applications of operational amplifiers in signal processing."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Short Answer / Definition")
        assert res.demand == CognitiveDemand.RECALL_AND_CONCEPT
        assert any("listing" in s for s in res.signals)

    def test_recall_and_concept_explanation(self):
        text = "Explain the working of a 4-stroke internal combustion engine with a neat sketch."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Explanation / Descriptive")
        assert res.demand == CognitiveDemand.RECALL_AND_CONCEPT

    def test_recall_and_concept_interrogative(self):
        text = "What is normalization? Explain first normal form (1NF)."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Explanation / Descriptive")
        assert res.demand == CognitiveDemand.RECALL_AND_CONCEPT

    # ------------------------------------------------------------------
    # B. Clear Procedural / Numerical Examples
    # ------------------------------------------------------------------
    def test_procedural_computation_find_eigenvalues(self):
        text = r"Find the eigenvalues and eigenvectors of the matrix $A = \begin{bmatrix} 2 & 1 \\ 1 & 2 \end{bmatrix}$."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Numerical / Calculation")
        assert res.demand == CognitiveDemand.PROCEDURAL_COMPUTATION
        assert res.confidence == DemandConfidence.HIGH

    def test_procedural_computation_calculate(self):
        text = r"Calculate the root mean square (RMS) value of the sinusoidal voltage $v(t) = 100 \sin(100\pi t)$."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Numerical / Calculation")
        assert res.demand == CognitiveDemand.PROCEDURAL_COMPUTATION

    def test_procedural_computation_solve_diff_equation(self):
        text = "Solve the differential equation (D^2 + 5D + 6)y = 3e^{2x}."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Numerical / Calculation")
        assert res.demand == CognitiveDemand.PROCEDURAL_COMPUTATION

    def test_procedural_computation_code_tracing(self):
        text = (
            "Predict the output of the following C code:\n"
            "#include <stdio.h>\n"
            "int main() { int x = 5; printf(\"%d\", x++ + ++x); return 0; }"
        )
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Programming & Implementation")
        assert res.demand == CognitiveDemand.PROCEDURAL_COMPUTATION
        assert any("code_tracing" in s or "programming_tracing" in s for s in res.signals)

    # ------------------------------------------------------------------
    # C. Clear Proof / Derivation Examples
    # ------------------------------------------------------------------
    def test_proof_derivation_schrodinger(self):
        text = "Derive the time-independent Schrodinger wave equation for a particle in a one-dimensional box."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Derivation / Proof")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN
        assert res.confidence == DemandConfidence.HIGH

    def test_proof_derivation_state_and_prove(self):
        text = "State and prove Cayley-Hamilton theorem."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Derivation / Proof")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN

    def test_proof_derivation_verify_theorem(self):
        text = "Verify Green's theorem in the plane for the vector field F = (x^2 - y)i + (y^2 + x)j over the square region."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Derivation / Proof")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN

    def test_proof_derivation_show_that(self):
        text = r"Show that the function f(z) = \sinh(z) is an analytic function for all complex numbers z."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Derivation / Proof")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN

    # ------------------------------------------------------------------
    # D. Clear Programming Implementation Examples
    # ------------------------------------------------------------------
    def test_programming_implementation_write_program(self):
        text = "Write a C program to implement binary search on a sorted array of integers."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Programming & Implementation")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN
        assert any("programming" in s for s in res.signals)

    def test_programming_implementation_data_structure(self):
        text = "Implement a circular queue using an array in C++ with enqueue and dequeue operations."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Programming & Implementation")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN

    def test_programming_implementation_sql_queries(self):
        text = "Write an SQL query to retrieve employee names whose salary is greater than the average salary of their department."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Programming & Implementation")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN

    # ------------------------------------------------------------------
    # E. Clear Design Examples
    # ------------------------------------------------------------------
    def test_design_circuit_system(self):
        text = "Design a 3-bit synchronous up-counter using JK flip-flops and draw the circuit diagram."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Design & Application")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN
        assert any("design" in s for s in res.signals)

    def test_design_dfa_automaton(self):
        text = "Construct a Deterministic Finite Automaton (DFA) that accepts the language L = {w in {0, 1}* | w ends with 01}."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Design & Application")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN

    def test_design_schema_normalization(self):
        text = "Normalize the relation R(A, B, C, D, E) up to BCNF given functional dependencies F = {A -> BC, CD -> E, B -> D}."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Other / Unclassified")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN
        assert any("normalize" in s for s in res.signals)

    # ------------------------------------------------------------------
    # F. Ambiguous Questions
    # ------------------------------------------------------------------
    def test_ambiguous_question_no_directives(self):
        text = "Consider the system of linear equations."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Other / Unclassified")
        assert res.demand == CognitiveDemand.UNCLASSIFIED
        assert res.confidence == DemandConfidence.LOW
        assert "no_discriminatory_signals" in res.signals

    def test_ambiguous_conflicting_prompt(self):
        # Combines strong proof/derivation directive with calculation directive in unitary prompt
        text = "State and prove Cayley-Hamilton theorem and calculate the inverse of matrix A."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Other / Unclassified")
        assert res.demand == CognitiveDemand.UNCLASSIFIED
        assert any("conflicting_signals" in s for s in res.signals)

    # ------------------------------------------------------------------
    # G. Mathematical "Evaluate" Examples
    # ------------------------------------------------------------------
    def test_mathematical_evaluate_integral(self):
        text = r"Evaluate \int_0^\pi x \sin x \, dx."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Numerical / Calculation")
        assert res.demand == CognitiveDemand.PROCEDURAL_COMPUTATION
        assert any("math_evaluate" in s or "numerical" in s for s in res.signals)

    def test_mathematical_evaluate_limit(self):
        text = r"Evaluate \lim_{x \to 0} \frac{\sin 3x}{\tan 2x}."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Numerical / Calculation")
        assert res.demand == CognitiveDemand.PROCEDURAL_COMPUTATION

    def test_mathematical_evaluate_colon_syntax(self):
        text = r"Evaluate: $\int_0^1 \int_0^1 (x + y) \, dx \, dy$."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Other / Unclassified")
        assert res.demand == CognitiveDemand.PROCEDURAL_COMPUTATION

    def test_analytical_evaluate_critique(self):
        text = "Critically evaluate the performance trade-offs of microkernel architecture versus monolithic kernel architecture."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Explanation / Descriptive")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN
        assert any("analytical_critique" in s for s in res.signals)

    # ------------------------------------------------------------------
    # H. "Design" Engineering Examples
    # ------------------------------------------------------------------
    def test_design_action_vs_noun_mcq(self):
        # When "design" appears as a noun in a factual MCQ, it is RECALL_AND_CONCEPT, NOT design task
        mcq_text = (
            "What does the ADDIE design model in engineering stand for?\n"
            "(A) Analyze, Develop, Design, Implement, Evaluate\n"
            "(B) Analysis, Draft, Deliver, Integrate, Execute\n"
            "(C) Architecture, Design, Deployment, Inspection, Evaluation\n"
            "(D) None of the above"
        )
        res = DeterministicCognitiveDemandClassifier.classify(mcq_text, question_type="Objective / MCQ")
        assert res.demand == CognitiveDemand.RECALL_AND_CONCEPT
        assert res.demand != CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN

    def test_design_engineering_circuit(self):
        text = "Design a combinational circuit with 3 inputs and 1 output that generates 1 when the binary input is a prime number."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Design & Application")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN

    # ------------------------------------------------------------------
    # I. Multi-part Questions
    # ------------------------------------------------------------------
    def test_multipart_unanimous_recall(self):
        text = "(a) Define normalization. (b) Explain 2NF and 3NF with examples."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Explanation / Descriptive")
        assert res.is_composite is True
        assert len(res.subparts) == 2
        assert res.demand == CognitiveDemand.RECALL_AND_CONCEPT

    def test_multipart_conflicting_demands(self):
        text = "(a) Define electric potential. (b) Calculate the potential at a distance of 5m from a 10uC charge."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Other / Unclassified")
        assert res.is_composite is True
        assert len(res.subparts) == 2
        assert res.demand == CognitiveDemand.UNCLASSIFIED
        assert any("conflicting_subparts" in s for s in res.signals)
        assert res.subparts[0].demand == CognitiveDemand.RECALL_AND_CONCEPT
        assert res.subparts[1].demand == CognitiveDemand.PROCEDURAL_COMPUTATION

    def test_multipart_structured_content(self):
        sc = {
            "text": "Answer the following subquestions.",
            "subquestions": [
                {"number": "i", "text": "Find the eigenvalues of the matrix A."},
                {"number": "ii", "text": "Solve the system Ax = b using Cramer's rule."}
            ]
        }
        res = DeterministicCognitiveDemandClassifier.classify(
            text="Answer the following subquestions.",
            structured_content=sc,
            question_type="Numerical / Calculation"
        )
        assert res.is_composite is True
        assert len(res.subparts) == 2
        assert res.demand == CognitiveDemand.PROCEDURAL_COMPUTATION
        assert res.subparts[0].demand == CognitiveDemand.PROCEDURAL_COMPUTATION
        assert res.subparts[1].demand == CognitiveDemand.PROCEDURAL_COMPUTATION

    # ------------------------------------------------------------------
    # J. OCR-Corrupted Text
    # ------------------------------------------------------------------
    def test_ocr_corrupted_noise(self):
        text = "%%%%%% ^^^^^^ !@#$!@#$ ***"
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Other / Unclassified")
        assert res.demand == CognitiveDemand.UNCLASSIFIED
        assert "ocr_corrupted_or_gibberish" in res.signals

    def test_ocr_corrupted_consonants(self):
        text = "bcdfghjklmnpqrstvwxyz bcdfghjklmnp"
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Other / Unclassified")
        assert res.demand == CognitiveDemand.UNCLASSIFIED
        assert "ocr_corrupted_or_gibberish" in res.signals

    # ------------------------------------------------------------------
    # K. Very Short Questions
    # ------------------------------------------------------------------
    def test_very_short_text(self):
        res1 = DeterministicCognitiveDemandClassifier.classify("{", question_type="Other / Unclassified")
        assert res1.demand == CognitiveDemand.UNCLASSIFIED
        assert "insufficient_text_length" in res1.signals

        res2 = DeterministicCognitiveDemandClassifier.classify("", question_type="Other / Unclassified")
        assert res2.demand == CognitiveDemand.UNCLASSIFIED

    # ------------------------------------------------------------------
    # L. Long Scenario Questions
    # ------------------------------------------------------------------
    def test_long_scenario_question(self):
        scenario = (
            "A university database contains tables for Students, Instructors, Courses, and Enrollments. "
            "Each student has a unique roll number, name, and GPA. Each course has a course code, title, and credits. "
            "An enrollment records which student took which course in which semester and their final grade. "
            "Construct an Entity-Relationship (ER) diagram for this system, identifying all entities, attributes, "
            "primary keys, and cardinality ratios."
        )
        res = DeterministicCognitiveDemandClassifier.classify(scenario, question_type="Design & Application")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN
        assert res.confidence == DemandConfidence.HIGH

    # ------------------------------------------------------------------
    # M. Existing question_type Conflicts
    # ------------------------------------------------------------------
    def test_conflict_qtype_numerical_vs_text_recall(self):
        # question_type claims Numerical / Calculation, but text is strictly recall with NO math
        text = "Define electric dipole moment and state its SI unit."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Numerical / Calculation")
        assert res.demand == CognitiveDemand.UNCLASSIFIED
        assert any("conflict" in s for s in res.signals)

    def test_conflict_qtype_short_answer_vs_text_computation(self):
        # question_type claims Short Answer / Definition, but text is pure calculation
        text = "Calculate the determinant and trace of the matrix [[1, 2], [3, 4]]."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Short Answer / Definition")
        assert res.demand == CognitiveDemand.UNCLASSIFIED
        assert any("conflict" in s for s in res.signals)

    # ------------------------------------------------------------------
    # N. Questions with Missing Marks (Marks Invariance)
    # ------------------------------------------------------------------
    def test_marks_invariance(self):
        text = "Find the eigenvalues and eigenvectors of matrix A."
        res_none = DeterministicCognitiveDemandClassifier.classify(text, question_type="Numerical / Calculation", marks=None)
        res_2m = DeterministicCognitiveDemandClassifier.classify(text, question_type="Numerical / Calculation", marks=2.0)
        res_16m = DeterministicCognitiveDemandClassifier.classify(text, question_type="Numerical / Calculation", marks=16.0)

        assert res_none.demand == res_2m.demand == res_16m.demand == CognitiveDemand.PROCEDURAL_COMPUTATION
        assert res_none.confidence == res_2m.confidence == res_16m.confidence

    # ------------------------------------------------------------------
    # O. Questions with No Unit / Topic
    # ------------------------------------------------------------------
    def test_question_with_no_unit_or_topic(self):
        text = "Explain the difference between call by value and call by reference in C."
        res = DeterministicCognitiveDemandClassifier.classify(text, question_type="Comparison / Distinction")
        assert res.demand == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN
        assert res.confidence == DemandConfidence.HIGH
