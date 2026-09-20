"""
Compiles canonical course catalog data from production_corpus.db into src/lib/courses-catalog.json.
Extracts factual numbers: papers, questions, mapped questions, units, topics, high-yield topics, and tracks.
"""
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.core.database import SessionLocal
from backend.models.core import (
    Course, Syllabus, Unit, Topic, Exam, Section, Question, CourseTrack, question_topic
)
from sqlalchemy import func

DESCRIPTIONS = {
    1: 'Calculus and Linear Algebra covers matrices, eigenvalues, multi-variable partial differentiation, vector calculus, ordinary differential equations, and infinite series under SRMIST Regulation 2021.',
    2: 'Engineering Chemistry provides rigorous foundational understanding of water treatment, polymer chemistry, thermodynamics, electrochemistry, and advanced analytical instrumentation.',
    3: 'Philosophy of Engineering explores engineering ethics, holistic engineering design methodologies, professional responsibility, epistemological models, and societal sustainability frameworks.',
    4: 'Introduction to Computational Biology integrates biological data science, nucleic acid informatics, sequence alignment algorithms, protein structure analysis, and genomics databases.',
    5: 'Programming for Problem Solving covers C programming foundations, control flow structures, modular procedural design, arrays, pointers, memory allocation, and foundational algorithmic problem-solving.',
    6: 'Fundamental of Economics (FOE) analyzes micro and macro-economic theory, demand elasticity, production cost functions, market competition structures, and national engineering fiscal frameworks.',
    7: 'Biomedical Sensors introduces biomedical transducer mechanisms, physiological signal recording, bio-potential electrodes, optical sensors, and biosensing instrumentation.',
    8: 'Foreign Languages offers track-isolated elective foreign language pathways at SRMIST, comprising German, French, Spanish, Japanese, Korean, and Chinese with dedicated syllabuses and examinations.',
    9: 'Cell Biology investigates cellular organelles, biomembrane transport dynamics, intracellular signaling cascades, cell cycle regulation, and molecular bioenergetics.',
    10: 'Microbiology covers microbial taxonomy, bacterial ultrastructure, viral biology, culture techniques, antimicrobial mechanisms, and industrial fermentation applications.',
    11: 'Physical and Analytical Chemistry delves into chemical kinetics, spectroscopy, phase equilibria, chromatographic separation techniques, and electroanalytical quantification.',
    12: 'Biochemistry explores structural and functional properties of biomolecules, enzymatic kinetics, bioenergetics, metabolic pathways (glycolysis, Krebs cycle), and nucleic acid metabolism.',
    13: 'Semiconductor Physics and Computational Methods covers quantum mechanics principles, energy band theory, semiconductor transport mechanics, carrier dynamics, and numerical modeling methods.',
    14: 'Electrical and Electronics Engineering covers DC/AC network theorems, magnetic circuits, single-phase and three-phase power systems, operational amplifiers, and semiconductor electronic devices.',
    15: 'Communicative English focuses on professional technical communication, reading comprehension, syntactical accuracy, report drafting, business correspondence, and verbal engineering communication.',
    16: 'Advanced Calculus and Complex Analysis covers analytic functions, conformal mapping, contour integration, Cauchy residue theorems, Fourier transforms, and Laplace transformation calculus.',
    17: 'Object Oriented Design and Programming (OODP) teaches object-oriented modeling, polymorphism, inheritance, generic programming, exception handling, design patterns, and C++/Java OOP implementations.',
    18: 'Electronic System and PCB Design covers electronic schematic capture, printed circuit board (PCB) routing rules, signal integrity, component footprints, and hardware fabrication standards.',
    19: 'Electromagnetic Theory, Quantum Mechanics, Waves and Optics covers Maxwell equations, electromagnetic wave propagation, wave-particle duality, Schrödinger equation, and optical wave phenomena.',
    20: 'Physics: Mechanics covers Newtonian particle dynamics, rotational mechanics, conservation theorems, harmonic oscillations, gravitation, and continuum mechanical elasticity.',
    21: 'Engineering Mechanics teaches statics and dynamics of rigid bodies, concurrent force equilibrium, structural trusses, friction, centroid/moment of inertia, and kinematic equations of motion.',
    22: 'Probability and Statistics covers probability axioms, random variables, probability density distributions, sampling theory, hypothesis testing, ANOVA, and regression modeling.',
    23: 'Building Materials in the Built Environment analyzes mechanical properties and testing standards for cement, concrete, aggregates, steel, timber, masonry, and sustainable construction composites.'
}

SLUG_MAP = {
    1: ('calculus-and-linear-algebra', ['calc', '21mab101t', 'sem1-calc', 'calculus']),
    2: ('chemistry', ['chem', '21cyb101j', 'sem1-chem']),
    3: ('philosophy-of-engineering', ['poe', 'phil', '21gnh101j', 'sem1-phil']),
    4: ('introduction-to-computational-biology', ['icb', '21btb102t', 'sem1-intr', 'comp-bio']),
    5: ('programming-for-problem-solving', ['pps', '21css101j', 'sem1-prog', 'programming']),
    6: ('fundamental-of-economics', ['foe', '18mss101t', 'sem1-fund', 'economics']),
    7: ('biomedical-sensors', ['bmb', '21bmb101t', 'sem1-biom', 'sensors']),
    8: ('foreign-languages', ['fl', 'fore', '21leh-elective', 'sem1-fore', 'languages', 'german', 'french', 'spanish', 'japanese', 'korean', 'chinese', '21leh104t', '21leh101t', '21leh103t', '21leh105t', '21leh102t', '21leh106t']),
    9: ('cell-biology', ['cellbio', '21btc102j', 'sem1-cell']),
    10: ('microbiology', ['microbio', '21btc201t', 'sem1-micr']),
    11: ('physical-and-analytical-chemistry', ['pac', '21chc101j', 'sem1-phys']),
    12: ('biochemistry', ['biochem', '21btc101t', 'sem1-bioc']),
    13: ('semiconductor-physics-and-computational-methods', ['spcm', '21pyb102j', 'sem1-spcm', 'semiconductor-physics']),
    14: ('electrical-and-electronics-engineering', ['eee', '21eeb101j', 'sem1-eee', 'electrical']),
    15: ('communicative-english', ['english', 'eng', '21leh101t', 'sem1-eng']),
    16: ('advanced-calculus-and-complex-analysis', ['acca', '21mab102t', 'sem2-acca', 'advanced-calculus']),
    17: ('object-oriented-design-and-programming', ['oodp', '21csc102j', 'sem2-oodp', 'oop']),
    18: ('electronic-system-and-pcb-design', ['espcb', '21ecc101j', 'sem2-espcb', 'pcb']),
    19: ('electromagnetic-theory-and-quantum-mechanics', ['emphy', '21pyb101j', 'sem1-emphy', 'electromagnetics']),
    20: ('physics-mechanics', ['phymech', '21pyb104j', 'sem1-phymech', 'mechanics']),
    21: ('engineering-mechanics', ['engmech', '21meb101t', 'sem2-engmech']),
    22: ('probability-and-statistics', ['prob', '21mab201t', 'sem2-prob', 'statistics']),
    23: ('building-materials-in-the-built-environment', ['bldmat', '21ceb101t', 'sem2-bldmat', 'building-materials'])
}

CREDITS_MAP = {
    1: 4, 2: 4, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3, 10: 3, 11: 3, 12: 3,
    13: 4, 14: 4, 15: 3, 16: 4, 17: 4, 18: 3, 19: 4, 20: 4, 21: 4, 22: 4, 23: 3
}

def compile_catalog():
    db = SessionLocal()
    courses = db.query(Course).order_by(Course.id).all()
    catalog = []

    for c in courses:
        slug, aliases = SLUG_MAP.get(c.id, (c.code.lower(), []))
        semester = 1 if c.code.startswith("SEM1") else 2
        regulation = "2018" if c.code.startswith("18") or (c.canonical_code and c.canonical_code.startswith("18")) else "2021"
        credits = CREDITS_MAP.get(c.id, 3)
        description = DESCRIPTIONS.get(c.id, f"{c.name} ({c.canonical_code}) academic curriculum at SRMIST.")

        exams = db.query(Exam).filter(Exam.course_id == c.id).all()
        paper_count = len(exams)
        exam_ids = [e.id for e in exams]

        if exam_ids:
            q_rows = (
                db.query(Question.id)
                .join(Section, Question.section_id == Section.id)
                .filter(Section.exam_id.in_(exam_ids))
                .all()
            )
            question_count = len(q_rows)
            q_ids = [r[0] for r in q_rows]

            mapped_q_rows = (
                db.query(question_topic.c.question_id)
                .filter(question_topic.c.question_id.in_(q_ids))
                .distinct()
                .all()
            )
            mapped_question_count = len(mapped_q_rows)
        else:
            question_count = 0
            mapped_question_count = 0

        mapping_rate = round(mapped_question_count / question_count, 3) if question_count > 0 else 0.0

        # Assessment Cycles
        assessment_cycles = [
            {"cycle": "CT1", "label": "Cycle Test 1 (Formative Test 1)", "units": [1, 2], "coverageDescription": "Covers foundational concepts from Units 1 and 2."},
            {"cycle": "CT2", "label": "Cycle Test 2 (Formative Test 2)", "units": [3, 4], "coverageDescription": "Covers intermediate applications from Units 3 and 4."},
            {"cycle": "EndSem", "label": "Semester University Examination", "units": [1, 2, 3, 4, 5], "coverageDescription": "Covers comprehensive syllabus across Units 1 through 5."}
        ]

        # Multi-track handling for Course 8 (Foreign Languages)
        has_tracks = len(c.tracks) > 0
        tracks_data = []

        if has_tracks:
            for t in c.tracks:
                syl = db.query(Syllabus).filter(Syllabus.track_id == t.id).first()
                t_units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all() if syl else []
                t_units_data = []
                for u in t_units:
                    t_units_data.append({
                        "number": u.number,
                        "name": u.name,
                        "topicCount": len(u.topics),
                        "topics": [top.name for top in u.topics]
                    })
                
                t_exams = db.query(Exam).filter(Exam.course_id == c.id, Exam.track_id == t.id).all()
                t_exam_ids = [e.id for e in t_exams]
                t_q_count = (
                    db.query(Question.id)
                    .join(Section, Question.section_id == Section.id)
                    .filter(Section.exam_id.in_(t_exam_ids))
                    .count()
                    if t_exam_ids else 0
                )

                # High yield topics for this track
                t_top_topics = []
                if syl and t_exam_ids:
                    top_rows = (
                        db.query(Topic.name, Unit.number, func.count(Question.id), func.count(func.distinct(Exam.id)))
                        .join(Unit, Topic.unit_id == Unit.id)
                        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
                        .join(question_topic, question_topic.c.topic_id == Topic.id)
                        .join(Question, question_topic.c.question_id == Question.id)
                        .join(Section, Question.section_id == Section.id)
                        .join(Exam, Section.exam_id == Exam.id)
                        .filter(Syllabus.track_id == t.id, Exam.track_id == t.id)
                        .group_by(Topic.name, Unit.number)
                        .order_by(func.count(Question.id).desc())
                        .limit(5)
                        .all()
                    )
                    for r in top_rows:
                        t_top_topics.append({
                            "topic": r[0],
                            "unitNumber": r[1],
                            "questionCount": r[2],
                            "paperCount": r[3]
                        })

                tracks_data.append({
                    "trackKey": t.track_key,
                    "trackName": t.track_name,
                    "trackCode": t.track_code,
                    "paperCount": len(t_exams),
                    "questionCount": t_q_count,
                    "units": t_units_data,
                    "highYieldTopics": t_top_topics,
                    "mintAiUrl": f"/mintai?course={c.code}&language={t.track_key}",
                    "practiceUrl": f"/mintai?course={c.code}&language={t.track_key}&tab=practice"
                })

            units_data = []
            high_yield_topics = []
        else:
            # Single-track course units
            syl = db.query(Syllabus).filter(Syllabus.course_id == c.id).order_by(Syllabus.id.desc()).first()
            c_units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all() if syl else []
            units_data = []
            for u in c_units:
                units_data.append({
                    "number": u.number,
                    "name": u.name,
                    "topicCount": len(u.topics),
                    "topics": [top.name for top in u.topics]
                })

            high_yield_topics = []
            if syl and exam_ids:
                top_rows = (
                    db.query(Topic.name, Unit.number, func.count(Question.id), func.count(func.distinct(Exam.id)))
                    .join(Unit, Topic.unit_id == Unit.id)
                    .join(Syllabus, Unit.syllabus_id == Syllabus.id)
                    .join(question_topic, question_topic.c.topic_id == Topic.id)
                    .join(Question, question_topic.c.question_id == Question.id)
                    .join(Section, Question.section_id == Section.id)
                    .join(Exam, Section.exam_id == Exam.id)
                    .filter(Syllabus.course_id == c.id)
                    .group_by(Topic.name, Unit.number)
                    .order_by(func.count(Question.id).desc())
                    .limit(6)
                    .all()
                )
                for r in top_rows:
                    high_yield_topics.append({
                        "topic": r[0],
                        "unitNumber": r[1],
                        "questionCount": r[2],
                        "paperCount": r[3]
                    })

        catalog.append({
            "id": c.id,
            "slug": slug,
            "aliases": aliases,
            "name": c.name,
            "code": c.code,
            "canonicalCode": c.canonical_code,
            "semester": semester,
            "regulation": regulation,
            "credits": credits,
            "description": description,
            "paperCount": paper_count,
            "questionCount": question_count,
            "mappedQuestionCount": mapped_question_count,
            "mappingRate": mapping_rate,
            "hasTracks": has_tracks,
            "tracks": tracks_data,
            "units": units_data,
            "assessmentCycles": assessment_cycles,
            "highYieldTopics": high_yield_topics,
            "mintAiUrl": f"/mintai?course={c.code}",
            "practiceUrl": f"/mintai?course={c.code}&tab=practice"
        })

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "lib", "courses-catalog.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Successfully compiled catalog with {len(catalog)} courses to {out_path}.")

if __name__ == "__main__":
    compile_catalog()
