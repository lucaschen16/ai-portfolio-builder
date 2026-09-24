"""
Class 3 — Technical Analyst Agent + Portfolio Manager v1

LangGraph flow (straight line, no branching):

  input_ticker → fetch_price_data → technical_signal_engine
    → technical_analyst_agent → portfolio_manager → render_ui → END
"""

import os
import json
from typing import TypedDict

import anthropic
from langgraph.graph import END, StateGraph

from src.data_access.market_data import normalize_ticker, fetch_ohlcv
from src.core.signals import compute_signals


# ── Shared state ─────────────────────────────────────────────────────
#
# This is the dictionary that travels through every node.
# Each node can read any field and return updates to specific fields.

class AnalystState(TypedDict):
    ticker: str                     # the stock symbol, e.g. "AAPL"
    price_data: dict                # raw OHLCV from Yahoo Finance
    technical_analysis: dict        # computed signals (trend, momentum, vol, levels)
    analyst_report: dict            # LLM interpretation of the signals
    portfolio_decision: dict        # portfolio manager output
    trace: list[dict]               # step-by-step trace for the UI


# ── Helpers ──────────────────────────────────────────────────────────

def _client():
    """Create an Anthropic client using the API key from .env"""
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def _append_trace(state: AnalystState, name: str, detail: str) -> list[dict]:
    """Add a step to the trace. Each node calls this to log what it did."""
    return state["trace"] + [{"name": name, "detail": detail, "status": "done"}]


# ── Node 1: Input (DONE — this is your example) ─────────────────────

def input_ticker_node(state: AnalystState) -> dict:
    """
    Normalize the user's input into a proper ticker symbol.
    For example: "apple" → "AAPL", "tsla" → "TSLA"
    """
    ticker = normalize_ticker(state["ticker"])
    return {
        "ticker": ticker,
        "trace": _append_trace(state, "Input", f"Normalized ticker to {ticker}."),
    }


# ── Node 2: Fetch price data ────────────────────────────────────────

def fetch_price_data_node(state: AnalystState) -> dict:
    """
    TODO 3: Fetch OHLCV data for the ticker.

    Steps:
    1. Call fetch_ohlcv(state["ticker"])
    2. If it returns None:
       - return {"price_data": {}, "trace": _append_trace(state, "Fetch Data", "Failed to fetch data for ...")}
    3. If it returns data:
       - return {"price_data": ohlcv, "trace": _append_trace(state, "Fetch Data", f"Fetched {len(ohlcv['closes'])} days of OHLCV data.")}

    Hint: look at input_ticker_node above for the pattern.
    """
    pass


# ── Node 3: Technical signal engine (deterministic — no LLM) ────────

def technical_signal_engine_node(state: AnalystState) -> dict:
    """
    TODO 4: Run the signal engine on the price data.

    Steps:
    1. If state["price_data"] is empty (falsy), skip:
       - return {"technical_analysis": {}, "trace": _append_trace(state, "Signal Engine", "Skipped — no price data available.")}
    2. Call compute_signals(state["price_data"])
    3. Store the result in "technical_analysis"
    4. Log the key signals in the trace, e.g.:
       f"Trend: {signals['trend']['signal']}, Momentum: {signals['momentum']['signal']}, ..."
    """
    pass


# ── Node 4: Technical analyst agent (LLM) ───────────────────────────

def technical_analyst_agent_node(state: AnalystState) -> dict:
    """
    TODO 5: Send the technical signals to Claude for interpretation.

    Steps:
    1. If state["technical_analysis"] is empty, skip (same pattern as above)
    2. Read the signals from state["technical_analysis"] (call it `ta`)
    3. Build a prompt string that includes:
       - the ticker and current price
       - all the signal values (MA20, MA50, RSI, volatility, support, resistance, volume)
       - instructions telling the LLM to return JSON in this structure:
         {
           "technical_verdict": "<bullish | mixed_bullish | neutral | mixed_bearish | bearish>",
           "confidence": <0-100>,
           "summary": "<2-3 sentence interpretation>",
           "caution": "<1 sentence risk note>",
           "portfolio_role_hint": "<core_candidate | satellite_candidate | watchlist_candidate | avoid_for_now>"
         }
    4. Call the LLM:
       response = _client().messages.create(
           model="claude-sonnet-4-6",
           max_tokens=400,
           messages=[{"role": "user", "content": prompt}],
       )
       text = response.content[0].text.strip()
    5. Parse the JSON:
       try:
           report = json.loads(text)
       except json.JSONDecodeError:
           report = {
               "technical_verdict": "neutral",
               "confidence": 50,
               "summary": text[:200],
               "caution": "Could not parse structured output.",
               "portfolio_role_hint": "watchlist_candidate",
           }
    6. Add the ticker to the report: report["ticker"] = state["ticker"]
    7. Return {"analyst_report": report, "trace": _append_trace(state, "Technical Analyst", f"Verdict: ...")}
    """
    pass


# ── Node 5: Portfolio manager v1 (LLM) ──────────────────────────────

def portfolio_manager_node(state: AnalystState) -> dict:
    """
    TODO 6: Send the analyst report to Claude for a portfolio decision.

    Same pattern as TODO 5, but:
    - Read from state["analyst_report"] (call it `ar`) and state["technical_analysis"] (call it `ta`)
    - Build a prompt that includes the verdict, confidence, summary, caution,
      role hint, and support/resistance levels
    - Ask Claude to return JSON in this structure:
      {
        "portfolio_action": "<include_core | include_small | watchlist | avoid>",
        "portfolio_role": "<core | satellite | watchlist | none>",
        "allocation_cap": <0.00 to 0.15>,
        "decision_reason": "<1-2 sentence explanation>",
        "needs_more_review": <true | false>
      }
    - Parse the JSON (with the same try/except fallback pattern)
    - Add decision["ticker"] = state["ticker"]
    - Return {"portfolio_decision": decision, "trace": ...}
    """
    pass


# ── Node 6: Render UI ───────────────────────────────────────────────

def render_ui_node(state: AnalystState) -> dict:
    """This just marks the end of the pipeline. Nothing to change here."""
    return {
        "trace": _append_trace(state, "Output", "Analysis complete. Ready for UI."),
    }


# ── Graph assembly ───────────────────────────────────────────────────

class TechnicalAnalystAgent:
    def __init__(self):
        graph = StateGraph(AnalystState)
        #TODO 7: Register all 6 nodes (input_ticker_node, fetch_price_data_node, technical_signal_engine_node, technical_analyst_agent_node, portfolio_manager_node, render_ui_node)
        # Register all 6 nodes
        

        # Set the starting point
        graph.set_entry_point("input_ticker")
        
        #TODO 8: Connect the nodes in the correct order (input_ticker → fetch_price_data → technical_signal_engine → technical_analyst_agent → portfolio_manager → render_ui → END) 
        # Connect nodes in order (straight line)
        

        self.graph = graph.compile()

    def run(self, ticker: str) -> dict:
        """Run the full graph from start to finish."""
        result = self.graph.invoke({
            "ticker": ticker,
            "price_data": {},
            "technical_analysis": {},
            "analyst_report": {},
            "portfolio_decision": {},
            "trace": [],
        })
        return {
            "ticker": result["ticker"],
            "price_data": result["price_data"],
            "technical_analysis": result["technical_analysis"],
            "analyst_report": result["analyst_report"],
            "portfolio_decision": result["portfolio_decision"],
            "trace": result["trace"],
        }
