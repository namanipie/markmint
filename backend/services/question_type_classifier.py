"""
Deterministic Question-Type Classifier for MarkMint Historical Corpus.

Classifies examination questions into actionable answer-mode archetypes
using strictly deterministic, rule-based syntactic, lexical, structural,
and mark-weighted signals.
"""

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Optional, List, Dict, Any


class QuestionType(str, Enum):
    OBJECTIVE_MCQ = "Objective / MCQ"
    SHORT_ANSWER = "Short Answer / Definition"
    EXPLANATION = "Explanation / Descriptive"
    NUMERICAL = "Numerical / Calculation"
    DERIVATION = "Derivation / Proof"
    COMPARISON = "Comparison / Distinction"
    PROGRAMMING = "Programming & Implementation"
    DESIGN = "Design & Application"
    UNCLASSIFIED = "Other / Unclassified"


class ClassificationConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TypeClassificationProposal:
    question_type: QuestionType
    confidence: ClassificationConfidence
    signals: List[str] = field(default_factory=list)
    raw_type: str = ""
    scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_type": self.question_type.value,
            "confidence": self.confidence.value,
            "signals": self.signals,
            "raw_type": self.raw_type,
            "scores": self.scores
        }


class DeterministicQuestionTypeClassifier:
    """
    Deterministic rule-based classifier evaluating question text, structure,
    syntax, and mark allocations.
    """

    # 1. Regex patterns for Objective / MCQ
    RE_MCQ_OPTIONS = re.compile(
        r'(?:\([A-D]\)|\[[A-D]\]|\([a-d]\)|\b[A-D]\.\s+[A-Za-z0-9])',
        re.MULTILINE
    )
    RE_FILL_BLANK = re.compile(r'_{3,}|fill\s+in\s+the\s+blank', re.IGNORECASE)
    RE_TRUE_FALSE = re.compile(r'\b(?:state\s+true\s+or\s+false|\(true/false\)|true\s+or\s+false)\b', re.IGNORECASE)

    # 2. Regex patterns for Comparison
    RE_COMPARISON = re.compile(
        r'\b(?:distinguish\s+between|differentiate\s+between|difference\s+between|differences\s+between|'
        r'compare\s+and\s+contrast|contrast\s+between|tabulate\s+the\s+differences?|'
        r'comparison\s+between|compare\b|versus|\bvs\b)\b',
        re.IGNORECASE
    )
    RE_CALCULUS_DIFF = re.compile(
        r'\b(?:differentiate\s+.*?\s+with\s+respect\s+to|differentiate\s+w\.?r\.?t|'
        r'differentiate\s+the\s+(?:following|function)|differential\s+calculus)\b',
        re.IGNORECASE
    )

    # 3. Regex patterns for Programming / Algorithm Implementation
    RE_PROGRAMMING = re.compile(
        r'\b(?:write\s+a\s+(?:c|python|java|cpp|c\+\+|shell)?\s*(?:program|code|script)|'
        r'write\s+a\s+function|write\s+an\s+algorithm|write\s+a\s+pseudocode|'
        r'write\s+(?:an?\s+)?sql\s+quer(?:y|ies)|write\s+(?:a\s+)?query\s+to|'
        r'implement\s+(?:an?\s+)?(?:algorithm|function|data\s+structure|stack|queue|linked\s+list)|'
        r'predict\s+the\s+output|find\s+the\s+output|find\s+the\s+error|'
        r'develop\s+a\s+(?:c|python|java|cpp)?\s*program)\b',
        re.IGNORECASE
    )
    RE_CODE_KEYWORDS = re.compile(
        r'\b(?:struct\s+[A-Za-z]|int\s+main\s*\(|#include\s*<|def\s+[a-zA-Z_]|'
        r'time\s+complexity|space\s+complexity|binary\s+search\s+tree|'
        r'call\s+by\s+value|call\s+by\s+reference|dynamic\s+memory\s+allocation|'
        r'malloc|free\(|pointer\s+arithmetic)\b',
        re.IGNORECASE
    )

    # 4. Regex patterns for Derivation / Proof
    RE_DERIVATION = re.compile(
        r'\b(?:derive\s+the\s+expression|derive\s+an\s+expression|derive\s+the\s+equation|'
        r'derive\s+the\s+relation|derive\s+the\s+formula|derive\s+schrodinger|'
        r'derive\s+time\s+independent|derive\s+hall\s+coefficient|'
        r'deduce\s+the\s+expression|deduce\s+the\s+relation|'
        r'obtain\s+an\s+expression\s+for|establish\s+the\s+relation|'
        r'state\s+and\s+prove|prove\s+that|show\s+that|'
        r'verify\s+cayley\s*-?\s*hamilton|verify\s+(?:green\'?s|stokes\'?|divergence)\s+theorem)\b',
        re.IGNORECASE
    )

    # 5. Regex patterns for Numerical / Calculation
    RE_CALCULATION = re.compile(
        r'\b(?:calculate|compute|find\s+the\s+value\s+of|evaluate\s+the\s+(?:integral|limit|expression|value)|'
        r'determine\s+the\s+value\s+of|solve\s+the\s+differential\s+equation|'
        r'solve\s+the\s+system\s+of|find\s+the\s+eigen\s*values?|'
        r'find\s+the\s+(?:radius|centre|center|equation|solution|area|volume|perimeter|length|angle|slope|gradient|divergence|curl|laplacian)|'
        r'find\s+the\s+rank|find\s+the\s+inverse|reduce\s+the\s+quadratic\s+form|'
        r'find\s+the\s+maximum\s+and\s+minimum|find\s+the\s+roots?|'
        r'calculate\s+the\s+(?:concentration|efficiency|potential|work|energy|force|velocity|acceleration|current|voltage|power)|'
        r'determine\s+the\s+(?:current|voltage|efficiency|frequency|impedance))\b',
        re.IGNORECASE
    )
    RE_MATH_EXPRESSION = re.compile(
        r'(?:\\begin\{bmatrix\}|\\begin\{pmatrix\}|\\int|\\sum|\\frac|\b[0-9]+(?:\.[0-9]+)?\s*(?:kg|mol|khz|mhz|ghz|hz|v|mv|ma|a|\u03a9|ohm|pf|uf|nf|cm|mm|m/s)\b)',
        re.IGNORECASE
    )

    # 6. Regex patterns for Design & Application
    RE_DESIGN = re.compile(
        r'\b(?:design\s+(?:an?\s+)?(?:[^\s]+\s+){0,4}(?:circuit|system|counter|amplifier|filter|controller|converter|datapath|schematic|fsm|automaton|logic)|'
        r'design\s+and\s+implement|synthesize\s+a\s+circuit|'
        r'construct\s+a\s+(?:state\s+diagram|state\s+table|truth\s+table\s+and\s+design)|'
        r'draw\s+the\s+schematic\s+and\s+design)\b',
        re.IGNORECASE
    )

    # 7. Regex patterns for Short Answer / Definition
    RE_SHORT_ANSWER = re.compile(
        r'\b(?:define\b|state\s+the\s+(?:principle|law|theorem|definition)|'
        r'what\s+is\s+meant\s+by|give\s+the\s+definition\s+of|'
        r'list\s+(?:any\s+)?(?:two|three|four|\d+)?\s*(?:advantages|disadvantages|applications|limitations|properties|features)|'
        r'name\s+any\s+(?:two|three|\d+)|mention\s+(?:any\s+)?(?:two|three|\d+)|'
        r'give\s+(?:two|three|\d+)\s+examples?\s+of|write\s+short\s+notes?\s+on)\b',
        re.IGNORECASE
    )

    # 8. Regex patterns for Explanation / Descriptive
    RE_EXPLANATION = re.compile(
        r'\b(?:explain\s+(?:the\s+working|in\s+detail|the\s+construction|the\s+concept|with\s+a?\s*neat\s+diagram)|'
        r'describe\s+(?:the\s+working|in\s+detail|the\s+process|the\s+construction|with\s+a?\s*neat\s+diagram)|'
        r'discuss\s+(?:in\s+detail|the\s+features|the\s+properties)|'
        r'elaborate\s+on|give\s+an\s+account\s+of|'
        r'explain\b|describe\b|discuss\b)\b',
        re.IGNORECASE
    )

    @classmethod
    def classify(
        cls,
        text: Optional[str],
        marks: Optional[float] = None,
        section_name: Optional[str] = None
    ) -> TypeClassificationProposal:
        """
        Classifies question into one of the 8 canonical answer-mode types,
        or returns Other / Unclassified if ambiguous or insufficient evidence.
        """
        raw_text = (text or "").strip()
        if not raw_text or len(raw_text) < 6:
            return TypeClassificationProposal(
                question_type=QuestionType.UNCLASSIFIED,
                confidence=ClassificationConfidence.LOW,
                signals=["insufficient_or_missing_text"]
            )

        clean_text = raw_text.lower()
        sec_name = (section_name or "").lower()
        marks_val = float(marks) if marks is not None else None

        # -------------------------------------------------------------
        # STEP 1: Objective / MCQ Evaluation (Highest structural specificity)
        # -------------------------------------------------------------
        options = cls.RE_MCQ_OPTIONS.findall(raw_text)
        distinct_options = set(o.upper().strip("()[] .") for o in options)
        has_mcq_structure = len(distinct_options) >= 2 or ("A" in distinct_options and "B" in distinct_options)
        has_fill_blank = bool(cls.RE_FILL_BLANK.search(clean_text))
        has_true_false = bool(cls.RE_TRUE_FALSE.search(clean_text))
        is_part_a = "part a" in sec_name or "part - a" in sec_name or "part-a" in sec_name

        if (has_mcq_structure or has_fill_blank or has_true_false):
            # Guard against subquestions: e.g. "(a) Explain... (b) Derive..."
            # In genuine MCQs, choices are short words/values, not multi-line questions with subquestion marks
            is_subquestion_false_positive = False
            if has_mcq_structure and len(distinct_options) == 2 and not ("C" in distinct_options or "D" in distinct_options):
                if re.search(r'\([a-b]\)\s*(?:explain|derive|calculate|discuss|write|define|prove)', clean_text):
                    is_subquestion_false_positive = True

            if not is_subquestion_false_positive:
                signals = []
                if has_mcq_structure:
                    signals.append(f"options_detected:{sorted(list(distinct_options))}")
                if has_fill_blank:
                    signals.append("fill_in_the_blank_indicator")
                if has_true_false:
                    signals.append("true_false_indicator")

                if marks_val is not None and marks_val <= 2.0:
                    signals.append(f"low_marks:{marks_val}")
                    return TypeClassificationProposal(
                        question_type=QuestionType.OBJECTIVE_MCQ,
                        confidence=ClassificationConfidence.HIGH,
                        signals=signals,
                        raw_type="objective_mcq"
                    )
                elif is_part_a:
                    signals.append("part_a_section")
                    return TypeClassificationProposal(
                        question_type=QuestionType.OBJECTIVE_MCQ,
                        confidence=ClassificationConfidence.HIGH,
                        signals=signals,
                        raw_type="objective_mcq"
                    )
                elif has_mcq_structure and len(distinct_options) >= 3:
                    return TypeClassificationProposal(
                        question_type=QuestionType.OBJECTIVE_MCQ,
                        confidence=ClassificationConfidence.HIGH,
                        signals=signals,
                        raw_type="objective_mcq"
                    )
                else:
                    return TypeClassificationProposal(
                        question_type=QuestionType.OBJECTIVE_MCQ,
                        confidence=ClassificationConfidence.MEDIUM,
                        signals=signals,
                        raw_type="objective_mcq"
                    )

        # -------------------------------------------------------------
        # STEP 2: Programming / Code Implementation
        # -------------------------------------------------------------
        prog_match = cls.RE_PROGRAMMING.search(clean_text)
        code_kw_match = cls.RE_CODE_KEYWORDS.search(clean_text)
        if prog_match or (code_kw_match and any(w in clean_text for w in ("write", "create", "implement", "construct"))):
            signals = []
            if prog_match:
                signals.append(f"programming_directive:{prog_match.group(0)}")
            if code_kw_match:
                signals.append(f"code_keyword:{code_kw_match.group(0)}")
            if marks_val is not None:
                signals.append(f"marks:{marks_val}")

            conf = ClassificationConfidence.HIGH if prog_match else ClassificationConfidence.MEDIUM
            return TypeClassificationProposal(
                question_type=QuestionType.PROGRAMMING,
                confidence=conf,
                signals=signals,
                raw_type="programming"
            )

        # -------------------------------------------------------------
        # STEP 3: Comparison / Distinction
        # (with Guardrail against calculus differentiation)
        # -------------------------------------------------------------
        comp_match = cls.RE_COMPARISON.search(clean_text)
        calc_diff_match = cls.RE_CALCULUS_DIFF.search(clean_text)

        if comp_match and not calc_diff_match:
            signals = [f"comparison_phrase:{comp_match.group(0)}"]
            if marks_val is not None:
                signals.append(f"marks:{marks_val}")
            return TypeClassificationProposal(
                question_type=QuestionType.COMPARISON,
                confidence=ClassificationConfidence.HIGH,
                signals=signals,
                raw_type="comparison"
            )

        # -------------------------------------------------------------
        # STEP 4: Derivation / Proof
        # -------------------------------------------------------------
        deriv_match = cls.RE_DERIVATION.search(clean_text)
        if deriv_match:
            signals = [f"derivation_directive:{deriv_match.group(0)}"]
            if marks_val is not None:
                signals.append(f"marks:{marks_val}")
            conf = ClassificationConfidence.HIGH if (marks_val is None or marks_val >= 4.0) else ClassificationConfidence.MEDIUM
            return TypeClassificationProposal(
                question_type=QuestionType.DERIVATION,
                confidence=conf,
                signals=signals,
                raw_type="derivation"
            )

        # -------------------------------------------------------------
        # STEP 5: Design & Application
        # -------------------------------------------------------------
        design_match = cls.RE_DESIGN.search(clean_text)
        if design_match:
            signals = [f"design_directive:{design_match.group(0)}"]
            if marks_val is not None:
                signals.append(f"marks:{marks_val}")
            return TypeClassificationProposal(
                question_type=QuestionType.DESIGN,
                confidence=ClassificationConfidence.HIGH,
                signals=signals,
                raw_type="design"
            )

        # -------------------------------------------------------------
        # STEP 6: Numerical / Calculation
        # -------------------------------------------------------------
        calc_match = cls.RE_CALCULATION.search(clean_text)
        has_math_expr = bool(cls.RE_MATH_EXPRESSION.search(raw_text))

        if calc_match or calc_diff_match or (has_math_expr and any(w in clean_text for w in ("solve", "find", "determine", "evaluate"))):
            signals = []
            if calc_match:
                signals.append(f"calculation_directive:{calc_match.group(0)}")
            if calc_diff_match:
                signals.append(f"calculus_differentiation:{calc_diff_match.group(0)}")
            if has_math_expr:
                signals.append("mathematical_expression_detected")
            if marks_val is not None:
                signals.append(f"marks:{marks_val}")

            conf = ClassificationConfidence.HIGH if calc_match else ClassificationConfidence.MEDIUM
            return TypeClassificationProposal(
                question_type=QuestionType.NUMERICAL,
                confidence=conf,
                signals=signals,
                raw_type="numerical"
            )

        # -------------------------------------------------------------
        # STEP 7: Short Answer / Definition vs Explanation / Descriptive
        # -------------------------------------------------------------
        short_match = cls.RE_SHORT_ANSWER.search(clean_text)
        expl_match = cls.RE_EXPLANATION.search(clean_text)
        word_count = len(clean_text.split())

        # If explicit definition/state keywords are present
        if short_match:
            signals = [f"short_answer_directive:{short_match.group(0)}"]
            if marks_val is not None:
                signals.append(f"marks:{marks_val}")

            # If marks are high (>= 8m), it is an extended descriptive question with a definition component
            if marks_val is not None and marks_val >= 8.0:
                signals.append(f"long_marks_override:{marks_val}")
                return TypeClassificationProposal(
                    question_type=QuestionType.EXPLANATION,
                    confidence=ClassificationConfidence.MEDIUM,
                    signals=signals,
                    raw_type="explanation"
                )
            elif marks_val is not None and marks_val <= 4.0:
                return TypeClassificationProposal(
                    question_type=QuestionType.SHORT_ANSWER,
                    confidence=ClassificationConfidence.HIGH,
                    signals=signals,
                    raw_type="short_answer"
                )
            elif word_count <= 25:
                return TypeClassificationProposal(
                    question_type=QuestionType.SHORT_ANSWER,
                    confidence=ClassificationConfidence.HIGH,
                    signals=signals,
                    raw_type="short_answer"
                )
            else:
                return TypeClassificationProposal(
                    question_type=QuestionType.SHORT_ANSWER,
                    confidence=ClassificationConfidence.MEDIUM,
                    signals=signals,
                    raw_type="short_answer"
                )

        # If explicit explanation keywords are present
        if expl_match:
            signals = [f"explanation_directive:{expl_match.group(0)}"]
            if marks_val is not None:
                signals.append(f"marks:{marks_val}")

            if marks_val is not None and marks_val <= 3.0 and word_count <= 15:
                # E.g. "Explain briefly X" (2m) -> Short Answer
                signals.append(f"brief_mark_weight:{marks_val}")
                return TypeClassificationProposal(
                    question_type=QuestionType.SHORT_ANSWER,
                    confidence=ClassificationConfidence.MEDIUM,
                    signals=signals,
                    raw_type="short_answer"
                )
            else:
                return TypeClassificationProposal(
                    question_type=QuestionType.EXPLANATION,
                    confidence=ClassificationConfidence.HIGH if (marks_val is None or marks_val >= 5.0) else ClassificationConfidence.MEDIUM,
                    signals=signals,
                    raw_type="explanation"
                )

        # -------------------------------------------------------------
        # STEP 8: Heuristic Fallbacks based on Mark & Sentence Structure
        # -------------------------------------------------------------
        # Questions starting with or containing "What is", "What are", "Define", "State", "Name", "List"
        if re.search(r'\b(?:what\s+is\b|what\s+are\b|state\b|name\b|list\b)', clean_text):
            signals = ["interrogative_definition_opener"]
            if marks_val is not None:
                signals.append(f"marks:{marks_val}")
            if marks_val is not None and marks_val <= 4.0:
                return TypeClassificationProposal(
                    question_type=QuestionType.SHORT_ANSWER,
                    confidence=ClassificationConfidence.MEDIUM,
                    signals=signals,
                    raw_type="short_answer"
                )
            elif marks_val is not None and marks_val >= 8.0:
                return TypeClassificationProposal(
                    question_type=QuestionType.EXPLANATION,
                    confidence=ClassificationConfidence.MEDIUM,
                    signals=signals,
                    raw_type="explanation"
                )

        # If question has high marks and substantial length, it is likely descriptive
        if marks_val is not None and marks_val >= 8.0 and word_count >= 15:
            return TypeClassificationProposal(
                question_type=QuestionType.EXPLANATION,
                confidence=ClassificationConfidence.LOW,
                signals=[f"high_marks_descriptive_heuristic:{marks_val}", f"word_count:{word_count}"],
                raw_type="explanation"
            )

        # -------------------------------------------------------------
        # STEP 9: Conservative Unclassified Fallback
        # (Ambiguous, composite without dominant signal, or unrecognized)
        # -------------------------------------------------------------
        return TypeClassificationProposal(
            question_type=QuestionType.UNCLASSIFIED,
            confidence=ClassificationConfidence.LOW,
            signals=["no_confident_discriminatory_signals", f"word_count:{word_count}"]
        )
