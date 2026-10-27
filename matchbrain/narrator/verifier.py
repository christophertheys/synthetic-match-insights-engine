"""Numeric grounding: every number in a caption must come from formatted fact slots."""

from __future__ import annotations

import re

from matchbrain.narrator.templates import slots

NUM = re.compile(r"(?:(?<!\d)[+-])?\d+(?:\.\d+)?")


def allowed_numbers(fact: dict) -> set[str]:
    allowed: set[str] = set()
    for value in slots(fact).values():
        text = str(value).lstrip("+")
        if NUM.fullmatch(str(value)) or NUM.fullmatch(text):
            allowed.add(text)
            allowed.add(str(value).lstrip("+"))
        for found in NUM.findall(str(value)):
            allowed.add(found.lstrip("+"))
    return {a for a in allowed if a and a != "-"}


def verify(text: str, fact: dict) -> tuple[bool, list[str]]:
    allowed = allowed_numbers(fact)
    found = [n.lstrip("+") for n in NUM.findall(text)]
    bad = [n for n in found if n not in allowed]
    evidence = fact.get("evidence") or []
    return (not bad and bool(evidence)), bad
