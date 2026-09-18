"""
Structured, data-driven taxonomy classification rules for Course 22: Probability and Statistics (PROB).
Loaded dynamically from the declarative taxonomy registry (Course ID 22).
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule
from backend.services.taxonomy_registry import get_taxonomy_registry

PROB_TAXONOMY_RULES: List[TaxonomyTopicRule] = get_taxonomy_registry().get_topic_rules(22)
