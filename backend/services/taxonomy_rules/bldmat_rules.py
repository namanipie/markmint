"""
Structured, data-driven taxonomy classification rules for Course 23: Building Materials in the Built Environment (BLDMAT).
Loaded dynamically from the declarative taxonomy registry (Course ID 23).
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule
from backend.services.taxonomy_registry import get_taxonomy_registry

BLDMAT_TAXONOMY_RULES: List[TaxonomyTopicRule] = get_taxonomy_registry().get_topic_rules(23)
