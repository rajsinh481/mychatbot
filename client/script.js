
function sendMessage() {
    let input = document.getElementById("userInput");
    let msg = input.value.trim();
    if (msg === "") return;

    let messages = document.getElementById("messages");

  
    messages.innerHTML += `
        <div class="user-msg">
            <span>${msg}</span>
        </div>
    `;

    messages.scrollTop = messages.scrollHeight;

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
    })
    .then(res => res.json())
    .then(data => {


        messages.innerHTML += `
            <div class="bot-msg">
                <span>${data.reply}</span>
            </div>
        `;

        messages.scrollTop = messages.scrollHeight;

      
        speakReply(stripHTML(data.reply));
    });

    input.value = "";
}


function startVoice() {
    if (!('webkitSpeechRecognition' in window)) {
        alert("Voice input not supported");
        return;
    }

    let recognition = new webkitSpeechRecognition();
    recognition.lang = "hi-IN"; // works for Gujarati also
    recognition.start();

    recognition.onresult = function (event) {
        document.getElementById("userInput").value =
            event.results[0][0].transcript;
    };
}


function speakReply(text) {
    if (!('speechSynthesis' in window)) return;

    let utterance = new SpeechSynthesisUtterance(text);

    if (/[\u0A80-\u0AFF]/.test(text)) {
        utterance.lang = "gu-IN"; // Gujarati
    } else if (/[\u0900-\u097F]/.test(text)) {
        utterance.lang = "hi-IN"; // Hindi
    } else {
        utterance.lang = "en-IN"; // English
    }

    utterance.rate = 0.95;
    utterance.pitch = 1;
    speechSynthesis.speak(utterance);
}

function stripHTML(html) {
    let div = document.createElement("div");
    div.innerHTML = html;
    return div.textContent || div.innerText || "";
}
