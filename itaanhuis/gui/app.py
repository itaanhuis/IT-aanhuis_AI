"""
app.py - hoofdvenster van de IT-aanhuis Helpdesk AI.

Moderne, zwart-met-cyan frosted-glass GUI (alleen GUI) met drie modi en een
taalschakelaar:
  * Helpdesk - proactieve helpdesk voor beheerder en klanten: foutcodes,
               printers, netwerk, algemene IT-vragen; geeft uit zichzelf
               stappenplannen (prioriteit P1-P3).
  * Chat     - gewone, algemene AI-chat.
  * Code     - levert werkende code; met 'Code opslaan'.
  * Taal     - schakel tussen Nederlands en Engels (antwoorden + interface).

Draait lokaal via Ollama.
"""

from __future__ import annotations

import os
import threading
import tkinter.font as tkfont
import tkinter.filedialog as filedialog
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from .. import DEFAULT_MODEL, OLLAMA_BASE_URL, __app_name__, __version__
from ..ollama_client import (OllamaClient, DEFAULT_SYSTEM_PROMPT, extract_code,
                             build_system, FEW_SHOT, FEW_SHOT_EN)
from ..control import JobControl
from ..feeds import SystemStats, Weather, human_rate, human_bytes
from .. import config
from .dialogs import ConfirmDialog, InstallModelDialog, PersonaDialog, INSTALL_OPTIONS
from .visuals import make_ambient, Honeycomb

from datetime import datetime

try:
    from PIL import Image
    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

_MONO_PREF = ["JetBrains Mono", "Fira Code", "Hack", "Source Code Pro",
              "DejaVu Sans Mono", "Consolas", "Menlo", "Courier New"]
WINDOW_ALPHA = 0.95
CARD_RADIUS = 16

THEME = {
    "bg": "#05070d", "sidebar": "#0a0f1a", "box": "#0b1120",
    "glass": "#111a2b", "glass2": "#0d1524",
    "text": "#d6e6f5", "dim": "#7f93b0", "title": "#38d6f0", "sub_col": "#5aa0ff",
    "accent": "#22d3ee", "accent2": "#2a6cf0", "accent_text": "#04121a",
    "hover": "#5fe0f5", "border": "#1c2c47", "entry_bg": "#0f1a2e", "entry_text": "#eaf5ff",
    "grid": "#152238", "good": "#22d3ee", "warn": "#f5c76a", "bad": "#ff6b8a", "glow": "#38bdf8",
}

# Vaste modus-labels voor de segmented button (werken in beide talen).
MODES = ["Helpdesk", "Chat", "Code"]
MODE_KEY = {"Helpdesk": "helpdesk", "Chat": "chat", "Code": "code"}
LANGS = ["Nederlands", "English"]
LANG_KEY = {"Nederlands": "nl", "English": "en"}

STRINGS = {
    "nl": {
        "subtitle": "IT hulp bij u aan huis",
        "sec_model": "Model", "sec_mode": "Modus", "sec_lang": "Taal",
        "sec_quick": "Snelle acties", "sec_console": "Gesprek",
        "btn_refresh": "Verversen", "btn_install": "Installeren",
        "btn_persona": "Persoonlijkheid", "btn_newchat": "Nieuwe chat",
        "btn_savecode": "Code opslaan",
        "send": "VERZENDEN", "ph": "Stel je vraag...", "loading": "Bezig...",
        "user": "Jij", "system": "SYSTEEM", "error": "FOUT",
        "a_helpdesk": "HELPDESK", "a_chat": "ASSISTENT", "a_code": "CODE",
        "g_helpdesk": "Welkom bij de IT-aanhuis helpdesk. Ik help met foutcodes, "
                      "printers, netwerk en algemene IT-vragen (P1–P3) en geef uit "
                      "mezelf een stappenplan waar dat helpt. Waarmee kan ik je helpen?",
        "g_chat": "Hoi! Ik ben de IT-aanhuis assistent. Stel gerust een vraag over "
                  "wat dan ook.",
        "g_code": "Code-modus actief. Beschrijf wat het script of programma moet "
                  "doen, dan lever ik werkende code (knop 'Code opslaan').",
        "mode_note": "Modus: {m}", "lang_note": "Taal: Nederlands",
        "quick": [("Foutcode uitleggen", "Leg deze foutcode uit: "),
                  ("Printerprobleem", "Printerprobleem: "),
                  ("Computerprobleem", "Mijn computer: "),
                  ("Netwerkprobleem", "Netwerkprobleem: ")],
        "save_title": "Code opslaan", "saved": "Code opgeslagen als {f}",
        "save_err": "Opslaan mislukt: {e}",
        "model_dl": "Model {t} wordt gedownload via Ollama... even geduld.",
        "model_ok": "Model {t} is geïnstalleerd.",
        "model_stop": "Download van {t} gestopt.", "model_fail": "Installatie van {t} mislukt.",
        "persona_reset": "Persoonlijkheid teruggezet naar standaard.",
        "persona_ok": "Persoonlijkheid bijgewerkt.",
        "stopped": "[gestopt]", "stopping": "Stoppen...",
        "sec_weather": "Weer", "sec_system": "Systeem",
        "w_locating": "locatie bepalen...", "w_offline": "weer offline",
        "w_noconn": "geen verbinding",
        "w_meta": "voelt {f}° · vocht {h}% · wind {wv}km/u",
    },
    "en": {
        "subtitle": "IT help at your home",
        "sec_model": "Model", "sec_mode": "Mode", "sec_lang": "Language",
        "sec_quick": "Quick actions", "sec_console": "Conversation",
        "btn_refresh": "Refresh", "btn_install": "Install",
        "btn_persona": "Persona", "btn_newchat": "New chat",
        "btn_savecode": "Save code",
        "send": "SEND", "ph": "Ask your question...", "loading": "Working...",
        "user": "You", "system": "SYSTEM", "error": "ERROR",
        "a_helpdesk": "HELPDESK", "a_chat": "ASSISTANT", "a_code": "CODE",
        "g_helpdesk": "Welcome to the IT-aanhuis helpdesk. I help with error codes, "
                      "printers, network and general IT questions (P1–P3) and "
                      "proactively give a step plan where useful. How can I help you?",
        "g_chat": "Hi! I'm the IT-aanhuis assistant. Ask me anything.",
        "g_code": "Code mode active. Describe what the script or program should do "
                  "and I'll deliver working code (use 'Save code').",
        "mode_note": "Mode: {m}", "lang_note": "Language: English",
        "quick": [("Explain error code", "Explain this error code: "),
                  ("Printer issue", "Printer issue: "),
                  ("Computer problem", "My computer: "),
                  ("Network issue", "Network issue: ")],
        "save_title": "Save code", "saved": "Code saved as {f}",
        "save_err": "Save failed: {e}",
        "model_dl": "Model {t} is downloading via Ollama... please wait.",
        "model_ok": "Model {t} installed.",
        "model_stop": "Download of {t} stopped.", "model_fail": "Install of {t} failed.",
        "persona_reset": "Persona reset to default.",
        "persona_ok": "Persona updated.",
        "stopped": "[stopped]", "stopping": "Stopping...",
        "sec_weather": "Weather", "sec_system": "System",
        "w_locating": "locating...", "w_offline": "weather offline",
        "w_noconn": "no connection",
        "w_meta": "feels {f}° · hum {h}% · wind {wv}km/h",
    },
}


class ITaanhuisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.client = OllamaClient(OLLAMA_BASE_URL, DEFAULT_MODEL)
        self.client.system_prompt = config.get_system_prompt()
        self.mode = "helpdesk"
        self.language = "nl"
        self.is_busy = False
        self.active_control: Optional[JobControl] = None
        self._last_code = None
        self._alive = True
        self._bg_img = None
        self._bg_size = (0, 0)
        self._cfg_job = None
        self.mono = self._pick_mono()
        self._quick_btns = []
        self.stats = SystemStats()
        self.weather = Weather()
        self._last_weather = None

        self.title(f"{__app_name__} v{__version__}")
        self.geometry("1460x820")
        self.minsize(1120, 720)
        self.configure(fg_color=THEME["bg"])
        try:
            self.attributes("-alpha", WINDOW_ALPHA)
        except Exception:
            pass

        self._bg_label = ctk.CTkLabel(self, text="")
        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_chat()
        self._build_hud()
        self._render_ambient(force=True)
        self.fetch_models()
        self.after(600, self.check_first_run)
        self.after(1000, self._poll_status)
        self._greet()

        self.after(200, self._tick_system)
        threading.Thread(target=self._weather_loop, daemon=True).start()
        self.bind("<Configure>", self._on_configure)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def L(self, key):
        return STRINGS[self.language][key]

    # ── helpers ─────────────────────────────────────────────────────────
    def _pick_mono(self):
        try:
            fams = set(tkfont.families())
        except Exception:
            return None
        for f in _MONO_PREF:
            if f in fams:
                return f
        return None

    def font(self, size, weight="normal", mono=False, slant="roman"):
        kw = {"size": size, "weight": weight, "slant": slant}
        if mono and self.mono:
            kw["family"] = self.mono
        return ctk.CTkFont(**kw)

    def _card(self, parent):
        return ctk.CTkFrame(parent, corner_radius=CARD_RADIUS, border_width=1,
                            fg_color=THEME["glass"], border_color=THEME["border"])

    def _section(self, parent, text):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        lbl = ctk.CTkLabel(wrap, text=text.upper(), anchor="w", text_color=THEME["title"],
                           font=self.font(12, "bold", mono=True))
        lbl.pack(fill="x", padx=2)
        ctk.CTkFrame(wrap, height=2, corner_radius=2, fg_color=THEME["accent"]).pack(
            fill="x", padx=2, pady=(3, 0))
        return wrap, lbl

    # ── ambient ─────────────────────────────────────────────────────────
    def _render_ambient(self, force=False):
        if not _HAS_PIL:
            return
        w = max(self.winfo_width(), 1); h = max(self.winfo_height(), 1)
        if w < 50 or h < 50:
            w, h = 1160, 800
        if not force and abs(w - self._bg_size[0]) < 12 and abs(h - self._bg_size[1]) < 12:
            return
        img = make_ambient(w, h)
        if img is None:
            return
        self._bg_size = (w, h)
        self._bg_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
        self._bg_label.configure(image=self._bg_img)
        self._bg_label.lower()

    def _on_configure(self, event):
        if event.widget is not self:
            return
        if self._cfg_job is not None:
            self.after_cancel(self._cfg_job)
        self._cfg_job = self.after(180, lambda: self._render_ambient())

    # ── logo ────────────────────────────────────────────────────────────
    def _load_logo(self):
        if not _HAS_PIL:
            return None
        for p in (Path(__file__).resolve().parents[1] / "assets" / "logo.png",
                  Path(__file__).resolve().parents[2] / "assets" / "logo.png"):
            if p.is_file():
                try:
                    im = Image.open(p).convert("RGBA")
                    bbox = im.getbbox()
                    if bbox:
                        im = im.crop(bbox)
                    px = [(r, g, b, 0 if (r < 26 and g < 26 and b < 26) else a)
                          for (r, g, b, a) in im.getdata()]
                    im.putdata(px)
                    w0, h0 = im.size
                    tw = 226; th = max(1, int(h0 * tw / w0))
                    return ctk.CTkImage(light_image=im, dark_image=im, size=(tw, th))
                except Exception:
                    return None
        return None

    # ── sidebar ─────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = self._card(self)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(14, 7), pady=14)
        self.sidebar.configure(width=278)
        self.sidebar.grid_propagate(False)

        logo = self._load_logo()
        if logo is not None:
            ctk.CTkLabel(self.sidebar, image=logo, text="").pack(padx=16, pady=(18, 2))
        else:
            ctk.CTkLabel(self.sidebar, text="IT-AANHUIS", text_color=THEME["title"],
                         font=self.font(22, "bold")).pack(padx=16, pady=(18, 2))
        self.subtitle_lbl = ctk.CTkLabel(self.sidebar, text=self.L("subtitle"),
                                         text_color=THEME["sub_col"], font=self.font(11, slant="italic"))
        self.subtitle_lbl.pack(padx=16, pady=(0, 2))
        ctk.CTkLabel(self.sidebar, text="www.it-aanhuis.com", text_color=THEME["dim"],
                     font=self.font(10, mono=True)).pack(padx=16, pady=(0, 10))

        # modus
        _, self.lbl_mode = self._section(self.sidebar, self.L("sec_mode"))
        _.pack(fill="x", padx=16, pady=(2, 4))
        self.mode_seg = ctk.CTkSegmentedButton(
            self.sidebar, values=MODES, command=self._set_mode,
            font=self.font(12, "bold", mono=True), corner_radius=10,
            fg_color=THEME["glass2"], selected_color=THEME["accent"],
            selected_hover_color=THEME["hover"], unselected_color=THEME["glass2"],
            text_color=THEME["entry_text"])
        self.mode_seg.set("Helpdesk"); self.mode_seg.pack(padx=16, pady=(0, 8), fill="x")

        # taal
        _, self.lbl_lang = self._section(self.sidebar, self.L("sec_lang"))
        _.pack(fill="x", padx=16, pady=(2, 4))
        self.lang_seg = ctk.CTkSegmentedButton(
            self.sidebar, values=LANGS, command=self._set_language,
            font=self.font(12, "bold", mono=True), corner_radius=10,
            fg_color=THEME["glass2"], selected_color=THEME["accent2"],
            selected_hover_color=THEME["hover"], unselected_color=THEME["glass2"],
            text_color=THEME["entry_text"])
        self.lang_seg.set("Nederlands"); self.lang_seg.pack(padx=16, pady=(0, 10), fill="x")

        # model
        _, self.lbl_model = self._section(self.sidebar, self.L("sec_model"))
        _.pack(fill="x", padx=16, pady=(2, 4))
        self.model_dropdown = ctk.CTkOptionMenu(
            self.sidebar, values=[DEFAULT_MODEL], command=self._on_model_change,
            font=self.font(12, mono=True), corner_radius=10, fg_color=THEME["glass2"],
            button_color=THEME["accent"], button_hover_color=THEME["hover"],
            text_color=THEME["entry_text"])
        self.model_dropdown.pack(padx=16, pady=(0, 6), fill="x")
        rowm = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        rowm.pack(padx=16, fill="x")
        self.refresh_btn = ctk.CTkButton(rowm, text=self.L("btn_refresh"), command=self.fetch_models,
                                         corner_radius=10, fg_color=THEME["glass2"], hover_color=THEME["hover"],
                                         text_color=THEME["title"], font=self.font(11, "bold", mono=True))
        self.refresh_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.install_btn = ctk.CTkButton(rowm, text=self.L("btn_install"), command=self.open_install_dialog,
                                         corner_radius=10, fg_color=THEME["glass2"], hover_color=THEME["hover"],
                                         text_color=THEME["title"], font=self.font(11, "bold", mono=True))
        self.install_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))
        self.persona_btn = ctk.CTkButton(self.sidebar, text=self.L("btn_persona"), command=self.open_persona_dialog,
                                         corner_radius=10, fg_color=THEME["glass2"], hover_color=THEME["hover"],
                                         text_color=THEME["title"], font=self.font(11, "bold", mono=True))
        self.persona_btn.pack(padx=16, pady=(6, 10), fill="x")

        # snelle acties
        _, self.lbl_quick = self._section(self.sidebar, self.L("sec_quick"))
        _.pack(fill="x", padx=16, pady=(2, 4))
        self.quick_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.quick_frame.pack(padx=0, fill="x")
        self._build_quick()

        self.newchat_btn = ctk.CTkButton(self.sidebar, text=self.L("btn_newchat"), corner_radius=10,
                                         fg_color=THEME["glass2"], hover_color=THEME["hover"],
                                         text_color=THEME["text"], font=self.font(12, mono=True),
                                         command=self._new_chat)
        self.newchat_btn.pack(padx=16, pady=(8, 3), fill="x")
        self.save_code_btn = ctk.CTkButton(self.sidebar, text=self.L("btn_savecode"), corner_radius=10,
                                           state="disabled", fg_color=THEME["glass2"], hover_color=THEME["hover"],
                                           text_color=THEME["title"], font=self.font(12, "bold", mono=True),
                                           command=self._save_code)
        self.save_code_btn.pack(padx=16, pady=3, fill="x")
        self.status_label = ctk.CTkLabel(self.sidebar, text="Ollama: ...", anchor="w",
                                         font=self.font(10, mono=True), text_color=THEME["dim"])
        self.status_label.pack(padx=16, pady=(10, 0), anchor="w")

    def _build_quick(self):
        for w in self.quick_frame.winfo_children():
            w.destroy()
        self._quick_btns = []
        for label, starter in self.L("quick"):
            b = ctk.CTkButton(self.quick_frame, text=label, corner_radius=10,
                              fg_color=THEME["glass2"], hover_color=THEME["hover"],
                              text_color=THEME["text"], anchor="w", font=self.font(12, mono=True),
                              command=lambda s=starter: self._quick(s))
            b.pack(padx=16, pady=3, fill="x")
            self._quick_btns.append(b)

    # ── chat ────────────────────────────────────────────────────────────
    def _build_chat(self):
        col = ctk.CTkFrame(self, fg_color="transparent")
        col.grid(row=0, column=1, sticky="nsew", padx=(7, 14), pady=14)
        col.grid_rowconfigure(0, weight=1)
        col.grid_columnconfigure(0, weight=1)

        card = self._card(col)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        sec, self.lbl_console = self._section(card, self.L("sec_console"))
        sec.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        self.chat_box = ctk.CTkTextbox(card, font=self.font(13, mono=True), border_width=0,
                                       wrap="word", fg_color="transparent", text_color=THEME["text"])
        self.chat_box.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
        self.chat_box.configure(state="disabled")
        self.loading_label = ctk.CTkLabel(card, text="", anchor="w", text_color=THEME["title"],
                                          font=self.font(12, mono=True, slant="italic"))
        self.loading_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 10))

        row = ctk.CTkFrame(col, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        row.grid_columnconfigure(0, weight=1)
        self.input_entry = ctk.CTkEntry(row, placeholder_text=self.L("ph"),
                                        font=self.font(14, mono=True), height=46, border_width=1,
                                        corner_radius=CARD_RADIUS, fg_color=THEME["glass"],
                                        text_color=THEME["entry_text"], border_color=THEME["border"])
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self.send_message())
        self.send_btn = ctk.CTkButton(row, text=self.L("send"), width=130, height=46,
                                      corner_radius=CARD_RADIUS, fg_color=THEME["accent"],
                                      text_color=THEME["accent_text"], hover_color=THEME["hover"],
                                      font=self.font(13, "bold", mono=True), command=self.send_message)
        self.send_btn.grid(row=0, column=1, sticky="e", padx=(0, 8))
        self.stop_btn = ctk.CTkButton(row, text="■ STOP", width=92, height=46,
                                      corner_radius=CARD_RADIUS, fg_color="#8b1a1a",
                                      text_color="#ffffff", hover_color="#b22222", state="disabled",
                                      font=self.font(13, "bold", mono=True), command=self.stop_current)
        self.stop_btn.grid(row=0, column=2, sticky="e")

    # ── HUD (rechts): weer + hexagon systeem-feed ───────────────────────
    def _build_hud(self):
        col = ctk.CTkFrame(self, fg_color="transparent", width=316)
        col.grid(row=0, column=2, sticky="nsew", padx=(7, 14), pady=14)
        col.grid_propagate(False)

        wc = self._card(col)
        wc.pack(fill="x", pady=(0, 12))
        sec, self.lbl_weather = self._section(wc, self.L("sec_weather"))
        sec.pack(fill="x", padx=14, pady=(12, 6))
        self.w_loc = ctk.CTkLabel(wc, text=self.L("w_locating"), anchor="w",
                                  font=self.font(11, mono=True), text_color=THEME["dim"])
        self.w_loc.pack(fill="x", padx=14)
        rw = ctk.CTkFrame(wc, fg_color="transparent"); rw.pack(fill="x", padx=14, pady=(0, 2))
        self.w_temp = ctk.CTkLabel(rw, text="--°", font=self.font(40, "bold", mono=True),
                                   text_color=THEME["title"]); self.w_temp.pack(side="left")
        self.w_desc = ctk.CTkLabel(rw, text="", font=self.font(12), text_color=THEME["text"],
                                   justify="left"); self.w_desc.pack(side="left", padx=(10, 0))
        self.w_feels = ctk.CTkLabel(wc, text="", anchor="w", font=self.font(10, mono=True),
                                    text_color=THEME["sub_col"]); self.w_feels.pack(fill="x", padx=14, pady=(0, 8))
        self.w_days = ctk.CTkFrame(wc, fg_color="transparent"); self.w_days.pack(fill="x", padx=14, pady=(0, 12))
        self.w_day_rows = []
        for _ in range(3):
            r = ctk.CTkLabel(self.w_days, text="", anchor="w", font=self.font(10, mono=True),
                             text_color=THEME["text"]); r.pack(fill="x"); self.w_day_rows.append(r)

        sc = self._card(col)
        sc.pack(fill="both", expand=True)
        sec2, self.lbl_system = self._section(sc, self.L("sec_system"))
        sec2.pack(fill="x", padx=14, pady=(12, 6))
        holder = ctk.CTkFrame(sc, fg_color="transparent"); holder.pack(expand=True)
        self.honey = Honeycomb(holder, THEME); self.honey.pack(padx=6, pady=(0, 6))
        self.sys_backend = ctk.CTkLabel(sc, text="", anchor="e", font=self.font(9, mono=True),
                                        text_color=THEME["dim"]); self.sys_backend.pack(fill="x", padx=14, pady=(0, 8))

    def _tick_system(self):
        if not self._alive:
            return
        threading.Thread(target=self._sample_and_push, daemon=True).start()
        self.after(1000, self._tick_system)

    def _sample_and_push(self):
        try:
            data = self.stats.sample()
        except Exception:
            return
        if self._alive:
            self.after(0, self._update_system, data)

    @staticmethod
    def _ckey(pct):
        return "bad" if pct >= 90 else "warn" if pct >= 70 else "accent"

    def _update_system(self, d):
        if not self._alive:
            return
        try:
            self.honey.set("cpu", d["cpu"], f"{d['cpu']:.0f}%", "CPU", self._ckey(d["cpu"]))
            if d["gpu"] is None:
                self.honey.set("gpu", None, "n/a", "GPU", "dim")
            else:
                self.honey.set("gpu", d["gpu"], f"{d['gpu']:.0f}%", "GPU", self._ckey(d["gpu"]))
            self.honey.set("ram", d["ram_pct"], f"{d['ram_pct']:.0f}%", "RAM", self._ckey(d["ram_pct"]))
            self.honey.set("disk", d["disk_pct"], f"{d['disk_pct']:.0f}%", "DISK", self._ckey(d["disk_pct"]))
            netpct = min(100.0, d["net_down"] / (5 * 1024 * 1024) * 100)
            down = d["net_down"]
            short = (f"{down:.0f}B" if down < 1000 else
                     f"{down/1000:.0f}k" if down < 1_000_000 else f"{down/1_000_000:.1f}M")
            self.honey.set("net", netpct, short, "NET↓", "glow")
            now = datetime.now()
            self.honey.set_clock(now.strftime("%H:%M"), now.strftime("%d %b"), now.second)
            self.sys_backend.configure(text=f"src: {d['backend']}")
        except Exception:
            pass

    def _weather_loop(self):
        import time
        while self._alive:
            data = self.weather.fetch()
            if self._alive:
                self.after(0, self._update_weather, data)
            for _ in range(900):
                if not self._alive:
                    return
                time.sleep(1)

    def _update_weather(self, w):
        if not self._alive:
            return
        self._last_weather = w
        try:
            if w is None:
                self.w_loc.configure(text=self.L("w_offline"))
                self.w_temp.configure(text="--°")
                self.w_desc.configure(text=self.L("w_noconn"))
                self.w_feels.configure(text="")
                for r in self.w_day_rows:
                    r.configure(text="")
                self.honey.set("weather", None, "--°", "WX", "accent2")
                return
            self.w_loc.configure(text=f"◉ {w['location']}")
            self.w_temp.configure(text=f"{w['temp']}°")
            self.w_desc.configure(text=w["desc"])
            self.w_feels.configure(text=self.L("w_meta").format(f=w["feels"], h=w["humidity"], wv=w["wind"]))
            for row, day in zip(self.w_day_rows, w["days"]):
                row.configure(text=f"{day['date'][5:]}  {day['hi']:>3}°/{day['lo']:>3}°  {day['desc'][:16]}")
            try:
                t = float(w["temp"]); pct = max(0.0, min(100.0, (t + 10) / 50 * 100))
            except Exception:
                pct = None
            self.honey.set("weather", pct, f"{w['temp']}°", "WX", "accent2")
        except Exception:
            pass

    def _greet(self):
        self.append_chat(self._assistant_label(), self.L(f"g_{self.mode}"))

    def _assistant_label(self):
        return self.L(f"a_{self.mode}")

    # ── modus / taal ────────────────────────────────────────────────────
    def _set_mode(self, value):
        self.mode = MODE_KEY.get(value, "helpdesk")
        self.append_chat(self.L("system"),
                         self.L("mode_note").format(m=value) + "\n" + self.L(f"g_{self.mode}"))

    def _set_language(self, value):
        self.language = LANG_KEY.get(value, "nl")
        self._apply_language()
        self.append_chat(self.L("system"), self.L("lang_note"))

    def _apply_language(self):
        self.subtitle_lbl.configure(text=self.L("subtitle"))
        self.lbl_mode.configure(text=self.L("sec_mode").upper())
        self.lbl_lang.configure(text=self.L("sec_lang").upper())
        self.lbl_model.configure(text=self.L("sec_model").upper())
        self.lbl_quick.configure(text=self.L("sec_quick").upper())
        self.lbl_console.configure(text=self.L("sec_console").upper())
        self.refresh_btn.configure(text=self.L("btn_refresh"))
        self.install_btn.configure(text=self.L("btn_install"))
        self.persona_btn.configure(text=self.L("btn_persona"))
        self.newchat_btn.configure(text=self.L("btn_newchat"))
        self.save_code_btn.configure(text=self.L("btn_savecode"))
        self.send_btn.configure(text=self.L("send"))
        self.input_entry.configure(placeholder_text=self.L("ph"))
        self.lbl_weather.configure(text=self.L("sec_weather").upper())
        self.lbl_system.configure(text=self.L("sec_system").upper())
        self._update_weather(self._last_weather)   # herrender weer in nieuwe taal
        self._build_quick()

    # ── quick / nieuwe chat ─────────────────────────────────────────────
    def _quick(self, starter):
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, starter)
        self.input_entry.focus_set(); self.input_entry.icursor("end")

    def _new_chat(self):
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self._greet()

    # ── modellen ────────────────────────────────────────────────────────
    def _on_model_change(self, value): self.client.model = value

    def fetch_models(self):
        def run():
            models = self.client.list_models()
            if models and self._alive:
                self.after(0, lambda: self._apply_models(models))
        threading.Thread(target=run, daemon=True).start()

    def _apply_models(self, models):
        self.model_dropdown.configure(values=models)
        if DEFAULT_MODEL in models:
            self.model_dropdown.set(DEFAULT_MODEL); self.client.model = DEFAULT_MODEL
        else:
            self.model_dropdown.set(models[0]); self.client.model = models[0]

    def check_first_run(self):
        models = self.client.list_models()
        if models is None:
            return
        known = [tag for tag, _ in INSTALL_OPTIONS.values()]
        if not any(m in known for m in models):
            self.open_install_dialog()

    def open_install_dialog(self):
        tag = InstallModelDialog(self, THEME).show()
        if tag:
            self.install_model(tag)

    def install_model(self, tag):
        control = self._new_job()
        self._set_busy(True)
        self._loading(True, f"{tag}...")
        self.append_chat(self.L("system"), self.L("model_dl").format(t=tag))

        def run():
            ok = self.client.pull_model(
                tag, on_progress=lambda l: self.after(0, self._append_line, f"  {l}"),
                control=control)
            if ok:
                self.after(0, self.append_chat, self.L("system"), self.L("model_ok").format(t=tag))
                self.after(0, self.fetch_models)
            elif control.cancelled:
                self.after(0, self.append_chat, self.L("system"), self.L("model_stop").format(t=tag))
            else:
                self.after(0, self.append_chat, self.L("error"), self.L("model_fail").format(t=tag))
            self.after(0, lambda: self._set_busy(False))
        threading.Thread(target=run, daemon=True).start()

    def open_persona_dialog(self):
        res = PersonaDialog(self, self.client.system_prompt, THEME).show()
        if res is None:
            return
        kind, text = res
        if kind == "reset":
            config.reset_system_prompt(); self.client.system_prompt = DEFAULT_SYSTEM_PROMPT
            self.append_chat(self.L("system"), self.L("persona_reset"))
        else:
            self.client.system_prompt = text; config.set_system_prompt(text)
            self.append_chat(self.L("system"), self.L("persona_ok"))

    # ── status ──────────────────────────────────────────────────────────
    def _poll_status(self):
        if not self._alive:
            return
        def run():
            up = self.client.is_up()
            if self._alive:
                self.after(0, lambda: self.status_label.configure(
                    text=f"Ollama: {'online' if up else 'offline'}",
                    text_color=THEME["accent"] if up else THEME["dim"]))
        threading.Thread(target=run, daemon=True).start()
        self.after(5000, self._poll_status)

    # ── laad-animatie ───────────────────────────────────────────────────
    def _loading(self, active, text=None):
        if not active:
            self.loading_label.configure(text=""); return
        chars = ["⠋", "⠙", "⠹", "⠸", "⠼",
                 "⠴", "⠦", "⠧", "⠇", "⠏"]
        def anim(step=0):
            if not self.is_busy or not self._alive:
                self.loading_label.configure(text=""); return
            self.loading_label.configure(text=f"{chars[step % len(chars)]} {text or self.L('loading')}")
            self.after(100, lambda: anim(step + 1))
        anim()

    # ── chat output ─────────────────────────────────────────────────────
    def append_chat(self, sender, message):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{sender}:\n{message}\n\n")
        self.chat_box.see("end"); self.chat_box.configure(state="disabled")

    def _append_line(self, line):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", line + "\n")
        self.chat_box.see("end"); self.chat_box.configure(state="disabled")

    def _insert(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", text)
        self.chat_box.see("end"); self.chat_box.configure(state="disabled")

    def _set_busy(self, busy):
        self.is_busy = busy
        self.send_btn.configure(state="disabled" if busy else "normal")
        self.stop_btn.configure(state="normal" if busy else "disabled")
        self._loading(busy)

    def _new_job(self):
        self.active_control = JobControl()
        return self.active_control

    def stop_current(self):
        if self.active_control is not None:
            self.active_control.cancel()
            self._append_line("[!] " + self.L("stopping"))
            self.loading_label.configure(text=self.L("stopping"))

    # ── verzenden ───────────────────────────────────────────────────────
    def send_message(self):
        if self.is_busy:
            return
        prompt = self.input_entry.get().strip()
        if not prompt:
            return
        self.input_entry.delete(0, "end")
        self.append_chat(self.L("user"), prompt)

        mode, lang = self.mode, self.language
        system = build_system(mode, lang, self.client.system_prompt)
        if mode == "helpdesk":
            shots = FEW_SHOT if lang == "nl" else FEW_SHOT_EN
        else:
            shots = False

        control = self._new_job()
        self._set_busy(True)
        self.append_chat(self._assistant_label(), "")
        buf = []

        def run():
            try:
                for tok in self.client.chat_stream(prompt, system=system,
                                                   few_shot=shots, control=control):
                    buf.append(tok)
                    self.after(0, self._insert, tok)
                if control.cancelled:
                    self.after(0, self._insert, "  " + self.L("stopped"))
                else:
                    full = "".join(buf)
                    if "```" in full:
                        code, ext = extract_code(full)
                        if code:
                            self._last_code = (code, ext)
                            self.after(0, lambda: self.save_code_btn.configure(state="normal"))
            finally:
                self.after(0, self._insert, "\n\n")
                self.after(0, lambda: self._set_busy(False))
        threading.Thread(target=run, daemon=True).start()

    def _save_code(self):
        if not self._last_code:
            return
        code, ext = self._last_code
        path = filedialog.asksaveasfilename(title=self.L("save_title"),
                                            defaultextension=f".{ext}",
                                            initialfile=f"it-aanhuis-code.{ext}")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(code)
            self.append_chat(self.L("system"), self.L("saved").format(f=os.path.basename(path)))
        except Exception as exc:  # noqa: BLE001
            self.append_chat(self.L("error"), self.L("save_err").format(e=exc))

    def _on_close(self):
        self._alive = False
        if self.active_control is not None:
            self.active_control.cancel()
        self.destroy()


def main():
    app = ITaanhuisApp()
    app.mainloop()


if __name__ == "__main__":
    main()
