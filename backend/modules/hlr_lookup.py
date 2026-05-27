import httpx
from fake_useragent import UserAgent
import json
import re

class HLRLookup:
    """HLR-запросы через htmlweb.ru."""
    
    def __init__(self):
        self.ua = UserAgent()
    
    async def lookup(self, phone: str) -> dict:
        result = {
            "provider": "", "country": "", "location": "",
            "region": "", "city": "", "area": "", "timezone": "",
            "network_type": "", "ported": False, "roaming": False,
            "mcc": "", "mnc": "", "imsi_info": "", "raw": ""
        }
        clean = phone.replace("+", "").replace("-", "").replace(" ", "")
        
        async with httpx.AsyncClient(timeout=15) as client:
            headers = {"User-Agent": self.ua.random}
            
            try:
                resp = await client.get(f"https://htmlweb.ru/geo/api.php?json&telcod={clean}", headers=headers, )
                if resp.status_code == 200:
                    raw_text = resp.text
                    result["raw"] = raw_text
                    
                    try:
                        data = json.loads(raw_text)
                        
                        if "country" in data:
                            result["country"] = data["country"].get("name", "")
                            result["mcc"] = str(data["country"].get("mcc", ""))
                        
                        if "region" in data:
                            result["region"] = data["region"].get("name", "")
                            result["area"] = data["region"].get("okrug", "")
                        
                        if "0" in data:
                            result["city"] = data["0"].get("name", "")
                            result["location"] = data["0"].get("name", "")
                            result["provider"] = data["0"].get("oper_brand", data["0"].get("oper", ""))
                            result["network_type"] = "MOBILE" if data["0"].get("mobile") else "FIXED"
                        
                        if "tz" in data:
                            result["timezone"] = data["tz"]
                        
                        if "limit" in data:
                            result["roaming"] = data["limit"] > 1
                            
                    except json.JSONDecodeError:
                        city_match = re.search(r"'0':\s*\{[^}]*'name':\s*'([^']+)'", raw_text)
                        if city_match:
                            result["city"] = city_match.group(1)
                            result["location"] = city_match.group(1)
                        
                        region_match = re.search(r"'region':\s*\{[^}]*'name':\s*'([^']+)'", raw_text)
                        if region_match:
                            result["region"] = region_match.group(1)
                        
                        oper_match = re.search(r"'oper_brand':\s*'([^']+)'", raw_text)
                        if oper_match:
                            result["provider"] = oper_match.group(1)
                        
            except Exception as e:
                result["raw"] = f"Error: {str(e)}"
        
        return result
