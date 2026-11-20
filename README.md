# AI Portfolio Builder

A local Flask app for exploring a ticker’s price history, reading an AI interpretation of its technical indicators, and asking questions about market news.

## Run locally

From the project folder on macOS or Linux, set up the Python environment on the first run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Start the app with the project’s Python interpreter:

```sh
.venv/bin/python app.py
```

Open the [dashboard](http://127.0.0.1:5000), choose **Technical Analyst**, enter `AAPL`, and click **Analyze**. The chart and statistics need an internet connection to load market data and the chart library. Press `Ctrl+C` in the terminal to stop the server.

## Enable the AI features

The Technical Analyst report, Portfolio Manager decision, and Market Explainer answers use Claude. To enable them, set the following entry in a `.env` file alongside `app.py`, replacing the placeholder with your Anthropic API key. Restart the server after saving.

```dotenv
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## What the app does

| Feature | What you get | Needs an Anthropic key |
| --- | --- | --- |
| Chart and statistics | Up to one year of daily Yahoo Finance prices and volume, with 20-day and 50-day moving averages and a 14-day RSI. | No |
| Technical Analyst report | A bullish-to-bearish verdict, confidence score, main risk, and what to watch next, based on the ticker’s indicators. | Yes |
| Portfolio Manager decision | A suggested role for the ticker, such as a core holding, small position, or watchlist candidate, with a maximum allocation and an explanation. | Yes |
| Market Explainer | A beginner-friendly answer to a question such as “Why is Apple stock moving?”, using available price data and Google News headlines. | Yes |

On the Technical Analyst page, **Graph Trace** shows what happened after you clicked **Analyze**. If price history is unavailable or the AI steps were skipped, the trace explains why.

## Where the code lives

- [app.py](app.py) starts Flask and registers both modules.
- [technical_analyst.py](technical_analyst.py) receives ticker submissions at `POST /api/analyze`. The [technical analyst workflow](src/agents/technical_analyst/agent.py) fetches prices, runs the [indicator calculations](src/core/signals.py), and generates the two AI cards.
- [news_explainer.py](news_explainer.py) receives Market Explainer questions at `POST /api/explain`. The [news explainer workflow](src/agents/news_explainer/agent.py) classifies the question, gathers context, and generates the answer.
