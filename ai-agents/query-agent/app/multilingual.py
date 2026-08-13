import re
import requests
from typing import Tuple


SINGLISH_DETECTION_KEYWORDS = {
    # Crops
    "thakkali", "thakkaali", "takali", "takkali", "wee", "vi", "badairingu", "badairingoo", "iringu", 
    "miris", "ala", "lunu", "luunu", "wambatu", "pipinna", "gammiris", "karot", "gowa", "pol", 
    "rabar", "kurundu", "wattakka", "bandakka", "bonchi", "elawalu", "pala",
    # Symptoms / Disease
    "kola", "kole", "kolawala", "kaha", "damburu", "dhumru", "lapa", "pulli", "kalu", "sudu", 
    "saththu", "satha", "sattu", "sata", "panuwo", "panuwa", "leda", "roge", "rogaya", "lele", 
    "merila", "karawela", "wawila", "kunu", "kunuwela", "surulana", "kurulana", "suruli", "paata",
    # Inputs / Market
    "wathura", "watura", "diya", "pohora", "poora", "pora", "mila", "ganan", "gana", "salli", 
    "dambulla", "pola", "beheth", "behet", "mardanaya", "palana", "prathikara",
    # Conversational / Helpers
    "mage", "wagawe", "wagawa", "thiyenawa", "tiyenawa", "thiyenne", "tiyenne", "thiyena", "tiyena", 
    "wela", "wenawa", "monawada", "monada", "monawd", "mokada", "mokakda", "kohomada", 
    "karanne", "karanna", "innawa", "innewa", "naha", "nehe"
}

SINGLISH_PHRASE_MAP = {
    "bada iringu": "maize",
    "bada iringoo": "maize",
    "bada-iringu": "maize",
    "badairingu": "maize",
    "badairingoo": "maize",
    "kaha pata": "yellow color",
    "kaha paata": "yellow color",
    "kaha paata wela": "yellow color has become",
    "kaha pata wela": "yellow color has become",
    "damburu lapa": "brown spots",
    "damburu pulli": "brown spots",
    "dhumru lapa": "brown spots",
    "dhumru pulli": "brown spots",
    "sudu pata": "white color",
    "sudu paata": "white color",
    "sudu saththu": "white insects",
    "sudu pata saththu": "white insects",
    "sudu paata saththu": "white insects",
    "kola kurulana": "leaf curling",
    "kola surulana": "leaf curling",
    "kola suruli": "leaf curling",
    "kola curli": "leaf curling",
    "leaf curling": "leaf curling",
    "kole curling": "leaf curling",
    "kole kurulana": "leaf curling",
    "kole surulana": "leaf curling",
    "kole suruli": "leaf curling",
    "wee wagawa": "rice cultivation",
    "vi wagawa": "rice cultivation",
    "paddy wagawa": "rice cultivation",
    "wee wagawe": "rice cultivation",
    "vi wagawe": "rice cultivation",
    "paddy wagawe": "rice cultivation",
    "thakkali wagawa": "tomato cultivation",
    "thakkali wagawe": "tomato cultivation",
    "thakkaali wagawa": "tomato cultivation",
    "thakkaali wagawe": "tomato cultivation",
}


SINGLISH_WORD_MAP = {
    # Crops
    "thakkali": "tomato",
    "thakkaali": "tomato",
    "takkali": "tomato",
    "takali": "tomato",
    "wee": "rice",
    "vi": "rice",
    "iringu": "maize",
    "miris": "chili",
    "ala": "potato",
    "lunu": "onion",
    "luunu": "onion",
    "wambatu": "brinjal",
    "pipinna": "cucumber",
    "gammiris": "pepper",
    "karot": "carrot",
    "gowa": "cabbage",
    "they": "tea",
    "pol": "coconut",
    "rabar": "rubber",
    "kurundu": "cinnamon",
    "beet": "beetroot",
    "wattakka": "pumpkin",
    "bandakka": "okra",
    "leeks": "leek",
    "bonchi": "bean",
    "bona": "bean",
    
    # Parts of plant
    "kola": "leaves",
    "kole": "leaf",
    "kolawala": "leaves",
    "patra": "leaves",
    "kola-wala": "leaves",
    "kole-wala": "leaves",
    "atta": "branch",
    "athu": "branches",
    "mula": "root",
    "mul": "roots",
    "mal": "flowers",
    "mala": "flower",
    "karal": "pods",
    "wala": "in",
    "eke": "on",
    "eka": "the",
    "eth": "on",
    
    # Symptoms / Colors / Diseases
    "kaha": "yellow",
    "damburu": "brown",
    "dhumru": "brown",
    "lapa": "spots",
    "pulli": "spots",
    "kalu": "black",
    "sudu": "white",
    "saththu": "insects",
    "satha": "insect",
    "sattu": "insects",
    "sata": "insect",
    "kuda": "insects",
    "koodo": "insects",
    "kudi": "insects",
    "panuwo": "worms",
    "panuwa": "worm",
    "leda": "disease",
    "lele": "disease",
    "roge": "disease",
    "rogaya": "disease",
    "rogi": "disease",
    "merila": "died",
    "karawela": "wilted",
    "wawila": "wilted",
    "kunu": "rot",
    "kunuwela": "rotted",
    "surulana": "curling",
    "kurulana": "curling",
    "suruli": "curling",
    "pata": "color",
    "paata": "color",
    "dada": "spots",
    "wilt": "wilt",
    "halila": "fallen",
    "halena": "falling",
    "nil":"Blue",
    
    # Irrigation / Fertilization / Market
    "wathura": "water",
    "watura": "water",
    "diya": "water",
    "pohora": "fertilizer",
    "poora": "fertilizer",
    "pora": "fertilizer",
    "mila": "price",
    "ganan": "price",
    "gana": "price",
    "salli": "money",
    "dambulla": "dambulla",
    "pola": "market",
    "beheth": "treatment",
    "behet": "treatment",
    "mardanaya": "control",
    "palana": "control",
    "prathikara": "treatment",
    
    # Conversational / Pronouns / Helpers
    "mage": "my",
    "wagawe": "cultivation",
    "wagawa": "cultivation",
    "thiyenawa": "is",
    "tiyenawa": "is",
    "thiyenne": "is",
    "tiyenne": "is",
    "thiyena": "is",
    "tiyena": "is",
    "wela": "become",
    "wenawa": "become",
    "monawada": "what",
    "monada": "what",
    "monawd": "what",
    "mokada": "what",
    "mokakda": "what",
    "kohomada": "how",
    "karanne": "do",
    "karanna": "do",
    "innawa": "is",
    "innewa": "is",
    "naha": "not",
    "nehe": "not",
    "hulan": "wind",
    "awula": "problem",
    "prasnaya": "problem",
    "prasne": "problem",
    "dumi": "smoke",
    "dum": "smoke"
}



SINHALA_PHRASE_MAP = {
    "බඩ ඉරිඟු": "maize",
    "බඩ ඉරිගු": "maize",
    "කහ පාට වෙලා": "yellow color has become",
    "කහ පාට": "yellow color",
    "දුඹුරු ලප": "brown spots",
    "දුඹුරු පුල්ලි": "brown spots",
    "සුදු පාට සත්තු": "white insects",
    "සුදු සත්තු": "white insects",
    "සුදු පාට": "white color",
    "කොළ හැකිලීම": "leaf curling",
    "කොළ හැකිලෙන": "leaf curling",
    "කොළ සුරුලන": "leaf curling",
    "කොළ කුරුලන": "leaf curling",
    "වී වගාවේ": "rice cultivation",
    "වී වගාව": "rice cultivation",
    "තක්කාලි වගාවේ": "tomato cultivation",
    "තක්කාලි වගාව": "tomato cultivation",
}


SINHALA_WORD_MAP = {
    # Crops
    "තක්කාලි": "tomato",
    "වී": "rice",
    "බඩඉරිඟු": "maize",
    "බඩඉරිගු": "maize",
    "මිරිස්": "chili",
    "අල": "potato",
    "ලූණු": "onion",
    "ලූනු": "onion",
    "වම්බටු": "brinjal",
    "පිපිඤ්ඤා": "cucumber",
    "ගම්මිරිස්": "pepper",
    "කැරට්": "carrot",
    "ගෝවා": "cabbage",
    "තේ": "tea",
    "පොල්": "coconut",
    "රබර්": "rubber",
    "කුරුඳු": "cinnamon",
    "බීට්": "beetroot",
    "වට්ටක්කා": "pumpkin",
    "බණ්ඩක්කා": "okra",
    "ලීක්ස්": "leek",
    "බෝංචි": "bean",
    
    # Parts of plant
    "කොළ": "leaves",
    "කොළය": "leaf",
    "කොලේ": "leaf",
    "පත්‍රය": "leaf",
    "පත්‍ර": "leaves",
    "පත්තර": "leaves",
    "අත්ත": "branch",
    "අතු": "branches",
    "මුල": "root",
    "මුල්": "roots",
    "මල්": "flowers",
    "මල": "flower",
    "කරල්": "pods",
    "වල": "in",
    "තුළ": "in",
    "තුල": "in",
    "උඩ": "on",
    "මත": "on",
    "ගැන": "about",
    
    # Symptoms / Colors / Diseases
    "කහ": "yellow",
    "දුඹුරු": "brown",
    "ලප": "spots",
    "පුල්ලි": "spots",
    "කළු": "black",
    "කලු": "black",
    "සුදු": "white",
    "සත්තු": "insects",
    "සතා": "insect",
    "පණුවෝ": "worms",
    "පනුවෝ" : "worms",
    "පණුවා": "worm",
    "පනුවා": "worm",
    "ලෙඩ": "disease",
    "ලෙඩක්": "disease",
    "රෝග": "disease",
    "රෝගය": "disease",
    "රෝගී": "disease",
    "මැරිලා": "died",
    "කරවෙලා": "wilted",
    "මැලවිලා": "wilted",
    "කුණු": "rot",
    "කුනු": "rot",
    "කුණුවෙලා": "rotted",
    "කුනුවෙලා": "rotted",
    "හැකිලෙන": "curling",
    "හැකිලීම": "curling",
    "සුරුලන": "curling",
    "කුරුලන": "curling",
    "පාට": "color",
    "වැටිලා": "fallen",
    "හැලෙන": "falling",
    
    # Inputs / Market / Conversational
    "වතුර": "water",
    "දිය": "water",
    "පොහොර": "fertilizer",
    "මිල": "price",
    "ගණන්": "price",
    "ගනන්": "price",
    "සල්ලි": "money",
    "බෙහෙත්": "treatment",
    "මර්ධනය": "control",
    "මර්දනය": "control",
    "පාලනය": "control",
    "ප්‍රතිකාර": "treatment",
    "මගේ": "my",
    "වගාවේ": "cultivation",
    "wagawa": "cultivation",
    "වගාව": "cultivation",
    "තියෙනවා": "is",
    "තියෙන්නේ": "is",
    "වෙලා": "become",
    "වෙනවා": "become",
    "මොනවාද": "what",
    "මොනවද": "what",
    "මොකද": "what",
    "මොකක්ද": "what",
    "කොහොමද": "how",
    "කරන්නේ": "do",
    "කරන්න": "do",
    "ඉන්නවා": "is",
    "ඉන්නෙ": "is",
    "නැහැ": "not",
    "නැහැනේ": "not",
    "සුළඟ": "wind",
    "අවුල": "problem",
    "ප්‍රශ්නය": "problem",
    "දුම": "smoke",
    "කීයද": "how much",
    "කීය": "how much"
}


def detect_language(text: str) -> str:
  
    
    if re.search(r"[\u0d80-\u0dff]", text):
        return "si"
        
    
    text_lower = text.lower()
    words = re.findall(r"\b\w+\b", text_lower)
    singlish_matches = sum(1 for w in words if w in SINGLISH_DETECTION_KEYWORDS)
    
    if singlish_matches >= 1:
        return "singlish"
        
    return "en"


def translate_singlish(text: str) -> str:
    
    text_lower = text.lower()
    

    for phrase in sorted(SINGLISH_PHRASE_MAP.keys(), key=len, reverse=True):
        text_lower = text_lower.replace(phrase, SINGLISH_PHRASE_MAP[phrase])
        
   
    tokens = re.findall(r"\w+|[^\w\s]", text_lower, re.UNICODE)
    translated_tokens = []
    
    for token in tokens:
        if token.isalnum():
         
            translated_tokens.append(SINGLISH_WORD_MAP.get(token, token))
        else:
            translated_tokens.append(token)
            

    translated_text = " ".join(translated_tokens)
    translated_text = re.sub(r"\s+([^\w\s])", r"\1", translated_text)
    return translated_text


def translate_sinhala_script(text: str) -> str:
   
    text_lower = text
    
   
    for phrase in sorted(SINHALA_PHRASE_MAP.keys(), key=len, reverse=True):
        eng = SINHALA_PHRASE_MAP[phrase]
        text_lower = text_lower.replace(phrase, eng)
        

    tokens = re.findall(r"[\u0d80-\u0dff\w]+|[^\u0d80-\u0dff\w\s]", text_lower, re.UNICODE)
    translated_tokens = []
    
    for token in tokens:
        if token in SINHALA_WORD_MAP:
            translated_tokens.append(SINHALA_WORD_MAP[token])
        else:
            translated_tokens.append(token)
            
    # Reassemble and clean up spaces before punctuation
    translated_text = " ".join(translated_tokens)
    translated_text = re.sub(r"\s+([^\w\s])", r"\1", translated_text)
    return translated_text


def translate_google(text: str, source_lang: str) -> str:
    
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": source_lang,
        "tl": "en",
        "dt": "t",
        "q": text
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        translated_segments = [segment[0] for segment in result[0] if segment[0]]
        return "".join(translated_segments)
    except Exception as e:
     
        return text


def translate_to_english(text: str, lang: str) -> str:
  
    if lang == "si":
        
        local_translated = translate_sinhala_script(text)
        
      
        if not re.search(r"[\u0d80-\u0dff]", local_translated):
            return local_translated
            
   
        google_translated = translate_google(text, "si")
        if google_translated != text:
            return google_translated
            
  
        return local_translated
        
    elif lang == "singlish":
        return translate_singlish(text)
        
    return text
