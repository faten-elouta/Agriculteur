#!/usr/bin/env python3
"""
farmer_journey.py — Agent Farmer Journey v0.

Teste l'application Terroir Context Agents avec AppTest.
Détecte les paramètres de query et valide le comportement de l'UI.
"""

from __future__ import annotations

import sys
from typing import Any

sys.path.insert(0, "/Users/fatenjibaoui/Agriculteur")

from streamlit.testing.v1 import AppTest
from services.datahub_client import DataHubClient
from services.real_data_service import fetch_real_territory


def main() -> None:
    at = AppTest.from_file("/Users/fatenjibaoui/Agriculteur/app.py", default_timeout=120)

    at.query_params["view"] = "application"
    at.run()

    dump(at, "ÉCRAN 1 — sélection commune/parcelle")
    print()

    at.query_params["view"] = "donnees"
    at.run()

    dump(at, "ÉCRAN 2 — données DataHub")
    print()

    at.query_params["view"] = "contact"
    at.run()

    dump(at, "ÉCRAN 3 — contact")
    print()


def dump(at: Any, label: str) -> None:
    print(f"=== {label} ===")
    try:
        view = at.session_state["view"]
    except KeyError:
        view = "N/A"
    print(f"  session_state.view: {view}")
    print(f"  query_params: {at.query_params}")
    if at.exception:
        for exc in at.exception:
            print(f"  EXCEPTION: {exc}")

    if hasattr(at, "radio"):
        for r in at.radio:
            print(f"  R: {short(r.label, 60)} opts: {[short(o, 25) for o in r.options][:6]}")

    if hasattr(at, "button"):
        print(f"  buttons: {len(at.button)}")

    if hasattr(at, "text_input"):
        print(f"  text_inputs: {len(at.text_input)}")


def short(s: str, max_len: int = 60) -> str:
    return s[:max_len] if len(s) > max_len else s


if __name__ == "__main__":
    main()