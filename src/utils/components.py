# src/utils/components.py — Reusable UI fragments
import html as html_module


def escape(text: str) -> str:
    return html_module.escape(text, quote=True)
