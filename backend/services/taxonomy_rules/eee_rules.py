"""
Structured, data-driven taxonomy classification rules for Course 14: Electrical and Electronics Engineering (EEE).
Loaded dynamically from the declarative taxonomy registry (Course ID 14).
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule
from backend.services.taxonomy_registry import get_taxonomy_registry

EEE_TAXONOMY_RULES: List[TaxonomyTopicRule] = get_taxonomy_registry().get_topic_rules(14)
