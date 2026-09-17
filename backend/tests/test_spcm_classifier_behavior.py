"""
Unit tests for deterministic SPCM classifier behavior, phrase matching, and guardrails.
Verifies conservative matching, specific keyword detection, and domain guardrails.
"""
import pytest
from backend.services.taxonomy_classifier import TaxonomyClassifierService
from backend.services.taxonomy_rules.spcm_rules import SPCM_TAXONOMY_RULES


@pytest.fixture
def classifier() -> TaxonomyClassifierService:
    return TaxonomyClassifierService(SPCM_TAXONOMY_RULES)


def test_spcm_high_confidence_canonical_phrase(classifier: TaxonomyClassifierService) -> None:
    """Verifies that an exact canonical phrase matches with HIGH confidence."""
    proposal = classifier.classify(1, "Explain the Kronig-Penney model in detail with energy band formation.")
    assert proposal.confidence == "HIGH"
    assert proposal.method == "CANONICAL_PHRASE"
    assert proposal.topic_name == "Band Theory and Kronig-Penney Model"
    assert proposal.unit_name == "Free Electron Theory and Energy Bands"
    assert any("kronig-penney" in e for e in proposal.evidence)


def test_spcm_medium_confidence_keyword(classifier: TaxonomyClassifierService) -> None:
    """Verifies that a distinctive domain keyword produces MEDIUM confidence."""
    proposal = classifier.classify(2, "Explain the working of LCAO method in band structure.")
    assert proposal.confidence == "MEDIUM"
    assert proposal.method == "SPECIFIC_KEYWORD"
    assert proposal.topic_name == "Fermi Surface and Computational Band Structure"
    assert "lcao" in proposal.evidence


def test_spcm_domain_guardrail_rejection(classifier: TaxonomyClassifierService) -> None:
    """
    Verifies that domain guardrails prevent cross-unit false positives.
    E.g., Fermi's golden rule must NOT match Fermi Surface or Quantum Free Electron Theory.
    """
    proposal = classifier.classify(3, "Derive the optical transition rate using Fermi's golden rule.")
    assert proposal.confidence == "HIGH"
    assert proposal.topic_name == "Joint Density of States and Transition Rates"
    assert proposal.unit_name == "Optical Processes and Photovoltaic Devices"
    # Ensure it was not hijacked by Fermi Surface
    assert proposal.topic_id != 77


def test_spcm_drude_lorentz_matching(classifier: TaxonomyClassifierService) -> None:
    """Verifies classical free electron theory matches Drude and Lorentz."""
    proposal = classifier.classify(4, "State the main postulates of Drude and Lorentz model for metals.")
    assert proposal.confidence == "HIGH"
    assert proposal.topic_name == "Classical Free Electron Theory"
    assert proposal.unit_name == "Free Electron Theory and Energy Bands"


def test_spcm_hall_effect_matching(classifier: TaxonomyClassifierService) -> None:
    """Verifies Hall effect and mobility matching in Unit 4."""
    proposal = classifier.classify(5, "Derive the Hall coefficient and explain how carrier type is determined.")
    assert proposal.confidence == "HIGH"
    assert proposal.topic_name == "Hall Effect and Carrier Mobility"
    assert proposal.unit_name == "Semiconductor Measurements and Transport Equations"


def test_spcm_cnt_armchair_zigzag_matching(classifier: TaxonomyClassifierService) -> None:
    """Verifies carbon nanotubes chiral vectors and properties."""
    proposal = classifier.classify(6, "Explain the chiral vector of CNT and distinguish armchair carbon nanotube from zigzag.")
    assert proposal.confidence == "HIGH"
    assert proposal.topic_name == "Carbon Nanotubes (CNT)"
    assert proposal.unit_name == "Nanostructures and Characterization"


def test_spcm_van_der_pauw_matching(classifier: TaxonomyClassifierService) -> None:
    """Verifies Van der Pauw and four probe measurements."""
    proposal = classifier.classify(7, "Describe the resistivity measurement of thin films using Van der Pauw method.")
    assert proposal.confidence == "HIGH"
    assert proposal.topic_name == "Two-Point and Four-Point Probe Measurements"
    assert proposal.unit_name == "Semiconductor Measurements and Transport Equations"


def test_spcm_malformed_and_short_questions(classifier: TaxonomyClassifierService) -> None:
    """Verifies that empty or too-short question texts return UNMAPPED immediately."""
    p_empty = classifier.classify(8, "")
    assert p_empty.confidence == "UNMAPPED"
    assert p_empty.method == "NO_MATCH"

    p_short = classifier.classify(9, "ab")
    assert p_short.confidence == "UNMAPPED"
    assert p_short.method == "NO_MATCH"


def test_spcm_latex_and_symbol_normalization(classifier: TaxonomyClassifierService) -> None:
    """Verifies that mathematical symbols and LaTeX delimiters do not obstruct matching."""
    proposal = classifier.classify(
        10,
        "Calculate the \\textit{built-in potential} $V_{bi}$ for a $P-N$ junction under thermal equilibrium."
    )
    assert proposal.confidence in ("HIGH", "MEDIUM")
    assert proposal.topic_name == "P-N Junction and Biasing"
