from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

import requests


MODEL_SOURCE_URLS = {
    "openai": "https://platform.openai.com/docs/models",
    "anthropic": "https://docs.anthropic.com/en/docs/about-claude/models/overview",
    "google": "https://ai.google.dev/gemini-api/docs/models",
    "nvidia": "https://docs.nvidia.com/nim/large-language-models/latest/supported-models.html",
}

# Conservative defaults chosen for compatibility with common SDKs.
# NVIDIA: curated from NIM supported-models (tool-calling capable).
FALLBACK_MODELS = {
    "openai": "gpt-5-mini",
    "anthropic": "claude-sonnet-4-5",
    "google": "gemini-2.5-pro",
    "nvidia": "meta/llama-3.1-8b-instruct",
}

MODEL_PATTERNS = {
    "openai": re.compile(r"\b(gpt-[a-z0-9.\-]+)\b", re.IGNORECASE),
    "anthropic": re.compile(r"\b(claude-[a-z0-9.\-]+)\b", re.IGNORECASE),
    "google": re.compile(r"\b(gemini-[a-z0-9.\-]+)\b", re.IGNORECASE),
    "nvidia": re.compile(r"\b(?:nvidia|meta|qwen|mistralai|openai)/[a-z0-9.\-_]+", re.IGNORECASE),
}

# Curated NVIDIA NIM models with tool-calling support (from NIM supported-models).
# Use these when web refresh is disabled or fails.
NVIDIA_RECOMMENDED_MODELS = [
    "nvidia/llama-3.3-nemotron-super-49b-v1.5",  # Best quality, parallel tool calling
    "openai/gpt-oss-120b",                        # Strong reasoning, parallel tool calling
    "qwen/qwen3-next-80b-a3b-instruct",           # Strong assistant, parallel tool calling
    "meta/llama-3.1-70b-instruct",                # Reliable general-purpose
    "nvidia/nvidia-nemotron-nano-9b-v2",          # Fast, parallel tool calling
    "meta/llama-3.1-8b-instruct",                # Lightweight, parallel tool calling
    "nvidia/llama-3.1-nemotron-nano-8b-v1",       # Agent-focused small model
    "mistralai/mistral-7b-instruct-v0.3",        # Lightweight Mistral
]


@dataclass(frozen=True)
class ModelRecommendation:
    provider: str
    model: str
    source_url: str
    refreshed_at_utc: str
    used_fallback: bool


def _pick_best_candidate(provider: str, candidates: set[str]) -> str | None:
    if not candidates:
        return None

    ranked = sorted(candidates, key=len, reverse=True)
    if provider == "openai":
        for model in ranked:
            if model.startswith("gpt-5.2"):
                return model
        for model in ranked:
            if model.startswith("gpt-5"):
                return model
    if provider == "anthropic":
        for model in ranked:
            if model.startswith("claude-opus-4-6"):
                return model
        for model in ranked:
            if model.startswith("claude-sonnet-4-5"):
                return model
    if provider == "google":
        for model in ranked:
            if model.startswith("gemini-3"):
                return model
        for model in ranked:
            if model.startswith("gemini-2.5"):
                return model
    if provider == "nvidia":
        # Prefer first curated model that appears in page
        for rec in NVIDIA_RECOMMENDED_MODELS:
            if rec.lower() in {m.lower() for m in candidates}:
                return rec

    return ranked[0] if ranked else None


def get_latest_model_recommendation(provider: str) -> ModelRecommendation:
    normalized_provider = provider.lower().strip()
    if normalized_provider not in MODEL_SOURCE_URLS:
        raise ValueError(f"Unsupported provider: {provider}")

    source_url = MODEL_SOURCE_URLS[normalized_provider]
    refreshed_at = dt.datetime.now(dt.timezone.utc).isoformat()

    # NVIDIA: use curated list; NIM catalog pages are dynamic and hard to parse reliably
    if normalized_provider == "nvidia":
        return ModelRecommendation(
            provider=normalized_provider,
            model=NVIDIA_RECOMMENDED_MODELS[0],
            source_url=source_url,
            refreshed_at_utc=refreshed_at,
            used_fallback=False,
        )

    try:
        response = requests.get(source_url, timeout=8)
        response.raise_for_status()
        text = response.text
        pattern = MODEL_PATTERNS[normalized_provider]
        matches = {item.lower() for item in pattern.findall(text)}
        selected = _pick_best_candidate(normalized_provider, matches)
        if selected:
            return ModelRecommendation(
                provider=normalized_provider,
                model=selected,
                source_url=source_url,
                refreshed_at_utc=refreshed_at,
                used_fallback=False,
            )
    except requests.RequestException:
        pass

    return ModelRecommendation(
        provider=normalized_provider,
        model=FALLBACK_MODELS[normalized_provider],
        source_url=source_url,
        refreshed_at_utc=refreshed_at,
        used_fallback=True,
    )
