from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "scripts" / "hunter_expansion_100.tsv"
OFFICIAL_INDEX = ROOT / "sources" / "official-encyclopedia-index.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


MANUAL_IMAGES = {
    "火焰哥尔赞": "https://p3-sdbk2-media.byteimg.com/tos-cn-i-xv4ileqgde/89f24796ae844aa1bf69be22a4476391~tplv-xv4ileqgde-resize-w%3A750.image",
    "EX雷德王": "https://vignette.wikia.nocookie.net/ultra/images/5/50/Ex_Red-King_S.png/revision/latest?cb=20180409064443&path-prefix=id",
    "EX哥莫拉": "https://img2.wikia.nocookie.net/__cb20140928014644/ultra/images/a/a2/Ex_Gomora_data.png",
    "EX杰顿": "https://p3-sdbk2-media.byteimg.com/tos-cn-i-xv4ileqgde/aa9f7d84c3a64243928a46bab2c3728f~tplv-xv4ileqgde-image.image",
    "佩丹尼姆杰顿": "https://p3-sdbk2-media.byteimg.com/tos-cn-i-xv4ileqgde/48e21d14c2a04504a0fc438ab1dbc30e~tplv-xv4ileqgde-image.image",
    "玛伽大蛇": "https://www.nicepng.com/png/detail/369-3697566_maga-orochi-render-profile-kaiju.png",
    "赛高古": "https://w7.pngwing.com/pngs/730/308/png-transparent-action-toy-figures-bandai-ultra-series-zaigorg-fighting-miscellaneous-photography-fictional-character.png",
    "卡内贡": "https://www.scifijapan.com/images/xplus/kanegon10.jpg",
    "黑王": "https://vignette2.wikia.nocookie.net/villains/images/9/95/Black_King.png/revision/latest?cb=20170405231323",
    "嘎次星人": "https://m-78.jp/wp-content/uploads/2021/01/ultraseven_alien_guts_kv_1.jpg",
    "格斯拉王": "https://img.atwiki.jp/niconicomugen/attach/9709/23623/kingguesra.png",
    "雷布朗多星人": "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/ca3e65e9-5231-4888-87c7-4c3c6b8df0d8/dg0dzio-05fecd50-3a82-4677-8f28-3fef27fda4f9.png/v1/fill/w_577%2Ch_651/alien_reiblood_by_dramakkomon108_dg0dzio-fullview.png",
    "暗黑铠甲": "https://canvas-lb.tubitv.com/opts/m8wYTHEhN5mzQA%3D%3D/37b0fb38-568e-43f8-8871-b3c6e75bf6d9/CJgDEMcEOgUxLjEuNg%3D%3D",
    "卡蜜拉": "https://storage.moegirl.org.cn/moegirl/commons/f/f0/Camearra.png",
    "达拉姆": "https://i.pinimg.com/564x/17/1f/ba/171fbaf5470230fac293d74496a60a08.jpg",
    "古兰特王": "https://i.pinimg.com/originals/56/8d/d4/568dd47e22a0b9b1e0999a79026ac823.png",
    "超戈布": "https://stat.ameba.jp/user_images/20221122/16/kotokailove/af/7a/j/o0750108015206542902.jpg",
    "吉咖奇美拉": "https://i.pinimg.com/736x/04/eb/5d/04eb5d99255a6ec7a50bbe9fafd3cb0c.jpg",
    "贝琉多拉": "https://dafunda.com/wp-content/uploads/2023/02/Belyudra.jpg",
    "EX艾雷王": "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/8bf802b7-04d7-41c7-aa51-2283f556ca1b/d84h84h-1747498e-43e5-4022-817f-9c6f58315798.jpg",
    "希特拉": "https://static.wikia.nocookie.net/ultra/images/8/89/Hudra_Render.png",
    "U杀手萨乌鲁斯": "https://www.abandomoviez.net/dba/fotos/dba_1820_1.jpg",
    "U杀手萨乌鲁斯·新": "https://static.tvtropes.org/pmwiki/pub/images/2970dc2916b4d999646a262156156ec5_3.png",
}


def load_rows() -> list[dict]:
    rows = []
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("|")
        if len(fields) != 8:
            raise ValueError(f"Bad expansion row: {line}")
        name, official, stage, rating, category, work, aliases, signature = fields
        rows.append(
            {
                "name": name,
                "official": official,
                "stage": int(stage),
                "rating": rating,
                "category": category,
                "work": work,
                "aliases": [x for x in aliases.split(",") if x],
                "signature": signature,
            }
        )
    if len(rows) != 100:
        raise ValueError(f"Expected 100 rows, got {len(rows)}")
    return rows


def yaml_entry(row: dict) -> str:
    aliases = ", ".join(row["aliases"])
    aliases_line = f"\n别名: [{aliases}]" if aliases else ""
    return f"""图鉴名称: {row['name']}
原作归属: {row['work']}
候选阶段: [第{row['stage']}阶段]
类别: {row['category']}{aliases_line}
评级: {row['rating']}
评级口径:
  - 仅采用该规范名称对应形态的原作常态稳定表现，不借用同词根其他形态的数据。
  - 临时操纵者增幅、一次性奇迹、融合素材个体的额外战绩不并入基础评级。
外形识别:
  - 以原作对应形态的轮廓、器官和配色为准；图鉴图片只用于识别，不赋予角色全知。
习性与定位:
  - {row['category']}；动机需结合原作生态、操纵关系与本时间线现场证据，不默认无差别屠杀。
攻击方式:
  - {row['signature']}。
战斗使用:
  - 初次交战先展示其优势区间，再允许角色通过观察、受击、仪器或可靠档案获得破解线索。
  - 同档胜负受地形、伤势、克制、情报与协作影响；跨档结果必须具有明确因果。
资料开放层:
  目击: 只确认外形、移动方式、公开攻击与现场破坏。
  解析: 可确认基础评级、典型习性、器官功能与已验证弱点。
  交战: 可记录本时间线个体的伤势、战术变化、操纵痕迹与最终去向。
使用边界:
  - 候选阶段只表示事件导演可选用，不代表该对象已经登场或角色已经认识。
  - 只有正文或MVU记录完整规范名称时，才能读取本条目；相似词根、普通种、EX形态、机械体、融合体与同化体不得串档。
"""


def update_card(project: Path, rows: list[dict]) -> None:
    worldbook = project / "世界书"
    state_path = project / "tavern-cards-state.json"
    index_path = worldbook / "怪兽图鉴总索引.txt"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    manifest = state["entryManifest"]["unknown"]
    max_index = max(int(v.get("display_index", 0)) for v in manifest.values())
    max_order = max(int(v.get("position", {}).get("order", 0)) for v in manifest.values())

    for offset, row in enumerate(rows, 1):
        path = worldbook / f"{row['name']}.yaml"
        if path.exists():
            raise ValueError(f"Worldbook entry already exists: {path}")
        content = yaml_entry(row)
        path.write_text(content, encoding="utf-8")
        manifest[row["name"]] = {
            "abstract": "",
            "enabled": False,
            "strategy": {"type": "selective", "keys": ["猎星EJS内部资料池键"]},
            "position": {"type": "at_depth", "order": max_order + offset, "role": "system", "depth": 0},
            "display_index": max_index + offset,
            "keywords": ["猎星EJS内部资料池键"],
            "path": f"世界书\\{row['name']}.yaml",
        }
    text = index_path.read_text(encoding="utf-8")
    match = re.search(r"const 怪兽登记表 = (\[.*?\]);", text)
    if not match:
        raise ValueError("怪兽登记表 not found")
    registry = json.loads(match.group(1))
    existing = {item["名称"] for item in registry}
    for row in rows:
        if row["name"] in existing:
            raise ValueError(f"Duplicate registry name: {row['name']}")
        registry.append({"名称": row["name"], "阶段": [row["stage"]], "别名": row["aliases"]})
    new_index = text[: match.start(1)] + json.dumps(registry, ensure_ascii=False, separators=(",", ":")) + text[match.end(1) :]
    index_path.write_text(new_index, encoding="utf-8")

    for stage in range(1, 9):
        candidates = [row for row in rows if row["stage"] == stage]
        path = worldbook / f"第{'一二三四五六七八'[stage-1]}阶段敌怪完整图鉴.yaml"
        original = path.read_text(encoding="utf-8")
        marker = "目录边界:"
        addition = "".join(f"  - 名称: {row['name']}\n    评级: {row['rating']}\n" for row in candidates)
        updated = original.replace(marker, addition + marker, 1)
        if updated == original:
            raise ValueError(f"Stage marker missing: {path}")
        path.write_text(updated, encoding="utf-8")

    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def request_bytes(url: str, referer: str = "") -> bytes:
    parts = urllib.parse.urlsplit(url)
    url = urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc.encode("idna").decode("ascii"), urllib.parse.quote(urllib.parse.unquote(parts.path), safe="/%:@"), urllib.parse.quote(urllib.parse.unquote(parts.query), safe="=&?/:@"), parts.fragment)
    )
    headers = {"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"}
    if referer:
        try:
            referer.encode("ascii")
            headers["Referer"] = referer
        except UnicodeEncodeError:
            pass
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def placeholder(row: dict) -> Image.Image:
    image = Image.new("RGB", (768, 1024), "#100a18")
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 744, 1000), outline="#7b35c9", width=4)
    draw.text((60, 450), row["name"], fill="#f0e8ff", font=ImageFont.load_default(size=40))
    draw.text((60, 520), "IMAGE REVIEW REQUIRED", fill="#d39bff", font=ImageFont.load_default(size=24))
    return image


def save_portrait(payload: bytes | None, row: dict, asset_dir: Path, preserve_existing: bool = False) -> tuple[int, int, bool]:
    is_placeholder = False
    if payload:
        try:
            image = Image.open(io.BytesIO(payload))
            image.load()
            if image.width < 180 or image.height < 180:
                raise ValueError("image too small")
        except Exception:
            image = placeholder(row)
            is_placeholder = True
    elif preserve_existing and (asset_dir / "portrait.png").exists():
        image = Image.open(asset_dir / "portrait.png")
        image.load()
    else:
        image = placeholder(row)
        is_placeholder = True
    if max(image.size) > 1800:
        image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
    asset_dir.mkdir(parents=True, exist_ok=True)
    png = image.convert("RGBA") if "A" in image.getbands() else image.convert("RGB")
    png.save(asset_dir / "portrait.png", optimize=True)
    png.save(asset_dir / "portrait.webp", "WEBP", quality=88, method=6)
    return image.width, image.height, is_placeholder


def update_assets(rows: list[dict], download: bool, review_only: bool = False) -> None:
    official = {item["name"].upper(): item for item in json.loads(OFFICIAL_INDEX.read_text(encoding="utf-8"))}
    manifest_path = ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report_path = ROOT / "sources" / "expansion-100-image-report.json"
    previous = []
    if report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
    previous_by_name = {item["name"]: item for item in previous}
    selected = [row for row in rows if not review_only or previous_by_name.get(row["name"], {}).get("needs_review", True)]
    report_by_name = {item["name"]: item for item in previous}
    for index, row in enumerate(selected, 1):
        official_item = official.get(row["official"].upper())
        image_url = MANUAL_IMAGES.get(row["name"]) or (official_item or {}).get("image_url", "")
        page_url = (official_item or {}).get("page_url", "")
        payload = None
        error = ""
        if download and image_url:
            try:
                payload = request_bytes(image_url, page_url)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
        asset_rel = f"assets/monsters/{row['name']}"
        profile_rel = f"data/monsters/{row['name']}.json"
        was_good = not previous_by_name.get(row["name"], {}).get("needs_review", True)
        width, height, needs_review = save_portrait(payload, row, ROOT / asset_rel, preserve_existing=was_good)
        profile = {
            "id": "monster:" + hashlib.sha1(row["name"].encode("utf-8")).hexdigest()[:10],
            "type": "monster",
            "name_zh": row["name"],
            "name_en": row["official"],
            "aliases": [row["name"], *row["aliases"]],
            "image": f"{asset_rel}/portrait.webp",
            "image_original": f"{asset_rel}/portrait.png",
            "first_appearance": {"work": row["work"], "detail": "", "year": None},
            "origin": f"{row['category']}，候选阶段为第{row['stage']}阶段。",
            "summary": f"原作常态评级{row['rating']}；典型能力包括{row['signature']}。",
            "notable_history": [f"原作归属：{row['work']}。", f"形态口径：{row['name']}独立建档，不与同词根形态串档。"],
            "hunter_contract_rating": row["rating"],
            "sources": ([{"title": row["official"], "url": page_url, "image_url": image_url}] if image_url else []),
        }
        profile_path = ROOT / profile_rel
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        key = profile["id"]
        manifest["entities"][key] = {
            "type": "monster",
            "name": row["name"],
            "aliases": profile["aliases"],
            "image": profile["image"],
            "profile": profile_rel,
        }
        source_path = ROOT / "sources" / f"monster-{row['name']}.json"
        source_path.write_text(
            json.dumps(
                {
                    "name": row["name"],
                    "official_name": row["official"],
                    "page_url": page_url,
                    "image_url": image_url,
                    "downloaded_width": width,
                    "downloaded_height": height,
                    "needs_manual_image_review": needs_review,
                    "error": error,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        report_by_name[row["name"]] = {"name": row["name"], "official": row["official"], "image_url": image_url, "needs_review": needs_review, "error": error}
        print(f"[{index:03d}/{len(selected):03d}] {row['name']} {'REVIEW' if needs_review else 'OK'}", flush=True)
        if download:
            time.sleep(0.08)
    manifest["updated_at"] = "2026-08-13"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = [report_by_name[row["name"]] for row in rows]
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path)
    parser.add_argument("--card", action="store_true")
    parser.add_argument("--assets", action="store_true")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--review-only", action="store_true")
    args = parser.parse_args()
    rows = load_rows()
    if args.card:
        if not args.project:
            raise SystemExit("--project is required with --card")
        update_card(args.project.resolve(), rows)
    if args.assets:
        update_assets(rows, args.download, args.review_only)


if __name__ == "__main__":
    main()
