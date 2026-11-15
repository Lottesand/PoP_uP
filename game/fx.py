# 단순한 타격 이펙트: 4px 블록으로만 그린다 (도트 캐릭터와 같은 굵기)
import math
import random
import gfx
from config import *

BLOCK = 4


def snap(v):
    return int(v) // BLOCK * BLOCK


class Effect:
    """win 창 층에 그린다. clip이면 그 창 안으로 자른다"""
    life = 0.2

    def __init__(self, win, clip=True):
        self.win, self.clip = win, clip
        self.t = 0.0
        self.dead = False

    def update(self, dt, game):
        self.t += dt
        self.dead = self.t >= self.life

    def draw(self):
        clip = self.clip and self.win is not None
        if clip:
            gfx.push_clip(*self.win.client_rect())
        self.paint(self.t / self.life)
        if clip:
            gfx.pop_clip()

    def paint(self, k):
        pass


class PokeTrail(Effect):
    """찌르기: 손에서 찌른 끝까지 잠깐 남는 굵은 선, 끝에 작은 십자"""
    life = 0.1

    def __init__(self, win, x0, y0, x1, y1, clip=True):
        super().__init__(win, clip)
        self.a, self.b = (x0, y0), (x1, y1)

    def paint(self, k):
        (x0, y0), (x1, y1) = self.a, self.b
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / BLOCK))
        start = int(n * k)                      # 손 쪽부터 사라진다
        for i in range(start, n + 1):
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            gfx.fill(snap(x), snap(y), BLOCK, BLOCK, WHITE)
            gfx.frame(snap(x) - 1, snap(y) - 1, BLOCK + 2, BLOCK + 2, ACCENT)
        for dx, dy in ((0, 0), (BLOCK, 0), (-BLOCK, 0), (0, BLOCK), (0, -BLOCK)):
            gfx.fill(snap(x1) + dx, snap(y1) + dy, BLOCK, BLOCK, ACCENT)


class Spark(Effect):
    """맞은 자리: 블록 몇 개가 사방으로 튀고 가운데가 번쩍"""
    life = 0.25

    def __init__(self, win, x, y, color=(255, 200, 0), n=6, clip=True):
        super().__init__(win, clip)
        self.x, self.y, self.color = x, y, color
        a0 = random.uniform(0, math.pi * 2)
        self.dirs = [(math.cos(a0 + i * math.pi * 2 / n), math.sin(a0 + i * math.pi * 2 / n)) for i in range(n)]

    def paint(self, k):
        if k < 0.35:
            s = BLOCK * 3
            gfx.fill(snap(self.x) - s // 2, snap(self.y) - s // 2, s, s, WHITE)
        d = 10 + 40 * k
        size = BLOCK * 2 if k < 0.5 else BLOCK
        for dx, dy in self.dirs:
            gfx.fill(snap(self.x + dx * d), snap(self.y + dy * d), size, size, self.color)


class Ring(Effect):
    """폭발: 네모난 고리가 반경까지 퍼지며 얇아진다"""
    life = 0.35

    def __init__(self, win, x, y, radius, color=(255, 140, 0), clip=True):
        super().__init__(win, clip)
        self.x, self.y, self.r, self.color = x, y, radius, color

    def paint(self, k):
        r = snap(self.r * (0.3 + 0.7 * k))
        t = BLOCK * (3 if k < 0.4 else 2 if k < 0.7 else 1)
        x, y = snap(self.x), snap(self.y)
        gfx.frame(x - r, y - r, 2 * r, 2 * r, self.color, t)
        if k < 0.3:
            s = snap(self.r * 0.5 * (1 - k / 0.3)) + BLOCK
            gfx.fill(x - s, y - s, 2 * s, 2 * s, (255, 220, 120))
