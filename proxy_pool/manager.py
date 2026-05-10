import random
import httpx

class ProxyManager:
    def __init__(self):
        self.free_proxy_sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        ]
        self.proxies = []
        self._load_proxies()
    
    def _load_proxies(self):
        # Предзагруженные прокси для начала работы
        self.proxies = [
            "http://51.89.14.70:80",
            "http://45.79.216.187:8080",
            "http://165.227.71.60:80",
            "http://143.110.189.150:8080",
        ]
    
    async def fetch_fresh_proxies(self):
        async with httpx.AsyncClient(timeout=5) as client:
            for url in self.free_proxy_sources:
                try:
                    resp = await client.get(url)
                    new_proxies = [line.strip() for line in resp.text.splitlines() if line.strip()]
                    self.proxies.extend([f"http://{p}" for p in new_proxies])
                except:
                    pass
        self.proxies = list(set(self.proxies))
    
    def get_random(self) -> str:
        return random.choice(self.proxies) if self.proxies else None
