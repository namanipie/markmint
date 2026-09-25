"""
Unit tests for deterministic ExamChronologyResolver.

Verifies:
- Academic year format extraction
- Date stamp and month-year extraction
- Prevention of false positives (course codes, question numbers, semester labels)
- Strict isolation of question banks and multi-year compilations
- Preservation of existing non-null metadata
- Deterministic assessment type normalization
"""

import pytest
from backend.services.exam_chronology_resolver import (
    ExamChronologyResolver,
    EvidenceSource,
    ResolutionCategory,
)


class TestExamChronologyResolver:

    def test_academic_year_extraction(self):
        headers = [
            ("Academic Year: 2022-23", 2022),
            ("Academic Year 2023-2024", 2023),
            ("AcademicYear:2024-2025", 2024),
            ("Academic Year:         2022-23", 2022),
            ("Academic  Year:  2023-24 (ODD Semester)", 2023),
        ]
        for header, expected_yr in headers:
            yr, ev = ExamChronologyResolver.extract_year_from_header_text(header)
            assert yr == expected_yr, f"Failed for '{header}': expected {expected_yr}, got {yr}"
            assert ev is not None
            assert ev.source == EvidenceSource.PDF_HEADER_ACADEMIC_YEAR

    def test_date_stamp_extraction(self):
        headers = [
            ("Date: 04-10-2023 Time: 10:00 AM", 2023),
            ("Exam held on 3/11/2023", 2023),
            ("Date of Examination: 15.05.2024", 2024),
        ]
        for header, expected_yr in headers:
            yr, ev = ExamChronologyResolver.extract_year_from_header_text(header)
            assert yr == expected_yr, f"Failed for '{header}': expected {expected_yr}, got {yr}"
            assert ev is not None
            assert ev.source == EvidenceSource.PDF_HEADER_DATE

    def test_month_year_extraction(self):
        headers = [
            ("JULY 2024 DEGREE EXAMINATION", 2024),
            ("Semester Examination - November 2022", 2022),
            ("CYCLE TEST - II (Feb 2023)", 2023),
        ]
        for header, expected_yr in headers:
            yr, ev = ExamChronologyResolver.extract_year_from_header_text(header)
            assert yr == expected_yr, f"Failed for '{header}': expected {expected_yr}, got {yr}"
            assert ev is not None
            assert ev.source in (EvidenceSource.PDF_HEADER_MONTH_YEAR, EvidenceSource.PDF_HEADER_EXAM_TITLE)

    def test_course_codes_false_positive_prevention(self):
        """Course codes like 18PYB103J, 21CSS101J, 21CSC101T must NEVER be extracted as years."""
        code_headers = [
            "Course Code: 18PYB103J - Semiconductor Physics",
            "Subject Code: 21CSS101J: Programming for Problem Solving",
            "18CSC201J Data Structures and Algorithms",
            "21CSC101T Object Oriented Design and Programming",
        ]
        for header in code_headers:
            yr, ev = ExamChronologyResolver.extract_year_from_header_text(header)
            assert yr is None, f"Course code mistakenly parsed as year for: '{header}', got {yr}"

    def test_question_numbers_false_positive_prevention(self):
        """Question numbers (e.g. '20.', '21.') must not trigger 2020 or 2021."""
        body_text = (
            "19. Define encapsulation.\n"
            "20. Explain polymorphic dispatch in C++.\n"
            "21. Discuss memory management and heap allocation.\n"
        )
        yr, ev = ExamChronologyResolver.extract_year_from_header_text(body_text)
        assert yr is None

    def test_question_bank_isolation(self):
        """Question banks and multi-unit compilations must be detected and marked as non-exam."""
        qb_titles = [
            "18PYB103J-Short answer questions.pdf",
            "21PYB102J Question Bank.pdf",
            "Chemistry - ALL CT COMPILATION.pdf",
            "Electrical And Electronics Engineering - Question Bank",
            "Philosophy Of Engineering - ALL UNIT poe.pdf",
            "Chapter 3_ Stereo Chemistry And Organic Reactions.pdf",
            "UNIT_1_PHYSICS_QUESTION_BANK_FROM_KTR_CAMPUS.pdf",
            "French Notes CT1",
        ]
        for title in qb_titles:
            assert ExamChronologyResolver.is_question_bank_or_compilation(title) is True

        res = ExamChronologyResolver.resolve_exam(
            exam_id=200,
            course_id=13,
            course_name="Semiconductor Physics",
            current_year=None,
            current_assessment_type="UNKNOWN",
            source_title="18PYB103J-Short answer questions.pdf",
        )
        assert res.resolution_category == ResolutionCategory.UNRESOLVED
        assert res.proposed_year is None
        assert res.is_mutation_candidate is False
        assert "question bank" in res.reason.lower()

    def test_existing_metadata_preservation(self):
        """Existing non-null year must be strictly preserved without mutation."""
        res = ExamChronologyResolver.resolve_exam(
            exam_id=42,
            course_id=1,
            course_name="Calculus And Linear Algebra",
            current_year=2023,
            current_assessment_type="END_SEM",
            source_title="Calculus - PYQ 2023 May.pdf",
        )
        assert res.resolution_category == ResolutionCategory.ALREADY_RESOLVED
        assert res.proposed_year == 2023
        assert res.proposed_assessment_type == "END_SEM"
        assert res.is_mutation_candidate is False
        assert res.reason == "Existing non-null year preserved"

    def test_assessment_type_normalization(self):
        assert ExamChronologyResolver.extract_assessment_type_from_text("CYCLE TEST - 1") == "CT1"
        assert ExamChronologyResolver.extract_assessment_type_from_text("Cycle Test - II") == "CT2"
        assert ExamChronologyResolver.extract_assessment_type_from_text("CT3 Examination") == "CT3"
        assert ExamChronologyResolver.extract_assessment_type_from_text("Model QP-ODD 2024-25") == "Model"
        assert ExamChronologyResolver.extract_assessment_type_from_text("Semester Examination") == "END_SEM"

    def test_ambiguous_conflicting_years(self):
        """Conflicting years in document title must produce AMBIGUOUS status."""
        res = ExamChronologyResolver.resolve_exam(
            exam_id=999,
            course_id=5,
            course_name="PPS",
            current_year=None,
            current_assessment_type=None,
            source_title="PPS Exam 2022 vs 2024 Review.pdf",
        )
        assert res.resolution_category == ResolutionCategory.AMBIGUOUS
        assert res.proposed_year is None
        assert res.is_mutation_candidate is False

    def test_candidates_admitted_cohort_year_false_positive_prevention(self):
        """
        Degree examinations stating 'DEGREE EXAMINATION, MAY 2023' followed by
        '(For the candidates admitted from the academic year 2021-2022)' must
        resolve to the actual exam year 2023, NOT the cohort admission year 2021.
        """
        header = (
            "B.Tech. / M.Tech (Integrated) DEGREE EXAMINATION, MAY 2023\n"
            "Second Semester\n"
            "21MAB102T - ADVANCED CALCULUS AND COMPLEX ANALYSIS\n"
            "(For the candidates admitted from the academic year 2021 -2022 & 2022 -2023)\n"
            "Time: 3 Hours Max. Marks: 75\n"
        )
        yr, ev = ExamChronologyResolver.extract_year_from_header_text(header)
        assert yr == 2023, f"Expected 2023, got {yr}"
        assert ev.source == EvidenceSource.PDF_HEADER_MONTH_YEAR

    def test_semester_and_year_of_study_false_positive_prevention(self):
        """Labels like 'Year/Sem: I/I' or 'Semester 1' must not be parsed as years."""
        header = (
            "SRM Institute of Science and Technology\n"
            "Faculty of Engineering and Technology\n"
            "Program offered: B.Tech (All Branches)\n"
            "Year/Sem: I/I\n"
            "Semester 1 Examination\n"
            "Duration: 1 Hour\n"
        )
        yr, ev = ExamChronologyResolver.extract_year_from_header_text(header)
        assert yr is None, f"Expected None for semester labels, got {yr}"
