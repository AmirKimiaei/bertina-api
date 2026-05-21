"""
bertina-py demo — exercises every Phase 1 module against live services.
Run:  python examples/demo.py
"""

from __future__ import annotations

import textwrap

# ── helpers ──────────────────────────────────────────────────────────────────

SECTION = "\n" + "─" * 60 + "\n"


def header(title: str) -> None:
    print(f"{SECTION}  {title}{SECTION}")


def indent(text: str, width: int = 4) -> str:
    return textwrap.indent(str(text), " " * width)


# ── 1. SEARCH ────────────────────────────────────────────────────────────────


def demo_search() -> None:
    from bertina.search import BertinaSearch, SearchType

    header("1 · Web Search  (query: 'هوش مصنوعی')")

    with BertinaSearch() as client:
        resp = client.search("هوش مصنوعی", type=SearchType.WEB)

    print(f"  query       : {resp.query}")
    print(f"  results     : {len(resp.results)}")
    print(f"  related     : {resp.related[:3]}")

    for i, r in enumerate(resp.results[:3], 1):
        print(f"\n  [{i}] {r.title}")
        print(f"      {r.url}")
        if r.description:
            print(indent(textwrap.fill(r.description, 70), 6))


def demo_alive_check() -> None:
    from bertina.search import BertinaSearch, SearchType

    header("2 · Alive Check  (top 5 web results for 'python')")

    with BertinaSearch() as client:
        resp = client.search("python", type=SearchType.WEB)
        resp = client.check_alive(resp)

    for r in resp.results[:5]:
        status = "✓ alive" if r.is_alive else "✗ dead "
        print(f"  {status}  {r.url}")


def demo_news() -> None:
    from bertina.search import BertinaSearch, SearchType

    header("3 · News Search  (query: 'ایران')")

    with BertinaSearch() as client:
        resp = client.search("ایران", type=SearchType.NEWS)

    for r in resp.results[:4]:
        print(f"  [{r.source}]  {r.title}")
        if r.published_at:
            print(f"            {r.published_at}")


def demo_scholar() -> None:
    from bertina.search import BertinaSearch, SearchType

    header("4 · Scholar Search  (query: 'deep learning')")

    with BertinaSearch() as client:
        resp = client.search("deep learning", type=SearchType.SCHOLAR)

    for r in resp.results[:3]:
        print(f"  {r.title}")
        print(f"    {r.authors_and_year or '—'}  |  citations: {r.citations or '—'}")


# ── 2. RADAR ─────────────────────────────────────────────────────────────────


def demo_radar() -> None:
    from bertina.radar import BertinaRadar

    header("5 · News Radar")

    with BertinaRadar() as client:
        page = client.get()

    print(f"  hot topics      : {len(page.hot)}")
    print(f"  important topics: {len(page.important)}")

    print("\n  Top 5 hot:")
    for item in page.hot[:5]:
        print(f"    #{item.rank}  {item.title}  [{item.category}]")

    print("\n  Top 3 important:")
    for item in page.important[:3]:
        print(f"    #{item.rank}  {item.title}")


# ── 3. PLACES ────────────────────────────────────────────────────────────────


def demo_places() -> None:
    from bertina.places import BertinaPlaces

    header("6 · Places Directory")

    with BertinaPlaces() as client:
        provinces = client.get_provinces()

    print(f"  provinces : {len(provinces)}")
    total_cities = sum(len(p.cities) for p in provinces)
    print(f"  cities    : {total_cities}")

    print("\n  First 3 provinces:")
    for p in provinces[:3]:
        print(f"    {p.name}  ({len(p.cities)} cities)")
        for c in p.cities[:3]:
            print(f"      · {c.name}  {c.place_count}")


def demo_places_city() -> None:
    from bertina.places import BertinaPlaces

    header("7 · Places — city listing (تهران)")

    with BertinaPlaces() as client:
        categories = client.get_city("تهران")

    print(f"  categories found: {len(categories)}")
    for cat in categories[:6]:
        print(f"    · {cat.name}  {cat.place_count}")


# ── 4. TRANSLATE ─────────────────────────────────────────────────────────────


def demo_translate() -> None:
    from bertina.translate import BertinaTranslate, Language

    header("8 · Translation")

    with BertinaTranslate() as client:
        en_to_fa = client.translate(
            "Artificial intelligence is changing the world.", target=Language.FA
        )
        fa_to_en = client.translate(
            "دنیا دارد تغییر می‌کند.", source=Language.FA, target=Language.EN
        )
        auto_detect = client.translate("Bonjour le monde", target=Language.EN)

    print("  EN → FA")
    print(f"    input   : {en_to_fa.source_text}")
    print(f"    output  : {en_to_fa.translated_text}")
    print(f"    detected: {en_to_fa.detected_lang}")

    print("\n  FA → EN")
    print(f"    input   : {fa_to_en.source_text}")
    print(f"    output  : {fa_to_en.translated_text}")

    print("\n  AUTO-DETECT (FR → EN)")
    print(f"    input   : {auto_detect.source_text}")
    print(f"    output  : {auto_detect.translated_text}")
    print(f"    detected: {auto_detect.detected_lang}")


# ── 5. WEATHER ───────────────────────────────────────────────────────────────


def demo_weather() -> None:
    from bertina.weather import BertinaWeather

    header("9 · Weather Forecast (Tehran)")

    with BertinaWeather() as client:
        forecast = client.forecast("Tehran")

    cur = forecast.current
    print(
        f"  location    : {forecast.location}  ({forecast.latitude}, {forecast.longitude})"
    )
    print(f"  condition   : {cur.condition}")
    print(f"  temperature : {cur.temperature} °C  (feels like {cur.feels_like} °C)")
    print(f"  humidity    : {cur.humidity} %")
    print(f"  wind        : {cur.wind_speed} km/h")
    print(f"  UV index    : {cur.uv_index}")
    print(f"  pressure    : {cur.pressure} hPa")

    print("\n  7-day forecast:")
    for day in forecast.daily:
        print(
            f"    {day.date}  {day.temp_min:4.1f}–{day.temp_max:4.1f} °C  {day.condition}  "
            f"rain {day.precipitation_probability}%"
        )

    print("\n  Next 6 hours:")
    for hour in forecast.hourly[:6]:
        print(f"    {hour.time}  {hour.temperature:5.1f} °C  {hour.condition}")


# ── entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    steps = [
        ("Search", demo_search),
        ("Alive check", demo_alive_check),
        ("News", demo_news),
        ("Scholar", demo_scholar),
        ("Radar", demo_radar),
        ("Places list", demo_places),
        ("Places city", demo_places_city),
        ("Translate", demo_translate),
        ("Weather", demo_weather),
    ]

    for name, fn in steps:
        try:
            fn()
        except Exception as exc:
            print(f"\n  !! {name} failed: {exc}\n")


if __name__ == "__main__":
    main()
