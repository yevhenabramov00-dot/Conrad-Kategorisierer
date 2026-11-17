"""
conrad_app.py
-------------
Entry point for the Conrad Kategorisierer desktop application.

Architecture
------------
  conrad_app.py           ← this file (entry point, PySide6 bootstrap)
  ui/
      __init__.py
      main_window.py      ← QMainWindow, WorkerThread, widgets
      theme.py            ← design system: colors, stylesheets
  categorizer/
      __init__.py
      lookup.py           ← Conrad.de search + keyword matching
      excel_processor.py  ← openpyxl read / write

Usage
-----
  python conrad_app.py
  or double-click the packaged .exe / .app bundle.
"""

import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# PySide6 availability check
# ---------------------------------------------------------------------------
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtCore import Qt
except ImportError as exc:
    print(
        f"[error] PySide6 not found: {exc}\n"
        "Please install it: pip install PySide6"
    )
    sys.exit(1)

from ui.main_window import MainWindow

# ---------------------------------------------------------------------------
# Asset resolution (works for both dev and PyInstaller bundles)
# ---------------------------------------------------------------------------
def _resource_path(relative: str) -> str:
    """Return an absolute path that works in dev mode and in a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = str(Path(__file__).parent)
    return os.path.join(base, relative)


# ---------------------------------------------------------------------------
# Application bootstrap
# ---------------------------------------------------------------------------
def main() -> None:
    # High-DPI scaling (must be set before QApplication is created)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Conrad Kategorisierer")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Conrad Electronic SE")

    # Font stack
    font = QFont()
    font.setFamilies(["Segoe UI", "SF Pro Text", "-apple-system", "Helvetica Neue", "Arial"])
    font.setPointSize(13)
    app.setFont(font)

    # Windows Taskbar Icon grouping & display fix for corporate laptops
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "ConradElectronic.Categorizer.App.2.0"
            )
        except Exception:
            pass

    # App icon (square "CK" monogram for window, taskbar and dock)
    app_icon_path = _resource_path(os.path.join("assets", "app_icon.png"))
    if not os.path.exists(app_icon_path):
        app_icon_path = _resource_path(os.path.join("assets", "app_icon.ico"))

    # Sidebar branding logo
    sidebar_logo_path = _resource_path(os.path.join("assets", "conrad_logo.png"))

    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))
    elif os.path.exists(sidebar_logo_path):
        app.setWindowIcon(QIcon(sidebar_logo_path))

    window = MainWindow(logo_path=sidebar_logo_path)
    if os.path.exists(app_icon_path):
        window.setWindowIcon(QIcon(app_icon_path))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
