import pytest
from backend.services.families.normalizer import QuestionNormalizer
from backend.services.families.manager import LLMStructuralGuardrail

def test_normalization_exact_matches():
    q1 = "Explain AVL tree rotations with an example."
    q2 = "Q.1) Explain AVL tree rotations with an example. [5 marks]"
    q3 = "explain avl tree rotations with an example"
    
    n1 = QuestionNormalizer.normalize(q1)
    n2 = QuestionNormalizer.normalize(q2)
    n3 = QuestionNormalizer.normalize(q3)
    
    # We strip punctuation and lowercase
    assert n1 == n3
    
    # Note: Normalizer doesn't strip marks on its own, it relies on QuestionExtractor which already stripped them.
    # In the raw text, Q.1 might remain but be normalized to "q1 explain..."
    # The Exact match logic in manager checks if n1 in n2 or n2 in n1.
    assert n1 in n2

def test_structural_guardrail():
    # Similar structure but different concepts
    q1 = "Explain the advantages of indexing."
    q2 = "Explain the advantages of process scheduling."
    
    # High embedding similarity simulates the scenario
    is_valid = LLMStructuralGuardrail.validate(q1, q2, 0.85)
    
    # The guardrail should catch this distinct pair
    assert is_valid is False

def test_structural_guardrail_pass():
    # Same concept, different wording
    q1 = "Demonstrate how an AVL tree is rebalanced after insertion."
    q2 = "Discuss the process of maintaining the balance factor in an AVL tree."
    
    is_valid = LLMStructuralGuardrail.validate(q1, q2, 0.85)
    
    # Guardrail shouldn't block this
    assert is_valid is True
