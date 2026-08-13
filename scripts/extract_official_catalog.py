from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "temp-encyclopedialist.html").read_text(encoding="utf-8")
items = []
for block in re.findall(r"<article class=\"p-herolist__item\">(.*?)</article>", source, re.S):
    href = re.search(r"<a href=\"([^\"]+)\"", block)
    name = re.search(r"<h3 class=\"p-herolist__name\">\s*(.*?)\s*</h3>", block, re.S)
    image = re.search(r"(?:data-src|src)=\"([^\"]+(?:jpg|jpeg|png|webp))\"", block, re.I)
    if not (href and name and image):
        continue
    display = html.unescape(re.sub(r"<[^>]+>", "", name.group(1))).strip()
    image_url = html.unescape(image.group(1))
    if image_url.startswith("/"):
        image_url = "https://tsuburaya-prod.com" + image_url
    items.append({"name": display, "page_url": href.group(1), "image_url": image_url})

(ROOT / "sources" / "official-encyclopedia-index.json").write_text(
    json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"Extracted {len(items)} official encyclopedia records")
