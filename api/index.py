
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from sqlalchemy import text

from api.extensions import db
from api import models  # Mendaftarkan kelima model ke SQLAlchemy


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL")

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Budget Tracker API berhasil dijalankan!",
        "project": "Budget Tracker",
        "author": "Hazer Elkana",
        "status": "success"
    }), 200


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "API berjalan dengan baik"
    }), 200


@app.route("/api/health/db", methods=["GET"])
def database_health_check():
    if not database_url:
        return jsonify({
            "status": "error",
            "message": "DATABASE_URL belum dikonfigurasi"
        }), 500

    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return jsonify({
            "status": "success",
            "message": "Koneksi PostgreSQL berhasil"
        }), 200

    except Exception:
        app.logger.exception("Database connection failed")

        return jsonify({
            "status": "error",
            "message": "Koneksi database gagal. Periksa konfigurasi."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)

from api.routes import api_bp
app.register_blueprint(api_bp)