from __future__ import annotations

from app.capabilities import get_all_tools


def build_tools(store, **kwargs):
    """Build tools from all registered capabilities. Pass store= and any other kwargs."""
    return get_all_tools(store=store, **kwargs)
