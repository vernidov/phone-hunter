import httpx
from fake_useragent import UserAgent
import json
import re
import os
from core.config import settings

class HLRLookup:
    """HLR-запросы + IMSI-анализ."""
    
    def __init__(self):
        self.ua = UserAgent()
        # Грузим IMSI-базу
        self.imsi_ranges = {}
        if os.path.exists(settings.IMSI_RANGES):
            with open(settings.IMSI_RANGES, "r", encoding="utf-8") as f:
                self.imsi_ranges = json.load(f)
    
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
                resp = await client.get(f"https://htmlweb.ru/geo/api.php?json&telcod={clean}", headers=headers)
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
                            result["mnc"] = str(data["0"].get("mnc", ""))
                            
                            # IMSI-анализ
                            mcc = result["mcc"]
                            mnc = result["mnc"]
                            imsi_key = f"{mcc}{mnc}"
                            if imsi_key in self.imsi_ranges:
                                result["imsi_info"] = self.imsi_ranges[imsi_key]
                            elif mcc == "250":
                                # Российские операторы по MNC
                                ru_operators = {
                                    "01": "MTS", "02": "MegaFon", "03": "NCC", "04": "Sibchallenge",
                                    "05": "ETK", "06": "Skylink", "07": "SMARTS", "09": "Skylink",
                                    "10": "DTC", "11": "Yota", "12": "Baykalwestcom", "13": "Kuban-GSM",
                                    "14": "MegaFon", "15": "SMARTS", "16": "MTS", "17": "Utel",
                                    "20": "Tele2", "23": "MTS", "28": "Beeline", "35": "MOTIV",
                                    "38": "Tambov-GSM", "39": "Rostelecom", "44": "Stavtelesot",
                                    "50": "Beeline", "51": "Beeline", "52": "Beeline", "53": "Beeline",
                                    "99": "Beeline"
                                }
                                result["imsi_info"] = ru_operators.get(mnc, f"Россия MCC=250 MNC={mnc}")
                        
                        if "tz" in data:
                            result["timezone"] = data["tz"]
                        elif "0" in data and "tz" in data["0"]:
                            result["timezone"] = data["0"]["tz"]
                        
                        if "limit" in data:
                            result["roaming"] = data["limit"] > 1
                            
                    except json.JSONDecodeError:
                        # Text fallback
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
                        
                        mcc_match = re.search(r"'mcc':\s*(\d+)", raw_text)
                        if mcc_match:
                            result["mcc"] = mcc_match.group(1)
                
            except Exception as e:
                result["raw"] = f"Error: {str(e)}"
        
        return result