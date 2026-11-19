"""
config.py - opgeslagen instellingen (o.a. aangepaste persona).

Locatie: %LOCALAPPDATA%\\IT-aanhuis-AI\\config.json (Windows), met val-terug naar
de home-map. Alles is best-effort: ontbrekende/onschrijfbare config breekt de app
niet, er wordt dan teruggevallen op de standaardwaarden.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

from .ollama_client import DEFAULT_SYSTEM_PROMPT


def _dir() -> Path:
    override = os.environ.get("ITAANHUIS_CONFIG_DIR")
    if override:
        return Path(override)
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "IT-aanhuis-AI"


CONFIG_DIR = _dir()
CONFIG_FILE = CONFIG_DIR / "config.json"


def load() -> Dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(cfg: Dict) -> bool:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def get_system_prompt() -> str:
    val = load().get("system_prompt")
    return val.strip() if isinstance(val, str) and val.strip() else DEFAULT_SYSTEM_PROMPT


def set_system_prompt(text: str) -> bool:
    cfg = load()
    text = (text or "").strip()
    if not text:
        cfg.pop("system_prompt", None)
    else:
        cfg["system_prompt"] = text
    return save(cfg)


def reset_system_prompt() -> bool:
    cfg = load()
    cfg.pop("system_prompt", None)
    return save(cfg)
