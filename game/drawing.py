# 그림판에서 저장한 그림 = 무기.
# 하얀 칸은 투명, 칠한 칸만 남기고 잘라 낸다. 그림의 크기·모양·색으로 무기 능력이 정해진다.
#   크기(칠한 칸 수): 클수록 세지만 느리게 휘두른다
#   모양: 길쭉하면 창(앞으로 찌르기, 멀리 닿음), 아니면 칼(위에서 아래로 크게 휘두르기)
#   가장 많이 쓴 색: 빨강 = 불, 파랑 = 얼음, 초록 = 풀, 노랑 = 번개, 검정·회색 = 묵직함
import ctypes
import math

import pico2d.pico2d as p2
from pico2d import Image
from sdl2 import (SDL_CreateTexture, SDL_UpdateTexture, SDL_SetTextureBlendMode, SDL_PIXELFORMAT_ABGR8888,
                  SDL_TEXTUREACCESS_STATIC, SDL_BLENDMODE_BLEND, SDL_SetTextureAlphaMod, SDL_SetTextureColorMod)

import gfx
from config import *

WHITE_CELL = (255, 255, 255)
MOTION = 1.8                    # 한 번 휘두르는 전체 시간 = 맞는 시간(swing_time) × 이만큼
# 동작 구간 (전체 0~1): 칼 = 들어 올리기 → 내려치기 → 넘어가기 → 되돌리기, 창 = 당기기 → 찌르기 → 버티기 → 되돌리기
BLADE_PHASES = (0.2, 0.45, 0.58)
SPEAR_PHASES = (0.25, 0.4, 0.56)
SPEAR_RATIO = 2.6               # 긴 변 / 짧은 변이 이 이상이면 창
LONG_MIN, LONG_MAX = 56, 190    # 무기 길이 (px)

# 그림판 팔레트 색 → 속성
COLOR_ELEMENT = {
    (0, 0, 0): 'heavy', (127, 127, 127): 'heavy', (195, 195, 195): 'heavy',
    (136, 0, 21): 'fire', (237, 28, 36): 'fire', (255, 127, 39): 'fire',
    (255, 242, 0): 'shock', (34, 177, 76): 'leaf', (0, 162, 232): 'ice', (63, 72, 204): 'ice',
    (163, 73, 164): None,
}
ELEMENTS = {                    # 속성 → (이름, 설명, 이펙트 색)
    'fire': ('불', '맞은 적이 3초 동안 불탄다', (255, 120, 0)),
    'ice': ('얼음', '맞은 적이 2초 동안 느려진다', (120, 200, 255)),
    'leaf': ('풀', '맞힐 때마다 HP 2 회복', (60, 200, 90)),
    'shock': ('번개', '맞은 적이 1초 동안 기절한다', (255, 230, 0)),
    'heavy': ('묵직함', '세게 밀쳐 내고 잠깐 기절시킨다', (90, 90, 90)),
    None: ('없음', '특별한 효과 없음', (255, 200, 0)),
}


def element_of(c):
    if c in COLOR_ELEMENT:
        return COLOR_ELEMENT[c]
    near = min(COLOR_ELEMENT, key=lambda p: sum((a - b) ** 2 for a, b in zip(p, c)))
    return COLOR_ELEMENT[near]


class Drawing:
    """잘라 낸 그림 한 장. cells[y][x] = 색 또는 None(투명), y는 위에서부터"""
    kind = 'drawing'

    def drop(self):
        pass                            # 사진 창에 원본이 남아 있으니 그냥 손에서 놓는다

    def __init__(self, cells):
        self.cells = cells
        self.h, self.w = len(cells), len(cells[0])
        self.inked = [(x, y, c) for y, row in enumerate(cells) for x, c in enumerate(row) if c is not None]
        self.n = len(self.inked)
        self.tall = self.h > self.w                 # 세로로 길면 위쪽이 칼끝
        long_, short = max(self.w, self.h), max(1, min(self.w, self.h))
        self.shape = 'spear' if long_ / short >= SPEAR_RATIO else 'blade'
        counts = {}
        for x, y, c in self.inked:
            e = element_of(c)
            counts[e] = counts.get(e, 0) + 1
        self.element = max(counts, key=counts.get)
        # 능력치
        self.damage = int(round(min(40, max(6, 5 + math.sqrt(self.n) * 1.2))))
        self.swing_time = min(0.5, 0.16 + self.n / 3000) * (1.2 if self.element == 'heavy' else 1.0)
        self.motion_time = self.swing_time * MOTION      # 준비 · 내지르기 · 되돌리기까지 한 번 동작 전체
        self.cooldown = self.motion_time + 0.04
        # 한 칸 = 2px이 기본. 너무 길면 줄이고 너무 짧으면 키워서 길이를 LONG_MIN~LONG_MAX에 맞춘다
        self.px = min(LONG_MAX / long_, max(LONG_MIN / long_, 2.0))
        self.length = long_ * self.px               # 손에서 칼끝까지
        self.thick = short * self.px
        self.image = None
        # 맞는 판정 점: 칠한 칸 중심 (너무 많으면 듬성듬성)
        step = max(1, int(math.sqrt(self.n / 90)))
        self.local = [self.to_local(x, y) for x, y, c in self.inked if x % step == 0 and y % step == 0]

    @classmethod
    def from_canvas(cls, pixels, cw, ch):
        """그림판 픽셀(RGBA) → 칠한 부분만 잘라 낸 그림. 아무것도 안 그렸으면 None"""
        rows = []
        for y in range(ch):
            row = []
            for x in range(cw):
                i = (y * cw + x) * 4
                c = tuple(pixels[i:i + 3])
                row.append(None if c == WHITE_CELL else c)
            rows.append(row)
        ys = [y for y, row in enumerate(rows) if any(row)]
        if not ys:
            return None
        xs = [x for x in range(cw) if any(rows[y][x] for y in ys)]
        x0, x1, y0, y1 = xs[0], xs[-1] + 1, ys[0], ys[-1] + 1
        return cls([row[x0:x1] for row in rows[y0:y1]])

    # ---------------------------------------------------------------- 정보
    @property
    def shape_name(self):
        return '창 (앞으로 찌르기)' if self.shape == 'spear' else '칼 (크게 휘두르기)'

    @property
    def speed_name(self):
        return '빠름' if self.swing_time < 0.22 else '보통' if self.swing_time < 0.34 else '느림'

    def info(self):
        name, desc, c = ELEMENTS[self.element]
        return ['공격력 %d   ·   속도 %s (%.2f초)' % (self.damage, self.speed_name, self.swing_time),
                '모양: %s   ·   길이 %dpx' % (self.shape_name, self.length),
                '속성: %s - %s' % (name, desc)]

    @property
    def color(self):
        return ELEMENTS[self.element][2]

    # ---------------------------------------------------------------- 좌표
    def to_local(self, x, y):
        """칸 (x, y) → 무기 좌표 (u = 손에서 칼끝 쪽, v = 옆). 가로 그림은 왼쪽, 세로 그림은 아래쪽이 손잡이"""
        if self.tall:
            return (self.h - y - 0.5) * self.px, -(x + 0.5 - self.w / 2) * self.px
        return (x + 0.5) * self.px, (self.h / 2 - y - 0.5) * self.px

    def points(self, hx, hy, a, mirror):
        dx, dy = math.cos(a), math.sin(a)
        return [(hx + u * dx - v * mirror * dy, hy + u * dy + v * mirror * dx) for u, v in self.local]

    def tip(self, hx, hy, a):
        return hx + math.cos(a) * self.length, hy + math.sin(a) * self.length

    # ---------------------------------------------------------------- 그리기
    def texture(self):
        if self.image is None:
            buf = bytearray(self.w * self.h * 4)
            for x, y, c in self.inked:
                i = (y * self.w + x) * 4
                buf[i:i + 4] = bytes(c) + b'\xff'
            tex = SDL_CreateTexture(p2.renderer, SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_STATIC, self.w, self.h)
            SDL_SetTextureBlendMode(tex, SDL_BLENDMODE_BLEND)
            SDL_UpdateTexture(tex, None, (ctypes.c_ubyte * len(buf)).from_buffer(buf), self.w * 4)
            self.image = Image(tex)
        return self.image

    def draw(self, hx, hy, a, mirror, scale=1.0, alpha=255, tint=None):
        """손 (hx, hy)에서 a 방향으로 뻗은 무기. alpha · tint는 잔상용"""
        img = self.texture()
        SDL_SetTextureAlphaMod(img.texture, int(alpha))
        SDL_SetTextureColorMod(img.texture, *(tint or (255, 255, 255)))
        self._draw(img, hx, hy, a, mirror, scale)
        SDL_SetTextureAlphaMod(img.texture, 255)
        SDL_SetTextureColorMod(img.texture, 255, 255, 255)

    def _draw(self, img, hx, hy, a, mirror, scale):
        half = self.length * scale / 2
        cx, cy = hx + math.cos(a) * half, hy + math.sin(a) * half
        if self.tall:
            img.composite_draw(a - math.pi / 2, 'h' if mirror < 0 else '', cx, cy,
                               self.w * self.px * scale, self.h * self.px * scale)
        else:
            img.composite_draw(a, 'v' if mirror < 0 else '', cx, cy, self.w * self.px * scale, self.h * self.px * scale)

    def draw_fit(self, l, b, w, h, max_px=None):
        """사각형 안 가운데에 맞춰 그린다 (사진 앱 · HUD 칸). 그린 사각형을 돌려준다"""
        k = min(w / self.w, h / self.h)
        if max_px:
            k = min(k, max_px)
        dw, dh = self.w * k, self.h * k
        x, y = l + (w - dw) / 2, b + (h - dh) / 2
        self.texture().draw_to_origin(x, y, dw, dh)
        return x, y, dw, dh

    # ---------------------------------------------------------------- 맞히기
    def strike(self, monster, game, from_x, damage=None):
        """몬스터를 맞혔다: 데미지 + 속성 효과"""
        damage = damage or self.damage
        monster.hit(damage, 'drawing', from_x)
        e = self.element
        if e == 'fire':
            monster.burn = 3.0
        elif e == 'ice':
            monster.slow = 2.0
        elif e == 'leaf':
            game.heal(2, big=False)
        elif e == 'shock':
            monster.stun = max(monster.stun, 1.0)
        elif e == 'heavy':
            monster.vx = 520 if monster.center()[0] >= from_x else -520
            monster.stun = max(monster.stun, 0.35)
        return damage


# ==================================================================== 던진 그림
class ThrownDrawing:
    """우클릭으로 던진 그림: 빙글빙글 돌며 날아간다. 데미지 1.5배, 창은 3마리, 칼은 2마리까지 꿰뚫는다"""
    name = 'drawing'
    GRAVITY = 600

    def __init__(self, drawing, x, y, vx, vy, win, mirror):
        self.drawing = drawing
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.win = win
        self.mirror = mirror
        self.age = 0.0
        self.dead = False
        self.hits = []
        self.spin = math.atan2(vy, vx)

    @property
    def damage(self):
        return int(self.drawing.damage * 1.5)

    def rect(self):
        s = max(30, min(self.drawing.length, 120) * 0.7)
        return self.x - s / 2, self.y - s / 2, s, s

    def strike(self, monster, game):
        return self.drawing.strike(monster, game, self.x, self.damage)

    def struck(self, monster):
        self.hits.append(monster)
        if len(self.hits) >= (3 if self.drawing.shape == 'spear' else 2):
            self.dead = True

    def bounds(self):
        if self.win is not None:
            return self.win.client_rect()
        return 0, TASKBAR_H, W, H - TASKBAR_H

    def update(self, dt):
        self.age += dt
        self.vy -= self.GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.drawing.shape == 'blade':
            self.spin -= 14 * dt * self.mirror        # 칼은 돌고, 창은 날아가는 방향을 본다
        else:
            self.spin = math.atan2(self.vy, self.vx)
        l, b, w, h = self.bounds()
        if self.win is not None and self.win.state == 'min':
            self.dead = True
        if not (l <= self.x <= l + w and b <= self.y <= b + h) or self.age > 3:
            self.dead = True

    def draw(self):
        if self.win is not None:
            gfx.push_clip(*self.win.client_rect())
        d = self.drawing
        half = d.length / 2
        # 그림 가운데가 (x, y)에 오도록 손 위치를 거꾸로 잡는다
        self.drawing.draw(self.x - math.cos(self.spin) * half, self.y - math.sin(self.spin) * half,
                          self.spin, self.mirror)
        if self.win is not None:
            gfx.pop_clip()


# ==================================================================== 예시 그림 (그림판에 안 그려도 주울 수 있는 무기)
# 글자 → 그림판 팔레트 색. ' ' = 투명
SAMPLE_COLORS = {
    'r': (237, 28, 36), 'd': (136, 0, 21), 'o': (255, 127, 39), 'k': (0, 0, 0),
    'b': (63, 72, 204), 'B': (0, 162, 232), 'g': (127, 127, 127),
}
SAMPLES = {
    # 불꽃 창: 길쭉해서 창(찌르기), 빨강 · 주황이 가장 많아 불 속성
    'flame_spear': [
        '                          oo        ',
        '                        oorro       ',
        'kk  dddddddddddddddddd korrrrrrrrr  ',
        'kkkkdddddddddddddddddddkrrrrrrrrrrrr',
        'kk  dddddddddddddddddd korrrrrrrrr  ',
        '                        oorro       ',
        '                          oo        ',
    ],
    # 얼음 망치: 뭉툭해서 칼(휘두르기), 파랑이 가장 많아 얼음 속성. 세로 그림이라 위쪽(머리)이 끝
    'ice_hammer': [
        'bbbbbbbbbbbbbbbb',
        'bBBBBBBBBBBBBBBb',
        'bBBBBBBBBBBBBBBb',
        'bBBBBBBBBBBBBBBb',
        'bBBBBBBBBBBBBBBb',
        'bBBBBBBBBBBBBBBb',
        'bbbbbbbbbbbbbbbb',
    ] + ['      gggg      '] * 13 + ['     kkkkkk     '] * 2,
}


def sample(name):
    """예시 그림 → Drawing. SAMPLES의 글자 그림, 아니면 assets/pictures/<이름>.json (tools/make_pictures.py가 만든 칸 데이터)"""
    if name in SAMPLES:
        rows = SAMPLES[name]
        width = max(len(r) for r in rows)
        return Drawing([[SAMPLE_COLORS.get(ch) for ch in r.ljust(width)] for r in rows])
    import json
    import os
    with open(os.path.join(ASSETS, 'pictures', name + '.json'), encoding='utf-8') as f:
        data = json.load(f)
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    palette = {chars[i]: tuple(c) for i, c in enumerate(data['palette'])}
    return Drawing([[palette.get(ch) for ch in row] for row in data['rows']])
