"""
ui/main_window.py
-----------------
Conrad Categoriser – PySide6 main window.

Layout
------
┌─────────────┬────────────────────────────────────────────┐
│   Sidebar   │               Content Area                 │
│  (200 px)   │  ┌── Drop Zone ──────────────────────────┐ │
│  Logo       │  │  drag & drop / browse                 │ │
│  Nav        │  └───────────────────────────────────────┘ │
│             │  ┌── Stats ───────────────────────────────┐ │
│             │  │  Total | Categorised | Manual Review   │ │
│             │  └───────────────────────────────────────┘ │
│             │  ┌── Progress ────────────────────────────┐ │
│             │  │  bar + status text                     │ │
│             │  └───────────────────────────────────────┘ │
│             │  ┌── Results Table ───────────────────────┐ │
│             │  │  live product rows                     │ │
│             │  └───────────────────────────────────────┘ │
└─────────────┴──────────────────────────────────────────-─┘
│              Status bar                                   │
└───────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import os
import platform
import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import (
    Qt, QThread, Signal, QObject, QMimeData, QSize, QTimer
)
from PySide6.QtGui import (
    QColor, QDragEnterEvent, QDropEvent, QFont, QIcon,
    QPainter, QPainterPath, QPixmap, QPen
)
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QLineEdit, QAbstractItemView
)

from ui.theme import Theme
from categorizer.excel_processor import derive_output_path, process_file


# ── Worker ───────────────────────────────────────────────────────────────────

class WorkerSignals(QObject):
    row       = Signal(int, str, str, str, str, str)   # row data
    progress  = Signal(int, int, int, int)              # current/total/matched/manual
    status    = Signal(str)
    finished  = Signal(dict)
    error     = Signal(str)


class CategorizerWorker(QThread):
    def __init__(self, in_file: str, out_file: str, cache: dict) -> None:
        super().__init__()
        self.in_file  = in_file
        self.out_file = out_file
        self.cache    = cache
        self._stop    = False
        self.signals  = WorkerSignals()

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            result = process_file(
                in_file=self.in_file,
                out_file=self.out_file,
                cache=self.cache,
                on_row=lambda *a: self.signals.row.emit(*a),
                on_progress=lambda *a: self.signals.progress.emit(*a),
                on_status=lambda s: self.signals.status.emit(s),
                stop_flag=lambda: self._stop,
            )
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))


# ── Widgets ───────────────────────────────────────────────────────────────────

class LogoWidget(QLabel):
    """Renders the Conrad logo PNG scaled to fit the sidebar width."""

    def __init__(self, logo_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pix = QPixmap(logo_path)
        self.setFixedHeight(36)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        if self._pix.isNull():
            return
        scaled = self._pix.scaledToHeight(
            32, Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)


class StatCard(QWidget):
    """A single statistic card (value + label)."""

    def __init__(self, label: str, theme: Theme, accent_color: str | None = None) -> None:
        super().__init__()
        self.setObjectName("StatCard")
        self._accent = accent_color
        self._theme  = theme

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self._value = QLabel("0")
        self._value.setObjectName("StatValue")
        if accent_color:
            self._value.setStyleSheet(f"color: {accent_color}; font-size: 28px; font-weight: 700;")

        self._label = QLabel(label.upper())
        self._label.setObjectName("StatLabel")

        layout.addWidget(self._value)
        layout.addWidget(self._label)

    def set_value(self, v: int | str) -> None:
        self._value.setText(str(v))


class DropZone(QWidget):
    """Drag-and-drop area that also acts as a click target to browse."""

    file_selected = Signal(str)

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self._theme   = theme
        self._active  = False
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        self._icon = QLabel("📂")
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet("font-size: 32px; background: transparent;")

        self._main_lbl = QLabel("Excel-Datei hierher ziehen")
        self._main_lbl.setObjectName("DropLabel")
        self._main_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._hint_lbl = QLabel("oder klicken, um zu durchsuchen  •  .xlsx")
        self._hint_lbl.setObjectName("DropHint")
        self._hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Selected file display (hidden until a file is chosen)
        self._file_name  = QLabel()
        self._file_name.setObjectName("FileName")
        self._file_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._file_name.hide()

        self._file_path  = QLabel()
        self._file_path.setObjectName("FilePath")
        self._file_path.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._file_path.hide()

        layout.addWidget(self._icon)
        layout.addWidget(self._main_lbl)
        layout.addWidget(self._hint_lbl)
        layout.addWidget(self._file_name)
        layout.addWidget(self._file_path)

    # ── File display ──────────────────────────────────────────────────────

    def show_file(self, path: str) -> None:
        p = Path(path)
        self._icon.setText("📄")
        self._main_lbl.setText("Datei ausgewählt")
        self._hint_lbl.setText("Klicken um andere Datei zu wählen")
        self._file_name.setText(p.name)
        self._file_name.show()
        self._file_path.setText(str(p.parent))
        self._file_path.show()

    def clear(self) -> None:
        self._icon.setText("📂")
        self._main_lbl.setText("Excel-Datei hierher ziehen")
        self._hint_lbl.setText("oder klicken, um zu durchsuchen  •  .xlsx")
        self._file_name.hide()
        self._file_path.hide()

    # ── Drag & drop ───────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith(".xlsx") for u in urls):
                self._active = True
                self.setObjectName("DropZoneActive")
                self.style().unpolish(self)
                self.style().polish(self)
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        self._active = False
        self.setObjectName("DropZone")
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        self._active = False
        self.setObjectName("DropZone")
        self.style().unpolish(self)
        self.style().polish(self)
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".xlsx"):
                self.file_selected.emit(path)
                return

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._browse()

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Excel-Datei auswählen",
            "",
            "Excel-Arbeitsmappen (*.xlsx);;Alle Dateien (*)",
        )
        if path:
            self.file_selected.emit(path)


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, logo_path: str = "") -> None:
        super().__init__()
        self._theme      = Theme(dark=False)
        self._logo_path  = logo_path
        self._cache: dict = {}
        self._worker: CategorizerWorker | None = None
        self._in_file    = ""
        self._out_file   = ""
        self._running    = False

        self.setWindowTitle("Conrad Kategorisierer")
        self.setMinimumSize(1050, 680)
        self.resize(1200, 760)

        self._build_ui()
        self._apply_theme()

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("ContentArea")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content(), 1)

        # Status bar
        self._status_bar = self.statusBar()
        self._status_lbl = QLabel("Bereit. Bitte wählen Sie eine Excel-Datei aus.")
        self._status_lbl.setObjectName("StatusText")
        self._status_bar.addWidget(self._status_lbl)
        self._status_bar.setObjectName("StatusBar")

    # ── Sidebar ───────────────────────────────────────────────────────────

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(0)

        # Logo
        if self._logo_path and Path(self._logo_path).exists():
            logo = LogoWidget(self._logo_path)
            layout.addWidget(logo)
        else:
            lbl = QLabel("CONRAD")
            lbl.setStyleSheet(
                f"font-size: 20px; font-weight: 800; "
                f"color: {self._theme.accent}; letter-spacing: -1px;"
            )
            layout.addWidget(lbl)

        layout.addSpacing(4)

        sub = QLabel("Kategorisierer")
        sub.setObjectName("AppSubtitle")
        layout.addWidget(sub)

        layout.addSpacing(32)

        # Section label
        nav_section = QLabel("NAVIGATION")
        nav_section.setObjectName("SidebarSection")
        layout.addWidget(nav_section)
        layout.addSpacing(8)

        # Nav items (single-screen app — visual nav only)
        self._nav_start = self._nav_item("⬛  Start", active=True)
        layout.addWidget(self._nav_start)

        layout.addStretch()

        # Theme toggle
        self._theme_btn = QPushButton("☀  Helles Design")
        self._theme_btn.setObjectName("NavItem")
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.setFlat(True)
        self._theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self._theme_btn)

        layout.addSpacing(8)

        # Version
        ver = QLabel("v2.0")
        ver.setObjectName("AppSubtitle")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

        return sidebar

    def _nav_item(self, text: str, active: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("NavItemActive" if active else "NavItem")
        btn.setFlat(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return btn

    # ── Content ───────────────────────────────────────────────────────────

    def _build_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("ContentArea")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 16)
        layout.setSpacing(20)

        # Page header
        header = QHBoxLayout()
        page_title = QLabel("Katalog verarbeiten")
        page_title.setStyleSheet(
            "font-size: 20px; font-weight: 700; letter-spacing: -0.5px;"
        )
        header.addWidget(page_title)
        header.addStretch()

        # Theme toggle button (icon in header)
        self._header_theme_btn = QPushButton("🌙")
        self._header_theme_btn.setObjectName("IconBtn")
        self._header_theme_btn.setFixedSize(36, 36)
        self._header_theme_btn.setToolTip("Design wechseln")
        self._header_theme_btn.clicked.connect(self._toggle_theme)
        header.addWidget(self._header_theme_btn)

        layout.addLayout(header)

        # Drop zone + path row
        self._drop_zone = DropZone(self._theme)
        self._drop_zone.file_selected.connect(self._on_file_selected)
        layout.addWidget(self._drop_zone)

        # Output path row
        path_row = QHBoxLayout()
        path_lbl = QLabel("Ausgabedatei:")
        path_lbl.setObjectName("SectionHeader")
        path_lbl.setFixedWidth(100)
        self._out_path_edit = QLineEdit()
        self._out_path_edit.setPlaceholderText("Wird automatisch neben der Quelldatei erstellt…")
        self._out_path_edit.setReadOnly(True)
        path_row.addWidget(path_lbl)
        path_row.addWidget(self._out_path_edit, 1)
        layout.addLayout(path_row)

        # Stats cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._card_total    = StatCard("Produkte gesamt", self._theme)
        self._card_matched  = StatCard("Zugeordnet",      self._theme, "#22C55E")
        self._card_manual   = StatCard("Manuell pflegen", self._theme, "#F59E0B")
        self._card_skipped  = StatCard("Übersprungen",    self._theme, "#64748B")
        for c in (self._card_total, self._card_matched, self._card_manual, self._card_skipped):
            cards_row.addWidget(c)
        layout.addLayout(cards_row)

        # Progress row
        prog_col = QVBoxLayout()
        prog_col.setSpacing(6)
        self._progress = QProgressBar()
        self._progress.setFixedHeight(6)
        self._progress.setTextVisible(False)
        self._progress.setValue(0)
        prog_col.addWidget(self._progress)
        self._prog_lbl = QLabel("Bereit")
        self._prog_lbl.setObjectName("StatusText")
        prog_col.addWidget(self._prog_lbl)
        layout.addLayout(prog_col)

        # Action buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._start_btn = QPushButton("▶  Verarbeitung starten")
        self._start_btn.setObjectName("PrimaryBtn")
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.setFixedHeight(42)
        self._start_btn.clicked.connect(self._on_start)
        self._start_btn.setEnabled(False)

        self._stop_btn = QPushButton("⏹  Stopp")
        self._stop_btn.setObjectName("SecondaryBtn")
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setFixedHeight(42)
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)

        self._open_file_btn = QPushButton("📄  Ergebnis öffnen")
        self._open_file_btn.setObjectName("SecondaryBtn")
        self._open_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_file_btn.setFixedHeight(42)
        self._open_file_btn.clicked.connect(self._open_output_file)
        self._open_file_btn.setEnabled(False)

        self._open_folder_btn = QPushButton("📁  Ordner öffnen")
        self._open_folder_btn.setObjectName("SecondaryBtn")
        self._open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_folder_btn.setFixedHeight(42)
        self._open_folder_btn.clicked.connect(self._open_output_folder)
        self._open_folder_btn.setEnabled(False)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._open_file_btn)
        btn_row.addWidget(self._open_folder_btn)
        layout.addLayout(btn_row)

        # Results table
        section_lbl = QLabel("VERARBEITETE PRODUKTE")
        section_lbl.setObjectName("SectionHeader")
        layout.addWidget(section_lbl)

        self._table = self._build_table()
        layout.addWidget(self._table, 1)

        return content

    def _build_table(self) -> QTableWidget:
        columns = ["Zeile", "Produktbezeichnung", "Hersteller-Nr.", "Status", "Kategorie ID", "Kategorie"]
        tbl = QTableWidget(0, len(columns))
        tbl.setHorizontalHeaderLabels(columns)
        tbl.setAlternatingRowColors(True)
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)

        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(0, 60)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(2, 120)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(3, 100)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(4, 110)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(5, 180)

        tbl.verticalHeader().setDefaultSectionSize(34)
        return tbl

    # ── Event handlers ────────────────────────────────────────────────────

    def _on_file_selected(self, path: str) -> None:
        if not path.lower().endswith(".xlsx"):
            QMessageBox.warning(self, "Falsches Format", "Bitte wählen Sie eine .xlsx-Datei aus.")
            return
        self._in_file  = path
        self._out_file = derive_output_path(path)
        self._drop_zone.show_file(path)
        self._out_path_edit.setText(self._out_file)
        self._start_btn.setEnabled(True)
        self._status_lbl.setText(f"Datei geladen: {Path(path).name}")

    def _on_start(self) -> None:
        if not self._in_file or not os.path.exists(self._in_file):
            QMessageBox.warning(self, "Keine Datei", "Bitte wählen Sie zuerst eine Excel-Datei aus.")
            return
        if self._running:
            return

        # Reset
        self._table.setRowCount(0)
        self._card_total.set_value(0)
        self._card_matched.set_value(0)
        self._card_manual.set_value(0)
        self._card_skipped.set_value(0)
        self._progress.setValue(0)

        self._running = True
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._open_file_btn.setEnabled(False)
        self._open_folder_btn.setEnabled(False)

        self._worker = CategorizerWorker(self._in_file, self._out_file, self._cache)
        self._worker.signals.row.connect(self._on_row)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.status.connect(self._on_status)
        self._worker.signals.finished.connect(self._on_finished)
        self._worker.signals.error.connect(self._on_error)
        self._worker.start()

    def _on_stop(self) -> None:
        if self._worker:
            self._worker.stop()
        self._stop_btn.setEnabled(False)
        self._status_lbl.setText("Wird gestoppt…")

    def _on_row(self, row_num: int, name: str, mpn: str, status: str, cat_id: str, cat_name: str) -> None:
        r = self._table.rowCount()
        self._table.insertRow(r)

        items = [str(row_num), name, mpn, status, cat_id, cat_name]
        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignVCenter
                | (Qt.AlignmentFlag.AlignCenter if col in (0, 3, 4) else Qt.AlignmentFlag.AlignLeft)
            )
            # Status color coding
            if col == 3:
                color = {
                    "Zugeordnet":   self._theme.success,
                    "Manuell":      self._theme.manual,
                    "Übersprungen": self._theme.skip,
                }.get(status, self._theme.text2)
                item.setForeground(QColor(color))
            self._table.setItem(r, col, item)

        self._table.scrollToBottom()

    def _on_progress(self, current: int, total: int, matched: int, manual: int) -> None:
        self._progress.setMaximum(max(total, 1))
        self._progress.setValue(current)
        skipped = current - matched - manual
        self._card_total.set_value(total)
        self._card_matched.set_value(matched)
        self._card_manual.set_value(manual)
        self._card_skipped.set_value(max(skipped, 0))

    def _on_status(self, msg: str) -> None:
        self._status_lbl.setText(msg)
        self._prog_lbl.setText(msg)

    def _on_finished(self, result: dict) -> None:
        self._running = False
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._open_file_btn.setEnabled(True)
        self._open_folder_btn.setEnabled(True)

        t = result["total"]
        m = result["matched"]
        s = result["skipped"]
        mn = result["manual"]
        self._status_lbl.setText(
            f"Fertig! {t} Produkte  •  {m} zugeordnet  •  {mn} manuell  •  {s} übersprungen"
        )
        self._prog_lbl.setText("Verarbeitung abgeschlossen")
        QMessageBox.information(
            self,
            "Abgeschlossen",
            f"Katalog-Verarbeitung erfolgreich abgeschlossen!\n\n"
            f"Produkte gesamt:    {t}\n"
            f"Neu zugeordnet:     {m}\n"
            f"Bereits gefüllt:    {s}\n"
            f"Manuell pflegen:    {mn}\n\n"
            f"Ergebnis gespeichert:\n{result['out_file']}",
        )

    def _on_error(self, msg: str) -> None:
        self._running = False
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_lbl.setText("Fehler aufgetreten.")
        QMessageBox.critical(self, "Verarbeitungsfehler", f"Ein Fehler ist aufgetreten:\n\n{msg}")

    # ── File / folder opening (cross-platform) ────────────────────────────

    def _open_output_file(self) -> None:
        path = self._out_file
        if not os.path.exists(path):
            QMessageBox.warning(self, "Datei nicht gefunden", f"Die Ergebnisdatei wurde nicht gefunden:\n{path}")
            return
        _open_path(path)

    def _open_output_folder(self) -> None:
        path = self._out_file
        folder = str(Path(path).parent) if path else ""
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Ordner nicht gefunden", f"Ordner nicht gefunden:\n{folder}")
            return
        _open_path(folder)

    # ── Theme ─────────────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        self._theme.toggle()
        self._apply_theme()

    def _apply_theme(self) -> None:
        t = self._theme
        QApplication.instance().setStyleSheet(t.app_stylesheet())
        icon = "🌙" if not t.dark else "☀"
        label = "Dunkles Design" if not t.dark else "Helles Design"
        self._header_theme_btn.setText(icon)
        self._theme_btn.setText(f"{icon}  {label}")

        # Re-color status badge items already in the table
        for row in range(self._table.rowCount()):
            status_item = self._table.item(row, 3)
            if status_item:
                status_text = status_item.text()
                color = {
                    "Zugeordnet":   t.success,
                    "Manuell":      t.manual,
                    "Übersprungen": t.skip,
                }.get(status_text, t.text2)
                status_item.setForeground(QColor(color))


# ── Utility ───────────────────────────────────────────────────────────────────

def _open_path(path: str) -> None:
    """Open a file or folder using the native OS mechanism."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as exc:
        print(f"[warn] Could not open {path}: {exc}")
