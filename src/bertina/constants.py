SEARCH_BASE = "https://search.bertina.ir"
TRANSLATE_BASE = "https://translate.bertina.ir"
WEATHER_BASE = "https://weather.bertina.ir"
LLM_BASE = "https://llm.bertina.ir"
ADS_BASE = "https://ads.bertina.ir"
MAIL_BASE = "https://www.bertinamail.com"
DNS_IP = "193.186.32.32"

DEFAULT_HEADERS = {
    "Accept-Language": "en,fa;q=0.9",
    "Upgrade-Insecure-Requests": "1",
}

SEARCH_HEADERS = {
    **DEFAULT_HEADERS,
    "Referer": f"{SEARCH_BASE}/",
}

RETRY_STATUS_CODES = {429, 502, 503, 504}
