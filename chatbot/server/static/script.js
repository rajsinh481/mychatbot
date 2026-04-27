let USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    USER_ID = "user_" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("user_id", USER_ID);
}

let chatHistory = JSON.parse(localStorage.getItem("chatHistory")) || [];

function toggleHistory() {
    let panel = document.getElementById("historyPanel");
    if (!panel) return;
    panel.style.left = panel.style.left === "0px" ? "-300px" : "0px";
}

function saveHistory(question, answer) {
    chatHistory.unshift({ q: question, a: answer });
    localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
    renderHistory();
}

function renderHistory() {
    let historyList = document.getElementById("historyList");
    if (!historyList) return;

    historyList.innerHTML = "";

    if (chatHistory.length === 0) {
        historyList.innerHTML = `<div style="padding:10px;color:#666;">No history yet</div>`;
        return;
    }

    chatHistory.forEach((chat, index) => {
        historyList.innerHTML += `
            <div class="history-item" onclick="loadHistory(${index})">
                ${escapeHTML(chat.q.substring(0, 35))}${chat.q.length > 35 ? "..." : ""}
            </div>
        `;
    });
}

function loadHistory(index) {
    let messages = document.getElementById("messages");
    messages.innerHTML = `
        <div class="user-msg"><span>${escapeHTML(chatHistory[index].q)}</span></div>
        <div class="bot-msg"><span>${escapeHTML(chatHistory[index].a)}</span></div>
    `;
    toggleHistory();
}

function clearHistory() {
    chatHistory = [];
    localStorage.removeItem("chatHistory");
    renderHistory();

    fetch("/clear-history", { method: "POST" });

    const messages = document.getElementById("messages");
    messages.innerHTML = `
        <div class="bot-msg">
            <span>History cleared ✅</span>
        </div>
    `;
}

function sendMessage() {
    let input = document.getElementById("userInput");
    let msg = input.value.trim();
    if (!msg) return;

    let messages = document.getElementById("messages");
    messages.innerHTML += `<div class="user-msg"><span>${escapeHTML(msg)}</span></div>`;

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, user_id: USER_ID })
    })
    .then(res => res.json())
    .then(data => {
        messages.innerHTML += `<div class="bot-msg"><span>${escapeHTML(data.reply)}</span></div>`;
        messages.scrollTop = messages.scrollHeight;
        saveHistory(msg, data.reply);
    });

    input.value = "";
}

document.addEventListener("DOMContentLoaded", () => {
    renderHistory();

    const clearBtn = document.getElementById("clearHistoryBtn");
    if (clearBtn) clearBtn.addEventListener("click", clearHistory);

    const input = document.getElementById("userInput");
    if (input) {
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});

function escapeHTML(str) {
    return (str || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}