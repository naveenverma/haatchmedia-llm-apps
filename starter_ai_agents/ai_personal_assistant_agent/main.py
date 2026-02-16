from __future__ import annotations

import os

from app.agent import build_agent_executor, run_chat_loop
from app.config import get_settings
from app.model_factory import build_chat_model
from app.storage import StateStore
from app.tools import build_tools


def main() -> None:
    settings = get_settings()
    store = StateStore(settings.data_file)
    controller_mode = os.getenv("ENABLE_CODE_EVOLUTION", "").strip().lower() in ("1", "true", "yes")

    def make_agent():
        tools = build_tools(store)
        llm, _, _ = build_chat_model(
            provider=settings.llm_provider,
            explicit_model_name=settings.model_name,
            enable_web_refresh=settings.enable_model_web_refresh,
            nvidia_base_url=settings.nvidia_base_url if settings.llm_provider == "nvidia" else None,
            nvidia_api_key=settings.nvidia_api_key if settings.llm_provider == "nvidia" else None,
        )
        return build_agent_executor(llm=llm, tools=tools, controller_mode=controller_mode)

    llm, chosen_model, used_fallback = build_chat_model(
        provider=settings.llm_provider,
        explicit_model_name=settings.model_name,
        enable_web_refresh=settings.enable_model_web_refresh,
        nvidia_base_url=settings.nvidia_base_url if settings.llm_provider == "nvidia" else None,
        nvidia_api_key=settings.nvidia_api_key if settings.llm_provider == "nvidia" else None,
    )
    tools = build_tools(store)
    executor = build_agent_executor(llm=llm, tools=tools, controller_mode=controller_mode)

    mode = "controller (code evolution on)" if controller_mode else "standard"
    print(
        f"Booted with provider={settings.llm_provider} model={chosen_model} fallback={used_fallback} [{mode}]"
    )
    run_chat_loop(
        executor,
        rebuild_agent_fn=make_agent if controller_mode else None,
    )


if __name__ == "__main__":
    main()
