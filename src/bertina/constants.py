SEARCH_BASE = "https://search.bertina.ir"
TRANSLATE_BASE = "https://translate.bertina.ir"
WEATHER_BASE = "https://weather.bertina.ir"
LLM_BASE = "https://llm.bertina.ir"
ADS_BASE = "https://ads.bertina.ir"
MAIL_BASE = "https://www.bertinamail.com"
DNS_IP = "193.186.32.32"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

RETRY_STATUS_CODES = {429, 502, 503, 504}
