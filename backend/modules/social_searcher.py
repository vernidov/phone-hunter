import httpx
from fake_useragent import UserAgent
import asyncio
import re

class SocialSearcher:
    """Поиск номера по соцсетям через несколько поисковиков."""
    
    def __init__(self):
        self.ua = UserAgent()
    
    async def search(self, phone: str) -> dict:
        result = {"vk": None, "telegram": None, "whatsapp": None, "viber": None, 
                  "instagram": None, "facebook": None, "ok": None, "other_mentions": []}
        
        clean = phone.replace("+", "").replace("-", "").replace(" ", "")
        
        async with httpx.AsyncClient(timeout=15) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "ru-RU,ru;q=0.9",
                "Accept": "text/html,application/xhtml+xml"
            }
            
            # Поиск VK
            try:
                resp = await client.get(f"https://vk.com/search?c%5Bphone%5D={clean}", headers=headers, )
                if resp.status_code == 200:
                    profiles = re.findall(r'href="/(id\d+|[\w.]+)"', resp.text)
                    if profiles:
                        result["vk"] = f"https://vk.com/{profiles[0]}"
                await asyncio.sleep(1)
            except:
                pass
            
            # Поиск OK.ru
            try:
                resp = await client.get(f"https://ok.ru/dk?st.cmd=searchResult&st.query={clean}", headers=headers, )
                if resp.status_code == 200:
                    profiles = re.findall(r'href="(/profile/\d+)"', resp.text)
                    if profiles:
                        result["ok"] = f"https://ok.ru{profiles[0]}"
                await asyncio.sleep(1)
            except:
                pass
            
            # Поиск через Google
            try:
                resp = await client.get(f"https://www.google.com/search?q=%22{clean}%22&hl=ru", headers=headers, )
                if resp.status_code == 200:
                    links = [a for a in re.findall(r'https?://[^\s"<>]+', resp.text) if len(a) > 20][:10]
                    result["other_mentions"] = links
            except:
                pass
        
        return result
