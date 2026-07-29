# Ultraman Hunter Assets

供《奥特曼 猎星之契》等 SillyTavern 角色卡调用的奥特曼、怪兽图片与精简资料库。

## 数据结构

```text
assets/
  ultras/{id}/portrait.webp
  monsters/{id}/portrait.webp
data/
  ultras/{id}.json
  monsters/{id}.json
manifest.json
```

前端优先读取根目录的 `manifest.json`，再根据实体 ID 加载图片与独立资料。

## 首批样例

### 奥特曼

| 名称 | 图片 | 资料 |
|---|---|---|
| 初代奥特曼 | ![初代奥特曼](assets/ultras/ultraman/portrait.webp) | [JSON](data/ultras/ultraman.json) |
| 赛文奥特曼 | ![赛文奥特曼](assets/ultras/ultraseven/portrait.webp) | [JSON](data/ultras/ultraseven.json) |
| 迪迦奥特曼 | ![迪迦奥特曼](assets/ultras/ultraman-tiga/portrait.webp) | [JSON](data/ultras/ultraman-tiga.json) |
| 梦比优斯奥特曼 | ![梦比优斯奥特曼](assets/ultras/ultraman-mebius/portrait.webp) | [JSON](data/ultras/ultraman-mebius.json) |
| 赛罗奥特曼 | ![赛罗奥特曼](assets/ultras/ultraman-zero/portrait.webp) | [JSON](data/ultras/ultraman-zero.json) |

### 怪兽与敌对角色

| 名称 | 图片 | 资料 |
|---|---|---|
| 哥莫拉 | ![哥莫拉](assets/monsters/gomora/portrait.webp) | [JSON](data/monsters/gomora.json) |
| 巴尔坦星人 | ![巴尔坦星人](assets/monsters/alien-baltan/portrait.webp) | [JSON](data/monsters/alien-baltan.json) |
| 雷德王 | ![雷德王](assets/monsters/red-king/portrait.webp) | [JSON](data/monsters/red-king.json) |
| 艾雷王 | ![艾雷王](assets/monsters/eleking/portrait.webp) | [JSON](data/monsters/eleking.json) |
| 金古桥 | ![金古桥](assets/monsters/king-joe/portrait.webp) | [JSON](data/monsters/king-joe.json) |

## CDN 地址

```text
https://testingcf.jsdelivr.net/gh/yatexy/ultraman-hunter-assets@main/manifest.json
https://testingcf.jsdelivr.net/gh/yatexy/ultraman-hunter-assets@main/assets/ultras/ultraman/portrait.webp
```

## 说明

- `portrait.png` 保存抓取到的原图，`portrait.webp` 是前端使用的压缩版本。
- 每份资料均记录百科页面和原始图片地址，方便校对与替换。
- 条目中的“猎星之契评级”沿用当前角色卡规则，不代表官方评级。
