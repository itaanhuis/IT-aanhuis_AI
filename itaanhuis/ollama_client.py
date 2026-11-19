"""
ollama_client.py - stdlib-only wrapper om de lokale Ollama API.

Levert de helpdesk-persona (Nederlands), streaming chat, model-beheer en een
code-extractor voor de 'Code opslaan'-knop. Geen externe HTTP-afhankelijkheid.
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Callable, Iterator, List, Optional

from . import OLLAMA_BASE_URL, DEFAULT_MODEL, __website__


# ── Persona's per modus ─────────────────────────────────────────────────
# HELPDESK: proactieve, gestructureerde helpdesk (bewerkbaar via de persona-editor).
DEFAULT_SYSTEM_PROMPT = (
    "Jij bent de helpdesk-AI van IT-aanhuis (www.it-aanhuis.com), een modern "
    "IT-bedrijf dat IT-hulp bij mensen thuis levert. Je ondersteunt zowel de "
    "beheerder/medewerkers van IT-aanhuis als klanten met helpdeskvragen, van "
    "prioriteit 1 (urgent, werk ligt stil) tot prioriteit 3 (lage impact).\n\n"
    "Richtlijnen:\n"
    "- Wees vriendelijk, geduldig, duidelijk en professioneel.\n"
    "- Help met foutmeldingen/foutcodes, printers en randapparatuur, netwerk, "
    "Windows, e-mail, accounts en algemene IT-vragen.\n"
    "- Herken en verklaar foutcodes (Windows, netwerk, hardware, software, "
    "HRESULT, BSOD-stopcodes, HTTP-statussen) en noem de waarschijnlijke oorzaak.\n"
    "- Wees proactief: geef uit jezelf een duidelijk, genummerd STAPPENPLAN of een "
    "checklist dat kan helpen, ook als de klant er niet expliciet om vraagt. Stel "
    "daarna een gerichte vervolgvraag.\n"
    "- Schat kort de prioriteit in (P1 urgent t/m P3 laag) wanneer relevant.\n"
    "- Houd antwoorden beknopt en praktisch. Verwijs bij fysieke reparatie, twijfel "
    "of een kritieke P1-storing naar IT-aanhuis (www.it-aanhuis.com)."
)

# CHAT: gewone, algemene AI-chat (geen ticket-structuur verplicht).
CHAT_SYSTEM_PROMPT = (
    "Jij bent de AI-assistent van IT-aanhuis. Voer een gewoon, behulpzaam en "
    "vriendelijk gesprek zoals elke AI-chatassistent, over welk onderwerp dan ook. "
    "Wees duidelijk en beknopt en denk met de gebruiker mee."
)

# CODE: lever werkende code.
CODE_SYSTEM_PROMPT = (
    "Jij bent een ervaren software-engineer bij IT-aanhuis. Lever bij een "
    "programmeervraag EEN compleet, werkend, becommentarieerd codebestand in een "
    "enkel fenced code-blok met de juiste taal-tag, daarna een korte uitleg. "
    "Geen placeholders of TODO's. Standaard Python tenzij anders gevraagd."
)

# Taal-instructie die aan elke modus wordt toegevoegd.
LANG_INSTRUCTION = {
    "nl": "Antwoord altijd in het Nederlands, ongeacht de taal van de vraag.",
    "en": "Always respond in English, regardless of the language of the question.",
}


def build_system(mode: str, language: str, helpdesk_persona: str) -> str:
    """Bouw de effectieve system prompt uit (modus + taal)."""
    base = {
        "helpdesk": helpdesk_persona,
        "chat": CHAT_SYSTEM_PROMPT,
        "code": CODE_SYSTEM_PROMPT,
    }.get(mode, helpdesk_persona)
    return base + "\n\n" + LANG_INSTRUCTION.get(language, LANG_INSTRUCTION["nl"])

# Korte voorbeelddialoog om het kleine base-model in persona te houden.
FEW_SHOT = [
    {"role": "user", "content": "hoi"},
    {"role": "assistant", "content": "Hallo! Je spreekt met de helpdesk-AI van "
     "IT-aanhuis. Waarmee kan ik je helpen?"},
    {"role": "user", "content": "mijn pc geeft error 0x80070005"},
    {"role": "assistant", "content": "Foutcode 0x80070005 betekent 'Toegang "
     "geweigerd' (Access Denied). Vaak een rechten- of antivirus-probleem.\n"
     "1) Draai de actie als Administrator.\n2) Controleer of antivirus het "
     "blokkeert.\n3) Bij Windows Update: reset de componenten.\nOm welke actie "
     "gaat het precies?"},
]

FEW_SHOT_EN = [
    {"role": "user", "content": "hi"},
    {"role": "assistant", "content": "Hello! You're talking to the IT-aanhuis "
     "helpdesk AI. How can I help you?"},
    {"role": "user", "content": "my pc shows error 0x80070005"},
    {"role": "assistant", "content": "Error 0x80070005 means 'Access Denied', "
     "usually a permissions or antivirus issue.\n1) Run the action as "
     "Administrator.\n2) Check whether antivirus is blocking it.\n3) For Windows "
     "Update: reset the components.\nWhich action exactly are you trying?"},
]

CODE_EXT = {
    "python": "py", "py": "py", "bash": "sh", "sh": "sh", "shell": "sh",
    "powershell": "ps1", "ps1": "ps1", "javascript": "js", "js": "js",
    "typescript": "ts", "html": "html", "css": "css", "c": "c", "cpp": "cpp",
    "csharp": "cs", "cs": "cs", "go": "go", "rust": "rs", "ruby": "rb",
    "php": "php", "java": "java", "json": "json", "yaml": "yaml", "sql": "sql",
    "batch": "bat", "bat": "bat", "cmd": "bat",
}


def extract_code(text: str):
    """Haal het eerste fenced code-blok uit een antwoord -> (code, extensie)."""
    m = re.search(r"```([A-Za-z0-9_+#-]*)\s*\n(.*?)```", text, re.DOTALL)
    if m:
        lang = (m.group(1) or "").strip().lower()
        return m.group(2).rstrip("\n"), CODE_EXT.get(lang, "txt")
    return text.strip(), "txt"


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL,
                 system_prompt: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    # ── status ──────────────────────────────────────────────────────────
    def is_up(self, timeout: float = 3.0) -> bool:
        try:
            with urllib.request.urlopen(self.base_url + "/", timeout=timeout):
                return True
        except Exception:
            return False

    # ── modellen ────────────────────────────────────────────────────────
    def list_models(self, timeout: float = 5.0) -> Optional[List[str]]:
        try:
            req = urllib.request.Request(self.base_url + "/api/tags")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return None

    def pull_model(self, tag: str,
                   on_progress: Optional[Callable[[str], None]] = None,
                   control=None) -> bool:
        payload = json.dumps({"name": tag, "stream": True}).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/api/pull", data=payload,
            headers={"Content-Type": "application/json"})
        last = -10
        try:
            with urllib.request.urlopen(req) as resp:
                for raw in resp:
                    if control is not None and control.cancelled:
                        if on_progress:
                            on_progress(f"{tag}: geannuleerd")
                        return False
                    line = raw.decode("utf-8").strip()
                    if not line:
                        continue
                    info = json.loads(line)
                    if "error" in info:
                        if on_progress:
                            on_progress("FOUT: " + str(info["error"]))
                        return False
                    total, done = info.get("total"), info.get("completed")
                    if total and done is not None:
                        pct = int(done * 100 / total)
                        if pct >= last + 10:
                            last = pct
                            if on_progress:
                                on_progress(f"{tag}: {pct}%")
                    elif info.get("status") and on_progress:
                        on_progress(f"{tag}: {info['status']}")
            if on_progress:
                on_progress(f"{tag}: klaar")
            return True
        except Exception as exc:  # noqa: BLE001
            if on_progress:
                on_progress(f"FOUT: {exc}")
            return False

    # ── chat ────────────────────────────────────────────────────────────
    def chat_stream(self, prompt: str, system: Optional[str] = None,
                    few_shot: bool = True, control=None) -> Iterator[str]:
        system = system or self.system_prompt
        messages = [{"role": "system", "content": system}]
        if few_shot is True:
            messages.extend(FEW_SHOT)
        elif isinstance(few_shot, list):
            messages.extend(few_shot)
        messages.append({"role": "user", "content": prompt})
        payload = json.dumps({
            "model": self.model, "stream": True,
            "options": {"temperature": 0.3, "num_predict": 500, "num_ctx": 1536},
            "messages": messages,
        }).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                for raw in resp:
                    if control is not None and control.cancelled:
                        break
                    line = raw.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    tok = d.get("message", {}).get("content", "")
                    if tok:
                        yield tok
                    if d.get("done"):
                        break
        except Exception as exc:  # noqa: BLE001
            yield (f"\n[!] Kan de Ollama-node niet bereiken op {self.base_url}: {exc}"
                   f"\n    Start Ollama en probeer opnieuw.")
