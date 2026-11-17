"""
categorizer/excel_processor.py
-------------------------------
Excel file reading and writing via openpyxl.
No UI dependencies – communicates only via callback.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

try:
    import openpyxl
    from openpyxl.styles.numbers import FORMAT_TEXT
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from categorizer.lookup import match_product, MANUAL_FALLBACK_TEXT


def derive_output_path(input_path: str) -> str:
    """Return the auto-generated output file path next to the input file."""
    p = Path(input_path)
    return str(p.with_name(f"{p.stem}_categorized{p.suffix}"))


def process_file(
    in_file: str,
    out_file: str,
    cache: dict,
    on_row: Callable[[int, str, str, str, str, str], None],
    on_progress: Callable[[int, int, int, int], None],
    on_status: Callable[[str], None],
    stop_flag: Callable[[], bool],
) -> dict:
    """
    Load *in_file*, categorize every product row, write *out_file*.

    Callbacks
    ---------
    on_row(row_num, name, mpn, status_text, cat_id, cat_name)
    on_progress(current, total, matched_plus_skipped, manual)
    on_status(message)
    stop_flag() → True means the caller wants to abort

    Returns a summary dict with keys:
        total, matched, skipped, manual, out_file
    """
    if not OPENPYXL_AVAILABLE:
        raise RuntimeError("openpyxl ist nicht installiert.")

    on_status("Öffne Excel-Datei…")
    wb = openpyxl.load_workbook(in_file)
    sheet_name = (
        "Produktcheckliste"
        if "Produktcheckliste" in wb.sheetnames
        else wb.sheetnames[0]
    )
    ws = wb[sheet_name]

    # Dynamic column discovery from header row
    col_map: dict[str, int] = {}
    for col_idx in range(1, ws.max_column + 1):
        val = ws.cell(row=1, column=col_idx).value
        if val:
            col_map[str(val).strip()] = col_idx

    parent_col = col_map.get("Parent", 4)
    name_col = col_map.get("Name", 37)
    ean_col = col_map.get("Product.EAN.Main", 40)
    mpn_col = col_map.get(
        "ATT.GLOBAL.ManufacturerAID",
        col_map.get(
            "Product.Supplier.ArticleID",
            col_map.get("ATT.GLOBAL.ManufacturerTypeDesc", 43),
        ),
    )

    start_row = 8
    max_row = ws.max_row
    valid_rows = [
        r
        for r in range(start_row, max_row + 1)
        if ws.cell(row=r, column=name_col).value
        and str(ws.cell(row=r, column=name_col).value).strip()
    ]

    total = len(valid_rows)
    matched = 0
    manual = 0
    skipped = 0

    on_progress(0, total, 0, 0)

    for idx, r in enumerate(valid_rows, 1):
        if stop_flag():
            break

        name_val = str(ws.cell(row=r, column=name_col).value or "").strip()
        parent_cell = ws.cell(row=r, column=parent_col)
        current_parent = parent_cell.value
        mpn_val = str(ws.cell(row=r, column=mpn_col).value or "").strip()
        ean_val = str(ws.cell(row=r, column=ean_col).value or "").strip()

        if current_parent and str(current_parent).strip():
            # Already filled – skip
            skipped += 1
            status_text = "Übersprungen"
            cat_id_text = str(current_parent).strip()
            cat_name_text = "Vorhanden"
        else:
            on_status(f"Verarbeite Zeile {r}/{max_row}: {name_val[:45]}…")
            cat_id, cat_name, _ = match_product(name_val, mpn_val, ean_val, cache)
            parent_cell.number_format = FORMAT_TEXT  # preserve leading zeros

            if cat_id:
                parent_cell.value = str(cat_id).zfill(7)
                matched += 1
                status_text = "Zugeordnet"
                cat_id_text = parent_cell.value
                cat_name_text = cat_name or ""
            else:
                parent_cell.value = MANUAL_FALLBACK_TEXT
                manual += 1
                status_text = "Manuell"
                cat_id_text = MANUAL_FALLBACK_TEXT
                cat_name_text = "Keine Zuordnung"

        on_row(r, name_val, mpn_val, status_text, cat_id_text, cat_name_text)
        on_progress(idx, total, matched + skipped, manual)

        # Incremental save every 5 rows
        if idx % 5 == 0:
            wb.save(out_file)

    wb.save(out_file)

    return {
        "total": total,
        "matched": matched,
        "skipped": skipped,
        "manual": manual,
        "out_file": out_file,
    }
