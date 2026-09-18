"""
Structured, data-driven taxonomy classification rules for Course 18: Electronic System and PCB Design (ESPCB).
Loaded dynamically from the declarative taxonomy registry (Course ID 18).
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule
from backend.services.taxonomy_registry import get_taxonomy_registry

ESPCB_TAXONOMY_RULES: List[TaxonomyTopicRule] = get_taxonomy_registry().get_topic_rules(18)
