(function () {
    const thread = document.getElementById("dm-thread");
    const input = document.getElementById("dm-input");
    const sendButton = document.getElementById("dm-send");

    if (!thread || !input || !sendButton) {
        return;
    }

    const conversationId = thread.dataset.conversationId;

    function scrollToBottom() {
        thread.scrollTop = thread.scrollHeight;
    }

    function appendBubble(sender, text, time) {
        const bubble = document.createElement("div");
        bubble.className = "dm-bubble dm-bubble-" + sender;

        const textEl = document.createElement("p");
        textEl.className = "dm-bubble-text";
        textEl.textContent = text;

        const timeEl = document.createElement("span");
        timeEl.className = "dm-bubble-time";
        timeEl.textContent = time;

        bubble.appendChild(textEl);
        bubble.appendChild(timeEl);
        thread.appendChild(bubble);

        scrollToBottom();
    }

    async function sendMessage() {
        const text = input.value.trim();

        if (text === "") {
            return;
        }

        sendButton.disabled = true;

        try {
            const response = await fetch("/api/messages/" + conversationId + "/send", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) {
                throw new Error("Mesaj gönderilemedi");
            }

            const data = await response.json();

            appendBubble(data.sender, data.text, data.time);
            input.value = "";
        } catch (error) {
            console.error(error);
        } finally {
            sendButton.disabled = false;
            input.focus();
        }
    }

    sendButton.addEventListener("click", sendMessage);

    input.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });

    scrollToBottom();
    input.focus();
})();
