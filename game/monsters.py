# OS의 버그들. 몬스터는 폴더(fs 노드)에 살고, 그 폴더를 보여 주는 탐색기 창 안에서만 움직인다.
# 위치는 창 내용 영역 왼쪽 아래 기준 상대 좌표라서 창을 끌어도 같이 따라간다.
import math
import random
import gfx
from config import *

GRAVITY = 2400


class Monster:
    w, h = 40, 40
    max_hp = 20
    contact_damage = 10

    def __init__(self, folder, rx, ry=0.0):
        self.folder = folder            # 이 몬스터가 사는 폴더
        self.rx, self.ry = rx, ry       # 내용 영역 기준 위치 (왼쪽 아래)
        self.vx = self.vy = 0.0
        self.hp = self.max_hp
        self.win = None                 # 지금 이 폴더를 보여 주는 창 (없으면 쉬는 중)
        self.stun = 0.0
        self.flash = 0.0
        self.dead = False
        self.facing = -1
        self.on_ground = False

    # ---------------------------------------------------------------- 좌표
    def area(self):
        return self.win.app.content if hasattr(self.win.app, 'content') else self.win.client_rect()

    def rect(self):
        l, b, w, h = self.area()
        return l + self.rx, b + self.ry, self.w, self.h

    def center(self):
        x, y, w, h = self.rect()
        return x + w / 2, y + h / 2

    # ---------------------------------------------------------------- 맞기
    def hit(self, damage, kind, from_x):
        self.hp -= damage
        self.flash = 0.15
        if kind == 'min':
            self.stun = 1.0
        cx, cy = self.center()
        self.vx = 260 if cx >= from_x else -260
        if self.hp <= 0:
            self.dead = True

    # ---------------------------------------------------------------- 움직임
    def update(self, dt, game):
        self.flash = max(0.0, self.flash - dt)
        if self.stun > 0:
            self.stun -= dt
            self.vx *= 0.85
            self.physics(dt, game)
            return
        self.think(dt, game)
        self.physics(dt, game)

    def think(self, dt, game):
        pass

    def physics(self, dt, game):
        l, b, w, h = self.area()
        prev = self.ry
        self.vy -= GRAVITY * dt
        self.rx += self.vx * dt
        self.ry += self.vy * dt
        if self.rx < 0 or self.rx > w - self.w:
            self.rx = min(max(self.rx, 0), w - self.w)
            self.vx = -self.vx
            self.facing = -self.facing
        if self.ry + self.h > h:
            self.ry, self.vy = h - self.h, min(0, self.vy)
        self.on_ground = False
        if self.vy <= 0:
            best = 0.0 if self.ry <= 0 else None
            for x0, x1, py in game.platforms(self.win):
                ry = py - b
                if 0 < ry < h and l + self.rx + self.w - 4 > x0 and l + self.rx + 4 < x1 \
                        and prev >= ry - 0.01 and self.ry <= ry:
                    best = ry if best is None else max(best, ry)
            if best is not None:
                self.ry, self.vy, self.on_ground = best, 0.0, True

    def sees(self, player, reach_x, reach_y=120):
        """같은 창 안에 들어와 있는 포인터가 가까이 있는가"""
        if player.mode != 'on' or player.win is not self.win or player.dead:
            return False
        px, py = player.center()
        cx, cy = self.center()
        return abs(px - cx) <= reach_x and abs(py - cy) <= reach_y

    # ---------------------------------------------------------------- 그리기
    def draw(self):
        gfx.push_clip(*self.area())
        self.draw_body(*self.rect())
        x, y, w, h = self.rect()
        if self.hp < self.max_hp:
            gfx.fill(x, y + h + 6, w, 4, (60, 60, 60))
            gfx.fill(x, y + h + 6, w * max(0, self.hp) / self.max_hp, 4, CLOSE_RED)
        if self.stun > 0:
            gfx.text('z', x + w - 4, y + h + 14 + 4 * math.sin(self.stun * 10), 12, ACCENT, FONT_BOLD)
        gfx.pop_clip()

    def draw_body(self, x, y, w, h):
        gfx.fill(x, y, w, h, (200, 60, 60))
