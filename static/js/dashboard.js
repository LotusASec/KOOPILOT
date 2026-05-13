async function loadAiStatus() {
    const badge = document.getElementById("ai-status-badge");
    const textEl = document.getElementById("ai-status-text");

    if (!badge || !textEl) {
        return;
    }

    try {
        const response = await fetch("/api/ai/status");
        const data = await response.json();

        badge.classList.remove("ai-status-unknown", "ai-status-ok", "ai-status-fallback");

        if (data.configured) {
            badge.classList.add("ai-status-ok");
            textEl.textContent = "Gemini bağlı (" + data.model + ")";
            badge.title = "Cevaplar Gemini API'sinden geliyor";
        } else {
            badge.classList.add("ai-status-fallback");
            textEl.textContent = "Bağlantı yok";
            badge.title = data.reason || "Gemini yapılandırılmamış";
        }
    } catch (error) {
        badge.classList.add("ai-status-fallback");
        textEl.textContent = "Bağlantı yok";
    }
}

function appendUserMessage(chatBox, question) {
    const messageEl = document.createElement("div");
    messageEl.className = "ai-message";

    const label = document.createElement("strong");
    label.textContent = "Kullanıcı: ";
    messageEl.appendChild(label);

    messageEl.appendChild(document.createTextNode(question));
    chatBox.appendChild(messageEl);
}

function appendAiMessage(chatBox, answer, isError) {
    const messageEl = document.createElement("div");
    messageEl.className = "ai-message";
    if (isError) {
        messageEl.classList.add("ai-message-error");
    }

    const label = document.createElement("strong");
    label.textContent = "AI Asistan: ";
    messageEl.appendChild(label);

    messageEl.appendChild(document.createTextNode(answer));
    chatBox.appendChild(messageEl);
}

async function sendQuestion() {
    const input = document.getElementById("question-input");
    const chatBox = document.getElementById("chat-box");

    const question = input.value.trim();

    if (question === "") {
        return;
    }

    appendUserMessage(chatBox, question);
    input.value = "";

    try {
        const response = await fetch("/api/ai/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        const data = await response.json();
        appendAiMessage(chatBox, data.answer, data.source === "error");
    } catch (error) {
        appendAiMessage(
            chatBox,
            "Bağlantı hatası: AI asistanına şu an ulaşılamıyor. Lütfen birkaç saniye sonra tekrar deneyin.",
            true
        );
    }
}

document.addEventListener("DOMContentLoaded", loadAiStatus);
