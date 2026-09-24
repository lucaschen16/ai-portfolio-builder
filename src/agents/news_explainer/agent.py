import os
from typing import TypedDict

import anthropic
from langgraph.graph import END, StateGraph

from src.data_access.market_data import get_market_snapshot
from src.data_access.news_feed import get_news


class NewsExplainerState(TypedDict):
    question: str
    topic: str
    route: str
    route_label: str
    context: list[str]
    detailed_answer: str
    final_answer: str
    trace: list[dict]


TOPIC_ROUTES = {
    "stock": ("stock_expert", "Stock Expert"),
    "crypto": ("crypto_expert", "Crypto Expert"),
    "etf": ("etf_expert", "ETF Expert"),
    "beginner": ("beginner_expert", "Beginner Concept Expert"),
}


def _client():
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def _market_context(question: str, topic: str) -> list[str]:
    snapshot = get_market_snapshot(question, topic)
    articles = get_news(question, topic, limit=5)
    context = []
    if snapshot:
        context.append(
            f"Live market snapshot for {snapshot['ticker']}: ${snapshot['price']} "
            f"({snapshot['daily_change_pct']}% today, {snapshot['five_day_change_pct']}% over 5 days)."
        )
    for article in articles:
        title = article.get("title", "").strip()
        if title:
            context.append(f"{title} ({article.get('source', 'Google News')})")
    return context


def _append_trace(state: NewsExplainerState, name: str, detail: str) -> list[dict]:
    return state["trace"] + [{"name": name, "detail": detail, "status": "done"}]


def _classify_question(question: str) -> tuple[str, str]:
    lowered = question.lower().strip()
    if any(keyword in lowered for keyword in ("bitcoin", "btc", "ethereum", "eth", "crypto", "token", "solana")):
        return "crypto", "Detected crypto keywords, so the graph routed to the crypto branch."
    if any(keyword in lowered for keyword in ("etf", "exchange traded fund", "index fund", "spy", "qqq", "voo")):
        return "etf", "Detected ETF keywords, so the graph routed to the ETF branch."
    if any(keyword in lowered for keyword in ("what is", "how does", "explain", "beginner", "difference between", "why do investors")):
        return "beginner", "Detected a concept-style question, so the graph routed to the beginner branch."
    return "stock", "Defaulted to the stock branch for a company or price-move explanation."


def _generate_explanation(question: str, topic: str, headlines: list[str]) -> str:
    topic_notes = {
        "stock": "Focus on earnings, guidance, sector rotation, valuation, and macro sentiment when relevant.",
        "crypto": "Focus on crypto sentiment, risk appetite, regulation, liquidity, and major catalysts when relevant.",
        "etf": "Focus on ETF structure, diversification, index exposure, inflows/outflows, and fees when relevant.",
        "beginner": "Focus on definitions, intuition, and simple examples instead of jargon.",
    }
    context_block = "\n".join(f"- {headline}" for headline in headlines) if headlines else "- No recent headlines supplied."

    prompt = f"""You are the {topic} expert node in a finance LangGraph workflow.

User question:
{question}

Recent market headlines:
{context_block}

Instructions:
- Answer the user's question directly and in detail.
- Use the headlines only if they actually help.
- {topic_notes[topic]}
- Keep the tone clear and educational.
- Do not use markdown symbols like #, *, or **.
- Use these section labels exactly:
Direct Answer:
Key Drivers:
What To Watch:
Caveats:
"""

    response = _client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _simplify_explanation(question: str, topic: str, detailed_answer: str) -> str:
    prompt = f"""You are the simplifier node in a finance teaching workflow.

Question:
{question}

Topic:
{topic}

Detailed draft:
{detailed_answer}

Rewrite it for a beginner without making it shallow.

Instructions:
- Keep the answer detailed, but easier to read.
- Keep the tone warm and clear.
- Do not use markdown symbols like #, *, or **.
- Use these section labels exactly:
Quick Take:
Why It Happened:
What To Watch Next:
Beginner Note:
"""

    response = _client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def input_node(state: NewsExplainerState) -> dict:
    return {
        "trace": _append_trace(state, "Input", "Stored the user's question in graph state."),
    }


def classify_node(state: NewsExplainerState) -> dict:
    topic, detail = _classify_question(state["question"])
    route, route_label = TOPIC_ROUTES[topic]
    return {
        "topic": topic,
        "route": route,
        "route_label": route_label,
        "trace": _append_trace(state, "Classifier", detail),
    }


def router_node(state: NewsExplainerState) -> dict:
    return {
        "trace": _append_trace(state, "Router", f"Sent the question to the {state['route_label']} node."),
    }


def route_question(state: NewsExplainerState) -> str:
    return state["route"]


def stock_expert_node(state: NewsExplainerState) -> dict:
    context = _market_context(state["question"], "stock")
    detailed_answer = _generate_explanation(state["question"], "stock", context)
    return {
        "context": context,
        "detailed_answer": detailed_answer,
        "trace": _append_trace(state, "Stock Expert", "Generated a stock-focused explanation with current market context."),
    }


def crypto_expert_node(state: NewsExplainerState) -> dict:
    context = _market_context(state["question"], "crypto")
    detailed_answer = _generate_explanation(state["question"], "crypto", context)
    return {
        "context": context,
        "detailed_answer": detailed_answer,
        "trace": _append_trace(state, "Crypto Expert", "Generated a crypto-focused explanation with current market context."),
    }


def etf_expert_node(state: NewsExplainerState) -> dict:
    context = _market_context(state["question"], "etf")
    detailed_answer = _generate_explanation(state["question"], "etf", context)
    return {
        "context": context,
        "detailed_answer": detailed_answer,
        "trace": _append_trace(state, "ETF Expert", "Generated an ETF-focused explanation with current market context."),
    }


def beginner_expert_node(state: NewsExplainerState) -> dict:
    context = _market_context(state["question"], "beginner")
    detailed_answer = _generate_explanation(state["question"], "beginner", context)
    return {
        "context": context,
        "detailed_answer": detailed_answer,
        "trace": _append_trace(state, "Beginner Expert", "Generated a concept-first explanation for a beginner question."),
    }


def simplify_node(state: NewsExplainerState) -> dict:
    final_answer = _simplify_explanation(state["question"], state["topic"], state["detailed_answer"])
    return {
        "final_answer": final_answer,
        "trace": _append_trace(state, "Simplifier", "Rewrote the answer into a cleaner beginner-friendly final response."),
    }


def output_node(state: NewsExplainerState) -> dict:
    return {
        "trace": _append_trace(state, "Output", "Prepared the final answer for the UI."),
    }


class NewsExplainerAgent:
    def __init__(self):
        graph = StateGraph(NewsExplainerState)

        graph.add_node("input", input_node)
        graph.add_node("classify", classify_node)
        graph.add_node("router", router_node)
        graph.add_node("stock_expert", stock_expert_node)
        graph.add_node("crypto_expert", crypto_expert_node)
        graph.add_node("etf_expert", etf_expert_node)
        graph.add_node("beginner_expert", beginner_expert_node)
        graph.add_node("simplify", simplify_node)
        graph.add_node("output", output_node)

        graph.set_entry_point("input")
        graph.add_edge("input", "classify")
        graph.add_edge("classify", "router")

        graph.add_conditional_edges(
            "router",
            route_question,
            {
                "stock_expert": "stock_expert",
                "crypto_expert": "crypto_expert",
                "etf_expert": "etf_expert",
                "beginner_expert": "beginner_expert",
            },
        )

        graph.add_edge("stock_expert", "simplify")
        graph.add_edge("crypto_expert", "simplify")
        graph.add_edge("etf_expert", "simplify")
        graph.add_edge("beginner_expert", "simplify")
        graph.add_edge("simplify", "output")
        graph.add_edge("output", END)

        self.graph = graph.compile()

    def run(self, question: str) -> dict:
        result = self.graph.invoke(
            {
                "question": question,
                "topic": "",
                "route": "",
                "route_label": "",
                "context": [],
                "detailed_answer": "",
                "final_answer": "",
                "trace": [],
            }
        )
        return {
            "topic": result["topic"],
            "route": result["route"],
            "route_label": result["route_label"],
            "context": result["context"],
            "final_answer": result["final_answer"],
            "trace": result["trace"],
        }
