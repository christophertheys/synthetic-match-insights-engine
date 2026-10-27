"""Narrator: template captions by default, Azure AI Foundry / GitHub Models when configured."""

from __future__ import annotations

import json
import os
from functools import lru_cache

from matchbrain.narrator.templates import render_template, render_why, slots
from matchbrain.narrator.verifier import verify


def provider_name() -> str:
    if os.getenv("AZURE_OPENAI_ENDPOINT") and (os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")):
        return "azure_openai"
    if os.getenv("GITHUB_MODELS_TOKEN"):
        return "github_models"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "templates"


@lru_cache(maxsize=1)
def _client():
    name = provider_name()
    if name == "templates":
        return None, None
    from openai import OpenAI, AzureOpenAI

    if name == "azure_openai":
        client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
        model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        return client, model
    if name == "github_models":
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=os.environ["GITHUB_MODELS_TOKEN"],
        )
        model = os.getenv("GITHUB_MODELS_MODEL", "gpt-4o-mini")
        return client, model
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return client, os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def llm_complete(system: str, user: str) -> str | None:
    client, model = _client()
    if client is None:
        return None
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    return data.get("caption") or data.get("recap")


class Narrator:
    def render(self, fact: dict, persona: dict) -> tuple[str, str, bool]:
        mode = persona.get("mode") or "casual"
        lang = persona.get("lang") or "en"
        headline = render_template(fact, mode, lang)
        why = render_why(fact, lang)
        ok, _ = verify(headline, fact)
        return headline, why, ok

    def polish(self, fact: dict, persona: dict, template_text: str) -> str:
        """Optional Azure/Foundry upgrade. Falls back to the template if unverified."""
        if provider_name() == "templates":
            return template_text
        try:
            caption = llm_complete(
                "You are a football broadcast captioner. Use ONLY numbers present in the facts JSON. "
                "Reply as JSON {\"caption\": str}. One sentence, under 22 words. No extra statistics.",
                json.dumps(
                    {"lang": persona.get("lang"), "mode": persona.get("mode"), "facts": slots(fact), "template": template_text},
                    ensure_ascii=False,
                ),
            )
        except Exception:
            return template_text
        if not caption:
            return template_text
        ok, _ = verify(caption, fact)
        return caption if ok else template_text

    def recap(self, facts: list[dict], persona: dict, snapshot: dict) -> str:
        lang = persona.get("lang") or "en"
        mode = persona.get("mode") or "casual"
        lines = [render_template(f, mode, lang) for f in facts[:8]]
        fallback = " ".join(lines)
        if provider_name() == "templates":
            return fallback
        payload = {
            "lang": lang,
            "mode": mode,
            "score": snapshot.get("score"),
            "facts": [slots(f) | {"kind": f["kind"], "why": render_why(f, lang)} for f in facts[:8]],
        }
        try:
            text = llm_complete(
                "Write a 2-3 sentence match recap. Use ONLY numbers in the JSON. Reply as JSON {\"recap\": str}.",
                json.dumps(payload, ensure_ascii=False),
            )
        except Exception:
            return fallback
        return text or fallback
