from collections import defaultdict
from typing import Any, Optional
import math
import re

from backend.schemas import (
    ExamDNA,
    DataSufficiency,
    DNASampleSize,
    TopicDNA,
    UnitDNA,
    UnitDistributionDNA,
    QuestionTypeDNA,
    UnitQuestionTypeBreakdown,
    MarkBucketDNA,
    MarksDistributionDNA,
    StemPatternDNA,
    RepetitionBreakdownDNA,
    QuestionPatternSummaryDNA,
    RepetitionDNA,
    FamilyDNA,
    TemporalUnitQuestionTypeBreakdown, TemporalTrend,
    TemporalUnitFocusBreakdown, TopicHistoricalFootprint,
    TemporalTopicFocusBreakdown,
)

class DNAAnalyzerService:
    @classmethod
    def determine_sufficiency(cls, papers: int, questions: int) -> DataSufficiency:
        if papers <= 1 or questions < 10:
            return DataSufficiency.INSUFFICIENT
        if papers <= 3 or questions <= 30:
            return DataSufficiency.LIMITED
        if papers <= 6 or questions <= 100:
            return DataSufficiency.MODERATE
        return DataSufficiency.STRONG

    @classmethod
    def _resolve_unit_number(cls, unit_name: Any, explicit_number: Optional[int] = None) -> Optional[int]:
        if explicit_number is not None:
            try:
                return int(explicit_number)
            except (ValueError, TypeError):
                pass
        if not unit_name or str(unit_name).strip() in ("Unmapped / Unknown", "Unspecified Unit"):
            return None
        m = re.search(r"(?i)\bunit\s*[-:]?\s*(\d+)\b", str(unit_name))
        if m:
            return int(m.group(1))
        return None

    @classmethod
    def analyze(
        cls,
        exams: list[dict[str, Any]],
        target_course_id: Optional[int] = None,
        syllabus_units: Optional[list[dict[str, Any]]] = None
    ) -> ExamDNA:
        """
        Analyzes historical exams mathematically with full temporal, course boundary,
        and evidence integrity.
        Expects a list of exam dicts mapped from the database.
        """
        if not exams:
            return cls._empty_dna()

        # 0. Deduplicate exams and enforce course isolation if target_course_id is provided
        seen_exam_ids = set()
        filtered_exams = []
        for e in exams:
            if target_course_id is not None and e.get("course_id") is not None:
                if e.get("course_id") != target_course_id:
                    continue
            eid = e.get("id")
            if eid is not None:
                if eid in seen_exam_ids:
                    continue
                seen_exam_ids.add(eid)
            filtered_exams.append(e)

        if not filtered_exams:
            return cls._empty_dna()

        # Sort exams chronologically
        sorted_exams = sorted(filtered_exams, key=lambda x: x.get("year") or 0)

        # Deduplicate questions within and across exams
        seen_q_ids = set()
        sanitized_exams = []
        all_questions = []

        for e in sorted_exams:
            exam_copy = dict(e)
            deduped_questions = []
            for q in e.get("questions", []):
                qid = q.get("id")
                if qid is not None:
                    if qid in seen_q_ids:
                        continue
                    seen_q_ids.add(qid)
                deduped_questions.append(q)
                all_questions.append(q)
            exam_copy["questions"] = deduped_questions
            sanitized_exams.append(exam_copy)

        papers_with_questions = [e for e in sanitized_exams if len(e.get("questions", [])) > 0]
        total_exams = len(papers_with_questions) if papers_with_questions else len(sanitized_exams)
        total_questions = len(all_questions)

        if total_questions == 0 or total_exams == 0:
            return cls._empty_dna()

        years = sorted(list({int(e.get("year")) for e in sanitized_exams if e.get("year") is not None}))
        min_year = min(years) if years else 0
        max_year = max(years) if years else 0

        # 'Recent' is the last 2 available chronological years in THIS dataset (excluding None)
        recent_years_set = {y for y in years if y >= max_year - 1} if max_year > 0 else set()

        exam_types = sorted(list({str(e.get("exam_type")) for e in sanitized_exams if e.get("exam_type")}))
        contributing_exam_ids = sorted(list({e.get("id") for e in sanitized_exams if e.get("id") is not None}))

        sufficiency = cls.determine_sufficiency(total_exams, total_questions)

        # 1. Base Aggregators
        total_marks = sum(float(q.get("marks") or 0.0) for q in all_questions if not q.get("is_alternative"))
        recent_total_marks = sum(
            float(q.get("marks") or 0.0)
            for e in sanitized_exams if e.get("year") and e.get("year") in recent_years_set
            for q in e.get("questions", []) if not q.get("is_alternative")
        )
        recent_total_questions = sum(
            1 for e in sanitized_exams if e.get("year") and e.get("year") in recent_years_set
            for q in e.get("questions", [])
        )

        topics_data: dict[str, Any] = defaultdict(lambda: {
            "q_count": 0, "marks": 0.0, "papers": set(),
            "long_ans": 0, "short_ans": 0, "recent_q_count": 0,
            "diffs": [], "non_alt_q_count": 0
        })
        units_data: dict[str, Any] = defaultdict(lambda: {
            "q_count": 0, "marks": 0.0, "papers": set(), "recent_marks": 0.0, "recent_q_count": 0
        })
        qtypes_data: dict[str, Any] = defaultdict(lambda: {"count": 0, "marks": 0.0})

        # Marks discrete aggregation
        mark_counts: dict[float, int] = defaultdict(int)
        mark_cum_marks: dict[float, float] = defaultdict(float)
        scored_marks_list: list[float] = []
        unscored_questions = 0

        # Unit mapping tracking
        unmapped_unit_questions = 0
        unmapped_unit_marks = 0.0

        # Stem patterns tracking
        stem_category_counts: dict[str, int] = defaultdict(int)

        # Repetition types
        rep_exact = rep_near = rep_concept = rep_struct = 0
        exact_repeat_count = 0
        family_repeat_count = 0
        singleton_count = 0

        families_data: dict[str, Any] = defaultdict(lambda: {
            "occurrences": 0, "years": set(), "exam_types": set(),
            "marks": [], "recent_count": 0, "family_id": None,
            "papers": set(), "question_ids": [], "repetition_types": []
        })

        # 2. Populate Aggregators
        for exam in sanitized_exams:
            exam_year = exam.get("year")
            exam_id = exam.get("id")
            exam_type = exam.get("exam_type")
            is_recent = bool(exam_year and exam_year in recent_years_set)

            for q in exam.get("questions", []):
                raw_m = q.get("marks")
                m = float(raw_m) if raw_m is not None else 0.0
                is_alt = bool(q.get("is_alternative", False))

                # Marks distribution tracking
                if raw_m is None:
                    unscored_questions += 1
                else:
                    m_rounded = round(float(raw_m), 2)
                    mark_counts[m_rounded] += 1
                    if not is_alt:
                        mark_cum_marks[m_rounded] += m_rounded
                        scored_marks_list.append(m_rounded)

                # Topics
                q_topics = q.get("topics")
                if q_topics is None:
                    topic_single = q.get("topic")
                    q_topics = [topic_single] if topic_single else []

                for topic in q_topics:
                    if topic:
                        td = topics_data[topic]
                        td["q_count"] += 1
                        if not is_alt:
                            td["marks"] += m
                            td["non_alt_q_count"] += 1
                        td["papers"].add(exam_id)
                        if m >= 5.0:
                            td["long_ans"] += 1
                        if m <= 3.0:
                            td["short_ans"] += 1
                        if is_recent:
                            td["recent_q_count"] += 1
                        if q.get("difficulty") is not None:
                            td["diffs"].append(q["difficulty"])

                # Units
                q_units = q.get("units")
                if q_units is None:
                    unit_single = q.get("unit")
                    q_units = [unit_single] if unit_single else []

                clean_units = list(dict.fromkeys(u for u in q_units if u))
                if not clean_units:
                    unmapped_unit_questions += 1
                    if not is_alt:
                        unmapped_unit_marks += m
                else:
                    for unit in clean_units:
                        ud = units_data[unit]
                        ud["q_count"] += 1
                        if not is_alt:
                            ud["marks"] += m
                            if is_recent:
                                ud["recent_marks"] += m
                        if is_recent:
                            ud["recent_q_count"] += 1
                        ud["papers"].add(exam_id)

                # Question Types
                raw_qtype = q.get("question_type")
                qtype_key = raw_qtype.strip() if (raw_qtype and isinstance(raw_qtype, str) and raw_qtype.strip()) else "unclassified"
                qtypes_data[qtype_key]["count"] += 1
                if not is_alt:
                    qtypes_data[qtype_key]["marks"] += m

                # Repetition Types
                rep = q.get("repetition_type")
                if rep in ("exact", "exact_repeat"):
                    rep_exact += 1
                    exact_repeat_count += 1
                elif rep == "near":
                    rep_near += 1
                    family_repeat_count += 1
                elif rep in ("conceptual", "family_repeat"):
                    rep_concept += 1
                    family_repeat_count += 1
                elif rep == "structural":
                    rep_struct += 1
                    family_repeat_count += 1
                else:
                    singleton_count += 1

                # Stem Pattern Detection (Deterministic action keywords)
                q_text = str(q.get("original_text") or q.get("text") or q.get("normalized_text") or "").strip().lower()
                stem_cat = cls._classify_stem_pattern(q_text)
                stem_category_counts[stem_cat] += 1

                # Question Families
                fam = q.get("family_name")
                fam_id = q.get("family_id")
                if fam:
                    fd = families_data[fam]
                    fd["occurrences"] += 1
                    if fam_id and fd["family_id"] is None:
                        fd["family_id"] = fam_id
                    if exam_id is not None:
                        fd["papers"].add(exam_id)
                    if exam_year:
                        fd["years"].add(exam_year)
                    if exam_type:
                        fd["exam_types"].add(exam_type)
                    if q.get("id"):
                        fd["question_ids"].append(q.get("id"))
                    rep_t = q.get("repetition_type")
                    if rep_t:
                        fd["repetition_types"].append(rep_t)
                    if not is_alt and raw_m is not None:
                        fd["marks"].append(float(raw_m))
                    if is_recent:
                        fd["recent_count"] += 1

        # 3. Compile Topic DTOs
        topics_dna = []
        for t_name, td in topics_data.items():
            diff_dist = {"0.0-0.3": 0, "0.3-0.7": 0, "0.7-1.0": 0}
            for d in td["diffs"]:
                if d < 0.3:
                    diff_dist["0.0-0.3"] += 1
                elif d < 0.7:
                    diff_dist["0.3-0.7"] += 1
                else:
                    diff_dist["0.7-1.0"] += 1

            recent_freq = td["recent_q_count"] / recent_total_questions if recent_total_questions > 0 else 0
            hist_freq = td["q_count"] / total_questions if total_questions > 0 else 0

            topics_dna.append(TopicDNA(
                topic=t_name,
                question_count=td["q_count"],
                paper_coverage=len(td["papers"]) / total_exams,
                total_marks=td["marks"],
                average_marks=td["marks"] / td["non_alt_q_count"] if td["non_alt_q_count"] > 0 else 0,
                long_answer_frequency=td["long_ans"] / td["q_count"] if td["q_count"] > 0 else 0,
                short_answer_frequency=td["short_ans"] / td["q_count"] if td["q_count"] > 0 else 0,
                recent_frequency=recent_freq,
                historical_frequency=hist_freq,
                difficulty_distribution=diff_dist
            ))

        # 4. Compile Unit DTOs
        units_dna = []
        for u_name, ud in sorted(units_data.items(), key=lambda x: str(x[0])):
            # Prefer marks-weighted distribution where total_marks exists
            hist_w = ud["marks"] / total_marks if total_marks > 0 else (ud["q_count"] / total_questions if total_questions > 0 else 0)
            rec_w = ud["recent_marks"] / recent_total_marks if recent_total_marks > 0 else (ud["recent_q_count"] / recent_total_questions if recent_total_questions > 0 else 0)

            q_pct = round((ud["q_count"] / total_questions) * 100, 2) if total_questions > 0 else 0.0
            m_pct = round((ud["marks"] / total_marks) * 100, 2) if total_marks > 0 else None

            units_dna.append(UnitDNA(
                unit=u_name,
                question_count=ud["q_count"],
                marks=ud["marks"],
                paper_coverage=len(ud["papers"]) / total_exams,
                recent_weighting=rec_w,
                historical_weighting=hist_w,
                percentage_of_questions=q_pct,
                percentage_of_marks=m_pct
            ))

        unit_distribution = UnitDistributionDNA(
            units=units_dna,
            unmapped_question_count=unmapped_unit_questions,
            unmapped_marks=round(unmapped_unit_marks, 2),
            is_marks_weighted=bool(total_marks > 0),
            total_marks_evaluated=round(total_marks, 2),
            total_questions_evaluated=total_questions
        )

        # 5. Compile Question Types DTOs
        qtypes_dna = []
        for qt, qtd in sorted(qtypes_data.items(), key=lambda x: x[1]["count"], reverse=True):
            pct = round(qtd["count"] / total_questions, 4) if total_questions > 0 else 0.0
            marks_w = round(qtd["marks"] / total_marks, 4) if total_marks > 0 else 0.0
            qtypes_dna.append(QuestionTypeDNA(
                question_type=qt,
                count=qtd["count"],
                percentage=pct,
                marks_weighting=marks_w
            ))

        # 6. Compile Marks Distribution DTO
        mark_buckets = []
        for m_val, cnt in sorted(mark_counts.items(), key=lambda x: x[0]):
            cum_m = mark_cum_marks.get(m_val, 0.0)
            mark_buckets.append(MarkBucketDNA(
                marks=m_val,
                question_count=cnt,
                percentage_of_questions=round(cnt / total_questions, 4) if total_questions > 0 else 0.0,
                cumulative_marks=round(cum_m, 2),
                percentage_of_marks=round(cum_m / total_marks, 4) if total_marks > 0 else 0.0
            ))

        marks_distribution = MarksDistributionDNA(
            buckets=mark_buckets,
            unscored_question_count=unscored_questions,
            unscored_percentage=round(unscored_questions / total_questions, 4) if total_questions > 0 else 0.0,
            total_scored_questions=len(scored_marks_list),
            total_marks=round(total_marks, 2),
            min_marks=min(scored_marks_list) if scored_marks_list else None,
            max_marks=max(scored_marks_list) if scored_marks_list else None,
            avg_marks=round(sum(scored_marks_list) / len(scored_marks_list), 2) if scored_marks_list else None
        )

        # 7. Compile Family DTOs
        families_dna = []
        for f_name, fd in families_data.items():
            sorted_years = sorted(list({y for y in fd["years"] if y is not None}))
            interval = 0.0
            if len(sorted_years) > 1:
                diffs = [sorted_years[i] - sorted_years[i-1] for i in range(1, len(sorted_years))]
                interval = sum(diffs) / len(diffs)

            marks_list = fd["marks"]
            avg_m = (round(sum(marks_list) / len(marks_list), 2)) if marks_list else None
            tot_m = round(sum(marks_list), 2) if marks_list else None

            rep_types = fd["repetition_types"]
            rep_type = rep_types[0] if rep_types else "singleton"
            if "exact_repeat" in rep_types or "exact" in rep_types:
                rep_type = "exact_repeat"
            elif "family_repeat" in rep_types or "near" in rep_types or "conceptual" in rep_types:
                rep_type = "family_repeat"

            families_dna.append(FamilyDNA(
                family_id=fd["family_id"],
                family_name=f_name,
                occurrences=fd["occurrences"],
                years=sorted_years,
                exam_types=list(fd["exam_types"]),
                average_marks=avg_m,
                total_marks=tot_m,
                distinct_paper_count=len(fd["papers"]),
                paper_ids=sorted(list(fd["papers"])),
                question_ids=fd["question_ids"],
                repetition_type=rep_type,
                recurrence_interval_years=interval,
                recent_recurrence_count=fd["recent_count"],
                trend="stable"
            ))

        # Sort families by recurrence significance (paper coverage, then total marks/occurrences)
        families_dna.sort(key=lambda f: (f.distinct_paper_count, f.occurrences, f.total_marks or 0.0), reverse=True)

        # 8. Compile Question Pattern Summary DTO
        stem_patterns = []
        stem_example_verbs = {
            "Proof & Derivation": ["prove", "show that", "derive", "verify"],
            "Calculation & Numerical": ["calculate", "evaluate", "find", "determine"],
            "Explanation & Conceptual": ["explain", "describe", "discuss", "define"],
            "Comparison": ["compare", "distinguish", "differentiate"],
            "Application & Design": ["design", "construct", "implement", "draw"],
            "General / Formulated": []
        }
        for pattern_name, p_cnt in sorted(stem_category_counts.items(), key=lambda x: x[1], reverse=True):
            stem_patterns.append(StemPatternDNA(
                pattern=pattern_name,
                question_count=p_cnt,
                percentage=round(p_cnt / total_questions, 4) if total_questions > 0 else 0.0,
                example_verbs=stem_example_verbs.get(pattern_name, [])
            ))

        pattern_summary = QuestionPatternSummaryDNA(
            top_recurring_families=families_dna[:10],
            stem_patterns=stem_patterns,
            repetition_breakdown=RepetitionBreakdownDNA(
                exact_repeat_count=exact_repeat_count,
                family_repeat_count=family_repeat_count,
                singleton_count=singleton_count,
                exact_repeat_percentage=round(exact_repeat_count / total_questions, 4) if total_questions > 0 else 0.0,
                family_repeat_percentage=round(family_repeat_count / total_questions, 4) if total_questions > 0 else 0.0,
                singleton_percentage=round(singleton_count / total_questions, 4) if total_questions > 0 else 0.0
            )
        )

        sample_size = DNASampleSize(
            papers=total_exams,
            questions=total_questions,
            time_range_years=(min_year, max_year),
            years=years,
            exam_types=exam_types,
            sufficiency=sufficiency,
            contributing_exam_ids=contributing_exam_ids,
            unmapped_question_count=unmapped_unit_questions,
            unscored_question_count=unscored_questions,
            total_marks=round(total_marks, 2)
        )

        # Temporal unit-question-type breakdown
        year_exam_counts = defaultdict(int)
        for e in sanitized_exams:
            y = e.get("year")
            if y is not None:
                year_exam_counts[y] += 1

        temporal_breakdowns = []
        if year_exam_counts:
            agg = defaultdict(lambda: defaultdict(lambda: {"count": 0, "marks": 0.0}))
            for e in sanitized_exams:
                y = e.get("year")
                if y is None:
                    continue
                for q in e.get("questions", []):
                    is_alt = bool(q.get("is_alternative", False))
                    raw_m = q.get("marks")
                    m = float(raw_m) if raw_m is not None else 0.0
                    q_units = q.get("units")
                    if q_units is None:
                        unit_single = q.get("unit")
                        q_units = [unit_single] if unit_single else []
                    clean_units = list(dict.fromkeys(u for u in q_units if u))
                    if not clean_units:
                        continue
                    raw_qtype = q.get("question_type")
                    qtype_key = raw_qtype.strip() if (raw_qtype and isinstance(raw_qtype, str) and raw_qtype.strip()) else "unclassified"
                    for unit in clean_units:
                        bucket = agg[(y, unit)][qtype_key]
                        bucket["count"] += 1
                        if not is_alt:
                            bucket["marks"] += m

            for (y, unit), qtype_dict in agg.items():
                total_q = sum(v["count"] for v in qtype_dict.values())
                total_m = sum(v["marks"] for v in qtype_dict.values())
                exams_in_y = year_exam_counts[y]
                is_sparse = (exams_in_y < 3) or (total_q < 5)
                for qtype, stats in qtype_dict.items():
                    cnt = stats["count"]
                    marks = round(stats["marks"], 2)
                    q_pct = round(cnt / total_q, 4) if total_q > 0 else 0.0
                    m_pct = round(marks / total_m, 4) if total_m > 0 else 0.0
                    temporal_breakdowns.append(
                        TemporalUnitQuestionTypeBreakdown(
                            year=y,
                            unit=unit,
                            question_type=qtype,
                            question_count=cnt,
                            question_percentage=q_pct,
                            scored_marks=marks,
                            marks_weight_percentage=m_pct,
                            exam_count=exams_in_y,
                            total_unit_questions=total_q,
                            is_sparse=is_sparse
                        )
                    )

            temporal_breakdowns.sort(key=lambda r: (r.year, str(r.unit), r.question_type))

        # -------------------------------------------------------------
        # 9. Historical Exam Focus Evolution: Feature 1 - Temporal Unit Focus
        # -------------------------------------------------------------
        known_units_dict: dict[str, Optional[int]] = {}
        if syllabus_units:
            for su in syllabus_units:
                u_name = su.get("name")
                if u_name:
                    known_units_dict[u_name] = cls._resolve_unit_number(u_name, su.get("number"))

        # Collect all units present on questions across sanitized_exams
        for e in sanitized_exams:
            for q in e.get("questions", []):
                if q.get("unit_objects"):
                    for uo in q.get("unit_objects"):
                        uo_name = uo.get("name")
                        if uo_name and uo_name not in known_units_dict:
                            known_units_dict[uo_name] = cls._resolve_unit_number(uo_name, uo.get("number"))
                else:
                    q_units = q.get("units") if q.get("units") is not None else ([q.get("unit")] if q.get("unit") else [])
                    for u in q_units:
                        if u and u not in known_units_dict and u != "Unmapped / Unknown":
                            known_units_dict[u] = cls._resolve_unit_number(u, q.get("unit_number"))

        sorted_mapped_units = sorted(
            known_units_dict.items(),
            key=lambda item: (item[1] is None, item[1] or 0, item[0])
        )

        all_unit_slots: list[tuple[str, Optional[int]]] = list(sorted_mapped_units)
        all_unit_slots.append(("Unmapped / Unknown", None))

        dated_years = sorted(list({int(e.get("year")) for e in sanitized_exams if e.get("year") is not None}))

        temporal_unit_focus: list[TemporalUnitFocusBreakdown] = []

        for y in dated_years:
            year_exams = [e for e in sanitized_exams if e.get("year") == y]
            exam_count_in_year = len(set(e.get("id") for e in year_exams if e.get("id") is not None)) or len(year_exams)

            questions_in_year = [q for e in year_exams for q in e.get("questions", [])]
            total_year_questions = len(questions_in_year)
            if total_year_questions == 0:
                continue

            total_year_scored_marks = sum(
                float(q.get("marks"))
                for q in questions_in_year
                if not q.get("is_alternative") and q.get("marks") is not None
            )

            mapped_questions_in_year = 0
            for q in questions_in_year:
                q_units = q.get("units") if q.get("units") is not None else ([q.get("unit")] if q.get("unit") else [])
                q_topics = q.get("topics") if q.get("topics") is not None else ([q.get("topic")] if q.get("topic") else [])
                if (
                    (q_units and any(u for u in q_units if u and u != "Unmapped / Unknown"))
                    or (q.get("unit") and q.get("unit") != "Unmapped / Unknown")
                    or (q_topics and any(q_topics))
                    or q.get("topic")
                    or (q.get("topic_objects") and len(q.get("topic_objects")) > 0)
                    or (q.get("unit_objects") and len(q.get("unit_objects")) > 0)
                ):
                    mapped_questions_in_year += 1

            is_sparse_year = (exam_count_in_year <= 1) or (mapped_questions_in_year < 10)

            unit_q_lists: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for q in questions_in_year:
                q_units = q.get("units") if q.get("units") is not None else ([q.get("unit")] if q.get("unit") else [])
                clean_units = list(dict.fromkeys(u for u in q_units if u and u != "Unmapped / Unknown"))
                if not clean_units:
                    unit_q_lists["Unmapped / Unknown"].append(q)
                else:
                    for u in clean_units:
                        unit_q_lists[u].append(q)

            for u_name, u_num in all_unit_slots:
                u_questions = unit_q_lists.get(u_name, [])
                q_cnt = len(u_questions)
                q_pct = round((q_cnt / total_year_questions) * 100.0, 2) if total_year_questions > 0 else 0.0

                u_scored_marks = sum(
                    float(q.get("marks"))
                    for q in u_questions
                    if not q.get("is_alternative") and q.get("marks") is not None
                )
                m_weight_pct = round((u_scored_marks / total_year_scored_marks) * 100.0, 2) if total_year_scored_marks > 0 else 0.0

                temporal_unit_focus.append(
                    TemporalUnitFocusBreakdown(
                        year=y,
                        unit=u_name,
                        unit_number=u_num,
                        question_count=q_cnt,
                        question_percentage=q_pct,
                        scored_marks=round(u_scored_marks, 2),
                        marks_weight_percentage=m_weight_pct,
                        exam_count=exam_count_in_year,
                        is_sparse=is_sparse_year
                    )
                )

        temporal_unit_focus.sort(key=lambda r: (r.year, r.unit_number is None, r.unit_number or 0, r.unit))

        # -------------------------------------------------------------
        # 10. Historical Exam Focus Evolution: Feature 2 - Topic Historical Footprints
        # -------------------------------------------------------------
        dated_exam_ids = {
            e.get("id")
            for e in sanitized_exams
            if e.get("year") is not None and e.get("id") is not None and len(e.get("questions", [])) > 0
        }
        total_dated_papers = len(dated_exam_ids)

        topic_aggregates: dict[Any, dict[str, Any]] = {}
        for e in sanitized_exams:
            eid = e.get("id")
            eyear = e.get("year")
            for q in e.get("questions", []):
                is_alt = bool(q.get("is_alternative", False))
                raw_m = q.get("marks")
                m = float(raw_m) if raw_m is not None else 0.0

                t_items = []
                if q.get("topic_objects"):
                    for to in q.get("topic_objects"):
                        t_items.append({
                            "id": to.get("id"),
                            "name": to.get("name"),
                            "unit_name": to.get("unit_name"),
                            "unit_number": to.get("unit_number"),
                        })
                else:
                    raw_topics = q.get("topics") if q.get("topics") is not None else ([q.get("topic")] if q.get("topic") else [])
                    q_units = q.get("units") if q.get("units") is not None else ([q.get("unit")] if q.get("unit") else [])
                    u_name = q_units[0] if q_units else "Unspecified Unit"
                    u_num = q.get("unit_number") or cls._resolve_unit_number(u_name)
                    for rt in raw_topics:
                        if rt:
                            t_items.append({
                                "id": q.get("topic_id"),
                                "name": str(rt),
                                "unit_name": u_name,
                                "unit_number": u_num,
                            })

                for item in t_items:
                    t_name = item.get("name")
                    if not t_name:
                        continue
                    t_id = item.get("id")
                    if t_id is None:
                        t_id = abs(hash(t_name)) % 1000000

                    t_key = (t_id, t_name)
                    if t_key not in topic_aggregates:
                        topic_aggregates[t_key] = {
                            "topic_id": t_id,
                            "topic_name": t_name,
                            "unit_name": item.get("unit_name") or "Unspecified Unit",
                            "unit_number": item.get("unit_number"),
                            "total_questions": 0,
                            "total_marks": 0.0,
                            "years_observed": set(),
                            "dated_papers": set(),
                        }
                    agg = topic_aggregates[t_key]
                    if item.get("unit_name") and (agg["unit_name"] == "Unspecified Unit" or not agg["unit_name"]):
                        agg["unit_name"] = item.get("unit_name")
                    if item.get("unit_number") is not None and agg["unit_number"] is None:
                        agg["unit_number"] = item.get("unit_number")

                    agg["total_questions"] += 1
                    if not is_alt:
                        agg["total_marks"] += m

                    if eyear is not None:
                        agg["years_observed"].add(int(eyear))
                        if eid is not None and eid in dated_exam_ids:
                            agg["dated_papers"].add(eid)

        topic_historical_footprints: list[TopicHistoricalFootprint] = []
        for agg in topic_aggregates.values():
            years_obs = sorted(list(agg["years_observed"]))
            first_seen = min(years_obs) if years_obs else None
            latest_seen = max(years_obs) if years_obs else None
            cov_pct = round((len(agg["dated_papers"]) / total_dated_papers) * 100.0, 2) if total_dated_papers > 0 else 0.0

            topic_historical_footprints.append(TopicHistoricalFootprint(
                topic_id=agg["topic_id"],
                topic_name=agg["topic_name"],
                unit_name=agg["unit_name"],
                unit_number=agg["unit_number"],
                total_questions=agg["total_questions"],
                total_marks=round(agg["total_marks"], 2),
                years_observed=years_obs,
                first_seen_year=first_seen,
                latest_seen_year=latest_seen,
                paper_coverage_percentage=cov_pct
            ))

        topic_historical_footprints.sort(key=lambda f: (
            f.unit_number is None,
            f.unit_number or 0,
            -f.total_questions,
            f.topic_name
        ))

        # -------------------------------------------------------------
        # 11. Historical Exam Focus Evolution: Feature 3 - Temporal Topic Focus Breakdown
        # -------------------------------------------------------------
        unmapped_years_observed = sorted(list({
            int(e.get("year"))
            for e in sanitized_exams
            if e.get("year") is not None
            for q in e.get("questions", [])
            if not (q.get("topics") or q.get("topic") or q.get("topic_objects"))
        }))

        temporal_topic_focus: list[TemporalTopicFocusBreakdown] = []

        for y in dated_years:
            year_exams = [e for e in sanitized_exams if e.get("year") == y]
            exam_count_in_year = len(set(e.get("id") for e in year_exams if e.get("id") is not None)) or len(year_exams)

            questions_in_year = [q for e in year_exams for q in e.get("questions", [])]
            total_year_questions = len(questions_in_year)
            if total_year_questions == 0:
                continue

            total_year_scored_marks = sum(
                float(q.get("marks"))
                for q in questions_in_year
                if not q.get("is_alternative") and q.get("marks") is not None
            )

            mapped_questions_in_year = 0
            for q in questions_in_year:
                q_units = q.get("units") if q.get("units") is not None else ([q.get("unit")] if q.get("unit") else [])
                q_topics = q.get("topics") if q.get("topics") is not None else ([q.get("topic")] if q.get("topic") else [])
                if (
                    (q_units and any(u for u in q_units if u and u != "Unmapped / Unknown"))
                    or (q.get("unit") and q.get("unit") != "Unmapped / Unknown")
                    or (q_topics and any(q_topics))
                    or q.get("topic")
                    or (q.get("topic_objects") and len(q.get("topic_objects")) > 0)
                    or (q.get("unit_objects") and len(q.get("unit_objects")) > 0)
                ):
                    mapped_questions_in_year += 1

            is_sparse_year = (exam_count_in_year <= 1) or (mapped_questions_in_year < 10)

            topic_year_groups: dict[Any, dict[str, Any]] = {}
            for q in questions_in_year:
                is_alt = bool(q.get("is_alternative", False))
                raw_m = q.get("marks")
                m = float(raw_m) if raw_m is not None else 0.0
                raw_qtype = q.get("question_type")
                qtype_key = raw_qtype.strip() if (raw_qtype and isinstance(raw_qtype, str) and raw_qtype.strip()) else "Other / Unclassified"

                t_items = []
                if q.get("topic_objects"):
                    for to in q.get("topic_objects"):
                        t_items.append({
                            "id": to.get("id"),
                            "name": to.get("name"),
                            "unit_name": to.get("unit_name"),
                            "unit_number": to.get("unit_number"),
                        })
                else:
                    raw_topics = q.get("topics") if q.get("topics") is not None else ([q.get("topic")] if q.get("topic") else [])
                    q_units = q.get("units") if q.get("units") is not None else ([q.get("unit")] if q.get("unit") else [])
                    u_name = q_units[0] if q_units else "Unspecified Unit"
                    u_num = q.get("unit_number") or cls._resolve_unit_number(u_name)
                    for rt in raw_topics:
                        if rt:
                            t_items.append({
                                "id": q.get("topic_id"),
                                "name": str(rt),
                                "unit_name": u_name,
                                "unit_number": u_num,
                            })

                if not t_items:
                    g_key = ("Unmapped / Unknown", None, "Unmapped / Unknown", None)
                    if g_key not in topic_year_groups:
                        topic_year_groups[g_key] = {
                            "unit": "Unmapped / Unknown",
                            "unit_number": None,
                            "topic": "Unmapped / Unknown",
                            "topic_id": None,
                            "question_count": 0,
                            "scored_marks": 0.0,
                            "question_types": defaultdict(int)
                        }
                    grp = topic_year_groups[g_key]
                    grp["question_count"] += 1
                    if not is_alt and raw_m is not None:
                        grp["scored_marks"] += m
                    grp["question_types"][qtype_key] += 1
                else:
                    for item in t_items:
                        t_name = item.get("name")
                        if not t_name:
                            continue
                        t_id = item.get("id")
                        if t_id is None:
                            t_id = abs(hash(t_name)) % 1000000
                        u_name = item.get("unit_name") or "Unspecified Unit"
                        u_num = item.get("unit_number")
                        g_key = (u_name, u_num, t_name, t_id)
                        if g_key not in topic_year_groups:
                            topic_year_groups[g_key] = {
                                "unit": u_name,
                                "unit_number": u_num,
                                "topic": t_name,
                                "topic_id": t_id,
                                "question_count": 0,
                                "scored_marks": 0.0,
                                "question_types": defaultdict(int)
                            }
                        grp = topic_year_groups[g_key]
                        grp["question_count"] += 1
                        if not is_alt and raw_m is not None:
                            grp["scored_marks"] += m
                        grp["question_types"][qtype_key] += 1

            for grp in topic_year_groups.values():
                q_cnt = grp["question_count"]
                q_pct = round((q_cnt / total_year_questions) * 100.0, 2) if total_year_questions > 0 else 0.0
                s_m = round(grp["scored_marks"], 2)
                m_pct = round((s_m / total_year_scored_marks) * 100.0, 2) if total_year_scored_marks > 0 else 0.0

                if grp["topic"] == "Unmapped / Unknown":
                    p_years = unmapped_years_observed
                else:
                    t_k = (grp["topic_id"], grp["topic"])
                    p_years = sorted(list(topic_aggregates[t_k]["years_observed"])) if t_k in topic_aggregates else [y]

                first_y = min(p_years) if p_years else None
                latest_y = max(p_years) if p_years else None

                temporal_topic_focus.append(
                    TemporalTopicFocusBreakdown(
                        year=y,
                        unit=grp["unit"],
                        unit_number=grp["unit_number"],
                        topic=grp["topic"],
                        topic_id=grp["topic_id"],
                        question_count=q_cnt,
                        question_percentage=q_pct,
                        scored_marks=s_m,
                        marks_weight_percentage=m_pct,
                        exam_count=exam_count_in_year,
                        persistence_years=p_years,
                        first_seen_year=first_y,
                        latest_seen_year=latest_y,
                        is_sparse=is_sparse_year,
                        question_types=dict(grp["question_types"])
                    )
                )

        temporal_topic_focus.sort(key=lambda r: (
            r.year,
            r.unit_number is None,
            r.unit_number or 0,
            r.topic == "Unmapped / Unknown",
            -r.question_count,
            r.topic
        ))

        return ExamDNA(
            sample_size=sample_size,
            topics=topics_dna,
            units=units_dna,
            question_types=qtypes_dna,
            repetition=RepetitionDNA(
                exact_count=rep_exact,
                near_count=rep_near,
                conceptual_count=rep_concept,
                structural_count=rep_struct
            ),
            families=families_dna,
            temporal_trends=[],
            unit_distribution=unit_distribution,
            marks_distribution=marks_distribution,
            pattern_summary=pattern_summary,
            temporal_unit_question_type_breakdown=temporal_breakdowns,
            temporal_unit_focus=temporal_unit_focus,
            topic_historical_footprints=topic_historical_footprints,
            temporal_topic_focus=temporal_topic_focus
        )

    @classmethod
    def _classify_stem_pattern(cls, text: str) -> str:
        """Deterministic formulation stem pattern detection."""
        if not text:
            return "Unspecified Text"

        # Check comparisons
        if any(w in text for w in ("difference between", "distinguish", "differentiate", "compare")):
            return "Comparison"

        # Check proofs / derivations
        if any(w in text for w in ("prove", "show that", "derive", "derivation", "verify", "establish")):
            return "Proof & Derivation"

        # Check calculations / numerical
        if any(w in text for w in ("calculate", "evaluate", "find", "determine", "compute", "solve", "estimate")):
            return "Calculation & Numerical"

        # Check applications / design
        if any(w in text for w in ("design", "construct", "implement", "draw", "illustrate", "write a program", "algorithm")):
            return "Application & Design"

        # Check theoretical / conceptual
        if any(w in text for w in ("explain", "describe", "discuss", "define", "state", "what is", "what are", "briefly")):
            return "Explanation & Conceptual"

        return "General / Formulated"

    @classmethod
    def _empty_dna(cls) -> ExamDNA:
        return ExamDNA(
            sample_size=DNASampleSize(
                papers=0, questions=0, time_range_years=(0, 0),
                years=[], exam_types=[], sufficiency=DataSufficiency.INSUFFICIENT,
                contributing_exam_ids=[], unmapped_question_count=0, unscored_question_count=0,
                total_marks=0.0
            ),
            topics=[], units=[], question_types=[],
            repetition=RepetitionDNA(exact_count=0, near_count=0, conceptual_count=0, structural_count=0),
            families=[], temporal_trends=[],
            unit_distribution=UnitDistributionDNA(
                units=[], unmapped_question_count=0, unmapped_marks=0.0,
                is_marks_weighted=False, total_marks_evaluated=0.0, total_questions_evaluated=0
            ),
            marks_distribution=MarksDistributionDNA(
                buckets=[], unscored_question_count=0, unscored_percentage=0.0,
                total_scored_questions=0, total_marks=0.0
            ),
            pattern_summary=QuestionPatternSummaryDNA(
                top_recurring_families=[],
                stem_patterns=[],
                repetition_breakdown=RepetitionBreakdownDNA()
            ),
            temporal_unit_question_type_breakdown=[],
            temporal_unit_focus=[],
            topic_historical_footprints=[],
            temporal_topic_focus=[]
        )

