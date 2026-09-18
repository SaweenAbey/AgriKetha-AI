import spacy
from spacy.pipeline import EntityRuler


nlp = spacy.load("en_core_web_sm")


CROPS = {
    "tomato", "rice", "paddy", "chili", "chilli", "potato", "onion", "brinjal", "eggplant",
    "cucumber", "pepper", "maize", "corn", "carrot", "cabbage", "tea", "coconut", "rubber",
    "cinnamon", "beetroot", "pumpkin", "okra", "bean", "beans", "leek", "leeks"
}


CROP_MAP = {
    "paddy": "rice",
    "chilli": "chili",
    "eggplant": "brinjal",
    "corn": "maize",
    "leeks": "leek",
    "beans": "bean",
}


FERTILIZERS = {
    "fertilizer", "fertiliser", "urea", "compost", "manure", "dung", "npk", 
    "nitrogen", "phosphorus", "potassium", "phosphate", "potash", "organic", "nutrient"
}


FERTILIZER_MAP = {
    "fertiliser": "fertilizer",
    "organic fertilizer": "organic",
}


MACHINERY = {
    "tractor", "harvester", "tiller", "seeder", "sprayer", "plow", "plough", 
    "pump", "motor", "combine", "machine", "machinery", "cultivator", "spraying",
    "plowing", "ploughing", "harvesting", "sowing", "planting"
}


MACHINERY_MAP = {
    "plough": "plow",
    "ploughing": "plowing",
    "motor": "pump",
}


patterns = [
    
    {"label": "CROP", "pattern": [{"LEMMA": "tomato"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "rice"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "paddy"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "chili"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "chilli"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "potato"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "onion"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "brinjal"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "eggplant"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "cucumber"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "pepper"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "maize"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "corn"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "carrot"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "cabbage"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "tea"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "coconut"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "rubber"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "cinnamon"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "beetroot"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "pumpkin"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "okra"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "bean"}]},
    {"label": "CROP", "pattern": [{"LEMMA": "leek"}]},
    {"label": "CROP", "pattern": [{"LOWER": "ladies"}, {"LOWER": "finger"}]},
    {"label": "CROP", "pattern": [{"LOWER": "ladies"}, {"LOWER": "fingers"}]},
    {"label": "CROP", "pattern": [{"LOWER": "ladies'"}, {"LOWER": "finger"}]},
    {"label": "CROP", "pattern": [{"LOWER": "ladies'"}, {"LOWER": "fingers"}]},
    
    # Fertilizer patterns
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "fertilizer"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "fertiliser"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "urea"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "compost"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "manure"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "dung"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "npk"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "nitrogen"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "phosphorus"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "potassium"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "phosphate"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "potash"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "organic"}]},
    {"label": "FERTILIZER", "pattern": [{"LEMMA": "nutrient"}]},

    # Machinery patterns
    {"label": "MACHINERY", "pattern": [{"LEMMA": "tractor"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "harvester"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "tiller"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "seeder"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "sprayer"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "plow"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "plough"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "pump"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "motor"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "combine"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "machine"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "machinery"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "cultivator"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "spraying"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "plowing"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "ploughing"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "harvesting"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "sowing"}]},
    {"label": "MACHINERY", "pattern": [{"LEMMA": "planting"}]},
]


if "entity_ruler" not in nlp.pipe_names:
    ruler = nlp.add_pipe("entity_ruler", before="ner")
else:
    ruler = nlp.get_pipe("entity_ruler")

ruler.add_patterns(patterns)


INTENT_KEYWORDS = {
    "disease diagnosis": {
        "disease", "sick", "spot", "yellow", "symptom", "infect", "infection",
        "pest", "bug", "insect", "rot", "die", "damage", "bite", "curl", "wilt",
        "fungus", "fungi", "mold", "mould", "mildew", "blight", "canker", "rust",
        "caterpillar", "aphid", "worm", "snail", "slug", "beetle", "fly", "flies",
        "whitefly", "whiteflies", "mite", "weed", "treatment", "cure", "remedy"
    },
    "irrigation advice": {
        "water", "watering", "irrigation", "dry", "wet", "rain", "rainfall",
        "monsoon", "drought", "moisture", "humidity", "drainage", "flood",
        "pour", "damp"
    },
    "fertilizer advice": {
        "fertilizer", "fertiliser", "nutrient", "npk", "nitrogen", "phosphorus",
        "potassium", "urea", "compost", "manure", "dung", "organic", "soil",
        "growth", "yield", "feed", "deficiency"
    },
    "market information": {
        "price", "market", "cost", "sell", "selling", "buy", "buying", "rate",
        "value", "rupee", "rupees", "rs", "wholesale", "retail", "shop", "dealer",
        "store", "purchase", "sale"
    },
    "machinery operations": {
        "tractor", "harvester", "tiller", "seeder", "sprayer", "plow", "plough", 
        "pump", "motor", "combine", "machine", "machinery", "operation", "harvesting", 
        "plowing", "ploughing", "spraying", "sowing", "planting", "cultivator", "equipment", 
        "mechanization", "mechanised", "mechanized", "tool", "implements", "gear"
    }
}

MULTILINGUAL_CROP_MAP = {
    "tomato": ["tomato", "tomatoes", "තක්කාලි", "තක්කාලී", "thakkali", "takkali", "தக்காளி"],
    "rice": ["rice", "paddy", "වී", "ගොයම්", "බාත්", "wee", "goyam", "nel", "நெல்"],
    "chili": ["chili", "chilli", "pepper", "peppers", "මිරිස්", "අමු මිරිස්", "කොච්චි", "miris", "amu miris", "kochchi", "மிளகாய்"],
    "potato": ["potato", "potatoes", "අල", "අර්තාපල්", "ala", "arthapal", "உருளைக்கிழங்கு"],
    "onion": ["onion", "onions", "shallot", "shallots", "ලූණු", "ලූනු", "රතු ලූණු", "බිග් ලූණු", "loonu", "lunu", "rathu lunu", "வெங்காயம்"],
    "brinjal": ["brinjal", "brinjals", "eggplant", "aubergine", "වම්බටු", "බටු", "wambatu", "batu", "கத்தரிக்காய்"],
    "cucumber": ["cucumber", "cucumbers", "පිපිඤ්ඤා", "කැකිරි", "pipinna", "kekiri", "வெள்ளரி"],
    "maize": ["maize", "corn", "sweetcorn", "බඩඉරිඟු", "ඉරිඟු", "badairingu", "iringu", "சோளம்"],
    "carrot": ["carrot", "carrots", "කැරට්", "කැරට්ස්", "karat", "கேரட்"],
    "cabbage": ["cabbage", "cabbages", "ගෝවා", "ගෝව", "gowa", "கோவா"],
    "tea": ["tea", "තේ", "තේ වගාව", "the", "thee", "தேயிலை"],
    "coconut": ["coconut", "coconuts", "පොල්", "pol", "தென்னை"],
    "rubber": ["rubber", "රබර්", "rabar", "ரப்பர்"],
    "cinnamon": ["cinnamon", "කුරුඳු", "කුරුදු", "kurundu", "இலவங்கப்பட்டை"],
    "beetroot": ["beetroot", "beet", "බීට්රූට්", "බීට්", "பீட்ரூட்"],
    "pumpkin": ["pumpkin", "pumpkins", "වට්ටක්කා", "ලබු", "wattakka", "labu", "பூசணிக்காய்"],
    "okra": ["okra", "ladies finger", "ladies' finger", "lady's finger", "බණ්ඩක්කා", "බන්ඩක්කා", "bandakka", "வெண்டைக்காய்"],
    "bean": ["bean", "beans", "බෝංචි", "bonchi", "அவரை"],
    "leek": ["leek", "leeks", "ලීක්ස්", "leeks", "லீக்ஸ்"]
}

def extract_crop(doc) -> str:
    """
    Extracts crop name from Doc with multilingual support (English, Sinhala, Tamil).
    """
    text_lower = doc.text.lower()
    
    # Check multilingual mapping first
    for crop_name, aliases in MULTILINGUAL_CROP_MAP.items():
        if any(alias in text_lower for alias in aliases):
            return crop_name

    for ent in doc.ents:
        if ent.label_ == "CROP":
            crop_text = ent.text.lower()
            
            if "ladies" in crop_text and "finger" in crop_text:
                return "okra"
                
            lemmas = [t.lemma_.lower() for t in ent]
            for lemma in lemmas:
                if lemma in CROP_MAP:
                    return CROP_MAP[lemma]
                if lemma in CROPS:
                    return lemma
                    
            for key, val in CROP_MAP.items():
                if key in crop_text:
                    return val
            
            if crop_text.endswith("s") and crop_text[:-1] in CROPS:
                return crop_text[:-1]
            return crop_text

    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in CROPS:
            return CROP_MAP.get(lemma, lemma)
        if token.text.lower() in CROPS:
            return CROP_MAP.get(token.text.lower(), token.text.lower())
            
    return None



def extract_grammatical_symptoms(doc) -> list:
    
    found_symptoms = []
    text_lower = doc.text.lower()
    
    plant_parts = {"leaf", "leaves", "stem", "root", "fruit", "branch", "foliage", "shoot", "flower"}
    conditions = {"yellow", "brown", "black", "dark", "dry", "wilt", "curl", "rot", "spotted"}
    

    for token in doc:
        if token.lemma_ in plant_parts:
            
            for child in token.children:
                if child.lemma_ in conditions:
                    if child.lemma_ == "yellow":
                        found_symptoms.append("yellow leaves")
                    elif child.lemma_ in {"brown", "dark", "black", "spotted"}:
                        found_symptoms.append("brown spots")
                    elif child.lemma_ in {"curl", "curled", "curling"}:
                        found_symptoms.append("leaf curling")
                    elif child.lemma_ in {"wilt", "wilted", "wilting"}:
                        found_symptoms.append("wilting")
            
           
            parent = token.head
            if parent.lemma_ in {"be", "become", "turn", "show", "have", "develop"}:
                for child in parent.children:
                    if child.dep_ in {"attr", "acomp", "dobj"} and child.lemma_ in conditions:
                        if child.lemma_ == "yellow":
                            found_symptoms.append("yellow leaves")
                        elif child.lemma_ in {"brown", "dark", "black", "spotted"}:
                            found_symptoms.append("brown spots")
                        elif child.lemma_ in {"curl", "curled", "curling"}:
                            found_symptoms.append("leaf curling")
                        elif child.lemma_ in {"wilt", "wilted", "wilting"}:
                            found_symptoms.append("wilting")


    # Multilingual symptom pattern matching (Sinhala, Singlish, Tamil, English)
    symptom_rules = [
        ("yellow leaves", [
            "yellow", "yellowing", "chlorosis", "කහ", "කහපාට", "කහවීම", "කහ පාට", "කහ කොළ", 
            "kaha", "kahapaata", "manjal", "மஞ்சள்"
        ]),
        ("brown spots", [
            "brown spot", "brown spots", "black spot", "black spots", "dark spot", "dark spots", "spot", "spots", 
            "ලප", "කළුපාට ලප", "කළු ලප", "දුඹුරු ලප", "තිත්", "කළු තිත්", "ලප තියෙනවා",
            "lapa", "kalu lapa", "dumburu lapa", "pulli", "புள்ளிகள்", "கருப்பு புள்ளி"
        ]),
        ("leaf curling", [
            "curl", "curling", "wrinkle", "wrinkled", "curled",
            "හැකිලීම", "හැකිලෙනවා", "ගුලිවීම", "හැකිලිලා", "කොළ හැකිලීම", 
            "hakilila", "hakilenawa", "suruttai", "சுருட்டை"
        ]),
        ("wilting", [
            "wilt", "wilting", "wilted", "droop", "drooping", "dry", "drying", 
            "මැළවීම", "මැලවෙනවා", "වේලෙනවා", "වියළීම", "මැලිලා", "මැලවිලා",
            "melawenawa", "melila", "vadal", "வாடல்"
        ]),
        ("white insects", [
            "whitefly", "whiteflies", "white insect", "insect", "insects", "bug", "bugs", "aphid", "aphids", "worm", "caterpillar",
            "සුදු මැස්සන්", "සුදු මැස්සා", "මැස්සෝ", "මැක්කන්", "කුඩිත්තන්", "පණුවන්", "පණුවා", "ගොබ පණුවා",
            "panuwo", "kudiththan", "poochi", "பூச்சி", "புழு"
        ]),
        ("fruit/root rot", [
            "rot", "rotting", "decay", "blight", "damping off",
            "කුණුවීම", "කුණු වෙනවා", "කුණු", "මුල් කුණුවීම", "ගෙඩි කුණුවීම", 
            "kunu", "kunuvima", "azhukal", "அழுகல்"
        ]),
        ("fungal infection", [
            "fungus", "fungi", "mold", "mildew", "rust", "canker",
            "පුස්", "දිලීර", "දිලීර රෝග", "pus", "dileera", "poonjai", "பூஞ்சை"
        ])
    ]

    for symptom_name, keywords in symptom_rules:
        if any(kw in text_lower for kw in keywords):
            found_symptoms.append(symptom_name)
        
    return list(sorted(set(found_symptoms)))

def extract_symptoms(doc) -> list:
   
    return extract_grammatical_symptoms(doc)

def extract_fertilizer_details(doc) -> list:
    found_fertilizers = set()
    for ent in doc.ents:
        if ent.label_ == "FERTILIZER":
            val = ent.text.lower()
            lemma = ent[0].lemma_.lower() if len(ent) > 0 else val
            mapped = FERTILIZER_MAP.get(lemma, FERTILIZER_MAP.get(val, lemma))
            if mapped in FERTILIZERS:
                found_fertilizers.add(mapped)
            else:
                found_fertilizers.add(val)
    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in FERTILIZERS:
            found_fertilizers.add(FERTILIZER_MAP.get(lemma, lemma))
        elif token.text.lower() in FERTILIZERS:
            found_fertilizers.add(FERTILIZER_MAP.get(token.text.lower(), token.text.lower()))
    text_lower = doc.text.lower()
    for f in FERTILIZERS:
        if f in text_lower:
            found_fertilizers.add(FERTILIZER_MAP.get(f, f))
    return list(sorted(found_fertilizers))

def extract_machinery_details(doc) -> list:
    found_machinery = set()
    for ent in doc.ents:
        if ent.label_ == "MACHINERY":
            val = ent.text.lower()
            lemma = ent[0].lemma_.lower() if len(ent) > 0 else val
            mapped = MACHINERY_MAP.get(lemma, MACHINERY_MAP.get(val, lemma))
            if mapped in MACHINERY:
                found_machinery.add(mapped)
            else:
                found_machinery.add(val)
    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in MACHINERY:
            found_machinery.add(MACHINERY_MAP.get(lemma, lemma))
        elif token.text.lower() in MACHINERY:
            found_machinery.add(MACHINERY_MAP.get(token.text.lower(), token.text.lower()))
    text_lower = doc.text.lower()
    for m in MACHINERY:
        if m in text_lower:
            found_machinery.add(MACHINERY_MAP.get(m, m))
    return list(sorted(found_machinery))

def detect_intent(doc) -> str:
    """
    Classifies intent of the query using token lemma matching against defined intent keywords.
    """
    scores = {intent: 0 for intent in INTENT_KEYWORDS}
    
 
    for token in doc:
        lemma = token.lemma_.lower()
        word = token.text.lower()
        
        for intent, keywords in INTENT_KEYWORDS.items():
            if lemma in keywords or word in keywords:
                scores[intent] += 1
                
    best_intent = max(scores, key=scores.get)
    

    if scores[best_intent] == 0:
        
        symptoms = extract_symptoms(doc)
        if symptoms:
            return "disease diagnosis"
        return "general agriculture"
        
    return best_intent

def analyze_query(text: str) -> dict:
    
    doc = nlp(text)
    return {
        "crop": extract_crop(doc),
        "symptoms": extract_symptoms(doc),
        "fertilizer_details": extract_fertilizer_details(doc),
        "machinery_details": extract_machinery_details(doc),
        "intent": detect_intent(doc)
    }
