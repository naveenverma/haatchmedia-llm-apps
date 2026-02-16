"""Web search capability - enabled via ENABLE_WEB_SEARCH=1."""

from __future__ import annotations

from langchain_core.tools import tool

from app.capabilities import register_capability


def _get_tools(**kwargs):
    try:
        from ddgs import DDGS
    except ImportError:
        raise ImportError(
            "ddgs is required for web search. Install with: pip install ddgs"
        )

    @tool
    def web_search(query: str, max_results: int = 8) -> str:
        """Search the web for current information. Use for: lists, news, facts, companies, 
        how-to guides, or anything not in your memory. Formulate a clear, specific search query 
        (e.g. 'list of pharmaceutical companies in Australia' not 'pharma companies')."""
        try:
            results = DDGS().text(query, max_results=max_results)
            if not results:
                return "No results found. Try a different or more specific search query."
            lines = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                body = r.get("body", "")
                url = r.get("href", r.get("url", ""))
                lines.append(f"{i}. {title}\n   {body}\n   {url}")
            return "\n\n".join(lines)
        except Exception as e:
            return f"Search failed: {e}"

    return [web_search]


register_capability("web_search", _get_tools, enable_env_var="ENABLE_WEB_SEARCH")
