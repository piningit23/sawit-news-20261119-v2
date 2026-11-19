#!/usr/bin/env python3
"""THE WORLD TODAY - v2: a dense broadsheet front page for 19 Nov 2026.

Draws a 1024x1024 newspaper front page summing up the world news of
Thursday 19 November 2026 (stories reported 18-19 Nov 2026): 42 verified
stories, a world map with one numbered dot per story, and a numbered
briefs index. Writes exactly one PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output).

Pure Python 3.13 standard library. No network, no randomness, no time:
two runs produce byte-identical output. The 5x7 pixel font, the PNG
encoder, the map and every illustration were written for this entry.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)
INK = (24, 24, 30)
RED = (178, 34, 34)
BLUE = (28, 58, 112)
NAVY = (16, 26, 54)
GOLD = (214, 164, 32)
TEAL = (18, 110, 105)
SKY = (140, 190, 220)
NIGHT = (14, 18, 44)
NEON = (255, 64, 170)
ORANGE = (232, 110, 24)
GREEN = (34, 120, 60)
GREY = (110, 108, 100)
LIGHT = (228, 222, 208)
WHITE = (255, 255, 255)
BLACK = (8, 8, 12)
YELLOW = (240, 210, 60)
SAND = (226, 205, 160)
MAPLAND = (198, 206, 212)
MAPLINE = (140, 148, 156)
CAPTION = (64, 62, 58)

# ------------------------------------------------------------------ image
PIX = bytearray(bytes(PAPER) * (W * H))
CLIP = None


def px(x, y, c):
    if CLIP is not None:
        if not (CLIP[0] <= x <= CLIP[2] and CLIP[1] <= y <= CLIP[3]):
            return
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i], PIX[i + 1], PIX[i + 2] = c


def rect(x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px(xx, yy, c)


def frame(x, y, w, h, c, t=2):
    rect(x, y, w, t, c)
    rect(x, y + h - t, w, t, c)
    rect(x, y, t, h, c)
    rect(x + w - t, y, t, h, c)


def hline(x0, x1, y, c, t=1):
    for yy in range(y, y + t):
        for xx in range(x0, x1 + 1):
            px(xx, yy, c)


def vline(x, y0, y1, c, t=1):
    for xx in range(x, x + t):
        for yy in range(y0, y1 + 1):
            px(xx, yy, c)


def line(x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                px(xx, yy, c)


def ring(cx, cy, r, c, t=2):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d = (xx - cx) ** 2 + (yy - cy) ** 2
            if (r - t) ** 2 <= d <= r * r:
                px(xx, yy, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
    for yy in range(ymin, ymax + 1):
        xs = []
        for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2), (x2, y2, x0, y0)):
            if ay == by:
                continue
            if min(ay, by) <= yy <= max(ay, by):
                xs.append(ax + (bx - ax) * (yy - ay) / (by - ay))
        if len(xs) >= 2:
            for xx in range(int(min(xs)), int(max(xs)) + 1):
                px(xx, yy, c)


def poly(points, c):
    """Fill a polygon given as a list of (x, y) points."""
    if len(points) < 3:
        return
    ymin = min(p[1] for p in points)
    ymax = max(p[1] for p in points)
    n = len(points)
    for yy in range(ymin, ymax + 1):
        xs = []
        for i in range(n):
            ax, ay = points[i]
            bx, by = points[(i + 1) % n]
            if ay == by:
                continue
            if min(ay, by) <= yy < max(ay, by):
                xs.append(ax + (bx - ax) * (yy - ay) / (by - ay))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for xx in range(int(xs[i]), int(xs[i + 1]) + 1):
                px(xx, yy, c)


# ------------------------------------------------------------- 5x7 font
G = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
}

CW = 6


def text_w(s, scale):
    return (len(s) * CW - 1) * scale


def draw_text(x, y, s, scale, c):
    s = s.upper()
    cx = x
    for ch in s:
        g = G.get(ch, G[' '])
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == '1':
                    rect(cx + col * scale, y + r * scale, scale, scale, c)
        cx += CW * scale
    return cx


def draw_centred(cx, y, s, scale, c):
    draw_text(cx - text_w(s, scale) // 2, y, s, scale, c)


def wrap(s, scale, maxw):
    words = s.upper().split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, scale) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------ illustrations
def art_gta(x, y, w, h):
    rect(x, y, w, h, NIGHT)
    disc(x + w // 2, y + h - 26, 34, ORANGE)
    disc(x + w // 2, y + h - 26, 26, YELLOW)
    base = y + h - 26
    towers = [(0, 52, 44), (46, 78, 38), (86, 60, 46), (134, 92, 40),
              (176, 66, 44), (222, 84, 38), (262, 58, 46), (308, 76, 42),
              (352, 62, 44), (398, 88, 38), (442, 70, 46), (488, 80, 40)]
    for dx, th, tw in towers:
        tx = x + dx
        rect(tx, base - th, tw, th, (26, 30, 66))
        for wy in range(base - th + 6, base - 6, 12):
            for wx in range(tx + 5, tx + tw - 5, 11):
                if (wx * 7 + wy * 3) % 5 == 0:
                    rect(wx, wy, 4, 5, GOLD)
    rect(x, base - 8, w, 8, NEON)
    for px0 in (x + 30, x + w - 46):
        line(px0, base, px0 + 8, base - 34, GREEN)
        for a in (-22, -10, 2, 14):
            line(px0 + 8, base - 34, px0 + 8 + a, base - 44, GREEN)
    cx0 = x + w // 2 - 46
    rect(cx0, base - 22, 92, 16, RED)
    rect(cx0 + 18, base - 34, 52, 14, RED)
    rect(cx0 + 24, base - 32, 40, 10, SKY)
    disc(cx0 + 20, base - 4, 8, BLACK)
    disc(cx0 + 72, base - 4, 8, BLACK)
    disc(cx0 + 20, base - 4, 3, GREY)
    disc(cx0 + 72, base - 4, 3, GREY)
    draw_text(x + w - 92, y + 8, "VI", 6, WHITE)
    draw_text(x + 10, y + 8, "GTA", 4, NEON)


def art_summit(x, y, w, h):
    rect(x, y, w, h, SKY)
    base = y + h
    for dx, th, tw in [(8, 22, 30), (44, 30, 26), (76, 20, 30), (112, 26, 26),
                       (144, 20, 30), (180, 28, 26), (212, 22, 30), (248, 26, 26),
                       (284, 20, 30), (316, 24, 26)]:
        rect(x + dx, base - th, tw, th, BLUE)
    rect(x + 30, base - 16, w - 60, 6, (120, 72, 40))
    for i, c in enumerate((RED, GOLD, BLUE)):
        fx = x + 60 + i * 96
        rect(fx, base - 34, 30, 18, c)
        disc(fx + 15, base - 40, 10, (238, 205, 170))
    rect(x + 8, y + 4, 34, 14, WHITE)
    rect(x + 8, y + 4, 34, 5, (180, 30, 30))
    rect(x + 8, y + 13, 34, 5, (180, 30, 30))
    rect(x + w - 42, y + 4, 34, 14, RED)
    disc(x + w - 34, y + 9, 3, GOLD)


def art_court(x, y, w, h):
    rect(x, y, w, h, (226, 228, 236))
    base = y + h - 4
    # courthouse: steps, columns, pediment
    rect(x + 10, base - 6, w - 20, 6, GREY)
    tri(x + w // 2 - 70, y + 12, x + w // 2 + 70, y + 12, x + w // 2, y + 2, BLUE)
    for i in range(5):
        cx = x + 26 + i * 36
        rect(cx, y + 14, 10, base - 20, WHITE)
        rect(cx - 2, y + 12, 14, 4, INK)
        rect(cx - 2, base - 10, 14, 4, INK)
    rect(x + w // 2 - 12, base - 22, 24, 12, INK)


def art_bridge(x, y, w, h):
    rect(x, y, w, h, (210, 226, 238))
    base = y + h - 22
    rect(x, base, w, 8, GREY)
    for tx in (x + 40, x + w // 2 - 4, x + w - 48):
        rect(tx, y + 8, 8, base - y - 8, INK)
        line(tx + 4, y + 8, x + 10, base, RED)
        line(tx + 4, y + 8, x + w - 10, base, RED)
    # broken span
    rect(x + w // 2 - 30, base - 2, 60, 6, (240, 240, 240))
    tri(x + w // 2 - 30, base, x + w // 2 - 6, base + 12, x + w // 2 - 34, base + 12, GREY)
    disc(x + w // 2 + 24, y + 14, 7, ORANGE)
    disc(x + w // 2 + 24, y + 14, 3, YELLOW)


def art_tower(x, y, w, h):
    rect(x, y, w, h, (200, 215, 235))
    base = y + h
    rect(x + w // 2 - 26, y + 8, 52, h - 8, (60, 80, 120))
    for wy in range(y + 14, base - 8, 12):
        for wx in range(x + w // 2 - 20, x + w // 2 + 20, 12):
            rect(wx, wy, 7, 7, (200, 220, 240))
    # damage: blown-out windows + smoke
    for wy in range(y + 26, y + 62, 12):
        rect(x + w // 2 - 20, wy, 7, 7, ORANGE)
        rect(x + w // 2 + 13, wy, 7, 7, ORANGE)
    disc(x + w // 2 - 34, y + 12, 8, GREY)
    disc(x + w // 2 - 44, y + 6, 6, GREY)
    disc(x + w // 2 + 40, y + 18, 7, GREY)


def art_climate(x, y, w, h):
    rect(x, y, w, h, (214, 232, 214))
    disc(x + 30, y + 18, 12, GOLD)
    for a in range(0, 360, 45):
        ex = int(30 + 20 * math.cos(a * math.pi / 180))
        ey = int(18 + 20 * math.sin(a * math.pi / 180))
        line(x + 30, y + 18, x + ex, y + ey, GOLD)
    # globe
    disc(x + w - 52, y + h // 2 + 4, 26, BLUE)
    rect(x + w - 66, y + h // 2 - 8, 28, 10, GREEN)
    rect(x + w - 52, y + h // 2 + 8, 22, 8, GREEN)
    ring(x + w - 52, y + h // 2 + 4, 26, TEAL, 2)
    # delegates row
    for i in range(5):
        fx = x + 14 + i * 30
        disc(fx + 8, y + h - 26, 7, (238, 205, 170))
        rect(fx, y + h - 18, 16, 14, (RED if i % 2 else BLUE))


def art_fire(x, y, w, h):
    rect(x, y, w, h, (250, 228, 200))
    base = y + h
    # houses
    for i, bx in enumerate((x + 12, x + 76, x + 140)):
        rect(bx, base - 30, 52, 30, (200, 180, 140) if i != 1 else (170, 60, 40))
        tri(bx - 4, base - 30, bx + 26, base - 46, bx + 56, base - 30,
            (120, 70, 40) if i != 1 else (90, 30, 20))
    # flames on middle house
    tri(x + 92, base - 46, x + 102, base - 74, x + 112, base - 46, ORANGE)
    tri(x + 96, base - 46, x + 102, base - 64, x + 108, base - 46, YELLOW)
    disc(x + 200, y + 12, 9, GREY)
    disc(x + 214, y + 8, 7, GREY)
    disc(x + 188, y + 8, 6, GREY)


def art_berlin(x, y, w, h):
    rect(x, y, w, h, (226, 232, 244))
    base = y + h
    rect(x + 24, base - 44, 120, 30, WHITE)
    for i in range(5):
        rect(x + 32 + i * 22, base - 38, 10, 24, BLUE)
    tri(x + 24, base - 44, x + 84, base - 56, x + 144, base - 44, RED)
    line(x + w - 34, y + 8, x + w - 34, base - 12, INK)
    rect(x + w - 34, y + 8, 30, 18, BLUE)
    disc(x + w - 26, y + 17, 4, GOLD)
    for i in range(4):
        disc(x + 170 + i * 12, base - 20, 4, (238, 205, 170))
        rect(x + 164 + i * 12, base - 14, 12, 12, (RED if i % 2 else NAVY))


def art_ice(x, y, w, h):
    rect(x, y, w, h, (205, 225, 240))
    base = y + h
    rect(x, base - 18, w, 18, (240, 246, 250))
    # icebergs
    tri(x + 20, base - 18, x + 44, base - 52, x + 68, base - 18, WHITE)
    tri(x + 90, base - 18, x + 118, base - 62, x + 146, base - 18, WHITE)
    tri(x + 160, base - 18, x + 182, base - 44, x + 204, base - 18, WHITE)
    # vote tally
    draw_text(x + 8, y + 4, "109-0", 4, BLUE)


def art_painting(x, y, w, h):
    rect(x, y, w, h, (240, 232, 214))
    frame(x + 8, y + 6, w - 16, h - 12, GOLD, 4)
    rect(x + 12, y + 10, w - 24, h - 20, SKY)
    disc(x + w - 40, y + 22, 12, YELLOW)
    # chestnut tree
    rect(x + w // 2 - 4, y + h - 34, 8, 24, (90, 60, 30))
    disc(x + w // 2, y + h - 52, 26, GREEN)
    disc(x + w // 2 - 22, y + h - 40, 16, GREEN)
    disc(x + w // 2 + 22, y + h - 40, 16, GREEN)
    disc(x + w // 2 - 10, y + h - 58, 6, WHITE)
    disc(x + w // 2 + 12, y + h - 48, 6, WHITE)
    disc(x + w // 2 - 24, y + h - 52, 5, WHITE)


def art_handshake(x, y, w, h):
    rect(x, y, w, h, (232, 226, 210))
    base = y + h
    # two flags
    rect(x + 12, y + 8, 56, 32, WHITE)
    for r in range(3):
        rect(x + 12, y + 8 + r * 11, 56, 5, (180, 30, 30) if r % 2 == 0 else WHITE)
    rect(x + 12, y + 8, 24, 17, BLUE)
    rect(x + w - 68, y + 8, 56, 32, (230, 200, 40))
    rect(x + w - 68, y + 18, 56, 11, (30, 60, 140))
    rect(x + w - 68, y + 29, 56, 11, (200, 40, 40))
    # hands meeting
    rect(x + w // 2 - 52, base - 34, 104, 16, (238, 205, 170))
    rect(x + w // 2 - 52, base - 34, 16, 16, (30, 60, 140))
    rect(x + w // 2 + 36, base - 34, 16, 16, (180, 30, 30))
    disc(x + w // 2, base - 42, 8, GOLD)


# ------------------------------------------------------------- story data
# (num, kicker, headline, caption, art, lon, lat, label dx, label dy)
PANELS = [
    (21, "UKRAINE - RUSSIA", "KERCH BRIDGE HIT A THIRD TIME",
     "RAIL TRAFFIC HALTS", art_bridge, 36, 45, 7, -3),
    (22, "MIDDLE EAST - RIYADH", "MISSILE DAMAGES RIYADH PIF TOWER",
     "WINDOWS BLOWN OUT", art_tower, 47, 25, 7, 6),
    (23, "CLIMATE - ANTALYA", "COP31 MINISTERS RACE TO UNBLOCK TALKS",
     "DELEGATES SPLIT", art_climate, 31, 37, -16, -3),
    (24, "ASIA - BANGLADESH", "BANGLADESH LOCKDOWN TURNS VIOLENT",
     "YUNUS HOME TORCHED", art_fire, 90, 24, 7, -3),
    (25, "EUROPE - BERLIN", "ALLIES MEET IN BERLIN FOR UKRAINE",
     "ALLIES BACK KYIV", art_berlin, 13, 52, 7, -3),
    (26, "ARCTIC - GREENLAND", "DENMARK RATIFIES GREENLAND DEAL",
     "VOTE ENDS STANDOFF", art_ice, 12, 56, 7, -3),
    (30, "CULTURE - ART", "VAN GOGH SELLS FOR RECORD $190.4M",
     "1890 WORK TOPS SALE", art_painting, -74, 41, -16, -4),
    (42, "SOUTH AMERICA", "US AND VENEZUELA SIGN MILITARY DEAL",
     "HEGSETH IN CARACAS", art_handshake, -67, 10, 7, -3),
]

# (num, lon, lat, label dx, label dy) for every story, in number order
DOTS = [
    (1, -80, 26, 7, -3), (2, 114, 22, 7, -3), (3, -95, 29, -16, -3),
    (4, 48, 29, 8, -6), (5, 4, 51, -59, -12), (6, 34, 31, 10, 6),
    (7, -74, 41, 14, -10), (8, 149, -35, 7, -3), (9, 28, 43, 10, 8),
    (10, -150, 64, 7, -3), (11, -98, 39, 7, -8), (12, 8, 50, -70, 35),
    (13, -77, 39, -30, -10), (14, -77, 38, 14, 10), (15, 13, 38, 24, 26),
    (16, 10, 60, 33, 20), (17, 80, 16, -18, 4), (18, -122, 37, -16, -3),
    (19, -76, 45, 20, -16), (20, 4, 52, -59, 1), (21, 36, 45, 10, -6),
    (22, 47, 25, 8, 6), (23, 31, 37, -18, -6), (24, 90, 24, 7, -8),
    (25, 13, 52, 25, -12), (26, 12, 56, 27, 4), (27, 116, 24, 10, 10),
    (28, 0, 51, -48, -12), (29, 3, 50, -56, 23), (30, -75, 40, -30, 8),
    (31, 8, 47, -22, 25), (32, 140, 36, 7, -3), (33, 77, 29, -18, -4),
    (34, 178, -18, -16, -3), (35, 107, -6, 7, 6), (36, 116, 40, 7, -3),
    (37, 7, 45, 6, 23), (38, -7, 34, -8, 14), (39, 28, -26, 7, -3),
    (40, 92, 22, 8, 6), (41, 12, 42, 12, 18), (42, -67, 10, 7, -3),
]

BRIEFS = [
    "GTA VI ROLLS OUT WORLDWIDE AT MIDNIGHT",
    "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
    "VOYAGER 1 REACHES ONE LIGHT-DAY OUT",
    "US AND IRAN TRADE FIRE AGAIN",
    "EU OFFERS UKRAINE EUR 45BN LOAN",
    "ISRAELI TANKS CROSS GAZA YELLOW LINE",
    "ANTHROPIC IPO RAISES RECORD $81.3BN",
    "AUSTRALIA SANCTIONS ISRAELI SETTLERS",
    "LPG TANKER GAS HUSKY SINKS OFF BULGARIA",
    "PELTOLA WINS ALASKA, SENATE 56-44",
    "US LOSES MEASLES-FREE STATUS",
    "DEUTSCHE BANK FLAGGED $582M EPSTEIN DEALS",
    "NSA SECRET NETWORK DOWN FOR 2ND DAY",
    "FED MINUTES: MORE RATE HIKES EXPECTED",
    "BAYESIAN CREW UNAWARE OF WIND RISK",
    "HAALAND SENDS NORWAY TO LAST EIGHT",
    "CYCLONE AKVAN NEARS ANDHRA COAST",
    "NVIDIA PROMISES EARLY PAY RISES",
    "CARNEY REBUILDS CHINA TIES",
    "ICJ: MYANMAR COMMITTED ROHINGYA GENOCIDE",
    "UKRAINE HITS KERCH BRIDGE A THIRD TIME",
    "HOUTHI MISSILE DAMAGES RIYADH PIF TOWER",
    "COP31 MINISTERS RACE TO UNBLOCK TALKS",
    "BANGLADESH LOCKDOWN TURNS VIOLENT",
    "ALLIES MEET IN BERLIN FOR UKRAINE",
    "DENMARK RATIFIES GREENLAND DEAL 109-0",
    "LEADERS ISSUE SHENZHEN PEACE DECLARATION",
    "UK INFLATION HITS 12-MONTH HIGH, 3.6%",
    "EU COMMISSION HIT BY AI CYBERATTACK",
    "VAN GOGH SELLS FOR RECORD $190.4M",
    "FIFA CONFIRMS THREE PRESIDENTIAL CANDIDATES",
    "INDIA AND JAPAN HOLD 2+2 TALKS IN TOKYO",
    "MODI MEETS PRINCE AND PRINCESS OF WALES",
    "FIJI DECLARES DISASTER OVER EL NINO DROUGHT",
    "INDONESIA PASSES ASSET FORFEITURE LAW",
    "TAKAICHI MEETS PUTIN IN CHINA",
    "ZVEREV AND ALCARAZ REACH ATP FINALS SEMIS",
    "MOROCCO REACH RECORD FIFTH IN FIFA RANKING",
    "SOUTH AFRICA BEAT BANGLADESH IN FIRST TEST",
    "INDIA BEAT PAKISTAN FOR 10TH SAFF TITLE",
    "ITALY PASSES ANTISEMITISM LAW 147-93",
    "US AND VENEZUELA SIGN MILITARY DEAL",
]

# ------------------------------------------------------------- page layout
def kicker(x, y, s, c=RED):
    draw_text(x, y, s, 2, c)


def panel(x, y, w, h, kick, head, cap, art, head_scale=2, art_h=48):
    global CLIP
    frame(x, y, w, h, INK, 2)
    ax, ay, aw = x + 6, y + 6, w - 12
    kicker(ax, ay, kick)
    CLIP = (ax, ay + 16, ax + aw, ay + 16 + art_h)
    art(ax, ay + 16, aw, art_h)
    CLIP = None
    hy = ay + 16 + art_h + 6
    lines = wrap(head, head_scale, aw)
    for i, ln in enumerate(lines[:2]):
        draw_text(ax, hy + i * (head_scale * 8 + 2), ln, head_scale, INK)
    cy = hy + len(lines[:2]) * (head_scale * 8 + 2) + 3
    for i, ln in enumerate(wrap(cap, 2, aw)):
        if cy + i * 16 > y + h - 8:
            break
        draw_text(ax, cy + i * 16, ln, 2, CAPTION)


def masthead():
    rect(0, 0, W, 104, INK)
    draw_centred(W // 2, 8, "THE WORLD TODAY", 7, PAPER)
    hline(24, W - 24, 66, GOLD, 3)
    draw_centred(W // 2, 74, "THURSDAY 19 NOVEMBER 2026", 3, GOLD)


def footer():
    hline(16, W - 16, 970, INK, 3)
    draw_centred(W // 2, 978, "ALL STORIES REPORTED 18-19 NOV 2026", 3, RED)
    draw_centred(W // 2, 1002,
                 "42 STORIES - SOURCES: REUTERS, BBC, AP, CNN, NASA AND OTHERS - SEE SOURCES.MD",
                 2, CAPTION)


# ------------------------------------------------------------- world map
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 72), (-65, 60), (-55, 52), (-60, 47), (-70, 42), (-75, 35),
     (-80, 32), (-81, 26), (-90, 21), (-95, 19), (-97, 16), (-92, 15),
     (-86, 13), (-83, 9), (-79, 9), (-85, 11), (-90, 14), (-95, 16),
     (-105, 20), (-110, 23), (-115, 30), (-120, 34), (-125, 40),
     (-124, 48), (-130, 55), (-145, 60), (-158, 58), (-165, 60)],
    # South America
    [(-79, 9), (-75, 11), (-72, 12), (-64, 10), (-58, 8), (-52, 5),
     (-50, 0), (-44, -3), (-38, -5), (-35, -9), (-40, -15), (-39, -20),
     (-48, -25), (-48, -30), (-55, -35), (-62, -40), (-65, -45),
     (-68, -50), (-70, -55), (-73, -50), (-73, -44), (-73, -37),
     (-71, -30), (-70, -20), (-75, -15), (-79, -8), (-81, -5),
     (-80, 0), (-80, 5)],
    # Africa
    [(-17, 15), (-17, 21), (-15, 27), (-10, 31), (-5, 35), (0, 36),
     (10, 37), (11, 34), (20, 32), (25, 32), (32, 31), (35, 28),
     (37, 22), (40, 15), (43, 11), (48, 11), (51, 10), (46, 5),
     (41, 0), (40, -5), (38, -10), (35, -18), (32, -25), (28, -32),
     (20, -35), (17, -32), (15, -27), (12, -18), (13, -12), (12, -6),
     (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12)],
    # Asia
    [(30, 36), (35, 36), (36, 33), (40, 32), (44, 30), (48, 30),
     (50, 29), (54, 26), (57, 25), (60, 25), (62, 25), (66, 25),
     (68, 24), (72, 20), (75, 18), (78, 15), (80, 13), (80, 10),
     (77, 8), (80, 7), (83, 10), (86, 15), (88, 22), (92, 21),
     (94, 17), (97, 16), (100, 14), (100, 10), (103, 8), (105, 9),
     (107, 11), (109, 13), (108, 18), (106, 20), (108, 21), (110, 20),
     (114, 22), (117, 24), (120, 25), (122, 28), (120, 32), (122, 35),
     (120, 38), (122, 40), (126, 40), (128, 38), (130, 42), (132, 43),
     (135, 44), (138, 46), (140, 48), (142, 50), (142, 54), (140, 58),
     (138, 60), (142, 60), (145, 60), (150, 60), (155, 60), (158, 58),
     (160, 55), (162, 58), (163, 60), (160, 62), (158, 65), (155, 68),
     (150, 70), (145, 72), (140, 72), (135, 72), (130, 73), (125, 73),
     (120, 73), (115, 73), (110, 74), (105, 76), (100, 76), (95, 76),
     (90, 75), (85, 74), (80, 73), (75, 72), (70, 72), (65, 70),
     (60, 69), (55, 68), (50, 68), (45, 68), (42, 66), (40, 64),
     (38, 62), (35, 60), (32, 58), (30, 55), (28, 50), (26, 46),
     (24, 44), (22, 42), (24, 40), (26, 38), (28, 36)],
    # Europe
    [(-10, 36), (-9, 38), (-9, 43), (-2, 44), (-1, 46), (-4, 48),
     (-2, 49), (0, 50), (2, 51), (5, 53), (8, 55), (8, 57), (10, 58),
     (12, 55), (18, 56), (21, 55), (24, 58), (21, 60), (18, 62),
     (12, 64), (10, 62), (5, 60), (5, 58), (-2, 57), (-5, 55),
     (-8, 52), (-10, 48), (-10, 43), (-10, 38)],
    # Australia
    [(113, -22), (114, -30), (115, -33), (118, -35), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (150, -23),
     (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
     (132, -12), (130, -13), (126, -14), (122, -17), (118, -20),
     (114, -22)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-2, 58), (0, 53)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 36), (140, 38),
     (141, 40), (142, 42), (140, 44), (138, 40), (136, 37), (133, 35),
     (130, 33)],
    # New Zealand
    [(167, -45), (170, -42), (173, -40), (175, -38), (178, -38),
     (176, -40), (173, -42), (170, -45)],
]

MAP_X0, MAP_X1, MAP_Y0, MAP_Y1 = 24, 1000, 656, 780


def project(lon, lat):
    x = MAP_X0 + (lon + 170) / 360.0 * (MAP_X1 - MAP_X0)
    y = MAP_Y0 + (75 - lat) / 130.0 * (MAP_Y1 - MAP_Y0)
    return int(x), int(y)


def world_map(x, y, w, h):
    frame(x, y, w, h, INK, 2)
    draw_text(x + 10, y + 7, "THE WORLD IN ONE MAP", 3, RED)
    draw_text(x + w - 10 - text_w("42 STORIES, NUMBERED TO THE BRIEFS BELOW", 2),
              y + 10, "42 STORIES, NUMBERED TO THE BRIEFS BELOW", 2, INK)
    hline(x + 10, x + w - 10, y + 34, INK, 2)
    for cont in CONTINENTS:
        pts = [project(lon, lat) for lon, lat in cont]
        poly(pts, MAPLAND)
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            line(x0, y0, x1, y1, MAPLINE)
    for num, lon, lat, dx, dy in DOTS:
        cx, cy = project(lon, lat)
        disc(cx, cy, 5, RED)
        ring(cx, cy, 5, WHITE, 1)
        ns = str(num)
        nx, ny = cx + dx, cy + dy
        if abs(dx) > 12 or abs(dy) > 8:
            line(cx, cy, nx + text_w(ns, 1) // 2, ny + 3, RED)
        rect(nx - 1, ny - 1, text_w(ns, 1) + 2, 9, WHITE)
        draw_text(nx, ny, ns, 1, RED)


def brief_strip(x, y, w, h):
    frame(x, y, w, h, INK, 2)
    draw_text(x + 10, y + 7, "WORLD IN BRIEF", 3, RED)
    draw_text(x + w - 10 - text_w("ALL 42 STORIES, NUMBERED TO THE MAP", 2),
              y + 10, "ALL 42 STORIES, NUMBERED TO THE MAP", 2, INK)
    hline(x + 10, x + w - 10, y + 34, INK, 2)
    col_x = [x + 10, x + 340, x + 670]
    for i, b in enumerate(BRIEFS):
        col = i // 14
        row = i % 14
        bx = col_x[col]
        by = y + 42 + row * 9
        ns = str(i + 1)
        draw_text(bx, by, ns + " " + b, 1, INK)


def build():
    masthead()
    # lead: GTA VI
    panel(16, 112, 600, 210, "CULTURE - GAMES", "VICE CITY OPENS ITS DOORS",
          "ROLLS OUT AT MIDNIGHT, 13 YEARS ON",
          art_gta, head_scale=4, art_h=92)
    # right column: summit + ICJ
    panel(624, 112, 384, 102, "DIPLOMACY - SHENZHEN", "THREE LEADERS, ONE TABLE",
          "LEADERS MEET IN SHENZHEN TODAY", art_summit,
          head_scale=2, art_h=32)
    panel(624, 222, 384, 100, "LAW - THE HAGUE", "MYANMAR COMMITTED GENOCIDE",
          "ICJ ORDERS REPARATIONS", art_court,
          head_scale=2, art_h=30)
    # row B
    bw, gap = 242, 8
    bx = 16
    for num, kick, head, cap, art, lon, lat, dx, dy in PANELS[:4]:
        panel(bx, 330, bw, 136, kick, head, cap, art, art_h=44)
        bx += bw + gap
    # row C
    bx = 16
    for num, kick, head, cap, art, lon, lat, dx, dy in PANELS[4:]:
        panel(bx, 474, bw, 126, kick, head, cap, art, art_h=38)
        bx += bw + gap
    # map + briefs + footer
    world_map(16, 608, 992, 178)
    brief_strip(16, 794, 992, 168)
    footer()


# ------------------------------------------------------------- PNG encoder
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png():
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += PIX[yy * W * 3:(yy + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    build()
    data = encode_png()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
