let source;
// DEFINE HELPER FUNCTIONS
function g(id) {
  return document.getElementById(id);
}

function replaceURLWithHTMLLinks(text) {
  var exp =
    /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/i;
  return text.replace(exp, "<a target=\"_blank\" href='$1'>$1</a>");
}

function sendPrompt(prompt) {
  response.innerHTML = "";
  keyword.value = "";
  keyword.placeholder = "処理中...";
  keyword.disabled = true;
  source = new EventSource(`/chat?prompt=${prompt}`);
  source.onmessage = function (event) {
    if (event.data === "[DONE]") {
      source.close();
    }
    insertAnswer(event.data, prompt);
  };
}

function reset() {
  keyword.placeholder = "Ask me anything...";
  keyword.disabled = false;
  keyword.focus();
}

function insertAnswer(answer, prompt) {
  if (answer === "[DONE]") {
    reset();
    response.innerHTML = replaceURLWithHTMLLinks(response.innerHTML);
    return;
  }
  const card = response;
  if (card) {
    card.innerText += answer;
  } else {
    let html = `${answer}`;
    response.insertAdjacentHTML("beforeend", html);
  }
}

// DEFINE DOM ELEMENTS
const response = g("response");
const keyword = g("keyword");

keyword.addEventListener("keydown", (e) => {
  if (e.keyCode == 13) {
    const prompt = keyword.value.trim();
    if (prompt) {
      sendPrompt(prompt);
    }
  }
});