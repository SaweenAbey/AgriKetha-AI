import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.nlp import analyze_query, extract_crop, extract_symptoms, detect_intent, nlp
from app.multilingual import detect_language, translate_to_english, translate_singlish, translate_sinhala_script, translate_tamil_script


class TestNLPProcessing(unittest.TestCase):
    def test_crop_extraction(self):
        # Singular & plural matching
        doc_tomato = nlp("I have tomatoes growing in my garden")
        self.assertEqual(extract_crop(doc_tomato), "tomato")

        # Sri Lankan synonyms and mappings
        doc_paddy = nlp("my paddy field is dry")
        self.assertEqual(extract_crop(doc_paddy), "rice")
        
        doc_eggplant = nlp("eggplant leaves are yellow")
        self.assertEqual(extract_crop(doc_eggplant), "brinjal")

        # Multi-word phrase mapping
        doc_ladies = nlp("caterpillars are eating my ladies' fingers")
        self.assertEqual(extract_crop(doc_ladies), "okra")

        # Missing crop
        doc_none = nlp("the weather is quite hot today")
        self.assertIsNone(extract_crop(doc_none))

    def test_symptom_extraction(self):
        # Exact custom entity matches
        doc1 = nlp("my tomato leaves are becoming yellow and I see brown spots")
        symptoms1 = extract_symptoms(doc1)
        self.assertIn("yellow leaves", symptoms1)
        self.assertIn("brown spots", symptoms1)

        # Conversational / Dependency parser matches
        doc2 = nlp("the leaf of my brinjal plant has turned yellow")
        symptoms2 = extract_symptoms(doc2)
        self.assertIn("yellow leaves", symptoms2)

        doc3 = nlp("why is the potato leaves curling?")
        symptoms3 = extract_symptoms(doc3)
        self.assertIn("leaf curling", symptoms3)

        doc4 = nlp("there are some white flies on my plants")
        symptoms4 = extract_symptoms(doc4)
        self.assertIn("white insects", symptoms4)

    def test_intent_detection(self):
        doc_disease = nlp("My potato leaves are rotting and wilting")
        self.assertEqual(detect_intent(doc_disease), "disease diagnosis")

        doc_water = nlp("What is the best irrigation schedule for maize?")
        self.assertEqual(detect_intent(doc_water), "irrigation advice")

        doc_fertilizer = nlp("Should I apply nitrogen or compost to cabbage?")
        self.assertEqual(detect_intent(doc_fertilizer), "fertilizer advice")

        doc_market = nlp("What is the wholesale price of red onion at Dambulla market?")
        self.assertEqual(detect_intent(doc_market), "market information")

        doc_machinery = nlp("How to maintain a tractor seeder or water pump?")
        self.assertEqual(detect_intent(doc_machinery), "machinery operations")

        doc_general = nlp("Good morning, how does crop rotation work?")
        self.assertEqual(detect_intent(doc_general), "general agriculture")

    def test_fertilizer_extraction(self):
        from app.nlp import extract_fertilizer_details
        doc = nlp("I need to apply urea and compost fertilizer to my paddy field")
        fertilizers = extract_fertilizer_details(doc)
        self.assertIn("urea", fertilizers)
        self.assertIn("compost", fertilizers)
        self.assertIn("fertilizer", fertilizers)

    def test_machinery_extraction(self):
        from app.nlp import extract_machinery_details
        doc = nlp("Is it possible to plow the field using a hand tractor tiller?")
        machinery = extract_machinery_details(doc)
        self.assertIn("plow", machinery)
        self.assertIn("tractor", machinery)
        self.assertIn("tiller", machinery)


class TestAgentAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_home_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["agent"], "Query Analysis & NLP Agent")

    def test_analyze_endpoint_valid(self):
        response = self.client.post("/analyze", json={"question": "my tomato leaves have brown spots"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["agent_1_result"]["crop"], "tomato")
        self.assertIn("brown spots", data["agent_1_result"]["symptoms"])

    def test_analyze_endpoint_fertilizer_and_machinery(self):
        response = self.client.post("/analyze", json={"question": "Should I add urea to rice or use a tractor for plowing?"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["agent_1_result"]["crop"], "rice")
        self.assertIn("urea", data["agent_1_result"]["fertilizer_details"])
        self.assertIn("tractor", data["agent_1_result"]["machinery_details"])
        self.assertIn("plow", data["agent_1_result"]["machinery_details"])

    def test_analyze_endpoint_sinhala(self):
        response = self.client.post("/analyze", json={"question": "මගේ තක්කාලි කොළ වල දුඹුරු ලප තියෙනවා"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["detected_language"], "si")
        self.assertEqual(data["agent_1_result"]["crop"], "tomato")
        self.assertIn("brown spots", data["agent_1_result"]["symptoms"])

    def test_analyze_endpoint_singlish(self):
        response = self.client.post("/analyze", json={"question": "mage thakkali kola kaha pata wela"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["detected_language"], "singlish")
        self.assertEqual(data["agent_1_result"]["crop"], "tomato")
        self.assertIn("yellow leaves", data["agent_1_result"]["symptoms"])

    def test_analyze_endpoint_tamil(self):
        response = self.client.post("/analyze", json={"question": "எனது தக்காளி இலையில் பழுப்பு புள்ளிகள் உள்ளன"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["detected_language"], "ta")
        self.assertEqual(data["agent_1_result"]["crop"], "tomato")
        self.assertIn("brown spots", data["agent_1_result"]["symptoms"])


class TestMultilingualProcessing(unittest.TestCase):
    def test_language_detection(self):
        self.assertEqual(detect_language("My tomato leaves have brown spots"), "en")
        self.assertEqual(detect_language("මගේ තක්කාලි කොළ වල දුඹුරු ලප තියෙනවා"), "si")
        self.assertEqual(detect_language("mage thakkali kola wala damburu lapa thiyenawa"), "singlish")
        self.assertEqual(detect_language("wee wagawe thiyena leda monawada"), "singlish")
        self.assertEqual(detect_language("තක්කාලි මිල කීයද"), "si")
        self.assertEqual(detect_language("thakkali mila kohomada"), "singlish")
        self.assertEqual(detect_language("எனது தக்காளி இலையில் பழுப்பு புள்ளிகள் உள்ளன"), "ta")
        self.assertEqual(detect_language("தக்காளி விலை எவ்வளவு"), "ta")

    def test_singlish_translation(self):
        self.assertIn("tomato", translate_singlish("thakkali"))
        self.assertIn("leaves", translate_singlish("kola"))
        self.assertIn("yellow", translate_singlish("kaha"))
        self.assertIn("disease", translate_singlish("leda"))
        self.assertIn("price", translate_singlish("mila"))
        
        translated = translate_singlish("mage thakkali kola wala damburu lapa thiyenawa")
        self.assertIn("tomato", translated)
        self.assertIn("leaves", translated)
        self.assertIn("brown spots", translated)

        translated_fert = translate_singlish("yuriya pohora danna oni")
        self.assertIn("urea", translated_fert)
        self.assertIn("fertilizer", translated_fert)

        translated_mach = translate_singlish("traktharaya wikunanne kohomada")
        self.assertIn("tractor", translated_mach)

    def test_pure_sinhala_translation(self):
        self.assertIn("tomato", translate_sinhala_script("තක්කාලි"))
        self.assertIn("leaves", translate_sinhala_script("කොළ"))
        self.assertIn("yellow", translate_sinhala_script("කහ"))
        
        translated = translate_sinhala_script("මගේ තක්කාලි කොළ වල දුඹුරු ලප තියෙනවා")
        self.assertIn("tomato", translated)
        self.assertIn("leaves", translated)
        self.assertIn("brown spots", translated)

        translated_fert = translate_sinhala_script("යූරියා පොහොර දාන්න ඕනෙ")
        self.assertIn("urea", translated_fert)
        self.assertIn("fertilizer", translated_fert)

        translated_mach = translate_sinhala_script("ට්‍රැක්ටරයෙන් හාන්න")
        self.assertIn("tractor", translated_mach)
        self.assertIn("plow", translated_mach)

    def test_sinhala_translation(self):
        translated = translate_to_english("මගේ තක්කාලි කොළ වල දුඹුරු ලප තියෙනවා", "si")
        self.assertIn("tomato", translated.lower())
        self.assertIn("brown", translated.lower())

    def test_pure_tamil_translation(self):
        self.assertIn("tomato", translate_tamil_script("தக்காளி"))
        self.assertIn("leaves", translate_tamil_script("இலைகள்"))
        self.assertIn("yellow", translate_tamil_script("மஞ்சள்"))
        
        translated = translate_tamil_script("எனது தக்காளி இலையில் பழுப்பு புள்ளிகள் உள்ளன")
        self.assertIn("tomato", translated)
        self.assertIn("leaf", translated)
        self.assertIn("brown spots", translated)

        translated_fert = translate_tamil_script("யூரியா உரம் போட வேண்டும்")
        self.assertIn("urea", translated_fert)
        self.assertIn("fertilizer", translated_fert)

        translated_mach = translate_tamil_script("டிராக்டர் உழுதல் எப்படி")
        self.assertIn("tractor", translated_mach)
        self.assertIn("plowing", translated_mach)

    def test_tamil_translation(self):
        translated = translate_to_english("எனது தக்காளி இலையில் பழுப்பு புள்ளிகள் உள்ளன", "ta")
        self.assertIn("tomato", translated.lower())
        self.assertIn("brown", translated.lower())


if __name__ == "__main__":
    unittest.main()
