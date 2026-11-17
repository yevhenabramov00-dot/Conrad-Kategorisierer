
"""
categorizer/lookup.py
---------------------
Conrad.de product search and category matching logic.
Pure business logic – no UI dependencies.
"""

import re
import json
import time
import random
import urllib.request
import urllib.parse

MANUAL_FALLBACK_TEXT = "Manuell pflegen"

# Domain keyword matching rules for high-confidence fallback
KEYWORD_RULES = [
    (r"\b(auftragstasche|werkstatt-auftragstasche)\b", "2700480", "Werkstatt-Auftragstaschen"),
    (r"\b(flachrundzange)\b", "1517028", "Flachrundzangen"),
    (r"\b(wechselbit|bit-stecknuss|bit-set|bitset|bitsatz)\b", "1512020", "Bit-Sets"),
    (r"\b(schnell-ladegerät|ladepad|ladegerät)\b", "0502019", "Ladegeräte & Ladepads"),
    (r"\b(emonster.*akku|akku.*werkzeug)\b", "1506057", "Werkzeug-Akkus"),
    (r"\b(akku)\b.*\b(18v|li-ion|batterie)\b", "1506057", "Werkzeug-Akkus"),
    (r"\b(drehmomentschlüssel|reparatursatz.*drehmoment)\b", "0312024", "Drehmomentschlüssel"),
    (r"\b(druckluft-schlagschrauber|schlagschrauber)\b", "1517983", "Druckluft-Schlagschrauber"),
    (r"\b(offener.*ringschlüssel|gelenkschlüssel)\b", "1515110", "Offene Ringschlüssel"),
    (r"\b(steckschlüssel|ringschlüssel|schraubenschlüssel-satz)\b", "1502030", "Steckschlüssel & Schraubenschlüssel"),
    (r"\b(kombizange|zangen?)\b", "1502010", "Zangen"),
    (r"\b(winkelstiftschlüssel|stiftschlüssel|torx-schlüssel)\b", "1502021", "Winkelstiftschlüssel"),
    (r"\b(lkw-radmutternschlüssel|radmutternschlüssel)\b", "0312023", "Radmutternschlüssel"),
    (r"\b(felgenschlüssel|rangierer|the minidevil)\b", "0312020", "Reifen & Radwerkzeuge"),
    (r"\b(schloß|laufrollensatz|laufschienen|rollbrett|liege|magnethalter)\b", "1504060", "Werkstatteinrichtung"),
    (r"\b(reifenmontagepaste|montagepaste)\b", "0312068", "Reifenmontagepaste"),
    (r"\b(injektoren|lecksuche|nebelmaschine|videoskop)\b", "0312070", "KFZ-Diagnose & Lecksuche"),
    (r"\b(motorbrücke|riemenscheiben|kupplungs.*de-und|zapfenschlüssel)\b", "0312026", "KFZ-Motorwerkzeuge"),
    (r"\b(bremsleitungs|prüflampe|bordnetz-spannungserhalter|sicherung.*500a)\b", "0812022", "Bremsen & KFZ-Elektrik"),
    (r"\b(ausdrücker.*antriebswellen|radnaben)\b", "1202204", "Achs- & Antriebswellenwerkzeuge"),
    (r"\b(schutzbrille)\b", "2201010", "Arbeitsschutzbrillen"),
    (r"\b(stufenbohrer)\b", "1506051", "Stufenbohrer"),
    (r"\b(maurerhammer|hammer)\b", "1516040", "Hämmer & Schlagwerkzeuge"),
    (r"\b(winkelgradmesser|winkelmesser)\b", "1510020", "Winkelmesser"),
    (r"\b(ersatzmesser|klingen)\b", "1517032", "Ersatzklingen"),
    (r"\b(cob-taschenlampe|taschenlampe)\b", "0312040", "Arbeitsleuchten & Taschenlampen"),
    (r"\b(feuerzeug)\b", "3300200", "Feuerzeuge"),
]


def conrad_search(query: str) -> list[dict]:
    """Query Conrad.de and return a list of matching categories."""
    if not query or not query.strip():
        return []
    clean_q = query.strip()
    url = (
        "https://www.conrad.de/de/search.html?search="
        + urllib.parse.quote(clean_q)
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    # Rate limit: polite delay to prevent aggressive bot triggering
    time.sleep(random.uniform(1.2, 2.5))
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    results = []
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
    for s in scripts:
        if '"articleGroup"' in s:
            try:
                data = json.loads(s)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "articleGroup" in item:
                            ag_idx = item.get("articleGroup")
                            ag_name_idx = item.get("articleGroupName")
                            category_id = (
                                data[ag_idx]
                                if isinstance(ag_idx, int) and ag_idx < len(data)
                                else str(ag_idx)
                            )
                            category_name = (
                                data[ag_name_idx]
                                if isinstance(ag_name_idx, int)
                                and ag_name_idx < len(data)
                                else str(ag_name_idx or "")
                            )
                            if isinstance(category_id, (str, int)) and str(
                                category_id
                            ).isdigit():
                                cat_id_str = str(category_id).zfill(7)
                                results.append(
                                    {
                                        "category_id": cat_id_str,
                                        "category_name": str(category_name),
                                        "url": f"https://www.conrad.de/de/o/-{cat_id_str}.html",
                                    }
                                )
            except Exception:
                pass
        cat_matches = re.findall(r"/de/o/([a-zA-Z0-9\-]+)-(\d{7})\.html", s)
        for slug, cid in cat_matches:
            results.append(
                {
                    "category_id": cid,
                    "category_name": slug.replace("-", " ").title(),
                    "url": f"https://www.conrad.de/de/o/{slug}-{cid}.html",
                }
            )

    seen: set[str] = set()
    deduped: list[dict] = []
    for r in results:
        cid = r["category_id"]
        if cid not in seen:
            seen.add(cid)
            deduped.append(r)
    return deduped


def match_product(
    name: str,
    brand_ref: str = "",
    ean: str = "",
    cache: dict | None = None,
) -> tuple[str | None, str | None, str]:
    """
    Attempt to find a Conrad category for a product purely by product name.

    Returns (category_id, category_name, url).
    category_id is None when no match was found.
    Leading zeros are preserved via zfill(7).
    """
    if cache is None:
        cache = {}

    clean_name = name.strip() if name else ""
    if not clean_name:
        return None, None, "https://www.conrad.de"

    # 1. Local cache (strictly by product name, never by brand)
    if clean_name in cache:
        cid = cache[clean_name]
        return (
            cid,
            "Lokaler Cache",
            f"https://www.conrad.de/de/o/-{cid}.html",
        )

    # 2. Domain keyword matching rules on product name
    lower_name = clean_name.lower()
    for pattern, cid, cname in KEYWORD_RULES:
        if re.search(pattern, lower_name):
            cid_str = cid.zfill(7)
            cache[clean_name] = cid_str
            return cid_str, cname, f"https://www.conrad.de/de/o/-{cid_str}.html"

    # 3. Product title search on Conrad.de
    clean_title = re.sub(r'[,/()"\']', " ", clean_name)
    words = [w for w in clean_title.split() if len(w) > 2][:4]
    q_title = " ".join(words)
    if q_title:
        cands = conrad_search(q_title)
        if cands:
            cid = cands[0]["category_id"].zfill(7)
            cache[clean_name] = cid
            return cid, cands[0]["category_name"], cands[0]["url"]

    fallback_url = "https://www.conrad.de/de/search.html?search=" + urllib.parse.quote(
        clean_name
    )
    return None, None, fallback_url
