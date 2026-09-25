"""
Unit tests for MarkMint Deterministic Question-Type Classifier.
Validates category accuracy, edge cases, domain guardrails, and deterministic stability.
"""

import pytest
from backend.services.question_type_classifier import (
    DeterministicQuestionTypeClassifier,
    QuestionType,
    ClassificationConfidence
)


# --- 1. CATEGORY TESTS ---

def test_objective_mcq_standard_options():
    text = "Which of the following is a volatile memory? (A) ROM (B) RAM (C) PROM (D) EEPROM"
    res = DeterministicQuestionTypeClassifier.classify(text, marks=1.0)
    assert res.question_type == QuestionType.OBJECTIVE_MCQ
    assert res.confidence == ClassificationConfidence.HIGH
    assert any("options_detected" in s for s in res.signals)


def test_objective_mcq_fill_in_the_blanks():
    text = "In a relational model, rows are called __________ and columns are called attributes."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=1.0)
    assert res.question_type == QuestionType.OBJECTIVE_MCQ
    assert res.confidence == ClassificationConfidence.HIGH


def test_objective_mcq_true_false():
    text = "State True or False: Every relation in BCNF is also in 3NF."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=1.0)
    assert res.question_type == QuestionType.OBJECTIVE_MCQ


def test_programming_c_program():
    text = "Write a C program to find the largest element in an array of N integers."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=8.0)
    assert res.question_type == QuestionType.PROGRAMMING
    assert res.confidence == ClassificationConfidence.HIGH
    assert any("programming_directive" in s for s in res.signals)


def test_programming_sql_query():
    text = "Write SQL query to retrieve employee details whose department is 'Research'."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=8.0)
    assert res.question_type == QuestionType.PROGRAMMING
    assert res.confidence == ClassificationConfidence.HIGH


def test_programming_algorithm_flowchart():
    text = "Write an algorithm to implement binary search on a sorted array."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=6.0)
    assert res.question_type == QuestionType.PROGRAMMING


def test_derivation_schrodinger():
    text = "Derive time independent Schrodinger wave equation for a particle in a one-dimensional potential well."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=15.0)
    assert res.question_type == QuestionType.DERIVATION
    assert res.confidence == ClassificationConfidence.HIGH


def test_derivation_cayley_hamilton_theorem():
    text = "Verify Cayley-Hamilton theorem for the matrix A and hence find A^-1."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=8.0)
    assert res.question_type == QuestionType.DERIVATION
    assert res.confidence == ClassificationConfidence.HIGH


def test_comparison_distinguish_between():
    text = "Distinguish between recursion and iteration with suitable examples."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=6.0)
    assert res.question_type == QuestionType.COMPARISON
    assert res.confidence == ClassificationConfidence.HIGH


def test_comparison_compare_and_contrast():
    text = "Compare and contrast CISC and RISC computer architectures."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=8.0)
    assert res.question_type == QuestionType.COMPARISON


def test_numerical_matrix_eigenvalues():
    text = "Find the eigen values and eigen vectors of the matrix \\begin{bmatrix} 2 & 1 \\\\ 1 & 2 \\end{bmatrix}."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=8.0)
    assert res.question_type == QuestionType.NUMERICAL
    assert res.confidence == ClassificationConfidence.HIGH


def test_numerical_physics_calculation():
    text = "Calculate the wavelength of an electron moving with a velocity of 10^6 m/s."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=6.0)
    assert res.question_type == QuestionType.NUMERICAL
    assert res.confidence == ClassificationConfidence.HIGH


def test_short_answer_definition():
    text = "Define Le Chatelier principle and mention its significance."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=2.0)
    assert res.question_type == QuestionType.SHORT_ANSWER
    assert res.confidence == ClassificationConfidence.HIGH


def test_short_answer_list_two():
    text = "List any two differences between primary and secondary storage."
    # Notice: 'list any two' with marks <= 4m
    res = DeterministicQuestionTypeClassifier.classify(text, marks=2.0)
    assert res.question_type in (QuestionType.SHORT_ANSWER, QuestionType.COMPARISON)


def test_explanation_descriptive():
    text = "Explain the construction and working principle of a cathode ray oscilloscope with a neat block diagram."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=12.0)
    assert res.question_type == QuestionType.EXPLANATION
    assert res.confidence == ClassificationConfidence.HIGH


def test_design_circuit():
    text = "Design a synchronous modulo-8 counter using JK flip-flops."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=15.0)
    assert res.question_type == QuestionType.DESIGN
    assert res.confidence == ClassificationConfidence.HIGH


# --- 2. DOMAIN GUARDRAILS & EDGE CASES ---

def test_calculus_differentiation_guardrail():
    """
    CRITICAL: 'Differentiate y with respect to x' must be classified as NUMERICAL,
    NOT as COMPARISON.
    """
    text = "Differentiate y = x^4 * e^(2x) with respect to x."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=4.0)
    assert res.question_type == QuestionType.NUMERICAL
    assert res.question_type != QuestionType.COMPARISON


def test_empty_and_corrupt_text():
    res_empty = DeterministicQuestionTypeClassifier.classify("", marks=2.0)
    assert res_empty.question_type == QuestionType.UNCLASSIFIED
    assert res_empty.confidence == ClassificationConfidence.LOW

    res_short = DeterministicQuestionTypeClassifier.classify("ab", marks=2.0)
    assert res_short.question_type == QuestionType.UNCLASSIFIED
    assert res_short.confidence == ClassificationConfidence.LOW

    res_none = DeterministicQuestionTypeClassifier.classify(None, marks=None)
    assert res_none.question_type == QuestionType.UNCLASSIFIED


def test_missing_marks_handled_gracefully():
    """Without marks, syntactic keywords should still determine the type."""
    text = "Derive the expression for electric field intensity due to a dipole."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=None)
    assert res.question_type == QuestionType.DERIVATION

    text_prog = "Write a C program to check whether a matrix is symmetric."
    res_prog = DeterministicQuestionTypeClassifier.classify(text_prog, marks=None)
    assert res_prog.question_type == QuestionType.PROGRAMMING


def test_subquestion_does_not_falsely_trigger_mcq():
    """
    A long answer question with subquestions (a) and (b) should NOT be classified as MCQ.
    """
    text = "21. (a) Derive the expression for capacitance of a parallel plate capacitor. (b) Calculate the energy stored."
    res = DeterministicQuestionTypeClassifier.classify(text, marks=15.0)
    assert res.question_type != QuestionType.OBJECTIVE_MCQ
    assert res.question_type in (QuestionType.DERIVATION, QuestionType.NUMERICAL)


def test_deterministic_stability():
    """Verify 100 identical executions produce identical output."""
    text = "Explain the working of LCAO method in band structure."
    first = DeterministicQuestionTypeClassifier.classify(text, marks=8.0)
    for _ in range(100):
        current = DeterministicQuestionTypeClassifier.classify(text, marks=8.0)
        assert current.question_type == first.question_type
        assert current.confidence == first.confidence
        assert current.signals == first.signals
