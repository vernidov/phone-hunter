import httpx
from fake_useragent import UserAgent
import re
import asyncio

class FraudChecker:
    """Проверка номера по жалобам + имена через API сайтов."""
    
    def __init__(self):
        self.ua = UserAgent()
    
    async def check(self, phone: str) -> dict:
        result = {
            "has_complaints": False,
            "tags": [],
            "names": [],
            "sources": [],
            "complaint_count": 0
        }
        clean = phone.replace("+", "").replace("-", "").replace(" ", "")
        
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9"
            }
            
            # 1. callinsider.ru — прямой запрос к странице номера (без JS)
            try:
                resp = await client.get(
                    f"https://www.callinsider.ru/number/{clean}.html",
                    headers=headers
                )
                if resp.status_code == 200:
                    text = resp.text
                    
                    # Ищем данные в data-атрибутах или скрытых полях
                    name_matches = re.findall(
                        r'(?:data-name|data-title|itemprop="name")[^>]*>([^<]+)<',
                        text, re.IGNORECASE
                    )
                    if name_matches:
                        result["names"].extend([n.strip() for n in name_matches if len(n.strip()) > 2])
                        result["sources"].append("callinsider.ru")
                    
                    # Ищем через JSON-LD или микроразметку
                    jsonld = re.findall(r'<script type="application/ld\+json">([^<]+)</script>', text)
                    for ld in jsonld:
                        import json
                        try:
                            data = json.loads(ld)
                            if isinstance(data, dict):
                                if "name" in data:
                                    result["names"].append(str(data["name"]))
                                if "description" in data:
                                    desc = str(data["description"])
                                    if "мошенник" in desc.lower():
                                        result["tags"].append("мошенник")
                                        result["has_complaints"] = True
                        except:
                            pass
                    
                    # Категории
                    if "мошенник" in text.lower():
                        result["tags"].append("мошенник")
                        result["has_complaints"] = True
                    if "спам" in text.lower():
                        result["tags"].append("спам")
                        result["has_complaints"] = True
                    if "коллектор" in text.lower():
                        result["tags"].append("коллектор")
                        result["has_complaints"] = True
                    
                    count_match = re.search(r'(\d+)\s*(?:жалоб|отзыв)', text, re.IGNORECASE)
                    if count_match:
                        result["complaint_count"] += int(count_match.group(1))
                        
            except:
                pass
            
            await asyncio.sleep(0.5)
            
            # 2. kto-zvonil.ru — через текстовую версию (без JS)
            try:
                resp = await client.get(
                    f"https://кто-звонит.рф/number/{clean}",
                    headers={**headers, "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"}
                )
                if resp.status_code == 200:
                    text = resp.text
                    
                    # Имена из текста (Googlebot видит без JS)
                    # Паттерн: "Иван", "Иван Иванов", "Иван И."
                    name_patterns = [
                        r'<h[1-4][^>]*>([А-Я][а-яё]+(?:\s[А-Я][а-яё]+)?)</h[1-4]>',
                        r'<strong>([А-Я][а-яё]+(?:\s[А-Я]\.?)?)</strong>',
                        r'"name":\s*"([А-Я][а-яё]+(?:\s[А-Я][а-яё]+)?)"',
                        r'"author":\s*"([А-Я][а-яё]+(?:\s[А-Я][а-яё]+)?)"',
                    ]
                    for pat in name_patterns:
                        names = re.findall(pat, text)
                        if names:
                            result["names"].extend([n.strip() for n in names if len(n.strip()) > 2 and not n.startswith('+')])
                    
                    if "кто-звонит.рф" not in result["sources"]:
                        result["sources"].append("kto-zvonil.ru")
                        
            except:
                pass
            
            await asyncio.sleep(0.3)
            
            # 3. zvonili.com — прямой запрос
            try:
                resp = await client.get(
                    f"https://zvonili.com/phone/{clean}/",
                    headers=headers
                )
                if resp.status_code == 200:
                    text = resp.text
                    
                    # Имена из заголовков
                    name_matches = re.findall(
                        r'<h[1-3][^>]*>([А-Я][а-яё]+(?:\s[А-Я][а-яё]+)?)</h[1-3]>',
                        text
                    )
                    if name_matches:
                        result["names"].extend([n.strip() for n in name_matches if len(n.strip()) > 2])
                    
                    if "zvonili.com" not in result["sources"]:
                        result["sources"].append("zvonili.com")
                        
            except:
                pass
            
            # Чистим
            result["tags"] = list(set(result["tags"]))
            result["names"] = list(set([n for n in result["names"] if len(n) > 2 and not n.startswith('+') and not n.startswith('7') and not n.startswith('8')]))[:10]
            result["sources"] = list(set(result["sources"]))
            
            if result["tags"] or result["names"] or result["complaint_count"] > 0:
                result["has_complaints"] = True
        
        return result