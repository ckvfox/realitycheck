// === RealityCheck Floating Chat (InfinityFree Safe Version) ===
document.addEventListener("DOMContentLoaded", () => {
  console.log("🧠 floating_chat.js gestartet");

  // 💬 Button erstellen
  const btn = document.createElement("div");
  btn.id = "chatbot-button";
  btn.title = "RealityCheck Chat öffnen";
  btn.textContent = "💬";
  document.body.appendChild(btn);

  // 🪟 Chatfenster
  const win = document.createElement("div");
  win.id = "chatbot-window";
  win.style.display = "none";
  win.style.opacity = "0";
  win.style.transition = "opacity 0.3s ease";
  document.body.appendChild(win);

  // 🌐 Seitenkontext bestimmen
  let context = "general";
  const url = window.location.href.toLowerCase();
  if (url.includes("countries")) context = "countries";
  else if (url.includes("world")) context = "world";
  else if (url.includes("analysis")) context = "analysis";
  else if (url.includes("overall")) context = "overall_ranking";
  else if (url.includes("index")) context = "home";

  // 🔄 Chat-HTML asynchron laden (kein iframe, InfinityFree-kompatibel)
  fetch("chat.html")
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.text();
    })
    .then(html => {
      win.innerHTML = html;
      console.log("✅ Chat geladen");
      // Intro-Nachricht
      const msg = document.createElement("div");
      msg.className = "chat-message system";
      msg.textContent = `🤖 RealityCheck Chat (${context}) bereit.`;
      win.prepend(msg);
    })
    .catch(err => {
      console.error("⚠️ Chat konnte nicht geladen werden:", err);
      win.innerHTML = `<div style="padding:1rem;color:red;">
        ⚠️ Chat konnte nicht geladen werden (${err.message})
      </div>`;
    });

  // 🖱️ Öffnen / Schließen
  btn.addEventListener("click", () => {
    const hidden = win.style.display === "none" || win.style.display === "";
    if (hidden) {
      win.style.display = "block";
      requestAnimationFrame(() => (win.style.opacity = "1"));
    } else {
      win.style.opacity = "0";
      setTimeout(() => (win.style.display = "none"), 300);
    }
  });

  // ⎋ ESC schließt Chat
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && win.style.display === "block") {
      win.style.opacity = "0";
      setTimeout(() => (win.style.display = "none"), 300);
    }
  });
});
