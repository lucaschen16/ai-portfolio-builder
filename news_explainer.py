from flask import Blueprint, jsonify, request

from src.agents.news_explainer import NewsExplainerAgent

news_explainer_bp = Blueprint("news_explainer", __name__)


@news_explainer_bp.post("/api/explain")
def explain():
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400

    try:
        agent = NewsExplainerAgent()
        return jsonify(agent.run(question))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
