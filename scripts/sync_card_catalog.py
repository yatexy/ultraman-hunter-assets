"""Build the remote Hunter Archive catalog from the card's worldbook indexes.

The script is resumable: existing manifest entries and valid portrait.webp files
are skipped. It uses the card's own independent entries for Chinese metadata and
Bing Images only to discover a representative image and source page.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from PIL import Image


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)

ULTRA_QUERY_HINTS = {
    "初代奥特曼": "Ultraman character",
    "佐菲": "Zoffy",
    "赛文奥特曼": "Ultraseven character",
    "杰克奥特曼": "Ultraman Jack",
    "艾斯奥特曼": "Ultraman Ace",
    "泰罗奥特曼": "Ultraman Taro",
    "雷欧奥特曼": "Ultraman Leo",
    "阿斯特拉": "Astra",
    "爱迪奥特曼": "Ultraman 80",
    "尤莉安": "Yullian",
    "迪迦奥特曼": "Ultraman Tiga",
    "戴拿奥特曼": "Ultraman Dyna character",
    "盖亚奥特曼": "Ultraman Gaia",
    "阿古茹奥特曼": "Ultraman Agul",
    "高斯奥特曼": "Ultraman Cosmos",
    "杰斯提斯奥特曼": "Ultraman Justice",
    "奈克瑟斯奥特曼": "Ultraman Nexus",
    "麦克斯奥特曼": "Ultraman Max character",
    "杰诺奥特曼": "Ultraman Xenon",
    "梦比优斯奥特曼": "Ultraman Mebius",
    "希卡利奥特曼": "Ultraman Hikari",
    "赛罗奥特曼": "Ultraman Zero",
    "银河奥特曼": "Ultraman Ginga",
    "维克特利奥特曼": "Ultraman Victory",
    "银河维克特利": "\"Ultraman Ginga Victory\"",
    "艾克斯奥特曼": "Ultraman X",
    "欧布奥特曼": "Ultraman Orb",
    "捷德奥特曼": "Ultraman Geed",
    "罗索奥特曼": "Ultraman Rosso",
    "布鲁奥特曼": "Ultraman Blu",
    "格丽乔奥特曼": "\"Ultrawoman Grigio\" -Darkness",
    "罗布奥特曼": "Ultraman Ruebe",
    "泰迦奥特曼": "Ultraman Taiga",
    "泰塔斯奥特曼": "Ultraman Titas",
    "风马奥特曼": "Ultraman Fuma",
    "泽塔奥特曼": "Ultraman Z",
    "特利迦奥特曼": "Ultraman Trigger",
    "德凯奥特曼": "Ultraman Decker",
    "布莱泽奥特曼": "Ultraman Blazar",
    "亚刻奥特曼": "Ultraman Arc character",
    "奥特之王": "Ultraman King",
    "诺亚奥特曼": "Ultraman Noa",
    "雷杰多奥特曼": "Ultraman Legend",
    "赛迦奥特曼": "Ultraman Saga",
}

ULTRA_PAGE_TITLES = {
    "格丽乔奥特曼": "Ultrawoman Grigio",
    "银河维克特利": "Ultraman Gingavictory",
}

MONSTER_PAGE_TITLES = {
    "泰莱斯通": "Telesdon",
    "哥莫拉": "Gomora",
    "雷德王": "Red King",
    "安东拉": "Antlar",
    "古维拉": "Gubila",
    "格斯拉": "Gesura",
    "佩吉拉": "Peguila",
    "拉贡": "Ragon",
    "古敦": "Gudon",
    "双尾怪": "Twin Tail",
    "穆鲁奇": "Muruchi",
    "西利赞": "Sealizar",
    "加库玛阿尔法": "Gakuma",
    "加库玛贝塔": "Gakuma",
    "立加德隆": "Ligatron",
    "佩德隆": "Pedoleon",
    "诺斯菲尔": "Nosferu",
    "艾雷王": "Eleking",
    "戈尔德拉斯": "Goldras",
    "庞敦": "Pandon",
    "梅特龙星人": "Alien Metron",
    "金古桥": "King Joe",
    "巴顿": "Birdon",
    "莱布王": "Live King",
    "恩马戈": "Enmargo",
    "阿斯特隆": "Arstron",
    "萨德拉": "Sadola",
    "泰兰特": "Tyrant",
    "加佐特": "Gazort",
    "基里艾洛德人": "Kyrieloid",
    "玛奇那": "Machina",
    "乔贝利艾": "Jobarieh",
    "克莱美第": "Zazahn",
    "巴赞甲": "Bazanga",
    "巴尔坦星人": "Alien Baltan",
    "扎拉布星人": "Alien Zarab",
    "达达": "Dada",
    "美菲拉斯星人": "Alien Mefilas",
    "佩丹星人": "Alien Pedan",
    "纳克尔星人": "Alien Nackle",
    "马格马星人": "Alien Magma",
    "希尔巴布尔美": "Silver Bloome",
    "切布尔星人": "Alien Chibull",
    "古阿军团残余": "Guar Army",
    "盖内伽古": "Genegarg",
    "贝劳克恩": "Verokron",
    "巴克西姆": "Vakishim",
    "多拉格里": "Doragory",
    "穆鲁罗亚": "Mururoa",
    "帝斯雷姆": "Deathrem",
    "格罗扎姆": "Grozam",
    "英普莱扎": "Inpelaizer",
    "巴尔基星人": "Alien Valky",
    "布莱克王": "Black King",
    "诺巴": "Nova",
    "古兰特拉": "Galberos",
    "弗斯特": "Beast the One",
    "泰兰特强化体": "Tyrant",
    "斯卡鲁哥莫拉": "Skull Gomora",
    "雷霆杀手": "Thunder Killer",
    "奇美拉柏洛斯": "Chimera Belial",
    "齐杰拉": "Gijera",
    "佐加": "Zoiger",
    "加坦杰厄": "Gatanothor",
    "基里艾洛德二代": "Kyrieloid",
    "梅加洛杰厄": "Megalothor",
    "卡尔蜜拉": "Carmeara",
    "达贡": "Darrgon",
    "希特拉姆": "Hudram",
    "格里姆德": "Grimdo",
    "戈尔巴": "Golba",
    "加拉特隆MK2": "Galactron MK2",
    "玛伽巴萨": "Maga-Basser",
    "玛伽庞敦": "Maga-Pandon",
    "斯菲亚合成兽": "Spheresaurus",
    "斯菲亚雷德王": "Sphere Red King",
    "斯菲亚哥莫拉": "Sphere Gomora",
    "斯菲亚奇美拉": "Mother Spheresaurus",
    "佐格第一形态": "Zogu",
    "佐格第二形态": "Zogu",
    "布鲁顿": "Bullton",
    "加恩Q": "Gan-Q",
    "壬龙": "Mizunoeno Dragon",
    "玛伽杰顿": "Maga-Zetton",
    "海帕杰顿幼体": "Hyper Zetton",
    "海帕杰顿": "Hyper Zetton",
    "格利扎": "Greeza",
    "黑暗扎基": "Dark Zagi",
    "极恶贝利亚": "Ultraman Belial Atrocious",
    "安培拉星人": "Alien Empera",
    "黑暗路基艾尔": "Dark Lugiel",
    "阿布索留特塔尔塔洛斯": "Absolute Tartarus",
    "德斯特鲁多斯": "Destrudos",
    "完全体格利扎": "Greeza",
    "完全复苏黑暗扎基": "Dark Zagi",
    "极限贝利亚力量体": "Ultraman Belial Atrocious",
    "安培拉完全力量体": "Alien Empera",
    "黑暗路基艾尔最终形态": "Dark Lugiel",
}


def request_bytes(url: str, referer: str | None = None, timeout: int = 25) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(12 * 1024 * 1024)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_js_array(text: str, variable: str) -> list[dict]:
    match = re.search(rf"const\s+{re.escape(variable)}\s*=\s*(\[.*?\]);", text, re.S)
    if not match:
        raise RuntimeError(f"Cannot find JS array: {variable}")
    return json.loads(match.group(1))


def parse_ultras(text: str) -> list[dict]:
    results: list[dict] = []
    pattern = re.compile(
        r"\{\s*名称:\s*'([^']+)'\s*,\s*词:\s*\[([^\]]*)\]",
        re.S,
    )
    for name, aliases_source in pattern.findall(text):
        aliases = re.findall(r"'([^']+)'", aliases_source)
        results.append({"name": name, "aliases": aliases, "type": "ultra"})
    return results


def scalar(text: str, *keys: str) -> str:
    for key in keys:
        match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
        if match:
            value = match.group(1).strip().strip("'\"")
            if value and value not in {"|", ">"}:
                return value
    return ""


def list_under(text: str, key: str, limit: int = 4) -> list[str]:
    match = re.search(
        rf"(?ms)^{re.escape(key)}:\s*\n((?:[ \t]+-[^\n]*\n?)+)",
        text,
    )
    if not match:
        return []
    return [
        item.strip()
        for item in re.findall(r"(?m)^[ \t]+-\s*(.+?)\s*$", match.group(1))
    ][:limit]


def worldbook_metadata(worldbook: Path, target: dict) -> dict:
    path_yaml = worldbook / f"{target['name']}.yaml"
    path_txt = worldbook / f"{target['name']}.txt"
    path = path_yaml if path_yaml.exists() else path_txt
    text = read_text(path) if path.exists() else ""
    rating = scalar(text, "评级", "当前战力评级") or "未评级"
    if target["type"] == "monster":
        role = scalar(text, "原作定位") or "原作敌怪"
        appearance = scalar(text, "外观")
        habits = scalar(text, "习性")
        attacks = scalar(text, "攻击方式")
        origin = f"{role}。"
        if habits:
            origin += habits.rstrip("。") + "。"
        pieces = []
        if appearance:
            pieces.append(f"外观特征：{appearance}")
        if habits:
            pieces.append(f"习性：{habits}")
        if attacks:
            pieces.append(f"主要攻击方式：{attacks}")
        summary = "；".join(pieces).rstrip("；") + ("。" if pieces else "")
        history = [
            value
            for value in (
                f"原作定位为{role}。" if role else "",
                f"其典型习性为{habits}。" if habits else "",
                f"常用战法包括{attacks}。" if attacks else "",
            )
            if value
        ]
    else:
        identity = scalar(text, "原作身份", "身份定位")
        identity_list = list_under(text, "身份", 3)
        appearance = scalar(text, "外观")
        appearance_list = list_under(text, "外观", 2)
        abilities = scalar(text, "主要能力")
        battle = scalar(text, "战斗特点", "战斗方式")
        origin = identity or (identity_list[0] if identity_list else "奥特战士。")
        if not origin.endswith("。"):
            origin += "。"
        pieces = []
        if identity_list:
            pieces.append("；".join(identity_list))
        if abilities:
            pieces.append(f"主要能力：{abilities}")
        if battle:
            pieces.append(f"战斗特点：{battle}")
        if not pieces and (appearance or appearance_list):
            pieces.append(appearance or "；".join(appearance_list))
        summary = "；".join(pieces).rstrip("；") + ("。" if pieces else "")
        history = identity_list or [
            value
            for value in (
                identity,
                f"主要能力包括{abilities}。" if abilities else "",
                f"战斗特点为{battle}。" if battle else "",
            )
            if value
        ]
    return {
        "rating": rating,
        "origin": origin,
        "summary": summary or origin,
        "notable_history": history[:3],
    }


def bing_image_candidates(name: str, entity_type: str) -> list[dict]:
    if entity_type == "ultra":
        hint = ULTRA_QUERY_HINTS.get(name, name)
        query = f'"{hint}" render full body'
    else:
        query = f'"{name}" 奥特曼 怪兽 图鉴 全身'
    url = "https://www.bing.com/images/search?" + urllib.parse.urlencode(
        {"q": query, "form": "HDRSC2", "first": "1"}
    )
    page = request_bytes(url).decode("utf-8", "ignore")
    raw_metadata: list[str] = []
    raw_metadata.extend(
        match[0] or match[1]
        for match in re.findall(
            r'class="iusc"[^>]*\sm="([^"]+)"|\sm="([^"]+)"[^>]*class="iusc"',
            page,
            re.I,
        )
    )
    candidates = []
    blocked_terms = (
        "外送茶",
        "援交",
        "成人",
        "色情",
        "av女",
        "博彩",
        "casino",
        "porn",
    )
    normalized_name = re.sub(r"\s+", "", name).lower()
    for raw in raw_metadata:
        try:
            data = json.loads(html.unescape(raw))
        except (json.JSONDecodeError, TypeError):
            continue
        image_url = data.get("murl")
        if not image_url or image_url.startswith("data:"):
            continue
        page_url = data.get("purl", "")
        title = data.get("t", "") or ""
        context = html.unescape(f"{title} {page_url} {image_url}").lower()
        if any(term in context for term in blocked_terms):
            continue
        compact_context = re.sub(r"\s+", "", context)
        relevance = 0
        if normalized_name in compact_context:
            relevance += 100
        short_name = normalized_name.replace("奥特曼", "")
        if len(short_name) >= 2 and short_name in compact_context:
            relevance += 45
        if any(term in context for term in ("奥特曼", "ultraman", "ultra", "怪兽", "kaiju")):
            relevance += 30
        if any(term in context for term in ("fandom.com", "baike.", "biligame.", "ultra")):
            relevance += 20
        if entity_type == "ultra" and not any(
            term in context for term in ("奥特曼", "ultraman", "ultra", short_name)
        ):
            continue
        if entity_type == "monster" and relevance < 45:
            continue
        candidates.append(
            {
                "query": query,
                "search_url": url,
                "image_url": image_url,
                "page_url": page_url,
                "title": title or name,
                "width": data.get("w"),
                "height": data.get("h"),
                "relevance": relevance,
            }
        )
    return sorted(candidates, key=lambda item: item["relevance"], reverse=True)


def fandom_image_candidates(name: str, entity_type: str) -> list[dict]:
    if entity_type == "ultra":
        search_term = ULTRA_QUERY_HINTS.get(name)
        exact_title = ULTRA_PAGE_TITLES.get(name)
    else:
        search_term = MONSTER_PAGE_TITLES.get(name)
        exact_title = MONSTER_PAGE_TITLES.get(name)
    if not search_term:
        return []
    if exact_title:
        exact_params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "redirects": "1",
            "titles": exact_title,
            "prop": "pageimages|info",
            "piprop": "original",
            "inprop": "url",
        }
        exact_url = "https://ultra.fandom.com/api.php?" + urllib.parse.urlencode(
            exact_params
        )
        try:
            exact_payload = json.loads(request_bytes(exact_url).decode("utf-8"))
            exact_results = []
            for page in exact_payload.get("query", {}).get("pages", []):
                original = page.get("original") or {}
                if page.get("missing") or not original.get("source"):
                    continue
                exact_results.append(
                    {
                        "query": exact_title,
                        "search_url": exact_url,
                        "image_url": original["source"],
                        "page_url": page.get("fullurl", ""),
                        "title": page.get("title", exact_title),
                        "width": original.get("width"),
                        "height": original.get("height"),
                        "relevance": 2000,
                    }
                )
            if exact_results:
                return exact_results
        except Exception:
            pass

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "generator": "search",
        "gsrsearch": search_term,
        "gsrlimit": "4",
        "prop": "pageimages|info",
        "piprop": "original",
        "inprop": "url",
    }
    api_url = "https://ultra.fandom.com/api.php?" + urllib.parse.urlencode(params)
    try:
        payload = json.loads(request_bytes(api_url).decode("utf-8"))
    except Exception:
        return []
    results = []
    pages = sorted(
        payload.get("query", {}).get("pages", []),
        key=lambda page: page.get("index", 999),
    )
    for page in pages:
        image_url = (page.get("original") or {}).get("source")
        if page.get("missing") or not image_url:
            continue
        results.append(
            {
                "query": search_term,
                "search_url": api_url,
                "image_url": image_url,
                "page_url": page.get("fullurl", ""),
                "title": page.get("title", search_term),
                "width": (page.get("original") or {}).get("width"),
                "height": (page.get("original") or {}).get("height"),
                "relevance": 1000 - page.get("index", 999),
            }
        )
    return results


def save_image(candidate: dict, asset_dir: Path) -> tuple[int, int]:
    payload = request_bytes(candidate["image_url"], candidate.get("page_url") or None)
    image = Image.open(io.BytesIO(payload))
    image.load()
    if image.width < 180 or image.height < 180:
        raise ValueError("image too small")
    if max(image.size) > 1800:
        image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
    asset_dir.mkdir(parents=True, exist_ok=True)
    png = image.convert("RGBA") if "A" in image.getbands() else image.convert("RGB")
    png.save(asset_dir / "portrait.png", optimize=True)
    webp = png.convert("RGBA") if png.mode == "RGBA" else png.convert("RGB")
    webp.save(asset_dir / "portrait.webp", "WEBP", quality=86, method=6)
    return image.width, image.height


def build_targets(worldbook: Path) -> list[dict]:
    ultras = parse_ultras(read_text(worldbook / "奥特曼图鉴总索引.txt"))
    monsters_data = parse_js_array(
        read_text(worldbook / "怪兽图鉴总索引.txt"),
        "怪兽登记表",
    )
    monsters = [
        {
            "name": item["名称"],
            "aliases": [item["名称"], *item.get("别名", [])],
            "type": "monster",
            "stages": item.get("阶段", []),
        }
        for item in monsters_data
    ]
    seen = set()
    targets = []
    for target in [*ultras, *monsters]:
        key = (target["type"], target["name"])
        if key in seen:
            continue
        seen.add(key)
        target["aliases"] = list(dict.fromkeys([target["name"], *target.get("aliases", [])]))
        targets.append(target)
    return targets


def existing_name_map(manifest: dict) -> dict[tuple[str, str], str]:
    return {
        (entry["type"], entry["name"]): key
        for key, entry in manifest.get("entities", {}).items()
    }


def entity_key(entity_type: str, name: str) -> str:
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
    return f"{entity_type}:{digest}"


def sync_one(
    repo: Path,
    worldbook: Path,
    manifest: dict,
    target: dict,
    allow_download: bool,
) -> str:
    entity_type = target["type"]
    folder = "ultras" if entity_type == "ultra" else "monsters"
    name = target["name"]
    metadata = worldbook_metadata(worldbook, target)
    asset_rel = f"assets/{folder}/{name}"
    profile_rel = f"data/{folder}/{name}.json"
    asset_dir = repo / asset_rel
    source = None
    if allow_download and not (asset_dir / "portrait.webp").exists():
        errors = []
        # Canonical images come from the dedicated wiki. Generic image search
        # silently returned unrelated characters during sampling, so a failed
        # wiki lookup is reported for manual mapping instead of being hidden.
        candidates = fandom_image_candidates(name, entity_type)
        for candidate in candidates[:12]:
            try:
                width, height = save_image(candidate, asset_dir)
                candidate["downloaded_width"] = width
                candidate["downloaded_height"] = height
                source = candidate
                break
            except Exception as error:  # noqa: BLE001 - keep the batch resumable
                errors.append(f"{type(error).__name__}: {error}")
        if source is None:
            raise RuntimeError(f"No usable image for {name}: {' | '.join(errors[-3:])}")
    source_path = repo / "sources" / f"{entity_type}-{name}.json"
    if source:
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(
            json.dumps(source, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    elif source_path.exists():
        source = json.loads(read_text(source_path))
    profile = {
        "id": entity_key(entity_type, name),
        "type": entity_type,
        "name_zh": name,
        "name_en": "",
        "aliases": target["aliases"],
        "image": f"{asset_rel}/portrait.webp",
        "image_original": f"{asset_rel}/portrait.png",
        "first_appearance": {
            "work": "原作出处见来源页面",
            "detail": "",
            "year": None,
        },
        "origin": metadata["origin"],
        "summary": metadata["summary"],
        "notable_history": metadata["notable_history"],
        "hunter_contract_rating": metadata["rating"],
        "sources": (
            [
                {
                    "title": source.get("title") or name,
                    "url": source.get("page_url") or source.get("search_url"),
                    "image_url": source.get("image_url"),
                }
            ]
            if source
            else []
        ),
    }
    profile_path = repo / profile_rel
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    key = entity_key(entity_type, name)
    manifest.setdefault("entities", {})[key] = {
        "type": entity_type,
        "name": name,
        "aliases": target["aliases"],
        "image": profile["image"],
        "profile": profile_rel,
    }
    manifest["updated_at"] = date.today().isoformat()
    return key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worldbook", required=True, type=Path)
    parser.add_argument("--repo", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--names", nargs="*", default=[])
    parser.add_argument("--type", choices=["ultra", "monster"])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--delay", type=float, default=0.7)
    args = parser.parse_args()

    repo = args.repo.resolve()
    worldbook = args.worldbook.resolve()
    manifest_path = repo / "manifest.json"
    manifest = json.loads(read_text(manifest_path))
    targets = build_targets(worldbook)
    inventory_path = repo / "sources" / "card-target-inventory.json"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(
        json.dumps(targets, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.inventory_only:
        print(f"Inventory: {len(targets)} targets → {inventory_path}")
        return
    existing = existing_name_map(manifest)
    selected = [
        target
        for target in targets
        if (not args.names or target["name"] in args.names)
        and (not args.type or target["type"] == args.type)
        and (
            args.names
            or (target["type"], target["name"]) not in existing
            or not (repo / manifest["entities"][existing[(target["type"], target["name"])]]["image"]).exists()
        )
    ]
    if args.limit:
        selected = selected[: args.limit]
    print(f"Selected {len(selected)} / {len(targets)} targets")
    if args.probe:
        for target in selected:
            candidates = bing_image_candidates(target["name"], target["type"])
            print(
                json.dumps(
                    {"name": target["name"], "candidates": candidates[:10]},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return
    failures = []
    for index, target in enumerate(selected, 1):
        try:
            key = sync_one(repo, worldbook, manifest, target, args.download)
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"[{index}/{len(selected)}] OK {target['name']} → {key}")
        except Exception as error:  # noqa: BLE001 - report and continue the batch
            failures.append({"name": target["name"], "error": str(error)})
            print(f"[{index}/{len(selected)}] FAIL {target['name']}: {error}")
        if args.download and index < len(selected):
            time.sleep(args.delay)
    failure_path = repo / "sources" / "sync-failures.json"
    failure_path.write_text(
        json.dumps(failures, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Completed: {len(selected) - len(failures)} OK, {len(failures)} failed")


if __name__ == "__main__":
    main()
