"""
Additive, idempotent seeder for Course 8: Foreign Languages (SEM1-FORE).
Establishes a first-class language-track architecture across 6 isolated language tracks:
- German (21LEH104T)
- French (21LEH103T)
- Spanish (21LEH107T)
- Japanese (21LEH105T)
- Korean (21LEH106T)
- Chinese (21LEH102T)

Idempotency guarantees:
- Reuses existing CourseTrack, Syllabus, Unit, Topic, Concept records if already present.
- Never deletes or overwrites existing exam records.
- Associates exams with their respective track_id with strict deterministic provenance.
"""
import os
import sys
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, CourseTrack, Syllabus, Unit, Topic, Concept, Exam, Document, CurriculumMapping
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage

LANGUAGE_TRACK_DEFINITIONS = [
    {
        "key": "german",
        "name": "German",
        "code": "21LEH104T",
        "source": "corpus/Semester_1/German/SYLLABUS/German - Syllabus.pdf",
        "units": [
            (
                1,
                "Begrüßungen, Sich Vorstellen und Grundlagen",
                [
                    "Begrüßungen und Verabschiedungen",
                    "Sich Vorstellen und Persönliche Angaben",
                    "Alphabet, Zahlen bis 100 und Buchstabieren",
                    "Länder, Sprachen und Wohnort",
                    "W-Fragen und Fragewörter",
                    "Wochentage, Monate und Jahreszeiten",
                ],
            ),
            (
                2,
                "Personalpronomen, Verben und Satzbau",
                [
                    "Personalpronomen im Nominativ",
                    "Konjugation Regelmäßiger und Unregelmäßiger Verben",
                    "Zahlen bis eine Million",
                    "Satzbau: Aussagesatz und Fragesätze",
                    "Formulare und Steckbriefe Ausfüllen",
                ],
            ),
            (
                3,
                "Wortschatz, Artikel und Wegbeschreibung",
                [
                    "Wortschatz: Gebäude, Plätze und Verkehrsmittel",
                    "Gegenstände, Schulsachen und Geräte",
                    "Bestimmte und Unbestimmte Artikel im Nominativ",
                    "Negation mit kein und nicht",
                    "Wegbeschreibung, Orientierung und Himmelsrichtungen",
                    "Ordinalzahlen und Datumsangaben",
                ],
            ),
            (
                4,
                "Lebensmittel, Einkaufen, Akkusativ und Uhrzeit",
                [
                    "Lebensmittel, Mahlzeiten und Getränke",
                    "Preise, Einkaufen und Maßeinheiten",
                    "Akkusativ: Bestimmte, Unbestimmte Artikel und Negation",
                    "Verben mit Akkusativ-Ergänzung",
                    "Uhrzeit: Offizielle und Inoffizielle Zeitangaben",
                ],
            ),
            (
                5,
                "Modalverben, Trennbare Verben und Familie",
                [
                    "Modalverben: müssen, können, wollen, sollen, dürfen, mögen",
                    "Trennbare und Untrennbare Verben",
                    "Possessivpronomen im Nominativ",
                    "Familie und Verwandtschaftsverhältnisse",
                    "Präteritum von sein und haben",
                ],
            ),
        ],
    },
    {
        "key": "french",
        "name": "French",
        "code": "21LEH103T",
        "source": "corpus/Semester_1/French/SYLLABUS/French - Syllabus.pdf",
        "units": [
            (
                1,
                "Alphabet, Phonétique et Communication en Classe",
                [
                    "L'Alphabet Français et la Phonétique",
                    "Les Accents et la Ponctuation",
                    "L'Orthographe et les Règles de Prononciation",
                    "La Communication et les Consignes en Classe",
                ],
            ),
            (
                2,
                "Salutations, Pronoms Sujets, Verbes de Base et Nombres",
                [
                    "Les Salutations et Formules de Politesse",
                    "Les Pronoms Personnels Sujets",
                    "Verbes Fondamentaux: être, avoir, s'appeler, habiter",
                    "Se Présenter et Présenter Quelqu'un",
                    "Les Articles Définis et Indéfinis",
                    "Les Nombres de 0 à 69, Jours et Mois",
                    "Les Pronoms Toniques",
                ],
            ),
            (
                3,
                "Verbes du 1er Groupe, Nationalités et Famille",
                [
                    "Les Nombres de 70 à 1000",
                    "Verbes Réguliers du 1er Groupe en -er",
                    "Verbes Aller et Venir",
                    "Les Professions et Métiers",
                    "Pays, Villes et Nationalités",
                    "Genre et Nombre des Adjectifs Qualificatifs",
                    "Les Prépositions de Lieu",
                    "Les Adjectifs Possessifs et la Famille",
                ],
            ),
            (
                4,
                "Mots Interrogatifs, Verbes Modaux, Loisirs et Heure",
                [
                    "Les Mots et Structures Interrogatives",
                    "Les Verbes Modaux: vouloir, pouvoir, devoir",
                    "Les Verbes Pronominaux et la Routine",
                    "Verbes du 2ème Groupe en -ir",
                    "Les Loisirs, Goûts et Préférences",
                    "Le Futur Proche",
                    "L'Heure et les Horaires",
                ],
            ),
            (
                5,
                "Adjectifs Démonstratifs, Quantités, Vêtements et Sorties",
                [
                    "Les Adjectifs Démonstratifs: ce, cette, ces",
                    "Les Expressions de Quantité et Articles Partitifs",
                    "Verbes Particuliers en -ger, -cer, -yer",
                    "Verbes du 3ème Groupe Irréguliers",
                    "Les Vêtements, Couleurs et la Mode",
                    "Adverbes de Fréquence et de Temps",
                    "Proposer, Accepter ou Refuser une Sortie",
                ],
            ),
        ],
    },
    {
        "key": "spanish",
        "name": "Spanish",
        "code": "21LEH107T",
        "source": "corpus/Semester_1/Spanish/SYLLABUS/Spanish - Syllabus.pdf",
        "units": [
            (
                1,
                "Abecedario, Saludos, Presentación y Verbos Básicos",
                [
                    "El Abecedario y Pronunciación",
                    "Saludos y Despedidas",
                    "Nacionalidades y Profesiones",
                    "Números del 1 al 100",
                    "Presentación Personal y Datos de Contacto",
                    "Pronombres Personales y Artículos Definidos",
                    "Verbos Auxiliares: ser, tener, llamarse",
                    "La Familia y Relaciones",
                ],
            ),
            (
                2,
                "Artículos Indefinidos, Direcciones y Presente Regular",
                [
                    "Artículos Indefinidos y Números hasta 1000",
                    "Estructuras de Negación y Traducción",
                    "Direcciones Cardinales y Medios de Transporte",
                    "Preguntar por Direcciones y Ubicaciones",
                    "Presente de Indicativo: Verbos Regulares -ar, -er, -ir",
                    "El Verbo Hay y Expresión de Existencia",
                    "El Superlativo y Cuantificadores",
                    "Preguntas Interrogativas: qué, cuál, cuántos, dónde, cómo",
                ],
            ),
            (
                3,
                "Verbos Ser y Estar, Clima y Verbos Irregulares",
                [
                    "Diferenciación entre Ser y Estar",
                    "Números Ordinales y Días de la Semana",
                    "Verbos Irregulares en Tiempo Presente",
                    "Expresiones del Clima y Estaciones del Año",
                    "Comprensión Lectora y Expresión Escrita",
                ],
            ),
            (
                4,
                "Compras, Precios, Demostrativos y Perífrasis Obligativa",
                [
                    "Vocabulario Escolar y Académico",
                    "Compras en Tiendas y Pedir Precios",
                    "Demostrativos: este, esta, estos, estas, esto",
                    "Perífrasis Obligativa: tener que + infinitivo",
                    "El Verbo Ir y Lugares",
                    "Prendas de Vestir y Colores",
                ],
            ),
            (
                5,
                "Aspecto, Carácter, Gustos con Gustar y Restaurante",
                [
                    "Descripción del Aspecto Físico y Carácter",
                    "Expresar Gustos e Intereses con el Verbo Gustar",
                    "En el Restaurante: Ordenar Comida y Pagar",
                    "Adjetivos Posesivos y Pertenencia",
                    "Rutina Diaria y Actividades Cotidianas",
                ],
            ),
        ],
    },
    {
        "key": "japanese",
        "name": "Japanese",
        "code": "21LEH105T",
        "source": "corpus/Semester_1/Japanese/SYLLABUS/Japanese - Syllabus.pdf",
        "units": [
            (
                1,
                "Self-Introduction, Hiragana Script and Basic Grammar",
                [
                    "Japanese Language, Culture and Self-Introduction",
                    "Greetings and Classroom Expressions",
                    "Basic Particles: wa, ka, mo, no",
                    "Sentence Patterns: desu and ja arimasen",
                    "Hiragana Writing System: Lessons 1 to 4",
                    "Demonstrative Pronouns: kono, sono, ano, dono, kore, sore, are, dore",
                    "Existence Sentences: arimasu, imasu with ni, ga particles",
                    "Days of the Week, Months, and Numbers",
                    "Kanji for Days of the Week and Numbers",
                ],
            ),
            (
                2,
                "Time Expressions, Locations, Prices and Culture",
                [
                    "Time Expressions: Hours, Minutes, Gozen and Gogo",
                    "Location Markers: ue, shita, naka and Directions",
                    "Location Pronouns: koko, soko, asoko, doko",
                    "Asking Prices and Requesting with o kudasai",
                    "Numbers up to One Lakh (100,000)",
                    "Japanese Seasons, Weather, Origami, Ikebana and Culture",
                    "Hiragana Lessons 5 to 10: Double Consonants and Long Vowels",
                    "Kanji: Numbers, Yen, Colours and Directions",
                ],
            ),
            (
                3,
                "Counters, Family, Living Style and Katakana",
                [
                    "Keeki o Yattsu Kudasai and General Counters (~tsu)",
                    "Specialized Counters: -nin, -hiki, -dai, -kai",
                    "Family Members: Plain vs Polite Forms",
                    "Japanese House, Living Style and Architecture",
                    "Katakana Rules, Characters and Writing System",
                    "Kanji: otoko, onna, ko, hito",
                ],
            ),
            (
                4,
                "Verbs, Tenses, Particles and Adjectives",
                [
                    "Action Verbs: ikimasu, okimasu, nemasu, tabemasu",
                    "Verb Tenses: Past Tense and Negative Forms (~masen deshita)",
                    "Particles in Context: e, de, to, ni, o, ga",
                    "Adjectives: -i and -na Ending Adjectives",
                    "Kanji: ikimasu, mimasu, yasumimasu, kaimasu",
                    "Daily Expressions, Body Parts and Religious Beliefs",
                ],
            ),
            (
                5,
                "Invitational Forms, Te-Form, Tai-Form and Kanji",
                [
                    "Invitational Expressions: ~masen ka and ~mashou",
                    "Adjectives: Present, Past, Affirmative and Negative Forms",
                    "Stationery and Transport Vocabulary",
                    "Grammar: Usage of ~te Form",
                    "Grammar: Desire and Want with ~tai Form",
                    "Kanji: ookii, chiisai, eki, chuui",
                    "Japanese Tea Ceremony, Political System and Economy",
                ],
            ),
        ],
    },
    {
        "key": "korean",
        "name": "Korean",
        "code": "21LEH106T",
        "source": "corpus/Semester_1/Korean/SYLLABUS/Korean - Syllabus.pdf",
        "units": [
            (
                1,
                "Hangul Alphabet, Vowels, Consonants and Self-Introduction",
                [
                    "Introduction to Korea and Korean Culture",
                    "Hangul Writing System (한글 소개)",
                    "Single Vowels and Double Vowels (단모음, 이중모음)",
                    "Basic, Aspirated and Tense Consonants",
                    "Final Consonants / Batchim (받침)",
                    "Self-Introduction and Daily Greetings (자기 소개, 인사말)",
                ],
            ),
            (
                2,
                "Particles, Sentence Endings and Demonstratives",
                [
                    "Topic Marking Particles: eun / neun (은/는)",
                    "Subject Marking Particles: i / ga (이/가)",
                    "Informal Polite Sentence Endings: ieyo / yeyo (이에요/예요)",
                    "Formal Polite Sentence Endings: bipnida / seupnida (ㅂ니다/습니다)",
                    "Demonstrative Pronouns: i, geu, jeo (이, 그, 저)",
                    "Sino-Korean Number System and Applications",
                ],
            ),
            (
                3,
                "Verb Conjugations, Tenses and Weather",
                [
                    "Present Tense Verb Conjugation: ayo / eoyo / haeyo (아요/어요/해요)",
                    "Past Tense Verb Conjugation: asseoyo / eosseoyo (았/었/했어요)",
                    "Native Korean Numbers and Counting Units",
                    "Weather, Seasons and Daily Vocabulary",
                    "Location Particles: e and eseo (에, 에서)",
                ],
            ),
            (
                4,
                "Time System, Calendar, Future Tense and Honorifics",
                [
                    "Telling Time: Hours, Minutes and Periods of the Day",
                    "Days of the Week and Months of the Year",
                    "Future Tense Conjugation: (eu)l geoyeyo ((으)ㄹ 거예요)",
                    "Object Marking Particles: eul / reul (을/를)",
                    "Honorific Particle: kkeseo and Subject Honorifics (시/으시)",
                ],
            ),
            (
                5,
                "Ability, Obligations, Requests and Daily Activities",
                [
                    "Expressing Ability and Possibility: (eu)l su itda / eopda ((으)ㄹ 수 있다/없다)",
                    "Imperatives and Requests: (eu)seyo ((으)세요)",
                    "Prohibitions: ji maseyo (지 마세요)",
                    "Expressing Desire and Wants: go sipda (고 싶다)",
                    "Complex Sentences with Connective Particles (고, 서)",
                    "Daily Activities, Hobbies and Campus Life",
                ],
            ),
        ],
    },
    {
        "key": "chinese",
        "name": "Chinese",
        "code": "21LEH102T",
        "source": "corpus/Semester_1/Chinese/SYLLABUS/Chinese - Syllabus.pdf",
        "units": [
            (
                1,
                "Pinyin, Tones, Basic Strokes and Daily Greetings",
                [
                    "Introduction to Mandarin Chinese and Geography",
                    "Pinyin System: Initials, Finals and Combinations",
                    "The Four Tones and Tone Neutralization",
                    "Eight Basic Strokes and Stroke Order of Characters",
                    "Personal Pronouns and Plural Forms (我, 你, 他, 们)",
                    "Grammar Particles: hen (很), ye (也), ma (吗), ne (呢), de (的)",
                    "Basic Daily Greetings and Politeness Phrases",
                ],
            ),
            (
                2,
                "Numbers, Currency, Time and Simple Sentence Patterns",
                [
                    "Chinese Number System and Counting",
                    "Chinese Currency and Monetary Terms (元, 角, 分)",
                    "Telephone Numbers and Conversational Needs",
                    "Time Telling, Calendar, Days, Months and Seasons",
                    "Basic S-V-O Sentence Patterns in Mandarin",
                    "Verbs: shi / bu shi (是/不是) and you / mei you (有/没有)",
                    "Asking and Introducing Nationalities",
                ],
            ),
            (
                3,
                "Question Words, Prices, Locations and Professions",
                [
                    "Interrogative Words: ji (几) and duo shao (多少)",
                    "Asking and Bargaining Prices in Chinese",
                    "Asking Names Formally and Expressing Apologies",
                    "Location Prepositions with zai (在)",
                    "Spatial Demonstratives: zher (这儿), nar (那儿), nar (哪儿)",
                    "Occupations, Professions and Workplace Vocabulary",
                ],
            ),
            (
                4,
                "Suggestions, Comments, Food and Sports",
                [
                    "Making, Accepting and Declining Suggestions",
                    "Subject-Predicate as Predicate Constructions",
                    "Food, Fruits and Ordering Meals Vocabulary",
                    "Action Verbs and Adverbial Modifiers",
                    "Sports, Games, Hobbies and Leisure Vocabulary",
                ],
            ),
            (
                5,
                "Family, University, Time Sequence and Modal Verbs",
                [
                    "Describing Family Members and Relatives",
                    "University, Academic Departments and Student Life",
                    "Time Sequencing Words: yiqian (以前), yihou (以后), haishi (还是)",
                    "Optative Modal Verbs: hui (会), neng (能), keyi (可以)",
                    "Expressing Likes, Dislikes and Color Preferences",
                    "Traditional Chinese Festivals and Culture",
                ],
            ),
        ],
    },
]


def seed_foreign_language_tracks():
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == 8).first()
        if not course:
            print("ERROR: Course 8 not found.")
            return

        course.canonical_code = "21LEH-ELECTIVE"
        course.regulation_year = 2021
        course.department = "English and Foreign Languages"

        # 1. Clean dummy general unit on Course 8 if any
        dummy_units = db.query(Unit).join(Syllabus).filter(
            Syllabus.course_id == 8,
            Unit.name == "General Unit"
        ).all()
        for du in dummy_units:
            topics = db.query(Topic).filter(Topic.unit_id == du.id).all()
            if not topics:
                db.delete(du)
        db.flush()

        created_tracks: Dict[str, CourseTrack] = {}

        # 2. Seed Each Language Track
        for defn in LANGUAGE_TRACK_DEFINITIONS:
            t_key = defn["key"]
            t_name = defn["name"]
            t_code = defn["code"]
            t_source = defn["source"]

            track = db.query(CourseTrack).filter(
                CourseTrack.course_id == 8,
                CourseTrack.track_key == t_key
            ).first()

            if not track:
                track = CourseTrack(
                    course_id=8,
                    track_key=t_key,
                    track_name=t_name,
                    track_code=t_code,
                    track_type="LANGUAGE",
                    source_metadata={"syllabus_file": t_source, "regulation": 2021}
                )
                db.add(track)
                db.flush()
            else:
                track.track_name = t_name
                track.track_code = t_code
                track.source_metadata = {"syllabus_file": t_source, "regulation": 2021}

            created_tracks[t_key] = track

            # Track-scoped Syllabus
            syllabus = db.query(Syllabus).filter(
                Syllabus.course_id == 8,
                Syllabus.track_id == track.id,
                Syllabus.version == "2021"
            ).first()

            if not syllabus:
                syllabus = Syllabus(
                    course_id=8,
                    track_id=track.id,
                    version="2021"
                )
                db.add(syllabus)
                db.flush()

            unit_map = {}

            # Seed Units and Topics
            for u_num, u_name, topics in defn["units"]:
                unit = db.query(Unit).filter(
                    Unit.syllabus_id == syllabus.id,
                    Unit.number == u_num
                ).first()

                if not unit:
                    unit = Unit(
                        syllabus_id=syllabus.id,
                        number=u_num,
                        name=u_name
                    )
                    db.add(unit)
                    db.flush()
                else:
                    unit.name = u_name

                unit_map[u_num] = unit

                for top_name in topics:
                    top = db.query(Topic).filter(
                        Topic.unit_id == unit.id,
                        Topic.name == top_name
                    ).first()

                    if not top:
                        top = Topic(unit_id=unit.id, name=top_name)
                        db.add(top)
                        db.flush()

                    concept = db.query(Concept).filter(
                        Concept.canonical_name == top_name,
                        Concept.subject == f"Foreign Languages - {t_name}"
                    ).first()
                    if not concept:
                        concept = Concept(
                            canonical_name=top_name,
                            subject=f"Foreign Languages - {t_name}",
                            unit_id=unit.id
                        )
                        db.add(concept)

            # Seed Track-Scoped Assessment Plan
            plan = db.query(CourseAssessmentPlan).filter(
                CourseAssessmentPlan.course_id == 8,
                CourseAssessmentPlan.track_id == track.id,
                CourseAssessmentPlan.regulation_year == 2021
            ).first()

            if not plan:
                plan = CourseAssessmentPlan(
                    course_id=8,
                    track_id=track.id,
                    regulation_year=2021,
                    source_title=f"SRM IST {t_code} {t_name} Assessment Plan",
                    version=f"1.0-{t_key}",
                    provenance={"source": t_source}
                )
                db.add(plan)
                db.flush()

                # CT1 Component: Units 1 and 2
                ct1 = AssessmentComponent(
                    plan_id=plan.id,
                    course_id=8,
                    code="CT1",
                    canonical_label=f"{t_name} Cycle Test 1",
                    student_label="CT1",
                    role="CYCLE_TEST",
                    sequence=1,
                    raw_labels=["CT1", "Cycle Test 1", "CT-1"]
                )
                db.add(ct1)
                db.flush()

                for u_num in [1, 2]:
                    if u_num in unit_map:
                        db.add(AssessmentCoverage(
                            assessment_component_id=ct1.id,
                            unit_id=unit_map[u_num].id,
                            coverage_type="IN_SCOPE"
                        ))

                # CT2 Component: Units 3 and 4
                ct2 = AssessmentComponent(
                    plan_id=plan.id,
                    course_id=8,
                    code="CT2",
                    canonical_label=f"{t_name} Cycle Test 2",
                    student_label="CT2",
                    role="CYCLE_TEST",
                    sequence=2,
                    raw_labels=["CT2", "Cycle Test 2", "CT-2"]
                )
                db.add(ct2)
                db.flush()

                for u_num in [3, 4]:
                    if u_num in unit_map:
                        db.add(AssessmentCoverage(
                            assessment_component_id=ct2.id,
                            unit_id=unit_map[u_num].id,
                            coverage_type="IN_SCOPE"
                        ))

                # ENDSEM Component: All units
                endsem = AssessmentComponent(
                    plan_id=plan.id,
                    course_id=8,
                    code="ENDSEM",
                    canonical_label=f"{t_name} End Semester Examination",
                    student_label="End Semester",
                    role="SUMMATIVE_EXAM",
                    sequence=3,
                    raw_labels=["ENDSEM", "End Semester", "University Exam", "DEGREE EXAMINATION"]
                )
                db.add(endsem)
                db.flush()

                for u_num in unit_map:
                    db.add(AssessmentCoverage(
                        assessment_component_id=endsem.id,
                        unit_id=unit_map[u_num].id,
                        coverage_type="IN_SCOPE"
                    ))

        # 3. Deterministically Link All 32 Historical Exams to their Exact Track
        all_exams = db.query(Exam).filter(Exam.course_id == 8).all()
        linked_counts = {k: 0 for k in created_tracks}

        for exam in all_exams:
            doc = db.query(Document).filter(Document.id == exam.document_id).first() if exam.document_id else None
            title = (doc.title or "") if doc else ""
            t_low = title.lower()

            assigned_track = None

            # Deterministic provenance rules
            if "german" in t_low or "skm_750i23120504120" in t_low or exam.id in [48, 49, 50, 51, 52, 127]:
                assigned_track = "german"
            elif "french" in t_low or "18leh103j" in t_low or exam.id in [46, 47, 124, 125, 126, 134]:
                assigned_track = "french"
            elif "spanish" in t_low or "18leh107" in t_low or exam.id in [88, 89, 90]:
                assigned_track = "spanish"
            elif "japanese" in t_low or "18leh105j" in t_low or exam.id in [57, 58, 59, 128, 129]:
                assigned_track = "japanese"
            elif "korean" in t_low or "18leh106j" in t_low or exam.id in [60, 61, 62, 63, 130, 131, 132, 133]:
                assigned_track = "korean"
            elif "chinese" in t_low or "18leh102j" in t_low or exam.id in [31, 32, 122, 123]:
                assigned_track = "chinese"

            if assigned_track and assigned_track in created_tracks:
                exam.track_id = created_tracks[assigned_track].id
                linked_counts[assigned_track] += 1

        # 4. Map Curriculum Mappings for Language Electives to Course 8
        curr_mappings = db.query(CurriculumMapping).all()
        mapped_count = 0
        for cm in curr_mappings:
            low = cm.subject_name.lower()
            if any(k in low for k in ['language', 'foreign', 'german', 'french', 'spanish', 'japanese', 'korean', 'chinese']):
                if "formal language" not in low:  # Exclude Formal Language and Automata (Computer Science course)
                    cm.course_id = 8
                    cm.status = "MATCHED"
                    mapped_count += 1

        db.commit()

        print("Course 8 (Foreign Languages) Multi-Track Seeding Completed!")
        for k, trk in created_tracks.items():
            print(f"  Track: {trk.track_name:10s} (ID {trk.id:2d}, code={trk.track_code}) -> {linked_counts[k]} exams linked")
        print(f"  Total Curriculum Mappings Matched: {mapped_count}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_foreign_language_tracks()
