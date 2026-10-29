"""
Generate declarative JSON taxonomy definitions for:
- Course 19: EM Physics (21PYB101J)
- Course 20: Physics Mechanics (21PYB104J)
- Course 8:  Foreign Languages (6 tracks: German, French, Spanish, Japanese, Korean, Chinese)

All definitions match exact Unit IDs and Topic IDs stored in production_corpus.db.
"""

import json
import os
import sys
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from typing import Dict, List, Any
from backend.core.database import SessionLocal
from backend.models.core import Course, CourseTrack, Syllabus, Unit, Topic


DEFS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "backend", "services", "taxonomy_registry", "definitions"
)


def generate_emphy_definition(db):
    syl = db.query(Syllabus).filter(Syllabus.course_id == 19, Syllabus.version == "2021").first()
    units = []
    
    # Topic rule annotations for EM Physics
    topic_keywords = {
        "Vector Calculus and Del Operator": {
            "strong": ["del operator", "divergence of a vector", "curl of a vector", "gradient of a scalar", "laplacian operator", "directional derivative"],
            "specific": ["del operator", "vector field", "conservative field", "curl", "divergence"],
            "negative": ["dielectric", "maxwell", "ferromagnetic", "schrodinger", "laser"],
            "hints": ["vector calculus", "field theory"]
        },
        "Electrostatics and Charge Distributions": {
            "strong": ["coulomb's law", "electric field intensity", "charge distribution", "volume charge density", "surface charge density", "line charge density"],
            "specific": ["coulomb", "charge density", "electric flux density"],
            "negative": ["magnetic", "optical fiber", "ferrite"],
            "hints": ["electrostatics"]
        },
        "Gauss's Law and Electrostatic Potentials": {
            "strong": ["gauss's law", "gauss theorem", "electrostatic potential", "poisson's equation", "laplace's equation", "equipotential surface"],
            "specific": ["gauss's law", "poisson equation", "laplace equation", "electrostatic potential"],
            "negative": ["magnetic", "schrodinger", "quantum"],
            "hints": ["potential theory", "electrostatics"]
        },
        "Electrodynamics and Magnetism": {
            "strong": ["biot-savart law", "ampere's circuital law", "lorentz force", "magnetic vector potential", "faraday's law of electromagnetic induction", "lenz's law"],
            "specific": ["biot-savart", "ampere's law", "lorentz force", "magnetic induction"],
            "negative": ["schrodinger", "laser", "blackbody"],
            "hints": ["magnetostatics", "electrodynamics"]
        },
        "Maxwell's Equations and EM Waves": {
            "strong": ["maxwell's equations", "displacement current", "poynting vector", "electromagnetic wave equation", "poynting theorem", "intrinsic impedance", "wave propagation in free space"],
            "specific": ["maxwell's equation", "displacement current", "poynting vector", "em wave equation"],
            "negative": ["quantum well", "diffraction grating"],
            "hints": ["electromagnetics", "wave propagation"]
        },
        "Dielectric Materials and Polarization": {
            "strong": ["dielectric polarization", "dielectric constant", "electric susceptibility", "clausius-mossotti relation", "electronic polarizability", "ionic polarizability", "orientational polarizability", "internal field in dielectrics", "lorentz field"],
            "specific": ["dielectric", "polarizability", "clausius-mossotti", "internal field"],
            "negative": ["magnetic hysteresis", "fiber optic"],
            "hints": ["dielectrics", "solid state physics"]
        },
        "Magnetic Properties and Parameters": {
            "strong": ["magnetic susceptibility", "magnetic permeability", "bohr magneton", "diamagnetism", "paramagnetism", "magnetic dipole moment"],
            "specific": ["susceptibility", "permeability", "bohr magneton", "diamagnetic", "paramagnetic"],
            "negative": ["dielectric constant", "schrodinger"],
            "hints": ["magnetism", "materials"]
        },
        "Ferromagnetism and Domain Theory": {
            "strong": ["ferromagnetism", "weiss domain theory", "hysteresis loop", "b-h curve", "curie temperature", "curie-weiss law", "remanence", "coercivity", "domain wall"],
            "specific": ["ferromagnetism", "domain theory", "hysteresis", "coercivity", "remanence", "curie temperature"],
            "negative": ["dielectric", "photoelectric"],
            "hints": ["ferromagnetism", "magnetic materials"]
        },
        "Soft and Hard Magnetic Materials": {
            "strong": ["soft magnetic materials", "hard magnetic materials", "permanent magnet", "transformer core material", "alnico", "eddy current losses"],
            "specific": ["soft magnetic", "hard magnetic", "alnico", "transformer core"],
            "negative": ["quantum", "laser"],
            "hints": ["magnetic applications"]
        },
        "Ferrites and Spinel Structures": {
            "strong": ["ferrites", "ferrimagnetism", "spinel structure", "inverse spinel", "garnets", "ferrite applications"],
            "specific": ["ferrites", "ferrimagnetic", "spinel structure", "inverse spinel"],
            "negative": ["optical fiber", "semiconductor laser"],
            "hints": ["ferrites", "ceramic magnets"]
        },
        "Spintronics and Magnetoresistance": {
            "strong": ["giant magnetoresistance", "gmr", "spintronics", "spin valve", "tunnel magnetoresistance", "tmr", "spin polarization"],
            "specific": ["spintronics", "magnetoresistance", "giant magnetoresistance", "spin valve"],
            "negative": ["diffraction", "blackbody"],
            "hints": ["spintronics", "nanotechnology"]
        },
        "Multiferroic Materials": {
            "strong": ["multiferroic", "magnetoelectric coupling", "ferroelectric and ferromagnetic", "magnetoelectric effect"],
            "specific": ["multiferroic", "magnetoelectric"],
            "negative": ["fresnel", "young's double slit"],
            "hints": ["smart materials"]
        },
        "Inadequacies of Classical Mechanics and Blackbody Radiation": {
            "strong": ["blackbody radiation", "planck's radiation law", "planck's quantum hypothesis", "wien's displacement law", "rayleigh-jeans law", "ultraviolet catastrophe"],
            "specific": ["blackbody", "planck radiation", "wien displacement", "rayleigh-jeans", "ultraviolet catastrophe"],
            "negative": ["fiber optic", "clausius-mossotti"],
            "hints": ["quantum origin", "thermal radiation"]
        },
        "Photoelectric and Compton Effects": {
            "strong": ["photoelectric effect", "work function", "stopping potential", "einstein photoelectric equation", "compton effect", "compton shift", "compton scattering", "compton wavelength"],
            "specific": ["photoelectric", "compton effect", "compton shift", "stopping potential", "work function"],
            "negative": ["magnetic domain", "truss"],
            "hints": ["quantum physics", "photon interaction"]
        },
        "Matter Waves and Uncertainty Principle": {
            "strong": ["de broglie hypothesis", "de broglie wavelength", "matter waves", "heisenberg's uncertainty principle", "davisson and germer experiment", "group velocity and phase velocity"],
            "specific": ["de broglie", "matter waves", "uncertainty principle", "davisson-germer", "group velocity"],
            "negative": ["ferrite", "poisson ratio"],
            "hints": ["wave-particle duality"]
        },
        "Wave Function and Postulates": {
            "strong": ["wave function", "physical significance of wave function", "born's interpretation", "normalization of wave function", "probability density", "postulates of quantum mechanics", "orthogonality of wave functions"],
            "specific": ["wave function", "born interpretation", "normalization condition", "probability density"],
            "negative": ["maxwell's equation", "laser diode"],
            "hints": ["quantum mechanics"]
        },
        "Schrödinger Wave Equations": {
            "strong": ["schrodinger wave equation", "time independent schrodinger equation", "time dependent schrodinger equation", "schrodinger equation", "eigenvalue and eigenfunction", "hamiltonian operator"],
            "specific": ["schrodinger", "time independent schrodinger", "eigenvalue equation", "hamiltonian operator"],
            "negative": ["classical mechanics", "snell's law"],
            "hints": ["schrodinger equation", "wave mechanics"]
        },
        "Quantum Wells and Potential Barriers": {
            "strong": ["particle in a one-dimensional box", "particle in a box", "infinite potential well", "quantum tunneling", "barrier penetration", "transmission coefficient", "step potential"],
            "specific": ["particle in a box", "potential well", "quantum tunneling", "barrier penetration"],
            "negative": ["optical fiber", "bending of beams"],
            "hints": ["quantum bound states", "tunneling"]
        },
        "Harmonic Oscillator and Hydrogen Atom": {
            "strong": ["quantum harmonic oscillator", "zero-point energy", "hydrogen atom in quantum mechanics", "radial wave function", "principal quantum number"],
            "specific": ["quantum harmonic oscillator", "zero-point energy", "hydrogen atom"],
            "negative": ["coulomb friction", "diffraction grating"],
            "hints": ["quantum systems"]
        },
        "Superposition and Interference of Light": {
            "strong": ["interference of light", "superposition principle", "young's double slit experiment", "coherent sources", "interference in thin films", "newton's rings", "wedge shaped thin film", "path difference and phase difference"],
            "specific": ["interference", "newton's rings", "thin films", "coherent sources", "fringe width"],
            "negative": ["polarization", "schrodinger", "compton"],
            "hints": ["wave optics", "interference"]
        },
        "Fresnel and Fraunhofer Diffraction": {
            "strong": ["diffraction of light", "fresnel diffraction", "fraunhofer diffraction", "fresnel half period zones", "zone plate", "distinction between fresnel and fraunhofer"],
            "specific": ["fresnel diffraction", "fraunhofer diffraction", "half period zones", "zone plate"],
            "negative": ["thin film interference", "population inversion"],
            "hints": ["diffraction theory"]
        },
        "Fraunhofer Slit Diffraction": {
            "strong": ["fraunhofer diffraction at single slit", "single slit diffraction", "diffraction at double slit", "diffraction pattern central maximum", "minima and maxima in diffraction"],
            "specific": ["single slit", "double slit diffraction", "central maximum", "diffraction minima"],
            "negative": ["quantum well", "fiber optic"],
            "hints": ["slit diffraction"]
        },
        "Plane Diffraction Grating": {
            "strong": ["plane transmission diffraction grating", "diffraction grating", "grating equation", "resolving power of grating", "dispersive power of grating", "grating spectra", "absent spectra"],
            "specific": ["diffraction grating", "grating equation", "resolving power", "dispersive power"],
            "negative": ["nicol prism", "blackbody"],
            "hints": ["diffraction grating", "spectroscopy"]
        },
        "Polarization of Light": {
            "strong": ["polarization of light", "brewster's law", "malus's law", "linearly polarized light", "circularly polarized light", "elliptically polarized light", "polarization by reflection"],
            "specific": ["polarization", "brewster's law", "malus's law", "linearly polarized"],
            "negative": ["laser pumping", "particle in a box"],
            "hints": ["polarization", "electromagnetic optics"]
        },
        "Double Refraction and Polarizing Devices": {
            "strong": ["double refraction", "birefringence", "nicol prism", "quarter wave plate", "half wave plate", "ordinary ray and extraordinary ray", "optical activity"],
            "specific": ["double refraction", "birefringence", "nicol prism", "quarter wave plate", "half wave plate"],
            "negative": ["grating", "ferrite"],
            "hints": ["crystal optics", "polarizing devices"]
        },
        "Laser Principles and Einstein Coefficients": {
            "strong": ["einstein's coefficients", "einstein a and b coefficients", "stimulated emission", "spontaneous emission", "stimulated absorption", "laser principles", "properties of laser beam", "spatial coherence", "temporal coherence"],
            "specific": ["einstein coefficients", "stimulated emission", "spontaneous emission", "coherence of laser"],
            "negative": ["optical fiber cable", "compton effect"],
            "hints": ["laser physics"]
        },
        "Population Inversion and Pumping Schemes": {
            "strong": ["population inversion", "optical pumping", "metastable state", "three level laser system", "four level laser system", "resonant cavity", "active medium"],
            "specific": ["population inversion", "optical pumping", "metastable state", "three level laser", "four level laser"],
            "negative": ["polarization", "newton rings"],
            "hints": ["laser action"]
        },
        "Gas and Solid State Lasers": {
            "strong": ["he-ne laser", "helium neon laser", "ruby laser", "nd:yag laser", "gas laser", "solid state laser", "construction of he-ne laser"],
            "specific": ["he-ne laser", "helium neon", "ruby laser", "nd:yag laser"],
            "negative": ["semiconductor laser", "optical fiber"],
            "hints": ["laser types", "engineering lasers"]
        },
        "Semiconductor Diode Lasers": {
            "strong": ["semiconductor diode laser", "gaas laser", "homojunction laser", "heterojunction laser", "semiconductor laser injection"],
            "specific": ["semiconductor laser", "gaas laser", "diode laser", "heterojunction laser"],
            "negative": ["he-ne laser", "ruby laser"],
            "hints": ["semiconductor optoelectronics"]
        },
        "Optical Fiber Transmission": {
            "strong": ["total internal reflection", "numerical aperture of fiber", "acceptance angle", "optical fiber structure", "core and cladding refractive index", "fractional refractive index change"],
            "specific": ["optical fiber", "numerical aperture", "acceptance angle", "total internal reflection", "core and cladding"],
            "negative": ["schrodinger", "ferrite"],
            "hints": ["fiber optics", "light guiding"]
        },
        "Fiber Classification and Losses": {
            "strong": ["step index fiber", "graded index fiber", "single mode fiber", "multimode fiber", "fiber attenuation", "fiber losses", "intermodal dispersion", "material dispersion", "scattering losses"],
            "specific": ["step index", "graded index", "single mode", "multimode fiber", "fiber attenuation", "dispersion in fiber"],
            "negative": ["laser pumping", "b-h curve"],
            "hints": ["fiber types", "transmission losses"]
        },
        "Fiber Optic Communication and Sensors": {
            "strong": ["optical fiber communication system", "fiber optic sensors", "displacement sensor", "temperature fiber sensor", "endoscopy in fiber optics", "optical sources and detectors"],
            "specific": ["fiber optic communication", "fiber sensor", "optical detector", "endoscopy"],
            "negative": ["schrodinger", "diffraction grating"],
            "hints": ["fiber optic applications"]
        }
    }

    for u in sorted(syl.units, key=lambda x: x.number):
        u_dict = {
            "id": u.id,
            "number": u.number,
            "name": u.name,
            "topics": []
        }
        for t in u.topics:
            kw = topic_keywords.get(t.name, {
                "strong": [t.name.lower()],
                "specific": [w.lower() for w in t.name.split() if len(w) > 4],
                "negative": [],
                "hints": []
            })
            u_dict["topics"].append({
                "id": t.id,
                "name": t.name,
                "canonical_name": t.name,
                "aliases": [],
                "strong_phrases": kw["strong"],
                "specific_keywords": kw["specific"],
                "negative_guards": kw["negative"],
                "context_hints": kw["hints"]
            })
        units.append(u_dict)

    entry = {
        "schema_version": "1.0",
        "taxonomy_version": "1.0.0",
        "course": {
            "id": 19,
            "name": "Physics: Electromagnetic Theory, Quantum Mechanics, Waves and Optics",
            "canonical_code": "21PYB101J",
            "code": "SEM1-EMPHY",
            "regulation_year": 2021,
            "department": "Department of Physics and Nanotechnology"
        },
        "provenance": {
            "source_document": "SRMIST B.Tech Regulation 2021 Curriculum & Syllabus - 21PYB101J",
            "regulation": "2021",
            "approved_by": "Academic Council SRMIST",
            "notes": "Authoritative 5-unit syllabus covering Electromagnetism & Dielectrics, Magnetic Materials, Quantum Mechanics, Wave Optics, and Lasers & Fiber Optics."
        },
        "units": units
    }

    out_path = os.path.join(DEFS_DIR, "course_19_emphy.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)
    print(f"Generated {out_path} with {len(units)} units and {sum(len(u['topics']) for u in units)} topics.")


def generate_phymech_definition(db):
    syl = db.query(Syllabus).filter(Syllabus.course_id == 20, Syllabus.version == "2021").first()
    units = []

    topic_keywords = {
        "Fundamental Forces in Nature and Kinematics": {
            "strong": ["fundamental forces in nature", "gravitational force", "electromagnetic force", "strong nuclear force", "weak nuclear force", "particle kinematics", "position velocity acceleration vector"],
            "specific": ["fundamental forces", "gravitational force", "kinematics", "velocity vector", "acceleration vector"],
            "negative": ["beam bending", "mohr's circle"],
            "hints": ["mechanics", "kinematics"]
        },
        "Frames of Reference": {
            "strong": ["inertial frame of reference", "non-inertial frame", "fictitious force", "pseudo force", "coriolis force", "centrifugal force", "coriolis acceleration"],
            "specific": ["inertial frame", "non-inertial", "coriolis force", "centrifugal force", "fictitious force"],
            "negative": ["truss", "strain gauge"],
            "hints": ["reference frames", "dynamics"]
        },
        "Simple Harmonic Motion and Conservation of Energy": {
            "strong": ["simple harmonic motion", "shm equation", "spring mass system", "simple pendulum", "energy in simple harmonic motion", "conservation of mechanical energy"],
            "specific": ["simple harmonic motion", "shm", "spring mass", "harmonic oscillation"],
            "negative": ["damped oscillation", "forced oscillation", "torsion"],
            "hints": ["oscillations", "energy"]
        },
        "Damped Harmonic Oscillators": {
            "strong": ["damped harmonic oscillator", "damping force", "damping coefficient", "quality factor", "q factor of oscillator", "logarithmic decrement", "underdamped critically damped overdamped"],
            "specific": ["damped harmonic", "damping coefficient", "logarithmic decrement", "quality factor"],
            "negative": ["forced harmonic", "resonance", "bending of beams"],
            "hints": ["damped motion"]
        },
        "Viscous Dampers and Energy Dissipation": {
            "strong": ["viscous damper", "dashpot", "energy dissipation rate", "relaxation time in damping", "decay of amplitude"],
            "specific": ["viscous damper", "dashpot", "energy dissipation", "relaxation time"],
            "negative": ["truss", "mohr circle"],
            "hints": ["damping systems"]
        },
        "Forced Harmonic Oscillators and Resonance": {
            "strong": ["forced harmonic oscillator", "driven oscillator", "mechanical resonance", "amplitude resonance", "velocity resonance", "sharpness of resonance", "resonant frequency"],
            "specific": ["forced harmonic", "mechanical resonance", "amplitude resonance", "driven oscillator", "resonant frequency"],
            "negative": ["free oscillation", "dry friction"],
            "hints": ["resonance", "forced vibration"]
        },
        "Particles and Rigid Bodies": {
            "strong": ["center of mass of system", "system of particles", "rigid body motion", "internal and external forces on rigid body"],
            "specific": ["center of mass", "rigid body", "system of particles"],
            "negative": ["stress tensor", "torsion equation"],
            "hints": ["rigid bodies"]
        },
        "Rotation About a Fixed Axis": {
            "strong": ["rotation about fixed axis", "moment of inertia of rigid body", "radius of gyration", "parallel axis theorem", "perpendicular axis theorem", "angular momentum", "torque and angular acceleration"],
            "specific": ["moment of inertia", "radius of gyration", "parallel axis theorem", "perpendicular axis theorem", "angular momentum"],
            "negative": ["strain gauge", "viscous damper"],
            "hints": ["rotational dynamics"]
        },
        "Kinetic Energy of Rigid Bodies": {
            "strong": ["rotational kinetic energy", "kinetic energy of rolling motion", "rolling without slipping", "work energy theorem for rotation", "angular impulse"],
            "specific": ["rotational kinetic energy", "rolling motion", "rolling without slipping", "angular impulse"],
            "negative": ["roof truss", "mohr's circle"],
            "hints": ["rotational energy"]
        },
        "Euler's Equations of Motion": {
            "strong": ["euler's equations of motion", "principal axes of inertia", "principal moments of inertia", "rotational motion in body coordinates"],
            "specific": ["euler's equations", "principal axes", "principal moments of inertia"],
            "negative": ["simple pendulum", "hooke's law"],
            "hints": ["3d dynamics", "advanced mechanics"]
        },
        "Gyroscopic Precession and Symmetrical Top": {
            "strong": ["gyroscopic precession", "precessional angular velocity", "gyroscopic couple", "symmetrical top", "gyroscope motion", "nutation"],
            "specific": ["gyroscopic", "precession", "gyroscopic couple", "symmetrical top"],
            "negative": ["flexural formula", "friction"],
            "hints": ["gyroscopes"]
        },
        "Conical Pendulum": {
            "strong": ["conical pendulum", "time period of conical pendulum", "angle of inclination of pendulum", "string tension in conical pendulum"],
            "specific": ["conical pendulum", "semi-vertical angle"],
            "negative": ["compound pendulum", "truss"],
            "hints": ["pendulum motion"]
        },
        "Rigid Bodies in Static Equilibrium": {
            "strong": ["static equilibrium of rigid body", "conditions of equilibrium", "coplanar force equilibrium", "sum of forces zero sum of moments zero", "equations of equilibrium"],
            "specific": ["static equilibrium", "equilibrium of rigid bodies", "equilibrium conditions"],
            "negative": ["dynamics", "forced oscillation"],
            "hints": ["statics"]
        },
        "Free Body Diagrams and Force Systems": {
            "strong": ["free body diagram", "fbd of rigid body", "concurrent forces", "coplanar force system", "moment of a force", "varignon's theorem", "couple and moment"],
            "specific": ["free body diagram", "fbd", "varignon's theorem", "force system"],
            "negative": ["quantum", "stress-strain"],
            "hints": ["force resolution", "statics"]
        },
        "Supports and Reaction Forces": {
            "strong": ["support reactions", "roller support", "hinged support", "pinned support", "fixed support", "reaction at supports", "statically determinate beam"],
            "specific": ["support reactions", "roller support", "pinned support", "fixed support"],
            "negative": ["coriolis", "resonance"],
            "hints": ["beam supports", "reactions"]
        },
        "Bridge and Roof Trusses": {
            "strong": ["plane truss", "method of joints", "method of sections", "zero force members in truss", "bridge truss", "roof truss", "warren truss", "pratt truss"],
            "specific": ["method of joints", "method of sections", "truss", "zero force member", "roof truss"],
            "negative": ["pure bending", "torsion"],
            "hints": ["structural mechanics", "trusses"]
        },
        "Theory of Dry Friction": {
            "strong": ["coulomb's theory of dry friction", "dry friction", "coefficient of static friction", "coefficient of kinetic friction", "angle of friction", "angle of repose", "cone of friction", "wedge friction", "ladder friction"],
            "specific": ["dry friction", "coefficient of friction", "angle of friction", "angle of repose", "wedge friction", "ladder friction"],
            "negative": ["viscous damper", "mohr's circle"],
            "hints": ["friction", "statics"]
        },
        "State of Stress at a Point": {
            "strong": ["state of stress at a point", "stress tensor", "normal stress and shear stress", "traction vector", "cauchy stress formula", "complementary shear stress"],
            "specific": ["stress tensor", "state of stress", "normal stress", "shear stress", "traction vector"],
            "negative": ["conical pendulum", "gyroscope"],
            "hints": ["solid mechanics", "stress analysis"]
        },
        "Generalized Hooke's Law and Thermal Strains": {
            "strong": ["generalized hooke's law", "young's modulus", "poisson's ratio", "modulus of rigidity", "bulk modulus", "relations between elastic constants", "thermal stress", "thermal strain"],
            "specific": ["hooke's law", "poisson's ratio", "young's modulus", "thermal stress", "elastic constants"],
            "negative": ["method of joints", "coriolis"],
            "hints": ["elasticity", "materials"]
        },
        "Plane State of Stress and Principal Stresses": {
            "strong": ["plane state of stress", "plane stress", "principal stresses", "principal planes", "maximum in-plane shear stress", "transformation of plane stress"],
            "specific": ["plane stress", "principal stresses", "principal planes", "maximum shear stress"],
            "negative": ["dry friction", "resonance"],
            "hints": ["stress transformation"]
        },
        "Mohr's Circle for Planar Stress": {
            "strong": ["mohr's circle for planar stress", "mohr's circle", "construction of mohr's circle", "center and radius of mohr's circle", "principal stresses from mohr's circle"],
            "specific": ["mohr's circle", "mohr circle"],
            "negative": ["euler's equation", "viscous damping"],
            "hints": ["graphical stress analysis"]
        },
        "Material Failure Mechanisms": {
            "strong": ["theories of failure", "maximum principal stress theory", "rankine theory", "maximum shear stress theory", "tresca criterion", "maximum distortion energy theory", "von mises criterion", "yield criterion"],
            "specific": ["tresca criterion", "von mises criterion", "rankine theory", "theories of failure", "yield criterion"],
            "negative": ["truss analysis", "simple harmonic"],
            "hints": ["failure criteria", "mechanics of materials"]
        },
        "Electrical Resistance Strain Gauges": {
            "strong": ["electrical resistance strain gauge", "strain gauge", "gauge factor", "strain rosette", "wheatstone bridge strain measurement", "quarter bridge half bridge"],
            "specific": ["strain gauge", "gauge factor", "strain rosette", "wheatstone bridge strain"],
            "negative": ["moment of inertia", "gyroscopic"],
            "hints": ["experimental stress analysis"]
        },
        "Pure Bending of Beams": {
            "strong": ["pure bending of beams", "simple bending", "neutral axis of beam", "radius of curvature in bending", "assumptions in pure bending", "neutral surface"],
            "specific": ["pure bending", "neutral axis", "radius of curvature", "bending of beams"],
            "negative": ["torsion of shafts", "free body diagram"],
            "hints": ["beam theory", "bending"]
        },
        "Flexural Formula for Bending": {
            "strong": ["flexural formula", "bending equation", "m/i = sigma/y = e/r", "section modulus", "flexural rigidity", "bending stress distribution"],
            "specific": ["flexural formula", "bending equation", "section modulus", "flexural rigidity", "bending stress"],
            "negative": ["torsion equation", "coriolis force"],
            "hints": ["beam stress calculation"]
        },
        "Torsion of Circular Shafts": {
            "strong": ["torsion of circular shafts", "torsional deformation", "angle of twist", "shear stress in circular shaft", "polar moment of inertia of shaft"],
            "specific": ["torsion of shafts", "angle of twist", "polar moment of inertia", "circular shaft"],
            "negative": ["bending equation", "roof truss"],
            "hints": ["torsion", "shafts"]
        },
        "Torsion Equation": {
            "strong": ["torsion equation", "t/j = tau/r = c*theta/l", "torsional rigidity", "power transmitted by shaft", "torque transmission"],
            "specific": ["torsion equation", "torsional rigidity", "power transmitted by shaft"],
            "negative": ["flexural formula", "mohr circle"],
            "hints": ["torsion formula"]
        },
        "Twisting Moment Diagrams": {
            "strong": ["twisting moment diagram", "tmd", "shaft subjected to multiple torques", "internal twisting moment"],
            "specific": ["twisting moment diagram", "tmd", "internal twisting moment"],
            "negative": ["bending moment diagram", "strain rosette"],
            "hints": ["torque diagrams"]
        },
        "Strain Energy and Resilience": {
            "strong": ["strain energy", "modulus of resilience", "proof resilience", "strain energy in simple tension", "strain energy in bending", "strain energy in torsion", "castigliano's theorem"],
            "specific": ["strain energy", "resilience", "proof resilience", "modulus of resilience"],
            "negative": ["coriolis force", "gyroscopic precession"],
            "hints": ["energy methods", "strain energy"]
        }
    }

    for u in sorted(syl.units, key=lambda x: x.number):
        u_dict = {
            "id": u.id,
            "number": u.number,
            "name": u.name,
            "topics": []
        }
        for t in u.topics:
            kw = topic_keywords.get(t.name, {
                "strong": [t.name.lower()],
                "specific": [w.lower() for w in t.name.split() if len(w) > 4],
                "negative": [],
                "hints": []
            })
            u_dict["topics"].append({
                "id": t.id,
                "name": t.name,
                "canonical_name": t.name,
                "aliases": [],
                "strong_phrases": kw["strong"],
                "specific_keywords": kw["specific"],
                "negative_guards": kw["negative"],
                "context_hints": kw["hints"]
            })
        units.append(u_dict)

    entry = {
        "schema_version": "1.0",
        "taxonomy_version": "1.0.0",
        "course": {
            "id": 20,
            "name": "Physics: Mechanics",
            "canonical_code": "21PYB104J",
            "code": "SEM1-PHYMECH",
            "regulation_year": 2021,
            "department": "Department of Physics and Nanotechnology"
        },
        "provenance": {
            "source_document": "SRMIST B.Tech Regulation 2021 Curriculum & Syllabus - 21PYB104J Physics: Mechanics",
            "regulation": "2021",
            "approved_by": "Academic Council SRMIST",
            "notes": "Authoritative 5-unit syllabus covering Oscillations & Dynamics, Rigid Body Dynamics, Statics & Structural Mechanics, Stress-Strain & Failure, and Beams & Torsion."
        },
        "units": units
    }

    out_path = os.path.join(DEFS_DIR, "course_20_phymech.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)
    print(f"Generated {out_path} with {len(units)} units and {sum(len(u['topics']) for u in units)} topics.")


def generate_foreign_languages_definition(db):
    tracks = db.query(CourseTrack).filter(CourseTrack.course_id == 8).order_by(CourseTrack.id).all()
    track_defs = []
    units = []

    # Language-specific keyword dictionaries
    # German (Track 1)
    german_rules = {
        "Begrüßung, Alphabet und Aussprache": {
            "strong": ["guten morgen", "guten tag", "guten abend", "auf wiedersehen", "wie geht es ihnen", "buchstabieren", "alphabet"],
            "specific": ["guten morgen", "guten tag", "auf wiedersehen", "tshuess", "alphabet", "begrussung"],
            "negative": [], "hints": ["german basics"]
        },
        "Zahlen von 0 bis 100 und Grundrechenarten": {
            "strong": ["zahlen", "eins zwei drei", "null bis", "grundrechenarten", "plus minus mal geteilt"],
            "specific": ["zahlen", "eins", "zwei", "drei", "zwanzig", "hundert"],
            "negative": [], "hints": ["numbers"]
        },
        "Personalpronomen und Konjugation im Präsens (sein, haben, heißen)": {
            "strong": ["ich du er sie es", "personalpronomen", "konjugation", "sein haben", "ich bin du bist", "ich heisse"],
            "specific": ["personalpronomen", "konjugation", "prasens", "haben", "heissen"],
            "negative": [], "hints": ["german grammar"]
        },
        "Sich vorstellen und andere Personen vorstellen": {
            "strong": ["wie heissen sie", "ich heisse", "wer ist das", "das ist mein freund", "woher kommen sie", "ich komme aus"],
            "specific": ["vorstellen", "wie heisst du", "woher kommen", "mein name ist"],
            "negative": [], "hints": ["introductions"]
        },
        "Höflichkeitsformen (Sie vs. du)": {
            "strong": ["hoeflichkeitsform", "sie vs du", "duzen oder siezen", "formelle anrede"],
            "specific": ["duzen", "siezen", "anrede"],
            "negative": [], "hints": ["politeness"]
        },
        "Länder, Nationalitäten und Sprachen": {
            "strong": ["deutschland", "osterreich", "schweiz", "welche sprachen sprechen sie", "nationalitat", "deutsch japanisch chinesisch"],
            "specific": ["deutschland", "osterreich", "spricht man", "nationalitat", "sprachen"],
            "negative": [], "hints": ["countries and languages"]
        },
        "W-Fragen und Ja/Nein-Fragen (Satzbau)": {
            "strong": ["w-fragen", "wer wie was wo", "ja nein fragen", "satzbau", "inversionsfrage"],
            "specific": ["w-frage", "frageworter", "satzbau", "inversion"],
            "negative": [], "hints": ["questions"]
        },
        "Bestimmte und unbestimmte Artikel (der, die, das / ein, eine)": {
            "strong": ["bestimmter artikel", "unbestimmter artikel", "der die das", "ein eine ein"],
            "specific": ["artikel", "der die das", "bestimmte artikel", "unbestimmte"],
            "negative": [], "hints": ["articles"]
        },
        "Negation mit 'nicht' und 'kein'": {
            "strong": ["negation mit nicht", "negation mit kein", "kein keine", "nicht oder kein"],
            "specific": ["negation", "nicht", "kein", "keine"],
            "negative": [], "hints": ["negation"]
        },
        "Familienmitglieder und Verwandtschaftsverhältnisse": {
            "strong": ["meine familie", "vater mutter eltern", "bruder schwester", "sohn tochter", "grossvater grossmutter"],
            "specific": ["familie", "eltern", "bruder", "schwester", "vater", "mutter"],
            "negative": [], "hints": ["family"]
        },
        "Possessivpronomen im Nominativ (mein, dein, sein, ihr)": {
            "strong": ["possessivpronomen", "mein dein sein", "ihr unser euer", "possessivartikel"],
            "specific": ["possessivpronomen", "possessivartikel", "mein", "dein"],
            "negative": [], "hints": ["possessives"]
        },
        "Uhrzeiten (offiziell und umgangssprachlich)": {
            "strong": ["wie spat ist es", "wie viel uhr ist es", "uhrzeit", "viertel vor", "viertel nach", "halb"],
            "specific": ["uhrzeit", "wie spat", "wieviel uhr", "viertel"],
            "negative": [], "hints": ["time"]
        },
        "Wochentage, Monate und Jahreszeiten": {
            "strong": ["montag dienstag mittwoch", "wochentage", "januar februar marz", "monate des jahres", "fruhling sommer herbst winter", "jahreszeiten"],
            "specific": ["wochentage", "monate", "jahreszeiten", "der herbst", "der sommer", "der fruhling"],
            "negative": [], "hints": ["calendar"]
        },
        "Tagesablauf und trennbare Verben im Präsens": {
            "strong": ["tagesablauf", "trennbare verben", "aufstehen", "fernsehen", "einkaufen", "anfangen"],
            "specific": ["tagesablauf", "trennbare verben", "aufstehen", "einkaufen"],
            "negative": [], "hints": ["daily routine"]
        },
        "Akkusativ: Bestimmte, unbestimmte und Negativartikel": {
            "strong": ["akkusativ", "den die das", "einen eine ein", "keinen keine", "akkusativobjekt"],
            "specific": ["akkusativ", "akkusativobjekt", "den", "einen", "keinen"],
            "negative": ["dativ"], "hints": ["accusative"]
        },
        "Verben mit Akkusativergänzung": {
            "strong": ["verben mit akkusativ", "brauchen", "haben", "kaufen", "suchen", "finden"],
            "specific": ["akkusativerganzung", "verben mit akkusativ"],
            "negative": [], "hints": ["verbs"]
        },
        "Essen, Trinken und Mahlzeiten": {
            "strong": ["essen und trinken", "fruhstuck", "mittagessen", "abendessen", "was isst du", "was trinkst du"],
            "specific": ["essen", "trinken", "mahlzeiten", "fruhstuck", "lebensmittel"],
            "negative": [], "hints": ["food and drink"]
        },
        "Im Restaurant bestellen und bezahlen": {
            "strong": ["im restaurant", "ich mochte bestellen", "die rechnung bitte", "zusammen oder getrennt", "kellner"],
            "specific": ["restaurant", "bestellen", "rechnung bitte", "kellner"],
            "negative": [], "hints": ["dining"]
        },
        "Modalverben im Präsens (können, müssen, wollen, dürfen, möchten)": {
            "strong": ["modalverben", "konnen mussen wollen", "durfen mochten", "ich kann du kannst", "ich muss"],
            "specific": ["modalverben", "konnen", "mussen", "wollen", "durfen", "mochten"],
            "negative": [], "hints": ["modal verbs"]
        },
        "Freizeitaktivitäten, Hobbys und Sport": {
            "strong": ["freizeitaktivitaten", "hobbys", "was machst du in der freizeit", "fussball spielen", "musik horen", "schwimmen"],
            "specific": ["freizeit", "hobbys", "sport", "spielen", "schwimmen"],
            "negative": [], "hints": ["hobbies"]
        },
        "Wohnungsbeschreibung, Zimmer und Möbel": {
            "strong": ["wohnung", "zimmer", "wohnzimmer schlafzimmer kuche bad", "mobel", "tisch stuhl bett schrank"],
            "specific": ["wohnung", "zimmer", "mobel", "kuche", "schlafzimmer"],
            "negative": [], "hints": ["housing"]
        },
        "Adjektive und ihre Steigerung (Komparativ und Superlativ)": {
            "strong": ["adjektive", "komparativ und superlativ", "schneller als", "am schnellsten", "gut besser am besten", "gross grosser am grossten"],
            "specific": ["komparativ", "superlativ", "steigerung der adjektive"],
            "negative": [], "hints": ["comparison"]
        },
        "Wechselpräpositionen mit Dativ und Akkusativ": {
            "strong": ["wechselprapositionen", "an auf hinter in neben", "uber unter vor zwischen", "wo mit dativ", "wohin mit akkusativ"],
            "specific": ["wechselprapositionen", "dativ oder akkusativ", "an auf in"],
            "negative": [], "hints": ["prepositions"]
        },
        "Dativ: Bestimmte, unbestimmte und Personalpronomen": {
            "strong": ["dativ", "dem der dem", "einem einer einem", "mir dir ihm ihr", "dativobjekt"],
            "specific": ["dativ", "dem der", "einem einer", "mir dir ihm"],
            "negative": [], "hints": ["dative"]
        },
        "Wegbeschreibung und Orientierung in der Stadt": {
            "strong": ["wegbeschreibung", "wo ist die bank", "gehen sie geradeaus", "biegen sie links rechts ab", "in der stadt orientieren"],
            "specific": ["wegbeschreibung", "geradeaus", "biegen sie", "wo ist", "in der stadt"],
            "negative": [], "hints": ["directions"]
        },
        "Einkaufen, Kleidung und Farben": {
            "strong": ["einkaufen im geschaft", "kleidung", "hose hemd kleid schuhe", "farben", "rot blau grun gelb schwarz weiss"],
            "specific": ["kleidung", "farben", "einkaufen", "hose", "hemd"],
            "negative": [], "hints": ["shopping"]
        },
        "Perfekt mit haben und sein (Grundlagen der Vergangenheit)": {
            "strong": ["perfekt", "partizip ii", "gegangen", "gemacht", "habe gemacht", "bin gegangen", "perfekt mit haben und sein"],
            "specific": ["perfekt", "partizip ii", "vergangenheit"],
            "negative": [], "hints": ["perfect tense"]
        }
    }

    # French (Track 2)
    french_rules = {
        "L'Alphabet Français et la Phonétique": {
            "strong": ["l'alphabet francais", "alphabet francais", "phonetique francaise", "voyelles et consonnes", "les accents francais"],
            "specific": ["alphabet", "phonetique", "voyelles", "accents"],
            "negative": [], "hints": ["french basics"]
        },
        "Les Accents et la Ponctuation": {
            "strong": ["accent aigu", "accent grave", "accent circonflexe", "la cedille", "le trema", "ponctuation"],
            "specific": ["accent aigu", "accent grave", "circonflexe", "cedille", "trema"],
            "negative": [], "hints": ["accents"]
        },
        "L'Orthographe et les Règles de Prononciation": {
            "strong": ["liaison en francais", "elision", "lettres muettes", "prononciation francaise"],
            "specific": ["liaison", "elision", "lettres muettes", "prononciation"],
            "negative": [], "hints": ["pronunciation"]
        },
        "La Communication et les Consignes en Classe": {
            "strong": ["consignes de classe", "ouvrez vos livres", "ecoutez et repetez", "comment dit-on", "je ne comprends pas"],
            "specific": ["consignes", "en classe", "ouvrez", "ecoutez"],
            "negative": [], "hints": ["classroom french"]
        },
        "Les Salutations et Formules de Politesse": {
            "strong": ["bonjour", "bonsoir", "salut", "au revoir", "s'il vous plait", "merci beaucoup", "enchantee", "comment allez-vous"],
            "specific": ["bonjour", "salut", "au revoir", "politesse", "enchantee", "merci"],
            "negative": [], "hints": ["greetings"]
        },
        "Les Pronoms Personnels Sujets": {
            "strong": ["pronoms personnels sujets", "je tu il elle", "nous vous ils elles", "pronom sujet"],
            "specific": ["pronoms personnels", "pronoms sujets", "sujets"],
            "negative": [], "hints": ["subject pronouns"]
        },
        "Verbes Fondamentaux: être, avoir, s'appeler, habiter": {
            "strong": ["verbe etre", "verbe avoir", "je suis tu es", "j'ai tu as", "je m'appelle", "j'habite a", "etes intelligents"],
            "specific": ["verbe etre", "verbe avoir", "s'appeler", "habiter", "etes"],
            "negative": [], "hints": ["basic verbs"]
        },
        "Se Présenter et Présenter Quelqu'un": {
            "strong": ["se presenter", "je me presente", "voici mon ami", "c'est un collegue", "quel est votre nom"],
            "specific": ["se presenter", "presenter", "voici", "c'est mon"],
            "negative": [], "hints": ["introductions"]
        },
        "Les Articles Définis et Indéfinis": {
            "strong": ["articles definis", "articles indefinis", "le la l' les", "un une des"],
            "specific": ["articles definis", "articles indefinis", "le la les", "un une des"],
            "negative": [], "hints": ["articles"]
        },
        "Les Nombres de 0 à 69, Jours et Mois": {
            "strong": ["nombres de 0 a 69", "sept cent soixante", "jours de la semaine", "mois de l'annee", "lundi mardi mercredi", "janvier fevrier"],
            "specific": ["nombres", "jours", "mois de l'annee", "soixante"],
            "negative": [], "hints": ["numbers and calendar"]
        },
        "Les Pronoms Toniques": {
            "strong": ["pronoms toniques", "moi toi lui elle", "nous vous eux elles tonique", "avec moi", "et toi"],
            "specific": ["pronoms toniques", "moi", "toi", "lui"],
            "negative": [], "hints": ["tonic pronouns"]
        },
        "Les Nombres de 70 à 1000": {
            "strong": ["soixante-dix", "quatre-vingts", "quatre-vingt-dix", "cent mille", "nombres 70 a 1000"],
            "specific": ["quatre-vingts", "soixante-dix", "sept cent", "mille"],
            "negative": [], "hints": ["higher numbers"]
        },
        "Verbes Réguliers du 1er Groupe en -er": {
            "strong": ["verbes du premier groupe", "verbes en -er", "parler aimer travailler", "terminaisons en -er", "e es e ons ez ent"],
            "specific": ["premier groupe", "verbes en -er", "terminaisons"],
            "negative": [], "hints": ["first group verbs"]
        },
        "Verbes Aller et Venir": {
            "strong": ["verbe aller", "verbe venir", "je vais tu vas", "je viens tu viens", "venir de"],
            "specific": ["verbe aller", "verbe venir", "je vais", "je viens"],
            "negative": [], "hints": ["irregular verbs"]
        },
        "Les Professions et Métiers": {
            "strong": ["professions et metiers", "quelle est votre profession", "medecin avocat ingenieur", "professeur etudiant"],
            "specific": ["professions", "metiers", "ingenieur", "professeur", "medecin"],
            "negative": [], "hints": ["jobs"]
        },
        "Pays, Villes et Nationalités": {
            "strong": ["pays et villes", "nationalites", "france francais", "inde indien indienne", "en france au japon aux etats-unis"],
            "specific": ["nationalites", "pays", "la france", "symboles de la france"],
            "negative": [], "hints": ["countries"]
        },
        "Genre et Nombre des Adjectifs Qualificatifs": {
            "strong": ["adjectifs qualificatifs", "feminin des adjectifs", "pluriel des adjectifs", "accord des adjectifs"],
            "specific": ["adjectifs qualificatifs", "accord des adjectifs", "feminin", "pluriel"],
            "negative": [], "hints": ["adjectives"]
        },
        "Les Prépositions de Lieu": {
            "strong": ["prepositions de lieu", "a en au aux", "devant derriere sous sur", "a cote de en face de"],
            "specific": ["prepositions de lieu", "devant", "derriere", "a cote de"],
            "negative": [], "hints": ["prepositions"]
        },
        "Les Adjectifs Possessifs et la Famille": {
            "strong": ["adjectifs possessifs", "mon ma mes", "ton ta tes", "son sa ses", "la famille en francais", "pere mere frere soeur"],
            "specific": ["adjectifs possessifs", "mon ma mes", "famille", "pere", "mere"],
            "negative": [], "hints": ["possessives and family"]
        },
        "Les Mots et Structures Interrogatives": {
            "strong": ["mots interrogatifs", "qui que quoi ou quand comment pourquoi", "est-ce que", "l'inversion interrogative"],
            "specific": ["interrogatifs", "est-ce que", "pourquoi", "comment", "ou quand"],
            "negative": [], "hints": ["interrogatives"]
        },
        "Les Verbes Modaux: vouloir, pouvoir, devoir": {
            "strong": ["verbes modaux", "vouloir pouvoir devoir", "je veux tu veux", "je peux tu peux", "je dois"],
            "specific": ["vouloir", "pouvoir", "devoir", "verbes modaux"],
            "negative": [], "hints": ["modals"]
        },
        "Les Verbes Pronominaux et la Routine": {
            "strong": ["verbes pronominaux", "se lever se coucher", "se doucher s'habiller", "la routine quotidienne"],
            "specific": ["verbes pronominaux", "routine quotidienne", "se lever", "se coucher"],
            "negative": [], "hints": ["reflexive verbs"]
        },
        "Verbes du 2ème Groupe en -ir": {
            "strong": ["verbes du deuxieme groupe", "verbes en -ir", "finir choisir remplir", "terminaisons -is -is -it -issons -issez -issent"],
            "specific": ["deuxieme groupe", "verbes en -ir", "finir", "choisir"],
            "negative": [], "hints": ["second group verbs"]
        },
        "Les Loisirs, Goûts et Préférences": {
            "strong": ["les loisirs", "gouts et preferences", "j'aime le cinema", "je deteste le sport", "faire du sport jouer au football"],
            "specific": ["loisirs", "preferences", "j'aime", "je prefere"],
            "negative": [], "hints": ["leisure"]
        },
        "Le Futur Proche": {
            "strong": ["le futur proche", "aller plus infinitif", "je vais manger", "nous allons partir"],
            "specific": ["futur proche", "aller + infinitif"],
            "negative": [], "hints": ["near future"]
        },
        "L'Heure et les Horaires": {
            "strong": ["quelle heure est-il", "il est deux heures", "et quart", "et demie", "moins le quart", "les horaires"],
            "specific": ["quelle heure", "l'heure", "et quart", "et demie"],
            "negative": [], "hints": ["time"]
        },
        "Les Adjectifs Démonstratifs: ce, cette, ces": {
            "strong": ["adjectifs demonstratifs", "ce cet cette ces", "demonstratif en francais"],
            "specific": ["adjectifs demonstratifs", "ce cet cette ces"],
            "negative": [], "hints": ["demonstratives"]
        },
        "Les Expressions de Quantité et Articles Partitifs": {
            "strong": ["articles partitifs", "du de la de l' des", "expressions de quantite", "un kilo de", "beaucoup de", "un peu de"],
            "specific": ["articles partitifs", "partitifs", "quantite", "du de la", "beaucoup de"],
            "negative": [], "hints": ["partitives"]
        },
        "Verbes Particuliers en -ger, -cer, -yer": {
            "strong": ["verbes en -ger", "manger", "verbes en -cer", "commencer", "verbes en -yer", "payer"],
            "specific": ["verbes en -ger", "verbes en -cer", "manger", "commencer"],
            "negative": [], "hints": ["spelling change verbs"]
        },
        "Verbes du 3ème Groupe Irréguliers": {
            "strong": ["verbes du troisieme groupe", "verbes irreguliers", "faire prendre mettre voir partir"],
            "specific": ["troisieme groupe", "verbes irreguliers", "faire", "prendre", "mettre"],
            "negative": [], "hints": ["third group verbs"]
        },
        "Les Vêtements, Couleurs et la Mode": {
            "strong": ["les vetements", "pantalon chemise robe manteau", "les couleurs", "rouge bleu vert blanc noir", "la mode francaise"],
            "specific": ["vetements", "couleurs", "pantalon", "chemise", "robe"],
            "negative": [], "hints": ["clothing and colors"]
        },
        "Adverbes de Fréquence et de Temps": {
            "strong": ["adverbes de frequence", "toujours souvent quelquefois rarement jamais", "adverbes de temps", "aujourd'hui demain hier"],
            "specific": ["adverbes de frequence", "toujours", "souvent", "jamais", "parfois"],
            "negative": [], "hints": ["adverbs"]
        },
        "Proposer, Accepter ou Refuser une Sortie": {
            "strong": ["proposer une sortie", "tu veux aller au cinema", "d'accord avec plaisir", "desole je ne peux pas", "invitation"],
            "specific": ["proposer", "accepter", "refuser", "invitation", "sortie"],
            "negative": [], "hints": ["invitations"]
        }
    }

    # Combine track rules
    lang_rules = {
        1: german_rules,
        2: french_rules,
    }

    for track in tracks:
        track_defs.append({
            "id": track.id,
            "key": track.track_key,
            "name": track.track_name,
            "code": track.track_code
        })

        t_syl = db.query(Syllabus).filter(Syllabus.course_id == 8, Syllabus.track_id == track.id).first()
        if not t_syl:
            continue

        rules_for_track = lang_rules.get(track.id, {})

        for u in sorted(t_syl.units, key=lambda x: x.number):
            u_dict = {
                "id": u.id,
                "number": u.number,
                "name": u.name,
                "track_id": track.id,
                "track_key": track.track_key,
                "topics": []
            }
            for t in u.topics:
                kw = rules_for_track.get(t.name, {
                    "strong": [t.name.lower()],
                    "specific": [w.lower() for w in t.name.split() if len(w) > 4],
                    "negative": [],
                    "hints": [track.track_name.lower()]
                })
                # Add topic name words as fallback if empty
                if not kw["strong"]:
                    kw["strong"] = [t.name.lower()]
                if not kw["specific"]:
                    kw["specific"] = [w.lower() for w in t.name.split() if len(w) > 4]

                u_dict["topics"].append({
                    "id": t.id,
                    "name": t.name,
                    "canonical_name": t.name,
                    "aliases": [],
                    "strong_phrases": kw.get("strong", [t.name.lower()]),
                    "specific_keywords": kw.get("specific", []),
                    "negative_guards": kw.get("negative", []),
                    "context_hints": kw.get("hints", [track.track_name.lower()])
                })
            units.append(u_dict)

    entry = {
        "schema_version": "1.0",
        "taxonomy_version": "1.0.0",
        "course": {
            "id": 8,
            "name": "Foreign Languages",
            "canonical_code": "SEM1-FORE",
            "code": "SEM1-FORE",
            "regulation_year": 2021,
            "department": "Department of English and Foreign Languages"
        },
        "provenance": {
            "source_document": "SRMIST B.Tech Regulation 2021 Foreign Language Electives Curriculum & Syllabi",
            "regulation": "2021",
            "approved_by": "Academic Council SRMIST",
            "notes": "Language-segmented catalog course with 6 isolated tracks: German (21LEH104T), French (21LEH103T), Spanish (21LEH107T), Japanese (21LEH105T), Korean (21LEH106T), and Chinese (21LEH102T)."
        },
        "tracks": track_defs,
        "units": units
    }

    out_path = os.path.join(DEFS_DIR, "course_08_fore.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)
    print(f"Generated {out_path} with {len(units)} units across {len(track_defs)} tracks and {sum(len(u['topics']) for u in units)} topics.")


def main():
    db = SessionLocal()
    try:
        generate_emphy_definition(db)
        generate_phymech_definition(db)
        generate_foreign_languages_definition(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
