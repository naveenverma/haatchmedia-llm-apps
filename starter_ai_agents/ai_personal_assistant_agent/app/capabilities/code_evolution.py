"""Code evolution capability - controller can add new capabilities when agents report gaps."""

from __future__ import annotations

import importlib
import re
import subprocess
from pathlib import Path

from langchain_core.tools import tool

from app.capabilities import register_capability


def _get_tools(**kwargs):
    @tool
    def add_capability(
        capability_name: str,
        code: str,
        pip_deps: str = "",
    ) -> str:
        """Add a new capability when you cannot do something with current tools.
        Use after web_search to find how to implement it. capability_name must be a valid
        Python identifier (e.g. email_fetch). code must be a complete Python module that:
        - defines _get_tools(**kwargs) returning list of @tool functions
        - calls register_capability('id', _get_tools, enable_env_var=None)
        pip_deps: comma-separated package names to install (e.g. 'imapclient,requests').
        Returns success/failure. If successful, the user can ask again and you will have the new tool."""
        name = re.sub(r"[^a-zA-Z0-9_]", "", capability_name)
        if not name:
            return "Invalid capability_name: must be alphanumeric/underscore only."

        cap_dir = Path(__file__).resolve().parent
        target = cap_dir / f"{name}.py"
        if target.exists():
            return f"Capability {name} already exists. Try a different name or use the existing one."

        try:
            target.write_text(code.strip(), encoding="utf-8")
        except Exception as e:
            return f"Failed to write file: {e}"

        if pip_deps:
            deps = [d.strip() for d in pip_deps.split(",") if d.strip()]
            if deps:
                try:
                    subprocess.run(
                        ["pip", "install", "-q"] + deps,
                        capture_output=True,
                        timeout=120,
                        check=False,
                    )
                except Exception as e:
                    return f"File written but pip install failed: {e}"

        try:
            mod = importlib.import_module(f"app.capabilities.{name}")
            if not hasattr(mod, "register_capability"):
                # Module loaded; register_capability is called at import
                pass
        except Exception as e:
            target.unlink(missing_ok=True)
            return f"Capability file invalid (syntax/runtime error): {e}"

        return (
            f"Capability '{name}' added successfully. "
            "The new tools are now available. Ask the user to repeat their request."
        )

    return [add_capability]


register_capability("code_evolution", _get_tools, enable_env_var="ENABLE_CODE_EVOLUTION")
