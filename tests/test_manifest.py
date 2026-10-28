"""The options panel stays short and reads in order."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
OPTIONS = MANIFEST["cell_options"]

ORDER = ["location", "layout", "months", "show_eclipses", "only_visible", "title"]
UP_FRONT = ["location", "layout", "show_eclipses", "only_visible"]


def test_manifest_basics():
    assert MANIFEST["name"] == "Meteors & Eclipses"
    assert MANIFEST["icon"] == "ph-shooting-star"
    assert MANIFEST["category"] == "time"
    assert MANIFEST["requires"] == []
    assert MANIFEST["render"]["needs_network"] is False
    assert MANIFEST["supports"]["sizes"] == ["xs", "sm", "md", "lg"]


def test_option_names_and_order():
    assert [o["name"] for o in OPTIONS] == ORDER
    assert "label" not in ORDER


def test_few_options_up_front():
    front = [
        o["name"] for o in OPTIONS if not o.get("show_if") and not o.get("advanced")
    ]
    assert front == UP_FRONT
    assert len(front) <= 5


def test_show_if_refers_to_real_options():
    names = {o["name"] for o in OPTIONS}
    for o in OPTIONS:
        for key in o.get("show_if") or {}:
            assert key in names


def test_no_em_dashes_anywhere():
    for name in (
        "plugin.json",
        "README.md",
        "client.js",
        "client.css",
        "server.py",
        "astro.py",
        "data.py",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert chr(0x2014) not in text, name
