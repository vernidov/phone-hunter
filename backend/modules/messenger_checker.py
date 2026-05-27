import httpx
from fake_useragent import UserAgent
import asyncio
import re

class MessengerChecker:
    """Проверка мессенджеров через прямые запросы."""
    
    def __init__(self):
        self.ua = UserAgent()
    
    async def check(self, phone: str) -> dict:
        result = {"telegram": False, "whatsapp": False, "viber": False, "signal": False, "wechat": False}
        clean = phone.replace("+", "").replace("-", "").replace(" ", "")
        
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            
            # Telegram
            try:
                resp = await client.get(f"https://t.me/+{clean}", headers=headers, )
                result["telegram"] = "tgme_page_title" in resp.text or "tgme_action_button" in resp.text
            except:
                pass
            
            await asyncio.sleep(0.3)
            
            # WhatsApp
            try:
                resp = await client.get(f"https://wa.me/{clean}", headers=headers, )
                result["whatsapp"] = "WhatsApp" in resp.text or resp.status_code == 200
            except:
                pass
            
            await asyncio.sleep(0.3)
            
            # Viber
            try:
                resp = await client.get(f"https://invite.viber.com/?g2=AQB{clean}", headers=headers, )
                result["viber"] = resp.status_code == 200 and len(resp.text) > 500
            except:
                pass
            
            await asyncio.sleep(0.3)
            
            # Signal
            try:
                resp = await client.get(f"https://signal.me/#p/+{clean}", headers=headers, )
                result["signal"] = "signal" in resp.text.lower()
            except:
                pass
        
        return result
