"""
categorizer/browser_scraper.py
-------------------------------
Playwright-based browser automation for Conrad.de scraping.
Launches a real Chromium-based browser (Comet or Google Chrome on macOS)
to bypass bot detection. Runs visibly so the user can minimize it.
"""

from __future__ import annotations

import re
import time
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# Browser executable discovery (Comet first, then Chrome as fallback)
# ---------------------------------------------------------------------------

BROWSER_CANDIDATES = [
    # Comet (Perplexity)
    "/Applications/Comet.app/Contents/MacOS/Comet",
    str(Path.home() / "Applications/Comet.app/Contents/MacOS/Comet"),
    # Google Chrome
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
]


def find_browser_executable() -> str | None:
    """Return the first usable Chromium-based browser binary, or None."""
    for path in BROWSER_CANDIDATES:
        if Path(path).exists():
            return path
    return None


# ---------------------------------------------------------------------------
# Conrad.de scraping via Playwright
# ---------------------------------------------------------------------------

CATEGORY_URL_RE = re.compile(r"/de/o/([a-zA-Z0-9\-]+)-(\d{7})\.html")
CATEGORY_ID_DIGITS_RE = re.compile(r"\b(\d{7})\b")


def _extract_categories_from_page(page) -> list[dict]:
    """
    Parse all 7-digit Conrad EFEU category IDs visible in the current page HTML.
    Returns a list of dicts with category_id, category_name, url.
    """
    results: list[dict] = []
    seen: set[str] = set()

    # 1. All /de/o/<slug>-<7digits>.html hrefs
    links = page.query_selector_all("a[href*='/de/o/']")
    for link in links:
        href = link.get_attribute("href") or ""
        m = CATEGORY_URL_RE.search(href)
        if m:
            slug, cid = m.group(1), m.group(2)
            if cid not in seen:
                seen.add(cid)
                label = link.inner_text().strip() or slug.replace("-", " ").title()
                results.append({
                    "category_id": cid,
                    "category_name": label,
                    "url": f"https://www.conrad.de{href}",
                })

    # 2. Breadcrumb / product detail: look for category ID in page JSON data
    html = page.content()
    for m in CATEGORY_URL_RE.finditer(html):
        slug, cid = m.group(1), m.group(2)
        if cid not in seen:
            seen.add(cid)
            results.append({
                "category_id": cid,
                "category_name": slug.replace("-", " ").title(),
                "url": f"https://www.conrad.de/de/o/{slug}-{cid}.html",
            })

    return results


def search_on_conrad(
    product_name: str,
    page,
    delay_range: tuple[float, float] = (2.2, 4.0),
) -> list[dict]:
    """
    Search a single product name on Conrad.de using an already-open browser page.
    Takes deliberate pacing (2.2 - 4.0s) for high accuracy and bot safety.
    Returns list of matching categories, most relevant first.
    """
    query = product_name.strip()
    if not query:
        return []

    url = "https://www.conrad.de/de/search.html?search=" + re.sub(
        r"\s+", "+", query
    )

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=18000)
        # Polite delay to simulate human behavior and avoid rate limiting
        time.sleep(random.uniform(*delay_range))
        return _extract_categories_from_page(page)
    except Exception:
        return []


def run_browser_session(
    products: list[tuple[int, str]],
    on_result: callable,
    on_status: callable,
    stop_flag: callable,
    executable_path: str | None = None,
) -> None:
    """
    Launch a real browser, search each product on Conrad.de, and emit results.

    Parameters
    ----------
    products      : list of (row_number, product_name)
    on_result     : callback(row_num, product_name, category_id, category_name)
    on_status     : callback(str)  – status text updates
    stop_flag     : callable() -> bool  – return True to abort
    executable_path : explicit path to Chrome/Comet binary (auto-detected if None)
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        on_status("Playwright nicht installiert. Bitte: pip install playwright && playwright install chromium")
        for row_num, name in products:
            on_result(row_num, name, None, None)
        return

    exe = executable_path or find_browser_executable()

    on_status("Browser wird gestartet…")

    launch_kwargs: dict = {
        "headless": False,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    }
    if exe:
        launch_kwargs["executable_path"] = exe
        on_status(f"Verwende Browser: {Path(exe).name}")
    else:
        on_status("Kein Chrome/Comet gefunden – verwende Playwright Chromium")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            locale="de-DE",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        # Warm up: open Conrad.de once to get cookies/session
        try:
            page.goto("https://www.conrad.de", wait_until="domcontentloaded", timeout=18000)
            time.sleep(1.5)
        except Exception:
            pass

        for row_num, name in products:
            if stop_flag():
                break
            on_status(f"Suche auf Conrad.de: {name[:50]}…")
            cats = search_on_conrad(name, page)
            if cats:
                on_result(row_num, name, cats[0]["category_id"], cats[0]["category_name"])
            else:
                on_result(row_num, name, None, None)

        browser.close()
    on_status("Browser-Suche abgeschlossen.")
