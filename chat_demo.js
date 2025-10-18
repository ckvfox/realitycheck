document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("user-input");
  const send = document.getElementById("send");
  const messages = document.getElementById("messages");

  send.addEventListener("click", handleMessage);
  input.addEventListener("keypress", e => { if (e.key === "Enter") handleMessage(); });

  greetWithContext();

  async function handleMessage() {
    const text = input.value.trim();
    if (!text) return;
    addMsg("Du", text);
    input.value = "";
    const reply = await getReply(text);
    addMsg("RealityCheck", reply);
  }

  function addMsg(sender, text) {
    messages.innerHTML += `\n<b>${sender}:</b> ${text}\n`;
    messages.scrollTop = messages.scrollHeight;
  }

  async function getReply(question) {
    const q = question.toLowerCase();

    // === Korrekte Pfade gemäß deiner Struktur ===
    const countries = await loadJSON("countries.json").catch(() => ({}));
    const available = await loadJSON("available_kpi.json").catch(() => ({}));

    // === Kontext laden ===
    const contextCountry = localStorage.getItem("currentCountry");
    const contextKPI = localStorage.getItem("currentKPI");

    if (!question && (contextCountry || contextKPI)) {
      return `Du siehst aktuell ${contextCountry || "ein Land"} und den KPI ${contextKPI || "ein Thema"}.`;
    }

    // === Falls allgemeine Frage mit Kontext ===
    if (q.includes("wie steht") && contextCountry && contextKPI) {
      try {
        const data = await loadJSON(`data/${contextKPI}.json`);
        const entry = findCountryData(data, contextCountry);
        if (entry) {
          return `${contextCountry} hat beim KPI '${contextKPI}' aktuell einen Wert von ${entry.value} (${entry.year}).`;
        }
      } catch {}
    }

    // === Land & KPI erkennen ===
    const country = findMatch(q, countries?.countries?.map(c => c.name) || []);
    const kpi = findMatch(q, Object.keys(available || {}));

    if (country && kpi) {
      try {
        const data = await loadJSON(`data/${kpi}.json`);
        const entry = findCountryData(data, country);
        if (entry) return `${country} hat beim KPI '${kpi}' aktuell einen Wert von ${entry.value} (${entry.year}).`;
        else return `Für ${country} liegen keine Daten zu '${kpi}' vor.`;
      } catch {
        return `Ich konnte die Daten zu '${kpi}' nicht laden.`;
      }
    }

    if (country && !kpi)
      return `Ich kenne ${country}. Frag z. B.: „Wie steht ${country} beim Demokratieindex?“`;

    if (kpi && !country)
      return `Der KPI '${kpi}' ist verfügbar. Frag z. B.: „Wie steht Deutschland beim ${kpi}?“`;

    if (q.includes("hilfe") || q.includes("was kannst"))
      return "Ich bin der RealityCheck-Demo-Bot. Frag mich nach einem Land und einer Kennzahl.";

    return "Ich bin nur eine Demo ohne KI. Frag mich nach einem Land und einer Kennzahl.";
  }

  function findMatch(q, list) {
    if (!list) return null;
    for (const item of list) {
      if (q.includes(item.toLowerCase())) return item;
    }
    return null;
  }

  function findCountryData(data, country) {
    const d = data?.data || data;
    if (!Array.isArray(d)) return null;
    const entry = d.filter(e => e.country === country || e.country_name === country)
                   .sort((a,b)=>b.year - a.year)[0];
    return entry || null;
  }

  async function loadJSON(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`Fehler beim Laden von ${path}`);
    return res.json();
  }

  function greetWithContext() {
    const c = localStorage.getItem("currentCountry");
    const k = localStorage.getItem("currentKPI");
    if (c || k) {
      addMsg("RealityCheck", `👋 Willkommen zurück! Du siehst aktuell ${c || "ein Land"} und interessierst dich für ${k || "einen KPI"}.`);
    }
  }
});
