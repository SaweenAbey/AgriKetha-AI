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

def extract_crop(doc) -> str:
   

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
            
    
    text_lower = doc.text.lower()
    for crop in CROPS:
        if crop in text_lower:
            return CROP_MAP.get(crop, crop)
            
    if "ladies finger" in text_lower or "ladies' finger" in text_lower or "okra" in text_lower:
        return "okra"
        
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


    if "yellow" in text_lower and ("leaf" in text_lower or "leaves" in text_lower or "leafs" in text_lower):
        found_symptoms.append("yellow leaves")
    if ("brown" in text_lower or "dark" in text_lower or "black" in text_lower or "spotted" in text_lower) and ("spot" in text_lower or "mark" in text_lower):
        found_symptoms.append("brown spots")
    if ("curl" in text_lower or "wrinkle" in text_lower) and ("leaf" in text_lower or "leaves" in text_lower):
        found_symptoms.append("leaf curling")
    if "wilt" in text_lower or "droop" in text_lower or "dry" in text_lower:
        found_symptoms.append("wilting")
    if "white" in text_lower and ("insect" in text_lower or "bug" in text_lower or "fly" in text_lower or "flies" in text_lower or "whitefly" in text_lower or "whiteflies" in text_lower):
        found_symptoms.append("white insects")
        
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