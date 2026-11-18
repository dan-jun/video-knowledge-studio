# -*- coding: utf-8 -*-
"""生成 B 站封面候选（16:9, 1280x720）。

参考高播放量封面：
- BV1axHPzBE7N（11.9 万）：「一口气搞懂」橙色超大字 + 白字主题 + 深色星空底
- BV17x8jzvEm6（8.5 万）：纯黑底 + Attention is all you need + 公式 + QKV 三格

用法：python tools/make_covers.py <outdir>
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import resolve_out

from runtime import FONT_CJK, FONT_CJK_BOLD
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
F_BOLD = FONT_CJK_BOLD
F_REG = FONT_CJK

BG = (10, 12, 16)
ORANGE = (255, 138, 30)
WHITE = (245, 247, 250)
BLUE = (90, 169, 255)
DIM = (150, 160, 172)
CELL = (24, 30, 40)


def font(path, size):
    return ImageFont.truetype(path, size)


def centered(d, box, text, f, fill):
    x0, y0, x1, y1 = box
    w = d.textlength(text, font=f)
    bbox = f.getbbox(text)
    h = bbox[3] - bbox[1]
    d.text((x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2 - bbox[1]), text, font=f, fill=fill)


def grid_qkv(d, cx, y, size, gap, label_size, matrix):
    """画 Q/K/V 三个小矩阵格子 + 标签。"""
    labels = ["Q", "K", "V"]
    total = 3 * size + 2 * gap
    x = cx - total / 2
    f_lab = font(F_BOLD, label_size)
    for k in range(3):
        centered(d, (x, y - 46, x + size, y - 6), labels[k], f_lab, BLUE)
        for i in range(3):
            for j in range(3):
                x0 = x + j * (size / 3)
                y0 = y + i * (size / 3)
                d.rectangle([x0, y0, x0 + size / 3 - 4, y0 + size / 3 - 4],
                            outline=WHITE, width=2, fill=matrix[k][i][j])
        x += size + gap


def v1_big_text(out):
    """大字冲击型：一口气搞懂 + 自注意力。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # 背景：右下沉一点的蓝色光晕
    for r in range(420, 0, -6):
        a = int(16 * (1 - r / 420))
        d.ellipse([W - 420 - r, H - 300 - r, W - 420 + r, H - 300 + r], fill=(10 + a, 14 + a, 22 + a))

    small = font(F_BOLD, 92)
    d.text((80, 70), "一口气搞懂", font=small, fill=ORANGE)

    big = font(F_BOLD, 168)
    d.text((74, 190), "自注意力", font=big, fill=WHITE)

    mid = font(F_BOLD, 64)
    d.text((80, 400), "QKV → 多头 → 手写实现", font=mid, fill=BLUE)

    tag = font(F_BOLD, 44)
    d.rounded_rectangle([80, 520, 80 + 300, 520 + 74], radius=14, outline=ORANGE, width=4)
    centered(d, (80, 520, 380, 594), "17 分钟讲透", tag, ORANGE)

    foot = font(F_REG, 34)
    d.text((80, 630), "零基础也能听懂 · 含练习题与复盘", font=foot, fill=DIM)
    img.save(os.path.join(out, "cover-1-大字冲击.png"))


def v2_formula(out):
    """极简公式型：Attention is all you need + 公式 + QKV 格子。"""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    t1 = font(F_BOLD, 62)
    centered(d, (0, 64, W, 150), "Attention is all you need", t1, WHITE)

    t2 = font(F_BOLD, 50)
    centered(d, (0, 168, W, 230), "自注意力到底在算什么？", t2, DIM)

    f = font(F_BOLD, 56)
    formula = "Attention(Q,K,V) = softmax( QK^T / √d ) V"
    centered(d, (0, 262, W, 340), formula, f, BLUE)

    m = [[CELL] * 3 for _ in range(3)]
    m[0][0] = (46, 74, 120)
    m[1][1] = (46, 74, 120)
    m[2][2] = (46, 74, 120)
    grid_qkv(d, W / 2, 400, 150, 46, 40, m)

    t3 = font(F_BOLD, 34)
    centered(d, (0, 620, W, 680), "17 分钟 · 从公式到手写代码", t3, DIM)
    img.save(os.path.join(out, "cover-2-极简公式.png"))


def v3_heatmap(out):
    """问题 + 热力图型。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    t1 = font(F_BOLD, 110)
    d.text((64, 56), "「注意」", font=t1, fill=WHITE)
    d.text((64, 172), "到底注意啥？", font=t1, fill=ORANGE)

    t2 = font(F_REG, 40)
    d.text((68, 320), "把 QKV 摊成一张热力图，一眼看懂", font=t2, fill=DIM)

    # 右下角热力图
    n, cell = 5, 62
    x0, y0 = W - 64 - n * cell, 300
    w = [[0.8, 0.2, 0.1, 0.05, 0.0],
         [0.3, 0.6, 0.2, 0.1, 0.05],
         [0.2, 0.45, 0.35, 0.15, 0.05],
         [0.1, 0.2, 0.5, 0.3, 0.1],
         [0.05, 0.1, 0.3, 0.45, 0.4]]
    for i in range(n):
        for j in range(n):
            v = w[i][j]
            d.rectangle([x0 + j * cell, y0 + i * cell, x0 + (j + 1) * cell - 3, y0 + (i + 1) * cell - 3],
                        fill=(int(30 + 180 * v), int(60 + 140 * v), int(120 + 120 * v)))
    tag = font(F_BOLD, 40)
    d.rounded_rectangle([64, 470, 64 + 260, 470 + 66], radius=12, outline=BLUE, width=4)
    centered(d, (64, 470, 324, 536), "4 分钟", tag, BLUE)
    img.save(os.path.join(out, "cover-3-热力图.png"))


def main():
    out = resolve_out(sys.argv[1] if len(sys.argv) > 1 else "covers")
    os.makedirs(out, exist_ok=True)
    v1_big_text(out)
    v2_formula(out)
    v3_heatmap(out)
    for f in sorted(os.listdir(out)):
        print("→", os.path.join(out, f))


if __name__ == "__main__":
    main()
