# ⚙️ RealityCheck – GitHub Actions Workflows

Dieses Verzeichnis enthält alle automatisierten Abläufe (CI/CD-Pipelines) für das RealityCheck-Projekt.  
Sie decken **Fetch**, **Analyse**, **FTP-Upload** und **Benachrichtigungen per E-Mail** ab.

Alle Workflows verwenden:
- 🧩 **Python 3.11**
- 🧠 `OPENAI_API_KEY` aus GitHub Secrets
- 🚀 **FTP-Deploy-Action** (`SamKirkland/ftp-deploy-action@v4.3.5`)
- 📧 **E-Mail-Benachrichtigung** (immer aktiv – bei Erfolg oder Fehler)

---

## 🧪 `manual-fetch.yml`
**Manueller Voll-Fetch + Analyse + FTP + E-Mail**

➡️ Start:  
GitHub → *Actions* → *RealityCheck – Manual Fetch (Test)* → **Run workflow**

Führt automatisch aus:
1. Lädt alle KPIs (WorldBank, OWID, CSV, UNHCR)
2. Generiert Rankings und Konsolidierungen
3. Führt die KI-Analyse aus
4. Lädt `/data/` per FTP hoch
5. Sendet dir das Log per E-Mail 📧

**Empfohlen:** vor Monatsende oder nach Änderungen an den Quellen.

---

## 📅 `monthly-fetch.yml`
**Automatischer Monatslauf**  
läuft am **1. Tag jedes Monats um 03:00 UTC (05:00 MEZ)**

Führt die gleichen Schritte wie der manuelle Fetch aus.  
Perfekt, um RealityCheck aktuell zu halten – ganz ohne manuelles Eingreifen.

Wenn du möchtest, kannst du ihn auch **manuell starten**, z. B. zum Testen.

---

## 🚀 `manual-ftp-full.yml`
**Vollständiger FTP-Upload (Clean Slate)**

Löscht zuerst alle Dateien im Zielverzeichnis (`/data/`)  
und lädt **alle lokalen Dateien neu** hoch.

➡️ Start:  
GitHub → *Actions* → *RealityCheck – Full FTP Upload* → **Run workflow**

⚠️ Verwende dies nur, wenn:
- das Serververzeichnis beschädigt ist
- viele Dateien manuell gelöscht oder geändert wurden

---

## 🔁 `manual-ftp-sync.yml`
**Schneller FTP-Sync – nur geänderte Dateien**

Überträgt **nur Unterschiede** zwischen lokalem `/data/`  
und dem Serververzeichnis – ideal für kleine Aktualisierungen.

➡️ Start:  
GitHub → *Actions* → *RealityCheck – FTP Sync Upload* → **Run workflow**

Empfohlen nach manuellen Anpassungen einzelner JSONs oder CSVs.

---

## 🎯 `manual-partial-upload.yml`
**Upload einzelner Dateien per Eingabe**

➡️ Start:  
GitHub → *Actions* → *RealityCheck – Partial FTP Upload* →  
→ **Run workflow** → im Eingabefeld `files` z. B.:

data/fetch_log.txt,data/overall_ranking.json,data/fun_ranking.json

markdown
Code kopieren

Nur diese Dateien werden hochgeladen.

**Beispiel-Einsatz:**
- Du hast nachträglich `fun_ranking.json` geändert.
- Oder willst nur das neue Log hochladen.

---

## 🔒 Benötigte GitHub Secrets

| Secret | Beschreibung |
|---------|---------------|
| `OPENAI_API_KEY` | Dein gültiger OpenAI API-Schlüssel |
| `FTP_SERVER` | FTP-Serveradresse (z. B. `ftpupload.net`) |
| `FTP_USERNAME` | FTP-Benutzername |
| `FTP_PASSWORD` | FTP-Passwort |
| `FTP_DIR` | Basisverzeichnis (z. B. `/realitycheck.great-site.net/htdocs`) |
| `SMTP_SERVER` | SMTP-Server für Mail (z. B. `smtp.gmail.com`) |
| `SMTP_PORT` | Port (z. B. `465`) |
| `SMTP_USERNAME` | Absenderadresse (z. B. `yourname@gmail.com`) |
| `SMTP_PASSWORD` | App-spezifisches Passwort (nicht dein echtes Gmail-PW!) |
| `EMAIL_TO` | Empfängeradresse für Benachrichtigungen |

---

## 📬 Benachrichtigungen

Nach jedem Workflow (egal ob erfolgreich oder fehlerhaft)  
erhältst du eine E-Mail mit:
- dem Status (`success` / `failure`)
- dem Datum
- und angehängtem Log (`fetch_log.txt`)

Beispiel-Betreff:  
RealityCheck Run – success

yaml
Code kopieren

---

## 🧠 Tipps

- Du kannst die Logs auch in GitHub unter **Actions → Artifacts** herunterladen.  
- Wenn sich dein FTP-Server ändert, musst du nur die **Secrets** anpassen –  
  die Workflows bleiben unverändert.
- Alle Workflows sind modular – du kannst sie unabhängig voneinander ausführen.

---

✍️ *Stand: Oktober 2025 – RealityCheck Automated Pipeline by ChatGPT-5*