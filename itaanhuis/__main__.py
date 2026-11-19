"""Startpunt voor `python -m itaanhuis` - start de GUI."""

import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="itaanhuis", description="IT-aanhuis Helpdesk AI (GUI).")
    parser.add_argument("--version", action="store_true", help="toon versie en stop")
    args = parser.parse_args()

    if args.version:
        from . import __app_name__, __version__
        print(f"{__app_name__} v{__version__}")
        return

    try:
        from .gui.app import main as gui_main
    except Exception as exc:  # noqa: BLE001
        print(f"[!] GUI niet beschikbaar ({exc}).")
        print("    Installeer de dependencies met:  pip install customtkinter Pillow")
        return
    gui_main()


if __name__ == "__main__":
    main()
