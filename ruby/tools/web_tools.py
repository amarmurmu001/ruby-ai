import logging
import re
from .base import Tool

logger = logging.getLogger("ruby.tools.web")


class WebSearch(Tool):
    name = "web_search"
    description = "Search the web for current information"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"]
    }

    def execute(self, query: str) -> str:
        results = self._search_ddg(query)
        if results:
            return results

        results = self._search_google_api(query)
        if results:
            return results

        return "Search engines unavailable. Try again later."

    def _search_ddg(self, query: str) -> str | None:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=5))
            if not raw:
                return None
            lines = []
            for r in raw:
                title = r.get("title", "").strip()
                body = r.get("body", "").strip()[:200]
                href = r.get("href", "")
                lines.append(f"[{title[:80]}]\n    {body}\n    {href}")
            return "\n\n".join(lines) if lines else None
        except ImportError:
            return None
        except Exception as e:
            logger.warning("DDG search error: %s", e)
            return None

    def _search_google_api(self, query: str) -> str | None:
        try:
            from config.settings import settings
            api_key = settings.GOOGLE_API_KEY
            cx = settings.GOOGLE_CSE_ID
            if not api_key or not cx:
                return None
            import requests
            url = "https://www.googleapis.com/customsearch/v1"
            params = {"key": api_key, "cx": cx, "q": query, "num": 5}
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            items = data.get("items", [])
            if not items:
                return None
            lines = []
            for item in items:
                title = item.get("title", "").strip()
                snippet = item.get("snippet", "").strip()[:200]
                link = item.get("link", "")
                lines.append(f"[{title[:80]}]\n    {snippet}\n    {link}")
            return "\n\n".join(lines) if lines else None
        except ImportError:
            return None
        except Exception as e:
            logger.warning("Google API search error: %s", e)
            return None


class FetchURL(Tool):
    name = "fetch_url"
    description = "Fetch and extract text content from a URL"
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"}
        },
        "required": ["url"]
    }

    def execute(self, url: str) -> str:
        try:
            import requests
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RubyAI/1.0"
            })
            resp.raise_for_status()
            content = resp.text
            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content).strip()
            return content[:5000]
        except ImportError:
            return "Requests library not available"
        except Exception as e:
            return f"Fetch error: {e}"
