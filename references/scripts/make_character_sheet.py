import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a numbered character sheet from separate subject images."
    )
    parser.add_argument("images", nargs="+", help="Subject image paths, in stable numbered order.")
    parser.add_argument("--out", required=True, help="Output PNG path.")
    parser.add_argument("--cell-width", type=int, default=620)
    parser.add_argument("--cell-height", type=int, default=760)
    parser.add_argument("--label-height", type=int, default=70)
    return parser.parse_args()


def main():
    args = parse_args()
    paths = [Path(path) for path in args.images]
    images = [Image.open(path).convert("RGBA") for path in paths]

    width = args.cell_width * len(images)
    height = args.cell_height + args.label_height
    sheet = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        font = ImageFont.load_default()

    for idx, img in enumerate(images, start=1):
        img.thumbnail((args.cell_width - 80, args.cell_height - 80), Image.Resampling.LANCZOS)
        x = (idx - 1) * args.cell_width + (args.cell_width - img.width) // 2
        y = 20 + (args.cell_height - 80 - img.height) // 2
        sheet.alpha_composite(img, (x, y))

        label = f"#{idx}"
        bbox = draw.textbbox((0, 0), label, font=font)
        tx = (idx - 1) * args.cell_width + (args.cell_width - (bbox[2] - bbox[0])) // 2
        draw.text((tx, args.cell_height + 12), label, fill=(0, 0, 0, 255), font=font)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(out.resolve())


if __name__ == "__main__":
    main()
