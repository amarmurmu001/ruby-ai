import logging
import json
from .base import Tool
from config.settings import settings

logger = logging.getLogger("ruby.tools.web")

class WebSearch(Tool):
    name = "web_search"
    description = "Search the web for current information. Uses Wikipedia as primary source."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"]
    }

    def execute(self, query: str) -> str:
        try:
            import requests
            from urllib.parse import quote

            results = []

            try:
                resp = requests.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": query,
                        "format": "json",
                        "srlimit": 3
                    },
                    timeout=15,
                    headers={"User-Agent": "RubyAI/1.0"}
                )
                data = resp.json()
                for item in data.get("query", {}).get("search", []):
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    import re
                    clean = re.sub(r"<[^>]+>", "", snippet).strip()
                    results.append(f"[Wikipedia] {title}: {clean[:500]}")
            except Exception as e:
                results.append(f"(Wikipedia search error: {e})")

            if not results:
                try:
                    resp = requests.get(
                        "https://api.duckduckgo.com/",
                        params={"q": query, "format": "json", "no_html": "1"},
                        timeout=15
                    )
                    data = resp.json()
                    abstract = data.get("AbstractText", "")
                    if abstract:
                        results.append(f"Summary: {abstract[:500]}")
                    for topic in data.get("RelatedTopics", [])[:3]:
                        if "Text" in topic:
                            results.append(topic["Text"][:300])
                except Exception:
                    pass

            return "\n\n".join(results) if results else "No results found"
        except ImportError:
            return "Requests library not available"
        except Exception as e:
            return f"Search error: {e}"

class FetchURL(Tool):
    name = "fetch_url"
    description = "Fetch content from a URL"
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
                "User-Agent": "RubyAI/1.0"
            })
            resp.raise_for_status()
            content = resp.text
            import re
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content).strip()
            return content[:5000]
        except ImportError:
            return "Requests library not available"
        except Exception as e:
            return f"Fetch error: {e}"
