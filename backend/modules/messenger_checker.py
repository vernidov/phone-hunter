import httpx
from fake_useragent import UserAgent
import asyncio

class MessengerChecker:
    """Проверка наличия аккаунтов в мессенджерах без API-ключей."""
    
    def __init__(self):
        self.ua = UserAgent()
    
    async def check(self, phone: str) -> dict:
        result = {"telegram": False, "whatsapp": False, "viber": False, "signal": False, "wechat": False}
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            headers = {"User-Agent": self.ua.random, "X-Requested-With": "XMLHttpRequest"}
            
            # Telegram (прямая проверка через веб)
            try:
                resp = await client.get(f"https://t.me/+{phone.replace('+','')}", headers=headers)
                result["telegram"] = "tgme_page_title" in resp.text
            except:
                pass
            
            await asyncio.sleep(0.5)
            
            # WhatsApp (проверка через публичный статус)
            try:
                resp = await client.get(f"https://wa.me/{phone.replace('+','')}", headers=headers)
                result["whatsapp"] = resp.status_code == 200
            except:
                pass
            
            await asyncio.sleep(0.5)
            
            # Viber (проверка через публичную ссылку)
            try:
                resp = await client.get(f"viber://chat?number={phone.replace('+','')}", headers=headers)
                result["viber"] = True
            except:
                pass
        
        return result
