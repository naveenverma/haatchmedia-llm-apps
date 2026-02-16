from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    model_name: str | None
    enable_model_web_refresh: bool
    data_file: str
    nvidia_base_url: str
    nvidia_api_key: str | None


def get_settings() -> Settings:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model_name = os.getenv("MODEL_NAME") or None
    refresh = os.getenv("ENABLE_MODEL_WEB_REFRESH", "true").strip().lower() == "true"
    data_file = os.getenv("ASSISTANT_DATA_FILE", "assistant_state.json").strip()
    nvidia_base_url = (
        os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").strip().rstrip("/")
    )
    nvidia_api_key = os.getenv("NIM_API_KEY") or os.getenv("NVIDIA_API_KEY") or None
    return Settings(
        llm_provider=provider,
        model_name=model_name,
        enable_model_web_refresh=refresh,
        data_file=data_file,
        nvidia_base_url=nvidia_base_url,
        nvidia_api_key=nvidia_api_key,
    )
