#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal multi-provider LLM client for the draw.io RPA work.

Added 2026-09-03. Self-contained on purpose: this repo is the RPA study, and it
should not import the SVG_agent pipeline it is being compared against. It talks
to each provider over plain HTTPS with ``requests``, which is already installed
in RPA_drawio/venv_rpa — no SDKs to add.

Keys and model names come from D:\\SVG_agent\\.env, whose LLM_PROVIDER line
records the intended order: gemini first, OpenAI when Gemini's quota is gone,
Anthropic last.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path

import requests

ENV_PATH = Path(os.environ.get("RPA_ENV_FILE", r"D:\SVG_agent\.env"))

DEFAULT_MODELS = {
    "gemini": "gemini-flash-lite-latest",
    "openai": "gpt-5.4-mini",
    "anthropic": "claude-sonnet-5",
}
ESCALATION = ["gemini", "openai", "anthropic"]


def load_env(path: Path = ENV_PATH) -> dict:
    """Read the .env by hand.

    python-dotenv is available but the file carries trailing ``##`` notes on its
    value lines (``LLM_PROVIDER=gemini ##escalate: gemini -> openai -> anthropic``),
    and those must not become part of the value.
    """
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = re.split(r"\s+#", val, maxsplit=1)[0].strip().strip('"').strip("'")
        values[key.strip()] = val
    return values


class AllProvidersFailed(RuntimeError):
    pass


class LLMClient:
    """One call, tried against each provider in turn until one answers."""

    def __init__(self, env: dict | None = None, providers=None, log=None):
        self.env = env if env is not None else load_env()
        self.providers = providers or ESCALATION
        self.log = log or (lambda *a, **k: None)
        self.calls = []

    def _model(self, provider: str) -> str:
        # LLM_MODEL names a model for LLM_PROVIDER only; using it for a different
        # provider would send a Gemini model name to OpenAI.
        if provider == self.env.get("LLM_PROVIDER"):
            return self.env.get("LLM_MODEL") or DEFAULT_MODELS[provider]
        return DEFAULT_MODELS[provider]

    def vision(self, prompt: str, image_path: str, max_tokens: int = 4096,
               retries: int = 2) -> dict:
        """Ask a question about one image. Returns {"text", "provider", "model"}."""
        return self.vision_multi(prompt, [image_path], max_tokens, retries)

    def vision_multi(self, prompt: str, image_paths, max_tokens: int = 4096,
                     retries: int = 2) -> dict:
        """Ask a question about several images at once (reference vs produced)."""
        images = []
        for p in image_paths:
            images.append((
                base64.b64encode(Path(p).read_bytes()).decode("ascii"),
                "image/png" if str(p).lower().endswith(".png") else "image/jpeg"))
        last = None
        for provider in self.providers:
            key = self._key_for(provider)
            if not key:
                self.log("[llm] %s: no API key, skipping" % provider)
                continue
            model = self._model(provider)
            for attempt in range(retries + 1):
                try:
                    t0 = time.time()
                    text = getattr(self, "_call_" + provider)(
                        key, model, prompt, images, max_tokens)
                    self.calls.append({"provider": provider, "model": model,
                                       "seconds": round(time.time() - t0, 2)})
                    self.log("[llm] %s/%s ok in %.1fs" % (provider, model, time.time() - t0))
                    return {"text": text, "provider": provider, "model": model}
                except Exception as exc:
                    last = "%s/%s: %s" % (provider, model, exc)
                    self.log("[llm] %s attempt %d failed: %s" % (provider, attempt + 1, str(exc)[:200]))
                    # A quota or auth problem will not fix itself on retry.
                    if any(s in str(exc) for s in ("quota", "RESOURCE_EXHAUSTED", "401", "403")):
                        break
                    time.sleep(2 + 3 * attempt)
        raise AllProvidersFailed(last or "no provider had a usable key")

    def _key_for(self, provider: str):
        return {"gemini": self.env.get("GOOGLE_API_KEY"),
                "openai": self.env.get("OPENAI_API_KEY"),
                "anthropic": self.env.get("ANTHROPIC_API_KEY")}.get(provider)

    # ---- providers ---------------------------------------------------------
    def _call_gemini(self, key, model, prompt, images, max_tokens):
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               "%s:generateContent" % model)
        parts = [{"text": prompt}]
        for b64, media in images:
            parts.append({"inline_data": {"mime_type": media, "data": b64}})
        body = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens},
        }
        r = requests.post(url, params={"key": key}, json=body, timeout=180)
        if r.status_code != 200:
            raise RuntimeError("%s %s" % (r.status_code, r.text[:300]))
        data = r.json()
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)

    def _call_openai(self, key, model, prompt, images, max_tokens):
        content = [{"type": "text", "text": prompt}]
        for b64, media in images:
            content.append({"type": "image_url",
                            "image_url": {"url": "data:%s;base64,%s" % (media, b64)}})
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer %s" % key},
            json={"model": model,
                  "messages": [{"role": "user", "content": content}],
                  "max_completion_tokens": max_tokens},
            timeout=180)
        if r.status_code != 200:
            raise RuntimeError("%s %s" % (r.status_code, r.text[:300]))
        return r.json()["choices"][0]["message"]["content"]

    def _call_anthropic(self, key, model, prompt, images, max_tokens):
        content = [{"type": "text", "text": prompt}]
        for b64, media in images:
            content.append({"type": "image", "source": {"type": "base64",
                                                        "media_type": media, "data": b64}})
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
            json={"model": model, "max_tokens": max_tokens,
                  "messages": [{"role": "user", "content": content}]},
            timeout=180)
        if r.status_code != 200:
            raise RuntimeError("%s %s" % (r.status_code, r.text[:300]))
        return "".join(b.get("text", "") for b in r.json()["content"])


def extract_json(text: str):
    """Pull the JSON object out of a model reply that may be fenced or prefaced."""
    if not text:
        raise ValueError("empty reply")
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in reply: %r" % text[:200])
    body = text[start:end + 1]
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        # Small syntax slips are common in long replies and cost a whole case if
        # they are treated as fatal. Repair the two that actually occur — a
        # trailing comma before a closing bracket, and an unescaped newline inside
        # a string — and only then give up.
        repaired = re.sub(r",\s*([}\]])", r"\1", body)
        repaired = re.sub(r'"((?:[^"\\]|\\.)*)"',
                          lambda m: '"%s"' % m.group(1).replace("\n", " "), repaired,
                          flags=re.S)
        return json.loads(repaired)
