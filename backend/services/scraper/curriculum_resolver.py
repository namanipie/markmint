"""
Canonical curriculum resolver for MarkMint.
Resolves crawled subject/semester navigation context against Course and CurriculumMapping models.
Guarantees:
- Never fabricates curriculum mappings or creates arbitrary courses.
- Resolves into MATCHED, AMBIGUOUS, UNMATCHED, or CATALOG_ONLY.
- Preserves raw subject metadata for unmatched resources.
"""

import re
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.core import Course, CurriculumMapping, Exam, Question
from .models import CurriculumMatchState, CurriculumMatchResult


def normalize_text(text: str) -> str:
    """Normalize string to lowercase alphanumeric characters only."""
    return re.sub(r"[^a-zA-Z0-9]", "", str(text)).lower()


class CurriculumResolver:
    """Resolves academic subjects to MarkMint's canonical Course and CurriculumMapping layer."""

    # Explicit known alias / acronym dictionary to prevent ambiguous string matching
    KNOWN_ALIASES = {
        "foe": "Fundamental Of Economics (FOE)",
        "fundamentalsofeconomics": "Fundamental Of Economics (FOE)",
        "fundamentalofeconomics": "Fundamental Of Economics (FOE)",
        "calculusandlinearalgebra": "Calculus And Linear Algebra",
        "calc": "Calculus And Linear Algebra",
        "chemistry": "Chemistry",
        "chem": "Chemistry",
        "programmingforproblemsolving": "Programming For Problem Solving",
        "pps": "Programming For Problem Solving",
        "programmingforproblemsolvingpps": "Programming For Problem Solving",
        "philosophyofengineering": "Philosophy Of Engineering",
        "introductiontocomputationalbiology": "Introduction To Computational Biology",
        "icb": "Introduction To Computational Biology",
        "biomedicalsensors": "Biomedical Sensors",
        "foreignlanguages": "Foreign Languages",
        "german": "Foreign Languages",
        "korean": "Foreign Languages",
        "japanese": "Foreign Languages",
        "spanish": "Foreign Languages",
        "chinese": "Foreign Languages",
        "french": "Foreign Languages",
        "cellbiology": "Cell Biology",
        "microbiology": "Microbiology",
        "physicalandanalyticalchemistry": "Physical And Analytical Chemistry",
        "biochemistry": "Biochemistry",
        "semiconductorphysicsandcomputationalmethods": "Semiconductor Physics and Computational Methods",
        "electricalandelectronicsengineering": "Electrical and Electronics Engineering",
        "electricalandelectronicsengineeringeee": "Electrical and Electronics Engineering",
        "communicativeenglish": "Communicative English",
        "advancedcalculusandcomplexanalysis": "Advanced Calculus and Complex Analysis",
        "objectorienteddesignandprogramming": "Object Oriented Design and Programming",
        "objectorienteddesignandprogrammingoodp": "Object Oriented Design and Programming",
        "electronicsystemandpcbdesign": "Electronic System and PCB Design",
        "electromagnetictheoryquantummechanicswavesandoptics": "Electromagnetic Theory, Quantum Mechanics, Waves and Optics",
        "electromagneticphysics": "Electromagnetic Theory, Quantum Mechanics, Waves and Optics",
        "physicsmechanics": "Physics: Mechanics",
        "engineeringmechanics": "Engineering Mechanics",
        "engineeringmechanicsem": "Engineering Mechanics",
        "probabilityandstatistics": "Probability and Statistics",
        "probabilityandstatisticspands": "Probability and Statistics",
        "probabilityandstatisticsps": "Probability and Statistics",
        "buildingmaterialsinthebuiltenvironment": "Building Materials in the Built Environment",
        "advancedprogrammingpractice": "Advanced Programming Practice",
        "advancedprogrammingpracticeapp": "Advanced Programming Practice",
        "app": "Advanced Programming Practice",
        "artificialintelligence": "Artificial Intelligence",
        "artificialintelligenceai": "Artificial Intelligence",
        "ai": "Artificial Intelligence",
        "computerorganizationandarchitecture": "Computer Organization and Architecture",
        "computerorganizationandarchitecturecoa": "Computer Organization and Architecture",
        "coa": "Computer Organization and Architecture",
        "designandanalysisofalgorithms": "Design and Analysis of Algorithms",
        "designandanalysisofalgorithmsdaa": "Design and Analysis of Algorithms",
        "daa": "Design and Analysis of Algorithms",
        "datastructuresandalgorithms": "Data Structures and Algorithms",
        "datastructuresandalgorithmsdsa": "Data Structures and Algorithms",
        "dsa": "Data Structures and Algorithms",
        "databasemanagementsystems": "Database Management Systems",
        "databasemanagementsystemsdbms": "Database Management Systems",
        "dbms": "Database Management Systems",
        "operatingsystems": "Operating Systems",
        "operatingsystemsos": "Operating Systems",
        "os": "Operating Systems",
        "controlsystems": "Control Systems",
        "digitalelectronicprinciples": "Digital Logic Design",
        "electronicdevices": "Solid State Devices",
        "coi": "Constitution of India",
        "constitutionofindia": "Constitution of India",
        "physicselectromagnetictheoryquantummechanicswavesandoptics": "Electromagnetic Theory, Quantum Mechanics, Waves and Optics",
        "measuringinstrument": "Electrical and Electronics Engineering",
        "measuringinstruments": "Electrical and Electronics Engineering",
        "transformsandboundaryvalueproblems": "Transforms and Boundary Value Problems",
        "transformsandboundaryvalueproblemstbvp": "Transforms and Boundary Value Problems",
        "tbvp": "Transforms and Boundary Value Problems",
        "probabilityandqueueingtheory": "Probability and Queueing Theory",
        "probabilityandqueueingtheorypqt": "Probability and Queueing Theory",
        "pqt": "Probability and Queueing Theory",
        "probabilityappliedstatistics": "Probability and Statistics",
    }

    def __init__(self, db: Session):
        self.db = db

    def resolve(
        self, subject_name: str, semester: Optional[int | str] = None
    ) -> CurriculumMatchResult:
        """
        Resolves subject against canonical Course and CurriculumMapping tables.
        """
        if not subject_name or not subject_name.strip():
            return CurriculumMatchResult(
                status=CurriculumMatchState.UNMATCHED,
                notes="Empty or missing subject name",
            )

        raw_subject = subject_name.strip()
        norm_subj = normalize_text(raw_subject)

        # Check alias
        canonical_subject_name = self.KNOWN_ALIASES.get(norm_subj, raw_subject)
        norm_canonical = normalize_text(canonical_subject_name)

        # 1. Direct lookup in Course table
        courses = self.db.query(Course).all()
        matched_course = None
        for c in courses:
            if (
                normalize_text(c.name) == norm_canonical
                or normalize_text(c.code or "") == norm_canonical
                or (c.canonical_code and normalize_text(c.canonical_code) == norm_canonical)
            ):
                matched_course = c
                break

        if matched_course:
            # Determine canonical semester(s) from curriculum mappings
            all_course_maps = (
                self.db.query(CurriculumMapping)
                .filter(CurriculumMapping.course_id == matched_course.id)
                .all()
            )
            valid_semesters = sorted(list({m.semester for m in all_course_maps if m.semester is not None}))

            input_sem = None
            if semester is not None:
                try:
                    input_sem = int(str(semester).strip())
                except ValueError:
                    pass

            if input_sem is not None and input_sem in valid_semesters:
                canonical_sem = input_sem
            elif valid_semesters:
                canonical_sem = valid_semesters[0]
            else:
                canonical_sem = None

            # Check if course has active exam materials or is catalog-only
            exam_count = (
                self.db.query(func.count(Exam.id))
                .filter(Exam.course_id == matched_course.id)
                .scalar()
                or 0
            )
            q_count = (
                self.db.query(func.count(Question.id))
                .join(Exam, Exam.id == Question.section_id)  # or through Section
                .scalar()
                or 0
            )

            status = (
                CurriculumMatchState.MATCHED
                if exam_count > 0
                else CurriculumMatchState.CATALOG_ONLY
            )

            canon_map_id = all_course_maps[0].id if all_course_maps else None

            return CurriculumMatchResult(
                status=status,
                course_id=matched_course.id,
                course_name=matched_course.name,
                canonical_code=matched_course.canonical_code,
                curriculum_mapping_id=canon_map_id,
                canonical_semester=canonical_sem,
                valid_semesters=valid_semesters,
                notes=(
                    f"Canonical Course: {matched_course.name} ({matched_course.code})"
                    + (" [Catalog Only]" if status == CurriculumMatchState.CATALOG_ONLY else " [Ready]")
                ),
            )

        # 2. Lookup in CurriculumMapping table
        curr_query = self.db.query(CurriculumMapping).filter(
            func.lower(CurriculumMapping.subject_name) == canonical_subject_name.lower()
        )

        if semester:
            try:
                sem_int = int(str(semester).strip())
                curr_query = curr_query.filter(CurriculumMapping.semester == sem_int)
            except ValueError:
                pass

        mappings = curr_query.all()

        # If direct string query had no rows, try normalized match
        if not mappings:
            all_mappings = self.db.query(CurriculumMapping).all()
            mappings = [
                m
                for m in all_mappings
                if normalize_text(m.subject_name) == norm_canonical
            ]
            if semester:
                try:
                    sem_int = int(str(semester).strip())
                    mappings = [m for m in mappings if m.semester == sem_int]
                except ValueError:
                    pass

        if mappings:
            statuses = {m.status for m in mappings}
            course_ids = {m.course_id for m in mappings if m.course_id is not None}

            if "AMBIGUOUS" in statuses or len(course_ids) > 1:
                return CurriculumMatchResult(
                    status=CurriculumMatchState.AMBIGUOUS,
                    curriculum_mapping_id=mappings[0].id,
                    notes=mappings[0].notes or "Multiple candidate syllabus variants or marked ambiguous",
                )

            if len(course_ids) == 1:
                cid = list(course_ids)[0]
                course = self.db.query(Course).get(cid)
                all_maps = (
                    self.db.query(CurriculumMapping)
                    .filter(CurriculumMapping.course_id == cid)
                    .all()
                )
                valid_sems = sorted(list({m.semester for m in all_maps if m.semester is not None}))
                input_sem = None
                if semester is not None:
                    try:
                        input_sem = int(str(semester).strip())
                    except ValueError:
                        pass

                chosen_sem = input_sem if (input_sem in valid_sems) else (mappings[0].semester or (valid_sems[0] if valid_sems else None))

                return CurriculumMatchResult(
                    status=CurriculumMatchState.MATCHED,
                    course_id=cid,
                    course_name=course.name if course else None,
                    canonical_code=course.canonical_code if course else None,
                    curriculum_mapping_id=mappings[0].id,
                    canonical_semester=chosen_sem,
                    valid_semesters=valid_sems,
                    notes=f"Resolved via CurriculumMapping to Course ID {cid}",
                )

            valid_sems = sorted(list({m.semester for m in mappings if m.semester is not None}))
            input_sem = None
            if semester is not None:
                try:
                    input_sem = int(str(semester).strip())
                except ValueError:
                    pass

            chosen_sem = input_sem if (input_sem in valid_sems) else (mappings[0].semester if mappings else None)

            return CurriculumMatchResult(
                status=CurriculumMatchState.CATALOG_ONLY,
                curriculum_mapping_id=mappings[0].id,
                canonical_semester=chosen_sem,
                valid_semesters=valid_sems,
                notes="Curriculum entry exists in catalog but has no canonical Course entity",
            )

        # 3. Subject completely unmatched
        return CurriculumMatchResult(
            status=CurriculumMatchState.UNMATCHED,
            notes=f"Subject '{raw_subject}' not found in canonical curriculum catalog",
        )
