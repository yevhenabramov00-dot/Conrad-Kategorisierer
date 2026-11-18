"""
categorizer/gemini_classifier.py
---------------------------------
Gemini API integration for semantic category classification.
Takes a product name and classifies it into Conrad's 7-digit EFEU category
using the Gemini generative AI model.

No browser required. Uses the product name directly.
"""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
DEFAULT_MODEL = "gemini-2.0-flash"

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Du bist ein Experte für Conrad.de Produktkategorien.
Conrad.de verwendet ein hierarchisches Kategoriensystem mit 7-stelligen numerischen IDs (z.B. 1517028, 2700480, 1512020).

Deine Aufgabe: Für jeden gegebenen Produktnamen (auf Deutsch) ordne das Produkt der passendsten Conrad EFEU-Kategorie zu.

Regeln:
- Antworte NUR mit einem JSON-Objekt pro Produkt.
- Gib die 7-stellige Kategorie-ID als String mit führenden Nullen zurück.
- Wenn du sehr unsicher bist, setze confidence auf "low" - dann wird "Manuell pflegen" gesetzt.
- Fokussiere dich auf den Produkttyp (Substantiv), nicht auf die Marke.

Bekannte Kategorie-Beispiele (nicht vollständig):
- 1517028 = Flachrundzangen
- 2700480 = Werkstatt-Auftragstaschen / Dokumententaschen
- 1512020 = Bit-Sets / Wechselbit-Sätze  
- 1506057 = Akkus für Werkzeug (18V, Li-Ion)
- 0502019 = Ladegeräte & Ladepads
- 0312024 = Drehmomentschlüssel
- 1517983 = Druckluft-Schlagschrauber
- 1515110 = Offene Ringschlüssel mit Gelenk
- 1502030 = Steckschlüssel & Schraubenschlüssel-Sätze
- 1502010 = Zangen (allgemein)
- 1502021 = Winkelstiftschlüssel / Torx-Schlüssel
- 0312023 = Radmutternschlüssel / LKW-Radmutternschlüssel
- 0312020 = Reifen & Radwerkzeuge
- 1504060 = Werkstatteinrichtung (Liegen, Rollbretter)
- 0312068 = Reifenmontagepaste
- 0312070 = KFZ-Diagnose & Lecksuche (Videoskope, Nebelmaschinen)
- 0312026 = KFZ-Motorwerkzeuge (Riemenscheiben, Kupplungen)
- 0812022 = Bremsen & KFZ-Elektrik
- 1202204 = Achs- & Antriebswellenwerkzeuge
- 2201010 = Arbeitsschutzbrillen
- 1506051 = Stufenbohrer
- 1516040 = Hämmer & Schlagwerkzeuge
- 1510020 = Winkelmesser
- 1517032 = Ersatzklingen
- 0312040 = Arbeitsleuchten & Taschenlampen
- 3300200 = Feuerzeuge
- 0312027 = KFZ-Spezialwerkzeuge (Stanzen, Dorne)
- 0203110 = Zapfenschlüssel / Zahnradwerkzeuge
- 1900146 = Musterartikel / Testprodukte
"""

USER_PROMPT_TEMPLATE = """Klassifiziere folgende Produkte und antworte mit einem JSON-Array:

{products}

Antworte mit genau diesem Format (JSON-Array, ein Objekt pro Produkt):
[
  {{
    "row": <Zeilennummer>,
    "name": "<Produktname>",
    "category_id": "<7-stellige-ID oder null>",
    "category_name": "<Kategoriename auf Deutsch>",
    "confidence": "high|medium|low"
  }}
]
"""


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

def classify_products(
    products: list[tuple[int, str]],
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> list[dict]:
    """
    Send a batch of products to Gemini and return classification results.

    Parameters
    ----------
    products : list of (row_number, product_name)
    api_key  : Gemini API key
    model    : model name string

    Returns
    -------
    list of dicts with keys: row, name, category_id, category_name, confidence
    """
    if not products or not api_key or not api_key.strip():
        return []

    # Build the product listing for the prompt
    product_lines = "\n".join(
        f"- Zeile {row}: {name}"
        for row, name in products
    )
    user_prompt = USER_PROMPT_TEMPLATE.format(products=product_lines)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": SYSTEM_PROMPT + "\n\n" + user_prompt}
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    url = GEMINI_API_URL.format(model=model, api_key=api_key.strip())
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Gemini API Fehler {e.code}: {e.read().decode()}")
    except Exception as e:
        raise RuntimeError(f"Gemini API Verbindungsfehler: {e}")

    # Parse response
    data = json.loads(raw)
    text = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )

    # Strip markdown code fences if present
    text = re.sub(r"^```[a-z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text.strip())

    try:
        results = json.loads(text)
        if isinstance(results, dict):
            results = [results]
        return results if isinstance(results, list) else []
    except json.JSONDecodeError:
        return []


def classify_single(
    row_num: int,
    product_name: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> tuple[str | None, str | None]:
    """
    Classify a single product. Returns (category_id, category_name).
    Returns (None, None) if confidence is low or API fails.
    """
    try:
        results = classify_products([(row_num, product_name)], api_key, model)
        if results:
            r = results[0]
            cid = r.get("category_id")
            cname = r.get("category_name")
            confidence = r.get("confidence", "medium")
            if confidence == "low" or not cid:
                return None, None
            # Ensure 7-digit format
            if cid and str(cid).isdigit():
                return str(cid).zfill(7), cname
    except Exception:
        pass
    return None, None
