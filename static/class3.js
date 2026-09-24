(function () {
"use strict";

var loading = false;
var chart = null;
var candleSeries = null;
var volumeSeries = null;
var ma20Series = null;
var ma50Series = null;

// ── Trace animation ─────────────────────────────────────────────────

var traceNames = ["Input", "Fetch Data", "Signal Engine", "Technical Analyst", "Portfolio Manager", "Output"];
var traceTimer = null;

function renderTrace(steps) {
  var el = document.getElementById("graph-trace");
  if (!el) return;
  el.innerHTML = steps.map(function (step) {
    var dotClass = "ta-trace-dot " + (step.status || "idle");
    return '<div class="ta-trace-step">' +
      '<span class="' + dotClass + '"></span>' +
      '<div><span class="ta-trace-name">' + esc(step.name) + '</span>' +
      '<span class="ta-trace-detail">' + esc(step.detail) + '</span></div></div>';
  }).join("");
}

function startTraceAnimation() {
  var stageIndex = 0;
  if (traceTimer) clearInterval(traceTimer);

  traceTimer = setInterval(function () {
    if (!loading || stageIndex >= traceNames.length) {
      clearInterval(traceTimer);
      traceTimer = null;
      return;
    }
    var steps = traceNames.map(function (name, i) {
      if (i < stageIndex) return { name: name, detail: "Done.", status: "done" };
      if (i === stageIndex) return { name: name, detail: "Processing...", status: "running" };
      return { name: name, detail: "Waiting.", status: "idle" };
    });
    renderTrace(steps);
    stageIndex++;
  }, 800);
}

// ── Helpers ──────────────────────────────────────────────────────────

function esc(text) {
  var div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}

function fmt(val) {
  if (val === null || val === undefined) return "—";
  return typeof val === "number" ? val.toFixed(2) : String(val);
}

function tsToDate(ts) {
  var d = new Date(ts * 1000);
  return d.getFullYear() + "-" +
    String(d.getMonth() + 1).padStart(2, "0") + "-" +
    String(d.getDate()).padStart(2, "0");
}

function badgeColor(signal) {
  if (!signal) return "";
  var s = signal.toLowerCase();
  if (s === "bullish" || s === "supportive" || s === "low") return "badge-green";
  if (s === "bearish" || s === "weak" || s === "high" || s === "stretched") return "badge-red";
  return "badge-amber";
}

function actionColor(action) {
  if (!action) return "";
  var a = action.toLowerCase();
  if (a.indexOf("core") >= 0) return "badge-green";
  if (a.indexOf("small") >= 0) return "badge-green";
  if (a === "watchlist") return "badge-amber";
  return "badge-red";
}

// ── Chart ────────────────────────────────────────────────────────────

function renderChart(priceData, ta) {
  var container = document.getElementById("chart-container");
  var placeholder = document.getElementById("chart-placeholder");
  if (placeholder) placeholder.style.display = "none";

  // Clear previous chart
  container.innerHTML = "";

  chart = LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: 480,
    layout: {
      background: { color: "#111827" },
      textColor: "#94a3b8",
      fontSize: 12,
    },
    grid: {
      vertLines: { color: "#1e293b" },
      horzLines: { color: "#1e293b" },
    },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: { borderColor: "#1e293b" },
    timeScale: { borderColor: "#1e293b" },
  });

  // Volume histogram (rendered first so candles draw on top)
  volumeSeries = chart.addHistogramSeries({
    color: "rgba(59,130,246,.25)",
    priceFormat: { type: "volume" },
    priceScaleId: "volume",
  });
  chart.priceScale("volume").applyOptions({
    scaleMargins: { top: 0.8, bottom: 0 },
  });

  var volumeData = [];
  for (var vi = 0; vi < priceData.timestamps.length; vi++) {
    var volVal = priceData.volumes ? priceData.volumes[vi] : 0;
    var isUp = priceData.closes[vi] >= priceData.opens[vi];
    volumeData.push({
      time: tsToDate(priceData.timestamps[vi]),
      value: volVal,
      color: isUp ? "rgba(34,197,94,.35)" : "rgba(239,68,68,.35)",
    });
  }
  volumeSeries.setData(volumeData);

  // Candlestick series
  candleSeries = chart.addCandlestickSeries({
    upColor: "#22c55e",
    downColor: "#ef4444",
    borderUpColor: "#22c55e",
    borderDownColor: "#ef4444",
    wickUpColor: "#22c55e",
    wickDownColor: "#ef4444",
  });

  var candles = [];
  for (var i = 0; i < priceData.timestamps.length; i++) {
    candles.push({
      time: tsToDate(priceData.timestamps[i]),
      open: priceData.opens[i],
      high: priceData.highs[i],
      low: priceData.lows[i],
      close: priceData.closes[i],
    });
  }
  candleSeries.setData(candles);

  // MA20 line
  if (ta && ta.trend && ta.trend.ma20_series) {
    ma20Series = chart.addLineSeries({
      color: "#3b82f6",
      lineWidth: 2,
      title: "MA20",
    });
    var ma20Data = [];
    for (var j = 0; j < ta.trend.ma20_series.length; j++) {
      if (ta.trend.ma20_series[j] !== null) {
        ma20Data.push({ time: tsToDate(priceData.timestamps[j]), value: ta.trend.ma20_series[j] });
      }
    }
    ma20Series.setData(ma20Data);
  }

  // MA50 line
  if (ta && ta.trend && ta.trend.ma50_series) {
    ma50Series = chart.addLineSeries({
      color: "#f59e0b",
      lineWidth: 2,
      title: "MA50",
    });
    var ma50Data = [];
    for (var k = 0; k < ta.trend.ma50_series.length; k++) {
      if (ta.trend.ma50_series[k] !== null) {
        ma50Data.push({ time: tsToDate(priceData.timestamps[k]), value: ta.trend.ma50_series[k] });
      }
    }
    ma50Series.setData(ma50Data);
  }

  // Support line
  if (ta && ta.levels && ta.levels.nearest_support) {
    var supportLine = chart.addLineSeries({
      color: "#22c55e",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      title: "Support",
    });
    supportLine.setData([
      { time: tsToDate(priceData.timestamps[0]), value: ta.levels.nearest_support },
      { time: tsToDate(priceData.timestamps[priceData.timestamps.length - 1]), value: ta.levels.nearest_support },
    ]);
  }

  // Resistance line
  if (ta && ta.levels && ta.levels.nearest_resistance) {
    var resistLine = chart.addLineSeries({
      color: "#ef4444",
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      title: "Resistance",
    });
    resistLine.setData([
      { time: tsToDate(priceData.timestamps[0]), value: ta.levels.nearest_resistance },
      { time: tsToDate(priceData.timestamps[priceData.timestamps.length - 1]), value: ta.levels.nearest_resistance },
    ]);
  }

  chart.timeScale().fitContent();

  // Resize handler
  window.addEventListener("resize", function () {
    if (chart) chart.applyOptions({ width: container.clientWidth });
  });
}

// ── Update panels ────────────────────────────────────────────────────

function updateQuickStats(data) {
  var box = document.getElementById("quick-stats");
  box.style.display = "block";

  document.getElementById("stats-ticker").textContent = data.ticker;
  document.getElementById("stats-price").textContent = "$" + fmt(data.technical_analysis.current_price);
  document.getElementById("stats-ma20").textContent = fmt(data.technical_analysis.trend.ma20);
  document.getElementById("stats-ma50").textContent = fmt(data.technical_analysis.trend.ma50);
  document.getElementById("stats-rsi").textContent = fmt(data.technical_analysis.momentum.rsi);

  var vol = data.technical_analysis.volume;
  if (vol) {
    document.getElementById("stats-volume").textContent = vol.latest ? (vol.latest / 1e6).toFixed(1) + "M" : "—";
    document.getElementById("stats-vol-ratio").textContent = vol.ratio ? vol.ratio + "x" : "—";
  }

  if (data.analyst_report && data.analyst_report.technical_verdict) {
    var row = document.getElementById("verdict-badge-row");
    var badge = document.getElementById("verdict-badge");
    row.style.display = "flex";
    var verdict = data.analyst_report.technical_verdict;
    badge.textContent = verdict.replace(/_/g, " ");
    badge.className = "ta-verdict-badge " + (verdict.indexOf("bullish") >= 0 ? "badge-green" : verdict.indexOf("bearish") >= 0 ? "badge-red" : "badge-amber");
  }
}

function updateAnalystCard(data) {
  var card = document.getElementById("analyst-card");
  card.style.display = "block";

  var ta = data.technical_analysis;
  var ar = data.analyst_report;

  document.getElementById("badge-trend").textContent = "Trend: " + (ta.trend.signal || "—");
  document.getElementById("badge-trend").className = "ta-badge " + badgeColor(ta.trend.signal);

  document.getElementById("badge-momentum").textContent = "Momentum: " + (ta.momentum.signal || "—");
  document.getElementById("badge-momentum").className = "ta-badge " + badgeColor(ta.momentum.signal);

  document.getElementById("badge-vol").textContent = "Vol: " + (ta.volatility.signal || "—");
  document.getElementById("badge-vol").className = "ta-badge " + badgeColor(ta.volatility.signal);

  if (ta.volume) {
    document.getElementById("badge-volume").textContent = "Volume: " + (ta.volume.signal || "—");
    document.getElementById("badge-volume").className = "ta-badge " + badgeColor(ta.volume.signal === "high" ? "stretched" : ta.volume.signal === "low" ? "weak" : "supportive");
  }

  document.getElementById("analyst-support").textContent = "$" + fmt(ta.levels.nearest_support);
  document.getElementById("analyst-resistance").textContent = "$" + fmt(ta.levels.nearest_resistance);
  document.getElementById("analyst-confidence").textContent = ar.confidence ? ar.confidence + "%" : "—";
  document.getElementById("analyst-hint").textContent = (ar.portfolio_role_hint || "—").replace(/_/g, " ");
  document.getElementById("analyst-summary").textContent = ar.summary || "—";
  document.getElementById("analyst-caution").textContent = ar.caution || "—";
  document.getElementById("analyst-watch-next").textContent = ar.watch_next || "—";
}

function updateManagerCard(data) {
  var card = document.getElementById("manager-card");
  card.style.display = "block";

  var pm = data.portfolio_decision;

  // Suggestion badge
  var suggEl = document.getElementById("mgr-suggestion");
  var sugg = (pm.suggestion || "hold").toLowerCase();
  suggEl.textContent = sugg.toUpperCase();
  suggEl.className = "ta-meta-value " + (sugg === "buy" ? "badge-green" : sugg === "sell" ? "badge-red" : "badge-amber");

  // TP and SL
  document.getElementById("mgr-tp").textContent = pm.take_profit != null ? "$" + Number(pm.take_profit).toFixed(2) : "—";
  document.getElementById("mgr-sl").textContent = pm.stop_loss != null ? "$" + Number(pm.stop_loss).toFixed(2) : "—";
  document.getElementById("mgr-rr").textContent = pm.risk_reward_ratio || "—";

  var actionEl = document.getElementById("mgr-action");
  actionEl.textContent = (pm.portfolio_action || "—").replace(/_/g, " ");
  actionEl.className = "ta-meta-value " + actionColor(pm.portfolio_action);

  document.getElementById("mgr-role").textContent = (pm.portfolio_role || "—").replace(/_/g, " ");
  document.getElementById("mgr-cap").textContent = pm.allocation_cap != null ? (pm.allocation_cap * 100).toFixed(0) + "%" : "—";
  document.getElementById("mgr-review").textContent = pm.needs_more_review ? "Yes" : "No";
  document.getElementById("mgr-reason").textContent = pm.decision_reason || "—";
  document.getElementById("mgr-entry").textContent = pm.entry_note || "—";
}

// ── Main ─────────────────────────────────────────────────────────────

function analyze() {
  var input = document.getElementById("ticker-input");
  var ticker = (input.value || "").trim().toUpperCase();
  if (!ticker || loading) return;

  loading = true;
  var btn = document.getElementById("analyze-btn");
  btn.innerHTML = '<svg class="btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg><span class="btn-label">Loading…</span>';
  btn.disabled = true;

  // Hide cards during loading
  document.getElementById("analyst-card").style.display = "none";
  document.getElementById("manager-card").style.display = "none";

  startTraceAnimation();

  fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker: ticker }),
  })
    .then(function (resp) {
      return resp.json().then(function (data) {
        if (!resp.ok) throw new Error(data.error || "Request failed.");
        return data;
      });
    })
    .then(function (data) {
      loading = false;
      if (traceTimer) { clearInterval(traceTimer); traceTimer = null; }

      var btn = document.getElementById("analyze-btn");
      btn.innerHTML = '<svg class="btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg><span class="btn-label">Analyze</span>';
      btn.disabled = false;

      // Render trace from server
      if (data.trace) {
        renderTrace(data.trace);
      }

      // Render chart
      if (data.price_data && data.price_data.closes) {
        renderChart(data.price_data, data.technical_analysis);
      }

      // Update panels
      if (data.technical_analysis && data.technical_analysis.current_price) {
        updateQuickStats(data);
      }
      if (data.analyst_report && data.analyst_report.technical_verdict) {
        updateAnalystCard(data);
      }
      if (data.portfolio_decision && data.portfolio_decision.portfolio_action) {
        updateManagerCard(data);
      }
    })
    .catch(function (err) {
      loading = false;
      if (traceTimer) { clearInterval(traceTimer); traceTimer = null; }

      var btn = document.getElementById("analyze-btn");
      btn.innerHTML = '<svg class="btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg><span class="btn-label">Analyze</span>';
      btn.disabled = false;

      renderTrace(traceNames.map(function (name) {
        return { name: name, detail: "Error: " + err.message, status: "idle" };
      }));

      alert("Error: " + err.message);
    });
}

function init() {
  var btn = document.getElementById("analyze-btn");
  var input = document.getElementById("ticker-input");

  if (btn) btn.addEventListener("click", analyze);
  if (input) {
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        analyze();
      }
    });
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

})();
