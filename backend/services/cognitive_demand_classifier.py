"""
Deterministic Cognitive Demand Classifier for MintAI Historical Exam DNA.

Classifies examination questions into observable cognitive demand archetypes:
1. RECALL_AND_CONCEPT: Knowledge retrieval, definitions, conceptual explanations,
   principles, factual identification, listing components.
2. PROCEDURAL_COMPUTATION: Mathematical calculations, algorithmic execution,
   numerical solving, code tracing, procedural transformations.
3. ANALYTICAL_PROOF_AND_DESIGN: Formal proofs, derivations, system/schema/algorithm design,
   open-ended synthesis, analytical comparison, debugging/failure analysis.
4. UNCLASSIFIED: Insufficient, indeterminate, or contradictory evidence.

IMPORTANT:
These are OBSERVABLE DEMAND ARCHETYPES, not psychological difficulty levels.
The classifier must never claim that one archetype is objectively "harder" than another.
Marks MUST NOT determine cognitive demand.
"""

from dataclasses import dataclass, field
from enum import Enum
import json
import re
from typing import Optional, List, Dict, Any, Union, Tuple


class CognitiveDemand(str, Enum):
    RECALL_AND_CONCEPT = "RECALL_AND_CONCEPT"
    PROCEDURAL_COMPUTATION = "PROCEDURAL_COMPUTATION"
    ANALYTICAL_PROOF_AND_DESIGN = "ANALYTICAL_PROOF_AND_DESIGN"
    UNCLASSIFIED = "UNCLASSIFIED"


class DemandConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SubpartDemand:
    subpart_label: str
    text: str
    demand: CognitiveDemand
    confidence: DemandConfidence
    signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subpart_label": self.subpart_label,
            "text": self.text,
            "demand": self.demand.value,
            "confidence": self.confidence.value,
            "signals": self.signals,
        }


@dataclass
class DemandClassificationProposal:
    demand: CognitiveDemand
    confidence: DemandConfidence
    signals: List[str] = field(default_factory=list)
    subparts: List[SubpartDemand] = field(default_factory=list)
    is_composite: bool = False
    evidence_layer: Optional[str] = None
    raw_demand: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "demand": self.demand.value,
            "confidence": self.confidence.value,
            "signals": self.signals,
            "subparts": [sp.to_dict() for sp in self.subparts],
            "is_composite": self.is_composite,
            "evidence_layer": self.evidence_layer,
            "raw_demand": self.raw_demand or self.demand.value,
        }


class DeterministicCognitiveDemandClassifier:
    """
    Deterministic rule-based classifier evaluating question text, structure,
    syntax, and verified answer-modality types.
    """

    # 1. Regex patterns for Analytical Proof & Design
    RE_PROOF_DERIVATION = re.compile(
        r'\b(?:derive\s+(?:the|an)\s+(?:expression|equation|relation|formula|model|schrodinger|time\s+independent|hall\s+coefficient|density\s+of\s+states|wave\s+equation)|'
        r'(?:^|\n|;\s*|\.\s*|\bhence\s+)\s*derive\b|'
        r'state\s+and\s+prove|prove\s+that|show\s+that|demonstrate\s+that|'
        r'deduce\s+(?:the|an)\s+expression|deduce\s+(?:the|an)\s+relation|'
        r'obtain\s+(?:the|an)\s+expression\s+for|establish\s+the\s+relation|'
        r'verify\s+cayley\s*-?\s*hamilton|verify\s+(?:green\'?s?|stoke\'?s?|divergence|gauss\'?s?)\s+theorem|'
        r'verify\s+whether\s+the\s+function.*?is\s+harmonic|prove\s+or\s+disprove)\b',
        re.IGNORECASE
    )

    RE_DESIGN_CONSTRUCTIVE = re.compile(
        r'\b(?:design\s+(?:an?\s+)?(?:[^\s]+\s+){0,4}(?:circuit|system|counter|amplifier|filter|controller|converter|datapath|schematic|fsm|automaton|dfa|nfa|turing\s+machine|schema|database|table|class|interface|architecture|pipeline|protocol)|'
        r'design\s+and\s+implement|synthesize\s+a\s+circuit|'
        r'construct\s+a\s+(?:state\s+diagram|state\s+table|truth\s+table\s+and\s+design|dfa|nfa|parse\s+tree|derivation\s+tree)|'
        r'normalize\s+(?:the\s+)?(?:following|given\s+)?relation|'
        r'normalize\b.*?\b(?:3nf|bcnf|4nf|2nf|normal\s+form)|'
        r'find\s+the\s+canonical\s+cover|find\s+(?:all\s+)?candidate\s+keys?\s+(?:and\s+normalize)?)\b',
        re.IGNORECASE
    )

    RE_PROGRAMMING_IMPL = re.compile(
        r'\b(?:write\s+a\s+(?:c|python|java|cpp|c\+\+|shell|bash|sql)?\s*(?:program|code|query|queries|script|function|procedure|trigger)|'
        r'develop\s+a\s+(?:c|python|java|cpp)?\s*program|'
        r'write\s+an\s+algorithm|write\s+(?:a\s+)?pseudocode|'
        r'implement\s+(?:an?\s+)?(?:algorithm|function|data\s+structure|stack|queue|linked\s+list|tree|graph))\b',
        re.IGNORECASE
    )

    RE_COMPARISON = re.compile(
        r'\b(?:distinguish\s+between|differentiate\s+between|difference\s+between|differences\s+between|'
        r'compare\s+and\s+contrast|contrast\s+between|tabulate\s+the\s+differences?|comparison\s+between|'
        r'(?:differentiate|distinguish)\s+[a-zA-Z0-9\s\-]+(?:\band\b|\bfrom\b))\b',
        re.IGNORECASE
    )

    RE_CALCULUS_DIFF = re.compile(
        r'\b(?:differentiate\s+.*?\s+with\s+respect\s+to|differentiate\s+w\.?r\.?t|differentiate\s+the\s+(?:following|function)|differential\s+calculus)\b',
        re.IGNORECASE
    )

    RE_PHYSICAL_DIFF = re.compile(
        r'\b(?:phase|potential|path|pressure|height|temperature|level)\s+difference\s+between\b',
        re.IGNORECASE
    )

    RE_ANALYTICAL_EVAL = re.compile(
        r'\b(?:analyze\s+(?:the\s+time\s+complexity|the\s+space\s+complexity|the\s+performance|the\s+trade-offs?)|'
        r'critically\s+(?:analyze|evaluate|examine)|'
        r'evaluate\s+the\s+(?:challenges|implications|trade-offs|pros\s+and\s+cons|impact)|'
        r'debug|find\s+the\s+bug|find\s+the\s+error\s+and\s+correct|identify\s+the\s+flaw)\b',
        re.IGNORECASE
    )

    # 2. Regex patterns for Procedural Computation
    RE_NUMERICAL_DIRECTIVE = re.compile(
        r'\b(?:calculate|compute|find\s+the\s+value\s+of|determine\s+the\s+value\s+of|'
        r'solve\s+(?:the\s+(?:differential\s+)?equation|the\s+system|the\s+initial\s+value|the\s+recurrence|for\s+[a-zA-Z]|\(?\s*[a-zA-Z0-9\^D\(\)\'\"]+\s*[=\+\-\*]|y\'\'|y\')|'
        r'find\s+the\s+(?:eigen\s*values?|eigen\s*vectors?|rank|inverse|determinant|trace|roots?|general\s+solution|particular\s+integral|complementary\s+function|harmonic\s+conjugate|radius\s+of\s+convergence|maximum\s+and\s+minimum|dimensions)|'
        r'find\s+(?:the\s+)?(?:taylor|laurent|fourier|laplace|bilinear|envelope|series|expansion|map|transformation|analytic|harmonic)\b|find\s+f\(z\)|'
        r'find\s+the\s+(?:area|volume|perimeter|length|angle|slope|gradient|divergence|curl|laplacian|work|energy|force|velocity|acceleration|current|voltage|power|concentration|efficiency|impedance|resistance)|'
        r'reduce\s+the\s+quadratic\s+form|diagonalize|canonical\s+form|change\s+the\s+order\s+of\s+integration)\b',
        re.IGNORECASE
    )

    RE_EVALUATE_MATH = re.compile(
        r'\b(?:evaluate\s+(?:the\s+)?(?:integral|limit|derivative|expression|value|determinant|definite\s+integral|double\s+integral|triple\s+integral|contour\s+integral|greens?\s+theorem)|'
        r'evaluate\s*[:\s]*[\$\\]|evaluate\s+\\int|evaluate\s+\\lim|evaluate\s+\\oint|'
        r'evaluate\s+f\([a-z]\)|'
        r'evaluate\s*\(\s*[\d\.\-\+\*\/]+\s*\)|'
        r'evaluate\s+[0-9]+(?:\.[0-9]+)?\s*[\+\-\*\/])\b',
        re.IGNORECASE
    )

    RE_CODE_TRACING = re.compile(
        r'\b(?:predict\s+the\s+output|trace\s+the\s+output|find\s+the\s+output|what\s+is\s+the\s+output|what\s+will\s+be\s+the\s+output|what\s+is\s+printed)\b',
        re.IGNORECASE
    )

    RE_MATH_EXEC = re.compile(
        r'(?:\\int|\\sum|\\begin\{bmatrix\}|\\begin\{pmatrix\}|\\oint|\bdy\/dx\b|\bd\^2y\/dx\^2\b)',
        re.IGNORECASE
    )

    # 3. Regex patterns for Recall & Concept
    RE_DEFINITION = re.compile(
        r'\b(?:define\b|give\s+the\s+definition\s+of|state\s+the\s+(?:principle|law|theorem|definition|rule|postulate|assumptions?)|'
        r'what\s+is\s+meant\s+by|what\s+do\s+you\s+understand\s+by|state\s+true\s+or\s+false|fill\s+in\s+the\s+blank)\b|_{3,}',
        re.IGNORECASE
    )

    RE_LISTING = re.compile(
        r'\b(?:list\s+(?:the\s+)?(?:two|three|four|\d+)?\s*(?:advantages|disadvantages|applications|limitations|properties|features|types|methods|assumptions|characteristics)|'
        r'name\s+any\s+(?:two|three|\d+)?|mention\s+any\s+(?:two|three|\d+)?|give\s+(?:two|three|\d+)\s+examples?|write\s+short\s+notes?\s+on)\b',
        re.IGNORECASE
    )

    RE_EXPLANATION = re.compile(
        r'\b(?:explain\s+(?:the\s+working|the\s+construction|the\s+concept|the\s+principle|the\s+meaning|the\s+function|with\s+a?\s*neat\s+diagram)|'
        r'describe\s+(?:the\s+working|the\s+process|the\s+construction|with\s+a?\s*neat\s+diagram)|'
        r'discuss\s+(?:in\s+detail|the\s+features|the\s+properties)|elaborate\s+on|give\s+an\s+account\s+of|'
        r'explain\b|describe\b|discuss\b)\b',
        re.IGNORECASE
    )

    RE_CONCEPT_OPENER = re.compile(
        r'\b(?:what\s+is\b|what\s+are\b|which\s+of\s+the\s+following\s+is\b|'
        r'identify\s+(?:from\s+the\s+following|the\s+functional\s+groups?|the\s+aromatic|the\s+type|which)|'
        r'classify\s+(?:the\s+following|into))\b',
        re.IGNORECASE
    )

    # 4. MCQ structure detection for guardrails
    RE_MCQ_OPTIONS = re.compile(
        r'(?:\([A-D]\)|\[[A-D]\]|\b[A-D]\.\s+[A-Za-z0-9])',
        re.MULTILINE
    )

    @classmethod
    def is_genuine_mcq(cls, text: str, question_type: Optional[str] = None) -> bool:
        """Determines if the text or metadata corresponds to an objective MCQ item."""
        if question_type:
            return question_type in ("Objective / MCQ", "Objective")
        options = cls.RE_MCQ_OPTIONS.findall(text)
        distinct = set(o.upper().strip("()[] .") for o in options)
        return "C" in distinct and "D" in distinct and len(distinct) >= 3

    @classmethod
    def is_ocr_corrupted_or_gibberish(cls, text: str) -> bool:
        """Flags unprocessable OCR garbage, random symbol sequences, or unpronounceable strings."""
        clean = text.strip()
        if len(clean) < 6:
            return True
        alpha_count = sum(1 for c in clean if c.isalpha())
        # If low alpha count and not containing valid mathematical expression symbols or fill-in underscores
        if alpha_count / len(clean) < 0.25 and not any(sym in clean for sym in ("\\", "$", "=", "+", "-", "*", "/", "_")):
            return True
        # Repetitive non-alpha noise (e.g. ^^^^^^, %%%%%) - excludes fill-in blank underscores
        if re.search(r'[\^\%\!\@\#\$\*]{5,}', clean):
            return True
        # Long consonant cluster noise without vowels
        if re.search(r'\b[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]{10,}\b', clean):
            return True
        return False

    @classmethod
    def extract_subparts(
        cls,
        text: str,
        structured_content: Optional[Union[Dict, str]] = None,
        is_mcq: bool = False
    ) -> List[Tuple[str, str]]:
        """
        Extracts individually identifiable subparts from structured content
        or explicit textual markers without mistaking MCQ options for subparts.
        """
        if is_mcq:
            return []

        # 1. From structured content (highest fidelity parser output)
        if structured_content and structured_content not in ('null', 'None'):
            try:
                data = structured_content if isinstance(structured_content, dict) else json.loads(structured_content)
                if isinstance(data, dict) and "subquestions" in data and isinstance(data["subquestions"], list):
                    subqs = data["subquestions"]
                    if len(subqs) >= 2:
                        res = []
                        for idx, sq in enumerate(subqs):
                            lbl = str(sq.get("number") or idx + 1)
                            sub_txt = sq.get("text", "").strip()
                            if sub_txt and len(sub_txt) >= 4:
                                res.append((lbl, sub_txt))
                        if len(res) >= 2:
                            return res
            except Exception:
                pass

        # 2. From text via regex (when not an MCQ)
        # If text contains internal choice separator '--- OR ---', isolate primary question
        primary_text = text.split("--- OR ---")[0] if "--- OR ---" in text else text

        matches = list(re.finditer(r'(?:^|\n|\s+)\(([a-e]|[i-v]+)\)\s+', primary_text, re.IGNORECASE))
        if len(matches) >= 2:
            res = []
            for i in range(len(matches)):
                start = matches[i].end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(primary_text)
                sub_txt = primary_text[start:end].strip()
                lbl = matches[i].group(1).lower()
                if len(sub_txt) >= 6:
                    res.append((lbl, sub_txt))
            if len(res) >= 2:
                return res

        return []

    @classmethod
    def classify_text_signals(cls, clean_text: str, raw_text: str) -> Dict[CognitiveDemand, List[str]]:
        """Evaluates Layer 2 and Layer 3 regex signals from question text."""
        matched: Dict[CognitiveDemand, List[str]] = {
            CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN: [],
            CognitiveDemand.PROCEDURAL_COMPUTATION: [],
            CognitiveDemand.RECALL_AND_CONCEPT: [],
        }

        # 1. Analytical Proof & Design
        if cls.RE_PROOF_DERIVATION.search(clean_text):
            m = cls.RE_PROOF_DERIVATION.search(clean_text)
            matched[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN].append(f"proof_derivation:{m.group(0)}")
        if cls.RE_DESIGN_CONSTRUCTIVE.search(clean_text):
            m = cls.RE_DESIGN_CONSTRUCTIVE.search(clean_text)
            matched[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN].append(f"design_directive:{m.group(0)}")
        if cls.RE_PROGRAMMING_IMPL.search(clean_text):
            m = cls.RE_PROGRAMMING_IMPL.search(clean_text)
            matched[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN].append(f"programming_implementation:{m.group(0)}")
        comp_match = cls.RE_COMPARISON.search(clean_text)
        calc_diff_match = cls.RE_CALCULUS_DIFF.search(clean_text)
        phys_diff_match = cls.RE_PHYSICAL_DIFF.search(clean_text)
        if comp_match and not calc_diff_match and not phys_diff_match:
            matched[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN].append(f"comparison:{comp_match.group(0)}")
        if cls.RE_ANALYTICAL_EVAL.search(clean_text):
            m = cls.RE_ANALYTICAL_EVAL.search(clean_text)
            matched[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN].append(f"analytical_critique:{m.group(0)}")

        # 2. Procedural Computation
        if cls.RE_NUMERICAL_DIRECTIVE.search(clean_text) or calc_diff_match:
            m = cls.RE_NUMERICAL_DIRECTIVE.search(clean_text)
            sig = m.group(0) if m else "calculus_differentiation"
            matched[CognitiveDemand.PROCEDURAL_COMPUTATION].append(f"numerical_directive:{sig}")
        if cls.RE_EVALUATE_MATH.search(clean_text):
            m = cls.RE_EVALUATE_MATH.search(clean_text)
            matched[CognitiveDemand.PROCEDURAL_COMPUTATION].append(f"math_evaluate:{m.group(0)}")
        if cls.RE_CODE_TRACING.search(clean_text):
            m = cls.RE_CODE_TRACING.search(clean_text)
            matched[CognitiveDemand.PROCEDURAL_COMPUTATION].append(f"code_tracing:{m.group(0)}")
        if cls.RE_MATH_EXEC.search(raw_text) and any(w in clean_text for w in ("find", "solve", "determine", "calculate", "evaluate")):
            matched[CognitiveDemand.PROCEDURAL_COMPUTATION].append("math_notation_with_directive")

        # 3. Recall and Concept
        if cls.RE_DEFINITION.search(clean_text):
            m = cls.RE_DEFINITION.search(clean_text)
            matched[CognitiveDemand.RECALL_AND_CONCEPT].append(f"definition:{m.group(0)}")
        if cls.RE_LISTING.search(clean_text):
            m = cls.RE_LISTING.search(clean_text)
            matched[CognitiveDemand.RECALL_AND_CONCEPT].append(f"listing:{m.group(0)}")
        if cls.RE_EXPLANATION.search(clean_text):
            m = cls.RE_EXPLANATION.search(clean_text)
            matched[CognitiveDemand.RECALL_AND_CONCEPT].append(f"explanation:{m.group(0)}")
        if cls.RE_CONCEPT_OPENER.search(clean_text):
            m = cls.RE_CONCEPT_OPENER.search(clean_text)
            matched[CognitiveDemand.RECALL_AND_CONCEPT].append(f"concept_opener:{m.group(0)}")

        # Prune empty
        return {k: v for k, v in matched.items() if v}

    @classmethod
    def classify(
        cls,
        text: Optional[str],
        question_type: Optional[Union[str, Any]] = None,
        structured_content: Optional[Union[Dict[str, Any], str]] = None,
        marks: Optional[float] = None,
        section_name: Optional[str] = None
    ) -> DemandClassificationProposal:
        """
        Classifies question into one of the four approved demand archetypes:
        - RECALL_AND_CONCEPT
        - PROCEDURAL_COMPUTATION
        - ANALYTICAL_PROOF_AND_DESIGN
        - UNCLASSIFIED

        Strictly deterministic, layered evidence, ambiguity preserving.
        Marks are purely independent metadata and NEVER determine cognitive demand.
        """
        raw_text = (text or "").strip()
        if not raw_text or len(raw_text) < 6:
            return DemandClassificationProposal(
                demand=CognitiveDemand.UNCLASSIFIED,
                confidence=DemandConfidence.LOW,
                signals=["insufficient_text_length"]
            )

        if cls.is_ocr_corrupted_or_gibberish(raw_text):
            return DemandClassificationProposal(
                demand=CognitiveDemand.UNCLASSIFIED,
                confidence=DemandConfidence.LOW,
                signals=["ocr_corrupted_or_gibberish"]
            )

        clean_text = raw_text.lower()
        qtype_str = str(question_type.value if hasattr(question_type, "value") else (question_type or "")).strip()
        is_mcq = cls.is_genuine_mcq(raw_text, qtype_str)

        # -------------------------------------------------------------
        # STEP 1: Multi-part Subpart Decomposition
        # -------------------------------------------------------------
        subparts = cls.extract_subparts(raw_text, structured_content, is_mcq=is_mcq)
        if len(subparts) >= 2:
            subpart_demands: List[SubpartDemand] = []
            non_unclassified: set[CognitiveDemand] = set()

            for lbl, sub_txt in subparts:
                sub_res = cls.classify(
                    text=sub_txt,
                    question_type=None,
                    structured_content=None,
                    marks=None
                )
                subpart_demands.append(
                    SubpartDemand(
                        subpart_label=lbl,
                        text=sub_txt,
                        demand=sub_res.demand,
                        confidence=sub_res.confidence,
                        signals=sub_res.signals
                    )
                )
                if sub_res.demand != CognitiveDemand.UNCLASSIFIED:
                    non_unclassified.add(sub_res.demand)

            if len(non_unclassified) > 1:
                # Direct conflict across subparts: preserve ambiguity at parent level
                conflicting_labels = [d.value for d in sorted(non_unclassified, key=lambda x: x.value)]
                return DemandClassificationProposal(
                    demand=CognitiveDemand.UNCLASSIFIED,
                    confidence=DemandConfidence.HIGH,
                    signals=[f"composite_question_conflicting_subparts: {conflicting_labels}"],
                    subparts=subpart_demands,
                    is_composite=True,
                    evidence_layer="multipart_composite"
                )
            elif len(non_unclassified) == 1:
                # Unanimous demand among all classified subparts
                unanimous_demand = next(iter(non_unclassified))
                return DemandClassificationProposal(
                    demand=unanimous_demand,
                    confidence=DemandConfidence.HIGH,
                    signals=[f"composite_question_unanimous_subparts: {unanimous_demand.value}"],
                    subparts=subpart_demands,
                    is_composite=True,
                    evidence_layer="multipart_composite"
                )
            else:
                # All subparts unclassified
                return DemandClassificationProposal(
                    demand=CognitiveDemand.UNCLASSIFIED,
                    confidence=DemandConfidence.LOW,
                    signals=["composite_question_all_subparts_unclassified"],
                    subparts=subpart_demands,
                    is_composite=True,
                    evidence_layer="multipart_composite"
                )

        # For genuine MCQs, isolate the question prompt stem from choice options to avoid distractor leakage
        text_for_signals = raw_text
        clean_text_for_signals = clean_text
        if is_mcq:
            split_prompt = re.split(r'\n\s*(?:\([A-D]\)|\[[A-D]\]|\b[A-D]\.\s+)', raw_text)[0].strip()
            if len(split_prompt) >= 6:
                text_for_signals = split_prompt
                clean_text_for_signals = split_prompt.lower()

        matched = cls.classify_text_signals(clean_text_for_signals, text_for_signals)
        matched_demands = list(matched.keys())
        all_text_signals = [sig for sig_list in matched.values() for sig in sig_list]

        # Check for intra-prompt signal conflicts
        if len(matched_demands) > 1:
            # Special case: If programming implementation is present (e.g. "Write a C program to calculate...", "Write an algorithm to compute..."),
            # the arithmetic verb ("calculate", "compute", "find") specifies the software requirements, NOT a manual computation task.
            if CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN in matched_demands and CognitiveDemand.PROCEDURAL_COMPUTATION in matched_demands:
                has_prog = any(s.startswith("programming_implementation") for s in matched[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN])
                has_tracing = any(s.startswith("code_tracing") for s in matched[CognitiveDemand.PROCEDURAL_COMPUTATION])
                if has_prog and not has_tracing:
                    matched[CognitiveDemand.PROCEDURAL_COMPUTATION] = []
                    matched_demands = [d for d in matched_demands if d != CognitiveDemand.PROCEDURAL_COMPUTATION]

            # Filter subordinate generic explanation opener if dominant proof or computation is present
            non_trivial_demands = set()
            for d, sigs in matched.items():
                if not sigs:
                    continue
                if d == CognitiveDemand.RECALL_AND_CONCEPT and len(sigs) == 1 and any(s.startswith("explanation:explain") or s.startswith("explanation:discuss") for s in sigs):
                    continue
                non_trivial_demands.add(d)

            if len(non_trivial_demands) > 1:
                conflicting_labels = [d.value for d in sorted(non_trivial_demands, key=lambda x: x.value)]
                return DemandClassificationProposal(
                    demand=CognitiveDemand.UNCLASSIFIED,
                    confidence=DemandConfidence.HIGH,
                    signals=[f"conflicting_signals: {conflicting_labels}"] + all_text_signals,
                    is_composite=False,
                    evidence_layer="layer2_syntactic_conflict"
                )
            elif len(non_trivial_demands) == 1:
                matched_demands = list(non_trivial_demands)

        # -------------------------------------------------------------
        # STEP 3: Layer 1 (question_type) & Layer 2 Reconciliation
        # -------------------------------------------------------------
        if qtype_str == "Derivation / Proof":
            if CognitiveDemand.PROCEDURAL_COMPUTATION in matched_demands and CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN not in matched_demands:
                return DemandClassificationProposal(
                    demand=CognitiveDemand.UNCLASSIFIED,
                    confidence=DemandConfidence.HIGH,
                    signals=["conflict_qtype_derivation_vs_text_computation"] + all_text_signals,
                    evidence_layer="layer1_layer2_conflict"
                )
            return DemandClassificationProposal(
                demand=CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN,
                confidence=DemandConfidence.HIGH if CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN in matched_demands else DemandConfidence.MEDIUM,
                signals=["layer1_derivation"] + all_text_signals,
                evidence_layer="layer1_question_type"
            )

        if qtype_str == "Design & Application":
            return DemandClassificationProposal(
                demand=CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN,
                confidence=DemandConfidence.HIGH,
                signals=["layer1_design"] + all_text_signals,
                evidence_layer="layer1_question_type"
            )

        if qtype_str == "Comparison / Distinction":
            return DemandClassificationProposal(
                demand=CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN,
                confidence=DemandConfidence.HIGH,
                signals=["layer1_comparison"] + all_text_signals,
                evidence_layer="layer1_question_type"
            )

        if qtype_str == "Numerical / Calculation":
            if CognitiveDemand.RECALL_AND_CONCEPT in matched_demands and CognitiveDemand.PROCEDURAL_COMPUTATION not in matched_demands:
                return DemandClassificationProposal(
                    demand=CognitiveDemand.UNCLASSIFIED,
                    confidence=DemandConfidence.HIGH,
                    signals=["conflict_qtype_numerical_vs_text_recall"] + all_text_signals,
                    evidence_layer="layer1_layer2_conflict"
                )
            return DemandClassificationProposal(
                demand=CognitiveDemand.PROCEDURAL_COMPUTATION,
                confidence=DemandConfidence.HIGH if CognitiveDemand.PROCEDURAL_COMPUTATION in matched_demands else DemandConfidence.MEDIUM,
                signals=["layer1_numerical"] + all_text_signals,
                evidence_layer="layer1_question_type"
            )

        if qtype_str == "Short Answer / Definition":
            if CognitiveDemand.PROCEDURAL_COMPUTATION in matched_demands and CognitiveDemand.RECALL_AND_CONCEPT not in matched_demands:
                return DemandClassificationProposal(
                    demand=CognitiveDemand.UNCLASSIFIED,
                    confidence=DemandConfidence.HIGH,
                    signals=["conflict_qtype_short_answer_vs_text_computation"] + all_text_signals,
                    evidence_layer="layer1_layer2_conflict"
                )
            return DemandClassificationProposal(
                demand=CognitiveDemand.RECALL_AND_CONCEPT,
                confidence=DemandConfidence.HIGH if CognitiveDemand.RECALL_AND_CONCEPT in matched_demands else DemandConfidence.MEDIUM,
                signals=["layer1_short_answer"] + all_text_signals,
                evidence_layer="layer1_question_type"
            )

        if qtype_str == "Explanation / Descriptive":
            if CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN in matched_demands:
                return DemandClassificationProposal(
                    demand=CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN,
                    confidence=DemandConfidence.HIGH,
                    signals=["text_override_proof_design"] + all_text_signals,
                    evidence_layer="layer2_syntactic"
                )
            if CognitiveDemand.PROCEDURAL_COMPUTATION in matched_demands:
                return DemandClassificationProposal(
                    demand=CognitiveDemand.PROCEDURAL_COMPUTATION,
                    confidence=DemandConfidence.HIGH,
                    signals=["text_override_computation"] + all_text_signals,
                    evidence_layer="layer2_syntactic"
                )
            return DemandClassificationProposal(
                demand=CognitiveDemand.RECALL_AND_CONCEPT,
                confidence=DemandConfidence.HIGH if CognitiveDemand.RECALL_AND_CONCEPT in matched_demands else DemandConfidence.MEDIUM,
                signals=["layer1_explanation"] + all_text_signals,
                evidence_layer="layer1_question_type"
            )

        if qtype_str == "Programming & Implementation":
            if CognitiveDemand.PROCEDURAL_COMPUTATION in matched_demands:
                return DemandClassificationProposal(
                    demand=CognitiveDemand.PROCEDURAL_COMPUTATION,
                    confidence=DemandConfidence.HIGH,
                    signals=["programming_tracing_computation"] + all_text_signals,
                    evidence_layer="layer2_syntactic"
                )
            if CognitiveDemand.RECALL_AND_CONCEPT in matched_demands and CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN not in matched_demands:
                return DemandClassificationProposal(
                    demand=CognitiveDemand.RECALL_AND_CONCEPT,
                    confidence=DemandConfidence.MEDIUM,
                    signals=["programming_conceptual"] + all_text_signals,
                    evidence_layer="layer2_syntactic"
                )
            return DemandClassificationProposal(
                demand=CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN,
                confidence=DemandConfidence.HIGH if CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN in matched_demands else DemandConfidence.MEDIUM,
                signals=["programming_constructive"] + all_text_signals,
                evidence_layer="layer1_question_type"
            )

        if qtype_str in ("Objective / MCQ", "Objective"):
            if CognitiveDemand.PROCEDURAL_COMPUTATION in matched_demands:
                return DemandClassificationProposal(
                    demand=CognitiveDemand.PROCEDURAL_COMPUTATION,
                    confidence=DemandConfidence.HIGH,
                    signals=["mcq_calculation"] + all_text_signals,
                    evidence_layer="layer2_syntactic"
                )
            if CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN in matched_demands:
                return DemandClassificationProposal(
                    demand=CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN,
                    confidence=DemandConfidence.MEDIUM,
                    signals=["mcq_analysis"] + all_text_signals,
                    evidence_layer="layer2_syntactic"
                )
            return DemandClassificationProposal(
                demand=CognitiveDemand.RECALL_AND_CONCEPT,
                confidence=DemandConfidence.HIGH,
                signals=["mcq_recall_concept"] + all_text_signals,
                evidence_layer="layer1_question_type"
            )

        # -------------------------------------------------------------
        # STEP 4: Fallback for Other / Unclassified or Missing qtype
        # -------------------------------------------------------------
        if len(matched_demands) == 1:
            dem = matched_demands[0]
            conf = DemandConfidence.HIGH if len(matched[dem]) >= 2 else DemandConfidence.MEDIUM
            return DemandClassificationProposal(
                demand=dem,
                confidence=conf,
                signals=[f"text_directive:{dem.value}"] + all_text_signals,
                evidence_layer="layer2_syntactic"
            )

        # Indeterminate evidence: conservative unclassified fallback
        return DemandClassificationProposal(
            demand=CognitiveDemand.UNCLASSIFIED,
            confidence=DemandConfidence.LOW,
            signals=["no_discriminatory_signals"],
            evidence_layer="indeterminate_fallback"
        )
