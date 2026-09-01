import argparse
import csv
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw


def parse_args():
    parser = argparse.ArgumentParser(
        description="Composite locked subject image layers onto a background plate."
    )
    parser.add_argument("--background", required=True, help="Clean background plate.")
    parser.add_argument("--placements", required=True, help="CSV with image,center_x,height,anchor_y,anchor_frac.")
    parser.add_argument("--out", required=True, help="Output composite PNG.")
    parser.add_argument("--annotated-out", help="Optional annotated output PNG.")
    parser.add_argument("--defringe", action="store_true", help="Remove light matte/white fringe from subject edges.")
    return parser.parse_args()


def is_background(px):
    r, g, b = px[:3]
    return r >= 176 and g >= 176 and b >= 176 and max(r, g, b) - min(r, g, b) <= 42


def remove_white_fringe(src):
    w, h = src.size
    pix = src.load()
    alpha = src.getchannel("A")
    alpha_pix = alpha.load()
    edge = bytearray(w * h)

    for y in range(h):
        for x in range(w):
            if alpha_pix[x, y] == 0:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and alpha_pix[nx, ny] == 0:
                    edge[y * w + x] = 1
                    break

    for y in range(h):
        row = y * w
        for x in range(w):
            if not edge[row + x]:
                continue
            r, g, b, a = pix[x, y]
            neutral = max(r, g, b) - min(r, g, b) <= 55
            if neutral and min(r, g, b) >= 150:
                pix[x, y] = (r, g, b, 0)
            elif neutral and min(r, g, b) >= 115:
                pix[x, y] = (r, g, b, min(a, 90))

    return src


def make_cutout(path, defringe):
    src = Image.open(path).convert("RGBA")
    if src.getchannel("A").getextrema()[0] < 255:
        return src

    w, h = src.size
    pix = src.load()
    visited = bytearray(w * h)
    q = deque()

    def push(x, y):
        idx = y * w + x
        if visited[idx]:
            return
        if is_background(pix[x, y]):
            visited[idx] = 1
            q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                push(nx, ny)

    alpha = Image.new("L", (w, h), 255)
    a = alpha.load()
    for y in range(h):
        row = y * w
        for x in range(w):
            if visited[row + x]:
                a[x, y] = 0

    src.putalpha(alpha)
    if defringe:
        src = remove_white_fringe(src)

    bbox = src.getbbox()
    return src.crop(bbox) if bbox else src


def read_placements(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"image", "center_x", "height", "anchor_y", "anchor_frac"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"placements CSV missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def paste_anchor(base, layer, center_x, anchor_y, height, anchor_frac):
    ratio = height / layer.height
    new_size = (round(layer.width * ratio), round(layer.height * ratio))
    resized = layer.resize(new_size, Image.Resampling.LANCZOS)
    x = round(center_x - resized.width / 2)
    y = round(anchor_y - resized.height * anchor_frac)
    base.alpha_composite(resized, (x, y))
    return (x, y, resized.width, resized.height)


def main():
    args = parse_args()
    base = Image.open(args.background).convert("RGBA")
    rows = read_placements(args.placements)

    boxes = []
    for row in rows:
        layer = make_cutout(Path(row["image"]), args.defringe)
        box = paste_anchor(
            base,
            layer,
            float(row["center_x"]),
            float(row["anchor_y"]),
            float(row["height"]),
            float(row["anchor_frac"]),
        )
        boxes.append(box)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    base.save(out)
    print(out.resolve())

    if args.annotated_out:
        annotated = base.copy()
        draw = ImageDraw.Draw(annotated)
        for idx, (x, y, w, h) in enumerate(boxes, start=1):
            draw.rectangle((x, y, x + w, y + h), outline=(255, 220, 0, 220), width=3)
            draw.text((x + 5, y + 5), f"#{idx}", fill=(0, 0, 0, 255), stroke_width=3, stroke_fill=(255, 220, 0, 255))
        annotated_out = Path(args.annotated_out)
        annotated_out.parent.mkdir(parents=True, exist_ok=True)
        annotated.save(annotated_out)
        print(annotated_out.resolve())


if __name__ == "__main__":
    main()
