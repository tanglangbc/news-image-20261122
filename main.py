#!/usr/bin/env python3
"""The World Today - Sunday, 22 November 2026.

Draws a 1024x1024 newspaper front page with only the Python standard
library: a hand-built 5x7 pixel font, integer raster drawing and a small
PNG writer. No image assets, no fonts, no network. Fully deterministic:
the same bytes come out on every run.

Usage:
    MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes entry.png into the output directory (default /output).
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (250, 246, 235)
INK = (18, 18, 18)
RED = (163, 22, 33)
BLUE = (31, 78, 121)
TEAL = (15, 118, 110)
GOLD = (178, 128, 28)
SKY = (122, 165, 198)
DARK = (38, 48, 60)
GREY = (105, 100, 88)
PALE = (221, 233, 241)
ORANGE = (214, 106, 24)
GREEN = (34, 112, 62)

# 5x7 pixel font. Each glyph is seven rows; each row is a five-bit
# number, bit 4 the leftmost pixel.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
}


class Canvas:
    """An RGB pixel buffer with integer drawing primitives."""

    def __init__(self, width, height, color):
        self.w = width
        self.h = height
        self.px = bytearray(width * height * 3)
        self.fill_rect(0, 0, width, height, color)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def hline(self, x, y, length, color):
        for dx in range(max(length, 0)):
            self.set(x + dx, y, color)

    def vline(self, x, y, length, color):
        for dy in range(max(length, 0)):
            self.set(x, y + dy, color)

    def fill_rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            base = (yy * self.w + x) * 3
            for xx in range(max(w, 0)):
                i = base + xx * 3
                if 0 <= x + xx < self.w:
                    self.px[i], self.px[i + 1], self.px[i + 2] = color

    def outline_rect(self, x, y, w, h, color, thick=1):
        for t in range(thick):
            self.hline(x, y + t, w, color)
            self.hline(x, y + h - 1 - t, w, color)
            self.vline(x + t, y, h, color)
            self.vline(x + w - 1 - t, y, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def circle(self, cx, cy, r, color):
        for a in range(360):
            import math
            x = int(cx + r * math.cos(math.radians(a)) + 0.5)
            y = int(cy + r * math.sin(math.radians(a)) + 0.5)
            self.set(x, y, color)

    def fill_triangle(self, p1, p2, p3, color):
        xs = [p1[0], p2[0], p3[0]]
        ys = [p1[1], p2[1], p3[1]]
        for yy in range(min(ys), max(ys) + 1):
            xs_at = []
            for (xa, ya), (xb, yb) in ((p1, p2), (p2, p3), (p3, p1)):
                if ya == yb:
                    continue
                if min(ya, yb) <= yy <= max(ya, yb):
                    xs_at.append(xa + (xb - xa) * (yy - ya) / (yb - ya))
            if len(xs_at) >= 2:
                self.hline(int(min(xs_at)), yy,
                           int(max(xs_at)) - int(min(xs_at)) + 1, color)

    def glyph(self, x, y, char, scale, color):
        rows = FONT.get(char.upper(), FONT[" "])
        for r, bits in enumerate(rows):
            for c in range(5):
                if bits & (1 << (4 - c)):
                    self.fill_rect(x + c * scale, y + r * scale,
                                   scale, scale, color)

    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            self.glyph(cx, y, ch, scale, color)
            cx += 6 * scale
        return cx

    def draw_centered(self, y, text, scale, color):
        self.draw_text((self.w - self.text_width(text, scale)) // 2,
                       y, text, scale, color)

    def wrap(self, text, max_width, scale):
        words = text.split()
        lines = []
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_width(trial, scale) <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def png_chunk(kind, data):
    body = kind + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))


def write_png(path, canvas):
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * canvas.w * 3:(y + 1) * canvas.w * 3]
    data = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) +
            png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            png_chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)

# --- Scenes: small iconic drawings, one per story -----------------------

def draw_storm(cv, x, y, w, h):
    """Deadly storm over a Brazilian town: black clouds, rain, rubble."""
    cv.fill_rect(x, y, w, h, (70, 84, 96))
    cv.disc(x + w // 4, y + h // 4, 52, (28, 32, 40))
    cv.disc(x + w // 2, y + h // 5, 62, (20, 24, 30))
    cv.disc(x + 3 * w // 4, y + h // 4, 48, (28, 32, 40))
    cv.fill_rect(x, y + h // 3, w, h // 6, (48, 54, 64))
    for i in range(14):
        rx = x + 20 + i * 34
        cv.line(rx, y + h // 2, rx - 12, y + h // 2 + 34, (180, 200, 220))
        cv.line(rx + 8, y + h // 2, rx - 4, y + h // 2 + 34, (180, 200, 220))
    # Tilted house and rubble at the bottom.
    cv.fill_rect(x + 40, y + h - 52, 130, 52, (146, 96, 58))
    cv.fill_triangle((x + 30, y + h - 52), (x + 105, y + h - 92),
                     (x + 180, y + h - 52), (90, 52, 36))
    cv.fill_rect(x + w - 200, y + h - 38, 150, 38, (120, 84, 52))
    cv.fill_triangle((x + w - 190, y + h - 38), (x + w - 140, y + h - 66),
                     (x + w - 90, y + h - 38), (96, 60, 40))
    cv.fill_triangle((x + w // 2 - 30, y + h - 20), (x + w // 2 + 10, y + h - 44),
                     (x + w // 2 + 50, y + h - 20), (110, 78, 50))


def draw_chip(cv, x, y, w, h):
    """A chip under scrutiny: green circuit board, black chip, red fall."""
    cv.fill_rect(x, y, w, h, (16, 68, 44))
    for i in range(6):
        cv.hline(x + 16, y + 18 + i * 16, w - 32, (46, 140, 96))
    for i in range(5):
        cv.vline(x + 30 + i * 52, y + 12, h - 24, (46, 140, 96))
    cv.fill_rect(x + w // 2 - 62, y + h // 2 - 46, 124, 92, (12, 12, 12))
    cv.outline_rect(x + w // 2 - 62, y + h // 2 - 46, 124, 92, GOLD, 3)
    for i in range(5):
        cv.hline(x + w // 2 - 74, y + h // 2 - 34 + i * 18, 12, GOLD)
        cv.hline(x + w // 2 + 62, y + h // 2 - 34 + i * 18, 12, GOLD)
    cv.draw_text(x + w // 2 - 42, y + h // 2 - 12, "NVDA", 3, (240, 240, 240))
    cv.line(x + 16, y + 26, x + w // 3, y + 58, RED)
    cv.line(x + w // 3, y + 58, x + w // 2, y + 30, RED)
    cv.line(x + w // 2, y + 30, x + w - 20, y + 86, RED)
    cv.fill_triangle((x + w - 34, y + 72), (x + w - 8, y + 78),
                     (x + w - 30, y + 96), RED)


def draw_card(cv, x, y, w, h):
    """A credit card stamped with a 10 percent cap."""
    cv.fill_rect(x, y, w, h, PALE)
    cv.fill_rect(x + 24, y + h // 2 - 52, 300, 104, BLUE)
    cv.outline_rect(x + 24, y + h // 2 - 52, 300, 104, INK, 2)
    cv.fill_rect(x + 48, y + h // 2 - 36, 44, 30, GOLD)
    cv.hline(x + 48, y + 12, 120, (240, 240, 240))
    cv.draw_text(x + 168, y + h // 2 - 34, "10%", 8, RED)
    cv.draw_text(x + 178, y + h // 2 + 22, "CAP", 4, (255, 255, 255))


def draw_strikes(cv, x, y, w, h):
    """Night strikes over a city skyline: bursts and smoke."""
    cv.fill_rect(x, y, w, h, (16, 20, 34))
    for bx, bh in ((70, 52), (150, 72), (250, 58), (330, 84), (410, 62)):
        cv.fill_rect(x + bx, y + h - bh, 56, bh, (34, 40, 56))
    cv.disc(x + w // 3, y + 46, 26, ORANGE)
    cv.disc(x + w // 3, y + 46, 14, GOLD)
    cv.disc(x + 2 * w // 3, y + 34, 20, ORANGE)
    cv.disc(x + 2 * w // 3, y + 34, 10, (250, 220, 120))
    for dx, dy in ((-40, -18), (38, -22), (-30, 26), (34, 24), (0, -40)):
        cv.line(x + w // 3 + dx // 2, y + 46 + dy // 2,
                x + w // 3 + dx, y + 46 + dy, ORANGE)
    cv.disc(x + w // 2, y + 66, 30, (90, 90, 100))
    cv.disc(x + w // 2 + 26, y + 56, 22, (110, 110, 120))


def draw_quake(cv, x, y, w, h):
    """A 6.7 quake: cracked ground, leaning towers, a seismograph line."""
    cv.fill_rect(x, y, w, h, (232, 222, 200))
    cv.fill_rect(x + 36, y + 8, 70, h - 32, (120, 110, 96))
    cv.fill_rect(x + 130, y + 26, 70, h - 50, (140, 128, 110))
    cv.line(x + 36, y + 8, x + 60, y + 2, (120, 110, 96))
    cv.line(x + 106, y + 8, x + 82, y + 2, (120, 110, 96))
    cv.fill_rect(x, y + h - 24, w, 24, (168, 140, 104))
    px, py = x + 8, y + h - 24
    for dx, dy in ((60, 8), (40, -8), (70, 6), (50, -8), (60, 8), (60, -6)):
        cv.line(px, py, px + dx, py + dy, INK)
        px, py = px + dx, py + dy
    cv.line(x + 16, y + 22, x + w - 16, y + 22, RED)
    for i, up in enumerate((0, 1, 0, 1, 0, 1, 0, 1)):
        x0 = x + 20 + i * 28
        cv.line(x0, y + 22, x0 + 14, y + 22 - (18 if up else 4), RED)
        cv.line(x0 + 14, y + 22 - (18 if up else 4), x0 + 28, y + 22, RED)


# --- Page layout ---------------------------------------------------------

def panel(cv, x, y, w, h, scene, kicker, headline, body, accent,
          head_scale=3):
    cv.outline_rect(x, y, w, h, INK, 2)
    sh = int(h * 0.42)
    scene(cv, x + 2, y + 2, w - 4, sh - 2)
    cv.hline(x, y + sh, w, INK)
    ty = y + sh + 12
    cv.draw_text(x + 14, ty, kicker, 2, accent)
    ty += 24
    for ln in cv.wrap(headline, w - 28, head_scale):
        cv.draw_text(x + 14, ty, ln, head_scale, INK)
        ty += 7 * head_scale + 6
    ty += 2
    for ln in cv.wrap(body, w - 28, 2):
        cv.draw_text(x + 14, ty, ln, 2, (60, 58, 52))
        ty += 7 * 2 + 5


def build_page():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    # Masthead.
    cv.draw_centered(30, "THE WORLD TODAY", 11, INK)
    cv.draw_centered(118, "SUNDAY, 22 NOVEMBER 2026", 3, RED)
    cv.hline(28, 152, 968, INK)
    cv.hline(28, 158, 968, INK)
    # Lead story: Brazil storm, full width.
    lx, ly, lw, lh = 28, 172, 968, 280
    cv.outline_rect(lx, ly, lw, lh, INK, 2)
    draw_storm(cv, lx + 2, ly + 2, 470, lh - 4)
    cv.vline(lx + 474, ly, lh, INK)
    tx = lx + 494
    cv.draw_text(tx, ly + 22, "BRAZIL  -  DEADLY STORM", 2, RED)
    ty = ly + 56
    for ln in cv.wrap("'WE LOST EVERYTHING'", 968 - 494 - 24, 5):
        cv.draw_text(tx, ty, ln, 5, INK)
        ty += 7 * 5 + 8
    ty += 6
    for ln in cv.wrap("A Brazilian town clears the rubble after a "
                      "deadly storm, as residents count what the "
                      "wind and water took.", 968 - 494 - 24, 2):
        cv.draw_text(tx, ty, ln, 2, (60, 58, 52))
        ty += 7 * 2 + 5
    # Second row: Nvidia probe, Trump card cap.
    panel(cv, 28, 466, 476, 252, draw_chip, "TECH  -  MARKETS",
          "NVIDIA FACES US ACCOUNTING PROBE",
          "The chipmaker faces a US accounting probe as turmoil "
          "deepens, media report.", RED)
    panel(cv, 520, 466, 476, 252, draw_card, "USA  -  POLITICS",
          "TRUMP VOWS 10% CAP ON CARD RATES",
          "President Trump says he will work with Democrats to cap "
          "credit card interest at 10 percent.", BLUE)
    # Third row: Houthi strikes, Peru quake.
    panel(cv, 28, 732, 476, 220, draw_strikes, "MIDDLE EAST",
          "HOUTHIS STRIKE SAUDI CAPITAL",
          "Yemen's Houthis say they launched revenge strikes on "
          "the Saudi capital.", RED)
    panel(cv, 520, 732, 476, 220, draw_quake, "PERU  -  EARTHQUAKE",
          "6.7 QUAKE HITS PERU",
          "A 6.7-magnitude earthquake hits Peru. No deaths "
          "reported.", TEAL)
    # Footer: also today, wrapped over two lines.
    cv.hline(28, 968, 968, INK)
    cv.draw_text(28, 980, "ALSO TODAY:", 2, RED)
    fy = 980
    for ln in cv.wrap("Rohingyas hail genocide verdict on Myanmar  -  "
                      "EU proposes tax on Big Tech  -  Alcaraz downs "
                      "Cobolli at the ATP Finals", 968 - 130, 2):
        cv.draw_text(28 + 130, fy, ln, 2, INK)
        fy += 19
    return cv


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    write_png(os.path.join(out, "entry.png"), build_page())


if __name__ == "__main__":
    main()
