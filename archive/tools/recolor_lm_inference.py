"""Recolor selected PNG figures without changing their geometry or labels.

Uses only the Python standard library. Run from the repository root.
"""

from collections import Counter
from pathlib import Path
import struct
import sys
import zlib


def chunks(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Not a PNG")
    offset = 8
    while offset < len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        yield kind, payload
        offset += length + 12
        if kind == b"IEND":
            break


def paeth(a, b, c):
    p = a + b - c
    da, db, dc = abs(p - a), abs(p - b), abs(p - c)
    return a if da <= db and da <= dc else b if db <= dc else c


def read_png(path):
    parts = list(chunks(path.read_bytes()))
    width, height, depth, color, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", next(payload for kind, payload in parts if kind == b"IHDR")
    )
    if (depth, color, compression, filtering, interlace) not in (
        (8, 2, 0, 0, 0),
        (8, 6, 0, 0, 0),
    ):
        raise ValueError(f"Unsupported PNG format: {path}")
    channels = 3 if color == 2 else 4
    stride = width * channels
    raw = zlib.decompress(b"".join(payload for kind, payload in parts if kind == b"IDAT"))
    rows = []
    offset = 0
    previous = bytearray(stride)
    for _ in range(height):
        method = raw[offset]
        row = bytearray(raw[offset + 1 : offset + 1 + stride])
        offset += stride + 1
        for i in range(stride):
            left = row[i - channels] if i >= channels else 0
            above = previous[i]
            upper_left = previous[i - channels] if i >= channels else 0
            if method == 1:
                row[i] = (row[i] + left) & 255
            elif method == 2:
                row[i] = (row[i] + above) & 255
            elif method == 3:
                row[i] = (row[i] + ((left + above) // 2)) & 255
            elif method == 4:
                row[i] = (row[i] + paeth(left, above, upper_left)) & 255
            elif method != 0:
                raise ValueError(f"Unknown PNG filter {method}: {path}")
        rows.append(row)
        previous = row
    if offset != len(raw):
        raise ValueError(f"Unexpected PNG payload length: {path}")
    return width, height, channels, rows


def analyze(path):
    width, height, channels, rows = read_png(path)
    counts = Counter()
    for row in rows[::4]:
        counts.update(tuple(row[i : i + 3]) for i in range(0, len(row), channels * 4))
    print(f"{path}: {width}x{height}, {channels} channels, {len(counts)} sampled colors")
    for (red, green, blue), count in counts.most_common(24):
        print(f"  #{red:02x}{green:02x}{blue:02x} {count}")


TARGETS = (
    "img/screenshots/config.png",
    "img/image 1.png",
    "img/image 2.png",
    "img/prefix_surprise.png",
    "img/divergence.png",
)


def grayscale(pixel):
    red, green, blue = pixel
    shade = round(0.2126 * red + 0.7152 * green + 0.0722 * blue)
    if shade >= 242:
        shade = 255  # Make the original pale pink page background white.
    return (shade, shade, shade)


def png_chunk(kind, payload):
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_png(path, width, height, channels, rows):
    header = struct.pack(">IIBBBBB", width, height, 8, 2 if channels == 3 else 6, 0, 0, 0)
    compressed = zlib.compress(b"".join(b"\x00" + row for row in rows), level=6)
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", compressed)
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def apply(name):
    source = Path("archive/writing/lm-inference") / name
    width, height, channels, rows = read_png(source)
    cache = {}
    changed = 0
    for row in rows:
        for i in range(0, len(row), channels):
            if channels == 4 and row[i + 3] == 0:
                continue
            original = tuple(row[i : i + 3])
            replacement = cache.get(original)
            if replacement is None:
                replacement = grayscale(original)
                cache[original] = replacement
            if replacement != original:
                row[i : i + 3] = bytes(replacement)
                changed += 1
    for root in (Path("writing/lm-inference"), Path("archive/content/writing/lm-inference")):
        output = root / name
        write_png(output, width, height, channels, rows)
    print(f"{name}: recolored {changed} pixels, preserved {width}x{height} geometry")


if __name__ == "__main__":
    if sys.argv[1:] == ["--apply"]:
        for name in TARGETS:
            apply(name)
    else:
        for name in sys.argv[1:]:
            analyze(Path(name))
