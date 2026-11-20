from flask import Blueprint, current_app, jsonify, request

from src.agents.technical_analyst import TechnicalAnalystAgent

technical_analyst_bp = Blueprint("technical_analyst", __name__)


@technical_analyst_bp.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True)
    ticker = data.get("ticker") if isinstance(data, dict) else None
    if not isinstance(ticker, str) or not ticker.strip():
        return jsonify({"error": "ticker is required"}), 400

    try:
        return jsonify(TechnicalAnalystAgent().run(ticker.strip()))
    except Exception:
        current_app.logger.exception("Ticker analysis failed")
        return jsonify({"error": "Ticker analysis failed. Please try again."}), 500
