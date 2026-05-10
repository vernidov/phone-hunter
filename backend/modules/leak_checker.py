import httpx
import hashlib
from fake_useragent import UserAgent

class LeakChecker:
    """Поиск номера в утечках через публичные базы (haveibeenpwned API style, snusbase scrapers)."""
    
    def __init__(self):
        self.ua = UserAgent()
        self.leak_sources = [
            "https://leakcheck.io/api/public?key=free&check=",
            "https://leakosintapi.com/?token=free&q=",
            "https://psbdmp.ws/api/v3/search/",
        ]
    
    async def check(self, phone: str) -> dict:
        result = {"found_in_leaks": False, "leaks": [], "passwords": [], "names": [], "emails": []}
        clean = ''.join(filter(str.isdigit, phone))
        sha1_hash = hashlib.sha1(clean.encode()).hexdigest().upper()
        
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"User-Agent": self.ua.random}
            
            # Проверка через haveibeenpwned API (k-anonymity, бесплатно)
            try:
                prefix = sha1_hash[:5]
                resp = await client.get(f"https://api.pwnedpasswords.com/range/{prefix}", headers=headers)
                if resp.status_code == 200:
                    hashes = [line.split(":")[0] for line in resp.text.splitlines()]
                    if sha1_hash[5:] in hashes:
                        result["found_in_leaks"] = True
                        result["leaks"].append("HaveIBeenPwned (password leak)")
            except:
                pass
            
            # LeakCheck (публичный доступ)
            try:
                resp = await client.get(f"https://leakcheck.io/api/public?key=free&check={clean}", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("found"):
                        result["found_in_leaks"] = True
                        result["leaks"].extend(data.get("sources", []))
                        result["passwords"].extend(data.get("passwords", []))
                        result["names"].extend(data.get("names", []))
                        result["emails"].extend(data.get("emails", []))
            except:
                pass
        
        return result
