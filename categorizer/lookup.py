
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
    # ── Handwerkzeuge & Werkstatt (KS Tools) ───────────────
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

    # ── Smartphones & Zubehör (Schutzglas & Hüllen IMMER vor Smartphone!) ──
    (r"\b(schutzglas|panzerglas|clear protect|displayschutz|kameraschutz|cam protect)\b", "1806235", "Displayschutzglas"),
    (r"\b(handytasche|handyhülle|smartphone-hülle|booklet|cover|case\b|daily protect|extreme protect|slim protect|fantastic feel)\b", "1807030", "Handytaschen & Schutzhüllen"),
    (r"\b(magnetkabel|ladekabel.*case|nomad case)\b", "0410105", "Ladekabel & Magnetkabel"),
    (r"\b(tischladestation|ladestation.*telefon)\b", "2110050", "Telefon-Ladestationen"),
    (r"\b(seniorenhandy|großtastenhandy|amplibase)\b", "1801050", "Senioren-Mobiltelefone"),
    (r"\b(iphone|galaxy\s+s2[0-9]|smartphone)\b", "1801015", "Smartphones"),

    # ── Festnetz & Telekommunikation (Spezifisch vor Allgemein!) ──
    (r"\b(schnurgebundenes festnetztelefon|schnurtelefon|schnurgebunden)\b", "1002014", "Schnurgebundene Festnetztelefone"),
    (r"\b(festnetztelefon|seniorentelefon|xtra 4g|xtra 2355)\b", "1018010", "Senioren- & 4G-Telefone"),

    # ── Haushalt, Saugen & Reinigen ────────────────────────
    (r"\b(staubsaugerbeutel|ecopor|airspace)\b", "0601139", "Staubsaugerbeutel"),
    (r"\b(abluftfilter.*staubsauger|deo perlen.*staubsauger|staubsaugerfilter)\b", "6904040", "Staubsaugerfilter & Zubehör"),
    (r"\b(bürstdüse|fugenreinigungsdüse|hartbodendüse|fussel.*entfernungsdüse)\b", "2205419", "Staubsaugerdüsen"),
    (r"\b(akku staubsauger|kabelloser.*staubsauger|handstaubsauger)\b", "6904010", "Akku-Staubsauger"),
    (r"\b(fusselentferner|fusselrasierer)\b", "0601121", "Fusselentferner"),

    # ── Küche & Kochen (Severin, Samura) ───────────────────
    (r"\b(kochmesser|schleifstein|messerwinkelhalter|santokumesser)\b", "0602004", "Küchenmesser & Schleifzubehör"),
    (r"\b(mikrowelle)\b", "6902073", "Mikrowellen"),
    (r"\b(heißluftfritteuse|s-fry|airfryer)\b", "0601146", "Heißluftfritteusen"),
    (r"\b(smoothie mixer|stabmixer|standmixer)\b", "0601151", "Mixer & Stabmixer"),
    (r"\b(kaffeemaschine)\b", "0601147", "Kaffeemaschinen"),
    (r"\b(multigrill|kontaktgrill)\b", "0601174", "Kontaktgrills & Multigrills"),
    (r"\b(waffeleisen|duo-waffeleisen)\b", "0601178", "Waffeleisen"),
    (r"\b(allesschneider)\b", "0601142", "Allesschneider"),
    (r"\b(slush|ice cream maker|eismaschine)\b", "0601171", "Eismaschinen"),
    (r"\b(induktionskochplatte|einzelkochplatte)\b", "0601148", "Induktionskochplatten"),

    # ── Körperpflege & Gesundheit (Braun, Oral-B, Philips) ──
    (r"\b(zahnbürste|oral-b|sonicare|schallzahnbürste)\b", "0605046", "Elektrische Zahnbürsten"),
    (r"\b(bodygroomer|haarschneider|barttrimmer|rasierer)\b", "0605042", "Rasierer & Haarschneider"),
    (r"\b(glätteisen|haarglätter)\b", "0605053", "Haarglätter"),
    (r"\b(lockenstab)\b", "0813060", "Lockenstäbe"),
    (r"\b(heizkissen|wärmekissen|wärmedecke)\b", "0601015", "Heizkissen & Wärmedecken"),
    (r"\b(massagepistole|massagegerät)\b", "0601116", "Massagegeräte"),
    (r"\b(inhalator|vernebler)\b", "0601117", "Inhalatoren"),

    # ── Uhren & Wecker (Eurotime) ──────────────────────────
    (r"\b(wecker|radiowecker|wake up)\b", "0819010", "Wecker & Radiowecker"),
    (r"\b(funkwanduhr|wanduhr)\b", "0819016", "Wanduhren & Funkuhren"),

    # ── Bastelbedarf & Plotter (Siser) ─────────────────────
    (r"\b(schneideplotter|plotter\b)\b", "0405004", "Schneideplotter"),
    (r"\b(plotterfolie|bügelfolie|textiltransfer|crafty pocket|easyweed)\b", "1209024", "Plotterfolien & Textiltransfer"),
    (r"\b(cutting mat|schneidematte)\b", "2801160", "Schneidematten"),
    (r"\b(sublimation marker|sublimationsstift)\b", "0402051", "Sublimationsstifte"),

    # ── PC Hardware & Gaming (Thermaltake) ─────────────────
    (r"\b(pc-gehäuse|midi-tower|tg argb)\b", "0414010", "PC-Gehäuse"),
    (r"\b(aio.*kühler|wasserkühlung|wasserkühler)\b", "0415153", "PC-Wasserkühlung"),
    (r"\b(gaming monitor|oled.*monitor)\b", "0413017", "Gaming Monitore"),
    (r"\b(racing wheel|pedals damper)\b", "0409020", "Gaming-Lenkräder & Pedale"),
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
    gemini_api_key: str = "",
) -> tuple[str | None, str | None, str]:
    """
    Attempt to find a Conrad category for a product purely by product name.

    Pipeline (in order):
      1. Local name cache
      2. Domain keyword rules
      3. Conrad.de urllib search (best-effort, may be blocked)
      4. Gemini AI classification (if api_key is provided)

    Returns (category_id, category_name, url).
    category_id is None when no match was found → "Manuell pflegen".
    Leading zeros are preserved via zfill(7).
    """
    if cache is None:
        cache = {}

    clean_name = name.strip() if name else ""
    if not clean_name:
        return None, None, "https://www.conrad.de"

    # 1. Local cache (keyed strictly by product name)
    if clean_name in cache:
        cid = cache[clean_name]
        return (
            cid,
            "Lokaler Cache",
            f"https://www.conrad.de/de/o/-{cid}.html",
        )

    # 2. Domain keyword matching rules
    lower_name = clean_name.lower()
    for pattern, cid, cname in KEYWORD_RULES:
        if re.search(pattern, lower_name):
            cid_str = cid.zfill(7)
            cache[clean_name] = cid_str
            return cid_str, cname, f"https://www.conrad.de/de/o/-{cid_str}.html"

    # 3. Conrad.de urllib search (may return empty if site blocks request)
    clean_title = re.sub(r'[,/()"\']', " ", clean_name)
    words = [w for w in clean_title.split() if len(w) > 2][:4]
    q_title = " ".join(words)
    if q_title:
        cands = conrad_search(q_title)
        if cands:
            cid = cands[0]["category_id"].zfill(7)
            cache[clean_name] = cid
            return cid, cands[0]["category_name"], cands[0]["url"]

    # 4. Gemini AI fallback (only when API key is configured)
    if gemini_api_key:
        try:
            from categorizer.gemini_classifier import classify_single
            cid, cname = classify_single(0, clean_name, gemini_api_key)
            if cid:
                cid_str = cid.zfill(7)
                cache[clean_name] = cid_str
                return cid_str, f"🤖 {cname}", f"https://www.conrad.de/de/o/-{cid_str}.html"
        except Exception:
            pass

    fallback_url = "https://www.conrad.de/de/search.html?search=" + urllib.parse.quote(
        clean_name
    )
    return None, None, fallback_url
