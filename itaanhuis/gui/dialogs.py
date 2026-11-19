"""
dialogs.py - modale dialogen voor de IT-aanhuis Helpdesk AI (Nederlands).

  * ConfirmDialog      - generieke ja/nee.
  * InstallModelDialog - base-model installeren ('Model installeren').
  * PersonaDialog      - de persona (system prompt) aanpassen.
"""

from __future__ import annotations

from typing import Optional, Tuple

import customtkinter as ctk

from ..ollama_client import DEFAULT_SYSTEM_PROMPT

# Alleen base-modellen; standaard 1.5b-base.
INSTALL_OPTIONS = {
    "default": ("qwen2.5-coder:1.5b-base", "Licht (standaard)"),
    "1": ("qwen2.5-coder:7b-base", "Middel, ~4.7 GB VRAM"),
    "2": ("qwen2.5-coder:14b-base", "Sterk, ~9 GB VRAM"),
    "3": ("qwen2.5-coder:32b-base", "Vlaggenschip, ~20 GB VRAM"),
}


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, body: str, theme: dict):
        super().__init__(master)
        self.result = False
        self.title(title)
        self.geometry("480x300")
        self.configure(fg_color=theme["sidebar"])
        self.transient(master)
        self.after(150, self.grab_set)
        ctk.CTkLabel(self, text=title, text_color=theme["title"],
                     font=ctk.CTkFont(size=15, weight="bold")).pack(padx=20, pady=(18, 6))
        box = ctk.CTkTextbox(self, fg_color=theme["box"], text_color=theme["text"],
                             border_color=theme["border"], border_width=1,
                             font=ctk.CTkFont(size=12), wrap="word")
        box.pack(padx=20, pady=6, fill="both", expand=True)
        box.insert("end", body); box.configure(state="disabled")
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(padx=20, pady=(6, 16), fill="x")
        ctk.CTkButton(row, text="Ja", fg_color=theme["accent"], text_color=theme["accent_text"],
                      hover_color=theme["hover"], command=self._yes).pack(
            side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(row, text="Nee", fg_color=theme["glass2"], hover_color=theme["hover"],
                      text_color=theme["title"], command=self._no).pack(
            side="left", expand=True, fill="x", padx=(6, 0))
        self.protocol("WM_DELETE_WINDOW", self._no)

    def _yes(self): self.result = True; self.destroy()
    def _no(self): self.result = False; self.destroy()

    def show(self) -> bool:
        self.master.wait_window(self)
        return self.result


class InstallModelDialog(ctk.CTkToplevel):
    def __init__(self, master, theme: dict):
        super().__init__(master)
        self.chosen: Optional[str] = None
        self.title("Model installeren")
        self.geometry("470x340")
        self.configure(fg_color=theme["sidebar"])
        self.transient(master)
        self.after(150, self.grab_set)
        self._theme = theme
        self.label = ctk.CTkLabel(self, text="", text_color=theme["text"], wraplength=420,
                                  font=ctk.CTkFont(size=13), justify="left")
        self.label.pack(padx=20, pady=(20, 10))
        self.holder = ctk.CTkFrame(self, fg_color="transparent")
        self.holder.pack(padx=20, pady=10, fill="x")
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._step_default()

    def _clear(self):
        for w in self.holder.winfo_children():
            w.destroy()

    def _choose(self, tag): self.chosen = tag; self.destroy()
    def _cancel(self): self.chosen = None; self.destroy()

    def _step_default(self):
        th = self._theme; self._clear()
        tag, desc = INSTALL_OPTIONS["default"]
        self.label.configure(text=f"Het standaard base-model installeren?\n{tag} - {desc}\n\n[J/n]")
        ctk.CTkButton(self.holder, text="J (standaard installeren)", fg_color=th["accent"],
                      text_color=th["accent_text"], hover_color=th["hover"],
                      command=lambda: self._choose(tag)).pack(pady=5, fill="x")
        ctk.CTkButton(self.holder, text="n (zwaarder model kiezen)", fg_color=th["glass2"],
                      hover_color=th["hover"], text_color=th["title"],
                      command=self._step_pick).pack(pady=5, fill="x")

    def _step_pick(self):
        th = self._theme; self._clear()
        self.label.configure(text="Kies een zwaarder base-model:")
        for key in ("1", "2", "3"):
            tag, desc = INSTALL_OPTIONS[key]
            ctk.CTkButton(self.holder, text=f"{key}) {tag} - {desc}", fg_color=th["glass2"],
                          hover_color=th["hover"], text_color=th["title"],
                          command=lambda t=tag: self._choose(t)).pack(pady=5, fill="x")
        ctk.CTkButton(self.holder, text="Annuleren", fg_color=th["box"],
                      hover_color=th["hover"], text_color=th["text"],
                      command=self._cancel).pack(pady=5, fill="x")

    def show(self) -> Optional[str]:
        self.master.wait_window(self)
        return self.chosen


class PersonaDialog(ctk.CTkToplevel):
    """Persona (system prompt) aanpassen. show() -> ('save', text) | ('reset', None) | None."""

    def __init__(self, master, current: str, theme: dict):
        super().__init__(master)
        self.result: Optional[Tuple[str, Optional[str]]] = None
        self.title("Persoonlijkheid bewerken")
        self.geometry("640x480")
        self.configure(fg_color=theme["sidebar"])
        self.transient(master)
        self.after(150, self.grab_set)
        ctk.CTkLabel(self, text="PERSOONLIJKHEID / SYSTEM PROMPT", text_color=theme["title"],
                     font=ctk.CTkFont(size=15, weight="bold")).pack(padx=20, pady=(18, 2))
        ctk.CTkLabel(self, text="Dit bepaalt wie de helpdesk-AI is en hoe hij antwoordt.",
                     text_color=theme["sub_col"], font=ctk.CTkFont(size=11)).pack(padx=20, pady=(0, 10))
        self.box = ctk.CTkTextbox(self, fg_color=theme["box"], text_color=theme["entry_text"],
                                  border_color=theme["border"], border_width=1,
                                  wrap="word", corner_radius=8)
        self.box.pack(padx=20, pady=6, fill="both", expand=True)
        self.box.insert("1.0", current)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(padx=20, pady=(8, 16), fill="x")
        ctk.CTkButton(row, text="Opslaan", fg_color=theme["accent"], text_color=theme["accent_text"],
                      hover_color=theme["hover"], command=self._save).pack(
            side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(row, text="Standaard herstellen", fg_color=theme["glass2"],
                      hover_color=theme["hover"], text_color=theme["title"],
                      command=self._reset).pack(side="left", expand=True, fill="x", padx=6)
        ctk.CTkButton(row, text="Annuleren", fg_color=theme["box"], hover_color=theme["hover"],
                      text_color=theme["text"], command=self._cancel).pack(
            side="left", expand=True, fill="x", padx=(6, 0))
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _save(self):
        text = self.box.get("1.0", "end").strip()
        self.result = ("save", text or DEFAULT_SYSTEM_PROMPT); self.destroy()

    def _reset(self):
        self.box.delete("1.0", "end"); self.box.insert("1.0", DEFAULT_SYSTEM_PROMPT)
        self.result = ("reset", None); self.destroy()

    def _cancel(self): self.result = None; self.destroy()

    def show(self):
        self.master.wait_window(self)
        return self.result
