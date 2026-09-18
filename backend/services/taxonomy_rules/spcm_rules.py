"""
Structured, data-driven taxonomy classification rules for Course 13: Semiconductor Physics and Computational Methods (SPCM).
Loaded dynamically from the declarative taxonomy registry (Course ID 13).
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule
from backend.services.taxonomy_registry import get_taxonomy_registry

SPCM_TAXONOMY_RULES: List[TaxonomyTopicRule] = get_taxonomy_registry().get_topic_rules(13)
