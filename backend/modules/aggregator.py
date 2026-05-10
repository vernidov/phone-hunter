import asyncio
from datetime import datetime
from modules.validator import PhoneValidator
from modules.hlr_lookup import HLRLookup
from modules.social_searcher import SocialSearcher
from modules.messenger_checker import MessengerChecker
from modules.leak_checker import LeakChecker
from modules.geo_analyzer import GeoAnalyzer
from modules.darknet_scanner import DarknetScanner
from modules.fraud_checker import FraudChecker
from modules.line_type_checker import LineTypeChecker
from modules.port_checker import PortChecker

class Aggregator:
    def __init__(self):
        self.validator = PhoneValidator()
        self.hlr = HLRLookup()
        self.social = SocialSearcher()
        self.messenger = MessengerChecker()
        self.leak = LeakChecker()
        self.geo = GeoAnalyzer()
        self.darknet = DarknetScanner()
        self.fraud = FraudChecker()
        self.line_type = LineTypeChecker()
        self.port = PortChecker()
    
    async def full_search(self, phone: str) -> dict:
        validation = self.validator.analyze(phone)
        hlr_result = await self.hlr.lookup(phone)
        
        geo = self.geo.analyze(
            phone,
            hlr_region=hlr_result.get("region", ""),
            hlr_city=hlr_result.get("city", "")
        )
        
        current_operator = validation.get("operator") or hlr_result.get("provider", "")
        expected_operator = self._expected_operator(phone)
        
        port_result = self.port.check(
            phone,
            hlr_raw=hlr_result.get("raw", ""),
            current_operator=current_operator,
            expected_operator=expected_operator
        )
        
        line_result = self.line_type.check(phone, hlr_provider=current_operator)
        
        tasks = [
            self.social.search(phone),
            self.messenger.check(phone),
            self.leak.check(phone),
            self.darknet.search(phone),
            self.fraud.check(phone),
        ]
        
        social_r, messenger_r, leak_r, darknet_r, fraud_r = await asyncio.gather(*tasks)
        
        return {
            "query": {
                "phone": phone,
                "normalized": validation.get("normalized", ""),
                "timestamp": datetime.now().isoformat()
            },
            "validation": validation,
            "geo": geo,
            "hlr": hlr_result,
            "social": social_r,
            "messengers": messenger_r,
            "leaks": leak_r,
            "darknet": darknet_r,
            "fraud": fraud_r,
            "line_type": line_result,
            "port": port_result,
            "risk_score": self._calculate_risk(leak_r, social_r, fraud_r)
        }
    
    def _expected_operator(self, phone: str) -> str:
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) < 10: return ""
        def_code = digits[-10:-7]
        mapping = {
            "900":"Tele2","901":"Tele2","902":"Tele2","903":"Beeline",
            "904":"Tele2","905":"Beeline","906":"Beeline","908":"Tele2",
            "909":"Beeline","910":"MTS","911":"MTS","912":"MTS","913":"MTS",
            "914":"MTS","915":"MTS","916":"MTS","917":"MTS","918":"MTS",
            "919":"MTS","920":"MegaFon","921":"MegaFon","922":"MegaFon",
            "923":"MegaFon","924":"MegaFon","925":"MegaFon","926":"MegaFon",
            "927":"MegaFon","928":"MegaFon","929":"MegaFon",
            "950":"Tele2","951":"Tele2","952":"Tele2","953":"Tele2",
            "960":"Beeline","961":"Beeline","962":"Beeline","963":"Beeline",
            "964":"Beeline","965":"Beeline","966":"Beeline","967":"Beeline",
            "968":"Beeline","980":"MTS","981":"MTS","982":"MTS","983":"MTS",
            "984":"MTS","985":"MTS","986":"MTS","987":"MTS","988":"MTS",
            "989":"MTS"
        }
        return mapping.get(def_code, "")
    
    def _calculate_risk(self, leak: dict, social: dict, fraud: dict) -> int:
        score = 0
        if leak.get("found_in_leaks"): score += 30
        if social.get("vk"): score += 10
        if social.get("telegram"): score += 10
        if fraud.get("has_complaints"): score += 30
        if fraud.get("complaint_count", 0) > 5: score += 15
        return min(score, 100)