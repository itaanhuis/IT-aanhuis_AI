"""
IT-aanhuis Helpdesk AI
======================

Een Windows desktop-assistent (GUI) voor IT-aanhuis (www.it-aanhuis.com).
De helpdesk-AI draait volledig lokaal via Ollama (base-modellen), spreekt
standaard Nederlands en ondersteunt zowel medewerkers als klanten met
helpdeskvragen van prioriteit 1 t/m 3: foutcodes herkennen, computervragen,
en programmeren in meerdere talen.

Merk: IT-aanhuis  ·  IT hulp bij u aan huis
"""

__version__ = "1.0.0"
__app_name__ = "IT-aanhuis Helpdesk AI"
__brand__ = "IT-aanhuis"
__website__ = "https://www.it-aanhuis.com/"

# Alleen base-modellen; standaard het lichte coder-model.
DEFAULT_MODEL = "qwen2.5-coder:1.5b-base"
OLLAMA_BASE_URL = "http://localhost:11434"
