#!/usr/bin/env python3
"""Generate app icons for the PWA using only the Python standard library.

Draws a cozy pint of beer (amber fill + white foam) on a warm pub-dark
gradient — the motif of the "건배 / Cheers" game.
"""
import os
import struct
import zlib

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def make_icon(size):
    px = bytearray(size * size * 4)

    bg_top = (54, 36, 22)     # warm dark amber
    bg_bot = (18, 12, 12)     # near-black

    def bg_at(y):
        return lerp_color(bg_top, bg_bot, y / max(1, size - 1))

    # paint background gradient
    for y in range(size):
        r, g, b = bg_at(y)
        for x in range(size):
            i = (y * size + x) * 4
            px[i] = r; px[i + 1] = g; px[i + 2] = b; px[i + 3] = 255

    def put(x, y, c):
        if 0 <= x < size and 0 <= y < size:
            i = (y * size + x) * 4
            px[i] = c[0]; px[i + 1] = c[1]; px[i + 2] = c[2]; px[i + 3] = 255

    # Glass geometry (slightly tapered pint).
    gx0, gx1 = size * 0.30, size * 0.70
    gy0, gy1 = size * 0.20, size * 0.86
    wall = size * 0.035
    radius = size * 0.06

    glass = (214, 226, 244)
    liquid_top = (255, 200, 74)
    liquid_bot = (226, 150, 30)
    foam = (250, 247, 238)

    liquid_top_y = gy0 + (gy1 - gy0) * 0.30   # foam/liquid boundary

    fill_round_rect(put, gx0, gy0, gx1, gy1, radius, lambda x, y: glass)
    # hollow it back to background
    fill_round_rect(put, gx0 + wall, gy0 + wall, gx1 - wall, gy1 - wall,
                    radius * 0.7, lambda x, y: bg_at(int(y)))
    # liquid
    fill_round_rect(put, gx0 + wall, liquid_top_y, gx1 - wall, gy1 - wall,
                    radius * 0.7,
                    lambda x, y: lerp_color(liquid_top, liquid_bot,
                                            (y - liquid_top_y) / max(1, (gy1 - wall - liquid_top_y))))
    # foam cap (band + a couple of bumps)
    fill_round_rect(put, gx0 + wall, gy0 + wall, gx1 - wall, liquid_top_y + size * 0.02,
                    radius * 0.6, lambda x, y: foam)
    for bx in (0.42, 0.55, 0.63):
        fill_circle(put, size * bx, gy0 + wall, size * 0.05, foam)

    # a few rising bubbles
    for (bx, by) in [(0.42, 0.62), (0.58, 0.70), (0.50, 0.55), (0.62, 0.50)]:
        fill_circle(put, size * bx, size * by, size * 0.014, (255, 232, 170))

    return png_bytes(size, size, px)


def fill_round_rect(put, x0, y0, x1, y1, r, colorfn):
    ix0, iy0, ix1, iy1 = int(x0), int(y0), int(x1), int(y1)
    cl, cr = ix0 + r, ix1 - r
    ct, cb = iy0 + r, iy1 - r
    for y in range(iy0, iy1 + 1):
        for x in range(ix0, ix1 + 1):
            inside = True
            if x < cl and y < ct:
                inside = (x - cl) ** 2 + (y - ct) ** 2 <= r * r
            elif x > cr and y < ct:
                inside = (x - cr) ** 2 + (y - ct) ** 2 <= r * r
            elif x < cl and y > cb:
                inside = (x - cl) ** 2 + (y - cb) ** 2 <= r * r
            elif x > cr and y > cb:
                inside = (x - cr) ** 2 + (y - cb) ** 2 <= r * r
            if inside:
                put(x, y, colorfn(x, y))


def fill_circle(put, cx, cy, r, color):
    ir = int(r)
    for dy in range(-ir, ir + 1):
        for dx in range(-ir, ir + 1):
            if dx * dx + dy * dy <= r * r:
                put(int(cx + dx), int(cy + dy), color)


def png_bytes(width, height, rgba):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(rgba[y * stride:(y + 1) * stride])
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for size, name in [(180, "icon-180.png"), (192, "icon-192.png"),
                       (512, "icon-512.png")]:
        with open(os.path.join(OUT_DIR, name), "wb") as f:
            f.write(make_icon(size))
        print("wrote icons/" + name)


if __name__ == "__main__":
    main()
