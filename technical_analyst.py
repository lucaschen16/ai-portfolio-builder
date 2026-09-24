from flask import Blueprint, jsonify, request

# TODO 7: Import TechnicalAnalystAgent from src.agents.technical_analyst

technical_analyst_bp = Blueprint("technical_analyst", __name__)


@technical_analyst_bp.post("/api/analyze")
def analyze():
    data = request.get_json() or {}
    ticker = (data.get("ticker") or "").strip()

    if not ticker:
        return jsonify({"error": "ticker is required"}), 400

    # TODO 7: Replace the placeholder below with:
    # 1. agent = TechnicalAnalystAgent()
    # 2. result = agent.run(ticker)
    # 3. return jsonify(result)
    #
    # Wrap it in a try/except so errors return a JSON response:
    #   except Exception as e:
    #       return jsonify({"error": str(e)}), 500

    return jsonify({"error": "not implemented yet"}), 501
