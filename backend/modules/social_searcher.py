import httpx
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import asyncio

class SocialSearcher:
    """Поиск номера по соцсетям через открытый веб-поиск и Google Dorking."""
    
    def __init__(self):
        self.ua = UserAgent()
        self.search_engines = ["https://www.google.com/search?q=", "https://search.yahoo.com/search?p=", "https://www.bing.com/search?q="]
    
    async def search(self, phone: str) -> dict:
        result = {"vk": None, "telegram": None, "whatsapp": None, "viber": None, "instagram": None, "facebook": None, "ok": None, "other_mentions": []}
        
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            headers = {"User-Agent": self.ua.random}
            queries = [
                f'"{phone}" site:vk.com',
                f'"{phone}" site:ok.ru',
                f'"{phone}" site:telegram.org',
                f'"{phone}" site:instagram.com',
            ]
            
            for query in queries:
                try:
                    resp = await client.get(f"https://www.google.com/search?q={query}&hl=ru", headers=headers)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        links = [a.get("href") for a in soup.find_all("a") if a.get("href") and "http" in a.get("href")]
                        for link in links[:5]:
                            if "vk.com" in link: result["vk"] = link
                            if "ok.ru" in link: result["ok"] = link
                            if "t.me" in link or "telegram" in link: result["telegram"] = link
                            if "instagram.com" in link: result["instagram"] = link
                            result["other_mentions"].append(link)
                    await asyncio.sleep(1)
                except:
                    pass
        return result
