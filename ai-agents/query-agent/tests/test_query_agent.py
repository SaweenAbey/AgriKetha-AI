import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.nlp import analyze_query, extract_crop, extract_symptoms, detect_intent, nlp


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

        doc_general = nlp("Good morning, how does crop rotation work?")
        self.assertEqual(detect_intent(doc_general), "general agriculture")


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


if __name__ == "__main__":
    unittest.main()
