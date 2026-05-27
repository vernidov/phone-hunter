import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import json
import os
from core.config import settings

class PhoneValidator:
    def __init__(self):
        with open(settings.COUNTRY_CODES, "r", encoding="utf-8") as f:
            self.countries = json.load(f)
    
    def analyze(self, phone: str) -> dict:
        result = {
            "valid": False, "raw": phone, "normalized": "",
            "country": "", "region": "", "operator": "",
            "timezone": [], "type": "", "auto_detected": False
        }
        
        # Автоопределение: если номер без "+" — пробуем угадать страну
        cleaned = ''.join(filter(str.isdigit, phone))
        
        if not phone.startswith("+"):
            # Если 11 цифр и начинается с 7 или 8 — Россия
            if len(cleaned) == 11 and (cleaned.startswith("7") or cleaned.startswith("8")):
                phone = "+7" + cleaned[-10:]
                result["auto_detected"] = True
            # Если 10 цифр — добавляем +7
            elif len(cleaned) == 10 and cleaned.startswith("9"):
                phone = "+7" + cleaned
                result["auto_detected"] = True
            # Если 12 цифр и начинается с 3 — Украина
            elif len(cleaned) == 12 and cleaned.startswith("380"):
                phone = "+" + cleaned
                result["auto_detected"] = True
            # Если 12 цифр и начинается с 375 — Беларусь
            elif len(cleaned) == 12 and cleaned.startswith("375"):
                phone = "+" + cleaned
                result["auto_detected"] = True
            else:
                phone = "+" + cleaned
        
        try:
            parsed = phonenumbers.parse(phone, None)
            result["valid"] = phonenumbers.is_valid_number(parsed)
            result["normalized"] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            result["country"] = geocoder.country_name_for_number(parsed, "en") or self._match_country(phone)
            result["region"] = geocoder.description_for_number(parsed, "ru") or ""
            result["operator"] = carrier.name_for_number(parsed, "ru") or self._local_operator_lookup(phone)
            result["timezone"] = list(timezone.time_zones_for_number(parsed)) if phonenumbers.is_valid_number(parsed) else []
            result["type"] = self._get_number_type(parsed)
        except:
            result["normalized"] = phone
            result["country"] = self._match_country(phone)
        
        return result
    
    def _match_country(self, phone: str) -> str:
        digits = ''.join(filter(str.isdigit, phone))
        for code, info in sorted(self.countries.items(), key=lambda x: len(x[0]), reverse=True):
            if digits.startswith(code):
                return info.get("name", "")
        return "Unknown"
    
    def _local_operator_lookup(self, phone: str) -> str:
        digits = ''.join(filter(str.isdigit, phone))
        prefixes = {
            "900":"Tele2","901":"Skylink","902":"Tele2","903":"Beeline","904":"Tele2",
            "905":"Beeline","906":"Beeline","908":"Tele2","909":"Beeline",
            "910":"MTS","911":"MTS","912":"MTS","913":"MTS","914":"MTS","915":"MTS",
            "916":"MTS","917":"MTS","918":"MTS","919":"MTS",
            "920":"Megafon","921":"Megafon","922":"Megafon","923":"Megafon",
            "924":"Megafon","925":"Megafon","926":"Megafon","927":"Megafon",
            "928":"Megafon","929":"Megafon",
            "950":"Tele2","951":"Tele2","952":"Tele2","953":"Tele2",
            "960":"Beeline","961":"Beeline","962":"Beeline","963":"Beeline",
            "964":"Beeline","965":"Beeline","966":"Beeline","967":"Beeline","968":"Beeline",
            "980":"MTS","981":"MTS","982":"MTS","983":"MTS","984":"MTS",
            "985":"MTS","986":"MTS","987":"MTS","988":"MTS","989":"MTS"
        }
        prefix = digits[1:4] if len(digits) >= 4 and digits[0] in "78" else digits[2:5] if len(digits) >= 5 else ""
        return prefixes.get(prefix, "Unknown")
    
    def _get_number_type(self, parsed) -> str:
        types = {0:"FIXED_LINE",1:"MOBILE",2:"FIXED_OR_MOBILE",3:"TOLL_FREE",
                 4:"PREMIUM_RATE",5:"SHARED_COST",6:"VOIP",7:"PERSONAL_NUMBER",
                 8:"PAGER",9:"UAN",10:"VOICEMAIL"}
        return types.get(phonenumbers.number_type(parsed), "UNKNOWN")
