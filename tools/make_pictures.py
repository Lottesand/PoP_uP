# 그림 파일 무기 만들기: tools/pictures_src/의 그림에서 배경을 지우고(투명) 도트 칸으로 줄여
# game/assets/pictures/<이름>.json 으로 저장한다. 게임은 이 칸 데이터를 그림판 그림처럼 무기로 쓴다.
#   python tools/make_pictures.py
# 배경 지우기: 이미 투명한 그림은 그대로, 아니면 가장자리에서 이어진 흰 바탕만 지운다 (안쪽 흰색은 남는다).
import json
import os
from collections import deque
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'pictures_src')
OUT = os.path.join(HERE, '..', 'game', 'assets', 'pictures')
# 이름 → (긴 변 칸 수, 색 수)
PICTURES = {'dino': (64, 10), 'logo': (44, 10)}
WHITE_BG = 235                  # 이보다 밝은 RGB는 흰 바탕 후보
CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def remove_white_background(img):
    """가장자리에 닿은 흰 바탕을 지운다 (흰 몸통처럼 테두리 안의 흰색은 남긴다)"""
    img = img.convert('RGBA')
    w, h = img.size
    px = img.load()
    if any(px[x, y][3] < 255 for x in (0, w - 1) for y in (0, h - 1)):
        return img                  # 이미 배경이 투명하다
    white = lambda x, y: min(px[x, y][:3]) >= WHITE_BG
    todo = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    seen = set()
    while todo:
        x, y = todo.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or not white(x, y):
            continue
        seen.add((x, y))
        px[x, y] = (255, 255, 255, 0)
        todo.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return img


def to_cells(img, long_side, colors):
    img = img.crop(img.getbbox())
    k = long_side / max(img.size)
    small = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
    alpha = small.getchannel('A')
    rgb = small.convert('RGB').quantize(colors, method=Image.Quantize.MEDIANCUT).convert('RGB')
    palette, rows = [], []
    for y in range(small.height):
        row = ''
        for x in range(small.width):
            if alpha.getpixel((x, y)) < 110:
                row += '.'
                continue
            c = list(rgb.getpixel((x, y)))
            if c not in palette:
                palette.append(c)
            row += CHARS[palette.index(c)]
        rows.append(row)
    return {'palette': palette, 'rows': rows}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (long_side, colors) in PICTURES.items():
        img = remove_white_background(Image.open(os.path.join(SRC, name + '.png')))
        data = to_cells(img, long_side, colors)
        with open(os.path.join(OUT, name + '.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print(name, len(data['rows'][0]), 'x', len(data['rows']), len(data['palette']), 'colors')
        print('\n'.join(data['rows']))


if __name__ == '__main__':
    main()
