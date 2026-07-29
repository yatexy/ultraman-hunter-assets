from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "monsters" / "圣物失控融合体"
SIZE = (900, 1200)


def main() -> None:
    image = Image.new("RGB", SIZE, "#07050c")
    pixels = image.load()
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            dx = (x - 450) / 450
            dy = (y - 510) / 760
            glow = max(0.0, 1.0 - (dx * dx + dy * dy))
            pixels[x, y] = (
                int(7 + 20 * glow),
                int(5 + 5 * glow),
                int(12 + 30 * glow),
            )

    scanner = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    sd = ImageDraw.Draw(scanner)
    for radius, alpha in ((320, 42), (270, 28), (210, 20)):
        sd.ellipse(
            (450 - radius, 470 - radius, 450 + radius, 470 + radius),
            outline=(155, 78, 255, alpha),
            width=3,
        )
    sd.line((85, 1060, 815, 1060), fill=(156, 76, 255, 65), width=2)
    sd.line((130, 1090, 770, 1090), fill=(226, 49, 84, 40), width=1)
    image = Image.alpha_composite(image.convert("RGBA"), scanner)

    glow_layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.ellipse((334, 182, 566, 414), outline=(170, 87, 255, 150), width=24)
    gd.ellipse((365, 432, 535, 602), fill=(132, 58, 246, 100))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(28))
    image = Image.alpha_composite(image, glow_layer)

    body = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    armor = (37, 36, 47, 255)
    silver = (161, 165, 177, 255)
    shadow = (15, 13, 21, 255)
    violet = (149, 70, 238, 255)
    crimson = (199, 38, 72, 255)

    # Broken relic halo and asymmetrical horns.
    d.arc((315, 165, 585, 435), 195, 320, fill=silver, width=22)
    d.arc((315, 165, 585, 435), 8, 122, fill=(94, 61, 124, 255), width=17)
    d.polygon([(418, 260), (447, 120), (472, 267)], fill=silver)
    d.polygon([(472, 274), (548, 178), (520, 302)], fill=(102, 80, 120, 255))

    # Head, torso and heavy limbs.
    d.polygon([(375, 275), (450, 225), (535, 286), (512, 398), (445, 440), (377, 392)], fill=armor)
    d.polygon([(330, 410), (450, 360), (585, 425), (620, 690), (531, 835), (365, 824), (286, 670)], fill=shadow)
    d.polygon([(332, 409), (400, 380), (372, 785), (286, 670)], fill=armor)
    d.polygon([(500, 382), (585, 425), (620, 690), (535, 791)], fill=(47, 37, 57, 255))
    d.polygon([(306, 442), (211, 493), (132, 735), (210, 766), (330, 607)], fill=armor)
    d.polygon([(577, 444), (687, 514), (772, 733), (696, 774), (565, 610)], fill=(44, 37, 53, 255))
    d.polygon([(362, 787), (302, 1080), (407, 1080), (464, 810)], fill=armor)
    d.polygon([(470, 802), (505, 1080), (615, 1080), (538, 783)], fill=(47, 39, 55, 255))
    d.polygon([(605, 646), (758, 806), (695, 833), (558, 734)], fill=shadow)

    # Relic plates, claws and energy fissures.
    d.polygon([(343, 415), (404, 384), (392, 695), (326, 655)], fill=silver)
    d.polygon([(507, 390), (566, 423), (582, 621), (528, 677)], fill=(112, 111, 127, 255))
    d.polygon([(383, 304), (442, 268), (430, 392), (381, 376)], fill=(131, 134, 146, 255))
    d.polygon([(455, 264), (522, 302), (505, 377), (458, 396)], fill=(75, 65, 88, 255))
    for points in (
        [(193, 740), (139, 793), (205, 778)],
        [(216, 746), (180, 819), (239, 781)],
        [(703, 749), (772, 802), (710, 783)],
        [(682, 759), (735, 831), (667, 790)],
    ):
        d.polygon(points, fill=silver)
    d.line((413, 414, 391, 572, 431, 735), fill=crimson, width=11)
    d.line((498, 414, 530, 553, 493, 745), fill=violet, width=12)
    d.line((361, 864, 339, 1005), fill=crimson, width=8)
    d.line((526, 854, 566, 1016), fill=violet, width=9)

    # Eyes and split core.
    d.polygon([(393, 314), (433, 326), (397, 344)], fill=(186, 220, 255, 255))
    d.polygon([(470, 326), (515, 311), (508, 347)], fill=(190, 83, 255, 255))
    d.ellipse((392, 486, 512, 606), fill=(7, 8, 17, 255), outline=silver, width=10)
    d.pieslice((408, 501, 496, 589), 90, 270, fill=(116, 211, 255, 255))
    d.pieslice((408, 501, 496, 589), 270, 90, fill=violet)
    d.line((452, 505, 452, 587), fill=(232, 235, 244, 230), width=5)

    image = Image.alpha_composite(image, body)
    vignette = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    vd.rectangle((18, 18, 882, 1182), outline=(145, 70, 221, 90), width=2)
    vd.line((18, 105, 18, 18, 105, 18), fill=(210, 62, 112, 180), width=5)
    vd.line((795, 1182, 882, 1182, 882, 1095), fill=(145, 77, 231, 180), width=5)
    image = Image.alpha_composite(image, vignette)

    OUT.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(OUT / "portrait.png", optimize=True)
    image.convert("RGB").save(OUT / "portrait.webp", "WEBP", quality=88, method=6)


if __name__ == "__main__":
    main()
