class LineTypeChecker:
    """Определение типа линии: частное лицо или корпоративный."""
    
    # Диапазоны корпоративных номеров (известные пулы юрлиц)
    BUSINESS_RANGES = {
        # Билайн корпоративные
        "960": {"start": "9600000000", "end": "9600999999"},
        "961": {"start": "9610000000", "end": "9611999999"},
        # МТС корпоративные
        "985": {"start": "9850000000", "end": "9852999999"},
        "986": {"start": "9860000000", "end": "9861999999"},
        # Мегафон корпоративные
        "927": {"start": "9270000000", "end": "9270999999"},
        "928": {"start": "9280000000", "end": "9281999999"},
        # Tele2 корпоративные
        "904": {"start": "9040000000", "end": "9040999999"},
    }
    
    # Мнемоника операторов по префиксу
    OPERATOR_PREFIX = {
        "900": "Tele2", "901": "Tele2", "902": "Tele2", "903": "Beeline",
        "904": "Tele2", "905": "Beeline", "906": "Beeline", "908": "Tele2",
        "909": "Beeline", "910": "MTS", "911": "MTS", "912": "MTS", "913": "MTS",
        "914": "MTS", "915": "MTS", "916": "MTS", "917": "MTS", "918": "MTS",
        "919": "MTS", "920": "MegaFon", "921": "MegaFon", "922": "MegaFon",
        "923": "MegaFon", "924": "MegaFon", "925": "MegaFon", "926": "MegaFon",
        "927": "MegaFon", "928": "MegaFon", "929": "MegaFon",
        "950": "Tele2", "951": "Tele2", "952": "Tele2", "953": "Tele2",
        "960": "Beeline", "961": "Beeline", "962": "Beeline", "963": "Beeline",
        "964": "Beeline", "965": "Beeline", "966": "Beeline", "967": "Beeline",
        "968": "Beeline", "980": "MTS", "981": "MTS", "982": "MTS", "983": "MTS",
        "984": "MTS", "985": "MTS", "986": "MTS", "987": "MTS", "988": "MTS",
        "989": "MTS"
    }
    
    def check(self, phone: str, hlr_provider: str = "") -> dict:
        result = {
            "line_type": "unknown",
            "is_business": False,
            "is_mass_activation": False,
            "operator_match": True,
            "confidence": 0
        }
        
        digits = ''.join(filter(str.isdigit, phone))
        
        # Определяем DEF-код
        if len(digits) >= 10:
            def_code = digits[-10:-7] if len(digits) >= 10 else digits[1:4]
            
            # Проверка на корпоративный диапазон
            if def_code in self.BUSINESS_RANGES:
                num_part = int(digits[-10:]) if len(digits) >= 10 else 0
                start = int(self.BUSINESS_RANGES[def_code]["start"][-7:])
                end = int(self.BUSINESS_RANGES[def_code]["end"][-7:])
                if start <= num_part % 10000000 <= end:
                    result["line_type"] = "business"
                    result["is_business"] = True
                    result["confidence"] = 70
                    return result
            
            # Проверка оператора по DEF
            expected_operator = self.OPERATOR_PREFIX.get(def_code, "")
            if hlr_provider and expected_operator:
                if hlr_provider.lower() != expected_operator.lower():
                    result["operator_match"] = False
                    # Возможно перенесённый номер
                    result["line_type"] = "ported_or_virtual"
                    result["confidence"] = 50
            
            # Проверка на массовую активацию (диапазоны одноразок)
            mass_ranges = ["900", "901", "902", "908", "950", "951", "952"]
            if def_code in mass_ranges:
                # Tele2 часто раздаёт эти диапазоны под спам
                result["is_mass_activation"] = True
            
            if not result["line_type"] or result["line_type"] == "unknown":
                result["line_type"] = "personal"
                result["confidence"] = 60
        
        return result