"""
style.py — All colors, fonts, and QSS for Clonr.

One place to change the look. Nothing else imports colors directly.
"""

# ── Palette ───────────────────────────────────────────────────────────────────

BG          = "#0f1117"
BG_CARD     = "#1a1d27"
BG_CARD_HVR = "#22263a"
BG_MODAL    = "#1a1d27"
BORDER      = "#2a2d3e"
ACCENT      = "#4f8ef7"
ACCENT_HVR  = "#6ba3ff"
DANGER      = "#e05c5c"
DANGER_HVR  = "#f07070"
TEXT        = "#e8eaf0"
TEXT_DIM    = "#6b7280"
TEXT_WARN   = "#f5a623"


# ── Stylesheet ────────────────────────────────────────────────────────────────

STYLESHEET = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 13px;
}}

/* ── Disk cards ── */
#DiskCard {{
    background-color: {BG_CARD};
    border: 2px solid {BORDER};
    border-radius: 10px;
}}
#DiskCard:hover {{
    background-color: {BG_CARD_HVR};
    border-color: {ACCENT};
}}
#DiskCard[selected="true"] {{
    border-color: {ACCENT};
}}
#DiskCard[empty="true"] {{
    border: 2px dashed {BORDER};
}}
#DiskCard[empty="true"]:hover {{
    border-color: {ACCENT};
}}

/* ── Buttons ── */
#BtnClone {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    padding: 14px 0px;
}}
#BtnClone:hover {{
    background-color: {ACCENT_HVR};
}}
#BtnClone:disabled {{
    background-color: {BORDER};
    color: {TEXT_DIM};
}}
#BtnCancel {{
    background-color: transparent;
    color: {TEXT_DIM};
    border: 2px solid {BORDER};
    border-radius: 8px;
    font-size: 13px;
    padding: 10px 28px;
}}
#BtnCancel:hover {{
    color: {TEXT};
    border-color: {TEXT_DIM};
}}
#BtnConfirm {{
    background-color: {DANGER};
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 28px;
}}
#BtnConfirm:hover {{
    background-color: {DANGER_HVR};
}}

/* ── Progress bar ── */
QProgressBar {{
    background-color: {BG_CARD};
    border: none;
    border-radius: 6px;
    height: 10px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 6px;
}}

/* ── Disk picker list ── */
QListWidget {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    outline: none;
}}
QListWidget::item {{
    padding: 10px 14px;
    border-radius: 6px;
}}
QListWidget::item:selected {{
    background-color: {ACCENT};
    color: white;
}}
QListWidget::item:hover:!selected {{
    background-color: {BG_CARD_HVR};
}}

/* ── Modal overlay ── */
#ModalOverlay {{
    background-color: rgba(0, 0, 0, 180);
}}
#ModalBox {{
    background-color: {BG_MODAL};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}

/* ── Labels ── */
#LabelTitle {{
    font-size: 22px;
    font-weight: 700;
    color: {TEXT};
    letter-spacing: 2px;
}}
#LabelSection {{
    font-size: 11px;
    font-weight: 600;
    color: {TEXT_DIM};
    letter-spacing: 1.5px;
}}
#LabelWarn {{
    color: {TEXT_WARN};
    font-size: 12px;
}}
#LabelDanger {{
    color: {DANGER};
    font-size: 13px;
    font-weight: 600;
}}
#LabelDim {{
    color: {TEXT_DIM};
    font-size: 12px;
}}
"""
