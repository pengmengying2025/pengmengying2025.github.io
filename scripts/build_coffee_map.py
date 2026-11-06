#!/usr/bin/env python3
"""Regenerate the Coffee Atlas maps on the Elsewhere page.

After changing the map in Google My Maps, export it as KMZ (whole map), save it over
the old file in Dropbox, run this, then commit _includes/coffee-atlas-japan.svg and
_includes/coffee-atlas-usa.svg:

    python3 scripts/build_coffee_map.py

The KMZ is only read and stays out of the repo. Cafés are sorted by their My Maps icon:
the heart is "loved", the star is "daily coffee", and the square is left off the map.
An icon the script does not know stops it, so a new kind never drops out unnoticed.
Only Japan and the contiguous United States are drawn; the script names any café
outside them and leaves it off. Cafés around Tokyo go into an enlarged inset.

Each café's latitude and longitude are rounded to two decimals (about a kilometre)
before anything is drawn, so the SVGs hold no finer position than that. Names are
not written to the SVGs.

Outlines come from Natural Earth 5.1.2, which is public domain and needs no credit:
Japan from the edition drawn from Japan's point of view (it counts the Northern
Territories as Japanese), the United States from the 1:50m countries with lakes, and
Tokyo from the 1:10m states and provinces. The first run creates a private virtual
environment and downloads these files (about 48 MB) into
~/.cache/academic-homepage-coffee-map. Output is reproducible: the same KMZ gives
identical files.
"""

import argparse
import hashlib
import math
import os
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_includes"
KMZ = Path.home() / "Dropbox" / "个人主页用" / "Mengying’s Coffee Map.kmz"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "academic-homepage-coffee-map"
VENV = CACHE / "venv"
REQUIREMENTS = ["pyshp==2.3.1"]

# Natural Earth files at this exact tag of github.com/nvkelso/natural-earth-vector, with their SHA-256.
NATURAL_EARTH = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/"
NATURAL_EARTH_FILES = {
    "10m_cultural/ne_10m_admin_0_countries_jpn.shp": "b32931a3158d8a6d24cd661d30d389da32b357cc8fe7e12b5b05139b47249e5b",
    "10m_cultural/ne_10m_admin_0_countries_jpn.shx": "e816774f88dc1c6fb560c47cb5890a6056f9193f3559e034b177d60e1e1a4d90",
    "10m_cultural/ne_10m_admin_0_countries_jpn.dbf": "7af028205de4939a1f2deea0d4b66019f00074c81d962edbbf5fdc5886051bea",
    "50m_cultural/ne_50m_admin_0_countries_lakes.shp": "9d31cfcbb1f483f55eb5a14674e718289bff48db27a073af59d2809a135fc619",
    "50m_cultural/ne_50m_admin_0_countries_lakes.shx": "a56e3e20245d1dc1e014009b7a743dd9a66e1d341ca1eda3c7e254e025e1259d",
    "50m_cultural/ne_50m_admin_0_countries_lakes.dbf": "4ec70fc63842df719ee1f9f7bb0469b528b1eab8099c44aea6c7339a10cacc4b",
    "10m_cultural/ne_10m_admin_1_states_provinces.shp": "c6f5c8b4b1320d9417033762419c6df1eb423989cd880fba78ea0b1e3522cbe4",
    "10m_cultural/ne_10m_admin_1_states_provinces.shx": "37a9e2bc79ed31d3bdea3cb62d928f77281a1c88d645cd33430231c75dbcf350",
    "10m_cultural/ne_10m_admin_1_states_provinces.dbf": "445a8a9bea889634faf0af18081830df0b05b8471fc6af8dc42aecdd7a71bba1",
}

# My Maps names each style after its icon number: icon-1592-E65100-... is the orange heart.
KINDS = {"1592": "loved", "1502": "daily", "1500": None}  # heart, star, square (left off)

# What each map covers, as (west, south, east, north) in degrees.
JAPAN_AREA = (128.0, 30.0, 150.0, 46.0)  # the four main islands and nearby ones; Okinawa and Ogasawara have no cafés
USA_AREA = (-126.0, 24.0, -66.0, 50.0)  # the contiguous states

# Colors: the site's accent and primary for the dots, a warm grey for land.
COLORS = {"loved": "#B7533B", "daily": "#233B40"}
LAND = "#E9E3DA"
BACKGROUND = "#FCFAF7"
FRAME = "#C9C0B3"

# Sizes in SVG units. Both maps are the same number of units tall, so side by side at the
# same height their dots and lines come out the same size.
HEIGHT = 400
MARGIN = 8
DOT = 4.2
DOT_RING = 1.2  # the light ring that keeps touching dots apart
SIMPLIFY = 0.45  # outline detail finer than this is dropped
SMALLEST_ISLAND = 2.5  # square units
INSET_WIDTH = 0.42  # the Tokyo inset's share of the Japan map's width
INSET_PADDING = 10


def run_in_private_venv():
    """Re-launch this script inside the cached virtual environment."""
    if Path(sys.prefix).resolve() == VENV.resolve():
        return
    python = VENV / "bin" / "python"
    if not python.exists():
        print("Creating the map tools environment (first run only)...")
        CACHE.mkdir(parents=True, exist_ok=True)
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    subprocess.check_call(
        [str(python), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", *REQUIREMENTS]
    )
    os.execv(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]])


def natural_earth(name):
    """Return a shapefile reader for one Natural Earth layer, downloading it on first use."""
    import shapefile

    folder = CACHE / "natural-earth-5.1.2"
    folder.mkdir(parents=True, exist_ok=True)
    for path, digest in NATURAL_EARTH_FILES.items():
        if Path(path).stem != name:
            continue
        local = folder / Path(path).name
        if not local.exists():
            print(f"Downloading {local.name}...")
            request = urllib.request.Request(NATURAL_EARTH + path, headers={"User-Agent": "academic-homepage-coffee-map"})
            with urllib.request.urlopen(request, timeout=120) as response:
                local.write_bytes(response.read())
        if hashlib.sha256(local.read_bytes()).hexdigest() != digest:
            local.unlink()
            sys.exit(f"{local.name} did not match its checksum and was deleted; run the script again.")
    return shapefile.Reader(str(folder / name), encoding="utf-8")


def read_cafes(kmz):
    """Return (kind, longitude, latitude, name, layer) for every place in the KMZ."""
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    with zipfile.ZipFile(kmz) as archive:
        document = ET.fromstring(archive.read("doc.kml"))
    cafes, unknown = [], []
    for folder in document.iter(f"{{{ns['k']}}}Folder"):
        layer = folder.findtext("k:name", default="", namespaces=ns)
        for place in folder.iterfind("k:Placemark", ns):
            name = (place.findtext("k:name", default="", namespaces=ns) or "").strip()
            style = place.findtext("k:styleUrl", default="", namespaces=ns)
            icon = re.match(r"#icon-(\d+)-", style)
            coordinates = place.findtext(".//k:Point/k:coordinates", default="", namespaces=ns).split(",")
            if not icon or icon.group(1) not in KINDS or len(coordinates) < 2:
                unknown.append(f"{name} ({style or 'no style'}, layer {layer})")
                continue
            lon, lat = float(coordinates[0]), float(coordinates[1])
            cafes.append((KINDS[icon.group(1)], lon, lat, name, layer))
    if unknown:
        sys.exit("Unknown icon or no point, so nothing was written:\n  " + "\n  ".join(unknown))
    return cafes


def inside(area, lon, lat):
    west, south, east, north = area
    return west <= lon <= east and south <= lat <= north


def equirectangular(middle_latitude):
    """Plain longitude and latitude, with longitude shrunk to its true length at the middle latitude."""
    shrink = math.cos(math.radians(middle_latitude))
    return lambda lon, lat: (lon * shrink, -lat)


def albers_usa(lon, lat):
    """Albers equal-area conic with the usual parallels for the contiguous United States."""
    first, second, origin_lat, origin_lon = map(math.radians, (29.5, 45.5, 23.0, -96.0))
    n = (math.sin(first) + math.sin(second)) / 2
    c = math.cos(first) ** 2 + 2 * n * math.sin(first)
    rho0 = math.sqrt(c - 2 * n * math.sin(origin_lat)) / n
    rho = math.sqrt(c - 2 * n * math.sin(math.radians(lat))) / n
    theta = n * (math.radians(lon) - origin_lon)
    return rho * math.sin(theta), rho * math.cos(theta) - rho0  # SVG's y grows downward


def rings_of(reader, field, value, area):
    """Return the outline rings of one record whose bounding boxes fall inside the area."""
    for index, record in enumerate(reader.iterRecords(fields=[field])):
        if record[field] == value:
            shape = reader.shape(index)
            break
    else:
        sys.exit(f"No {field} = {value} in the Natural Earth file")
    ends = list(shape.parts) + [len(shape.points)]
    rings = []
    for start, end in zip(ends, ends[1:]):
        ring = shape.points[start:end]
        lons, lats = [p[0] for p in ring], [p[1] for p in ring]
        if inside(area, min(lons), min(lats)) and inside(area, max(lons), max(lats)):
            rings.append(ring)
    return rings


def area_of(ring):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]))) / 2


def simplified(points, tolerance):
    """Douglas-Peucker on a closed ring; the first point stays."""
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        (ax, ay), (bx, by) = points[start], points[end]
        length = math.hypot(bx - ax, by - ay)
        farthest, distance = None, tolerance
        for i in range(start + 1, end):
            px, py = points[i]
            d = abs((bx - ax) * (ay - py) - (ax - px) * (by - ay)) / length if length else math.hypot(px - ax, py - ay)
            if d > distance:
                farthest, distance = i, d
        if farthest is not None:
            keep[farthest] = True
            stack += [(start, farthest), (farthest, end)]
    return [p for p, k in zip(points, keep) if k]


class Frame:
    """Places projected coordinates into a box of SVG units."""

    def __init__(self, project, box, rings_or_points, height=None, width=None):
        self.project = project
        xs, ys = zip(*(project(lon, lat) for lon, lat in rings_or_points))
        self.left, self.top = min(xs), min(ys)
        span_x, span_y = max(xs) - self.left, max(ys) - self.top
        self.scale = height / span_y if height else width / span_x
        self.width, self.height = span_x * self.scale, span_y * self.scale
        self.x0, self.y0 = box

    def __call__(self, lon, lat):
        x, y = self.project(lon, lat)
        return self.x0 + (x - self.left) * self.scale, self.y0 + (y - self.top) * self.scale


def outline_path(rings, place):
    """Return SVG path data for the rings, simplified and without specks."""
    parts = []
    for ring in rings:
        points = [place(lon, lat) for lon, lat in ring]
        if area_of(points) < SMALLEST_ISLAND:
            continue
        points = simplified(points, SIMPLIFY)
        if len(points) < 4:
            continue
        numbers = " ".join(f"{x:.1f} {y:.1f}" for x, y in points[:-1])
        parts.append(f"M{numbers}Z")
    return "".join(parts)


def spread(spots):
    """Nudge dots apart until none overlap, each staying as close to its place as it can.

    Cafés a few streets apart share a rounded position, so without this a cluster
    shows as one dot and hides how many there are. Fixed steps, no randomness:
    the same input gives the same layout.
    """
    home = [list(spot) for spot in spots]
    at = [list(spot) for spot in spots]
    apart = 2 * DOT
    for step in range(400):
        moved = False
        for i in range(len(at)):
            for j in range(i + 1, len(at)):
                dx, dy = at[j][0] - at[i][0], at[j][1] - at[i][1]
                distance = math.hypot(dx, dy)
                if distance >= apart - 0.01:
                    continue
                if distance < 1e-6:  # same spot: part them along a fixed angle
                    dx, dy, distance = math.cos(j * 2.4), math.sin(j * 2.4), 1.0
                push = (apart - distance) / 2
                at[i][0] -= dx / distance * push
                at[i][1] -= dy / distance * push
                at[j][0] += dx / distance * push
                at[j][1] += dy / distance * push
                moved = True
        if step < 300:  # a gentle pull home keeps clusters tight; the last rounds only separate
            for spot, origin in zip(at, home):
                spot[0] += (origin[0] - spot[0]) * 0.05
                spot[1] += (origin[1] - spot[1]) * 0.05
        elif not moved:
            break
    return [tuple(spot) for spot in at]


def dots(cafes, place):
    """Return the dot elements: daily coffee first, so the loved ones sit on top."""
    cafes = sorted(cafes, key=lambda c: (c[2], c[1], c[0]))  # a fixed order, so the layout never changes by itself
    spots = spread([place(lon, lat) for _, lon, lat, *_ in cafes])
    lines = []
    for kind in ("daily", "loved"):
        mine = [spot for spot, cafe in zip(spots, cafes) if cafe[0] == kind]
        if mine:
            circles = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{DOT}"/>' for x, y in mine)
            lines.append(f'<g fill="{COLORS[kind]}">{circles}</g>')
    return lines


def svg(width, body):
    """Wrap the map in an SVG that screen readers skip: the intro, legend and full-map link say what it shows."""
    width = round(width + MARGIN, 1)
    return "\n".join(
        [
            "<!-- Made by scripts/build_coffee_map.py from the Coffee Map KMZ; edit the map, not this file. -->",
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {HEIGHT}" width="{width}" height="{HEIGHT}"'
            ' aria-hidden="true">',
            *body,
            "</svg>",
            "",
        ]
    )


def japan_map(cafes):
    reader = natural_earth("ne_10m_admin_0_countries_jpn")
    japan = rings_of(reader, "ADM0_A3_JP", "JPN", JAPAN_AREA)
    project = equirectangular(38.0)
    country = Frame(project, (MARGIN, MARGIN), [p for ring in japan for p in ring], height=HEIGHT - 2 * MARGIN)
    width = MARGIN + country.width

    tokyo_reader = natural_earth("ne_10m_admin_1_states_provinces")
    tokyo = max(rings_of(tokyo_reader, "iso_3166_2", "JP-13", JAPAN_AREA), key=area_of)  # the mainland, not the islands
    tokyo_project = equirectangular(35.7)
    inset_width = width * INSET_WIDTH - 2 * INSET_PADDING
    tokyo_frame = Frame(tokyo_project, (0, 0), tokyo, width=inset_width)
    frame_w, frame_h = tokyo_frame.width + 2 * INSET_PADDING, tokyo_frame.height + 2 * INSET_PADDING
    frame_x, frame_y = width - frame_w, HEIGHT - MARGIN - frame_h
    tokyo_frame.x0, tokyo_frame.y0 = frame_x + INSET_PADDING, frame_y + INSET_PADDING

    # The area the inset shows, in degrees, so the box on the country map matches it exactly.
    lons, lats = [p[0] for p in tokyo], [p[1] for p in tokyo]
    pad_lon = INSET_PADDING / tokyo_frame.scale / math.cos(math.radians(35.7))
    pad_lat = INSET_PADDING / tokyo_frame.scale
    inset_area = (min(lons) - pad_lon, min(lats) - pad_lat, max(lons) + pad_lon, max(lats) + pad_lat)
    x1, y1 = country(inset_area[0], inset_area[3])
    x2, y2 = country(inset_area[2], inset_area[1])

    in_tokyo = [c for c in cafes if inside(inset_area, c[1], c[2])]
    elsewhere = [c for c in cafes if not inside(inset_area, c[1], c[2])]

    # The inset sits in the open sea; stop if any land that is drawn would fall under it.
    for ring in japan:
        if area_of([country(lon, lat) for lon, lat in ring]) < SMALLEST_ISLAND:
            continue
        for lon, lat in ring:
            x, y = country(lon, lat)
            if frame_x <= x <= frame_x + frame_w and frame_y <= y <= frame_y + frame_h:
                sys.exit(f"The Tokyo inset would cover land at {lat:.2f}, {lon:.2f}; change INSET_WIDTH or the map area.")

    body = [
        f'<path fill="{LAND}" d="{outline_path(japan, country)}"/>',
        f'<g fill="none" stroke="{FRAME}" stroke-width="1">',
        f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{x2 - x1:.1f}" height="{y2 - y1:.1f}"/>',
        f'<path d="M{x1:.1f} {y2:.1f}L{frame_x:.1f} {frame_y:.1f}M{x2:.1f} {y2:.1f}L{frame_x + frame_w:.1f} {frame_y:.1f}"/>',
        "</g>",
        f'<rect x="{frame_x:.1f}" y="{frame_y:.1f}" width="{frame_w:.1f}" height="{frame_h:.1f}"'
        f' fill="{BACKGROUND}" stroke="{FRAME}" stroke-width="1"/>',
        f'<path fill="{LAND}" d="{outline_path([tokyo], tokyo_frame)}"/>',
        f'<g stroke="{BACKGROUND}" stroke-width="{DOT_RING}">',
        *dots(elsewhere, country),
        *dots(in_tokyo, tokyo_frame),
        "</g>",
    ]
    return svg(width, body), len(in_tokyo)


def usa_map(cafes):
    reader = natural_earth("ne_50m_admin_0_countries_lakes")
    usa = rings_of(reader, "ADM0_A3", "USA", USA_AREA)
    country = Frame(albers_usa, (MARGIN, MARGIN), [p for ring in usa for p in ring], height=HEIGHT - 2 * MARGIN)
    body = [
        f'<path fill="{LAND}" fill-rule="evenodd" d="{outline_path(usa, country)}"/>',
        f'<g stroke="{BACKGROUND}" stroke-width="{DOT_RING}">',
        *dots(cafes, country),
        "</g>",
    ]
    return svg(MARGIN + country.width, body)


def main():
    parser = argparse.ArgumentParser(description="Regenerate the Coffee Atlas maps on the Elsewhere page.")
    parser.add_argument("--kmz", type=Path, default=KMZ, help="the map exported from Google My Maps")
    args = parser.parse_args()
    if not args.kmz.is_file():
        sys.exit(f"Not found: {args.kmz}")

    run_in_private_venv()

    everything = read_cafes(args.kmz)
    shown = [(kind, round(lon, 2), round(lat, 2)) for kind, lon, lat, *_ in everything if kind]
    japan = [c for c in shown if inside(JAPAN_AREA, c[1], c[2])]
    usa = [c for c in shown if inside(USA_AREA, c[1], c[2])]
    outside = [c for c in everything if c[0] and not (inside(JAPAN_AREA, c[1], c[2]) or inside(USA_AREA, c[1], c[2]))]

    japan_svg, in_tokyo = japan_map(japan)
    (OUT / "coffee-atlas-japan.svg").write_text(japan_svg, encoding="utf-8")
    (OUT / "coffee-atlas-usa.svg").write_text(usa_map(usa), encoding="utf-8")

    left_off = sum(1 for c in everything if c[0] is None)
    print(f"Read {len(everything)} places from {args.kmz.name}")
    print(f"  Japan          {len(japan):3d}  ({in_tokyo} in the Tokyo inset)")
    print(f"  United States  {len(usa):3d}")
    print(f"  Square icon    {left_off:3d}  (left off)")
    for kind, lon, lat, name, layer in outside:
        print(f"  Outside the maps, left off: {name} ({lat:.2f}, {lon:.2f})")
    for name in ("coffee-atlas-japan.svg", "coffee-atlas-usa.svg"):
        text = (OUT / name).read_text(encoding="utf-8")
        width = re.search(r'viewBox="0 0 ([\d.]+) ', text).group(1)
        print(f"Wrote _includes/{name}: {width} units wide, {len(text.encode()) / 1024:.1f} KB")
    print("The widths are the flex shares of .coffee-atlas-japan and .coffee-atlas-usa in _sass/_design.scss.")


if __name__ == "__main__":
    main()
