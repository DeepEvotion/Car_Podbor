"""Flask entry point for CarMatch."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .db import Database
from .interview import FIELDS, interview, provider_settings
from .photos import find_photo
from . import recommender
from .recommender import apply_duel_choice, choose_duel, normalize_profile, recommend

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
CATALOG_VERSION = recommender.CATALOG_VERSION


def load_local_settings() -> None:
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            name, separator, value = line.partition("=")
            if separator and name.strip() in {"AI_CHAT_URL", "AI_API_KEY", "AI_MODEL", "AI_PROVIDER", "SQLITE_PATH"}:
                os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


def create_app(database: Database | None = None) -> Flask:
    load_local_settings()
    db = database or Database()
    db.init()
    recommender.CATALOG = db.catalog()
    if len(recommender.CATALOG) < 60:
        # Existing SQLite files are upgraded on the next start.
        db.init()
        recommender.CATALOG = db.catalog()
    car_ids = {car["id"] for car in recommender.CATALOG}
    app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")
    app.config["DB"] = db

    def error(message, status=422, code="VALIDATION_ERROR"):
        return jsonify(error={"code": code, "message": message, "fields": {}}), status

    @app.get("/api/catalog")
    def catalog():
        return jsonify(catalogVersion=CATALOG_VERSION, cars=recommender.CATALOG)

    @app.get("/api/photos/<car_id>")
    def photo(car_id):
        if car_id not in car_ids:
            return error("Автомобиль не найден", 404, "NOT_FOUND")
        cached = db.photo(car_id)
        if cached:
            return jsonify(cached)
        result = find_photo(car_id)
        if result is None:
            return error("Фото для модели временно недоступно", 404, "PHOTO_NOT_FOUND")
        db.save_photo(car_id, result)
        return jsonify(result)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", catalog=len(recommender.CATALOG), aiConfigured=provider_settings() is not None)

    @app.get("/api/share/<token>")
    def get_share(token):
        share = db.share(token)
        if not share:
            return error("Ссылка недоступна", 404, "NOT_FOUND")
        return jsonify(items=share["items"])

    @app.post("/api/share")
    def create_share():
        body = request.get_json(silent=True) or {}
        items = body.get("items")
        statuses = {"интересно", "рассматриваю", "мечта", "владею"}
        if not isinstance(items, list) or not 1 <= len(items) <= len(car_ids):
            return error("Выберите автомобили для ссылки")
        visible = {}
        try:
            for item in items:
                if item["carId"] not in car_ids or item["status"] not in statuses:
                    return error("Проверьте автомобили и статусы")
                visible[item["carId"]] = {"carId": item["carId"], "status": item["status"]}
        except (KeyError, TypeError):
            return error("Проверьте автомобили и статусы")
        token, revoke_key = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
        db.create_share(token, revoke_key, list(visible.values()))
        return jsonify(token=token, revokeKey=revoke_key), 201

    @app.delete("/api/share/<token>")
    def delete_share(token):
        if not db.revoke_share(token, request.headers.get("X-Revoke-Key", "")):
            return error("Ссылка недоступна", 404, "NOT_FOUND")
        return "", 204

    @app.post("/api/recommendation")
    def recommendation():
        try:
            body = request.get_json(silent=True) or {}
            return jsonify(recommend(normalize_profile(body.get("profile", {})), mode=body.get("mode", "balance")))
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
            return error(str(exc) or "Проверьте заполненные поля")

    @app.post("/api/duels")
    def duels():
        try:
            body = request.get_json(silent=True) or {}
            profile, duel = choose_duel(normalize_profile(body.get("profile", {})))
            if "choice" in body:
                pair = [duel[side]["id"] for side in ("left", "right")] if duel else None
                if pair is None or body.get("pair") != pair or body["choice"] not in {"left", "right", "both", "none", "skip"}:
                    return error("Выберите ответ для текущей пары")
                profile, duel = choose_duel(apply_duel_choice(profile, duel, body["choice"]))
            return jsonify(profile=profile, duel=duel)
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            return error("Проверьте заполненные поля")

    @app.post("/api/ai/parse-profile")
    def parse_profile():
        text = (request.get_json(silent=True) or {}).get("text", "")
        if not isinstance(text, str) or len(text) > 2000:
            return error("Описание должно занимать не более 2000 символов")
        try:
            return jsonify(interview(text, initial=True))
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            return jsonify(interview(text, initial=True, answers={})), 200

    @app.post("/api/ai/questions")
    def questions():
        body = request.get_json(silent=True) or {}
        text, answered, answers = body.get("text", ""), body.get("answered", []), body.get("answers", {})
        if not isinstance(text, str) or len(text) > 2000 or not isinstance(answered, list) or not all(k in FIELDS for k in answered) or not isinstance(answers, dict):
            return error("Проверьте ответы анкеты")
        try:
            return jsonify(interview(text, normalize_profile(answers), tuple(dict.fromkeys(answered))))
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            return error("Не удалось обновить вопросы. Продолжите по локальному сценарию")

    @app.post("/api/auth/demo")
    def demo():
        body = request.get_json(silent=True) or {}
        presets = {
            "first-car": {"useCases": ["city"], "passengers": 2, "luggageClass": "small", "transmission": "automatic", "budget": {"min": 900000, "max": 2200000, "status": "provided"}, "mustHave": ["automatic"]},
            "family-travel": {"useCases": ["family", "travel"], "roadConditions": ["highway"], "passengers": 5, "luggageClass": "large", "transmission": "automatic", "budget": {"min": 2500000, "max": 6500000, "status": "provided"}, "mustHave": ["five_seats", "automatic"]},
            "heart-choice": {"useCases": ["city", "travel"], "passengers": 2, "luggageClass": "medium", "style": {"brightness": .9, "modernity": .7, "comfort": .4, "sportiness": .85, "practicality": .25, "status": .75, "compactness": .7, "technology": .6, "retro": .5}},
        }
        key = body.get("demoKey")
        if key not in presets:
            return error("Демо-профиль не найден", 404, "NOT_FOUND")
        result = recommend(presets[key])
        names = {"first-car": "Демо-первый автомобиль", "family-travel": "Демо-семья и путешествия", "heart-choice": "Демо-выбор сердцем"}
        garage = [{"carId": car["carId"], "status": "интересно", "note": ""} for car in result["candidates"][:3]]
        return jsonify(userId=f"demo-{key}", demoKey=key, displayName=names[key], isDemo=True, profile=result["profile"], recommendation=result, garage=garage)

    @app.post("/api/auth/demo/reset")
    def demo_reset():
        key = (request.get_json(silent=True) or {}).get("demoKey")
        if key not in {"first-car", "family-travel", "heart-choice"}:
            return error("Демо-профиль не найден", 404, "NOT_FOUND")
        return jsonify(status="reset", demoKey=key)

    @app.route("/", defaults={"path": "index.html"})
    @app.route("/<path:path>")
    def frontend(path):
        return send_from_directory(FRONTEND, path or "index.html")

    return app


if __name__ == "__main__":
    create_app().run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")), debug=False)
