import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OUT = ROOT / "rendered"
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.exists() else FONT_REGULAR
    return ImageFont.truetype(str(path), size)


FONTS = {
    "micro": font(18, True),
    "small": font(22),
    "small_bold": font(22, True),
    "body": font(27),
    "body_bold": font(27, True),
    "name": font(47, True),
}


def crop_text(draw: ImageDraw.ImageDraw, value: str, max_width: int, max_lines: int) -> list[str]:
    value = " ".join(str(value or "").split())
    if not value:
        return ["资料待归档。"]
    lines: list[str] = []
    current = ""
    for char in value:
        candidate = current + char
        if draw.textlength(candidate, font=FONTS["body"]) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = char
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    consumed = sum(len(line) for line in lines)
    if consumed < len(value) and lines:
        while lines[-1] and draw.textlength(lines[-1] + "…", font=FONTS["body"]) > max_width:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines


def background(size: tuple[int, int], monster: bool) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size)
    pixels = image.load()
    if monster:
        start, end = (17, 8, 26), (4, 5, 10)
    else:
        start, end = (247, 249, 251), (199, 211, 219)
    for y in range(height):
        t = y / max(height - 1, 1)
        color = tuple(int(start[i] * (1 - t) + end[i] * t) for i in range(3))
        ImageDraw.Draw(image).line((0, y, width, y), fill=color)
    return image


def paste_portrait(canvas: Image.Image, portrait_path: Path, box: tuple[int, int, int, int], monster: bool) -> None:
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    panel = Image.new("RGBA", (width, height), (6, 8, 13, 255))
    pd = ImageDraw.Draw(panel)
    stripe = (29, 19, 38, 255) if monster else (20, 29, 35, 255)
    for x in range(-height, width, 34):
        pd.polygon(((x, 0), (x + 17, 0), (x + height + 17, height), (x + height, height)), fill=stripe)
    portrait = Image.open(portrait_path).convert("RGBA")
    portrait.thumbnail((width - 30, height - 26), Image.Resampling.LANCZOS)
    px = (width - portrait.width) // 2
    py = (height - portrait.height) // 2
    panel.alpha_composite(portrait, (px, py))
    canvas.paste(panel.convert("RGB"), (x1, y1))


def tag(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, accent: tuple[int, int, int], monster: bool) -> int:
    padding_x = 15
    width = int(draw.textlength(text, font=FONTS["small_bold"])) + padding_x * 2
    fill = (29, 14, 38) if monster else (238, 241, 244)
    draw.rounded_rectangle((x, y, x + width, y + 42), radius=7, fill=fill, outline=accent, width=2)
    draw.text((x + padding_x, y + 6), text, font=FONTS["small_bold"], fill=accent)
    return x + width + 10


def fit_tag_text(draw: ImageDraw.ImageDraw, text: str, max_width: int) -> str:
    text = str(text)
    padding = 30
    if draw.textlength(text, font=FONTS["small_bold"]) + padding <= max_width:
        return text
    suffix = "…"
    while text and draw.textlength(text + suffix, font=FONTS["small_bold"]) + padding > max_width:
        text = text[:-1]
    return text + suffix if text else ""


def render_card(profile: dict, portrait_path: Path, expanded: bool) -> Image.Image:
    monster = profile["type"] == "monster"
    accent = (166, 92, 255) if monster else (217, 54, 71)
    text = (239, 231, 246) if monster else (30, 38, 44)
    muted = (184, 168, 198) if monster else (80, 93, 101)
    size = (1200, 850 if expanded else 520)
    canvas = background(size, monster)
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((10, 10, size[0] - 10, size[1] - 10), radius=22, outline=accent, width=3)
    draw.line((390, 10, 390, size[1] - 10), fill=accent, width=2)
    paste_portrait(canvas, portrait_path, (13, 13, 388, size[1] - 13), monster)

    draw.text((425, 38), "HUNTER ARCHIVE // ENTITY CONFIRMED", font=FONTS["micro"], fill=accent)
    draw.text((425, 78), profile["name_zh"], font=FONTS["name"], fill=text)
    x = 425
    x = tag(draw, x, 148, "怪兽" if monster else "奥特曼", accent, monster)
    x = tag(draw, x, 148, profile.get("hunter_contract_rating") or "未评级", accent, monster)
    sources = profile.get("sources") or []
    source_title = (sources[0].get("title") if sources else "") or profile.get("first_appearance", {}).get("work") or "本线档案"
    remaining = 1155 - x
    fitted_source = fit_tag_text(draw, source_title, remaining)
    if fitted_source:
        tag(draw, x, 148, fitted_source, accent, monster)

    draw.text((425, 218), "档案摘要", font=FONTS["small_bold"], fill=accent)
    origin_lines = crop_text(draw, profile.get("origin") or profile.get("summary"), 710, 4 if not expanded else 3)
    y = 260
    for line in origin_lines:
        draw.text((425, y), line, font=FONTS["body"], fill=text)
        y += 43

    if expanded:
        y = max(y + 16, 405)
        draw.line((425, y - 18, 1155, y - 18), fill=accent, width=2)
        draw.text((425, y), "能力、习性与战斗资料", font=FONTS["small_bold"], fill=accent)
        y += 44
        for line in crop_text(draw, profile.get("summary") or profile.get("origin"), 710, 4):
            draw.text((425, y), line, font=FONTS["body"], fill=text)
            y += 42
        history = profile.get("notable_history") or []
        if history:
            y += 10
            draw.text((425, y), "代表记录", font=FONTS["small_bold"], fill=accent)
            y += 42
            for item in history[:3]:
                lines = crop_text(draw, "• " + str(item), 710, 2)
                for line in lines:
                    if y > 770:
                        break
                    draw.text((425, y), line, font=FONTS["small"], fill=muted)
                    y += 34
                if y > 770:
                    break
        draw.text((425, 806), "玩家侧原作资料；不等于当前角色已经掌握全部情报。", font=FONTS["micro"], fill=muted)
    else:
        draw.text((425, 470), "点击展开完整条目  +", font=FONTS["small_bold"], fill=accent)

    label = "KAIJU FILE" if monster else "ULTRA FILE"
    label_width = int(draw.textlength(label, font=FONTS["micro"])) + 30
    draw.rounded_rectangle((28, size[1] - 62, 28 + label_width, size[1] - 24), radius=6, fill=accent)
    draw.text((43, size[1] - 56), label, font=FONTS["micro"], fill=(255, 255, 255))
    return canvas


def save_webp_atomic(image: Image.Image, target: Path) -> None:
    temporary = target.with_suffix(target.suffix + ".tmp")
    image.save(temporary, "WEBP", quality=88, method=6)
    temporary.replace(target)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entities = list(manifest.get("entities", {}).values())
    for index, entity in enumerate(entities, 1):
        profile = json.loads((ROOT / entity["profile"]).read_text(encoding="utf-8"))
        portrait = ROOT / entity["image"]
        if not portrait.exists() or portrait.stat().st_size == 0:
            original = ROOT / profile.get("image_original", "")
            if not original.exists():
                raise FileNotFoundError(f"No usable portrait for {entity['name']}")
            portrait = original
            repaired = ROOT / entity["image"]
            repaired.parent.mkdir(parents=True, exist_ok=True)
            source = Image.open(original).convert("RGBA")
            save_webp_atomic(source, repaired)
        category = "怪兽" if entity["type"] == "monster" else "奥特曼"
        out_dir = OUT / category
        out_dir.mkdir(parents=True, exist_ok=True)
        compact = render_card(profile, portrait, expanded=False)
        full = render_card(profile, portrait, expanded=True)
        save_webp_atomic(compact, out_dir / f"{entity['name']}.webp")
        save_webp_atomic(full, out_dir / f"{entity['name']}_完整.webp")
        print(f"[{index}/{len(entities)}] {category}：{entity['name']}")


if __name__ == "__main__":
    main()
