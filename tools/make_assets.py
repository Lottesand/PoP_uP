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
def folder(paper=True):
    img, d = canvas()
    d.rounded_rectangle((16, 36, 116, 72), 8, fill=(219, 157, 38))
    d.rounded_rectangle((16, 52, 240, 220), 10, fill=(224, 166, 48))
    if paper:
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


def folder_empty():
    return folder(paper=False)


def explorer():
    # 파일 탐색기: 노란 폴더 아래에 파란 손잡이 띠
    img = folder()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((70, 150, 186, 196), 10, fill=(37, 133, 214))
    d.rounded_rectangle((90, 162, 166, 184), 6, fill=(120, 196, 245))
    return img


def recycle_bin(full=False):
    img, d = canvas()
    if full:
        d.polygon([(70, 40), (150, 20), (170, 90), (90, 110)], fill=(255, 255, 255), outline=(150, 160, 170))
        d.polygon([(120, 30), (200, 50), (180, 110), (100, 90)], fill=(250, 240, 200), outline=(180, 160, 110))
    d.polygon([(60, 70), (196, 70), (182, 232), (74, 232)], fill=(225, 236, 248, 230), outline=(120, 140, 165))
    for x in (96, 128, 160):
        d.line([(x, 92), (x - (x - 128) * 0.12, 214)], fill=(140, 160, 185), width=6)
    if not full:
        d.rounded_rectangle((48, 46, 208, 72), 6, fill=(200, 214, 230), outline=(120, 140, 165), width=3)
        d.rounded_rectangle((104, 30, 152, 48), 4, outline=(120, 140, 165), width=5)
    else:
        d.rounded_rectangle((52, 62, 204, 80), 6, fill=(200, 214, 230), outline=(120, 140, 165), width=3)
    return img


def recycle_bin_full():
    return recycle_bin(full=True)


def image_file():
    img = text_file()
    d = ImageDraw.Draw(img)
    d.rectangle((70, 84, 186, 200), fill=(140, 200, 245))
    d.polygon([(70, 200), (110, 140), (140, 176), (160, 156), (186, 200)], fill=(60, 150, 70))
    d.ellipse((150, 96, 172, 118), fill=(255, 220, 80))
    return img


def browser():
    img, d = canvas()
    c, r = 128, 116
    box = (c - r, c - r, c + r, c + r)
    d.pieslice(box, 210, 330, fill=(219, 68, 55))
    d.pieslice(box, 330, 450, fill=(244, 180, 0))
    d.pieslice(box, 90, 210, fill=(15, 157, 88))
    d.ellipse((c - 56, c - 56, c + 56, c + 56), fill=(255, 255, 255))
    d.ellipse((c - 44, c - 44, c + 44, c + 44), fill=(66, 133, 244))
    return img


def notepad():
    img, d = canvas()
    d.rounded_rectangle((44, 36, 212, 232), 8, fill=(250, 250, 250), outline=(150, 160, 170), width=4)
    vgrad(d, (46, 38, 211, 80), (80, 170, 240), (30, 120, 210))
    for x in range(64, 200, 26):
        d.ellipse((x, 24, x + 14, 52), outline=(90, 100, 110), width=4)
    for y in range(104, 220, 24):
        d.line([(64, y), (192, y)], fill=(170, 190, 210), width=5)
    return img


def paint():
    img, d = canvas()
    d.ellipse((20, 44, 236, 220), fill=(246, 226, 186), outline=(190, 160, 110), width=4)
    d.ellipse((150, 150, 196, 196), fill=(0, 0, 0, 0))
    for (x, y), col in zip(((62, 92), (104, 68), (152, 76), (186, 112), (66, 144)),
                           ((232, 40, 40), (250, 200, 0), (40, 170, 70), (30, 110, 220), (150, 60, 200))):
        d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=col)
    d.line([(118, 210), (228, 30)], fill=(150, 100, 50), width=14)
    d.polygon([(104, 236), (112, 200), (130, 208)], fill=(40, 40, 40))
    return img


def vscode():
    img, d = canvas()
    d.line([(184, 48), (52, 168)], fill=(0, 96, 160), width=40)
    d.line([(184, 208), (52, 88)], fill=(0, 122, 204), width=40)
    d.polygon([(168, 22), (236, 52), (236, 204), (168, 234)], fill=(31, 156, 240))
    d.polygon([(168, 22), (190, 32), (190, 224), (168, 234)], fill=(0, 122, 204))
    return img


def kakao():
    img, d = canvas()
    d.rounded_rectangle((12, 12, 244, 244), 52, fill=(254, 229, 0))
    d.ellipse((44, 58, 212, 174), fill=(58, 29, 29))
    d.polygon([(82, 156), (70, 204), (118, 168)], fill=(58, 29, 29))
    f = ImageFont.truetype(FONT_BOLD, 46)
    d.text((128, 116), 'TALK', font=f, fill=(254, 229, 0), anchor='mm')
    return img


def terminal():
    # 명령 프롬프트: 회색 제목 띠가 있는 검은 창에 C:\_
    img, d = canvas()
    d.rectangle((14, 34, 242, 222), fill=(12, 12, 12), outline=(110, 110, 110), width=4)
    d.rectangle((16, 36, 240, 70), fill=(190, 190, 190))
    f = ImageFont.truetype('C:/Windows/Fonts/consolab.ttf', 78)
    d.text((34, 150), 'C:\\', font=f, fill=(220, 220, 220), anchor='lm')
    d.rectangle((170, 172, 214, 184), fill=(220, 220, 220))
    return img


def usb():
    img, d = canvas()
    d.rectangle((100, 18, 156, 70), fill=(200, 204, 210), outline=(120, 124, 130), width=4)
    d.rectangle((112, 32, 124, 44), fill=(90, 90, 96))
    d.rectangle((132, 32, 144, 44), fill=(90, 90, 96))
    d.rounded_rectangle((80, 66, 176, 236), 14, fill=(60, 64, 74))
    d.rounded_rectangle((92, 78, 164, 224), 10, fill=(84, 90, 104))
    d.ellipse((120, 196, 136, 212), fill=(80, 220, 120))
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


def lock():
    img, d = canvas()
    d.arc((76, 28, 180, 140), 180, 360, fill=(110, 116, 126), width=22)
    d.line([(87, 84), (87, 120)], fill=(110, 116, 126), width=22)
    d.line([(169, 84), (169, 120)], fill=(110, 116, 126), width=22)
    d.rounded_rectangle((52, 112, 204, 236), 16, fill=(240, 180, 40), outline=(190, 130, 20), width=6)
    d.ellipse((114, 150, 142, 178), fill=(120, 80, 10))
    d.rectangle((122, 170, 134, 206), fill=(120, 80, 10))
    return img


def windows_logo():
    img, d = canvas()
    g = 10
    for x0, y0 in ((24, 24), (128 + g // 2, 24), (24, 128 + g // 2), (128 + g // 2, 128 + g // 2)):
        d.rectangle((x0, y0, x0 + 104 - g // 2, y0 + 104 - g // 2), fill=(255, 255, 255))
    return img


ICONS = {
    'folder': folder, 'folder_empty': folder_empty, 'explorer': explorer, 'this_pc': this_pc,
    'recycle_bin': recycle_bin, 'recycle_bin_full': recycle_bin_full, 'browser': browser,
    'notepad': notepad, 'paint': paint, 'vscode': vscode, 'kakao': kakao, 'terminal': terminal,
    'usb': usb, 'text_file': text_file, 'image_file': image_file, 'drive': drive, 'lock': lock,
    'windows_logo': windows_logo,
}


# ------------------------------------------------------------ 배경화면
def wallpaper(w=1920, h=1080):
    # 짙은 남색 바탕 + 원근으로 기울어진 빛나는 창 로고 + 왼쪽으로 퍼지는 빛줄기
    bg = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(bg)
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)], fill=(int(2 + 6 * k), int(10 + 22 * k), int(36 + 50 * k)))

    glow = Image.radial_gradient('L').resize((w * 2, h * 2)).crop((w * 0.62, h * 0.5, w * 0.62 + w, h * 0.5 + h))
    glow = Image.eval(glow, lambda v: max(0, 255 - v) * 0.55)
    bg.paste(Image.new('RGB', (w, h), (20, 110, 230)), (0, 0), glow.convert('L'))

    # 로고 사각형의 네 꼭짓점 (왼쪽은 멀어서 작고, 오른쪽은 가까워서 크다)
    tl, bl = (1040, 330), (1040, 760)
    tr, br = (1470, 190), (1470, 890)

    def at(u, v):
        top = (tl[0] + (tr[0] - tl[0]) * u, tl[1] + (tr[1] - tl[1]) * u)
        bot = (bl[0] + (br[0] - bl[0]) * u, bl[1] + (br[1] - bl[1]) * u)
        return (top[0] + (bot[0] - top[0]) * v, top[1] + (bot[1] - top[1]) * v)

    beams = Image.new('L', (w, h))
    bd = ImageDraw.Draw(beams)
    bd.polygon([tl, bl, (0, 1080), (0, 0)], fill=70)
    bd.polygon([at(0, 0.49), at(0, 0.51), (0, 640), (0, 470)], fill=110)
    bd.polygon([at(0.49, 0), at(0.51, 0), (560, 0), (300, 0)], fill=40)
    beams = beams.filter(ImageFilter.GaussianBlur(40))
    bg.paste(Image.new('RGB', (w, h), (60, 150, 255)), (0, 0), beams)

    logo = Image.new('L', (w, h))
    ld = ImageDraw.Draw(logo)
    gap = 0.018
    for u0, u1 in ((0, 0.5 - gap), (0.5 + gap, 1)):
        for v0, v1 in ((0, 0.5 - gap), (0.5 + gap, 1)):
            ld.polygon([at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1)], fill=255)
    halo = logo.filter(ImageFilter.GaussianBlur(28))
    bg.paste(Image.new('RGB', (w, h), (40, 140, 255)), (0, 0), Image.eval(halo, lambda v: v * 0.8))

    face = Image.new('RGB', (w, h))
    fd = ImageDraw.Draw(face)
    for x in range(1000, 1500):
        k = (x - 1040) / 430
        fd.line([(x, 0), (x, h)], fill=(int(40 + 80 * k), int(150 + 70 * k), 255))
    bg.paste(face, (0, 0), logo)
    return bg


def main():
    os.makedirs(os.path.join(OUT, 'icons'), exist_ok=True)
    for name, make in ICONS.items():
        big = make()
        for s in SIZES:
            big.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, 'icons', '%s_%d.png' % (name, s)))
    wallpaper().save(os.path.join(OUT, 'wallpaper.png'))
    # 확인용 한 장짜리 목록
    sheet = Image.new('RGBA', (len(ICONS) * 60, 60), (240, 240, 240, 255))
    for i, name in enumerate(ICONS):
        sheet.alpha_composite(Image.open(os.path.join(OUT, 'icons', name + '_48.png')), (i * 60 + 6, 6))
    return sheet


if __name__ == '__main__':
    main()
    print('assets ->', os.path.normpath(OUT))
