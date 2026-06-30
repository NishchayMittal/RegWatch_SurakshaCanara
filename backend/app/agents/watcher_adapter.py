from app.agents.base import BaseWatcherAgent
from app.agents.watcher_real import WatcherAgent as RealWatcherAgent
from bs4 import BeautifulSoup
import requests

class WatcherAgentAdapter(BaseWatcherAgent):
    def __init__(self):
        self.agent = RealWatcherAgent()

    def fetch(self, url: str) -> dict:
        regulator = self._guess_regulator(url)
        doc = self.agent.fetch_single(url, regulator)

        if doc is None:
            return {"url": url, "title": "Unknown", "source": regulator, "text": ""}

        # A's fetch_single() hardcodes title="Manual fetch" — fix it here
        # by extracting the real page <title> tag instead.
        real_title = self._extract_real_title(url) or doc.title

        return {
            "url": doc.url,
            "title": real_title,
            "source": doc.regulator,
            "text": doc.raw_text,
        }

    def _extract_real_title(self, url: str) -> str:
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "RegWatch/1.0"})
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try h1/h2 first — usually the actual circular name on RBI pages
            for tag in ["h1", "h2"]:
                heading = soup.find(tag)
                if heading and heading.get_text(strip=True):
                    text = heading.get_text(strip=True)
                    if len(text) > 15:  # skip trivial/empty headings
                        return text

            # Fallback to <title> tag if no good heading found
            if soup.title and soup.title.string:
                return soup.title.string.strip()
        except Exception:
            pass
        return None

    def _guess_regulator(self, url: str) -> str:
        if "rbi.org.in" in url:
            return "RBI"
        elif "sebi.gov.in" in url:
            return "SEBI"
        elif "mca.gov.in" in url:
            return "MCA"
        return "UNKNOWN"