"""
Structured, data-driven taxonomy classification rules for Course 17: Object Oriented Design and Programming (OODP).
Loaded dynamically from the declarative taxonomy registry (Course ID 17).
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule
from backend.services.taxonomy_registry import get_taxonomy_registry

OODP_TAXONOMY_RULES: List[TaxonomyTopicRule] = get_taxonomy_registry().get_topic_rules(17)
