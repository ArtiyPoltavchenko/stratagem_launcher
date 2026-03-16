"""Generate app icons for the PWA (app-192.png, app-512.png).

Uses only Python stdlib — no Pillow required.
Produces a simple PNG: dark background, yellow circle border, "SL" label.
Run from project root: python3 scripts/generate_icons.py
"""

import struct
import zlib
from pathlib import Path

BG     = (10, 10, 10)       # #0a0a0a
ACCENT = (245, 197, 24)     # #f5c518
DARK   = (37, 37, 37)       # #252525


def _pixel(size: int, x: int, y: int) -> tuple[int, int, int]:
    cx = cy = size / 2.0
    r_outer = size * 0.46
    r_inner = size * 0.38
    dx, dy = x - cx + 0.5, y - cy + 0.5
    dist = (dx * dx + dy * dy) ** 0.5

    # Outer ring (yellow)
    if r_inner <= dist <= r_outer:
        return ACCENT

    # Dark circle interior
    if dist > r_outer:
        return BG

    # Draw "SL" inside the circle
    u = size / 20.0           # base unit
    # S letter: centered left of middle
    sx, sy = cx - 3.2 * u, cy  # top-left corner of S bounding box (top = sy - 2u)
    lx, ly = cx + 0.3 * u, cy  # top-left corner of L

    def rect(px, py, rx1, ry1, rx2, ry2) -> bool:
        return rx1 <= px <= rx2 and ry1 <= py <= ry2

    t = max(1.0, u * 0.55)  # stroke thickness

    # S shape (5 strokes)
    s_hit = (
        rect(x, y, sx,           sy - 2*u, sx + 2.2*u, sy - 2*u + t)   # top bar
        or rect(x, y, sx,         sy - t/2, sx + 2.2*u, sy + t/2)       # mid bar
        or rect(x, y, sx,         sy + 2*u - t, sx + 2.2*u, sy + 2*u)   # bot bar
        or rect(x, y, sx,         sy - 2*u, sx + t,     sy)              # top-left stem
        or rect(x, y, sx+2.2*u-t, sy,       sx + 2.2*u, sy + 2*u)       # bot-right stem
    )

    # L shape (2 strokes)
    l_hit = (
        rect(x, y, lx, ly - 2*u, lx + t,       ly + 2*u)               # vertical
        or rect(x, y, lx, ly + 2*u - t, lx + 2.2*u, ly + 2*u)          # horizontal
    )

    if s_hit or l_hit:
        return ACCENT

    return DARK


def _make_png(size: int) -> bytes:
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            row.extend(_pixel(size, x, y))
        rows.append(b'\x00' + bytes(row))   # filter byte None

    raw = b''.join(rows)
    compressed = zlib.compress(raw, 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + body + struct.pack('>I', crc)

    ihdr = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    return (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', ihdr)
        + chunk(b'IDAT', compressed)
        + chunk(b'IEND', b'')
    )


def main() -> None:
    out_dir = Path(__file__).parent.parent / 'web' / 'icons'
    out_dir.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        path = out_dir / f'app-{size}.png'
        path.write_bytes(_make_png(size))
        print(f'Generated {path}  ({path.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
