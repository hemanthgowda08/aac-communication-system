"""Small SQLite-backed API for the Saathi AAC demo."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from flask import Flask, g, jsonify, request

ROOT = Path(__file__).resolve().parent
SEED_FILE = ROOT / "seed.json"
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS categories (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, icon TEXT NOT NULL, color TEXT NOT NULL, position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
  id TEXT PRIMARY KEY, category_id TEXT NOT NULL REFERENCES categories(id), emoji TEXT NOT NULL,
  en TEXT NOT NULL, hi TEXT NOT NULL, kn TEXT NOT NULL, position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS preferences (
  id INTEGER PRIMARY KEY CHECK(id=1), language TEXT NOT NULL DEFAULT 'en', speed REAL NOT NULL DEFAULT 1,
  high_contrast INTEGER NOT NULL DEFAULT 0, large_text INTEGER NOT NULL DEFAULT 0, favorite_categories TEXT NOT NULL DEFAULT '["needs","health"]'
);
CREATE TABLE IF NOT EXISTS saved_phrases (
  id TEXT PRIMARY KEY, text TEXT NOT NULL, normalized_text TEXT NOT NULL UNIQUE, translations TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS item_usage (
  item_id TEXT PRIMARY KEY REFERENCES items(id) ON DELETE CASCADE, uses INTEGER NOT NULL DEFAULT 0 CHECK(uses >= 0), last_used TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS phrase_usage (
  phrase_id TEXT PRIMARY KEY REFERENCES saved_phrases(id) ON DELETE CASCADE, uses INTEGER NOT NULL DEFAULT 0 CHECK(uses >= 0), last_used TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect_db(path: str) -> sqlite3.Connection:
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 5000")
    return db


def initialize_database(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_db(path)) as db, db:
        db.executescript(SCHEMA)
        seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
        for index, cat in enumerate(seed["categories"]):
            db.execute("INSERT OR IGNORE INTO categories(id,name,icon,color,position) VALUES(?,?,?,?,?)",
                       (cat["id"], cat["name"], cat["icon"], cat["color"], index))
        for index, item in enumerate(seed["items"]):
            db.execute("INSERT OR IGNORE INTO items(id,category_id,emoji,en,hi,kn,position) VALUES(?,?,?,?,?,?,?)",
                       (item["id"], item["category"], item["emoji"], item["en"], item["hi"], item["kn"], index))
        db.execute("INSERT OR IGNORE INTO preferences(id,favorite_categories) VALUES(1,'[\"needs\",\"health\"]')")
        for phrase in seed["starterPhrases"]:
            db.execute("INSERT OR IGNORE INTO saved_phrases(id,text,normalized_text,translations) VALUES(?,?,?,?)",
                       (phrase["id"], phrase["text"], phrase["text"].casefold(), json.dumps(phrase.get("translations", {}), ensure_ascii=False)))


def make_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("AAC_DATABASE", str(ROOT / "saathi.sqlite3")),
        CORS_ORIGINS=os.environ.get("AAC_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
        MAX_CONTENT_LENGTH=16_384,
        DEBUG=os.environ.get("AAC_DEBUG", "0") == "1",
    )
    if test_config:
        app.config.update(test_config)

    @app.before_request
    def setup_db() -> None:
        if not Path(app.config["DATABASE"]).exists():
            initialize_database(app.config["DATABASE"])
        g.db = connect_db(app.config["DATABASE"])

    @app.teardown_request
    def close_db(_error: BaseException | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.after_request
    def cors(response):
        origin = request.headers.get("Origin")
        allowed = [item.strip() for item in app.config["CORS_ORIGINS"] if item.strip()]
        if origin and origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Max-Age"] = "600"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="Request body is too large."), 413

    @app.errorhandler(400)
    def bad_request(_error):
        return jsonify(error="Invalid request."), 400

    @app.errorhandler(500)
    def server_error(_error):
        app.logger.exception("Unhandled API error")
        return jsonify(error="The server could not complete this request."), 500

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="The requested API resource was not found."), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify(error="That method is not supported for this resource."), 405

    def body() -> dict[str, Any]:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")
        return data

    def error(message: str, status: int = 400):
        return jsonify(error=message), status

    @app.get("/api/health")
    def health():
        g.db.execute("SELECT 1")
        return jsonify(status="ok", database="connected")

    @app.get("/api/categories")
    def categories():
        rows = g.db.execute("SELECT id,name,icon,color FROM categories ORDER BY position").fetchall()
        return jsonify([dict(row) for row in rows])

    @app.get("/api/items")
    def items():
        rows = g.db.execute("SELECT id,category_id AS category,emoji,en,hi,kn FROM items ORDER BY position").fetchall()
        return jsonify([dict(row) for row in rows])

    @app.get("/api/phrases")
    def phrases():
        rows = g.db.execute("SELECT id,text,translations,created_at FROM saved_phrases ORDER BY created_at DESC,rowid DESC").fetchall()
        return jsonify([{**dict(row), "translations": json.loads(row["translations"])} for row in rows])

    @app.post("/api/phrases")
    def create_phrase():
        try:
            data = body()
            text = data.get("text")
            translations = data.get("translations", {})
            if not isinstance(text, str) or not text.strip() or len(text.strip()) > 500:
                return error("Phrase text must contain 1 to 500 characters.")
            if not isinstance(translations, dict) or len(translations) > 8 or any(not isinstance(k, str) or not isinstance(v, str) or len(v) > 500 for k, v in translations.items()):
                return error("Translations must be an object with short text values.")
            normalized = " ".join(text.split()).casefold()
            current = g.db.execute("SELECT id,text,translations,created_at FROM saved_phrases WHERE normalized_text=?", (normalized,)).fetchone()
            if current:
                return jsonify({**dict(current), "translations": json.loads(current["translations"]), "duplicate": True}), 200
            phrase_id = "phrase-" + __import__("uuid").uuid4().hex
            g.db.execute("INSERT INTO saved_phrases(id,text,normalized_text,translations) VALUES(?,?,?,?)", (phrase_id, text.strip(), normalized, json.dumps(translations, ensure_ascii=False)))
            g.db.commit()
            row = g.db.execute("SELECT id,text,translations,created_at FROM saved_phrases WHERE id=?", (phrase_id,)).fetchone()
            return jsonify({**dict(row), "translations": json.loads(row["translations"])}), 201
        except ValueError as exc:
            return error(str(exc))

    @app.delete("/api/phrases/<phrase_id>")
    def delete_phrase(phrase_id: str):
        cursor = g.db.execute("DELETE FROM saved_phrases WHERE id=?", (phrase_id,))
        g.db.commit()
        if cursor.rowcount == 0:
            return error("Phrase not found.", 404)
        return jsonify(deleted=True)

    @app.get("/api/preferences")
    def get_preferences():
        row = g.db.execute("SELECT language,speed,high_contrast,large_text,favorite_categories FROM preferences WHERE id=1").fetchone()
        return jsonify(language=row["language"], speed=row["speed"], contrast=bool(row["high_contrast"]), large=bool(row["large_text"]), favorites=json.loads(row["favorite_categories"]))

    @app.put("/api/preferences")
    def put_preferences():
        try:
            data = body()
            current = {"language": "en", "speed": 1.0, "contrast": False, "large": False, "favorites": []}
            row = g.db.execute("SELECT language,speed,high_contrast,large_text,favorite_categories FROM preferences WHERE id=1").fetchone()
            if row:
                current = {"language": row["language"], "speed": row["speed"], "contrast": bool(row["high_contrast"]), "large": bool(row["large_text"]), "favorites": json.loads(row["favorite_categories"])}
            current.update({key: data[key] for key in current if key in data})
            if current["language"] not in ("en", "hi", "kn"):
                return error("Language must be en, hi, or kn.")
            if isinstance(current["speed"], bool) or not isinstance(current["speed"], (int, float)) or not 0.5 <= current["speed"] <= 2:
                return error("Speech speed must be between 0.5 and 2.")
            if not isinstance(current["contrast"], bool) or not isinstance(current["large"], bool):
                return error("Accessibility preferences must be true or false.")
            categories = {row[0] for row in g.db.execute("SELECT id FROM categories")}
            if not isinstance(current["favorites"], list) or len(set(current["favorites"])) != len(current["favorites"]) or any(value not in categories for value in current["favorites"]):
                return error("Favorite categories contain an invalid category.")
            g.db.execute("UPDATE preferences SET language=?,speed=?,high_contrast=?,large_text=?,favorite_categories=? WHERE id=1",
                         (current["language"], current["speed"], int(current["contrast"]), int(current["large"]), json.dumps(current["favorites"])))
            g.db.commit()
            return jsonify(current)
        except ValueError as exc:
            return error(str(exc))

    @app.get("/api/usage")
    def get_usage():
        result = {row["item_id"]: row["uses"] for row in g.db.execute("SELECT item_id,uses FROM item_usage")}
        result.update({row["phrase_id"]: row["uses"] for row in g.db.execute("SELECT phrase_id,uses FROM phrase_usage")})
        return jsonify(result)

    @app.post("/api/usage")
    def record_usage():
        try:
            data = body()
            item_id, phrase_id = data.get("item_id"), data.get("phrase_id")
            increment = data.get("increment", 1)
            if bool(item_id) == bool(phrase_id) or not all(value is None or isinstance(value, str) for value in (item_id, phrase_id)):
                return error("Provide exactly one item_id or phrase_id.")
            if isinstance(increment, bool) or not isinstance(increment, int) or not 1 <= increment <= 1000:
                return error("Usage increment must be a whole number from 1 to 1000.")
            if item_id:
                exists = g.db.execute("SELECT 1 FROM items WHERE id=?", (item_id,)).fetchone()
                if not exists:
                    return error("AAC item not found.", 404)
                g.db.execute("INSERT INTO item_usage(item_id,uses) VALUES(?,?) ON CONFLICT(item_id) DO UPDATE SET uses=uses+excluded.uses,last_used=CURRENT_TIMESTAMP", (item_id, increment))
            else:
                exists = g.db.execute("SELECT 1 FROM saved_phrases WHERE id=?", (phrase_id,)).fetchone()
                if not exists:
                    return error("Phrase not found.", 404)
                g.db.execute("INSERT INTO phrase_usage(phrase_id,uses) VALUES(?,?) ON CONFLICT(phrase_id) DO UPDATE SET uses=uses+excluded.uses,last_used=CURRENT_TIMESTAMP", (phrase_id, increment))
            g.db.commit()
            return jsonify(recorded=True), 201
        except ValueError as exc:
            return error(str(exc))

    @app.get("/api/suggestions")
    def suggestions():
        from backend.recommend import recommend
        message = request.args.get("message", "")
        language = request.args.get("language", "en")
        if len(message) > 500 or language not in ("en", "hi", "kn"):
            return error("Message is limited to 500 characters and language must be en, hi, or kn.")
        result = recommend(message, language)
        usage = {row["item_id"]: row["uses"] for row in g.db.execute("SELECT item_id,uses FROM item_usage")}
        for item in result:
            item["_usage"] = usage.get(item["id"], 0)
        key = " ".join(message.casefold().split())
        if key:
            rows = g.db.execute("SELECT p.id,p.text,p.translations,u.uses FROM saved_phrases p JOIN phrase_usage u ON u.phrase_id=p.id WHERE u.uses>0 ORDER BY u.uses DESC,p.text COLLATE NOCASE").fetchall()
            for row in rows:
                translations = json.loads(row["translations"])
                candidates = [row["text"], *translations.values()]
                if any(key in " ".join(candidate.casefold().split()) for candidate in candidates):
                    result.append({"id": row["id"], "text": row["text"], "translations": translations,
                                   "label": translations.get(language, row["text"]), "emoji": "💬", "type": "phrase", "_usage": row["uses"]})
        result.sort(key=lambda item: item.get("_usage", 0), reverse=True)
        return jsonify(result)

    @app.route("/api/<path:_path>", methods=["OPTIONS"])
    def options(_path: str):
        return "", 204

    return app


app = make_app()

if __name__ == "__main__":
    database = app.config["DATABASE"]
    initialize_database(database)
    app.run(host=os.environ.get("AAC_HOST", "127.0.0.1"), port=int(os.environ.get("AAC_PORT", "5000")), debug=app.config["DEBUG"])
