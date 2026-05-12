async function sendQuestion() {
    const input = document.getElementById("question-input");
    const chatBox = document.getElementById("chat-box");

    const question = input.value.trim();

    if (question === "") {
        return;
    }

    chatBox.innerHTML += `
        <div class="ai-message">
            <strong>Kullanıcı:</strong> ${question}
        </div>
    `;

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

    chatBox.innerHTML += `
        <div class="ai-message">
            <strong>AI Asistan:</strong> ${data.answer}
        </div>
    `;

    input.value = "";
}