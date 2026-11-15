# 포인터 도트 캐릭터 스프라이트 시트 재생
# 시트는 tools/build_sprites.py가 만든다. 둔탁한 도트 느낌으로 픽셀을 4배로 키워 그린다 (포인터 12px → 화면 48px).
import json
import os
from pico2d import load_image

from config import *

SCALE = 4


def draw_cell(image, x, y, w, h, pivot, px, py, flip=False, scale=SCALE):
    """시트의 (x, y, w, h) 칸을 pivot(칸 안 왼쪽 위 기준)이 화면 (px, py)에 오도록 그린다"""
    cx = px + (w / 2 - pivot[0]) * scale * (-1 if flip else 1)
    cy = py + (pivot[1] - h / 2) * scale
    image.clip_composite_draw(x, image.h - y - h, w, h, 0, 'h' if flip else '', cx, cy, w * scale, h * scale)


# ==================================================================== 포인터
class PointerSprite:
    def __init__(self):
        base = os.path.join(ASSETS, 'sprites')
        with open(os.path.join(base, 'pointer.json'), encoding='utf-8') as f:
            meta = json.load(f)
        self.states = meta['states']
        self.cell = meta['cell']
        self.frames, self.fps, self.origin = meta['frames'], meta['fps'], meta['origin']
        self.images = {}
        for mode in ('off', 'on'):
            for face in ('calm', 'angry', 'dizzy'):
                self.images[mode, face] = load_image(os.path.join(base, 'pointer_%s_%s.png' % (mode, face)))

    def draw(self, mode, face, state, t, feet_x, feet_y, flip=False, alpha=None):
        img = self.images[mode, face]
        w, h = self.cell
        row = self.states.index(state)
        col = int(t * self.fps) % self.frames
        if alpha is not None:
            img.opacify(alpha)
        draw_cell(img, col * w, row * h, w, h, self.origin, feet_x, feet_y, flip)
        if alpha is not None:
            img.opacify(1)


_pointer = None


def pointer():
    global _pointer
    if _pointer is None:
        _pointer = PointerSprite()
    return _pointer


# ==================================================================== 적
class CharSheet:
    """한 장 시트: 줄 = 상태, 칸 = 12프레임 (tools/build_sprites.py의 적 시트)"""

    def __init__(self, name):
        base = os.path.join(ASSETS, 'sprites', name)
        with open(base + '.json', encoding='utf-8') as f:
            meta = json.load(f)
        self.image = load_image(base + '.png')
        self.states, self.cell = meta['states'], meta['cell']
        self.frames, self.fps, self.origin = meta['frames'], meta['fps'], meta['origin']

    def draw(self, state, t, feet_x, feet_y, flip=False):
        w, h = self.cell
        row = self.states.index(state)
        col = int(t * self.fps) % self.frames
        draw_cell(self.image, col * w, row * h, w, h, self.origin, feet_x, feet_y, flip)

    def draw_rotated(self, state, t, cx, cy, rad, scale=SCALE):
        """칸 가운데를 (cx, cy)에 두고 rad만큼 돌려 그린다 (위에서 내려다본 버그)"""
        w, h = self.cell
        row = self.states.index(state)
        col = int(t * self.fps) % self.frames
        self.image.clip_composite_draw(col * w, self.image.h - row * h - h, w, h, rad, '', cx, cy,
                                       w * scale, h * scale)


_chars = {}


def char(name):
    if name not in _chars:
        _chars[name] = CharSheet(name)
    return _chars[name]
