const form = g('form');
const keyword = g('keyword');
const content = g('content');
let CHAT_ID;

function g(id) {
    return document.getElementById(id);
}

function reset() {
    keyword.value = '';
}

function scorllToBottom() {
    content.scrollTo(0, content.scrollHeight);
}

function onSubmit(event) {
    event.preventDefault();
    const prompt = keyword.value;
    CHAT_ID = Date.now();
    updateDOM('user', prompt);
    invokeAPI(keyword.value)
    reset();
    return false;
}

function invokeAPI(prompt) {
    const source = new EventSource(`/chat?prompt=${prompt}`);
    source.onmessage = function (event) {
        if (event.data === "[DONE]") {
            source.close();
        }
        updateDOM('ai', event.data);
      };
}

function updateDOM(type, text) {
    let html = '';
    if (type === 'user') {
        html = `<div class="card question">${text}</div>`;
    } else if (type === 'ai' && text !== '[DONE]') {
        const card = g(CHAT_ID);
        if (card) {
            card.innerText += text.replaceAll('[NEWLINE]', '\n');
        } else {
            html = `<div class="card answer" id="${CHAT_ID}">${text}</div>`;
        }
    }
    content.insertAdjacentHTML("beforeend", html);
    scorllToBottom();
}

form.addEventListener('submit', onSubmit);