<div align="center">

# 🛠️ IT-aanhuis Helpdesk AI

**Lokale helpdesk-assistent voor [IT-aanhuis](https://www.it-aanhuis.com/) — Windows, Nederlandstalig, volledig offline via Ollama.**

*IT hulp bij u aan huis*

</div>

---

De IT-aanhuis Helpdesk AI is een moderne desktop-app (zwart met cyan, frosted-glass look) die zowel **medewerkers** als **klanten** van IT-aanhuis helpt met helpdeskvragen — van **prioriteit 1** (urgent) tot **prioriteit 3** (lage impact). Alles draait **lokaal** via je eigen Ollama-node; geen cloud, geen API-sleutels.

## ✨ Wat hij doet

**Drie modi** (schakelbaar in de zijbalk):
- **Helpdesk** — proactieve helpdesk voor beheerder én klanten: foutcodes, printers, netwerk en algemene IT-vragen. Triaget de prioriteit (P1–P3) en geeft **uit zichzelf een stappenplan/checklist** dat kan helpen.
- **Chat** — een gewone, algemene AI-chat zoals elke chatassistent.
- **Code** — levert complete, werkende code (Python, PowerShell, Bash, JavaScript, C#, SQL, HTML/CSS…) met één klik **Code opslaan**.

**Taal** — schakel met één knop tussen **Nederlands** en **Engels** (antwoorden én interface), voor andere klanten of personeel.

Verder:
- **Herkent en verklaart foutcodes** — Windows, netwerk, hardware, software, HRESULT, BSOD-stopcodes, HTTP-statussen — met de waarschijnlijke oorzaak.
- **Snelle acties** in de zijbalk: foutcode uitleggen, printerprobleem, computerprobleem, netwerkprobleem.
- **Alleen base-modellen**, standaard `qwen2.5-coder:1.5b-base`; zwaardere modellen (7b/14b/32b) installeer je in de app.
- **Aanpasbare persoonlijkheid** (system prompt) — opgeslagen in `%LOCALAPPDATA%\IT-aanhuis-AI\config.json`.
- **STOP-knop** om een lopend antwoord of download direct af te breken.

## 🪟 Installatie (Windows)

1. Pak de map uit.
2. Open **PowerShell** in de map en draai:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Dit installeert de Python-dependencies (CustomTkinter, Pillow), installeert Ollama (via winget indien beschikbaar) en haalt het standaard base-model op.

Handmatig:

```powershell
python -m pip install -r requirements.txt
# zorg dat Ollama draait:  ollama serve
```

## ▶️ Starten

```bat
run.bat
```

(of `python it_aanhuis.py`)

## 🧱 Onder de motorkap

```
IT-aanhuis-AI/
├── it_aanhuis.py            # startscript
├── run.bat / install.ps1    # Windows starter + installatie
├── assets/logo.png          # IT-aanhuis logo
└── itaanhuis/
    ├── ollama_client.py     # Ollama-koppeling + NL helpdesk-persona
    ├── config.py            # opgeslagen persoonlijkheid
    ├── control.py           # STOP / annuleren
    └── gui/
        ├── app.py           # hoofdvenster (chat + zijbalk)
        ├── dialogs.py       # model installeren / persoonlijkheid / bevestigen
        └── visuals.py       # glassy cyan achtergrond
```

## ⚠️ Let op

De assistent geeft advies op basis van een lokaal taalmodel en kan fouten maken. Voor fysieke reparaties, twijfelgevallen of kritieke P1-storingen: schakel **IT-aanhuis** in via [www.it-aanhuis.com](https://www.it-aanhuis.com/).

---

<div align="center">

**IT-aanhuis** · IT hulp bij u aan huis · [www.it-aanhuis.com](https://www.it-aanhuis.com/)

</div>
