"""Capability registry: add new tools by implementing get_tools() and registering here."""

from __future__ import annotations

from typing import Any, Callable

from langchain_core.tools import BaseTool

# Registry: capability_id -> (get_tools_fn, env_var_for_enable)
# get_tools_fn receives **kwargs (e.g. store, settings) and returns list[BaseTool]
_CAPABILITY_REGISTRY: dict[str, tuple[Callable[..., list[BaseTool]], str | None]] = {}


def register_capability(
    capability_id: str,
    get_tools_fn: Callable[..., list[BaseTool]],
    enable_env_var: str | None = None,
) -> None:
    """Register a capability. enable_env_var: if set, capability is on only when env is truthy."""
    _CAPABILITY_REGISTRY[capability_id] = (get_tools_fn, enable_env_var)


def get_all_tools(enabled_only: bool = True, **kwargs: Any) -> list[BaseTool]:
    """Collect tools from all registered capabilities."""
    import os

    tools: list[BaseTool] = []
    for cap_id, (get_fn, env_var) in _CAPABILITY_REGISTRY.items():
        if enabled_only and env_var:
            if not os.getenv(env_var, "").strip().lower() in ("1", "true", "yes"):
                continue
        try:
            tools.extend(get_fn(**kwargs))
        except Exception as e:
            # Skip capability if it fails (e.g. missing deps)
            import warnings
            warnings.warn(f"Capability {cap_id} skipped: {e}", UserWarning)
    return tools


# Import capability modules so they register themselves (after registry is defined)
from app.capabilities import tasks_notes  # noqa: F401, E402
from app.capabilities import web_search  # noqa: F401, E402
from app.capabilities import code_evolution  # noqa: F401, E402
