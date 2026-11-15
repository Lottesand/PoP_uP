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
    """찌르기 (평타): 손에서 끝까지 두 줄 굵기 궤적 + 끝에서 터지는 클릭 표시(네모가 커지고 네 모서리로 선이 튐)"""
    life = 0.16

    def __init__(self, win, x0, y0, x1, y1, clip=True):
        super().__init__(win, clip)
        self.a, self.b = (x0, y0), (x1, y1)
        d = math.hypot(x1 - x0, y1 - y0) or 1
        self.n = ((y0 - y1) / d, (x1 - x0) / d)        # 궤적에 수직인 방향 (두 줄 굵기)

    def paint(self, k):
        (x0, y0), (x1, y1) = self.a, self.b
        if k < 0.6:
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / BLOCK))
            start = int(n * k / 0.6)               # 손 쪽부터 사라진다
            for i in range(start, n + 1):
                x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
                for side in (0, 1):
                    sx, sy = x + self.n[0] * BLOCK * side, y + self.n[1] * BLOCK * side
                    gfx.fill(snap(sx), snap(sy), BLOCK, BLOCK, WHITE if i > n * 0.6 else ACCENT_LIGHT)
        # 끝: 클릭 표시
        cx, cy = snap(x1), snap(y1)
        r = snap(6 + 18 * k) + BLOCK
        gfx.frame(cx - r, cy - r, 2 * r, 2 * r, ACCENT, BLOCK if k < 0.5 else 2)
        if k < 0.35:
            gfx.fill(cx - BLOCK * 2, cy - BLOCK * 2, BLOCK * 4, BLOCK * 4, WHITE)
        d = r + BLOCK * 2
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            for j in range(2):
                gfx.fill(cx + dx * (d + j * BLOCK) - BLOCK // 2, cy + dy * (d + j * BLOCK) - BLOCK // 2,
                         BLOCK, BLOCK, ACCENT)


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


class Mote(Effect):
    """그림 무기 끝에서 흩날리는 속성 알갱이 (4px 블록)
    fire 위로 솟는 불티 · ice 천천히 내려앉는 눈 · leaf 하늘하늘 잎 · shock 지지직 번개 · heavy 퍼지는 먼지"""
    life = 0.45

    def __init__(self, win, x, y, element, clip=True):
        super().__init__(win, clip)
        self.x, self.y, self.element = x, y, element
        self.vx, self.vy = random.uniform(-40, 40), random.uniform(-40, 40)
        if element == 'fire':
            self.vy = random.uniform(60, 140)
        elif element == 'ice':
            self.vy = random.uniform(-60, -20)
            self.life = 0.6
        elif element == 'heavy':
            self.vx, self.vy = random.uniform(-90, 90), random.uniform(-10, 40)
        self.phase = random.uniform(0, 6)

    def update(self, dt, game):
        super().update(dt, game)
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.element == 'leaf':
            self.x += math.sin(self.t * 12 + self.phase) * 60 * dt

    def paint(self, k):
        x, y, e = snap(self.x), snap(self.y), self.element
        a = int(255 * (1 - k))
        if e == 'fire':
            col = (255, 230, 120) if k < 0.3 else (255, 120, 0) if k < 0.6 else (200, 40, 0)
            s = BLOCK * (2 if k < 0.5 else 1)
            gfx.fill(x, y, s, s, col + (a,))
        elif e == 'ice':
            gfx.fill(x, y, BLOCK, BLOCK, (230, 248, 255, a))
            if int(self.t * 20) % 2:
                for dx, dy in ((BLOCK, 0), (-BLOCK, 0), (0, BLOCK), (0, -BLOCK)):
                    gfx.fill(x + dx, y + dy, BLOCK, BLOCK, (140, 210, 255, a))
        elif e == 'leaf':
            gfx.fill(x, y, BLOCK * 2, BLOCK, (60, 200, 90, a))
            gfx.fill(x + BLOCK, y + BLOCK, BLOCK, BLOCK, (30, 140, 60, a))
        elif e == 'shock':
            if int(self.t * 30) % 2 == 0:
                px, py = x, y
                for i in range(3):
                    nx, ny = px + random.choice((-BLOCK, BLOCK)), py + BLOCK
                    gfx.fill(nx, ny, BLOCK, BLOCK, (255, 240, 80, a))
                    px, py = nx, ny
        elif e == 'heavy':
            s = snap(BLOCK + 10 * k) + BLOCK
            gfx.fill(x - s // 2, y - s // 2, s, s, (150, 150, 150, a // 2))
        else:
            gfx.fill(x, y, BLOCK, BLOCK, (255, 255, 255, a))


class ElementBurst(Effect):
    """그림 무기로 맞힌 자리: 번쩍 + 속성 모양으로 터진다"""
    life = 0.32

    def __init__(self, win, x, y, element, color, big=False, clip=True):
        super().__init__(win, clip)
        self.x, self.y, self.element, self.color, self.big = x, y, element, color, big
        n = 10 if big else 7
        a0 = random.uniform(0, math.pi * 2)
        self.dirs = [(math.cos(a0 + i * math.pi * 2 / n), math.sin(a0 + i * math.pi * 2 / n)) for i in range(n)]

    def paint(self, k):
        x, y, e, c = snap(self.x), snap(self.y), self.element, self.color
        if k < 0.25:                                    # 가운데 번쩍
            s = BLOCK * (6 if self.big else 4)
            gfx.fill(x - s // 2, y - s // 2, s, s, WHITE)
        reach = (16 + 60 * k) * (1.4 if self.big else 1.0)
        if e == 'ice':                                  # 얼음: 십자로 뻗는 결정
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)):
                for j in range(int(reach * (1 - k) / BLOCK)):
                    gfx.fill(snap(x + dx * j * BLOCK), snap(y + dy * j * BLOCK), BLOCK, BLOCK,
                             (200, 240, 255) if j % 2 else c)
        elif e == 'shock':                              # 번개: 사방으로 꺾이는 줄기
            if int(k * 12) % 2 == 0:
                for dx, dy in self.dirs[:5]:
                    px, py = x, y
                    for j in range(5):
                        px += dx * BLOCK * 2 + random.choice((-BLOCK, 0, BLOCK))
                        py += dy * BLOCK * 2 + random.choice((-BLOCK, 0, BLOCK))
                        gfx.fill(snap(px), snap(py), BLOCK, BLOCK, (255, 240, 80))
        else:                                           # 불 · 풀 · 묵직함 · 없음: 블록이 튀어 나간다
            size = BLOCK * (3 if k < 0.4 else 2 if k < 0.7 else 1)
            for dx, dy in self.dirs:
                gfx.fill(snap(x + dx * reach), snap(y + dy * reach + (40 * k if e == 'fire' else 0)), size, size, c)
        r = snap(10 + reach * 0.8)                      # 속성 색 고리
        gfx.frame(x - r, y - r, 2 * r, 2 * r, c, BLOCK if k < 0.5 else 2)


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
