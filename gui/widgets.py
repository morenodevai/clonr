"""
widgets.py — Reusable UI components.

  DiskCard       — Clickable card showing a disk or an empty slot
  DiskPicker     — Modal overlay for selecting a disk
  ConfirmModal   — "Are you sure?" overlay before cloning
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from clonr.disk import DiskInfo
from gui.style import TEXT_DIM, ACCENT


# ── DiskCard ──────────────────────────────────────────────────────────────────

class DiskCard(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DiskCard")
        self.setFixedSize(220, 140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._disk: DiskInfo | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)

        self._icon  = QLabel("💽")
        self._icon.setFont(QFont("Segoe UI", 26))
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._name  = QLabel("Click to select")
        self._name.setObjectName("LabelDim")
        self._name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name.setWordWrap(True)

        self._size  = QLabel("")
        self._size.setObjectName("LabelDim")
        self._size.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._icon)
        layout.addWidget(self._name)
        layout.addWidget(self._size)

        self.setProperty("empty", True)
        self.setProperty("selected", False)

    def set_disk(self, info: DiskInfo | None) -> None:
        self._disk = info
        if info:
            self._icon.setText("💽")
            self._name.setText(info.friendly_name)
            self._size.setText(f"{info.size_gb:.1f} GB  ·  Disk {info.number}")
            self._name.setObjectName("")
        else:
            self._icon.setText("➕")
            self._name.setText("Click to select")
            self._name.setObjectName("LabelDim")
            self._size.setText("")

        # Update CSS properties then re-polish once — let the stylesheet do the rest
        self.setProperty("empty", info is None)
        self.setProperty("selected", info is not None)
        for widget in (self, self._name):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    @property
    def disk(self) -> DiskInfo | None:
        return self._disk

    def mousePressEvent(self, _event):
        self.clicked.emit()


# ── DiskPicker ────────────────────────────────────────────────────────────────

class DiskPicker(QWidget):
    """Full-window overlay listing available disks to pick from."""

    disk_chosen = pyqtSignal(object)   # emits DiskInfo
    cancelled   = pyqtSignal()

    def __init__(self, disks: list[DiskInfo], exclude: DiskInfo | None, parent=None):
        super().__init__(parent)
        self.setObjectName("ModalOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        box = QFrame()
        box.setObjectName("ModalBox")
        box.setFixedSize(360, 360)
        inner = QVBoxLayout(box)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(14)

        title = QLabel("SELECT DISK")
        title.setObjectName("LabelSection")
        inner.addWidget(title)

        self._list = QListWidget()
        self._list.setSpacing(2)
        for d in disks:
            if exclude and d.number == exclude.number:
                continue
            item = QListWidgetItem(f"  Disk {d.number}  —  {d.friendly_name}  ({d.size_gb:.1f} GB)")
            item.setData(Qt.ItemDataRole.UserRole, d)
            self._list.addItem(item)
        self._list.itemDoubleClicked.connect(self._on_double_click)
        inner.addWidget(self._list)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("BtnCancel")
        cancel.clicked.connect(self.cancelled.emit)
        select = QPushButton("Select")
        select.setObjectName("BtnConfirm")
        select.setStyleSheet(f"background-color: {ACCENT};")
        select.clicked.connect(self._on_select)
        btns.addWidget(cancel)
        btns.addWidget(select)
        inner.addLayout(btns)

        outer.addWidget(box)

    def _on_double_click(self, item: QListWidgetItem):
        self.disk_chosen.emit(item.data(Qt.ItemDataRole.UserRole))

    def _on_select(self):
        items = self._list.selectedItems()
        if items:
            self.disk_chosen.emit(items[0].data(Qt.ItemDataRole.UserRole))


# ── ConfirmModal ──────────────────────────────────────────────────────────────

class ConfirmModal(QWidget):
    """'Are you sure?' overlay. Emits confirmed or cancelled."""

    confirmed = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, dst: DiskInfo, parent=None):
        super().__init__(parent)
        self.setObjectName("ModalOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        box = QFrame()
        box.setObjectName("ModalBox")
        box.setFixedWidth(380)
        inner = QVBoxLayout(box)
        inner.setContentsMargins(32, 32, 32, 32)
        inner.setSpacing(14)

        title = QLabel("Are you sure?")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        inner.addWidget(title)

        inner.addWidget(QLabel("You are about to overwrite:"))

        disk_label = QLabel(f"  {dst.friendly_name}  —  {dst.size_gb:.1f} GB")
        disk_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        disk_label.setStyleSheet(f"color: white; background: #2a2d3e; border-radius: 6px; padding: 10px;")
        inner.addWidget(disk_label)

        warning = QLabel("This cannot be undone.\nAll data on this disk will be permanently lost.")
        warning.setObjectName("LabelDanger")
        warning.setWordWrap(True)
        inner.addWidget(warning)

        inner.addSpacing(8)

        btns = QHBoxLayout()
        btns.setSpacing(12)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("BtnCancel")
        cancel.setFixedHeight(42)
        cancel.clicked.connect(self.cancelled.emit)
        confirm = QPushButton("Yes, clone it")
        confirm.setObjectName("BtnConfirm")
        confirm.setFixedHeight(42)
        confirm.clicked.connect(self.confirmed.emit)
        btns.addWidget(cancel)
        btns.addWidget(confirm)
        inner.addLayout(btns)

        outer.addWidget(box)
