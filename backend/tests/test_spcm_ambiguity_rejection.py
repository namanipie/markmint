"""
Unit tests for SPCM ambiguity rejection and unmapped question handling.
Verifies conservative classification:
- Multi-topic matches are strictly marked AMBIGUOUS with topic_id=None.
- Composite OR exam questions across distinct units are rejected.
- Questions with missing or generic terminology are left UNMAPPED.
"""
import pytest
from backend.services.taxonomy_classifier import TaxonomyClassifierService
from backend.services.taxonomy_rules.spcm_rules import SPCM_TAXONOMY_RULES


@pytest.fixture
def classifier() -> TaxonomyClassifierService:
    return TaxonomyClassifierService(SPCM_TAXONOMY_RULES)


def test_spcm_multi_candidate_ambiguity_rejection(classifier: TaxonomyClassifierService) -> None:
    """Verifies that questions with multiple distinct plausible topics are strictly marked AMBIGUOUS."""
    # Mentions both Four-point probe (Unit 4) and Optical Joint Density of States (Unit 3)
    text = (
        "Explain the Four-point probe technique-linear method. "
        "--- OR --- "
        "Deduce an expression for optical joint density of states."
    )
    proposal = classifier.classify(101, text)
    assert proposal.confidence == "AMBIGUOUS"
    assert proposal.topic_id is None
    assert proposal.topic_name is None
    assert proposal.unit_id is None
    assert len(proposal.candidate_topics) >= 2
    candidate_names = [c["topic_name"] for c in proposal.candidate_topics]
    assert "Two-Point and Four-Point Probe Measurements" in candidate_names
    assert "Joint Density of States and Transition Rates" in candidate_names


def test_spcm_composite_subquestion_ambiguity(classifier: TaxonomyClassifierService) -> None:
    """Verifies composite questions with subparts (i) and (ii) across different units are rejected."""
    text = (
        "(i) Describe the behaviour of electron in a periodic potential. "
        "(ii) Enumerate the working concepts of PN junction and its biasing."
    )
    proposal = classifier.classify(102, text)
    assert proposal.confidence == "AMBIGUOUS"
    assert proposal.topic_id is None
    candidate_names = [c["topic_name"] for c in proposal.candidate_topics]
    assert "Band Theory and Kronig-Penney Model" in candidate_names
    assert "P-N Junction and Biasing" in candidate_names


def test_spcm_generic_text_remains_unmapped(classifier: TaxonomyClassifierService) -> None:
    """Verifies generic instructions or exam header text remain UNMAPPED."""
    text = "Answer all questions. Part A carries 20 marks. Each question carries 2 marks."
    proposal = classifier.classify(103, text)
    assert proposal.confidence == "UNMAPPED"
    assert proposal.method == "NO_MATCH"
    assert proposal.topic_id is None


def test_spcm_formula_without_context_remains_unmapped(classifier: TaxonomyClassifierService) -> None:
    """Verifies isolated numerical expressions without semantic context remain UNMAPPED."""
    text = "Calculate the value if x = 2.5 and y = 4.8 * 10^-19."
    proposal = classifier.classify(104, text)
    assert proposal.confidence == "UNMAPPED"
    assert proposal.topic_id is None
