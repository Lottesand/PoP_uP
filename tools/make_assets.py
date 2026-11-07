# 윈도우 10 느낌의 아이콘과 배경화면을 Pillow로 그려서 game/assets에 저장한다.
#   python tools/make_assets.py
# 아이콘은 256px로 그린 뒤 16/24/32/48px로 줄여서 계단 현상을 없앤다.
import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'game', 'assets')
SIZES = (16, 24, 32, 48)
FONT_BOLD = 'C:/Windows/Fonts/malgunbd.ttf'


def canvas():
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def vgrad(d, box, top, bottom):
    l, t, r, b = box
    for y in range(t, b):
        k = (y - t) / max(1, b - t - 1)
        d.line([(l, y), (r, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(len(top))))


# ------------------------------------------------------------ 아이콘
def folder():
    img, d = canvas()
    d.rounded_rectangle((16, 36, 116, 72), 8, fill=(219, 157, 38))
    d.rounded_rectangle((16, 52, 240, 220), 10, fill=(224, 166, 48))
    d.rectangle((30, 66, 226, 200), fill=(246, 246, 246))
    front = Image.new('RGBA', (256, 256))
    fd = ImageDraw.Draw(front)
    vgrad(fd, (8, 84, 248, 224), (255, 222, 120, 255), (252, 196, 64, 255))
    mask = Image.new('L', (256, 256))
    ImageDraw.Draw(mask).rounded_rectangle((8, 84, 248, 224), 10, fill=255)
    img.paste(front, (0, 0), mask)
    d.line([(14, 88), (242, 88)], fill=(255, 236, 170), width=3)
    return img


def this_pc():
    img, d = canvas()
    d.rounded_rectangle((20, 34, 236, 186), 8, fill=(46, 52, 64))
    screen = Image.new('RGBA', (256, 256))
    vgrad(ImageDraw.Draw(screen), (32, 46, 224, 174), (120, 210, 255, 255), (16, 110, 210, 255))
    img.alpha_composite(screen.crop((32, 46, 224, 174)), (32, 46))
    d.polygon([(32, 46), (140, 46), (32, 140)], fill=(255, 255, 255, 40))
    d.rectangle((112, 186, 144, 210), fill=(120, 124, 134))
    d.rounded_rectangle((72, 206, 184, 222), 6, fill=(150, 154, 164))
    return img


def recycle_bin():
    img, d = canvas()
    d.polygon([(60, 70), (196, 70), (182, 232), (74, 232)], fill=(225, 236, 248, 230), outline=(120, 140, 165))
    for x in (96, 128, 160):
        d.line([(x, 92), (x - (x - 128) * 0.12, 214)], fill=(140, 160, 185), width=6)
    d.rounded_rectangle((48, 46, 208, 72), 6, fill=(200, 214, 230), outline=(120, 140, 165), width=3)
    d.rounded_rectangle((104, 30, 152, 48), 4, outline=(120, 140, 165), width=5)
    return img


def text_file():
    img, d = canvas()
    d.polygon([(52, 20), (164, 20), (204, 60), (204, 236), (52, 236)], fill=(255, 255, 255), outline=(150, 156, 164))
    d.polygon([(164, 20), (164, 60), (204, 60)], fill=(220, 224, 230), outline=(150, 156, 164))
    for y in range(92, 220, 24):
        d.line([(76, y), (180, y)], fill=(160, 170, 180), width=6)
    return img


def drive():
    img, d = canvas()
    vgrad(d, (20, 96, 236, 196), (236, 238, 242), (178, 182, 190))
    d.rectangle((20, 96, 236, 196), outline=(120, 124, 132), width=4)
    for i, (x, y) in enumerate(((40, 116), (74, 116), (40, 150), (74, 150))):
        d.rectangle((x, y, x + 30, y + 30), fill=(0, 120, 215) if i != 3 else (0, 140, 235))
    d.rectangle((180, 166, 216, 178), fill=(60, 200, 90))
    return img


ICONS = {
    'folder': folder,
    'this_pc': this_pc,
    'recycle_bin': recycle_bin,
    'text_file': text_file,
    'drive': drive,
}


def main():
    os.makedirs(os.path.join(OUT, 'icons'), exist_ok=True)
    for name, make in ICONS.items():
        big = make()
        for s in SIZES:
            big.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, 'icons', '%s_%d.png' % (name, s)))
    # 확인용 한 장짜리 목록
    sheet = Image.new('RGBA', (len(ICONS) * 60, 60), (240, 240, 240, 255))
    for i, name in enumerate(ICONS):
        sheet.alpha_composite(Image.open(os.path.join(OUT, 'icons', name + '_48.png')), (i * 60 + 6, 6))
    return sheet


if __name__ == '__main__':
    main()
    print('assets ->', os.path.normpath(OUT))
