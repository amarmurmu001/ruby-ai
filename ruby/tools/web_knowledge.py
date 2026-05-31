import logging
import re
from urllib.parse import quote_plus

logger = logging.getLogger("ruby.tools.web")

class WebKnowledge:
    def search(self, query: str, max_results: int = 3) -> list[dict]:
        results = []
        try:
            results.extend(self._search_duckduckgo(query, max_results))
        except Exception as e:
            logger.warning("DuckDuckGo search failed: %s", e)

        if not results:
            try:
                results.extend(self._search_wikipedia(query, max_results))
            except Exception as e:
                logger.warning("Wikipedia search failed: %s", e)

        return results

    def _search_duckduckgo(self, query: str, max_results: int) -> list[dict]:
        import requests
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            timeout=10,
            headers={"User-Agent": "RubyAI/1.0"}
        )
        data = resp.json()
        results = []

        abstract = data.get("AbstractText", "")
        if abstract and len(abstract) > 50:
            source = data.get("AbstractSource", "DuckDuckGo")
            url = data.get("AbstractURL", "")
            results.append({
                "title": data.get("Heading", "Result"),
                "snippet": abstract[:1000],
                "source": source,
                "url": url
            })

        for topic in data.get("RelatedTopics", [])[:max_results]:
            if "Text" in topic:
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "snippet": topic.get("Text", "")[:500],
                    "source": "DuckDuckGo",
                    "url": topic.get("FirstURL", "")
                })
            if "Topics" in topic:
                for st in topic["Topics"][:2]:
                    if "Text" in st:
                        results.append({
                            "title": st.get("Text", "")[:80],
                            "snippet": st.get("Text", "")[:500],
                            "source": "DuckDuckGo",
                            "url": st.get("FirstURL", "")
                        })

        return results[:max_results]

    def _search_wikipedia(self, query: str, max_results: int) -> list[dict]:
        import requests
        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results
            },
            timeout=10,
            headers={"User-Agent": "RubyAI/1.0"}
        )
        search_data = search_resp.json()
        results = []

        for item in search_data.get("query", {}).get("search", []):
            title = item.get("title", "")
            page_resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "format": "json",
                    "exchars": 800
                },
                timeout=10,
                headers={"User-Agent": "RubyAI/1.0"}
            )
            page_data = page_resp.json()
            pages = page_data.get("query", {}).get("pages", {})
            extract = ""
            for pid, pdata in pages.items():
                if pid != "-1":
                    extract = pdata.get("extract", "")
                    break

            results.append({
                "title": title,
                "snippet": extract[:800] if extract else (item.get("snippet", "")[:300]),
                "source": "Wikipedia",
                "url": f"https://en.wikipedia.org/wiki/{quote_plus(title)}"
            })

        return results[:max_results]

    def fetch_url(self, url: str) -> str | None:
        try:
            import requests
            from bs4 import BeautifulSoup
            resp = requests.get(url, timeout=15,
                headers={"User-Agent": "RubyAI/1.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r'\s+', ' ', text)[:3000]
            return text
        except Exception as e:
            logger.warning("Fetch failed for %s: %s", url, e)
            return None
