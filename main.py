"""THE WORLD - front page for Monday 23 November 2026.

Standard library only (zlib, struct, os). Draws a deterministic
1024x1024 RGB PNG broadsheet page and writes it to entry.png.
"""

import os
import struct
import zlib

W = H = 1024
PAPER = (243, 239, 228)
INK = (24, 24, 27)
BODY = (74, 71, 68)
GREY = (122, 117, 110)
RED = (150, 32, 38)
WHITE = (250, 248, 242)
M = 36
CW = 464
COL2 = 524
ROWS = (352, 540, 728)

buf = bytearray(W * H * 3)
clip = (0, 0, W, H)
OX = OY = 0


def box(x0, y0, x1, y1, c):
    x0 = max(clip[0], int(x0 + OX))
    y0 = max(clip[1], int(y0 + OY))
    x1 = min(clip[2], int(x1 + OX))
    y1 = min(clip[3], int(y1 + OY))
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for y in range(y0, y1):
        i = (y * W + x0) * 3
        buf[i:i + len(row)] = row


def hline(x0, x1, y, t, c):
    box(x0, y, x1, y + t, c)


def vline(x, y0, y1, t, c):
    box(x, y0, x + t, y1, c)


def disc(cx, cy, r, c):
    r = int(r)
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                box(x, y, x + 1, y + 1, c)


def line(x0, y0, x1, y1, c, t=1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i // n
        y = y0 + (y1 - y0) * i // n
        box(x, y, x + t, y + t, c)


def poly(pts, c):
    ys = [p[1] for p in pts]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            box(int(a) , y, int(b) + 2, y + 1, c)


# 5x7 bitmap font: one glyph per line, seven rows of five bits.
FONT_TEXT = """
A 01110 10001 10001 11111 10001 10001 10001
B 11110 10001 10001 11110 10001 10001 11110
C 01110 10001 10000 10000 10000 10001 01110
D 11110 10001 10001 10001 10001 10001 11110
E 11111 10000 10000 11110 10000 10000 11111
F 11111 10000 10000 11110 10000 10000 10000
G 01110 10001 10000 10111 10001 10001 01111
H 10001 10001 10001 11111 10001 10001 10001
I 11111 00100 00100 00100 00100 00100 11111
J 00111 00010 00010 00010 00010 10010 01100
K 10001 10010 10100 11000 10100 10010 10001
L 10000 10000 10000 10000 10000 10000 11111
M 10001 11011 10101 10101 10001 10001 10001
N 10001 11001 10101 10011 10001 10001 10001
O 01110 10001 10001 10001 10001 10001 01110
P 11110 10001 10001 11110 10000 10000 10000
Q 01110 10001 10001 10001 10101 10010 01101
R 11110 10001 10001 11110 10100 10010 10001
S 01111 10000 10000 01110 00001 00001 11110
T 11111 00100 00100 00100 00100 00100 00100
U 10001 10001 10001 10001 10001 10001 01110
V 10001 10001 10001 10001 10001 01010 00100
W 10001 10001 10001 10101 10101 11011 10001
X 10001 10001 01010 00100 01010 10001 10001
Y 10001 10001 01010 00100 00100 00100 00100
Z 11111 00001 00010 00100 01000 10000 11111
0 01110 10001 10011 10101 11001 10001 01110
1 00100 01100 00100 00100 00100 00100 01110
2 01110 10001 00001 00010 00100 01000 11111
3 11111 00010 00100 00010 00001 10001 01110
4 00010 00110 01010 10010 11111 00010 00010
5 11111 10000 11110 00001 00001 10001 01110
6 00110 01000 10000 11110 10001 10001 01110
7 11111 00001 00010 00100 01000 01000 01000
8 01110 10001 10001 01110 10001 10001 01110
9 01110 10001 10001 01111 00001 00010 01100
SP 00000 00000 00000 00000 00000 00000 00000
. 00000 00000 00000 00000 00000 01100 01100
, 00000 00000 00000 00000 00110 00110 01100
' 00110 00110 00000 00000 00000 00000 00000
- 00000 00000 00000 11111 00000 00000 00000
: 00000 01100 01100 00000 01100 01100 00000
"""
FONT = {p[0]: p[1:] for p in (ln.split() for ln in FONT_TEXT.splitlines() if ln.strip())}


def glyph(ch):
    return FONT.get(ch.upper(), FONT["SP"])


def tw(s, sc=1):
    return (6 * len(s) - 1) * sc


def text(x, y, s, sc=1, c=INK):
    for ch in s:
        g = glyph(ch)
        for r in range(7):
            for k in range(5):
                if g[r][k] == "1":
                    box(x + k * sc, y + r * sc, x + (k + 1) * sc, y + (r + 1) * sc, c)
        x += 6 * sc


def ctext(x0, x1, y, s, sc=1, c=INK):
    text(x0 + (x1 - x0 - tw(s, sc)) // 2, y, s, sc, c)


def wrap(s, n):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + (1 if cur else 0) <= n:
            cur = (cur + " " + w) if cur else w
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------- illustrations


def art_libya():
    ox = oy = 0
    box(ox, oy, 464, oy + 54, (62, 74, 90))
    box(ox, oy + 54, 464, oy + 92, (26, 46, 64))
    box(ox, oy + 54, 464, oy + 56, (150, 168, 178))
    disc(76, oy + 26, 12, (224, 222, 206))
    disc(81, oy + 22, 10, (62, 74, 90))
    for i, wy in enumerate((62, 70, 78, 86)):
        for wx in range(-16, 464, 44):
            off = (wx * 7 + i * 13) % 26
            box(wx + off, oy + wy, wx + off + 22, oy + wy + 2, (64, 96, 116))
    poly([(150, oy + 56), (336, oy + 56),
          (312, oy + 78), (174, oy + 78)], (56, 60, 66))
    box(150, oy + 56, 336, oy + 60, (96, 100, 106))
    box(214, oy + 38, 272, oy + 56, (76, 80, 86))
    box(222, oy + 44, 250, oy + 50, (156, 186, 196))
    box(286, oy + 30, 300, oy + 56, (76, 80, 86))
    box(286, oy + 30, 300, oy + 34, (140, 40, 40))
    vline(326, oy + 20, oy + 56, 2, (76, 80, 86))
    for i in range(5):
        disc(306 + i * 7, oy + 26 - i * 5, 5 + i, (110, 110, 112))
    disc(330, oy + 64, 9, (196, 60, 40))
    disc(330, oy + 64, 4, (240, 196, 96))
    poly([(376, oy + 14), (404, oy + 28), (376, oy + 34)], (34, 38, 42))
    line(376, oy + 14, 356, oy + 8, (34, 38, 42), 2)
    line(380, oy + 32, 380, oy + 44, (34, 38, 42), 2)


def art_gaza():
    ox = oy = 0
    ground = oy + 82
    box(ox, oy, 464, ground, (208, 188, 152))
    box(ox, ground, 464, oy + 92, (148, 128, 98))
    disc(368, oy + 24, 15, (230, 202, 148))
    for i in range(4):
        disc(120 + i * 52, oy + 18 + (i % 2) * 8, 9 + i, (206, 196, 182))
    for bx, bw, bh in ((-8, 48, 42), (40, 34, 60), (74, 44, 34), (118, 30, 68),
                       (148, 44, 48), (192, 34, 74), (226, 32, 44), (258, 44, 58),
                       (302, 34, 38), (336, 40, 64), (376, 46, 48), (422, 44, 34)):
        top = ground - bh
        box(bx, top, bx + bw, ground, (88, 78, 66))
        poly([(bx, top), (bx + bw, top + bh // 3),
              (bx + bw, top)], (208, 188, 152))
        for wy in range(top + 12, ground - 8, 13):
            for wx in range(bx + 6, bx + bw - 8, 11):
                if (wx * 3 + wy) % 7 < 4:
                    box(wx, wy, wx + 4, wy + 6, (54, 48, 42))
        if bh > 55:
            vline(bx + 4, top - 8, top, 1, (60, 54, 48))
    for i in range(14):
        rx = (i * 37) % 440
        box(rx, ground - 4, rx + 14, ground + 8, (70, 62, 52))


def art_hormuz():
    ox = oy = 0
    box(ox, oy, 464, oy + 92, (24, 64, 76))
    for wy in (16, 40, 64, 84):
        for wx in range(0, 464, 46):
            wf = (wy * 5 + wx) % 24
            box(wx + wf, oy + wy, wx + wf + 20, oy + wy + 2, (42, 88, 100))
    poly([(ox, oy), (150, oy), (166, oy + 28), (142, oy + 52),
          (158, oy + 74), (138, oy + 92), (ox, oy + 92)], (200, 180, 142))
    poly([(464, oy), (314, oy), (298, oy + 24), (322, oy + 48),
          (304, oy + 70), (324, oy + 92), (464, oy + 92)],
         (200, 180, 142))
    for i in range(5):
        line(150, oy + 4 + i * 20, 146, oy + 14 + i * 20, (168, 148, 114), 3)
        line(314, oy + 6 + i * 20, 310, oy + 16 + i * 20, (168, 148, 114), 3)
    poly([(214, oy + 14), (258, oy + 14), (266, oy + 40),
          (262, oy + 76), (210, oy + 76), (206, oy + 40)],
         (52, 56, 62))
    poly([(214, oy + 14), (258, oy + 14), (236, oy + 4)], (52, 56, 62))
    box(214, oy + 22, 258, oy + 62, (128, 54, 48))
    for i in range(3):
        box(220, oy + 28 + i * 11, 252, oy + 33 + i * 11, (150, 70, 60))
    box(214, oy + 64, 258, oy + 74, (226, 224, 214))
    for i in range(3):
        box(219 + i * 12, oy + 66, 226 + i * 12, oy + 71, (40, 60, 70))
    line(214, oy + 78, 196, oy + 92, (120, 160, 176), 2)
    line(258, oy + 78, 276, oy + 92, (120, 160, 176), 2)
    line(226, oy + 78, 218, oy + 92, (120, 160, 176), 1)
    line(246, oy + 78, 254, oy + 92, (120, 160, 176), 1)
    disc(186, oy + 84, 5, (26, 26, 30))
    line(186, oy + 78, 186, oy + 90, (26, 26, 30), 2)
    line(180, oy + 84, 192, oy + 84, (26, 26, 30), 2)
    disc(290, oy + 18, 5, (26, 26, 30))
    line(290, oy + 12, 290, oy + 24, (26, 26, 30), 2)
    line(284, oy + 18, 296, oy + 18, (26, 26, 30), 2)
    disc(258, oy + 20, 9, (196, 60, 40))
    disc(258, oy + 20, 4, (240, 196, 96))


def art_nvidia():
    ox = oy = 0
    box(ox, oy, 464, oy + 92, (26, 34, 30))
    for gx in range(0, 465, 24):
        vline(gx, oy, oy + 92, 1, (34, 44, 38))
    for gy in range(0, 93, 24):
        hline(ox, 464, oy + gy, 1, (34, 44, 38))
    box(26, oy + 16, 122, oy + 88, (14, 18, 16))
    box(34, oy + 24, 114, oy + 80, (62, 122, 76))
    box(48, oy + 36, 100, oy + 68, (30, 56, 40))
    for i in range(5):
        box(40 + i * 14, oy + 84, 46 + i * 14, oy + 90, (176, 146, 66))
        box(40 + i * 14, oy + 14, 46 + i * 14, oy + 20, (176, 146, 66))
    text(52, oy + 40, "NV", 2, (150, 224, 160))
    disc(202, oy + 46, 44, (76, 104, 84))
    disc(202, oy + 46, 36, (92, 122, 98))
    disc(196, oy + 30, 14, (240, 228, 202))
    poly([(176, oy + 48), (216, oy + 48),
          (228, oy + 92), (164, oy + 92)], (18, 22, 20))
    poly([(186, oy + 48), (206, oy + 48), (198, oy + 78)],
         (236, 232, 220))
    line(186, oy + 50, 180, oy + 70, (18, 22, 20), 3)
    line(218, oy + 52, 244, oy + 24, (18, 22, 20), 9)
    disc(247, oy + 22, 6, (240, 228, 202))
    line(178, oy + 54, 156, oy + 74, (18, 22, 20), 9)
    for i in range(5):
        disc(292 + i * 30, oy + 78, 9, (66, 76, 70))
        disc(292 + i * 30, oy + 66, 7, (86, 94, 88))
    text(340, oy + 16, "1.5T", 2, (206, 176, 86))


def art_cop31():
    ox = oy = 0
    box(ox, oy, 464, oy + 92, (198, 202, 196))
    for gx in range(0, 465, 32):
        vline(gx, oy, oy + 92, 1, (188, 192, 186))
    disc(186, oy + 46, 42, (58, 100, 140))
    disc(170, oy + 32, 12, (104, 148, 104))
    disc(202, oy + 58, 15, (104, 148, 104))
    disc(158, oy + 60, 9, (104, 148, 104))
    disc(208, oy + 30, 8, (104, 148, 104))
    crack = ((186, 6), (176, 22), (192, 34), (180, 50), (196, 62), (184, 78), (192, 88))
    for i in range(len(crack) - 1):
        line(crack[i][0], oy + crack[i][1],
             crack[i + 1][0], oy + crack[i + 1][1], (238, 238, 230), 4)
    poly([(212, oy + 62), (236, oy + 74), (214, oy + 86)],
         (198, 202, 196))
    box(292, oy + 26, 428, oy + 72, (150, 32, 38))
    box(298, oy + 32, 422, oy + 66, (198, 202, 196))
    text(298, oy + 38, "NO DEAL", 3, (150, 32, 38))


def art_fifa():
    ox = oy = 0
    box(ox, oy, 464, oy + 92, (116, 32, 36))
    for gx in range(0, 465, 34):
        vline(gx, oy, oy + 92, 1, (104, 28, 32))
    poly([(190, oy + 10), (266, oy + 10),
          (256, oy + 44), (228, oy + 58), (200, oy + 44)],
         (208, 172, 78))
    poly([(198, oy + 14), (218, oy + 14),
          (212, oy + 42), (202, oy + 38)], (232, 200, 116))
    left = ((190, 16), (174, 26), (172, 38), (186, 46), (198, 44))
    right = ((266, 16), (282, 26), (284, 38), (270, 46), (258, 44))
    for h in (left, right):
        for i in range(len(h) - 1):
            line(h[i][0], oy + h[i][1], h[i + 1][0], oy + h[i + 1][1],
                 (208, 172, 78), 7)
    box(222, oy + 58, 234, oy + 72, (208, 172, 78))
    box(204, oy + 72, 252, oy + 82, (186, 150, 64))
    box(196, oy + 82, 260, oy + 88, (150, 120, 52))
    for sx, sy in ((312, 26), (342, 52), (300, 70), (362, 34)):
        line(sx - 5, oy + sy, sx + 7, oy + sy, (226, 194, 104), 2)
        line(sx, oy + sy - 5, sx, oy + sy + 7, (226, 194, 104), 2)
    text(318, oy + 62, "2031", 2, (226, 194, 104))


# --------------------------------------------------------------------- layout

box(0, 0, W, H, PAPER)
box(M, 20, W - M, 25, INK)
box(M, 30, W - M, 31, INK)
ctext(M, W - M, 38, "THE WORLD", 9, INK)
box(M, 106, W - M, 110, RED)
text(M, 118, "MONDAY, NOVEMBER 23, 2026", 2, INK)
text(W - M - tw("WORLD AFFAIRS - LATE EDITION", 2), 118, "WORLD AFFAIRS - LATE EDITION", 2, INK)
box(M, 138, W - M, 139, INK)

box(M, 146, W - M, 288, INK)
ctext(M, W - M, 162, "UKRAINE DRONES SINK", 4, WHITE)
ctext(M, W - M, 200, "RUSSIAN WARSHIPS OFF LIBYA", 4, WHITE)
ctext(M, W - M, 246, "VIDEO SHOWS SEA DRONE STRIKE IN NORTH AFRICA", 2, (226, 222, 214))
box(M, 288, W - M, 296, RED)
text(M, 312, "TEN STORIES THAT SHAPED THE DAY - GAZA, HORMUZ, NVIDIA AND COP31", 1, BODY)
text(W - M - tw("PAGES 2-11", 1), 312, "PAGES 2-11", 1, BODY)


def card(x, y, tag, title, body, art):
    global clip, OX, OY
    clip = (x, y, x + CW, y + 92)
    OX, OY = x, y
    art()
    OX = OY = 0
    clip = (0, 0, W, H)
    hline(x, x + CW, y + 94, 1, INK)
    text(x, y + 100, tag, 1, RED)
    ty = y + 112
    for ln in wrap(title, 38)[:2]:
        text(x, ty, ln, 2, INK)
        ty += 17
    by = y + 150
    for ln in wrap(body, 74)[:3]:
        text(x, by, ln, 1, BODY)
        by += 10


card(M, ROWS[0], "NORTH AFRICA", "UKRAINE'S SEA DRONES SINK RUSSIAN WARSHIPS OFF LIBYA",
     "Kyiv released video of naval drones hitting the Black Sea Fleet detachment at a Libyan port. "
     "Moscow calls it an act of war beyond Europe while rescue ships race to the burning hull.",
     art_libya)
card(COL2, ROWS[0], "GAZA", "OXFAM: A 'TOXIC WASTELAND' FOR DECADES",
     "Bombardment has poisoned soil and water, the aid group reports. Settler attacks spread across "
     "the West Bank as convoys are turned back at the crossings.",
     art_gaza)
card(M, ROWS[1], "STRAIT OF HORMUZ", "IRANIAN ATTACKS AT HIGHEST LEVEL SINCE WAR BEGAN",
     "Two tankers struck mines in the strait overnight and insurance rates doubled. Tehran warns "
     "the waterway is closed to enemies of the revolution.",
     art_hormuz)
card(COL2, ROWS[1], "NVIDIA", "HUANG REINSTATED AFTER 1.5T BLUNDER",
     "The board returned Jensen Huang to the chief executive's chair after the 1.5 trillion dollar "
     "blunder. Staff cheered; Trump claimed credit and Republicans broke with him.",
     art_nvidia)
card(M, ROWS[2], "COP31", "CLIMATE TALKS COLLAPSE WITH NO DEAL",
     "Two weeks of negotiations ended in acrimony as blocs traded blame over finance. Delegates left "
     "with a statement of deep regret and nothing binding.",
     art_cop31)
card(COL2, ROWS[2], "FIFA", "US-LEAD BID WINS 2031 WOMEN'S WORLD CUP",
     "FIFA chose the United States-led bid for 2031 and awarded the 2035 tournament to the UK. "
     "The vote was unanimous after the last rival withdrew.",
     art_fifa)

vline(512, ROWS[0], 908, 1, GREY)
hline(M, W - M, 536, 1, GREY)
hline(M, W - M, 724, 1, GREY)

text(M, 924, "IN BRIEF", 2, RED)
hline(M, W - M, 944, 2, INK)
BRIEFS = (
    ("DR CONGO", "Military aircraft missing; rebels claim they shot it down."),
    ("MYANMAR", "UK sanctions top generals after the Rohingya genocide ruling."),
    ("IRAN", "Female singer flogged for performing without a hijab."),
    ("FRANCE", "Pelicot 'humiliated' after nude photos were sent to media."),
)
for i, (tag, note) in enumerate(BRIEFS):
    bx = M + i * 238
    text(bx, 952, tag, 1, RED)
    ly = 962
    for ln in wrap(note, 36)[:2]:
        text(bx, ly, ln, 1, BODY)
        ly += 9


def chunk(tag, data):
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def save(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += buf[y * W * 3:(y + 1) * W * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(outdir, exist_ok=True)
outpath = os.path.join(outdir, "entry.png")
print("wrote", outpath, save(outpath), "bytes")
