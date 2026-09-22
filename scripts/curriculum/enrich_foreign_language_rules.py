"""
Comprehensive rule enrichment for Course 8 (Foreign Languages):
- German (Track 1)
- French (Track 2)
- Spanish (Track 3)
- Japanese (Track 4)
- Korean (Track 5)
- Chinese (Track 6)

Ensures high-precision, track-isolated classification matching the SRMIST 2021 curriculum.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.core.database import SessionLocal
from backend.models.core import CourseTrack, Syllabus, Unit, Topic


DEFS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "backend", "services", "taxonomy_registry", "definitions"
)


GERMAN_RULES = {
    "Begrüßung, Alphabet und Aussprache": {
        "strong": ["guten morgen", "guten tag", "guten abend", "auf wiedersehen", "wie geht es ihnen", "buchstabieren", "alphabet auf deutsch", "wie sagt man", "begrussung"],
        "specific": ["guten morgen", "guten tag", "auf wiedersehen", "tschuess", "alphabet", "begrussung", "buchstabieren"],
        "negative": [], "hints": ["german basics"]
    },
    "Zahlen von 0 bis 100 und Grundrechenarten": {
        "strong": ["zahlen", "eins zwei drei", "null bis", "grundrechenarten", "plus minus mal geteilt", "wie viel ist", "ziffern"],
        "specific": ["zahlen", "eins", "zwei", "drei", "zwanzig", "hundert", "dreissig", "funfzig"],
        "negative": [], "hints": ["numbers"]
    },
    "Personalpronomen und Konjugation im Präsens (sein, haben, heißen)": {
        "strong": ["personalpronomen", "konjugation", "sein haben", "ich bin du bist", "ich heisse", "konjugieren sie", "wer wo wie was"],
        "specific": ["personalpronomen", "konjugation", "prasens", "haben", "heissen", "sein"],
        "negative": [], "hints": ["german grammar"]
    },
    "Sich vorstellen und andere Personen vorstellen": {
        "strong": ["wie heissen sie", "ich heisse", "wer ist das", "das ist mein freund", "woher kommen sie", "ich komme aus", "handynummer", "telefonnummer", "alter", "wie alt"],
        "specific": ["vorstellen", "wie heisst du", "woher kommen", "mein name ist", "handynummer", "telefonnummer"],
        "negative": [], "hints": ["introductions"]
    },
    "Höflichkeitsformen (Sie vs. du)": {
        "strong": ["hoeflichkeitsform", "sie vs du", "duzen oder siezen", "formelle anrede", "informelle anrede"],
        "specific": ["duzen", "siezen", "anrede"],
        "negative": [], "hints": ["politeness"]
    },
    "Länder, Nationalitäten und Sprachen": {
        "strong": ["deutschland", "osterreich", "schweiz", "welche sprachen sprechen sie", "nationalitat", "deutsch japanisch chinesisch", "spricht man", "land und sprache"],
        "specific": ["deutschland", "osterreich", "spricht man", "nationalitat", "sprachen", "in osterreich"],
        "negative": [], "hints": ["countries and languages"]
    },
    "W-Fragen und Ja/Nein-Fragen (Satzbau)": {
        "strong": ["w-fragen", "wer wie was wo", "ja nein fragen", "satzbau", "inversionsfrage", "fragewort"],
        "specific": ["w-frage", "frageworter", "satzbau", "inversion", "fragewort"],
        "negative": [], "hints": ["questions"]
    },
    "Bestimmte und unbestimmte Artikel (der, die, das / ein, eine)": {
        "strong": ["bestimmter artikel", "unbestimmter artikel", "der die das", "ein eine ein", "artikel im nominativ"],
        "specific": ["artikel", "der die das", "bestimmte artikel", "unbestimmte"],
        "negative": [], "hints": ["articles"]
    },
    "Negation mit 'nicht' und 'kein'": {
        "strong": ["negation mit nicht", "negation mit kein", "kein keine", "nicht oder kein", "verneinung"],
        "specific": ["negation", "nicht", "kein", "keine", "verneinung"],
        "negative": [], "hints": ["negation"]
    },
    "Familienmitglieder und Verwandtschaftsverhältnisse": {
        "strong": ["meine familie", "vater mutter eltern", "bruder schwester", "sohn tochter", "grossvater grossmutter", "onkel tante", "verwandte"],
        "specific": ["familie", "eltern", "bruder", "schwester", "vater", "mutter", "grosseltern"],
        "negative": [], "hints": ["family"]
    },
    "Possessivpronomen im Nominativ (mein, dein, sein, ihr)": {
        "strong": ["possessivpronomen", "mein dein sein", "ihr unser euer", "possessivartikel", "meine mutter dein vater"],
        "specific": ["possessivpronomen", "possessivartikel", "mein", "dein", "sein", "ihr"],
        "negative": [], "hints": ["possessives"]
    },
    "Uhrzeiten (offiziell und umgangssprachlich)": {
        "strong": ["wie spat ist es", "wie viel uhr ist es", "uhrzeit", "viertel vor", "viertel nach", "halb", "um wie viel uhr"],
        "specific": ["uhrzeit", "wie spat", "wieviel uhr", "viertel", "halb"],
        "negative": [], "hints": ["time"]
    },
    "Wochentage, Monate und Jahreszeiten": {
        "strong": ["montag dienstag mittwoch", "wochentage", "januar februar marz", "monate des jahres", "fruhling sommer herbst winter", "jahreszeiten", "the spring", "the summer", "the winter", "the autumn"],
        "specific": ["wochentage", "monate", "jahreszeiten", "der herbst", "der sommer", "der fruhling", "der winter"],
        "negative": [], "hints": ["calendar"]
    },
    "Tagesablauf und trennbare Verben im Präsens": {
        "strong": ["tagesablauf", "trennbare verben", "aufstehen", "fernsehen", "einkaufen", "anfangen", "steht auf", "fangt an"],
        "specific": ["tagesablauf", "trennbare verben", "aufstehen", "einkaufen", "fernsehen"],
        "negative": [], "hints": ["daily routine"]
    },
    "Akkusativ: Bestimmte, unbestimmte und Negativartikel": {
        "strong": ["akkusativ", "den die das", "einen eine ein", "keinen keine", "akkusativobjekt", "wen oder was"],
        "specific": ["akkusativ", "akkusativobjekt", "den", "einen", "keinen"],
        "negative": ["dativ"], "hints": ["accusative"]
    },
    "Verben mit Akkusativergänzung": {
        "strong": ["verben mit akkusativ", "brauchen", "haben", "kaufen", "suchen", "finden", "mochten"],
        "specific": ["akkusativerganzung", "verben mit akkusativ"],
        "negative": [], "hints": ["verbs"]
    },
    "Essen, Trinken und Mahlzeiten": {
        "strong": ["essen und trinken", "fruhstuck", "mittagessen", "abendessen", "was isst du", "was trinkst du", "apfel brot milch"],
        "specific": ["essen", "trinken", "mahlzeiten", "fruhstuck", "lebensmittel"],
        "negative": [], "hints": ["food and drink"]
    },
    "Im Restaurant bestellen und bezahlen": {
        "strong": ["im restaurant", "ich mochte bestellen", "die rechnung bitte", "zusammen oder getrennt", "kellner", "trinkgeld"],
        "specific": ["restaurant", "bestellen", "rechnung bitte", "kellner"],
        "negative": [], "hints": ["dining"]
    },
    "Modalverben im Präsens (können, müssen, wollen, dürfen, möchten)": {
        "strong": ["modalverben", "konnen mussen wollen", "durfen mochten", "ich kann du kannst", "ich muss", "du darfst"],
        "specific": ["modalverben", "konnen", "mussen", "wollen", "durfen", "mochten"],
        "negative": [], "hints": ["modal verbs"]
    },
    "Freizeitaktivitäten, Hobbys und Sport": {
        "strong": ["freizeitaktivitaten", "hobbys", "was machst du in der freizeit", "fussball spielen", "musik horen", "schwimmen", "ins kino gehen"],
        "specific": ["freizeit", "hobbys", "sport", "spielen", "schwimmen"],
        "negative": [], "hints": ["hobbies"]
    },
    "Wohnungsbeschreibung, Zimmer und Möbel": {
        "strong": ["wohnung", "zimmer", "wohnzimmer schlafzimmer kuche bad", "mobel", "tisch stuhl bett schrank", "balkon"],
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
        "strong": ["dativ", "dem der dem", "einem einer einem", "mir dir ihm ihr", "dativobjekt", "wem"],
        "specific": ["dativ", "dem der", "einem einer", "mir dir ihm"],
        "negative": [], "hints": ["dative"]
    },
    "Wegbeschreibung und Orientierung in der Stadt": {
        "strong": ["wegbeschreibung", "wo ist die bank", "gehen sie geradeaus", "biegen sie links rechts ab", "in der stadt orientieren"],
        "specific": ["wegbeschreibung", "geradeaus", "biegen sie", "wo ist", "in der stadt"],
        "negative": [], "hints": ["directions"]
    },
    "Einkaufen, Kleidung und Farben": {
        "strong": ["einkaufen im geschaft", "kleidung", "hose hemd kleid schuhe", "farben", "rot blau grun gelb schwarz weiss", "was kostet"],
        "specific": ["kleidung", "farben", "einkaufen", "hose", "hemd"],
        "negative": [], "hints": ["shopping"]
    },
    "Perfekt mit haben und sein (Grundlagen der Vergangenheit)": {
        "strong": ["perfekt", "partizip ii", "gegangen", "gemacht", "habe gemacht", "bin gegangen", "perfekt mit haben und sein"],
        "specific": ["perfekt", "partizip ii", "vergangenheit"],
        "negative": [], "hints": ["perfect tense"]
    }
}


FRENCH_RULES = {
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
        "strong": ["verbe etre", "verbe avoir", "je suis tu es", "j'ai tu as", "je m'appelle", "j'habite a", "etes intelligents", "etes"],
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
        "strong": ["soixante-dix", "quatre-vingts", "quatre-vingt-dix", "cent mille", "nombres 70 a 1000", "nombre correct en lettres"],
        "specific": ["quatre-vingts", "soixante-dix", "sept cent", "mille", "en lettres"],
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
        "strong": ["pays et villes", "nationalites", "france francais", "inde indien indienne", "en france au japon aux etats-unis", "symboles de la france", "tgv est"],
        "specific": ["nationalites", "pays", "la france", "symboles de la france", "tgv"],
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


SPANISH_RULES = {
    "El Abecedario y Pronunciación": {
        "strong": ["abecedario", "el alfabeto", "pronunciacion en espanol", "letras del abecedario"],
        "specific": ["abecedario", "alfabeto", "pronunciacion"],
        "negative": [], "hints": ["spanish basics"]
    },
    "Saludos y Despedidas": {
        "strong": ["hola buenos dias", "buenas tardes", "buenas noches", "adios hasta luego", "saludos y despedidas"],
        "specific": ["saludos", "despedidas", "buenos dias", "buenas tardes", "hasta luego"],
        "negative": [], "hints": ["greetings"]
    },
    "Nacionalidades y Profesiones": {
        "strong": ["nacionalidad", "profesion", "espanol espanola", "medico profesor estudiante", "de donde eres"],
        "specific": ["nacionalidades", "profesiones", "de donde", "profesor", "medico"],
        "negative": [], "hints": ["professions"]
    },
    "Números del 1 al 100": {
        "strong": ["numeros del 1 al 100", "uno dos tres cuatro", "diez veinte treinta", "cuarenta cincuenta"],
        "specific": ["numeros", "veinte", "treinta", "cincuenta", "cien"],
        "negative": [], "hints": ["numbers"]
    },
    "Presentación Personal y Datos de Contacto": {
        "strong": ["presentacion personal", "me llamo", "como te llamas", "datos de contacto", "numero de telefono"],
        "specific": ["presentacion", "como te llamas", "me llamo", "telefono"],
        "negative": [], "hints": ["introductions"]
    },
    "Pronombres Personales y Artículos Definidos": {
        "strong": ["pronombres personales", "yo tu el ella", "articulos definidos", "el la los las"],
        "specific": ["pronombres", "articulos definidos", "el la los las"],
        "negative": [], "hints": ["grammar"]
    },
    "Verbos Auxiliares: ser, tener, llamarse": {
        "strong": ["verbo ser", "verbo tener", "yo soy tu eres", "yo tengo tu tienes", "llamarse"],
        "specific": ["verbo ser", "verbo tener", "llamarse", "yo soy", "yo tengo"],
        "negative": [], "hints": ["verbs"]
    },
    "La Familia y Relaciones": {
        "strong": ["la familia", "padre madre hermano", "hijo hija abuelo", "relaciones familiares"],
        "specific": ["familia", "padre", "madre", "hermano", "abuelo"],
        "negative": [], "hints": ["family"]
    },
    "Artículos Indefinidos y Números hasta 1000": {
        "strong": ["articulos indefinidos", "un una unos unas", "numeros hasta 1000", "cien doscientos mil", "dos mil veintiuno", "dos mil veintitres"],
        "specific": ["articulos indefinidos", "un una unos", "doscientos", "quinientos", "dos mil"],
        "negative": [], "hints": ["numbers"]
    },
    "Estructuras de Negación y Traducción": {
        "strong": ["negacion en espanol", "no nunca jamas", "traduccion al espanol"],
        "specific": ["negacion", "traduccion"],
        "negative": [], "hints": ["negation"]
    },
    "Direcciones Cardinales y Medios de Transporte": {
        "strong": ["puntos cardinales", "norte sur este oeste", "medios de transporte", "autobus tren coche metro"],
        "specific": ["cardinales", "transporte", "autobus", "metro", "tren"],
        "negative": [], "hints": ["transport"]
    },
    "Preguntar por Direcciones y Ubicaciones": {
        "strong": ["donde esta", "como se va a", "gire a la izquierda", "siga todo recto"],
        "specific": ["donde esta", "direcciones", "a la izquierda", "a la derecha", "recto"],
        "negative": [], "hints": ["directions"]
    },
    "Presente de Indicativo: Verbos Regulares -ar, -er, -ir": {
        "strong": ["verbos regulares", "presente de indicativo", "terminaciones ar er ir", "hablar comer vivir"],
        "specific": ["verbos regulares", "presente", "hablar", "comer", "vivir"],
        "negative": [], "hints": ["verbs"]
    },
    "El Verbo Hay y Expresión de Existencia": {
        "strong": ["verbo hay", "hay en la ciudad", "expresion de existencia"],
        "specific": ["hay", "existencia"],
        "negative": [], "hints": ["existence"]
    },
    "El Superlativo y Cuantificadores": {
        "strong": ["superlativo", "muy mas el mas", "cuantificadores", "mucho poco bastante"],
        "specific": ["superlativo", "cuantificadores", "mucho", "poco"],
        "negative": [], "hints": ["superlative"]
    },
    "Preguntas Interrogativas: qué, cuál, cuántos, dónde, cómo": {
        "strong": ["preguntas interrogativas", "que cual cuantos donde como", "cual es el tercer dia", "que ano es", "que mes del ano"],
        "specific": ["cual es", "que ano", "que mes", "interrogativas", "donde", "como"],
        "negative": [], "hints": ["questions"]
    },
    "Diferenciación entre Ser y Estar": {
        "strong": ["ser y estar", "diferencia ser y estar", "esta cansado es inteligente"],
        "specific": ["ser y estar", "estar en"],
        "negative": [], "hints": ["ser vs estar"]
    },
    "Números Ordinales y Días de la Semana": {
        "strong": ["numeros ordinales", "primero segundo tercero", "dias de la semana", "lunes martes miercoles jueves viernes sabado domingo", "tercer dia de la semana"],
        "specific": ["ordinales", "dias de la semana", "lunes", "tercer dia", "domingo"],
        "negative": [], "hints": ["days"]
    },
    "Verbos Irregulares en Tiempo Presente": {
        "strong": ["verbos irregulares", "ir venir hacer salir poner", "irregularidad vocalica"],
        "specific": ["verbos irregulares", "hacer", "venir", "poner"],
        "negative": [], "hints": ["irregular verbs"]
    },
    "Expresiones del Clima y Estaciones del Año": {
        "strong": ["el clima en espanol", "hace calor hace frio", "estaciones del ano", "primavera verano otono invierno", "temporada de", "estamos en la temporada"],
        "specific": ["clima", "estaciones del ano", "temporada de", "invierno", "primavera", "verano", "otono"],
        "negative": [], "hints": ["weather"]
    },
    "Comprensión Lectora y Expresión Escrita": {
        "strong": ["comprension lectora", "lea el texto", "redaccion en espanol"],
        "specific": ["comprension lectora", "lectura", "redaccion"],
        "negative": [], "hints": ["reading"]
    },
    "Vocabulario Escolar y Académico": {
        "strong": ["vocabulario escolar", "escuela universidad lapiz cuaderno libro"],
        "specific": ["escolar", "universidad", "cuaderno", "lapiz"],
        "negative": [], "hints": ["school"]
    },
    "Compras en Tiendas y Pedir Precios": {
        "strong": ["cuanto cuesta", "cuanto es", "en la tienda de ropa", "compras"],
        "specific": ["cuanto cuesta", "precios", "tienda", "compras"],
        "negative": [], "hints": ["shopping"]
    },
    "Demostrativos: este, esta, estos, estas, esto": {
        "strong": ["adjetivos demostrativos", "este esta estos estas esto"],
        "specific": ["demostrativos", "este", "esta", "estos"],
        "negative": [], "hints": ["demonstratives"]
    },
    "Perífrasis Obligativa: tener que + infinitivo": {
        "strong": ["perifrasis obligativa", "tener que mas infinitivo", "tengo que estudiar"],
        "specific": ["tener que", "perifrasis", "obligacion"],
        "negative": [], "hints": ["obligation"]
    },
    "El Verbo Ir y Lugares": {
        "strong": ["verbo ir", "voy vas va vamos vais van", "ir a la playa", "ir al cine"],
        "specific": ["verbo ir", "voy a", "vamos a"],
        "negative": [], "hints": ["motion"]
    },
    "Prendas de Vestir y Colores": {
        "strong": ["prendas de vestir", "camisa pantalon falda vestido zapatos", "colores en espanol", "rojo azul verde blanco negro"],
        "specific": ["ropa", "vestir", "colores", "pantalon", "camisa"],
        "negative": [], "hints": ["clothes and colors"]
    },
    "Descripción del Aspecto Físico y Carácter": {
        "strong": ["aspecto fisico", "alto bajo rubio moreno", "caracter", "simpatico amable"],
        "specific": ["aspecto fisico", "caracter", "alto", "rubio", "simpatico"],
        "negative": [], "hints": ["description"]
    },
    "Expresar Gustos e Intereses con el Verbo Gustar": {
        "strong": ["verbo gustar", "me gusta te gusta", "intereses y preferencias", "me encanta"],
        "specific": ["verbo gustar", "me gusta", "te gusta", "me encanta"],
        "negative": [], "hints": ["likes"]
    },
    "En el Restaurante: Ordenar Comida y Pagar": {
        "strong": ["en el restaurante", "la carta la cuenta", "camarero", "de primero de segundo", "ordenar comida"],
        "specific": ["restaurante", "la cuenta", "camarero", "carta"],
        "negative": [], "hints": ["dining"]
    },
    "Adjetivos Posesivos y Pertenencia": {
        "strong": ["adjetivos posesivos", "mi tu su nuestro vuestro", "pertenencia"],
        "specific": ["posesivos", "mi casa", "tu libro", "su"],
        "negative": [], "hints": ["possessives"]
    },
    "Rutina Diaria y Actividades Cotidianas": {
        "strong": ["rutina diaria", "levantarse ducharse acostarse", "actividades cotidianas"],
        "specific": ["rutina", "levantarse", "cotidianas"],
        "negative": [], "hints": ["routine"]
    }
}


JAPANESE_RULES = {
    "Japanese Language, Culture and Self-Introduction": {
        "strong": ["hajimemashite", "watashi wa", "douzo yoroshiku", "self-introduction", "japanese culture"],
        "specific": ["hajimemashite", "watashi wa", "self-introduction"],
        "negative": [], "hints": ["japanese culture"]
    },
    "Greetings and Classroom Expressions": {
        "strong": ["ohayou gozaimasu", "konnichiwa", "konbanwa", "arigatou gozaimasu", "sayounara", "sumimasen", "classroom expressions"],
        "specific": ["ohayou", "konnichiwa", "arigatou", "sumimasen", "sayounara"],
        "negative": [], "hints": ["greetings"]
    },
    "Basic Particles: wa, ka, mo, no": {
        "strong": ["particle wa", "particle ka", "particle mo", "particle no", "fill in the blank with appropriate particle wa"],
        "specific": ["particle wa", "particle ka", "particle no", "particle mo"],
        "negative": [], "hints": ["particles"]
    },
    "Sentence Patterns: desu and ja arimasen": {
        "strong": ["desu", "ja arimasen", "dewaarimasen", "sentence pattern desu"],
        "specific": ["desu", "ja arimasen", "dewaarimasen"],
        "negative": [], "hints": ["patterns"]
    },
    "Hiragana Writing System: Lessons 1 to 4": {
        "strong": ["hiragana", "hiragana writing", "ojiisan", "gakki", "kabin", "rakuda", "write in hiragana", "hiragana characters"],
        "specific": ["hiragana", "ojiisan", "gakki", "kabin", "rakuda"],
        "negative": ["katakana"], "hints": ["hiragana"]
    },
    "Demonstrative Pronouns: kono, sono, ano, dono, kore, sore, are, dore": {
        "strong": ["kore sore are dore", "kono sono ano dono", "demonstrative pronouns japanese"],
        "specific": ["kore", "sore", "are", "kono", "sono", "ano"],
        "negative": [], "hints": ["demonstratives"]
    },
    "Existence Sentences: arimasu, imasu with ni, ga particles": {
        "strong": ["arimasu", "imasu", "existence sentences", "ni arimasu", "ga imasu"],
        "specific": ["arimasu", "imasu", "ni arimasu"],
        "negative": [], "hints": ["existence"]
    },
    "Days of the Week, Months, and Numbers": {
        "strong": ["getsuyoubi ka kinyoubi", "days of the week japanese", "ichi ni san shi go", "nan-gatsu", "months in japanese"],
        "specific": ["getsuyoubi", "nichiyoubi", "ichi ni san", "nan-gatsu"],
        "negative": [], "hints": ["calendar"]
    },
    "Kanji for Days of the Week and Numbers": {
        "strong": ["kanji for days", "kanji numbers", "kanji ichi ni san", "kanji hi tsuki"],
        "specific": ["kanji days", "kanji numbers"],
        "negative": [], "hints": ["kanji"]
    },
    "Time Expressions: Hours, Minutes, Gozen and Gogo": {
        "strong": ["ima nan-ji desu ka", "nan-pun", "gozen", "gogo", "hours and minutes japanese"],
        "specific": ["nan-ji", "gozen", "gogo", "nan-pun"],
        "negative": [], "hints": ["time"]
    },
    "Location Markers: ue, shita, naka and Directions": {
        "strong": ["ue shita naka", "migi hidari", "location markers", "directions in japanese"],
        "specific": ["ue", "shita", "naka", "migi", "hidari"],
        "negative": [], "hints": ["locations"]
    },
    "Location Pronouns: koko, soko, asoko, doko": {
        "strong": ["koko soko asoko doko", "location pronouns"],
        "specific": ["koko", "soko", "asoko", "doko"],
        "negative": [], "hints": ["locations"]
    },
    "Asking Prices and Requesting with o kudasai": {
        "strong": ["ikura desu ka", "o kudasai", "asking prices japanese", "how much is this"],
        "specific": ["ikura", "kudasai", "o kudasai"],
        "negative": [], "hints": ["prices"]
    },
    "Numbers up to One Lakh (100,000)": {
        "strong": ["sen", "man", "juuman", "numbers up to 100000", "yen"],
        "specific": ["juuman", "sen yen", "ichiman"],
        "negative": [], "hints": ["large numbers"]
    },
    "Japanese Seasons, Weather, Origami, Ikebana and Culture": {
        "strong": ["haru natsu aki fuyu", "seasons japanese", "origami", "ikebana", "japanese tea"],
        "specific": ["haru", "natsu", "aki", "fuyu", "origami", "ikebana"],
        "negative": [], "hints": ["culture"]
    },
    "Hiragana Lessons 5 to 10: Double Consonants and Long Vowels": {
        "strong": ["double consonants hiragana", "long vowels hiragana", "sokuon", "chouon"],
        "specific": ["double consonants", "long vowels", "sokuon"],
        "negative": [], "hints": ["phonetics"]
    },
    "Kanji: Numbers, Yen, Colours and Directions": {
        "strong": ["kanji yen", "kanji colours", "kanji directions", "en kanji"],
        "specific": ["kanji yen", "en", "colours kanji"],
        "negative": [], "hints": ["kanji"]
    },
    "Keeki o Yattsu Kudasai and General Counters (~tsu)": {
        "strong": ["hitotsu futatsu mittsu", "general counters tsu", "keeki o yattsu kudasai"],
        "specific": ["hitotsu", "futatsu", "mittsu", "yattsu"],
        "negative": [], "hints": ["counters"]
    },
    "Specialized Counters: -nin, -hiki, -dai, -kai": {
        "strong": ["counters nin", "counters hiki", "counters dai", "counters mai", "specialized counters"],
        "specific": ["hiki", "dai", "nin", "mai", "counters"],
        "negative": [], "hints": ["counters"]
    },
    "Family Members: Plain vs Polite Forms": {
        "strong": ["chichi haha ani ane", "otousan okaasan oniisan oneesan", "family members japanese", "plain vs polite family"],
        "specific": ["chichi", "haha", "otousan", "okaasan", "oniisan"],
        "negative": [], "hints": ["family"]
    },
    "Japanese House, Living Style and Architecture": {
        "strong": ["japanese house", "tatami", "washitsu", "fusuma", "living style"],
        "specific": ["tatami", "washitsu", "japanese house"],
        "negative": [], "hints": ["housing"]
    },
    "Katakana Rules, Characters and Writing System": {
        "strong": ["katakana", "katakana writing", "write in katakana", "foreign words katakana"],
        "specific": ["katakana", "katakana rules"],
        "negative": ["hiragana"], "hints": ["katakana"]
    },
    "Kanji: otoko, onna, ko, hito": {
        "strong": ["kanji otoko onna", "kanji hito", "kanji ko"],
        "specific": ["otoko", "onna", "hito", "kanji"],
        "negative": [], "hints": ["kanji"]
    },
    "Action Verbs: ikimasu, okimasu, nemasu, tabemasu": {
        "strong": ["ikimasu", "okimasu", "nemasu", "tabemasu", "nomimasu", "action verbs japanese"],
        "specific": ["ikimasu", "tabemasu", "nomimasu", "nemasu", "okimasu"],
        "negative": [], "hints": ["verbs"]
    },
    "Verb Tenses: Past Tense and Negative Forms (~masen deshita)": {
        "strong": ["mashita", "masen deshita", "past tense japanese verbs", "negative past verbs"],
        "specific": ["mashita", "masen deshita", "past tense verbs"],
        "negative": [], "hints": ["verb tenses"]
    },
    "Particles in Context: e, de, to, ni, o, ga": {
        "strong": ["particle de", "particle to", "particle e", "particle ni", "particle o"],
        "specific": ["particle de", "particle to", "particle e"],
        "negative": [], "hints": ["particles"]
    },
    "Adjectives: -i and -na Ending Adjectives": {
        "strong": ["i-adjectives", "na-adjectives", "takai yasui", "kirei na", "shizuka na"],
        "specific": ["i-adjectives", "na-adjectives", "takai", "kirei"],
        "negative": [], "hints": ["adjectives"]
    },
    "Kanji: ikimasu, mimasu, yasumimasu, kaimasu": {
        "strong": ["kanji ikimasu", "kanji mimasu", "kanji kaimasu"],
        "specific": ["mimasu", "kaimasu", "kanji verbs"],
        "negative": [], "hints": ["kanji"]
    },
    "Daily Expressions, Body Parts and Religious Beliefs": {
        "strong": ["body parts japanese", "atama me mimi", "shinto", "buddhism in japan"],
        "specific": ["body parts", "atama", "religious beliefs"],
        "negative": [], "hints": ["daily life"]
    },
    "Invitational Expressions: ~masen ka and ~mashou": {
        "strong": ["masen ka", "mashou", "mashou ka", "invitational expressions japanese", "let's do"],
        "specific": ["masen ka", "mashou", "invitational"],
        "negative": [], "hints": ["invitations"]
    },
    "Adjectives: Present, Past, Affirmative and Negative Forms": {
        "strong": ["adjective conjugation", "katta", "kunai", "deshita", "adjectives past forms"],
        "specific": ["katta", "kunai", "adjective conjugation"],
        "negative": [], "hints": ["adjective forms"]
    },
    "Stationery and Transport Vocabulary": {
        "strong": ["stationery japanese", "pen nooto", "densha basu chikatetsu", "transport vocabulary"],
        "specific": ["stationery", "densha", "chikatetsu", "basu"],
        "negative": [], "hints": ["vocabulary"]
    },
    "Grammar: Usage of ~te Form": {
        "strong": ["te-form", "te form of verbs", "te kudasai", "usage of te form"],
        "specific": ["te-form", "te form", "te kudasai"],
        "negative": [], "hints": ["te-form"]
    },
    "Grammar: Desire and Want with ~tai Form": {
        "strong": ["tai form", "tabetai", "ikitai", "desire and want japanese", "hoshigaru"],
        "specific": ["tai form", "tabetai", "ikitai", "desire"],
        "negative": [], "hints": ["tai-form"]
    },
    "Kanji: ookii, chiisai, eki, chuui": {
        "strong": ["kanji ookii", "kanji chiisai", "kanji eki", "kanji chuui"],
        "specific": ["ookii", "chiisai", "eki", "kanji"],
        "negative": [], "hints": ["kanji"]
    },
    "Japanese Tea Ceremony, Political System and Economy": {
        "strong": ["tea ceremony", "chanoyu", "sado", "japanese political system", "japanese economy"],
        "specific": ["tea ceremony", "chanoyu", "economy japan"],
        "negative": [], "hints": ["culture"]
    }
}


KOREAN_RULES = {
    "Introduction to Korea and Korean Culture": {
        "strong": ["korean culture", "hallyu", "seoul", "south korea", "introduction to korea"],
        "specific": ["korean culture", "hallyu", "seoul"],
        "negative": [], "hints": ["culture"]
    },
    "Hangul Writing System (한글 소개)": {
        "strong": ["hangeul", "hangul writing system", "king sejong", "hunminjeongeum", "korean alphabet", "한글"],
        "specific": ["hangul", "hangeul", "alphabet korean"],
        "negative": [], "hints": ["writing"]
    },
    "Single Vowels and Double Vowels (단모음, 이중모음)": {
        "strong": ["single vowels", "double vowels", "korean vowels", "a ya eo yeo o yo u yu eu i", "단모음", "이중모음"],
        "specific": ["vowels", "단모음", "이중모음"],
        "negative": [], "hints": ["phonetics"]
    },
    "Basic, Aspirated and Tense Consonants": {
        "strong": ["aspirated consonants", "tense consonants", "giyeok nieun digeut", "korean consonants", "자음"],
        "specific": ["consonants", "aspirated", "tense consonants"],
        "negative": [], "hints": ["consonants"]
    },
    "Final Consonants / Batchim (받침)": {
        "strong": ["batchim", "final consonants", "받침", "batchim pronunciation"],
        "specific": ["batchim", "받침", "final consonant"],
        "negative": [], "hints": ["batchim"]
    },
    "Self-Introduction and Daily Greetings (자기 소개, 인사말)": {
        "strong": ["annyeonghaseyo", "gamsahamnida", "thank you is in korean", "yes is in korean", "annyeong", "daily greetings korean", "자기 소개", "인사말", "안녕하세요", "감사합니다"],
        "specific": ["annyeonghaseyo", "gamsahamnida", "thank you", "greetings korean", "안녕하세요", "감사합니다", "yes is"],
        "negative": [], "hints": ["greetings"]
    },
    "Topic Marking Particles: eun / neun (은/는)": {
        "strong": ["topic marking particle", "eun neun", "은 는", "topic particle korean"],
        "specific": ["eun neun", "은/는", "topic particle"],
        "negative": [], "hints": ["particles"]
    },
    "Subject Marking Particles: i / ga (이/가)": {
        "strong": ["subject marking particle", "i ga", "이 가", "subject particle korean"],
        "specific": ["i ga", "이/가", "subject particle"],
        "negative": [], "hints": ["particles"]
    },
    "Informal Polite Sentence Endings: ieyo / yeyo (이에요/예요)": {
        "strong": ["ieyo yeyo", "이에요 예요", "informal polite sentence ending", "is / am / are in korean"],
        "specific": ["ieyo", "yeyo", "이에요", "예요"],
        "negative": [], "hints": ["sentence endings"]
    },
    "Formal Polite Sentence Endings: bipnida / seupnida (ㅂ니다/습니다)": {
        "strong": ["bipnida seupnida", "ㅂ니다 습니다", "formal polite sentence ending"],
        "specific": ["bipnida", "seupnida", "습니다", "ㅂ니다"],
        "negative": [], "hints": ["sentence endings"]
    },
    "Demonstrative Pronouns: i, geu, jeo (이, 그, 저)": {
        "strong": ["demonstrative pronouns korean", "i geu jeo", "igeot geugeot jeogeot", "이 그 저"],
        "specific": ["i geu jeo", "igeot", "geugeot"],
        "negative": [], "hints": ["demonstratives"]
    },
    "Sino-Korean Number System and Applications": {
        "strong": ["sino korean numbers", "il i sam sa o yuk chil pal gu sip", "phone numbers korean", "일 이 삼 사"],
        "specific": ["sino-korean", "il i sam", "numbers korean"],
        "negative": [], "hints": ["numbers"]
    },
    "Present Tense Verb Conjugation: ayo / eoyo / haeyo (아요/어요/해요)": {
        "strong": ["present tense verb korean", "ayo eoyo haeyo", "아요 어요 해요", "verb conjugation korean"],
        "specific": ["ayo eoyo", "haeyo", "아요", "어요", "해요"],
        "negative": [], "hints": ["present tense"]
    },
    "Past Tense Verb Conjugation: asseoyo / eosseoyo (았/었/했어요)": {
        "strong": ["past tense verb korean", "asseoyo eosseoyo", "았어요 었어요 했어요", "korean past tense"],
        "specific": ["asseoyo", "eosseoyo", "았어요", "었어요"],
        "negative": [], "hints": ["past tense"]
    },
    "Native Korean Numbers and Counting Units": {
        "strong": ["native korean numbers", "hana dul set net daseot", "counting units korean", "gae myeong", "하나 둘 셋"],
        "specific": ["native korean", "hana dul set", "counting units", "하나 둘"],
        "negative": [], "hints": ["native numbers"]
    },
    "Weather, Seasons and Daily Vocabulary": {
        "strong": ["weather korean", "bom yeoreum gaeul gyeoul", "seasons korean", "nalssi", "날씨", "계절"],
        "specific": ["weather korean", "nalssi", "seasons korean", "날씨"],
        "negative": [], "hints": ["weather"]
    },
    "Location Particles: e and eseo (에, 에서)": {
        "strong": ["location particle e eseo", "에 에서", "korean location particles", "at / in korean"],
        "specific": ["e eseo", "에 에서", "location particle"],
        "negative": [], "hints": ["locations"]
    },
    "Telling Time: Hours, Minutes and Periods of the Day": {
        "strong": ["telling time korean", "myeot si", "hours and minutes korean", "o'clock korean", "몇 시"],
        "specific": ["myeot si", "telling time", "hours korean"],
        "negative": [], "hints": ["time"]
    },
    "Days of the Week and Months of the Year": {
        "strong": ["woryoil hwayoil", "days of the week korean", "months korean", "월요일 화요일", "ilwol iwol"],
        "specific": ["woryoil", "days of week korean", "months korean"],
        "negative": [], "hints": ["calendar"]
    },
    "Future Tense Conjugation: (eu)l geoyeyo ((으)ㄹ 거예요)": {
        "strong": ["future tense korean", "eul geoyeyo", "(으)ㄹ 거예요", "will do in korean"],
        "specific": ["future tense", "geoyeyo", "ㄹ 거예요"],
        "negative": [], "hints": ["future tense"]
    },
    "Object Marking Particles: eul / reul (을/를)": {
        "strong": ["object marking particle", "eul reul", "을 를", "object particle korean"],
        "specific": ["eul reul", "을/를", "object particle"],
        "negative": [], "hints": ["objects"]
    },
    "Honorific Particle: kkeseo and Subject Honorifics (시/으시)": {
        "strong": ["honorific particle", "kkeseo", "seonsaengnim", "u.s.a is in korean", "miguk", "teacher is in korean", "occupations korean", "선생님", "미국", "의사"],
        "specific": ["seonsaengnim", "u.s.a", "teacher", "miguk", "선생님", "미국", "occupations"],
        "negative": [], "hints": ["honorifics and occupations"]
    },
    "Expressing Ability and Possibility: (eu)l su itda / eopda ((으)ㄹ 수 있다/없다)": {
        "strong": ["ability in korean", "eul su itda", "eul su eopda", "(으)ㄹ 수 있다", "can and cannot korean"],
        "specific": ["su itda", "su eopda", "ability korean"],
        "negative": [], "hints": ["ability"]
    },
    "Imperatives and Requests: (eu)seyo ((으)세요)": {
        "strong": ["imperatives korean", "euseyo", "(으)세요", "please do in korean", "requests korean"],
        "specific": ["euseyo", "세요", "requests korean"],
        "negative": [], "hints": ["imperatives"]
    },
    "Prohibitions: ji maseyo (지 마세요)": {
        "strong": ["prohibition korean", "ji maseyo", "지 마세요", "do not in korean"],
        "specific": ["ji maseyo", "지 마세요", "prohibition"],
        "negative": [], "hints": ["prohibition"]
    },
    "Expressing Desire and Wants: go sipda (고 싶다)": {
        "strong": ["want in korean", "go sipda", "go sipeoyo", "고 싶다", "desire korean"],
        "specific": ["go sipda", "고 싶다", "desire korean"],
        "negative": [], "hints": ["desire"]
    },
    "Complex Sentences with Connective Particles (고, 서)": {
        "strong": ["connective particles korean", "go", "aseo eoseo", "and in korean", "because in korean"],
        "specific": ["connective", "aseo", "eoseo"],
        "negative": [], "hints": ["conjunctions"]
    },
    "Daily Activities, Hobbies and Campus Life": {
        "strong": ["daily activities korean", "hobbies korean", "chwimi", "campus life korean", "daehakgyo"],
        "specific": ["daily activities", "hobbies", "campus life"],
        "negative": [], "hints": ["activities"]
    }
}


CHINESE_RULES = {
    "Introduction to Mandarin Chinese and Geography": {
        "strong": ["mandarin chinese", "geography of china", "beijing shanghai", "dialects of chinese"],
        "specific": ["mandarin", "geography china", "beijing"],
        "negative": [], "hints": ["china geography"]
    },
    "Pinyin System: Initials, Finals and Combinations": {
        "strong": ["pinyin system", "initials and finals", "shengmu yunmu", "pinyin combination"],
        "specific": ["pinyin", "initials", "finals", "shengmu", "yunmu"],
        "negative": [], "hints": ["pinyin"]
    },
    "The Four Tones and Tone Neutralization": {
        "strong": ["four tones", "which of the following tone", "first tone second tone third tone fourth tone", "neutral tone", "tone mark", "tone neutralization", "ni hao tone"],
        "specific": ["tone", "tones", "first tone", "second tone", "third tone", "fourth tone", "neutral tone"],
        "negative": [], "hints": ["tones"]
    },
    "Eight Basic Strokes and Stroke Order of Characters": {
        "strong": ["stroke order", "eight basic strokes", "heng shu pie na", "chinese character strokes"],
        "specific": ["strokes", "stroke order", "heng shu"],
        "negative": [], "hints": ["strokes"]
    },
    "Personal Pronouns and Plural Forms (我, 你, 他, 们)": {
        "strong": ["personal pronouns chinese", "wo ni ta", "women nimen tamen", "我 你 他", "plural pronouns chinese"],
        "specific": ["wo", "ni", "ta", "women", "nimen", "personal pronouns"],
        "negative": [], "hints": ["pronouns"]
    },
    "Grammar Particles: hen (很), ye (也), ma (吗), ne (呢), de (的)": {
        "strong": ["chinese equivalent for 'very'", "grammar particles chinese", "hen", "ye", "ma", "ne", "de", "很 也 吗 呢 的"],
        "specific": ["very", "hen", "ye", "grammar particles", "很", "也"],
        "negative": [], "hints": ["particles"]
    },
    "Basic Daily Greetings and Politeness Phrases": {
        "strong": ["ni hao", "zaijian", "xiexie", "bu keqi", "duibuqi", "daily greetings chinese", "politeness phrases"],
        "specific": ["ni hao", "zaijian", "xiexie", "duibuqi", "greetings"],
        "negative": [], "hints": ["greetings"]
    },
    "Chinese Number System and Counting": {
        "strong": ["chinese numbers", "yi er san si wu liu qi ba jiu shi", "numbers in chinese", "counting in chinese", "一 二 三 四 五"],
        "specific": ["chinese numbers", "yi er san", "numbers"],
        "negative": [], "hints": ["numbers"]
    },
    "Chinese Currency and Monetary Terms (元, 角, 分)": {
        "strong": ["chinese currency", "yuan jiao fen", "kuai qian", "renminbi", "rmb", "元 角 分"],
        "specific": ["yuan", "kuai", "currency", "renminbi"],
        "negative": [], "hints": ["currency"]
    },
    "Telephone Numbers and Conversational Needs": {
        "strong": ["telephone numbers chinese", "dianhua haoma", "wei", "phone conversation chinese"],
        "specific": ["dianhua", "haoma", "telephone numbers"],
        "negative": [], "hints": ["phone"]
    },
    "Time Telling, Calendar, Days, Months and Seasons": {
        "strong": ["time telling chinese", "dian fen", "days of week chinese", "xingqi", "months chinese", "yue ri"],
        "specific": ["xingqi", "dian", "fen", "yue", "calendar chinese"],
        "negative": [], "hints": ["calendar"]
    },
    "Basic S-V-O Sentence Patterns in Mandarin": {
        "strong": ["svo sentence pattern", "word order in chinese", "sentence patterns mandarin"],
        "specific": ["svo", "sentence pattern", "word order"],
        "negative": [], "hints": ["patterns"]
    },
    "Verbs: shi / bu shi (是/不是) and you / mei you (有/没有)": {
        "strong": ["shi bu shi", "you mei you", "是 不是", "有 没有", "verbs to be and to have chinese"],
        "specific": ["shi", "bu shi", "you", "mei you", "是", "不是"],
        "negative": [], "hints": ["verbs"]
    },
    "Asking and Introducing Nationalities": {
        "strong": ["nationalities chinese", "zhongguo ren", "meiguo ren", "yin-du ren", "na guo ren", "which country"],
        "specific": ["ren", "zhongguo", "meiguo", "nationalities"],
        "negative": [], "hints": ["nationalities"]
    },
    "Interrogative Words: ji (几) and duo shao (多少)": {
        "strong": ["question words ji duoshao", "ji", "duoshao", "how many in chinese", "几", "多少"],
        "specific": ["ji", "duoshao", "how many", "几", "多少"],
        "negative": [], "hints": ["how many"]
    },
    "Asking and Bargaining Prices in Chinese": {
        "strong": ["duoshao qian", "tai gui le", "bargaining in chinese", "how much money", "多少钱"],
        "specific": ["duoshao qian", "tai gui le", "prices chinese"],
        "negative": [], "hints": ["shopping"]
    },
    "Asking Names Formally and Expressing Apologies": {
        "strong": ["nin guixing", "jiaoshenme mingzi", "meiguanxi", "apologies chinese"],
        "specific": ["guixing", "mingzi", "meiguanxi"],
        "negative": [], "hints": ["names"]
    },
    "Location Prepositions with zai (在)": {
        "strong": ["location zai", "zai nar", "prepositions of location chinese", "在"],
        "specific": ["zai", "zai nar", "location chinese"],
        "negative": [], "hints": ["locations"]
    },
    "Spatial Demonstratives: zher (这儿), nar (那儿), nar (哪儿)": {
        "strong": ["zher nar", "here and there chinese", "这儿 那儿 哪儿", "demonstratives location"],
        "specific": ["zher", "nar", "here there"],
        "negative": [], "hints": ["demonstratives"]
    },
    "Occupations, Professions and Workplace Vocabulary": {
        "strong": ["professions chinese", "laoshi", "xuesheng", "yisheng", "gongchengshi", "workplace vocabulary"],
        "specific": ["laoshi", "xuesheng", "yisheng", "professions"],
        "negative": [], "hints": ["professions"]
    },
    "Making, Accepting and Declining Suggestions": {
        "strong": ["suggestions chinese", "zenmeyang", "hao bu hao", "ba particle suggestion"],
        "specific": ["zenmeyang", "suggestions", "hao bu hao"],
        "negative": [], "hints": ["suggestions"]
    },
    "Subject-Predicate as Predicate Constructions": {
        "strong": ["subject-predicate predicate", "complex predicate chinese", "grammar constructions"],
        "specific": ["predicate", "subject-predicate"],
        "negative": [], "hints": ["grammar"]
    },
    "Food, Fruits and Ordering Meals Vocabulary": {
        "strong": ["ordering food chinese", "chifan he cha", "cai menu", "shuiguo pingguo", "restaurant chinese"],
        "specific": ["chifan", "he cha", "food chinese", "fruits"],
        "negative": [], "hints": ["food"]
    },
    "Action Verbs and Adverbial Modifiers": {
        "strong": ["action verbs chinese", "qu lai kan ting", "adverbial modifiers"],
        "specific": ["action verbs", "modifiers"],
        "negative": [], "hints": ["verbs"]
    },
    "Sports, Games, Hobbies and Leisure Vocabulary": {
        "strong": ["sports chinese", "ti zuqiu", "da lanqiu", "hobbies chinese", "leisure activities"],
        "specific": ["sports", "hobbies", "zuqiu", "lanqiu"],
        "negative": [], "hints": ["sports"]
    },
    "Describing Family Members and Relatives": {
        "strong": ["chinese equivalent for 'elder sister'", "chinese equivalent for 'elder brother'", "english equivalent for '妈妈'", "family members chinese", "baba mama", "gege didi", "jiejie meimei", "elder sister", "elder brother", "younger brother", "younger sister", "妈妈", "爸爸", "姐姐", "哥哥"],
        "specific": ["elder sister", "elder brother", "younger sister", "family members", "mama", "baba", "jiejie", "gege", "didi", "meimei", "妈妈", "姐姐"],
        "negative": [], "hints": ["family"]
    },
    "University, Academic Departments and Student Life": {
        "strong": ["university chinese", "daxue", "zhuanye", "department chinese", "student life"],
        "specific": ["daxue", "zhuanye", "university"],
        "negative": [], "hints": ["university"]
    },
    "Time Sequencing Words: yiqian (以前), yihou (以后), haishi (还是)": {
        "strong": ["time sequencing words", "yiqian", "yihou", "haishi", "huozhe", "以前 以后 还是"],
        "specific": ["yiqian", "yihou", "haishi", "before after"],
        "negative": [], "hints": ["sequencing"]
    },
    "Optative Modal Verbs: hui (会), neng (能), keyi (可以)": {
        "strong": ["modal verbs chinese", "hui neng keyi", "会 能 可以", "can and able to in chinese"],
        "specific": ["hui", "neng", "keyi", "modal verbs", "会", "能"],
        "negative": [], "hints": ["modals"]
    },
    "Expressing Likes, Dislikes and Color Preferences": {
        "strong": ["xihuan", "bu xihuan", "likes and dislikes chinese", "colors chinese", "hongse lanse baise heise"],
        "specific": ["xihuan", "colors chinese", "hongse"],
        "negative": [], "hints": ["preferences"]
    },
    "Traditional Chinese Festivals and Culture": {
        "strong": ["chinese festivals", "chunjie spring festival", "zhongqiujie mid-autumn", "traditional culture china"],
        "specific": ["chunjie", "festivals", "chinese culture"],
        "negative": [], "hints": ["culture"]
    }
}


TRACK_RULES_MAP = {
    1: GERMAN_RULES,
    2: FRENCH_RULES,
    3: SPANISH_RULES,
    4: JAPANESE_RULES,
    5: KOREAN_RULES,
    6: CHINESE_RULES,
}


def update_foreign_languages_definition():
    in_path = os.path.join(DEFS_DIR, "course_08_fore.json")
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for unit in data.get("units", []):
        t_id = unit.get("track_id")
        rules_map = TRACK_RULES_MAP.get(t_id, {})
        for topic in unit.get("topics", []):
            t_name = topic["name"]
            if t_name in rules_map:
                cfg = rules_map[t_name]
                topic["strong_phrases"] = cfg.get("strong", topic.get("strong_phrases", []))
                topic["specific_keywords"] = cfg.get("specific", topic.get("specific_keywords", []))
                topic["negative_guards"] = cfg.get("negative", topic.get("negative_guards", []))
                topic["context_hints"] = cfg.get("hints", topic.get("context_hints", []))

    with open(in_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Updated {in_path} with enriched rules across all 6 language tracks.")


if __name__ == "__main__":
    update_foreign_languages_definition()
