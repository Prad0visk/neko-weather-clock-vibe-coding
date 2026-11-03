"""Minimal STI image encoder adapted from SmallTV Mod's theme_pack.py.

Upstream author: giovi321; license: WTFPL v2. See THIRD_PARTY_NOTICES.md.
"""
import struct
from PIL import Image

def rgb565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def image_rgba(image):
    w, h = image.size
    if not (1 <= w <= 240 and 1 <= h <= 240):
        raise ValueError('Image dimensions must be 1..240 pixels')
    rgba = image.convert('RGBA')
    return rgba, rgba.getextrema()[3][0] != 255


def encode_sti1(image):
    rgba, has_alpha = image_rgba(image)
    w, h = rgba.size
    data = bytearray(b'STI1' + struct.pack('<HHB3x', w, h, int(has_alpha)))
    for r, g, b, a in rgba.getdata():
        data.extend(struct.pack('<H', rgb565(r, g, b)))
        if has_alpha:
            data.append(a)
    return bytes(data)


def row_runs(row, min_repeat):
    """Splits a row into (kind, pixels) runs of at most 64 pixels: 0
    transparent (a pixel of None), 1 one pixel repeated, 2 literal pixels.
    A repeat is used from `min_repeat` equal pixels on."""
    runs, literal = [], []

    def add(kind, pixels):
        for start in range(0, len(pixels), 64):
            runs.append((kind, pixels[start:start + 64]))

    i = 0
    while i < len(row):
        j = i
        while j < len(row) and row[j] == row[i]:
            j += 1
        if row[i] is None or j - i >= min_repeat:
            add(2, literal)
            literal = []
            add(0 if row[i] is None else 1, row[i:j])
        else:
            literal.extend(row[i:j])
        i = j
    add(2, literal)
    return runs


def encode_sti2(image, indexed=False):
    """STI2 as agreed in #31: rows as runs, direct RGB565 or indexed through a
    palette of up to 16 colours (None when the image has more)."""
    rgba, has_alpha = image_rgba(image)
    w, h = rgba.size
    # A pixel is (RGB565, alpha), or None when fully transparent.
    pixels = [None if a == 0 else (rgb565(r, g, b), a) for r, g, b, a in rgba.getdata()]
    rows = [pixels[y * w:(y + 1) * w] for y in range(h)]
    palette = []
    if indexed:
        for pixel in pixels:
            if pixel is not None and pixel not in palette:
                palette.append(pixel)
        if len(palette) > 16:
            return None

    def colour(pixel):
        return struct.pack('<H', pixel[0]) + (bytes([pixel[1]]) if has_alpha else b'')

    def encode_row(row):
        data = bytearray()
        for kind, run in row_runs(row, 4 if indexed else 2):
            data.append(kind << 6 | (len(run) - 1))
            if kind == 1:
                data.extend(bytes([palette.index(run[0])]) if indexed else colour(run[0]))
            elif kind == 2 and indexed:
                # Two indices per byte, high nibble first; an odd run's
                # unused low nibble is 0.
                indices = [palette.index(pixel) for pixel in run] + [0]
                data.extend(indices[k] << 4 | indices[k + 1] for k in range(0, len(run), 2))
            elif kind == 2:
                for pixel in run:
                    data.extend(colour(pixel))
        return bytes(data)

    data = bytearray(b'STI2' + struct.pack('<HHBB2x', w, h, int(has_alpha), len(palette)))
    for pixel in palette:
        data.extend(colour(pixel))
    # Offsets count from the end of the table; a row equal to the one above
    # shares its data.
    offsets, body, last = [], bytearray(), None
    for row in rows:
        encoded = encode_row(row)
        if encoded != last:
            offsets.append(len(body))
            body.extend(encoded)
            last = encoded
        else:
            offsets.append(offsets[-1])
    data.extend(struct.pack('<%dI' % h, *offsets))
    data.extend(body)
    return bytes(data)


def encode_image(image, sti2=False):
    """STI1 unless `sti2`; then the smallest of STI1, STI2 direct and STI2
    indexed, in that order on a tie."""
    forms = [encode_sti1(image)]
    if sti2:
        forms += [encode_sti2(image), encode_sti2(image, indexed=True)]
    return min((form for form in forms if form is not None), key=len)

