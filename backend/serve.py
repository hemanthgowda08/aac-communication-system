"""Production WSGI entry point. Build the Vite client before serving."""
import os

from waitress import serve

from backend.app import app, initialize_database

initialize_database(app.config["DATABASE"])
serve(app, host=os.environ.get("AAC_HOST", "127.0.0.1"), port=int(os.environ.get("AAC_PORT", "5000")), threads=4)
