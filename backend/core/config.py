import os

class Settings:
    PROJECT_NAME = "OSINT Phone Hunter Pro"
    VERSION = "2.0.0"
    DEBUG = True
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    CARRIERS_DB = os.path.join(DATA_DIR, "carriers", "full_mcc_mnc.db")
    COUNTRY_CODES = os.path.join(DATA_DIR, "prefixes", "country_codes.json")
    IMSI_RANGES = os.path.join(DATA_DIR, "fingerprint", "imsi_ranges.json")
    SEARCH_SOURCES = ["carriers_db","hlr_lookup","social_networks","messengers","leak_databases","darknet_forums","geo_analysis"]
    RATE_LIMIT_REQUESTS = 30
    RATE_LIMIT_PERIOD = 60
    USE_PROXY = True
    PROXY_POOL_SIZE = 100
    TIMEOUT = 15
    RETRY_COUNT = 2

settings = Settings()
