from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.model_recommender import FALLBACK_MODELS, get_latest_model_recommendation


def build_chat_model(
    provider: str,
    explicit_model_name: str | None = None,
    enable_web_refresh: bool = True,
    nvidia_base_url: str | None = None,
    nvidia_api_key: str | None = None,
):
    normalized_provider = provider.lower().strip()
    if normalized_provider not in FALLBACK_MODELS:
        raise ValueError(
            f"Unsupported provider '{provider}'. Use one of: "
            f"{', '.join(sorted(FALLBACK_MODELS.keys()))}"
        )

    model_name = explicit_model_name
    used_fallback = False

    if not model_name:
        if enable_web_refresh:
            recommendation = get_latest_model_recommendation(normalized_provider)
            model_name = recommendation.model
            used_fallback = recommendation.used_fallback
        else:
            model_name = FALLBACK_MODELS[normalized_provider]
            used_fallback = True

    if normalized_provider == "openai":
        llm = ChatOpenAI(model=model_name, temperature=0.2)
    elif normalized_provider == "anthropic":
        llm = ChatAnthropic(model=model_name, temperature=0.2)
    elif normalized_provider == "google":
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2)
    elif normalized_provider == "nvidia":
        base_url = nvidia_base_url or "https://integrate.api.nvidia.com/v1"
        api_key = nvidia_api_key or ""
        llm = ChatOpenAI(
            model=model_name,
            temperature=0.2,
            base_url=base_url,
            api_key=api_key,
        )
    else:
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2)

    return llm, model_name, used_fallback
