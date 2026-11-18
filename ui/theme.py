"""
ui/theme.py
-----------
Conrad design system: colors, typography, spacing, stylesheets.
Supports Light and Dark modes.
"""

from __future__ import annotations

# ── Conrad brand palette ────────────────────────────────────────────────────
# Primary blue derived from the Conrad logotype (#3D82F5 / #4589F5 range)
CONRAD_BLUE   = "#4589F5"   # logo blue – primary accent
CONRAD_BLUE_D = "#2D6FDF"   # darker pressed state

# ── Neutral palette (Slate-inspired, works well with the brand blue) ────────
# Light theme
L_BG          = "#F5F7FA"   # window background
L_SURFACE     = "#FFFFFF"   # card / panel surface
L_SURFACE2    = "#EEF1F7"   # subtle secondary surface
L_BORDER      = "#DDE3EE"   # border / divider
L_TEXT        = "#0D1117"   # primary text
L_TEXT_2      = "#5A6378"   # secondary / muted text
L_TEXT_3      = "#8C96AA"   # placeholder / caption
L_SUCCESS     = "#22C55E"
L_WARNING     = "#F59E0B"
L_ERROR       = "#EF4444"
L_MANUAL      = "#F59E0B"
L_SKIP        = "#64748B"

# Dark theme
D_BG          = "#0F1117"
D_SURFACE     = "#181C26"
D_SURFACE2    = "#232839"
D_BORDER      = "#2E3449"
D_TEXT        = "#E8EAEF"
D_TEXT_2      = "#8C96AA"
D_TEXT_3      = "#5A6378"
D_SUCCESS     = "#22C55E"
D_WARNING     = "#F59E0B"
D_ERROR       = "#EF4444"
D_MANUAL      = "#F59E0B"
D_SKIP        = "#64748B"


class Theme:
    """Holds resolved color tokens for the active mode."""

    def __init__(self, dark: bool = False) -> None:
        self.dark = dark
        self._resolve()

    def toggle(self) -> None:
        self.dark = not self.dark
        self._resolve()

    def _resolve(self) -> None:
        d = self.dark
        self.bg        = D_BG       if d else L_BG
        self.surface   = D_SURFACE  if d else L_SURFACE
        self.surface2  = D_SURFACE2 if d else L_SURFACE2
        self.border    = D_BORDER   if d else L_BORDER
        self.text      = D_TEXT     if d else L_TEXT
        self.text2     = D_TEXT_2   if d else L_TEXT_2
        self.text3     = D_TEXT_3   if d else L_TEXT_3
        self.accent    = CONRAD_BLUE
        self.accent_d  = CONRAD_BLUE_D
        self.success   = D_SUCCESS  if d else L_SUCCESS
        self.warning   = D_WARNING  if d else L_WARNING
        self.error     = D_ERROR    if d else L_ERROR
        self.manual    = D_MANUAL   if d else L_MANUAL
        self.skip      = D_SKIP     if d else L_SKIP

    # ── Stylesheet factories ────────────────────────────────────────────────

    def app_stylesheet(self) -> str:
        t = self
        return f"""
/* ── Global ─────────────────────────────────────────────── */
QWidget {{
    background-color: {t.bg};
    color: {t.text};
    font-family: "Segoe UI", "SF Pro Text", -apple-system, Arial, sans-serif;
    font-size: 13px;
}}
QToolTip {{
    background-color: {t.surface};
    color: {t.text};
    border: 1px solid {t.border};
    border-radius: 6px;
    padding: 4px 8px;
}}

/* ── Sidebar ─────────────────────────────────────────────── */
#Sidebar {{
    background-color: {t.surface};
    border-right: 1px solid {t.border};
}}
#AppTitle {{
    font-size: 15px;
    font-weight: 700;
    color: {t.text};
    letter-spacing: -0.3px;
}}
#AppSubtitle {{
    font-size: 11px;
    color: {t.text2};
}}
#SidebarSection {{
    font-size: 10px;
    font-weight: 600;
    color: {t.text3};
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}
#NavItem {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    text-align: left;
    color: {t.text2};
    font-size: 13px;
}}
#NavItem:hover {{
    background-color: {t.surface2};
    color: {t.text};
}}
#NavItemActive {{
    background-color: {t.accent}22;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    text-align: left;
    color: {t.accent};
    font-weight: 600;
    font-size: 13px;
}}

/* ── Drop Zone ───────────────────────────────────────────── */
#DropZone {{
    background-color: {t.surface};
    border: 2px dashed {t.border};
    border-radius: 16px;
}}
#DropZone:hover {{
    border-color: {t.accent};
    background-color: {t.accent}0A;
}}
#DropZoneActive {{
    background-color: {t.accent}18;
    border: 2px dashed {t.accent};
    border-radius: 16px;
}}
#DropLabel {{
    font-size: 15px;
    font-weight: 600;
    color: {t.text2};
}}
#DropHint {{
    font-size: 12px;
    color: {t.text3};
}}
#FileName {{
    font-size: 14px;
    font-weight: 600;
    color: {t.text};
}}
#FilePath {{
    font-size: 11px;
    color: {t.text3};
}}

/* ── Buttons ─────────────────────────────────────────────── */
#PrimaryBtn {{
    background-color: {t.accent};
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
}}
#PrimaryBtn:hover {{
    background-color: {t.accent_d};
}}
#PrimaryBtn:pressed {{
    background-color: {t.accent_d};
}}
#PrimaryBtn:disabled {{
    background-color: {t.border};
    color: {t.text3};
}}
#SecondaryBtn {{
    background-color: {t.surface2};
    color: {t.text};
    border: 1px solid {t.border};
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
}}
#SecondaryBtn:hover {{
    background-color: {t.border};
    color: {t.text};
}}
#SecondaryBtn:pressed {{
    background-color: {t.border};
}}
#SecondaryBtn:disabled {{
    color: {t.text3};
    border-color: {t.border};
}}
#IconBtn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 6px;
    color: {t.text2};
    font-size: 18px;
}}
#IconBtn:hover {{
    background-color: {t.surface2};
    color: {t.text};
}}

/* ── Stats Cards ─────────────────────────────────────────── */
#StatCard {{
    background-color: {t.surface};
    border: 1px solid {t.border};
    border-radius: 12px;
}}
#StatValue {{
    font-size: 28px;
    font-weight: 700;
    color: {t.text};
    letter-spacing: -1px;
}}
#StatLabel {{
    font-size: 11px;
    font-weight: 500;
    color: {t.text2};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ── Progress Bar ────────────────────────────────────────── */
QProgressBar {{
    background-color: {t.surface2};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {t.accent};
    border-radius: 4px;
}}

/* ── Table ───────────────────────────────────────────────── */
QTableWidget {{
    background-color: {t.surface};
    alternate-background-color: {t.surface2};
    border: 1px solid {t.border};
    border-radius: 12px;
    gridline-color: {t.border};
    selection-background-color: {t.accent}30;
    selection-color: {t.text};
    outline: none;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {t.accent}30;
    color: {t.text};
}}
QHeaderView::section {{
    background-color: {t.surface2};
    color: {t.text2};
    border: none;
    border-bottom: 1px solid {t.border};
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:first {{
    border-top-left-radius: 12px;
}}
QHeaderView::section:last {{
    border-top-right-radius: 12px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t.border};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t.text3};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background: {t.border};
    border-radius: 4px;
    min-width: 24px;
}}

/* ── Status Bar ──────────────────────────────────────────── */
#StatusBar {{
    background-color: {t.surface};
    border-top: 1px solid {t.border};
}}
#StatusText {{
    font-size: 12px;
    color: {t.text2};
}}

/* ── Section Header ──────────────────────────────────────── */
#SectionHeader {{
    font-size: 12px;
    font-weight: 600;
    color: {t.text3};
    letter-spacing: 0.6px;
    text-transform: uppercase;
}}

/* ── File Entry ──────────────────────────────────────────── */
QLineEdit {{
    background-color: {t.surface2};
    border: 1px solid {t.border};
    border-radius: 8px;
    padding: 7px 10px;
    color: {t.text};
    font-size: 12px;
}}
QLineEdit:focus {{
    border-color: {t.accent};
    background-color: {t.surface};
}}
QLineEdit::placeholder {{
    color: {t.text3};
}}

/* ── Separator ───────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {t.border};
}}
#Separator {{
    color: {t.border};
    max-height: 1px;
    background: {t.border};
}}

/* ── Settings / API key ──────────────────────────────────── */
#SettingsLabel {{
    font-size: 11px;
    font-weight: 600;
    color: {t.text3};
    letter-spacing: 0.4px;
}}
#SettingsCheck {{
    font-size: 12px;
    color: {t.text2};
    background: transparent;
    spacing: 6px;
}}
#SettingsCheck::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {t.border};
    background: {t.surface2};
}}
#SettingsCheck::indicator:checked {{
    background-color: {t.accent};
    border-color: {t.accent};
}}
#ApiKeyEdit {{
    background-color: {t.surface2};
    border: 1px solid {t.border};
    border-radius: 6px;
    padding: 5px 8px;
    color: {t.text};
    font-size: 11px;
    font-family: "SF Mono", "Consolas", monospace;
}}
#ApiKeyEdit:focus {{
    border-color: {t.accent};
}}

/* ── Main content area ───────────────────────────────────── */
#ContentArea {{
    background-color: {t.bg};
}}
"""
