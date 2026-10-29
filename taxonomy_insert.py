"""Insert validated course-specific vocabulary. Run locally with: 
.\.venv\Scripts\python.exe taxonomy_insert.py"""
import sys, os
sys.path.insert(0, '.')
from backend.core.database import SessionLocal
from backend.models.core import Course, Topic, Concept, Unit, Syllabus

db = SessionLocal()
try:
    # Verify DB reachable
    calc = db.query(Course).filter(Course.id == 1).first()
    chem = db.query(Course).filter(Course.id == 2).first()
    print("DB READ OK — Course 1:", calc.name, "Course 2:", chem.name)
    
    # Before counts
    topics_before = db.query(Topic).count()
    concepts_before = db.query(Concept).count()
    print("BEFORE — topics:", topics_before, "concepts:", concepts_before)
    
    # Idempotency: only insert if 0 topics exist (clean state)
    if topics_before > 0:
        print("Topics already exist — skipping insert (idempotent)")
    else:
        # Get syllabuses
        calc_syl = db.query(Syllabus).filter(Syllabus.course_id == calc.id).first()
        chem_syl = db.query(Syllabus).filter(Syllabus.course_id == chem.id).first()
        if not calc_syl:
            calc_syl = Syllabus(course_id=calc.id, version="current")
            db.add(calc_syl)
            db.flush()
        if not chem_syl:
            chem_syl = Syllabus(course_id=chem.id, version="current")
            db.add(chem_syl)
            db.flush()
        
        # Calculus vocabulary (from validated syllabus headings)
        calc_units = [
            ("Unit 1", "Matrices and Linear Algebra", ["Eigenvalues and Eigenvectors", "Matrix Operations", "Linear Systems"]),
            ("Unit 2", "Ordinary Differential Equations", ["First-Order ODE", "Second-Order ODE", "ODE Solutions"]),
            ("Unit 3", "Partial Differential Equations", ["PDE Classification", "Separation of Variables"]),
            ("Unit 4", "Laplace Transforms", ["Laplace Transform Tables", "Inverse Laplace Transforms"]),
            ("Unit 5", "Sequence and Series", ["Convergence Tests", "Power Series", "Fourier Series"]),
            ("Unit 6", "Functions of Several Variables", ["Partial Derivatives", "Gradient", "Directional Derivatives"]),
            ("Unit 7", "Multiple Integrals", ["Double Integrals", "Triple Integrals", "Change of Variables"]),
        ]
        
        if calc_syl:
            for num, name, topics in calc_units:
                # Create unit
                u = Unit(syllabus_id=calc_syl.id, name=f"{name}", number=int(num.split()[1]))
                db.add(u)
                db.flush()
                for tname in topics:
                    topic = Topic(name=tname, unit_id=u.id)
                    db.add(topic)
                    db.flush()
                    concept = Concept(canonical_name=tname, description=f"Course-specific topic from {name}: {tname}", status="CANONICAL")
                    db.add(concept)
                    db.flush()
        
        # Chemistry vocabulary (from Chemistry Unit 1-5 / Course docs)
        chem_units = [
            ("Unit 1", "Periodic Properties", ["Periodic Trends", "Atomic Radius", "Ionization Energy"]),
            ("Unit 2", "Chemical Equilibria", ["Equilibrium Constant", "Le Chatelier Principle", "Free Energy in Equilibria"]),
            ("Unit 3", "Stereo Chemistry And Organic Reactions", ["Stereoisomers", "Organic Reaction Mechanisms"]),
            ("Unit 4", "Polymers", ["Polymer Types", "Polymerization Processes"]),
            ("Unit 5", "Advanced Engineering Materials", ["Material Properties", "Corrosion Resistance"]),
        ]
        if chem_syl:
            for num, name, topics in chem_units:
                u = Unit(syllabus_id=chem_syl.id, name=f"{name}", number=int(num.split()[1]))
                db.add(u)
                db.flush()
                for tname in topics:
                    topic = Topic(name=tname, unit_id=u.id)
                    db.add(topic)
                    db.flush()
                    concept = Concept(canonical_name=tname, description=f"Course-specific topic from {name}: {tname}", status="CANONICAL")
                    db.add(concept)
                    db.flush()
        
        db.commit()
        print("INSERT COMMITTED")
    
    # After counts
    topics_after = db.query(Topic).count()
    concepts_after = db.query(Concept).count()
    print("AFTER — topics:", topics_after, "concepts:", concepts_after)
    
    # List inserted by course
    from backend.models.core import Unit, Syllabus
    calc_topics = db.query(Topic).join(Unit).join(Syllabus).filter(Syllabus.course_id == 1).all()
    chem_topics = db.query(Topic).join(Unit).join(Syllabus).filter(Syllabus.course_id == 2).all()
    print("Calculated inserted — Calculus topics:", len(calc_topics), "Chemistry topics:", len(chem_topics))
    
    for t in calc_topics[:3]:
        print("  Calc topic:", t.name, "course via unit/syllabus")
    for t in chem_topics[:3]:
        print("  Chem topic:", t.name, "course via unit/syllabus")
    
    # Cross-subject check: confirm no chemistry topic appears in calc unit
    calc_topic_names = {t.name for t in calc_topics}
    chem_topic_names = {t.name for t in chem_topics}
    overlap = calc_topic_names & chem_topic_names
    print("CROSS-SUBJECT OVERLAP:", "NONE" if not overlap else overlap)
    
except Exception as e:
    db.rollback()
    print("ERROR:", type(e).__name__, str(e)[:200])
finally:
    db.close()
