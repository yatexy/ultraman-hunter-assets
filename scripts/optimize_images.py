from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    for source in sorted((ROOT / "assets").rglob("portrait.png")):
        with Image.open(source) as image:
            image.load()
            image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            target = source.with_suffix(".webp")
            image.save(target, "WEBP", quality=88, method=6)
            relative = target.relative_to(ROOT)
            print(f"{relative.as_posix()} {image.width}x{image.height} {target.stat().st_size} bytes")


if __name__ == "__main__":
    main()
