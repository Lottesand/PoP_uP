# OS의 버그들. 몬스터는 폴더(fs 노드)에 살고, 그 폴더를 보여 주는 탐색기 창 안에서만 움직인다.
# 위치는 창 내용 영역 왼쪽 아래 기준 상대 좌표라서 창을 끌어도 같이 따라간다.
import math
import random
import gfx
import sprites
from config import *

GRAVITY = 2400


class Monster:
    w, h = 40, 40
    SHEET = None                    # game/assets/sprites/<이름>.png 도트 시트
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
        self.anim_t = 0.0

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
        self.anim_t += dt
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
        if player.win is not self.win or player.dead:
            return False
        px, py = player.center()
        cx, cy = self.center()
        return abs(px - cx) <= reach_x and abs(py - cy) <= reach_y

    # ---------------------------------------------------------------- 그리기
    def draw(self):
        gfx.push_clip(*self.area())
        x, y, w, h = self.rect()
        sprites.char(self.SHEET).draw(self.anim_state(), self.anim_t, x + w / 2, y, self.flip())
        if self.hp < self.max_hp:
            gfx.fill(x, y + h + 6, w, 4, (60, 60, 60))
            gfx.fill(x, y + h + 6, w * max(0, self.hp) / self.max_hp, 4, CLOSE_RED)
        if self.stun > 0:
            gfx.text('z', x + w - 4, y + h + 14 + 4 * math.sin(self.stun * 10), 12, ACCENT, FONT_BOLD)
        gfx.pop_clip()

    def anim_state(self):
        return 'stun'

    def flip(self):
        return False

    def common_state(self):
        if self.flash > 0:
            return 'hurt'
        if self.stun > 0:
            return 'stun'
        return None


# ==================================================================== 버그 벌레: 근거리 기습
class BugWorm(Monster):
    """위에서 내려다본 것처럼 중력 없이 사방으로 기어 다닌다. 같은 창 안의 포인터를 향해 천천히 몰려온다"""
    w, h = 44, 44
    SHEET = 'bug'
    max_hp = 20
    contact_damage = 10
    CHASE, WANDER = 75, 35          # 쫓을 때 / 어슬렁거릴 때 속도
    SPREAD = 40                     # 다른 버그와 이만큼은 떨어지려 한다

    def __init__(self, folder, rx, ry=None):
        super().__init__(folder, rx, random.uniform(0, 300) if ry is None else ry)
        self.heading = random.uniform(0, math.pi * 2)
        self.bump = 0.0             # 튕겨 나가는 중 (남은 초)

    def think(self, dt, game):
        if self.bump > 0:
            self.bump -= dt
            return
        p = game.player
        cx, cy = self.center()
        if p.win is self.win and not p.dead:
            px, py = p.center()
            want = math.atan2(py - cy, px - cx)
            speed = self.CHASE
        else:
            want = self.heading + random.uniform(-1.2, 1.2) * dt * 3
            speed = self.WANDER
        # 방향을 천천히 튼다 (홱 돌지 않고 기어가는 느낌)
        diff = (want - self.heading + math.pi) % (math.pi * 2) - math.pi
        self.heading += max(-4 * dt, min(4 * dt, diff))
        vx, vy = math.cos(self.heading) * speed, math.sin(self.heading) * speed
        # 다른 버그와 겹치지 않게 살짝 밀어낸다
        for m in game.monsters:
            if m is not self and m.win is self.win and isinstance(m, BugWorm):
                mx, my = m.center()
                d = math.hypot(cx - mx, cy - my)
                if 0 < d < self.SPREAD:
                    vx += (cx - mx) / d * 60
                    vy += (cy - my) / d * 60
        self.vx, self.vy = vx, vy

    def physics(self, dt, game):
        l, b, w, h = self.area()
        if self.stun > 0:
            self.vy *= 0.85
        self.rx += self.vx * dt
        self.ry += self.vy * dt
        if not 0 <= self.rx <= w - self.w:
            self.rx = min(max(self.rx, 0), w - self.w)
            self.heading = math.pi - self.heading
        if not 0 <= self.ry <= h - self.h:
            self.ry = min(max(self.ry, 0), h - self.h)
            self.heading = -self.heading

    def hit(self, damage, kind, from_x):
        super().hit(damage, kind, from_x)
        self.vy = 0
        self.bump = 0.25

    def anim_state(self):
        return self.common_state() or 'crawl'

    def angle(self):
        """시트는 머리가 위(+y)를 본다. 기어가는 쪽(상하좌우 네 방향 중 가까운 쪽)으로 돌려 그린다.
        비스듬히 돌리면 도트가 깨져서 90도 단위로만 돌린다"""
        a = math.atan2(self.vy, self.vx) if (self.vx or self.vy) else self.heading
        return round(a / (math.pi / 2)) * (math.pi / 2) - math.pi / 2

    def draw(self):
        gfx.push_clip(*self.area())
        x, y, w, h = self.rect()
        sprites.char(self.SHEET).draw_rotated(self.anim_state(), self.anim_t, x + w / 2, y + h / 2, self.angle())
        if self.hp < self.max_hp:
            gfx.fill(x, y + h + 6, w, 4, (60, 60, 60))
            gfx.fill(x, y + h + 6, w * max(0, self.hp) / self.max_hp, 4, CLOSE_RED)
        gfx.pop_clip()

    def burst_in(self, edge):
        """창 가장자리 틈에서 기어 나온다. edge: left / right / top / bottom"""
        self.heading = {'left': 0, 'right': math.pi, 'bottom': math.pi / 2, 'top': -math.pi / 2}[edge]

    def bounce(self, from_xy):
        # 포인터에 부딪히면 반대쪽으로 튕겨 나간다
        cx, cy = self.center()
        a = math.atan2(cy - from_xy[1], cx - from_xy[0])
        self.vx, self.vy = math.cos(a) * 260, math.sin(a) * 260
        self.bump = 0.45


# ==================================================================== 캐럿 ( | ): 숫자탄 사격
class Digit:
    """캐럿이 쏘는 숫자탄. 숫자가 곧 데미지"""
    SPEED = 420

    def __init__(self, win, x, y, tx, ty):
        self.win, self.x, self.y = win, x, y
        d = math.hypot(tx - x, ty - y) or 1
        self.vx, self.vy = (tx - x) / d * self.SPEED, (ty - y) / d * self.SPEED
        self.value = random.randint(0, 9)
        self.dead = False
        self.age = 0.0

    def update(self, dt, game):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.win not in game.wm.visible():
            self.dead = True
            return
        l, b, w, h = self.win.client_rect()
        if not (l <= self.x <= l + w and b <= self.y <= b + h) or self.age > 4:
            self.dead = True

    def rect(self):
        return self.x - 7, self.y - 9, 14, 18

    def draw(self):
        gfx.push_clip(*self.win.client_rect())
        gfx.fill(self.x - 9, self.y - 11, 18, 22, (255, 255, 255, 220))
        gfx.frame(self.x - 9, self.y - 11, 18, 22, CLOSE_RED)
        gfx.text(str(self.value), self.x, self.y, 16, CLOSE_RED, FONT_BOLD, align='center')
        gfx.pop_clip()


class Caret(Monster):
    w, h = 28, 52
    SHEET = 'caret'
    max_hp = 30
    contact_damage = 5
    PERIOD, AIM = 1.5, 0.5

    def __init__(self, folder, rx, ry=0.0):
        super().__init__(folder, rx, ry)
        self.timer = random.uniform(0.6, self.PERIOD)
        self.aiming = False
        self.home = rx
        self.recoil = 0.0

    def think(self, dt, game):
        self.timer -= dt
        self.recoil = max(0.0, self.recoil - dt)
        # 발판 위에서 좌우로 조금씩
        if abs(self.rx - self.home) > 30:
            self.vx = -math.copysign(30, self.rx - self.home)
        elif self.vx == 0:
            self.vx = 30
        if not self.aiming and self.timer <= 0:
            if self.sees(game.player, 700, 500):
                self.aiming, self.timer = True, self.AIM
                self.vx = 0
            else:
                self.timer = 0.5
        elif self.aiming and self.timer <= 0:
            self.aiming, self.timer = False, self.PERIOD
            cx, cy = self.center()
            px, py = game.player.center()
            game.bullets.append(Digit(self.win, cx, cy + 10, px, py))
            self.recoil = 0.2

    def anim_state(self):
        if self.common_state():
            return self.common_state()
        if self.aiming:
            return 'aim'
        return 'shoot' if self.recoil > 0 else 'idle'



# ==================================================================== 윈도우 로고: 다가와서 자폭
class Bomber(Monster):
    w, h = 44, 52
    SHEET = 'winlogo'
    max_hp = 15
    contact_damage = 0
    SENSE, CHASE, WANDER = 250, 200, 60
    FUSE, RADIUS, BLAST = 3.0, 160, 30

    def __init__(self, folder, rx, ry=0.0):
        super().__init__(folder, rx, ry)
        self.state = 'wander'
        self.fuse = 0.0
        self.vx = self.WANDER

    def hit(self, damage, kind, from_x):
        super().hit(damage, kind, from_x)
        if kind == 'min':
            self.state, self.fuse = 'chase', 0.0       # 최소화 버튼에 맞으면 카운트다운 처음부터

    def anim_state(self):
        return self.common_state() or {'wander': 'walk', 'chase': 'chase', 'count': 'count'}[self.state]

    def draw(self):
        super().draw()
        if self.state == 'count':
            x, y, w, h = self.rect()
            gfx.push_clip(*self.area())
            gfx.text(str(math.ceil(self.fuse)), x + w / 2, y + h + 16, 18, CLOSE_RED, FONT_BOLD, align='center')
            gfx.pop_clip()

    def think(self, dt, game):
        p = game.player
        if self.state == 'wander':
            if self.sees(p, self.SENSE, 200):
                self.state = 'chase'
            elif self.vx == 0:
                self.vx = self.WANDER
        elif self.state == 'chase':
            px, py = p.center()
            cx, cy = self.center()
            self.facing = 1 if px > cx else -1
            self.vx = self.facing * self.CHASE
            if not self.sees(p, self.SENSE + 100, 260):
                self.state = 'wander'
            elif abs(px - cx) < 70:
                self.state, self.fuse = 'count', self.FUSE
                self.vx = 0
        elif self.state == 'count':
            self.vx = 0
            self.fuse -= dt
            if self.fuse <= 0:
                self.dead = True
                game.explode(self.win, *self.center(), self.RADIUS, self.BLAST)



class Popup:
    """맞은 자리에서 떠오르는 데미지 숫자"""

    def __init__(self, win, x, y, text, color=CLOSE_RED):
        self.win, self.x, self.y, self.text, self.color = win, x, y, text, color
        self.t = 0.0
        self.dead = False

    def update(self, dt, game):
        self.t += dt
        self.y += 60 * dt
        self.dead = self.t > 0.7

    def draw(self):
        a = int(255 * min(1.0, (0.7 - self.t) / 0.3))
        if self.win is not None:
            gfx.push_clip(*self.win.client_rect())
        gfx.text(self.text, self.x + 1, self.y - 1, 16, (0, 0, 0, a // 2), FONT_BOLD, align='center')
        gfx.text(self.text, self.x, self.y, 16, self.color + (a,), FONT_BOLD, align='center')
        if self.win is not None:
            gfx.pop_clip()


KINDS = {'bug': BugWorm, 'caret': Caret, 'bomber': Bomber}
