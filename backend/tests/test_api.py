import tempfile
import unittest
from pathlib import Path

from backend.app import initialize_database, make_app


class SaathiApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        database = str(Path(self.temp.name) / "test.sqlite3")
        initialize_database(database)
        self.app = make_app({"TESTING": True, "DATABASE": database, "CORS_ORIGINS": ["http://localhost:5173"]})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_health_and_seeded_content(self):
        self.assertEqual(self.client.get("/api/health").json["status"], "ok")
        categories = self.client.get("/api/categories").json
        items = self.client.get("/api/items").json
        self.assertGreaterEqual(len(categories), 8)
        self.assertEqual(self.client.get("/api/preferences").json["favorites"], ["needs", "health"])
        self.assertTrue(any(item["id"] == "water" for item in items))
        self.assertTrue(any(item["id"] == "emergency" for item in items))

    def test_phrase_create_deduplicate_retrieve_and_delete(self):
        response = self.client.post("/api/phrases", json={"text": "I want a little water", "translations": {"hi": "मुझे थोड़ा पानी चाहिए"}})
        self.assertEqual(response.status_code, 201)
        phrase_id = response.json["id"]
        self.assertEqual(self.client.post("/api/phrases", json={"text": "  i WANT a little water  "}).json["id"], phrase_id)
        self.assertTrue(any(row["id"] == phrase_id for row in self.client.get("/api/phrases").json))
        self.assertEqual(self.client.delete(f"/api/phrases/{phrase_id}").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/phrases/{phrase_id}").status_code, 404)

    def test_phrase_validation_and_sql_payload(self):
        self.assertEqual(self.client.post("/api/phrases", json={"text": " "}).status_code, 400)
        self.assertEqual(self.client.post("/api/phrases", json={"text": "x" * 501}).status_code, 400)
        self.assertEqual(self.client.post("/api/phrases", json=["not", "an", "object"]).status_code, 400)
        self.assertEqual(self.client.get("/api/categories").status_code, 200)
        injection = self.client.delete("/api/phrases/%27%20OR%201%3D1")
        self.assertEqual(injection.status_code, 404)
        self.assertGreaterEqual(len(self.client.get("/api/phrases").json), 4)

    def test_preferences_validation_and_persistence(self):
        response = self.client.put("/api/preferences", json={"language": "hi", "speed": 0.8, "contrast": True, "large": True, "favorites": ["health", "needs"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/preferences").json["language"], "hi")
        self.assertEqual(self.client.put("/api/preferences", json={"language": "xx"}).status_code, 400)
        self.assertEqual(self.client.put("/api/preferences", json={"speed": 99}).status_code, 400)
        self.assertEqual(self.client.put("/api/preferences", json={"favorites": ["missing"]}).status_code, 400)

    def test_usage_is_persistent_and_personalizes_suggestions(self):
        self.assertEqual(self.client.post("/api/usage", json={"item_id": "missing"}).status_code, 404)
        self.assertEqual(self.client.post("/api/usage", json={"item_id": "water", "phrase_id": "both"}).status_code, 400)
        self.client.post("/api/usage", json={"item_id": "go"})
        self.client.post("/api/usage", json={"item_id": "go"})
        usage = self.client.get("/api/usage").json
        self.assertEqual(usage["go"], 2)
        suggestions = self.client.get("/api/suggestions?message=I%20want&language=en").json
        self.assertEqual(suggestions[0]["id"], "go")
        hindi = self.client.get("/api/suggestions?message=I%20want&language=hi").json
        self.assertEqual(hindi[0]["label"], "जाना")
        self.assertEqual(self.client.get("/api/suggestions?language=bad").status_code, 400)

    def test_frequently_used_saved_phrase_can_be_suggested(self):
        created = self.client.post("/api/phrases", json={"text": "I want a quiet room", "translations": {"hi": "मुझे शांत कमरा चाहिए"}}).json
        self.client.post("/api/usage", json={"phrase_id": created["id"], "increment": 3})
        suggestions = self.client.get("/api/suggestions?message=I%20want&language=hi").json
        phrase = next(item for item in suggestions if item.get("type") == "phrase")
        self.assertEqual(phrase["id"], created["id"])
        self.assertEqual(phrase["label"], "मुझे शांत कमरा चाहिए")

    def test_cors_is_allowlisted(self):
        allowed = self.client.get("/api/health", headers={"Origin": "http://localhost:5173"})
        blocked = self.client.get("/api/health", headers={"Origin": "https://unknown.example"})
        self.assertEqual(allowed.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")
        self.assertIsNone(blocked.headers.get("Access-Control-Allow-Origin"))


if __name__ == "__main__":
    unittest.main()
