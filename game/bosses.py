# 중간 보스 둘과 그 부하 · 탄.
#   구간 2 크롬 공룡 (Chrome 창): 점프 짓밟기 + 충격파 · 꼬리 치기 · 선인장 연속. 2페이즈에 익룡 2마리.
#       착지 직후 1초 경직 동안만 데미지를 다 받는다 (평소엔 절반).
#   구간 3 파일 융합 블랙홀 (%appdata%\Local\Temp): 흡입 인력장 · 파편 8방향(2페이즈 16방향, 회전 반대).
#       시스템 파일을 빨아들이면 HP 100 회복. 스크롤바(사다리)를 붙잡고 있으면 끌려가지 않는다.
import math
import random

import gfx
from monsters import Monster, Popup
from config import *


def draw_pixels(rows, l, b, px, color, flip=False):
    n = len(rows)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '#':
                x = l + ((len(row) - 1 - c) if flip else c) * px
                gfx.fill(x, b + (n - 1 - r) * px, px, px, color)


# ==================================================================== 보스 탄
class FloorShot:
    """바닥을 따라 미끄러지는 탄: 공룡 착지 충격파, 선인장"""

    def __init__(self, win, x, y, vx, value, kind):
        self.win, self.x, self.y, self.vx = win, x, y, vx
        self.value, self.kind = value, kind
        self.dead = False
        self.age = 0.0

    def update(self, dt, game):
        self.age += dt
        self.x += self.vx * dt
        if self.win not in game.wm.visible():
            self.dead = True
            return
        l, b, w, h = self.win.app.content
        if not l - 40 <= self.x <= l + w + 40 or self.age > (0.9 if self.kind == 'wave' else 4):
            self.dead = True

    def rect(self):
        if self.kind == 'wave':
            return self.x - 14, self.y, 28, 26
        return self.x - 12, self.y, 24, 48

    def draw(self):
        gfx.push_clip(*self.win.app.content)
        x, y, w, h = self.rect()
        if self.kind == 'wave':
            a = int(220 * max(0.0, 1 - self.age / 0.9))
            for i in range(3):
                gfx.fill(x + i * 8, y, 6, 10 + i * 6 if self.vx > 0 else 22 - i * 6, (83, 83, 83, a))
        else:
            c = (83, 83, 83)
            gfx.fill(x + 8, y, 8, h, c)                         # 크롬 공룡 게임 선인장
            gfx.fill(x, y + 18, 4, 16, c)
            gfx.fill(x + 4, y + 18, 4, 4, c)
            gfx.fill(x + 20, y + 24, 4, 14, c)
            gfx.fill(x + 16, y + 24, 4, 4, c)
        gfx.pop_clip()


class Shard:
    """블랙홀 파편: 사방으로 날아가는 깨진 파일 조각"""
    SPEED = 380

    def __init__(self, win, x, y, a, value=10):
        self.win, self.x, self.y = win, x, y
        self.vx, self.vy = math.cos(a) * self.SPEED, math.sin(a) * self.SPEED
        self.value = value
        self.dead = False
        self.age = 0.0

    def update(self, dt, game):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.win not in game.wm.visible():
            self.dead = True
            return
        l, b, w, h = self.win.app.content
        if not (l <= self.x <= l + w and b <= self.y <= b + h) or self.age > 4:
            self.dead = True

    def rect(self):
        return self.x - 8, self.y - 8, 16, 16

    def draw(self):
        gfx.push_clip(*self.win.app.content)
        gfx.fill(self.x - 8, self.y - 8, 16, 16, (250, 250, 250))
        gfx.frame(self.x - 8, self.y - 8, 16, 16, (120, 60, 200))
        gfx.fill(self.x - 4, self.y + 2, 8, 2, (120, 60, 200))
        gfx.fill(self.x - 4, self.y - 2, 6, 2, (120, 60, 200))
        gfx.pop_clip()


# ==================================================================== 크롬 공룡
DINO = [
    '..........######..',
    '.........##.######',
    '.........#########',
    '.........#########',
    '.........#####....',
    '.........########.',
    '#.......#####.....',
    '#.....#######.....',
    '##...#########....',
    '###.##########....',
    '##############....',
    '.############.....',
    '..##########......',
    '...########.......',
    '....###..##.......',
    '....##....#.......',
    '....#.....#.......',
    '....##....##......',
]
PTERO = [
    '....#.......',
    '...##.......',
    '..###.......',
    '.#####......',
    '###########.',
    '..#########.',
    '.....####...',
]


class ChromeDino(Monster):
    boss = True
    title = '크롬 공룡'
    PX = 7
    w = h = 18 * 7
    max_hp = 400
    contact_damage = 10
    GRAVITY = 2600

    def __init__(self, folder, rx, ry=0.0):
        super().__init__(folder, rx, ry)
        self.state, self.timer = 'ambush', 0.6
        self.facing = 1
        self.phase = 1
        self.plan = []
        self.summoned = False
        self.cactus_left = 0
        self.landed_hit = False

    @property
    def speed(self):
        return 1.3 if self.phase == 2 else 1.0

    def hit(self, damage, kind, from_x):
        # 경직 중이 아니면 절반만 들어간다. 밀리지도 기절하지도 않는다
        if self.state != 'stagger':
            damage = max(1, damage // 2)
        self.hp -= damage
        self.flash = 0.12
        if self.hp <= 0:
            self.dead = True
        self.last_damage = damage

    def update(self, dt, game):
        self.flash = max(0.0, self.flash - dt)
        self.anim_t += dt
        self.stun = 0.0
        self.burn = self.slow = 0.0
        if self.phase == 1 and self.hp <= self.max_hp // 2:
            self.phase = 2
            game.effects.append(Popup(self.win, *self.center(), '분노!', CLOSE_RED, 26))
            if not self.summoned:
                self.summoned = True
                l, b, w, h = self.area()
                for i in (0, 1):
                    game.monsters.append(Ptero(self.folder, 60 + i * (w - 180), h - 120))
        self.think(dt, game)
        self.physics(dt, game)

    def physics(self, dt, game):
        l, b, w, h = self.area()
        if self.ry > 0 or self.vy > 0:
            self.vy -= self.GRAVITY * dt
        self.rx += self.vx * dt
        self.ry += self.vy * dt
        self.rx = min(max(self.rx, 0), w - self.w)
        if self.ry <= 0:
            if self.vy < 0:
                self.ry, self.vy = 0.0, 0.0
                self.land(game)
            self.ry = 0.0

    def land(self, game):
        if self.state not in ('stomp', 'ambush'):
            return
        self.vx = 0
        cx = self.center()[0]
        _, b, _, _ = self.area()
        game.impact(0.06, 0.3, 8)
        for d in (-1, 1):
            game.bullets.append(FloorShot(self.win, cx + d * self.w / 2, b, d * 520, 10, 'wave'))
        p = game.player
        if p.win is self.win and abs(p.center()[0] - cx) < self.w / 2 + 10 and p.y < b + 40:
            game.hurt_player(20, cx)
        self.state, self.timer = 'stagger', 1.0
        game.effects.append(Popup(self.win, cx, b + self.h + 30, '경직!', (255, 200, 0), 20))

    def think(self, dt, game):
        p = game.player
        self.timer -= dt * self.speed
        cx = self.center()[0]
        px = p.center()[0] if p.win is self.win else cx
        if self.state in ('idle', 'stagger', 'windup') and self.ry == 0:
            self.facing = 1 if px >= cx else -1
        if self.state == 'ambush':
            return                      # 검색창에서 튀어나와 떨어지는 중 (착지하면 경직)
        if self.state in ('idle', 'stagger'):
            self.vx = 0
            if self.timer <= 0:
                self.next_attack(game, px, cx)
        elif self.state == 'windup':     # 꼬리 치기 준비
            if self.timer <= 0:
                l, b, w, h = self.area()
                if p.win is self.win and abs(px - cx) < self.w / 2 + 110 and p.y < b + self.h * 0.7:
                    game.hurt_player(15, cx)
                game.effects.append(Popup(self.win, cx - self.facing * 90, b + 40, '휘익', (83, 83, 83), 18))
                self.state, self.timer = 'idle', 0.7
        elif self.state == 'cactus':
            if self.timer <= 0:
                l, b, w, h = self.area()
                game.bullets.append(FloorShot(self.win, cx + self.facing * self.w / 2, b, self.facing * 460, 10,
                                              'cactus'))
                self.cactus_left -= 1
                self.timer = 0.5
                if self.cactus_left <= 0:
                    self.state, self.timer = 'idle', 0.9

    def next_attack(self, game, px, cx):
        if abs(px - cx) < self.w / 2 + 100 and random.random() < 0.6:
            self.state, self.timer = 'windup', 0.35
        elif random.random() < 0.5:
            self.state = 'stomp'
            self.vy = 1150
            self.vx = (px - cx) / 0.88 * self.speed
        else:
            self.state, self.timer = 'cactus', 0.2
            self.cactus_left = 3

    def draw(self):
        gfx.push_clip(*self.area())
        x, y, w, h = self.rect()
        c = WHITE if self.flash > 0 else (83, 83, 83) if self.state != 'stagger' else (130, 130, 130)
        draw_pixels(DINO, x, y, self.PX, c, self.facing < 0)
        if self.state == 'stagger':                             # 눈이 x
            ex = x + (11 if self.facing > 0 else 6) * self.PX
            gfx.fill(ex, y + 16 * self.PX, self.PX, self.PX, WHITE)
        if self.state == 'windup':
            gfx.text('!', x + w / 2, y + h + 20, 28, CLOSE_RED, FONT_BOLD, align='center')
        gfx.pop_clip()


class Ptero(Monster):
    """2페이즈에 날아오는 익룡: 사인 곡선으로 오르내리며 포인터에게 다가온다"""
    PX = 5
    w, h = 12 * 5, 7 * 5
    max_hp = 30
    contact_damage = 10

    def __init__(self, folder, rx, ry):
        super().__init__(folder, rx, ry)
        self.base = ry

    def physics(self, dt, game):
        l, b, w, h = self.area()
        self.rx = min(max(self.rx + self.vx * dt, 0), w - self.w)
        self.ry = min(max(self.base + math.sin(self.anim_t * 3) * 50, 0), h - self.h)

    def think(self, dt, game):
        p = game.player
        if p.win is self.win:
            px, py = p.center()
            cx, cy = self.center()
            self.facing = 1 if px > cx else -1
            self.vx = self.facing * 140
            l, b, w, h = self.area()
            self.base += max(-80 * dt, min(80 * dt, (py - b - self.h / 2) - self.base))

    def draw(self):
        gfx.push_clip(*self.area())
        x, y, w, h = self.rect()
        flap = PTERO if int(self.anim_t * 6) % 2 else PTERO[::-1]
        draw_pixels(flap, x, y, self.PX, WHITE if self.flash > 0 else (83, 83, 83), self.facing > 0)
        gfx.pop_clip()


# ==================================================================== 파일 융합 블랙홀
class Blackhole(Monster):
    boss = True
    title = '파일 융합 블랙홀'
    w = h = 120
    max_hp = 500
    contact_damage = 0
    PULL, CORE, CORE_DAMAGE = 300, 70, 15
    CYCLE = [('suck', 4.0), ('rest', 1.2), ('shards', 0.0), ('rest', 1.0), ('shards', 0.0), ('rest', 1.4)]

    def __init__(self, folder, rx, ry=0.0):
        super().__init__(folder, rx, ry)
        self.step = -1
        self.state, self.timer = 'rest', 2.0
        self.phase = 1
        self.spin = 0.0
        self.core_cd = 0.0
        self.placed = False

    def hit(self, damage, kind, from_x):
        self.hp -= damage
        self.flash = 0.12
        if self.hp <= 0:
            self.dead = True

    def update(self, dt, game):
        self.flash = max(0.0, self.flash - dt)
        self.anim_t += dt
        self.stun = self.burn = self.slow = 0.0
        self.vx = self.vy = 0.0
        l, b, w, h = self.area()
        if not self.placed:             # 폴더 창 한가운데에 자리 잡는다
            self.rx, self.ry = (w - self.w) / 2, (h - self.h) / 2 + 20
            self.placed = True
        self.rx = min(max(self.rx, 0), max(0, w - self.w))
        self.ry = min(max(self.ry, 0), max(0, h - self.h))
        if self.phase == 1 and self.hp <= self.max_hp // 2:
            self.phase = 2
            game.effects.append(Popup(self.win, *self.center(), '역회전!', (160, 90, 255), 26))
        direction = -1 if self.phase == 2 else 1
        self.spin += dt * (5 if self.state == 'suck' else 1.5) * direction
        self.core_cd = max(0.0, self.core_cd - dt)
        self.timer -= dt
        if self.timer <= 0:
            self.step = (self.step + 1) % len(self.CYCLE)
            self.state, self.timer = self.CYCLE[self.step]
            if self.state == 'shards':
                n = 16 if self.phase == 2 else 8
                cx, cy = self.center()
                for i in range(n):
                    a = self.spin + i * math.pi * 2 / n
                    game.bullets.append(Shard(self.win, cx, cy, a))
                self.state, self.timer = 'rest', 0.3
        if self.state == 'suck':
            self.suck(dt, game)

    def suck(self, dt, game):
        cx, cy = self.center()
        p = game.player
        if p.win is self.win and not p.dead:
            px, py = p.center()
            d = math.hypot(cx - px, cy - py) or 1
            k = min(1.0, max(0.3, 1 - d / 900))
            p.pull = ((cx - px) / d * self.PULL * k, (cy - py) / d * self.PULL * k)
            if d < self.CORE and self.core_cd <= 0 and not p.ladder:
                self.core_cd = 0.5
                game.hurt_player(self.CORE_DAMAGE, cx)
        for m in game.monsters:
            if isinstance(m, SysFile) and m.win is self.win and not m.dead:
                mx, my = m.center()
                d = math.hypot(cx - mx, cy - my) or 1
                m.rx += (cx - mx) / d * 55 * dt
                m.ry += (cy - my) / d * 55 * dt
                if d < 50:
                    m.dead = True       # 빨려 들어갔다
                    self.hp = min(self.max_hp, self.hp + 100)
                    game.effects.append(Popup(self.win, cx, cy + 70, '%s 흡수 +100' % m.name, (160, 90, 255), 20))

    def draw(self):
        gfx.push_clip(*self.area())
        cx, cy = self.center()
        # 빨려 들어가는 줄무늬
        if self.state == 'suck':
            for i in range(12):
                a = self.spin * 0.6 + i * math.pi / 6
                r = 150 - (self.anim_t * 160 + i * 23) % 120
                x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
                gfx.fill(int(x) // 4 * 4, int(y) // 4 * 4, 8, 4, (160, 90, 255, 160))
        # 강착 원반: 도는 4px 블록 두 겹
        for ring, (r, n, c) in enumerate(((58, 18, (120, 60, 200)), (44, 14, (70, 30, 140)))):
            for i in range(n):
                a = self.spin * (1 if ring == 0 else -1.4) + i * math.pi * 2 / n
                x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.9
                gfx.fill(int(x) // 4 * 4 - 4, int(y) // 4 * 4 - 4, 8, 8, WHITE if self.flash > 0 else c)
        gfx.circle(int(cx), int(cy), 34, BLACK)
        gfx.circle(int(cx), int(cy), 20, (20, 0, 40))
        gfx.pop_clip()


class SysFile(Monster):
    """블랙홀이 노리는 시스템 파일. 공격하면 데미지 대신 블랙홀 반대쪽으로 밀려난다 (지키는 방법)"""
    w, h = 64, 70
    max_hp = 1
    contact_damage = 0
    guard = True                        # 적이 아니다 (구간 클리어 조건에서 뺀다)

    def __init__(self, folder, rx, ry, name, icon='text_file'):
        super().__init__(folder, rx, ry)
        self.name, self.icon = name, icon

    def hit(self, damage, kind, from_x):
        hole = next((m for m in getattr(self, 'neighbors', []) if isinstance(m, Blackhole)), None)
        cx, cy = self.center()
        hx, hy = hole.center() if hole else (from_x, cy)
        d = math.hypot(cx - hx, cy - hy) or 1
        self.vx, self.vy = (cx - hx) / d * 420, (cy - hy) / d * 420
        self.flash = 0.15

    def update(self, dt, game):
        self.neighbors = [m for m in game.monsters if m.win is self.win]
        self.flash = max(0.0, self.flash - dt)
        self.anim_t += dt
        l, b, w, h = self.area()
        self.rx = min(max(self.rx + self.vx * dt, 0), w - self.w)
        self.ry = min(max(self.ry + self.vy * dt, 0), h - self.h)
        self.vx *= 1 - min(1.0, 4 * dt)
        self.vy *= 1 - min(1.0, 4 * dt)

    def draw(self):
        gfx.push_clip(*self.area())
        x, y, w, h = self.rect()
        if self.flash > 0:
            gfx.fill(x, y, w, h, (204, 232, 255))
        gfx.icon(self.icon, 48, x + 8, y + 20)
        gfx.text(self.name, x + w / 2, y + 8, 11, BLACK, align='center')
        gfx.pop_clip()
