(function () {
"use strict";

var exampleQuestions = [
  "Why did Nvidia stock go up?",
  "What is an ETF?",
  "Why is Bitcoin dropping today?",
  "How does diversification reduce risk?"
];

var state = {
  loading: false,
  topic: "Waiting",
  routeLabel: "Not run yet",
  context: [],
  trace: [
    { name: "Input", detail: "Waiting for a question.", status: "pending" },
    { name: "Classifier", detail: "The graph will detect the question type.", status: "pending" },
    { name: "Router", detail: "The graph will choose the right branch.", status: "pending" },
    { name: "Expert", detail: "An expert node will write the first answer.", status: "pending" },
    { name: "Simplifier", detail: "The answer will be rewritten for beginners.", status: "pending" },
    { name: "Output", detail: "The final answer will return to the page.", status: "pending" }
  ],
  messages: [
    {
      role: "ai",
      text: "Ask a market question for a beginner-friendly explanation."
    }
  ]
};

var traceTimer = null;

function esc(text) {
  var div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}

function formatAnswer(text) {
  if (!text) return "";

  var lines = text.split(/\r?\n/);
  var html = "";
  var sectionOpen = false;
  var listItems = [];

  function flushList() {
    if (!listItems.length) return;
    html += '<ul class="explainer-answer-list">' + listItems.join("") + "</ul>";
    listItems = [];
  }

  function closeSection() {
    flushList();
    if (sectionOpen) {
      html += "</div>";
      sectionOpen = false;
    }
  }

  lines.forEach(function (rawLine) {
    var line = rawLine.trim();
    var safe = esc(line)
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/^#+\s*/, "");
    var normalized = line.replace(/^#+\s*/, "").replace(/:$/, "");

    if (!line) {
      flushList();
      return;
    }

    if (/^(Quick Take|Why It Happened|What To Watch Next|Beginner Note|Direct Answer|Key Drivers|What To Watch|Caveats)$/.test(normalized)) {
      closeSection();
      html += '<div class="explainer-answer-section">';
      html += '<div class="explainer-answer-heading">' + esc(normalized) + "</div>";
      sectionOpen = true;
      return;
    }

    if (/^[-*]\s+/.test(line)) {
      listItems.push("<li>" + safe.replace(/^[-*]\s+/, "") + "</li>");
      return;
    }

    flushList();
    if (!sectionOpen) {
      html += '<div class="explainer-answer-section">';
      sectionOpen = true;
    }
    html += "<p>" + safe + "</p>";
  });

  closeSection();
  return html || "<p>" + esc(text).replace(/\n/g, "<br>") + "</p>";
}

function renderBubble(msg) {
  if (msg.role === "ai") return formatAnswer(msg.text);
  return esc(msg.text).replace(/\n/g, "<br>");
}

function renderMessages() {
  var el = document.getElementById("chat-messages");
  if (!el) return;
  el.innerHTML = state.messages.map(function (msg) {
    return '<div class="explainer-msg ' + msg.role + '">' +
      '<span class="explainer-avatar">' + (msg.role === "ai" ? "AI" : "YOU") + '</span>' +
      '<div class="explainer-bubble">' + renderBubble(msg) + '</div>' +
      '</div>';
  }).join("");
  if (state.loading) {
    el.innerHTML += '<div class="explainer-msg ai">' +
      '<span class="explainer-avatar">AI</span>' +
      '<div class="explainer-bubble"><span class="explainer-loading-line">Researching live market data and recent headlines...</span></div>' +
      '</div>';
  }
  el.scrollTop = el.scrollHeight;
}

function renderSummary() {
  var topic = document.getElementById("detected-topic");
  var route = document.getElementById("route-label");
  var context = document.getElementById("context-list");
  if (topic) topic.textContent = state.topic;
  if (route) route.textContent = state.routeLabel;
  if (context) {
    context.innerHTML = state.context.length
      ? state.context.map(function (item) {
        return '<div class="explainer-context-item">' + esc(item) + "</div>";
      }).join("")
      : '<div class="explainer-context-item">The agent will show the live quote snapshot and headlines it used after each run.</div>';
  }
}

function renderTrace() {
  var el = document.getElementById("graph-trace");
  if (!el) return;
  el.innerHTML = state.trace.map(function (step) {
    return '<div class="explainer-step ' + esc(step.status || "done") + '">' +
      '<span class="explainer-step-dot"></span>' +
      '<div><div class="explainer-step-name">' + esc(step.name) + '</div>' +
      '<div class="explainer-step-detail">' + esc(step.detail) + '</div></div>' +
      '</div>';
  }).join("");
}

function renderChips() {
  var row = document.getElementById("prompt-chips");
  if (!row) return;
  row.innerHTML = exampleQuestions.map(function (question) {
    return '<button class="explainer-chip" type="button" data-question="' + esc(question) + '">' + esc(question) + '</button>';
  }).join("");
  row.querySelectorAll(".explainer-chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      document.getElementById("question-input").value = chip.getAttribute("data-question");
    });
  });
}

function startTraceAnimation() {
  var stages = [
    [
      { name: "Input", detail: "Stored the user's question in graph state.", status: "done" },
      { name: "Classifier", detail: "Reading the question and detecting the topic.", status: "running" },
      { name: "Router", detail: "Waiting for the classifier result.", status: "pending" },
      { name: "Expert", detail: "Waiting for the selected branch to gather market context.", status: "pending" },
      { name: "Simplifier", detail: "Waiting for the first draft answer.", status: "pending" },
      { name: "Output", detail: "Waiting for the final formatted response.", status: "pending" }
    ],
    [
      { name: "Input", detail: "Stored the user's question in graph state.", status: "done" },
      { name: "Classifier", detail: "Detected the question type.", status: "done" },
      { name: "Router", detail: "Choosing the best branch for this question.", status: "running" },
      { name: "Expert", detail: "Waiting for the selected branch to gather market context.", status: "pending" },
      { name: "Simplifier", detail: "Waiting for the first draft answer.", status: "pending" },
      { name: "Output", detail: "Waiting for the final formatted response.", status: "pending" }
    ],
    [
      { name: "Input", detail: "Stored the user's question in graph state.", status: "done" },
      { name: "Classifier", detail: "Detected the question type.", status: "done" },
      { name: "Router", detail: "Selected the right branch for this question.", status: "done" },
      { name: "Expert", detail: "Gathering a live quote snapshot and recent headlines.", status: "running" },
      { name: "Simplifier", detail: "Waiting for the first draft answer.", status: "pending" },
      { name: "Output", detail: "Waiting for the final formatted response.", status: "pending" }
    ],
    [
      { name: "Input", detail: "Stored the user's question in graph state.", status: "done" },
      { name: "Classifier", detail: "Detected the question type.", status: "done" },
      { name: "Router", detail: "Selected the right branch for this question.", status: "done" },
      { name: "Expert", detail: "Finished the first detailed draft.", status: "done" },
      { name: "Simplifier", detail: "Rewriting the answer for a beginner.", status: "running" },
      { name: "Output", detail: "Waiting for the final formatted response.", status: "pending" }
    ]
  ];
  var index = 0;

  if (traceTimer) clearInterval(traceTimer);
  traceTimer = setInterval(function () {
    if (!state.loading || index >= stages.length) {
      clearInterval(traceTimer);
      traceTimer = null;
      return;
    }
    state.trace = stages[index];
    renderTrace();
    index += 1;
  }, 900);
}

function sendQuestion() {
  var input = document.getElementById("question-input");
  var question = (input.value || "").trim();
  if (!question || state.loading) return;

  state.messages.push({ role: "user", text: question });
  input.value = "";
  state.loading = true;
  state.topic = "Analyzing";
  state.routeLabel = "Choosing branch";
  state.context = [];
  renderMessages();
  renderSummary();
  startTraceAnimation();

  fetch("/api/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: question })
  })
    .then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok) throw new Error(data.error || "Request failed.");
        return data;
      });
    })
    .then(function (payload) {
      state.loading = false;
      if (traceTimer) {
        clearInterval(traceTimer);
        traceTimer = null;
      }
      state.topic = payload.topic || "Unknown";
      state.routeLabel = payload.route_label || "Unknown";
      state.context = payload.context || [];
      state.trace = payload.trace || state.trace;
      state.messages.push({ role: "ai", text: payload.final_answer || "No answer returned." });
      renderSummary();
      renderTrace();
      renderMessages();
    })
    .catch(function (error) {
      state.loading = false;
      if (traceTimer) {
        clearInterval(traceTimer);
        traceTimer = null;
      }
      state.trace = [
        { name: "Input", detail: "Stored the user's question in graph state.", status: "done" },
        { name: "Classifier", detail: "Started processing the question.", status: "done" },
        { name: "Router", detail: "The request failed before the graph finished.", status: "pending" },
        { name: "Expert", detail: "The expert branch did not complete.", status: "pending" },
        { name: "Simplifier", detail: "The simplifier did not run.", status: "pending" },
        { name: "Output", detail: "No final answer was returned.", status: "pending" }
      ];
      state.messages.push({ role: "ai", text: "Error: " + error.message });
      renderSummary();
      renderTrace();
      renderMessages();
    });
}

function init() {
  renderChips();
  renderSummary();
  renderTrace();
  renderMessages();

  var send = document.getElementById("send-btn");
  var input = document.getElementById("question-input");
  if (send) send.addEventListener("click", sendQuestion);
  if (input) {
    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendQuestion();
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
