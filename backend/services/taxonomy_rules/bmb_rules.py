"""
Taxonomy classification rules for Course 7: Biomedical Sensors (21BMB101T / 21BMC101J).
Derived directly from the official SRM IST Biomedical Engineering Syllabus, Question Bank, and course decks.

Unit 1 (id=7):  Measurement System and Medical Instrumentation (Topics 180-183)
Unit 2 (id=66): Temperature Transducers (Topics 184-187)
Unit 3 (id=67): Pressure and Magnetic Transducers (Topics 188-191)
Unit 4 (id=68): Optical Transducers (Topics 192-195)
Unit 5 (id=69): Medical Applications of Sensors (Topics 196-199)
"""
from typing import List
from backend.services.taxonomy_classifier import TaxonomyTopicRule

BMB_TAXONOMY_RULES: List[TaxonomyTopicRule] = [
    # -------------------------------------------------------------
    # UNIT 1: MEASUREMENT SYSTEM AND MEDICAL INSTRUMENTATION
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=180,
        topic_name="Functional Elements and Terminologies of Measurement Systems",
        unit_id=7,
        unit_name="Measurement System and Medical Instrumentation",
        strong_phrases=[
            "block that makes physical contact", "functional elements of a measurement system",
            "functional block of measurement system", "measurement terminologies"
        ],
        specific_keywords=["measurement system", "physical contact with physical quantity"],
        negative_guards=["oximeter", "heart rate", "photodiode", "rtd", "lvdt"]
    ),
    TaxonomyTopicRule(
        topic_id=181,
        topic_name="Classification and Display of Electrical Parameters",
        unit_id=7,
        unit_name="Measurement System and Medical Instrumentation",
        strong_phrases=[
            "measuring instrument", "resistance can be measured using", "ohmmeter",
            "classify instruments based on various factors", "display electrical parameters"
        ],
        specific_keywords=["ohmmeter", "measuring instrument"],
        negative_guards=["transducer", "oximeter", "photodiode"]
    ),
    TaxonomyTopicRule(
        topic_id=182,
        topic_name="Advantages and Architecture of Electronic Instruments",
        unit_id=7,
        unit_name="Measurement System and Medical Instrumentation",
        strong_phrases=[
            "category of instruments are best suited", "advantages of electronic instrument",
            "electronic instruments"
        ],
        specific_keywords=["electronic instrument", "electronic instruments"],
        negative_guards=["medical instrument", "oximeter", "lvdt"]
    ),
    TaxonomyTopicRule(
        topic_id=183,
        topic_name="Functional Elements and Salient Features of Medical Instruments",
        unit_id=7,
        unit_name="Measurement System and Medical Instrumentation",
        strong_phrases=[
            "salient features of medical instruments", "functional elements of a medical instrument",
            "medical instruments"
        ],
        specific_keywords=["medical instruments", "medical instrument"],
        negative_guards=["lvdt", "strain gauge", "thermocouple"]
    ),

    # -------------------------------------------------------------
    # UNIT 2: TEMPERATURE TRANSDUCERS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=184,
        topic_name="Principles, Types, and Classification of Transducers",
        unit_id=66,
        unit_name="Temperature Transducers",
        strong_phrases=[
            "converts one form of energy into another", "not a temperature transducer",
            "transducers - block diagram", "classification of transducers"
        ],
        specific_keywords=["converts one form of energy into another"],
        negative_guards=["lvdt", "oximeter"]
    ),
    TaxonomyTopicRule(
        topic_id=185,
        topic_name="Resistance Temperature Detectors (RTD): Principles and Applications",
        unit_id=66,
        unit_name="Temperature Transducers",
        strong_phrases=[
            "operating principle of rtd", "construction and operating principle of rtd",
            "resistance temperature detector", "characteristics of rtd"
        ],
        specific_keywords=["resistance temperature detector"],
        negative_guards=["oximeter", "lvdt"]
    ),
    TaxonomyTopicRule(
        topic_id=186,
        topic_name="Thermistors: Characteristics, Construction, and Working",
        unit_id=66,
        unit_name="Temperature Transducers",
        strong_phrases=[
            "negative temperature coefficient of resistance", "possess negative temperature coefficient",
            "characteristics of thermistor", "operating principles of thermistor"
        ],
        specific_keywords=["negative temperature coefficient"],
        negative_guards=["lvdt", "oximeter"]
    ),
    TaxonomyTopicRule(
        topic_id=187,
        topic_name="Thermocouples: Seebeck Effect, Operating Principles, and Applications",
        unit_id=66,
        unit_name="Temperature Transducers",
        strong_phrases=[
            "seeback effect is associated with", "seebeck effect is associated with",
            "seeback effect", "seebeck effect", "operating principles of thermocouple",
            "characteristics of thermocouple"
        ],
        specific_keywords=["seebeck", "seeback"],
        negative_guards=["lvdt", "oximeter"]
    ),

    # -------------------------------------------------------------
    # UNIT 3: PRESSURE AND MAGNETIC TRANSDUCERS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=188,
        topic_name="Strain Gauges and Load Cells: Principles and Construction",
        unit_id=67,
        unit_name="Pressure and Magnetic Transducers",
        strong_phrases=[
            "output of strain gauge", "characteristics of strain gauge",
            "measure force using a transducer"
        ],
        specific_keywords=["strain gauge"],
        negative_guards=["lvdt", "photodiode", "oximeter", "seebeck", "seeback", "temperature transducer"]
    ),

    TaxonomyTopicRule(
        topic_id=189,
        topic_name="Capacitive Transducers: Working Principles and Operation",
        unit_id=67,
        unit_name="Pressure and Magnetic Transducers",
        strong_phrases=[
            "capacitance of a capacitor is inversely proportional", "capacitive transducer",
            "capacitive transducers"
        ],
        specific_keywords=["capacitive transducer", "capacitive transducers"],
        negative_guards=["piezoelectric", "lvdt", "rtd"]
    ),
    TaxonomyTopicRule(
        topic_id=190,
        topic_name="Piezoelectric Transducers: Piezoelectric Effect and Applications",
        unit_id=67,
        unit_name="Pressure and Magnetic Transducers",
        strong_phrases=[
            "output of piezoelectric transducer", "piezoelectric transducer",
            "piezoelectric effect", "characteristics of piezoelectric transducer"
        ],
        specific_keywords=["piezoelectric"],
        negative_guards=["lvdt", "strain gauge", "photodiode"]
    ),
    TaxonomyTopicRule(
        topic_id=191,
        topic_name="Linear Variable Differential Transformers (LVDT): Construction and Operation",
        unit_id=67,
        unit_name="Pressure and Magnetic Transducers",
        strong_phrases=[
            "movable part of lvdt", "construction and operating principle of lvdt",
            "characteristics of lvdt", "linear variable differential transformer", "lvdt"
        ],
        specific_keywords=["lvdt"],
        negative_guards=["strain gauge", "photodiode", "oximeter"]
    ),

    # -------------------------------------------------------------
    # UNIT 4: OPTICAL TRANSDUCERS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=192,
        topic_name="Photodiodes: Operating Principles and Characteristic Curves",
        unit_id=68,
        unit_name="Optical Transducers",
        strong_phrases=[
            "photo diode operates on the principle", "photo diode", "photodiode",
            "characteristics of photodiode", "photo electric effect"
        ],
        specific_keywords=["photodiode", "photo diode"],
        negative_guards=["phototransistor", "photovoltaic", "ldr"]
    ),
    TaxonomyTopicRule(
        topic_id=193,
        topic_name="Phototransistors: Construction and Working Principles",
        unit_id=68,
        unit_name="Optical Transducers",
        strong_phrases=[
            "fall on a phototransistor", "phototransistor", "characteristics of phototransistor"
        ],
        specific_keywords=["phototransistor"],
        negative_guards=["photodiode", "photovoltaic", "ldr"]
    ),
    TaxonomyTopicRule(
        topic_id=194,
        topic_name="Light Dependent Resistors (LDR) and Photoconductive Cells",
        unit_id=68,
        unit_name="Optical Transducers",
        strong_phrases=[
            "optoelectronic transducer", "light dependent resistor", "characteristics of ldr", "ldr"
        ],
        specific_keywords=["ldr"],
        negative_guards=["photodiode", "phototransistor", "photovoltaic"]
    ),
    TaxonomyTopicRule(
        topic_id=195,
        topic_name="Photovoltaic Cells and Optical Sensor Applications",
        unit_id=68,
        unit_name="Optical Transducers",
        strong_phrases=[
            "photovoltaic effect", "operating principle of photovoltaic cell",
            "photovoltaic cell", "photovoltaic cells", "photovoltaic effect is associated with"
        ],
        specific_keywords=["photovoltaic"],
        negative_guards=["oximeter", "lvdt"]
    ),

    # -------------------------------------------------------------
    # UNIT 5: MEDICAL APPLICATIONS OF SENSORS
    # -------------------------------------------------------------
    TaxonomyTopicRule(
        topic_id=196,
        topic_name="Pulse Oximetry and Blood Oxygen Saturation (SpO2) Monitoring",
        unit_id=69,
        unit_name="Medical Applications of Sensors",
        strong_phrases=[
            "oximeter measures", "pulse oximetry", "pulse oximeter",
            "oxygen saturation in blood", "spo2"
        ],
        specific_keywords=["oximeter", "oximetry", "spo2"],
        negative_guards=["phototransistor", "lvdt", "rtd"]
    ),
    TaxonomyTopicRule(
        topic_id=197,
        topic_name="Heart Rate Sensors and Photoplethysmography (PPG)",
        unit_id=69,
        unit_name="Medical Applications of Sensors",
        strong_phrases=[
            "heart rate of a healthy adult", "measure pulse rate of an individual",
            "heart rate sensor", "photoplethysmography", "heart rate", "pulse rate"
        ],
        specific_keywords=["heart rate", "pulse rate", "photoplethysmography", "ppg"],
        negative_guards=["oximeter", "blood pressure"]
    ),
    TaxonomyTopicRule(
        topic_id=198,
        topic_name="Blood Pressure Sensors: Systolic and Diastolic Measurement",
        unit_id=69,
        unit_name="Medical Applications of Sensors",
        strong_phrases=[
            "bp of healthy adult", "blood pressure sensor", "blood pressure",
            "systolic and diastolic", "mm hg"
        ],
        specific_keywords=["blood pressure", "mm hg"],
        negative_guards=["oximeter", "heart rate"]
    ),
    TaxonomyTopicRule(
        topic_id=199,
        topic_name="Infrared (IR) Sensors in Clinical and Biomedical Diagnostics",
        unit_id=69,
        unit_name="Medical Applications of Sensors",
        strong_phrases=[
            "non-contact temperature sensor", "ir sensors", "ir sensor", "infrared sensor"
        ],
        specific_keywords=["non-contact temperature sensor", "infrared sensor"],
        negative_guards=["lvdt", "strain gauge"]
    ),

]
