from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT
SOURCE = ROOT / ".build"
ASSETS = ROOT / "assets"
SHEET = ASSETS / "neko-spritesheet.png"
BG_IMAGE = ASSETS / "room-empty.png"
PACKAGE = ROOT / "dist" / "Neko_Clima_BR_Demo.stheme"
PREVIEW = ROOT / "docs" / "images" / "preview.png"
PREVIEW_GIF = ROOT / "docs" / "images" / "preview-animation.gif"
SCENE = SOURCE / "images" / "room-weather-demo.png"
FRAME_SIZE = (128, 128)
CANVAS = (240, 240)
BG = "#160f2c"
YELLOW = "#ffe06a"
WHITE = "#fff4dc"
CYAN = "#8fe6ff"
PURPLE = "#d7b5ff"
SEAFOAM = "#b8e9d0"
RAIN_BLUE = "#62c5f5"
HUMIDITY_BLUE = "#74d3ff"
SOFT_WHITE = "#e8f3ff"
STORM_ORANGE = "#ff985e"

sys.path.insert(0, str(ROOT / "tools"))
from sti_codec import encode_image  # noqa: E402


def load_location() -> dict:
    """Read private local settings, otherwise use the public demo location."""
    config_path = ROOT / "config.local.json"
    if not config_path.exists():
        config_path = ROOT / "config.example.json"
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    label = config.get("city_label")
    latitude = config.get("latitude")
    longitude = config.get("longitude")
    timezone = config.get("timezone")
    if not isinstance(label, str) or not label.strip() or len(label) > 20:
        raise ValueError("city_label must be a short display label (max 20 characters)")
    if isinstance(latitude, bool) or not isinstance(latitude, (int, float)) or not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if isinstance(longitude, bool) or not isinstance(longitude, (int, float)) or not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    if not isinstance(timezone, str) or not timezone or len(timezone) > 48:
        raise ValueError("timezone must be a valid IANA timezone name")
    return {"city_label": label.strip(), "latitude": latitude,
            "longitude": longitude, "timezone": timezone}


def unpack(package: bytes) -> dict[str, bytes]:
    count = struct.unpack_from("<H", package, 4)[0]
    offset = 8
    files: dict[str, bytes] = {}
    for _ in range(count):
        name_len, data_len = struct.unpack_from("<HI", package, offset)
        offset += 6
        name = package[offset:offset + name_len].decode("ascii")
        offset += name_len
        files[name] = package[offset:offset + data_len]
        offset += data_len
    if offset != len(package):
        raise ValueError("Unexpected trailing data in base theme")
    return files


def make_frames() -> tuple[Image.Image, list[Image.Image]]:
    sheet = Image.open(SHEET).convert("RGBA")
    if abs(sheet.width / sheet.height - 2.0) > 0.01:
        raise ValueError(f"Expected a 4x2 sheet, got {sheet.size}")

    def tile(index: int) -> Image.Image:
        row, col = divmod(index, 4)
        box = (
            round(col * sheet.width / 4),
            round(row * sheet.height / 2),
            round((col + 1) * sheet.width / 4),
            round((row + 1) * sheet.height / 2),
        )
        return sheet.crop(box).resize(FRAME_SIZE, Image.Resampling.LANCZOS)

    # Keep the complete body and cushion perfectly static. Animate only a
    # small crop around the eyes so no part of the character can be displaced
    # or clipped by the screen edge.
    opened, half, closed = tile(0), tile(1), tile(2)
    eye_box = (42, 20, 103, 57)
    blink_dir = SOURCE / "animations" / "neko-blink"
    blink_dir.mkdir(parents=True, exist_ok=True)
    # Keep the original sleepy, grumpy half-lidded face and body. Brighten
    # only existing amber iris pixels; preserve their original size and shape.
    base = half.copy()
    iris_mask = Image.new("L", FRAME_SIZE, 0)
    iris_draw = ImageDraw.Draw(iris_mask)
    iris_draw.ellipse((51, 25, 76, 44), fill=255)
    iris_draw.ellipse((75, 27, 101, 46), fill=255)
    eye_highlight = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    pixels = base.load()
    bright_pixels = eye_highlight.load()
    selected = iris_mask.load()
    for yy in range(FRAME_SIZE[1]):
        for xx in range(FRAME_SIZE[0]):
            if not selected[xx, yy]:
                continue
            red, green, blue, alpha = pixels[xx, yy]
            if alpha and red > green * 1.28 and green > blue * 1.35 and red > 80:
                # Preserve the source silhouette exactly; use a fixed vivid
                # gold in a transparent overlay so indexed compression cannot
                # blend the tiny iris back into the dark fur.
                # 30% lower perceived luminance than the prior orange.
                pixels[xx, yy] = (218, 131, 29, alpha)
                bright_pixels[xx, yy] = (218, 131, 29, alpha)
    eye_window = Image.new("L", (eye_box[2]-eye_box[0], eye_box[3]-eye_box[1]), 0)
    eye_draw = ImageDraw.Draw(eye_window)
    eye_draw.ellipse((9, 5, 34, 24), fill=255)
    eye_draw.ellipse((33, 7, 59, 26), fill=255)
    base_patch = eye_highlight.crop(eye_box).copy()
    closed_patch = closed.crop(eye_box).copy()
    closed_patch.putalpha(ImageChops.multiply(closed_patch.getchannel("A"), eye_window))
    frames = [base_patch.copy() for _ in range(17)] + [closed_patch]
    for target, frame in enumerate(frames):
        # The blink patch needs only a compact eye palette. This lets the
        # firmware store it as indexed STI2 instead of 3-byte true-colour runs.
        reduced = frame.convert("RGB").quantize(colors=8, dither=Image.Dither.NONE).convert("RGB")
        alpha = frame.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
        reduced.putalpha(alpha)
        frames[target] = reduced
        reduced.save(SOURCE / "animations" / "neko-blink" / f"{target:03}.png", optimize=True)
    base.save(SOURCE / "images" / "neko-static.png", optimize=True)
    return base, frames



def make_weather_animations() -> dict[str, list[Image.Image]]:
    """Rain is baked into the window-glass crop; warm lantern glow flickers."""
    rain_dir = SOURCE / "animations" / "weather" / "rain"
    fire_dir = SOURCE / "animations" / "weather" / "fire"
    rain_dir.mkdir(parents=True, exist_ok=True)
    fire_dir.mkdir(parents=True, exist_ok=True)

    rw, rh = 160, 96
    window = Image.open(SCENE).convert("RGBA").crop((52, 78, 52 + rw, 78 + rh))
    mask = Image.new("L", (rw, rh), 0)
    md = ImageDraw.Draw(mask)
    # Glass panes only, excluding frames, sill, desk and lanterns.
    for poly in [
        [(0, 29), (37, 19), (37, 70), (0, 74)],
        [(42, 18), (84, 10), (84, 69), (42, 71)],
        [(91, 9), (106, 6), (107, 68), (91, 69)],
        [(116, 6), (136, 5), (138, 66), (116, 67)],
        [(144, 6), (159, 9), (159, 64), (144, 66)],
    ]: md.polygon(poly, fill=255)
    # The telescope crosses the glass; keep rain behind its silhouette.
    md.polygon([(55, 49), (65, 41), (76, 43), (84, 34), (92, 30),
                (101, 36), (111, 40), (124, 35), (132, 46),
                (125, 58), (111, 55), (101, 61), (88, 65), (74, 62), (62, 59)], fill=0)
    # Foreground table lanterns are cut out of the moving rain pass. Their
    # original pixels are also redrawn above the rain as a separate layer.
    md.polygon([(103, 53), (108, 49), (115, 50), (120, 55), (123, 61),
                (122, 70), (118, 76), (105, 76), (101, 70), (101, 61)], fill=0)
    md.polygon([(145, 21), (153, 19), (159, 23), (165, 29), (168, 40),
                (171, 50), (168, 58), (160, 63), (149, 62), (143, 57),
                (141, 47), (143, 38), (140, 31)], fill=0)
    # Keep warm, bright city lights untouched even where they sit behind glass.
    pix = window.load(); mp = mask.load()
    for y in range(rh):
        for x in range(rw):
            r, g, b, _ = pix[x, y]
            if r > 105 and r > g * 1.22 and g > b * 1.12:
                mp[x, y] = 0
    rain_frames: list[Image.Image] = []
    for frame in range(24):
        drops = Image.new("RGBA", (rw, rh), (0, 0, 0, 0)); dd = ImageDraw.Draw(drops)
        # 24 frames at 6 FPS move every drop down 4 px (24 px/s). The 96 px
        # travel is exactly the frame height, so the loop seam is continuous.
        sway = (0, 0, 1, 1, 1, 1, 0, 0, -1, -1, -1, -1,
                0, 0, 1, 1, 1, 1, 0, 0, -1, -1, -1, -1)[frame]
        for i in range(64):
            x = 3 + (i * 37 + (i % 5) * 11) % (rw - 6)
            y = (i * 29 + 7 + frame * 4) % rh
            dd.line((x + sway, y, x + sway - 1, y + 5), fill=(220, 240, 255, 135 + (i * 17) % 90), width=1)
        drops.putalpha(ImageChops.multiply(drops.getchannel("A"), mask))
        drops.save(rain_dir / f"{frame:03}.png", optimize=True)
        rain_frames.append(drops)

    fw, fh = 180, 44
    centers = ((16, 19), (165, 19))
    fire_frames: list[Image.Image] = []
    for frame in range(8):
        glow = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        pixels = glow.load()
        phase = 2 * math.pi * frame / 8
        for lamp_index, (cx, cy) in enumerate(centers):
            lamp_phase = phase + lamp_index * 0.7
            intensity = int(88 + 24 * math.sin(lamp_phase) + 10 * math.sin(2 * lamp_phase + 0.6))
            green = int(136 + 5 * math.sin(lamp_phase + 0.3))
            jx = (0, 1, 1, 0, -1, -1, 0, 0)[frame]
            jy = (0, -1, 0, 1, 1, 0, -1, 0)[frame]
            for y in range(max(0, cy + jy - 17), min(fh, cy + jy + 18)):
                for x in range(max(0, cx + jx - 17), min(fw, cx + jx + 18)):
                    dx, dy = x - (cx + jx), y - (cy + jy)
                    # Uneven oval gradient reads as flame light, not a round dot.
                    radius = (dx / (13 if dy < 0 else 17)) ** 2 + (dy / 15) ** 2
                    if radius <= 1:
                        alpha = int(intensity * (1 - radius) ** 1.5)
                        if alpha: pixels[x, y] = (255, green, 42, alpha)
        glow.save(fire_dir / f"{frame:03}.png", optimize=True)
        fire_frames.append(glow)
    return {"rain": rain_frames, "fire": fire_frames}


def make_weather_icons() -> dict[str, Image.Image]:
    """Draw small, clear weather pictograms for conditional image layers."""
    scale = 3
    icons: dict[str, Image.Image] = {}
    palette = {
        "sunny": (255, 211, 78), "partly": (255, 211, 78),
        "cloudy": (143, 230, 255), "fog": (143, 230, 255),
        "rain": (116, 211, 255),
        "snow": (232, 243, 255), "showers": (116, 211, 255),
        "storm": (255, 152, 94),
    }

    def make(name: str) -> Image.Image:
        im = Image.new("RGBA", (16 * scale, 16 * scale), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)

        def p(v: int) -> int:
            return v * scale

        def sun(cx: int, cy: int, r: int = 3, color=None) -> None:
            col = color or palette[name]
            d.ellipse((p(cx-r), p(cy-r), p(cx+r), p(cy+r)), fill=col)
            for dx, dy in ((0,-1),(0,1),(-1,0),(1,0),(-1,-1),(1,-1),(-1,1),(1,1)):
                d.line((p(cx+dx*(r+1)), p(cy+dy*(r+1)), p(cx+dx*(r+2)), p(cy+dy*(r+2))), fill=col, width=scale)

        def cloud(top: int = 5, color=None) -> None:
            col = color or palette[name]
            d.ellipse((p(2), p(top+3), p(9), p(top+10)), fill=col)
            d.ellipse((p(6), p(top), p(13), p(top+9)), fill=col)
            d.ellipse((p(9), p(top+4), p(15), p(top+10)), fill=col)
            d.rounded_rectangle((p(3), p(top+6), p(14), p(top+11)), radius=p(2), fill=col)

        if name == "sunny":
            sun(8, 8, 5)
        elif name == "partly":
            sun(6, 5, 4)
            cloud(6, (219, 241, 255))
        elif name == "cloudy":
            cloud(4)
        elif name == "fog":
            cloud(2)
            for yy in (13, 15):
                d.line((p(2), p(yy), p(13), p(yy)), fill=palette[name], width=scale)
        elif name == "drizzle":
            cloud(2)
            d.ellipse((p(5), p(13), p(6), p(15)), fill=palette[name])
            d.ellipse((p(10), p(13), p(11), p(15)), fill=palette[name])
        elif name == "rain":
            cloud(1)
            for xx in (4, 8, 12):
                d.line((p(xx+1), p(12), p(xx-1), p(15)), fill=palette[name], width=scale)
        elif name == "snow":
            cloud(0)
            for xx in (4, 8, 12):
                cy = 13
                d.line((p(xx), p(cy-2), p(xx), p(cy+2)), fill=palette[name], width=scale)
                d.line((p(xx-2), p(cy), p(xx+2), p(cy)), fill=palette[name], width=scale)
                d.line((p(xx-1), p(cy-1), p(xx+1), p(cy+1)), fill=palette[name], width=scale)
        elif name == "showers":
            cloud(1)
            for xx in (5, 11):
                d.line((p(xx+1), p(12), p(xx-1), p(15)), fill=palette[name], width=scale)
        elif name == "storm":
            cloud(1, (143, 230, 255))
            d.polygon([(p(9),p(10)),(p(6),p(14)),(p(9),p(14)),(p(8),p(16)),(p(12),p(12)),(p(9),p(12))], fill=palette[name])
        icons[name] = im.resize((16, 16), Image.Resampling.LANCZOS)
    for key in palette:
        make(key)
        icons[key] = icons[key].resize((24, 24), Image.Resampling.LANCZOS)
    return icons

def text_layer(ident: str, x: int, y: int, value: str, color: str, size: int = 8) -> dict:
    return {"id": ident, "type": "text", "x": x, "y": y, "value": value,
            "size": size, "color": color}


def visible_layer(ident: str, x: int, y: int, label: str, color: str,
                  source: str, *, codes: list[int] | None = None,
                  minimum: int | None = None, maximum: int | None = None) -> dict:
    condition = {"source": source}
    if codes is not None:
        condition["codes"] = codes
    else:
        condition["min"] = minimum
        condition["max"] = maximum
    return {
        "id": ident, "type": "text", "x": x, "y": y, "value": label,
        "size": 14, "color": color, "visibleWhen": condition,
    }


def weather_text_layer(ident: str, label: str, color: str,
                       codes: list[int]) -> dict:
    return {
        "id": ident, "type": "text", "x": 131, "y": 202,
        "value": label, "size": 14, "color": color,
        "visibleWhen": {"source": "w.c", "codes": codes},
    }


def status_marker(ident: str, y: int, source: str, color: str,
                  stops: list[tuple[int, str]]) -> dict:
    return {
        "id": ident, "type": "shape", "shape": "rectangle", "x": 131, "y": y,
        "width": 2, "height": 7, "cornerRadius": 1, "fill": color,
        "bind": {"fill": {"source": source,
                           "stops": [{"at": at, "value": value} for at, value in stops]}},
    }


def make_manifest() -> dict:
    location = load_location()
    panel = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    card_fill = (22, 15, 44, 72)
    card_edge = (186, 125, 230, 150)
    pd.rounded_rectangle((96, 134, 238, 191), radius=8,
                         fill=card_fill, outline=card_edge, width=1)
    pd.rounded_rectangle((96, 195, 238, 239), radius=8,
                         fill=card_fill, outline=card_edge, width=1)
    # A small translucent bridge links the two compact cards.
    pd.rectangle((105, 188, 113, 196), fill=card_fill)
    panel.save(SOURCE / "images" / "weather-panel.png", optimize=True)
    scene = ImageOps.fit(Image.open(BG_IMAGE).convert("RGBA"), CANVAS,
                         method=Image.Resampling.LANCZOS)
    scene.save(SCENE, optimize=True)
    scene.save(SOURCE / "images" / "room-weather.png", optimize=True)

    # Restore the two foreground lantern silhouettes after rain is drawn.
    # The panel remains a distinct layer above both the rain and lanterns.
    lantern_box = (154, 98, 224, 158)
    lantern_source = scene.crop(lantern_box)
    lantern_mask = Image.new("L", lantern_source.size, 0)
    lm = ImageDraw.Draw(lantern_mask)
    lm.polygon([(47, 1), (54, 0), (57, 5), (63, 8), (65, 15),
                (69, 22), (68, 34), (65, 41), (60, 45), (49, 44),
                (43, 40), (41, 33), (42, 23), (44, 16), (42, 9)], fill=255)
    lm.polygon([(4, 35), (7, 30), (13, 30), (17, 35), (19, 41),
                (19, 51), (16, 55), (5, 55), (1, 51), (1, 43)], fill=255)
    lantern_foreground = Image.new("RGBA", lantern_source.size, (0, 0, 0, 0))
    lantern_foreground.paste(lantern_source, (0, 0), lantern_mask)
    foreground = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    foreground.alpha_composite(lantern_foreground, lantern_box[:2])
    foreground.alpha_composite(panel)
    foreground.save(SOURCE / "images" / "scene-foreground.png", optimize=True)

    layers: list[dict] = [
        {"id": "room", "type": "image", "x": 0, "y": 0, "source": "images/room-weather.png"},
        {"id": "window-rain", "type": "animation", "x": 52, "y": 78, "width": 160, "height": 96,
         "source": "animations/weather/rain", "frames": 24, "fps": 6, "loop": True},
        {"id": "scene-foreground", "type": "image", "x": 0, "y": 0, "source": "images/scene-foreground.png"},
        {"id": "lamp-flicker", "type": "animation", "x": 0, "y": 115, "width": 180, "height": 44,
         "source": "animations/weather/fire", "frames": 8, "fps": 4, "loop": True},
        {"id": "neko-static", "type": "image", "x": 2, "y": 100, "source": "images/neko-static.png"},
        {"id": "neko-blink", "type": "animation", "x": 44, "y": 120, "width": 61, "height": 37,
         "source": "animations/neko-blink", "frames": 18, "fps": 2, "loop": True},
        {"id": "clock", "type": "text", "x": 120, "y": 18, "anchor": "top-center",
         "value": "{HH}:{MM}", "size": 32, "color": WHITE},
    ]

    # Use the device's synchronized local clock directly; the old external
    # month endpoint redirected HTTP to HTTPS and produced the "--" field.
    date = text_layer("date", 120, 58, "{WD}, {DD} {MON} {YYYY}", PURPLE, 16)
    date["anchor"] = "top-center"
    layers.append(date)

    # A consistent readout followed by a separated pair of color-coded
    # weather/air status rows. Sentence case softens the bitmap UI.
    temperature = text_layer("temperature", 107, 154, "Temp {w.t}C", YELLOW, 14)
    temperature["bind"] = {"color": {"source": "w.t", "stops": [
        {"at": -5, "value": "#8fe6ff"},
        {"at": 5, "value": "#8fe6ff"},
        {"at": 15, "value": "#d7efff"},
        {"at": 20, "value": "#fff4dc"},
        {"at": 27, "value": YELLOW},
        {"at": 34, "value": "#ff925e"},
    ]}}
    layers.extend([
        text_layer("city", 107, 136, location["city_label"], "#fff4dc", 14),
        temperature,
        text_layer("humidity", 107, 172, "Umid {w.h}%", HUMIDITY_BLUE, 14),
    ])

    # Open-Meteo uses WMO weather codes. Half-step boundaries keep each
    # integer code in exactly one category despite linear color interpolation.
    code = "w.c"
    layers.extend([
        {"id":"icon-sunny","type":"image","x":102,"y":198,"source":"i/s","visibleWhen":{"source":code,"codes":[0,1]}},
        {"id":"icon-partly","type":"image","x":102,"y":198,"source":"i/p","visibleWhen":{"source":code,"codes":[2]}},
        {"id":"icon-cloudy","type":"image","x":102,"y":198,"source":"i/c","visibleWhen":{"source":code,"codes":[3]}},
        {"id":"icon-fog","type":"image","x":102,"y":198,"source":"i/f","visibleWhen":{"source":code,"codes":[45,48]}},
        {"id":"icon-rain","type":"image","x":102,"y":198,"source":"i/r","visibleWhen":{"source":code,"codes":[51,53,55,56,57,61,63,65]}},
        {"id":"icon-snow","type":"image","x":102,"y":198,"source":"i/n","visibleWhen":{"source":code,"codes":[71,73,75,77,85,86]}},
        {"id":"icon-showers","type":"image","x":102,"y":198,"source":"i/h","visibleWhen":{"source":code,"codes":[66,67,80,81,82]}},
        {"id":"icon-storm","type":"image","x":102,"y":198,"source":"i/t","visibleWhen":{"source":code,"codes":[95,96,99]}},
        weather_text_layer("weather-sunny", "Ensolarado", YELLOW, [0, 1]),
        weather_text_layer("weather-partly", "Parc nublado", YELLOW, [2]),
        weather_text_layer("weather-cloudy", "Nublado", SOFT_WHITE, [3]),
        weather_text_layer("weather-fog", "Nevoeiro", CYAN, [45, 48]),
        weather_text_layer("weather-drizzle", "Garoa", RAIN_BLUE, [51, 53, 55, 56, 57]),
        weather_text_layer("weather-rain", "Chuva", RAIN_BLUE, [61, 63, 65, 66, 67]),
        weather_text_layer("weather-snow", "Neve", SOFT_WHITE, [71, 73, 75, 77, 85, 86]),
        weather_text_layer("weather-showers", "Pancadas", RAIN_BLUE, [80, 81, 82]),
        weather_text_layer("weather-storm", "Temporal", STORM_ORANGE, [95, 96, 99]),
        visible_layer("comfort-cool", 107, 224, "Frio", CYAN, "w.a", minimum=-80, maximum=17.9),
        visible_layer("comfort-good", 107, 224, "Confortavel", SEAFOAM, "w.a", minimum=18, maximum=26),
        visible_layer("comfort-hot", 107, 224, "Quente", STORM_ORANGE, "w.a", minimum=26.1, maximum=80),
    ])
    if len(layers) > 32:
        raise ValueError(f"Theme exceeds firmware's 32-layer limit: {len(layers)}")

    url = ("http://api.open-meteo.com/v1/forecast?"
           f"latitude={location['latitude']}&longitude={location['longitude']}"
           "&current=temperature_2m,relative_humidity_2m,weather_code,apparent_temperature"
           f"&timezone={quote(location['timezone'], safe='')}")
    return {
        "spec": 2,
        "theme": {"id": "neko-clima-br-stavel", "name": "Neko Clima BR Demo",
        "author": "Neko Clock Project", "version": "12.23.0"},
        "display": {"width": 240, "height": 240, "background": "#080719"},
        "data": [
            {"id": "w", "url": url, "interval": 300,
             "fields": [{"id": "t", "path": "current.temperature_2m"},
                        {"id": "h", "path": "current.relative_humidity_2m"},
                        {"id": "c", "path": "current.weather_code"},
                        {"id": "a", "path": "current.apparent_temperature"}]},
        ],
        "layers": layers,
    }


def render_preview(frames: list[Image.Image], weather_frames: dict[str, list[Image.Image]],
                   weather_icons: dict[str, Image.Image]) -> None:
    location = load_location()
    font_path = Path("/mnt/c/Windows/Fonts/consola.ttf")
    if not font_path.exists():
        font_path = Path(r"C:\Windows\Fonts\consola.ttf")
    font = lambda n: ImageFont.truetype(str(font_path), n) if font_path.exists() else ImageFont.load_default()

    foreground = Image.open(SOURCE / "images" / "scene-foreground.png").convert("RGBA")
    cat = Image.open(SOURCE / "images" / "neko-static.png").convert("RGBA")
    blink_box = (44, 120, 105, 157)
    def draw_frame(index: int) -> Image.Image:
        canvas = Image.open(SCENE).convert("RGBA")
        canvas.alpha_composite(weather_frames["rain"][(index // 2) % 24], (52, 78))
        canvas.alpha_composite(foreground)
        canvas.alpha_composite(weather_frames["fire"][(index // 3) % 8], (0, 115))
        canvas.alpha_composite(cat, (2, 100))
        canvas.alpha_composite(frames[(index // 6) % 18], blink_box[:2])
        draw = ImageDraw.Draw(canvas)
        draw.text((24, 58), "Ter, 03 Nov 2026", fill=PURPLE, font=font(16))
        draw.text((107, 136), location["city_label"], fill=WHITE, font=font(14))
        draw.text((107, 154), "Temp 22.0C", fill=YELLOW, font=font(14))
        draw.text((107, 172), "Umid 48%", fill=HUMIDITY_BLUE, font=font(14))
        canvas.alpha_composite(weather_icons["sunny"], (102, 198))
        draw.text((131, 202), "Ensolarado", fill=YELLOW, font=font(14))
        draw.text((107, 224), "Confortavel", fill=SEAFOAM, font=font(14))
        draw.text((75, 16), "18:15", fill=WHITE, font=font(32))
        return canvas

    draw_frame(0).convert("RGB").save(PREVIEW)
    animated = []
    for i in range(108):
        animated.append(draw_frame(i).convert("RGB").quantize(colors=256))
    animated[0].save(PREVIEW_GIF, save_all=True, append_images=animated[1:],
                      duration=83, loop=0, disposal=2)


def main() -> None:
    (SOURCE / "images").mkdir(parents=True, exist_ok=True)
    (ROOT / "dist").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "images").mkdir(parents=True, exist_ok=True)
    manifest = make_manifest()
    cat, frames = make_frames()
    weather_frames = make_weather_animations()
    weather_icons = make_weather_icons()
    if len(manifest["layers"]) > 32:
        raise ValueError(f"Theme exceeds firmware's 32-layer limit: {len(manifest['layers'])}")
    manifest_bytes = json.dumps(manifest, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    (SOURCE / "theme.json").write_bytes(manifest_bytes)
    room = Image.open(SCENE).convert("RGBA")
    entries: dict[str, bytes] = {
        "theme.json": manifest_bytes,
        "images/room-weather.png.sti": encode_image(room, True),
        "images/scene-foreground.png.sti": encode_image(Image.open(SOURCE / "images" / "scene-foreground.png").convert("RGBA"), True),
        "images/neko-static.png.sti": encode_image(cat, True),
    }
    for i, frame in enumerate(frames):
        entries[f"animations/neko-blink/{i:03}.png.sti"] = encode_image(frame, True)
    for group, group_frames in weather_frames.items():
        for i, frame in enumerate(group_frames):
            entries[f"animations/weather/{group}/{i:03}.png.sti"] = encode_image(frame, True)
    icon_paths = {"sunny":"s", "partly":"p", "cloudy":"c", "fog":"f", "rain":"r", "snow":"n", "showers":"h", "storm":"t"}
    for name, icon in weather_icons.items():
        entries[f"i/{icon_paths[name]}.sti"] = encode_image(icon, True)

    package = bytearray(b"STH1" + struct.pack("<HH", len(entries), 0))
    for name, payload in entries.items():
        encoded_name = name.encode("ascii")
        package.extend(struct.pack("<HI", len(encoded_name), len(payload)))
        package.extend(encoded_name)
        package.extend(payload)
    PACKAGE.write_bytes(package)
    render_preview(frames, weather_frames, weather_icons)
    print(f"PACKAGE={PACKAGE.resolve()}")
    print(f"PACKAGE_BYTES={PACKAGE.stat().st_size}")
    print(f"MANIFEST_BYTES={len(manifest_bytes)}")
    print(f"LAYERS={len(manifest['layers'])}")
    print(f"FRAMES={len(frames)}")
    print(f"PREVIEW={PREVIEW.resolve()}")
    print(f"PREVIEW_GIF={PREVIEW_GIF.resolve()}")


if __name__ == "__main__":
    main()
