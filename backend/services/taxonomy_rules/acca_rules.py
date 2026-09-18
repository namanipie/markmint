"""
Structured, data-driven taxonomy classification rules for Course 16: Advanced Calculus and Complex Analysis (ACCA).
Loaded dynamically from the declarative taxonomy registry (Course ID 16).
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule
from backend.services.taxonomy_registry import get_taxonomy_registry

ACCA_TAXONOMY_RULES: List[TaxonomyTopicRule] = get_taxonomy_registry().get_topic_rules(16)
