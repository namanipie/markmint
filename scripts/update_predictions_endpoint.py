import re

with open('backend/api/endpoints/predictions.py', 'r', encoding='utf-8') as f:
    content = f.read()

target_str = """        scope = get_course_assessment_scope(
            course.id,
            norm_cycle,
            db=db,
            track_id=active_track.id if active_track else None
        )
        if not hist_exams_orm:"""

replacement_str = """        scope = get_course_assessment_scope(
            course.id,
            norm_cycle,
            db=db,
            track_id=active_track.id if active_track else None
        )

        from datetime import datetime, timezone
        from backend.core.version import MODEL_VERSION, TAXONOMY_VERSION, ENGINE_VERSION
        from collections import defaultdict

        # OPTION B: Syllabus-derived baseline when 0 historical papers exist for this specific exam
        if not hist_exams_orm:
            intended_units = sorted(list(scope.in_scope_unit_numbers)) if scope.in_scope_unit_numbers else []
            if not intended_units:
                if norm_cycle == "CT1":
                    intended_units = [1, 2]
                elif norm_cycle == "CT2":
                    intended_units = [3, 4]
                else:
                    intended_units = [1, 2, 3, 4, 5]

            syl_filter = [Syllabus.course_id == course.id]
            if active_track:
                syl_filter.append(Syllabus.track_id == active_track.id)

            syl_topic_rows = (
                db.query(Topic.id, Topic.name, Unit.number, Unit.name)
                .join(Unit, Topic.unit_id == Unit.id)
                .join(Syllabus, Unit.syllabus_id == Syllabus.id)
                .filter(*syl_filter, Unit.number.in_(intended_units))
                .order_by(Unit.number.asc(), Topic.id.asc())
                .all()
            )

            cycle_label = scope.student_label or ("Cycle Test 1" if norm_cycle == "CT1" else "Cycle Test 2" if norm_cycle == "CT2" else "End Semester")

            baseline_predictions = []
            for rank_num, (t_id, t_name, u_num, u_name) in enumerate(syl_topic_rows[:12], 1):
                clean_name = t_name.strip()
                score_val = round(max(0.20, 1.0 - (rank_num * 0.06)), 2)
                baseline_predictions.append({
                    "category": "topic",
                    "name": clean_name,
                    "rank": rank_num,
                    "score": score_val,
                    "confidence": "SYLLABUS_BASELINE",
                    "prediction_score": score_val,
                    "probability": None,
                    "topic_id": t_id,
                    "unit_number": u_num,
                    "unit_name": u_name,
                    "evidence_count": 0,
                    "papers_analyzed": 0,
                    "papers_with_topic": 0,
                    "historical_occurrences": 0,
                    "total_marks_observed": 0.0,
                    "evidence_sufficiency": "BASELINE_SYLLABUS_ONLY",
                    "is_baseline_fallback": True,
                    "reason_codes": ["SYLLABUS_MANDATE", "CORE_CURRICULUM"],
                    "explanation": f"Syllabus-Derived Baseline ({cycle_label}) — 0 historical papers in archive yet. Focus on this foundational Unit {u_num} topic.",
                    "timeline": [],
                    "evidence_breakdown": {
                        "average_marks": 0.0,
                        "distinct_exam_count": 0,
                        "exam_coverage_ratio": 0.0,
                        "historical_occurrences": 0,
                        "total_marks_observed": 0.0,
                        "source_exams": [],
                        "reason_summary": f"Curriculum baseline for {cycle_label} from official SRMIST syllabus."
                    }
                })

            baseline_unit_breakdown = []
            for r_idx, u_num in enumerate(intended_units, 1):
                matching_rows = [r for r in syl_topic_rows if r[2] == u_num]
                u_title = matching_rows[0][3] if matching_rows else f"Unit {u_num}"
                equal_pct = round(100.0 / len(intended_units), 1) if intended_units else 0.0
                baseline_unit_breakdown.append({
                    "rank": r_idx,
                    "unit_number": u_num,
                    "unit_name": u_title,
                    "question_count": 0,
                    "marks": 0.0,
                    "percentage_of_marks": equal_pct,
                    "percentage_of_questions": equal_pct,
                    "paper_coverage": 0.0,
                    "is_baseline": True
                })

            assessment_scope_payload = {
                "student_cycle": norm_cycle or "ALL",
                "component_code": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
                "component_label": scope.component_label or cycle_label,
                "student_label": cycle_label,
                "role": scope.role,
                "marks": scope.marks,
                "evidence_status": "SYLLABUS_FALLBACK",
                "intended_scope": scope.intended_scope,
                "observed_scope": scope.observed_scope,
                "source_document": scope.source_document,
                "unit_numbers": intended_units,
                "total_in_scope_topics": len(syl_topic_rows),
                "observed_in_scope_topics": 0,
                "unobserved_in_scope_topics": [
                    {"name": r[1], "status": "UNOBSERVED_IN_SCOPE", "message": "In syllabus scope"}
                    for r in syl_topic_rows
                ],
                "out_of_scope_observed_topics": [],
            }

            return {
                "course_id": course.id,
                "subject": course.name,
                "target_year": target_year,
                "assessment_cycle": norm_cycle or "ALL",
                "assessment_component": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
                "assessment_label": cycle_label,
                "evidence_status": "SYLLABUS_FALLBACK",
                "intended_scope": scope.intended_scope,
                "observed_scope": scope.observed_scope,
                "assessment_scope": assessment_scope_payload,
                "predictions": baseline_predictions,
                "empirical_unit_breakdown": baseline_unit_breakdown,
                "observed_years": [],
                "unobserved_years": [],
                "gap_years": [],
                "evidence": f"Syllabus-derived baseline: 0 historical {cycle_label} papers available in archive yet.",
                "data_quality": f"Curriculum baseline active. Topics prioritized from official syllabus Units {', '.join(str(u) for u in intended_units)}.",
                "model_metadata": {
                    "model_version": MODEL_VERSION,
                    "taxonomy_version": TAXONOMY_VERSION,
                    "engine_version": ENGINE_VERSION,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }

        # HISTORICAL PAPERS EXIST: Compute empirical data-driven predictions strictly for this exam
        hist_exams_dicts = _build_historical_exam_payloads(hist_exams_orm)

        analyzer = DNAAnalyzerService()
        dna = analyzer.analyze(hist_exams_dicts)
        
        engine = ExamScopeCombinedModel(dna)
        all_topic_preds = engine.predict(PredictionTarget.TOPIC)
        family_preds = engine.predict(PredictionTarget.FAMILY)

        # Compute empirical unit distribution strictly from historical papers of THIS exam (NO HARDCODING)
        empirical_unit_map = defaultdict(lambda: {"q_count": 0, "marks": 0.0, "papers": set(), "name": ""})
        total_eval_q = 0
        total_eval_m = 0.0
        for ex in hist_exams_orm:
            for sec in ex.sections:
                for q in sec.questions:
                    total_eval_q += 1
                    m = float(q.marks or 0.0)
                    total_eval_m += m
                    for t in q.topics:
                        if t.unit:
                            u_num = t.unit.number
                            empirical_unit_map[u_num]["q_count"] += 1
                            empirical_unit_map[u_num]["marks"] += m
                            empirical_unit_map[u_num]["papers"].add(ex.id)
                            empirical_unit_map[u_num]["name"] = t.unit.name

        # Rank units strictly by marks & question appearances in these exam papers
        ranked_empirical_units = []
        for rank_idx, (u_num, data) in enumerate(
            sorted(empirical_unit_map.items(), key=lambda x: (x[1]["marks"], x[1]["q_count"]), reverse=True),
            1
        ):
            m_pct = round((data["marks"] / total_eval_m * 100), 1) if total_eval_m > 0 else 0.0
            q_pct = round((data["q_count"] / total_eval_q * 100), 1) if total_eval_q > 0 else 0.0
            coverage = round(len(data["papers"]) / len(hist_exams_orm), 2) if hist_exams_orm else 0.0
            ranked_empirical_units.append({
                "rank": rank_idx,
                "unit_number": u_num,
                "unit_name": data["name"],
                "question_count": data["q_count"],
                "marks": round(data["marks"], 1),
                "percentage_of_marks": m_pct,
                "percentage_of_questions": q_pct,
                "paper_coverage": coverage,
                "is_baseline": False
            })

        # All topics derived from this exam's papers are naturally valid; prioritize in-scope if scope defined
        if not scope.is_all and scope.in_scope_topic_names:
            in_scope_preds = [p for p in all_topic_preds if p.name in scope.in_scope_topic_names]
            out_of_scope_preds = [p for p in all_topic_preds if p.name not in scope.in_scope_topic_names]
            topic_preds = in_scope_preds + out_of_scope_preds
        else:
            topic_preds = all_topic_preds
            out_of_scope_preds = []

        unobserved_in_scope = (
            [
                {
                    "name": name,
                    "status": "UNOBSERVED_IN_SCOPE",
                    "message": "In syllabus scope, but no historical evidence available",
                }
                for name in sorted(list(scope.in_scope_topic_names - {p.name for p in topic_preds}))
            ]
            if (not scope.is_all and scope.in_scope_topic_names)
            else []
        )
        assessment_scope_payload = {
            "student_cycle": norm_cycle or "ALL",
            "component_code": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
            "component_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "student_label": scope.student_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "role": scope.role,
            "marks": scope.marks,
            "evidence_status": scope.evidence_status,
            "intended_scope": scope.intended_scope,
            "observed_scope": scope.observed_scope,
            "source_document": scope.source_document,
            "unit_numbers": sorted(list(scope.in_scope_unit_numbers)) if scope.in_scope_unit_numbers else [u["unit_number"] for u in ranked_empirical_units],
            "total_in_scope_topics": len(scope.in_scope_topic_names),
            "observed_in_scope_topics": len(topic_preds),
            "unobserved_in_scope_topics": unobserved_in_scope,
            "out_of_scope_observed_topics": [
                {
                    "name": p.name,
                    "status": "OUT_OF_SCOPE_OBSERVED",
                    "score": round(float(p.score or 0.0), 4),
                    "message": "Observed on historical examination papers.",
                }
                for p in out_of_scope_preds
            ],
        }

        observed_years = sorted(list({e.year for e in hist_exams_orm if e.year is not None}))

        predictions = []
        # Return top 10 empirical topic predictions with clean, recognizable names and authoritative unit tags
        for p in topic_preds[:10]:
            p_dict = p.to_dict()
            t_obj = (
                db.query(Topic)
                .join(Unit, Topic.unit_id == Unit.id)
                .join(Syllabus, Unit.syllabus_id == Syllabus.id)
                .filter(Syllabus.course_id == course.id, Topic.name == p.name)
                .first()
            )
            if t_obj:
                p_dict["topic_id"] = t_obj.id
                if t_obj.unit:
                    p_dict["unit_number"] = t_obj.unit.number
                    p_dict["unit_name"] = t_obj.unit.name

            topic_years = {
                e.year for e in hist_exams_orm
                if e.year is not None and any(
                    any(t.name == p.name for t in q.topics)
                    for s in e.sections for q in s.questions
                )
            }
            p_dict["timeline"] = [
                {
                    "year": y,
                    "exam_exists": True,
                    "topic_present": y in topic_years,
                    "family_present": False,
                    "present": y in topic_years,
                    "status": "TOPIC_PRESENT" if y in topic_years else "TOPIC_ABSENT",
                }
                for y in observed_years
            ]
            p_dict["historical_years"] = sorted(list(topic_years))
            matching_topic_exams = [
                {
                    "exam_id": e.id,
                    "year": e.year,
                    "assessment_type": e.assessment_type,
                    "title": e.document.title if (getattr(e, "document", None) and e.document and e.document.title) else f"Exam {e.year} ({e.assessment_type or 'Main'})",
                }
                for e in hist_exams_orm
                if e.year is not None and any(
                    any(t.name == p.name for t in q.topics)
                    for s in e.sections for q in s.questions
                )
            ]
            if "evidence_breakdown" in p_dict:
                p_dict["evidence_breakdown"]["source_exams"] = matching_topic_exams
                if topic_years:
                    p_dict["evidence_breakdown"]["source_years"] = sorted(list(topic_years))
            if "explainability" in p_dict:
                p_dict["explainability"]["source_exams"] = matching_topic_exams
                if topic_years:
                    p_dict["explainability"]["source_years"] = sorted(list(topic_years))
            predictions.append(p_dict)

        # Return top recurring question families with clean recognizable labels and unit numbers
        for p in family_preds[:6]:
            p_dict = p.to_dict()
            p_dict["is_family"] = True

            # Resolve unit number for family from its questions
            fam_q = (
                db.query(Question)
                .join(Section)
                .join(Exam)
                .filter(Question.family_id == p_dict.get("family_id"), Exam.course_id == course.id)
                .first()
            )
            if fam_q and fam_q.topics and fam_q.topics[0].unit:
                p_dict["unit_number"] = fam_q.topics[0].unit.number
                p_dict["unit_name"] = fam_q.topics[0].unit.name
                p_dict["associated_topic_name"] = fam_q.topics[0].name

            fam_years = {
                e.year for e in hist_exams_orm
                if e.year is not None and any(
                    q.family and q.family.canonical_name == p.name
                    for s in e.sections for q in s.questions
                )
            }
            p_dict["timeline"] = [
                {
                    "year": y,
                    "exam_exists": True,
                    "topic_present": False,
                    "family_present": y in fam_years,
                    "present": y in fam_years,
                    "status": "FAMILY_PRESENT" if y in fam_years else "FAMILY_ABSENT",
                }
                for y in observed_years
            ]
            p_dict["historical_years"] = sorted(list(fam_years))
            matching_fam_exams = [
                {
                    "exam_id": e.id,
                    "year": e.year,
                    "assessment_type": e.assessment_type,
                    "title": e.document.title if (getattr(e, "document", None) and e.document and e.document.title) else f"Exam {e.year} ({e.assessment_type or 'Main'})",
                }
                for e in hist_exams_orm
                if e.year is not None and any(
                    q.family and q.family.canonical_name == p.name
                    for s in e.sections for q in s.questions
                )
            ]
            if "evidence_breakdown" in p_dict:
                p_dict["evidence_breakdown"]["source_exams"] = matching_fam_exams
                if fam_years:
                    p_dict["evidence_breakdown"]["source_years"] = sorted(list(fam_years))
            if "explainability" in p_dict:
                p_dict["explainability"]["source_exams"] = matching_fam_exams
                if fam_years:
                    p_dict["explainability"]["source_years"] = sorted(list(fam_years))
            predictions.append(p_dict)

        all_span = list(range(observed_years[0], observed_years[-1] + 1)) if observed_years else []
        unobserved_years = [y for y in all_span if y not in observed_years]

        return {
            "course_id": course.id,
            "subject": course.name,
            "target_year": target_year,
            "assessment_cycle": norm_cycle or "ALL",
            "assessment_component": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
            "assessment_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "evidence_status": scope.evidence_status,
            "intended_scope": scope.intended_scope,
            "observed_scope": scope.observed_scope,
            "assessment_scope": assessment_scope_payload,
            "predictions": predictions,
            "empirical_unit_breakdown": ranked_empirical_units,
            "observed_years": observed_years,
            "unobserved_years": unobserved_years,
            "gap_years": unobserved_years,
            "evidence": f"Analyzed {len(hist_exams_orm)} historical {scope.student_label or norm_cycle} exams across {len(observed_years)} years.",
            "data_quality": f"Data-driven evidence base for {scope.student_label or norm_cycle} from verified examination archives.",
            "model_metadata": {
                "model_version": MODEL_VERSION,
                "taxonomy_version": TAXONOMY_VERSION,
                "engine_version": ENGINE_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }"""

# Find start of block to replace
start_idx = content.find("        scope = get_course_assessment_scope(")
# Find end of block: right before '    except HTTPException:'
end_idx = content.find("    except HTTPException:")

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + replacement_str + "\n" + content[end_idx:]
    with open('backend/api/endpoints/predictions.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully updated backend/api/endpoints/predictions.py")
else:
    print(f"Could not find indices: start={start_idx}, end={end_idx}")
