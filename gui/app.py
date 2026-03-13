"""
app.py — Main Clonr window.

Layout:
  Header     — logo
  Panels     — FROM card  arrow  TO card
  Progress   — bar + stats (hidden until cloning)
  Footer     — START CLONE button
"""

import time
import traceback
from typing import Callable
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QProgressBar, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from clonr import disk as disk_mod
from clonr.disk import DiskInfo
from clonr.constants import ETA_CAP_SECONDS
from gui.widgets import DiskCard, DiskPicker, ConfirmModal
from gui.style import STYLESHEET, TEXT_DIM


# ── Clone worker (runs in background thread) ──────────────────────────────────

class CloneWorker(QObject):
    progress = pyqtSignal(int, int)    # bytes_done, total
    finished = pyqtSignal()
    error    = pyqtSignal(str)

    def __init__(self, src: int, dst: int):
        super().__init__()
        self._src = src
        self._dst = dst

    def run(self) -> None:
        try:
            disk_mod.clone(self._src, self._dst, progress_cb=self.progress.emit)
            self.finished.emit()
        except (OSError, ValueError) as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Unexpected error: {traceback.format_exc()}")


# ── Main window ───────────────────────────────────────────────────────────────

class ClonrWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clonr")
        self.setMinimumSize(620, 520)
        self.setStyleSheet(STYLESHEET)

        self._disks:  list[DiskInfo] = []
        self._src:    DiskInfo | None = None
        self._dst:    DiskInfo | None = None
        self._thread: QThread | None = None
        self._worker: CloneWorker | None = None
        self._start:  float = 0.0

        self._build_ui()
        self._load_disks()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(0)

        layout.addLayout(self._build_header())
        layout.addSpacing(36)
        layout.addLayout(self._build_panels())
        layout.addSpacing(12)
        layout.addWidget(self._build_warning())
        layout.addSpacing(24)
        layout.addWidget(self._build_progress())
        layout.addSpacing(28)
        layout.addWidget(self._build_clone_btn())

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        title = QLabel("CLONR")
        title.setObjectName("LabelTitle")
        row.addWidget(title)
        row.addStretch()
        return row

    def _build_panels(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(0)

        # FROM
        src_col = QVBoxLayout()
        src_col.setSpacing(10)
        src_lbl = QLabel("FROM")
        src_lbl.setObjectName("LabelSection")
        self._card_src = DiskCard()
        self._card_src.clicked.connect(self._pick_src)
        src_col.addWidget(src_lbl)
        src_col.addWidget(self._card_src)

        # Arrow
        arrow = QLabel("->")
        arrow.setFont(QFont("Segoe UI", 28))
        arrow.setStyleSheet(f"color: {TEXT_DIM};")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # TO
        dst_col = QVBoxLayout()
        dst_col.setSpacing(10)
        dst_lbl = QLabel("TO")
        dst_lbl.setObjectName("LabelSection")
        self._card_dst = DiskCard()
        self._card_dst.clicked.connect(self._pick_dst)
        dst_col.addWidget(dst_lbl)
        dst_col.addWidget(self._card_dst)

        row.addLayout(src_col)
        row.addStretch()
        row.addWidget(arrow)
        row.addStretch()
        row.addLayout(dst_col)
        return row

    def _build_warning(self) -> QLabel:
        self._warn = QLabel("")
        self._warn.setObjectName("LabelWarn")
        self._warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._warn.hide()
        return self._warn

    def _build_progress(self) -> QWidget:
        container = QWidget()
        col = QVBoxLayout(container)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(8)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(10)

        self._progress_stats = QLabel("")
        self._progress_stats.setObjectName("LabelDim")
        self._progress_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)

        col.addWidget(self._progress_bar)
        col.addWidget(self._progress_stats)

        self._progress_container = container
        container.hide()
        return container

    def _build_clone_btn(self) -> QPushButton:
        self._btn_clone = QPushButton("START CLONE")
        self._btn_clone.setObjectName("BtnClone")
        self._btn_clone.setFixedHeight(52)
        self._btn_clone.setEnabled(False)
        self._btn_clone.clicked.connect(self._on_clone_clicked)
        return self._btn_clone

    # ── Disk loading ──────────────────────────────────────────────────────────

    def _load_disks(self) -> None:
        self._disks = disk_mod.list_disks()

    # ── Disk selection ────────────────────────────────────────────────────────

    def _pick_src(self) -> None:
        if self._is_cloning():
            return
        self._show_picker(exclude=self._dst, callback=self._on_src_chosen)

    def _pick_dst(self) -> None:
        if self._is_cloning():
            return
        self._show_picker(exclude=self._src, callback=self._on_dst_chosen)

    def _show_picker(self, exclude: DiskInfo | None,
                     callback: Callable[[DiskInfo], None]) -> None:
        overlay = DiskPicker(self._disks, exclude=exclude, parent=self.centralWidget())
        overlay.setGeometry(self.centralWidget().rect())
        overlay.disk_chosen.connect(lambda d: (callback(d), overlay.deleteLater()))
        overlay.cancelled.connect(overlay.deleteLater)
        overlay.show()
        overlay.raise_()

    def _on_src_chosen(self, info: DiskInfo) -> None:
        self._src = info
        self._card_src.set_disk(info)
        self._refresh_state()

    def _on_dst_chosen(self, info: DiskInfo) -> None:
        self._dst = info
        self._card_dst.set_disk(info)
        self._refresh_state()

    # ── State management ──────────────────────────────────────────────────────

    def _refresh_state(self) -> None:
        ready = self._src is not None and self._dst is not None
        self._btn_clone.setEnabled(ready)

        if ready and self._dst.size_bytes < self._src.size_bytes:
            self._warn.setText(
                f"Warning: destination is smaller than source "
                f"({self._dst.size_gb:.1f} GB < {self._src.size_gb:.1f} GB)"
            )
            self._warn.show()
            self._btn_clone.setEnabled(False)
        elif ready:
            self._warn.setText(f"All data on {self._dst.friendly_name} will be erased.")
            self._warn.show()
        else:
            self._warn.hide()

    def _is_cloning(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    # ── Clone flow ────────────────────────────────────────────────────────────

    def _on_clone_clicked(self) -> None:
        if not self._src or not self._dst:
            return
        self._show_confirm()

    def _show_confirm(self) -> None:
        overlay = ConfirmModal(self._dst, parent=self.centralWidget())
        overlay.setGeometry(self.centralWidget().rect())
        overlay.confirmed.connect(lambda: (overlay.deleteLater(), self._start_clone()))
        overlay.cancelled.connect(overlay.deleteLater)
        overlay.show()
        overlay.raise_()

    def _start_clone(self) -> None:
        self._btn_clone.setEnabled(False)
        self._btn_clone.setText("Cloning...")
        self._progress_container.show()
        self._progress_bar.setValue(0)
        self._progress_stats.setText("Starting...")
        self._start = time.monotonic()

        self._worker = CloneWorker(self._src.number, self._dst.number)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.start()

    def _cleanup_thread(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
        if self._worker is not None:
            self._worker.deleteLater()
        self._thread = None
        self._worker = None

    def _on_progress(self, done: int, total: int) -> None:
        pct     = int(done / total * 100)
        elapsed = time.monotonic() - self._start
        speed   = done / elapsed if elapsed > 0 else 0
        if done >= total:
            eta_str = "finishing..."
        elif speed > 0:
            eta_secs = (total - done) / speed
            eta_str  = f"{int(eta_secs)}s remaining" if eta_secs <= ETA_CAP_SECONDS else "calculating..."
        else:
            eta_str  = "calculating..."
        self._progress_bar.setValue(pct)
        self._progress_stats.setText(
            f"{done / 1e9:.2f} / {total / 1e9:.2f} GB  ·  "
            f"{speed / 1e6:.1f} MB/s  ·  "
            f"{eta_str}"
        )

    def _on_done(self) -> None:
        self._progress_bar.setValue(100)
        self._progress_stats.setText("Clone complete.")
        self._btn_clone.setText("Done")

    def _on_error(self, msg: str) -> None:
        self._warn.setText(f"Error: {msg}")
        self._warn.show()
        self._btn_clone.setEnabled(True)
        self._btn_clone.setText("START CLONE")

    # ── Window lifecycle ──────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        if self._is_cloning():
            self._thread.quit()
            if not self._thread.wait(5000):   # 5-second timeout — don't hang forever
                self._thread.terminate()
        super().closeEvent(event)
