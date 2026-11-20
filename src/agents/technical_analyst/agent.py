"""Technical analyst and portfolio manager workflow."""

import json
import os
from typing import Literal, TypedDict

import anthropic
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field, ValidationError

from src.core.signals import compute_signals
from src.data_access.market_data import fetch_ohlcv, normalize_ticker


class AnalystState(TypedDict):
    ticker: str
    price_data: dict
    technical_analysis: dict
    analyst_report: dict
    portfolio_decision: dict
    trace: list[dict]


class AnalystReport(BaseModel):
    technical_verdict: Literal["bullish", "mixed_bullish", "neutral", "mixed_bearish", "bearish"]
    confidence: int = Field(ge=0, le=100)
    summary: str
    caution: str
    portfolio_role_hint: Literal["core_candidate", "satellite_candidate", "watchlist_candidate", "avoid_for_now"]
    watch_next: str | None = None


class PortfolioDecision(BaseModel):
    portfolio_action: Literal["include_core", "include_small", "watchlist", "avoid"]
    portfolio_role: Literal["core", "satellite", "watchlist", "none"]
    allocation_cap: float = Field(ge=0, le=0.15)
    decision_reason: str
    needs_more_review: bool
    suggestion: Literal["buy", "hold", "sell"] | None = None
    take_profit: float | None = None
    stop_loss: float | None = None
    risk_reward_ratio: float | None = None
    entry_note: str | None = None


def _client():
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def _model_report(task, inputs, schema):
    response = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        system=(task + " Return only a JSON object matching this schema. "
                "Use null for optional fields that the data cannot support. "
                + json.dumps(schema.model_json_schema())),
        messages=[{"role": "user", "content": json.dumps(inputs)}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return schema.model_validate_json(text).model_dump()


def _append_trace(state, name, detail):
    return state["trace"] + [{"name": name, "detail": detail, "status": "done"}]


def input_ticker_node(state):
    ticker = normalize_ticker(state["ticker"])
    return {"ticker": ticker, "trace": _append_trace(state, "Input", f"Normalized ticker to {ticker}.")}


def fetch_price_data_node(state):
    data = fetch_ohlcv(state["ticker"]) or {}
    detail = (f"Fetched {len(data['closes'])} days of price and volume data." if data
              else f"Could not retrieve enough price history for {state['ticker']}.")
    return {"price_data": data, "trace": _append_trace(state, "Fetch Data", detail)}


def technical_signal_engine_node(state):
    signals = compute_signals(state["price_data"]) if state["price_data"] else {}
    detail = "Skipped because price history is unavailable."
    if signals:
        detail = f"Trend: {signals['trend']['signal']}. Momentum: {signals['momentum']['signal']}."
    return {"technical_analysis": signals, "trace": _append_trace(state, "Signal Engine", detail)}


def technical_analyst_agent_node(state):
    signals = state["technical_analysis"]
    report = {}
    detail = "Skipped because technical signals are unavailable."
    if signals and not os.environ.get("ANTHROPIC_API_KEY"):
        detail = "Set ANTHROPIC_API_KEY to generate the analyst report."
    elif signals:
        trend = {k: v for k, v in signals["trend"].items() if not k.endswith("_series")}
        try:
            report = _model_report(
                "Interpret the supplied technical signals in two or three sentences. Identify the main risk and what to watch next.",
                {**signals, "trend": trend, "ticker": state["ticker"]}, AnalystReport,
            )
            report["ticker"] = state["ticker"]
            detail = f"Verdict: {report['technical_verdict']}."
        except ValidationError:
            detail = "The analyst returned an unreadable report."
            report = {
                "ticker": state["ticker"], "technical_verdict": "neutral", "confidence": 50,
                "summary": detail, "caution": "The technical interpretation needs review.",
                "portfolio_role_hint": "watchlist_candidate", "needs_more_review": True,
            }
        except anthropic.APIError:
            detail = "Claude is unavailable. Check your Anthropic API key and connection."
    return {"analyst_report": report, "trace": _append_trace(state, "Technical Analyst", detail)}


def portfolio_manager_node(state):
    decision = {}
    detail = "Skipped because an analyst report is unavailable."
    if state["analyst_report"].get("needs_more_review"):
        detail = "Portfolio decision deferred pending a valid analyst report."
    elif state["analyst_report"]:
        signals = state["technical_analysis"]
        try:
            decision = _model_report(
                "Use the analyst report and price levels to choose a portfolio role and allocation cap. Explain the decision briefly.",
                {"report": state["analyst_report"], "price": signals["current_price"], "levels": signals["levels"]},
                PortfolioDecision,
            )
            decision["ticker"] = state["ticker"]
            detail = f"Portfolio action: {decision['portfolio_action']}."
        except ValidationError:
            detail = "The manager returned an unreadable decision. Review is required."
            decision = {
                "ticker": state["ticker"], "portfolio_action": "watchlist", "portfolio_role": "watchlist",
                "allocation_cap": 0, "needs_more_review": True, "decision_reason": detail,
            }
        except anthropic.APIError:
            detail = "Claude is unavailable for the portfolio decision."
    return {"portfolio_decision": decision, "trace": _append_trace(state, "Portfolio Manager", detail)}


def render_ui_node(state):
    return {"trace": _append_trace(state, "Output", "Finished processing the ticker.")}


class TechnicalAnalystAgent:
    def __init__(self):
        graph = StateGraph(AnalystState)
        graph.add_sequence([
            ("input_ticker", input_ticker_node),
            ("fetch_price_data", fetch_price_data_node),
            ("technical_signal_engine", technical_signal_engine_node),
            ("technical_analyst_agent", technical_analyst_agent_node),
            ("portfolio_manager", portfolio_manager_node),
            ("render_ui", render_ui_node),
        ])
        graph.set_entry_point("input_ticker")
        graph.add_edge("render_ui", END)
        self.graph = graph.compile()

    def run(self, ticker: str) -> dict:
        return self.graph.invoke({"ticker": ticker, "trace": []})
