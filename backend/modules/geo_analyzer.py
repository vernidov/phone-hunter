import json
import os
from core.config import settings

class GeoAnalyzer:
    """Геоанализ — теперь подтягивает регион из HLR если есть."""
    
    def __init__(self):
        with open(settings.COUNTRY_CODES, "r", encoding="utf-8") as f:
            self.countries = json.load(f)
    
    def analyze(self, phone: str, hlr_region: str = "", hlr_city: str = "") -> dict:
        digits = ''.join(filter(str.isdigit, phone))
        result = {
            "country_code": "", 
            "country_name": "", 
            "region_code": "", 
            "region_name": "", 
            "city": "",
            "time_zone": "", 
            "lat": 0, 
            "lon": 0
        }
        
        # Страна
        for code, info in sorted(self.countries.items(), key=lambda x: len(x[0]), reverse=True):
            if digits.startswith(code):
                result["country_code"] = code
                result["country_name"] = info.get("name", "")
                break
        
        # Приоритет: HLR данные > DEF-код
        if hlr_region:
            result["region_name"] = hlr_region
        if hlr_city:
            result["city"] = hlr_city
        
        # DEF-код региона (РФ) — только если HLR не дал регион
        if not result["region_name"] and len(digits) >= 10:
            ru_regions = {
                "900":"Москва", "901":"Москва", "902":"Москва",
                "903":"Москва", "904":"Москва", "905":"Москва", "906":"Москва",
                "910":"Центральный ФО", "911":"Северо-Западный ФО", "912":"Уральский ФО",
                "913":"Сибирский ФО", "914":"Дальневосточный ФО", "915":"Центральный ФО",
                "916":"Москва", "917":"Приволжский ФО", "918":"Южный ФО",
                "919":"Центральный ФО", "920":"Центральный ФО", "921":"Северо-Западный ФО",
                "922":"Уральский ФО", "923":"Сибирский ФО", "924":"Дальневосточный ФО",
                "925":"Москва", "926":"Москва", "927":"Приволжский ФО",
                "928":"Южный ФО", "929":"Центральный ФО",
                "950":"Москва", "951":"Москва", "952":"Москва",
                "960":"Северо-Западный ФО", "961":"Центральный ФО", "962":"Центральный ФО",
                "963":"Уральский ФО", "964":"Сибирский ФО", "965":"Дальневосточный ФО",
                "966":"Центральный ФО", "967":"Приволжский ФО", "968":"Южный ФО",
                "980":"Москва", "981":"Северо-Западный ФО", "982":"Уральский ФО",
                "983":"Сибирский ФО", "984":"Дальневосточный ФО", "985":"Москва",
                "986":"Приволжский ФО", "987":"Южный ФО", "988":"Центральный ФО",
                "989":"Центральный ФО",
            }
            def_code = digits[-10:-7] if len(digits) >= 10 else ""
            if def_code in ru_regions:
                result["region_name"] = ru_regions[def_code]
                result["region_code"] = def_code
        
        return result