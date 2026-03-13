"""
make_icon.py — Generate Clonr app icon.

Design: bold C in accent blue, CD disc nestled inside the C's opening.
Outputs: icon.ico (multi-size for exe) and icon.png (256px for repo).
"""

import math
from PIL import Image, ImageDraw

# ── Palette (matches app theme) ───────────────────────────────────────────────
BG         = (15,  17,  23,  255)   # #0f1117
ACCENT     = (79,  142, 247, 255)   # #4f8ef7
DISC_RING  = (140, 148, 168, 255)   # outer disc edge
DISC_BODY  = (200, 208, 224, 255)   # disc label area
DISC_SHINE = (230, 236, 252, 255)   # highlight
HOLE       = (15,  17,  23,  255)   # center hole = bg


def draw_icon(size: int) -> Image.Image:
    """Render the icon at any square size."""
    SCALE = 4
    S = size * SCALE

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # ── Rounded square background ─────────────────────────────────────────────
    bg_layer = Image.new("RGBA", (S, S), BG)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, S - 1, S - 1], radius=int(S * 0.18), fill=255
    )
    img.paste(bg_layer, mask=mask)
    draw = ImageDraw.Draw(img)

    # ── Shared geometry (used by both disc and C) ─────────────────────────────
    cx      = int(S * 0.43)
    cy      = S // 2
    c_outer = int(S * 0.370)
    c_inner = int(S * 0.248)
    gap     = 62

    # ── Disc (drawn first so C overlaps it, creating a "cradling" effect) ────
    disc_cx = int(cx + c_inner * 0.08)   # nudged left
    disc_cy = cy
    disc_r  = int(c_inner * 0.88)        # 30% bigger than before

    # Outer silver ring
    draw.ellipse(
        [disc_cx - disc_r, disc_cy - disc_r,
         disc_cx + disc_r, disc_cy + disc_r],
        fill=DISC_RING
    )
    # Label area
    label_r = int(disc_r * 0.70)
    draw.ellipse(
        [disc_cx - label_r, disc_cy - label_r,
         disc_cx + label_r, disc_cy + label_r],
        fill=DISC_BODY
    )
    # Highlight
    shine_r = int(disc_r * 0.42)
    draw.ellipse(
        [disc_cx - shine_r, disc_cy - shine_r,
         disc_cx + shine_r, disc_cy + shine_r],
        fill=DISC_SHINE
    )
    # Center hole
    hole_r = int(disc_r * 0.15)
    draw.ellipse(
        [disc_cx - hole_r, disc_cy - hole_r,
         disc_cx + hole_r, disc_cy + hole_r],
        fill=HOLE
    )

    # ── C ring ────────────────────────────────────────────────────────────────
    # Build polygon: outer arc CW then inner arc CCW (standard math angles)
    outer_pts, inner_pts = [], []
    for a in range(gap, 360 - gap + 1):
        r = math.radians(a)
        outer_pts.append((cx + c_outer * math.cos(r), cy + c_outer * math.sin(r)))
    for a in range(360 - gap, gap - 1, -1):
        r = math.radians(a)
        inner_pts.append((cx + c_inner * math.cos(r), cy + c_inner * math.sin(r)))

    draw.polygon(outer_pts + inner_pts, fill=ACCENT)

    # Rounded end-caps on the C tips
    mid_r = (c_outer + c_inner) / 2
    cap_r = (c_outer - c_inner) / 2
    for a in [gap, 360 - gap]:
        rad = math.radians(a)
        ex = cx + mid_r * math.cos(rad)
        ey = cy + mid_r * math.sin(rad)
        draw.ellipse([ex - cap_r, ey - cap_r, ex + cap_r, ey + cap_r], fill=ACCENT)

    # ── Scale down (anti-alias) ───────────────────────────────────────────────
    return img.resize((size, size), Image.LANCZOS)


def main():
    sizes = [16, 32, 48, 64, 128, 256]
    frames = [draw_icon(s) for s in sizes]

    # .ico — multi-size for Windows exe
    ico_path = "assets/icon.ico"
    frames[-1].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[:-1],
    )
    print(f"  Wrote {ico_path}")

    # .png — 256px for README / GitHub
    png_path = "assets/icon.png"
    frames[-1].save(png_path, format="PNG")
    print(f"  Wrote {png_path}")


if __name__ == "__main__":
    main()
