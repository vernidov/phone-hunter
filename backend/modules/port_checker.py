import re

class PortChecker:
    """Проверка переноса номера (MNP — Mobile Number Portability)."""
    
    def check(self, phone: str, hlr_raw: str = "", current_operator: str = "", 
              expected_operator: str = "") -> dict:
        result = {
            "ported": False,
            "former_operator": "",
            "current_operator": current_operator,
            "port_date": "",
            "is_old_number": False
        }
        
        # Если есть сырой HLR — ищем признаки переноса
        if hlr_raw:
            # Признак: номер в диапазоне одного оператора, но обслуживается другим
            if "'mobile': True" in hlr_raw and current_operator:
                # Ищем упоминание исходного оператора
                orig_match = re.search(r"'oper':\s*'([^']+)'", hlr_raw)
                brand_match = re.search(r"'oper_brand':\s*'([^']+)'", hlr_raw)
                
                original = orig_match.group(1) if orig_match else ""
                brand = brand_match.group(1) if brand_match else ""
                
                if brand and current_operator and brand.lower() != current_operator.lower():
                    result["ported"] = True
                    result["former_operator"] = brand
                    result["is_old_number"] = True
        
        # Если оператор не совпадает с ожидаемым по DEF-коду — перенос
        if expected_operator and current_operator:
            if expected_operator.lower() != current_operator.lower():
                result["ported"] = True
                result["former_operator"] = expected_operator
                result["is_old_number"] = True
        
        # Если номер в диапазоне другого оператора
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) >= 10 and not result["ported"]:
            def_code = digits[-10:-7] if digits[0] in "78" else ""
            def_operators = {
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
            expected = def_operators.get(def_code, "")
            if expected and current_operator and expected.lower() != current_operator.lower():
                result["ported"] = True
                result["former_operator"] = expected
                result["is_old_number"] = True
        
        return result