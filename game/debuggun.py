# 디버그 건: VS Code 왼쪽 활동 표시줄의 [실행 및 디버그] 아이콘(재생 삼각형 + 벌레)을 뜯어서 얻는 원거리 무기.
#   좌클릭: 빨간 중단점(●)을 쏜다 (6 데미지, 0.4초마다, 맞은 적 1.5초 결빙). 창 테두리를 세 번 맞히면 3초 동안 뚫린다.
#   우클릭: F5 Run 대쉬 (약 400px, 지나가며 닿은 적 20 데미지 관통, 대쉬 중 무적, 쿨 4초)
#   E: 버리기 (아이콘이 VS Code로 돌아간다)
import math
import gfx
from config import *

SHOT_DAMAGE, SHOT_COOLDOWN, SHOT_SPEED, FREEZE = 6, 0.4, 1500, 1.5
F5_SPEED, F5_TIME, F5_COOLDOWN, F5_DAMAGE = 1600, 0.25, 4.0, 20
BREAKPOINT = (229, 20, 0)
ICON_GRAY = (204, 204, 204)

# [실행 및 디버그] 아이콘 도트 (위에서부터, '#' = 삼각형 테두리, 'b' = 벌레)
ICON = [
    '..#...........',
    '..##..........',
    '..#.#.........',
    '..#..#........',
    '..#...#.......',
    '..#....#......',
    '..#.....#.....',
    '..#......#....',
    '..#.....#.....',
    'b.b.bb.#......',
    '.bbbb.#.......',
    'bbbbbb........',
    '.bbbb.........',
    'b.bb.b........',
]


HELD_GRAY = (70, 70, 70)            # 손에 들면 하얀 창 위에서도 보이게 진하게


def icon_drawing(color=ICON_GRAY):
    """아이콘 도트 → drawing.Drawing (돌려 그리기 · 화면 크기 맞추기를 그대로 쓴다)"""
    from drawing import Drawing
    cells = [[color if ch in '#b' else None for ch in row] for row in ICON]
    d = Drawing(cells)
    d.px = 3.0                          # 손에 들면 42px
    d.length, d.thick = d.w * d.px, d.h * d.px
    return d


_icons = {}


def icon(color=ICON_GRAY):
    if color not in _icons:
        _icons[color] = icon_drawing(color)
    return _icons[color]


def draw_breakpoint(x, y, r, alpha=255):
    gfx.circle(int(x), int(y), int(r), BREAKPOINT + (alpha,))
    if r >= 4:
        gfx.fill(int(x - r * 0.45), int(y + r * 0.1), max(2, int(r * 0.4)), max(2, int(r * 0.4)),
                 (255, 140, 120, alpha))


class DebugGun:
    kind = 'gun'
    color = BREAKPOINT

    def __init__(self, source):
        self.source = source            # 아이콘을 뜯어 온 VS Code 앱 (버리면 돌려준다)

    def drop(self):
        if self.source is not None:
            self.source.debug_taken = False

    def info(self):
        return ['좌클릭: 중단점 발사 %d · %.1f초마다 · %.1f초 결빙' % (SHOT_DAMAGE, SHOT_COOLDOWN, FREEZE),
                '우클릭: F5 Run 대쉬 %d 관통 · 쿨 %d초' % (F5_DAMAGE, F5_COOLDOWN)]

    def muzzle(self, hx, hy, a):
        return hx + math.cos(a) * icon(HELD_GRAY).length, hy + math.sin(a) * icon(HELD_GRAY).length

    def draw(self, hx, hy, a, mirror, recoil=0.0):
        """손에 든 아이콘: 재생 삼각형의 뾰족한 끝이 조준 쪽을 본다"""
        hx, hy = hx - math.cos(a) * recoil * 10, hy - math.sin(a) * recoil * 10
        icon(HELD_GRAY).draw(hx, hy, a, mirror)

    def draw_icon(self, l, b, size):
        icon().draw_fit(l, b, size, size)


class Shot:
    """중단점 한 발: 빨간 점이 곧장 날아가고 처음 맞힌 적에서 사라진다"""
    name = 'breakpoint'
    damage = SHOT_DAMAGE

    def __init__(self, x, y, a, win):
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * SHOT_SPEED, math.sin(a) * SHOT_SPEED
        self.win = win
        self.dead = False
        self.hits = []
        self.age = 0.0
        self.trail = []
        self.wall = None                # 창 안에서 쏴서 벽(테두리)에 닿은 자리 → play_mode가 금을 낸다

    def rect(self):
        return self.x - 9, self.y - 9, 18, 18

    def strike(self, monster, game):
        monster.hit(self.damage, 'breakpoint', self.x)
        monster.stun = max(monster.stun, FREEZE)        # 중단점에 걸린 것처럼 멈춘다
        monster.slow = max(monster.slow, FREEZE)        # 파랗게 얼어 보인다
        return self.damage

    def struck(self, monster):
        self.hits.append(monster)
        self.dead = True

    def bounds(self):
        if self.win is not None:
            return self.win.client_rect()
        return 0, TASKBAR_H, W, H - TASKBAR_H

    def update(self, dt):
        self.age += dt
        self.trail = ([(self.x, self.y)] + self.trail)[:4]
        self.x += self.vx * dt
        self.y += self.vy * dt
        l, b, w, h = self.bounds()
        if not (l <= self.x <= l + w and b <= self.y <= b + h) or self.age > 1.5:
            if self.win is not None and self.age <= 1.5 and not self.dead:
                self.wall = (min(max(self.x, l), l + w), min(max(self.y, b), b + h))
            self.dead = True
        if self.win is not None and self.win.state == 'min':
            self.dead = True

    def draw(self):
        if self.win is not None:
            gfx.push_clip(*self.win.client_rect())
        for i, (x, y) in enumerate(self.trail[1:]):
            draw_breakpoint(x, y, 6 - i * 2, 150 - i * 50)
        draw_breakpoint(self.x, self.y, 8)
        if self.win is not None:
            gfx.pop_clip()
