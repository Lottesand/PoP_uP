# 주인공 포인터. 아직 그림이 없어서 직사각형 + 손바닥 표정으로 그린다.
#
# Shift OFF (OS 제어 모드): 창의 제목 표시줄 윗면과 작업 표시줄 윗면을 밟고 다닌다.
#   창 안쪽(내용 영역)은 뒤로 지나간다. 마지막으로 밟은 창 바로 위 층에 그려져서, 그보다 앞의 창에는 가려진다.
# Shift ON (침투 모드): 겹치거나 발밑에 있는 창 중 가장 앞의 창 안으로 들어간다.
#   그 창의 내용 영역이 무대가 되고(가장자리는 벽), 마우스는 조준선이 된다.
#   다시 Shift를 누르면 그 창의 제목 표시줄 위로 튀어나온다.
import math
import gfx
from config import *

PW, PH = 48, 64
RUN_SPEED = 360
CLIMB_SPEED = 240
GRAVITY = 2700
JUMP_SPEED = 900                # 최대 약 150px
JUMP_CUT = 0.45                 # 점프 키를 일찍 떼면 상승 속도를 이만큼 남긴다
POP_SPEED = 620                 # 창 밖으로 튀어나올 때 위로 솟는 속도
SWITCH_COOLDOWN = 0.3
GRAB_RANGE = 160
THROW_SPEED = 1400
THROW_GRAVITY = 600
EAT_HEAL, EAT_COOLDOWN = 12, 8.0
BUTTON_RESPAWN = 10.0
MAX_HP = 100

GLYPH = {'min': '\uE921', 'max': '\uE922', 'close': '\uE8BB'}


# ==================================================================== 발판 계산
def subtract(spans, cut0, cut1):
    out = []
    for a, b in spans:
        if cut1 <= a or cut0 >= b:
            out.append((a, b))
            continue
        if a < cut0:
            out.append((a, cut0))
        if cut1 < b:
            out.append((cut1, b))
    return out


def os_platforms(wm):
    """OFF 모드 발판: (x0, x1, y, 주인 창). 앞의 창에 덮인 부분은 밟을 수 없다."""
    plats = [(0, W, TASKBAR_H, None)]
    wins = wm.visible()
    for i, win in enumerate(wins):
        l, b, w, h = win.rect()
        top = b + h
        if top >= H:
            continue
        spans = [(l, l + w)]
        for above in wins[i + 1:]:
            al, ab, aw, ah = above.rect()
            if ab <= top <= ab + ah:
                spans = subtract(spans, al, al + aw)
        plats += [(a, b_, top, win) for a, b_ in spans if b_ - a >= 8]
    return plats


# ==================================================================== 던진 버튼
class Thrown:
    def __init__(self, name, x, y, vx, vy, win):
        self.name, self.x, self.y, self.vx, self.vy = name, x, y, vx, vy
        self.win = win                  # 창 안에서 던졌으면 그 창 (그 창 층에, 그 창 안에서만 날아간다)
        self.age = 0.0
        self.dead = False

    def bounds(self):
        if self.win is not None:
            return self.win.client_rect()
        return 0, TASKBAR_H, W, H - TASKBAR_H

    def update(self, dt):
        self.age += dt
        self.vy -= THROW_GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        l, b, w, h = self.bounds()
        if self.win is not None and self.win.state == 'min':
            self.dead = True
        if not (l + 12 <= self.x <= l + w - 12 and b + 8 <= self.y <= b + h - 8) or self.age > 3:
            self.dead = True

    def draw(self):
        if self.win is not None:
            gfx.push_clip(*self.win.client_rect())
        draw_button(self.name, self.x, self.y)
        if self.win is not None:
            gfx.pop_clip()


def draw_button(name, cx, cy, scale=1.0):
    w, h = 30 * scale, 22 * scale
    l, b = cx - w / 2, cy - h / 2
    if name == 'close':
        gfx.fill(l, b, w, h, CLOSE_RED)
        c = WHITE
    else:
        gfx.fill(l, b, w, h, (238, 238, 238))
        c = TEXT
    gfx.frame(l, b, w, h, (90, 90, 90))
    gfx.symbol(GLYPH[name], cx, cy, int(9 * scale), c)


# ==================================================================== 포인터
class Pointer:
    def __init__(self, x=160, y=TASKBAR_H):
        self.x, self.y = x, y           # 왼쪽 아래
        self.vx = self.vy = 0.0
        self.mode = 'off'
        self.win = None                 # ON: 들어가 있는 창
        self.layer = None               # 이 창 바로 위 층에 그린다 (None이면 바탕화면 층)
        self.ground = None              # 밟고 있는 발판의 주인 ('taskbar', 창, 또는 None=공중)
        self.anchor = None              # (창, 지난 left, 지난 top): 창이 움직이면 같이 움직인다
        self.left = self.right = False
        self.up = self.down = False
        self.ladder = None              # (창, 사다리 번호): 스크롤바에 매달려 있는 중
        self.jump_held = False
        self.facing = 1
        self.hp = MAX_HP
        self.held = None                # 들고 있는 버튼 이름
        self.eat_cd = 0.0
        self.switch_cd = 0.0
        self.fail_t = 0.0               # 전환 실패 흔들림
        self.hurt_t = 0.0
        self.aim = (W / 2, H / 2)

    # ---------------------------------------------------------------- 입력
    def key(self, name, down):
        if name == 'left':
            self.left = down
        elif name == 'right':
            self.right = down
        elif name == 'up':
            self.up = down
        elif name == 'down':
            self.down = down
        elif name == 'jump':
            self.jump_held = down
            if down and (self.ground is not None or self.ladder):
                self.vy = JUMP_SPEED
                self.ground = None
                self.ladder = None
            elif not down and self.vy > 0:
                self.vy *= JUMP_CUT

    def toggle(self, wm):
        if self.switch_cd > 0:
            return False
        if self.mode == 'off':
            target = self.window_to_enter(wm)
            if target is None:
                self.fail_t = 0.25
                return False
            self.enter(target)
        else:
            self.pop_out()
        self.switch_cd = SWITCH_COOLDOWN
        return True

    def window_to_enter(self, wm):
        for win in reversed(wm.visible()):
            l, b, w, h = win.rect()
            overlap = self.x < l + w and self.x + PW > l and self.y < b + h and self.y + PH > b
            if overlap or self.ground is win:
                return win
        return None

    def enter(self, win):
        self.mode, self.win, self.layer = 'on', win, win
        l, b, w, h = win.client_rect()
        self.x = min(max(self.x, l), l + w - PW)
        if self.y + PH > b + h or self.ground is win:
            self.y = b + h - PH
        self.y = max(b, self.y)
        self.vy = 0
        self.ground = None
        self.set_anchor(win)

    def pop_out(self):
        win = self.win
        l, b, w, h = win.rect()
        self.mode, self.win = 'off', None
        self.x = min(max(self.x, l), l + w - PW)
        self.y = b + h
        self.vy = POP_SPEED
        self.ground = None
        self.layer = win
        self.set_anchor(None)

    def force_out(self):
        # 들어가 있던 창이 닫히거나 최소화되면 그 자리에서 밖으로 떨어진다
        self.mode, self.win, self.layer = 'off', None, None
        self.ground = None
        self.set_anchor(None)

    def set_anchor(self, win):
        if win is None:
            self.anchor = None
        else:
            l, b, w, h = win.rect()
            self.anchor = (win, l, b + h)

    # ---------------------------------------------------------------- 버튼 뜯기 · 던지기 · 먹기
    def center(self):
        return self.x + PW / 2, self.y + PH / 2

    def grab(self, mx, my, wm):
        if self.mode != 'on' or self.held:
            return False
        win, part = wm.hit(mx, my)
        if win is None or part[0] not in GLYPH:
            return False
        for name, bl, bb, bw, bh in win.caption_buttons():
            if name == part[0]:
                cx, cy = self.center()
                if math.hypot(bl + bw / 2 - cx, bb + bh / 2 - cy) > GRAB_RANGE:
                    return False
                win.torn[name] = BUTTON_RESPAWN
                self.held = name
                return True
        return False

    def hand(self):
        return self.x + PW / 2 + self.facing * 18, self.y + PH - 12

    def throw(self, mx, my):
        if not self.held:
            return None
        hx, hy = self.hand()
        dx, dy = mx - hx, my - hy
        d = math.hypot(dx, dy) or 1
        t = Thrown(self.held, hx, hy, dx / d * THROW_SPEED, dy / d * THROW_SPEED, self.win)
        self.held = None
        return t

    def eat(self):
        if not self.held or self.eat_cd > 0:
            return False
        self.held = None
        self.hp = min(MAX_HP, self.hp + EAT_HEAL)
        self.eat_cd = EAT_COOLDOWN
        return True

    # ---------------------------------------------------------------- 물리
    def update(self, dt, wm):
        self.switch_cd = max(0.0, self.switch_cd - dt)
        self.eat_cd = max(0.0, self.eat_cd - dt)
        self.fail_t = max(0.0, self.fail_t - dt)

        visible = wm.visible()
        if self.mode == 'on' and self.win not in visible:
            self.force_out()
        if self.layer is not None and self.layer not in visible:
            self.layer = None
        # 밟고 있는 창이나 들어가 있는 창이 끌려가면 같이 움직인다
        if self.anchor:
            win, al, at = self.anchor
            if win in visible:
                l, b, w, h = win.rect()
                self.x += l - al
                self.y += (b + h) - at
                self.anchor = (win, l, b + h)
            else:
                self.anchor = None

        move = (1 if self.right else 0) - (1 if self.left else 0)
        if move:
            self.facing = move
        if self.climb(dt, wm, move):
            return
        self.vx = move * RUN_SPEED
        prev_y = self.y
        self.x += self.vx * dt
        self.vy -= GRAVITY * dt
        self.y += self.vy * dt

        if self.mode == 'on':
            self.collide_inside(prev_y)
        else:
            self.collide_os(prev_y, wm)

    # ---------------------------------------------------------------- 스크롤바 사다리
    def ladder_rect(self, wm):
        win, i = self.ladder
        if win not in wm.visible():
            return None
        lads = win.app.ladders()
        return lads[i] if i < len(lads) else None

    def find_ladder(self, wm):
        """포인터 가운데가 닿아 있는 스크롤바. OFF에서는 앞 창에 덮이지 않은 것만"""
        cx, cy = self.center()
        wins = [self.win] if self.mode == 'on' else reversed(wm.visible())
        for win in wins:
            for i, (l, b, w, h) in enumerate(win.app.ladders()):
                if l - 14 <= cx <= l + w + 14 and b - PH / 2 <= cy <= b + h + PH / 2:
                    if self.mode == 'on' or wm.hit(l + w / 2, min(cy, b + h - 1))[0] is win:
                        return win, i
        return None

    def climb(self, dt, wm, move):
        """사다리에 매달려 있으면 오르내리고 True. W/S를 누르면 붙잡는다"""
        if self.ladder and (move or self.ladder_rect(wm) is None):
            self.ladder = None
        if self.ladder is None and (self.up or (self.down and self.ground is None)):
            self.ladder = self.find_ladder(wm)
            if self.ladder and self.mode == 'off':
                self.set_anchor(self.ladder[0])
                self.layer = self.ladder[0]
        if not self.ladder:
            return False
        l, b, w, h = self.ladder_rect(wm)
        self.x = l + w / 2 - PW / 2
        self.vx = 0
        self.vy = ((1 if self.up else 0) - (1 if self.down else 0)) * CLIMB_SPEED
        self.y = min(self.y + self.vy * dt, b + h - 10)
        self.ground = None
        if self.y + PH / 2 < b and self.vy <= 0:
            # 아래 끝을 지나면 놓고 떨어진다 (바로 밑 바닥에 선다)
            self.ladder = None
            self.vy = 0
            if self.mode == 'on':
                self.collide_inside(self.y + 1)
            else:
                self.collide_os(self.y + 1, wm)
        return True

    def land(self, y, owner):
        self.y = y
        self.vy = 0
        self.ground = owner
        if self.mode == 'off':
            win = owner if owner != 'taskbar' else None
            self.layer = win
            self.set_anchor(win)

    def collide_os(self, prev_y, wm):
        self.x = min(max(self.x, 0), W - PW)
        if self.y + PH > H:
            self.y, self.vy = H - PH, min(self.vy, 0)
        if self.vy > 0:
            self.ground = None
            self.set_anchor(None)
            return
        best = None
        for x0, x1, py, owner in os_platforms(wm):
            if self.x + PW - 6 > x0 and self.x + 6 < x1 and prev_y >= py - 0.01 and self.y <= py:
                if best is None or py > best[0]:
                    best = (py, owner if owner is not None else 'taskbar')
        if best:
            self.land(*best)
        else:
            self.ground = None
            self.set_anchor(None)

    def collide_inside(self, prev_y):
        l, b, w, h = self.win.client_rect()
        self.x = min(max(self.x, l), l + w - PW)
        if self.y + PH > b + h:
            self.y, self.vy = b + h - PH, min(self.vy, 0)
        if self.vy > 0:
            self.ground = None
            return
        best = (b, 'floor') if self.y <= b else None
        for x0, x1, py in self.win.app.platforms():
            if b < py < b + h and self.x + PW - 6 > x0 and self.x + 6 < x1 and prev_y >= py - 0.01 and self.y <= py:
                if best is None or py > best[0]:
                    best = (py, 'floor')
        if best:
            self.y, self.vy, self.ground = best[0], 0, best[1]
        else:
            self.ground = None

    # ---------------------------------------------------------------- 그리기
    def face(self):
        if self.hp <= 30 or self.hurt_t > 0:
            return 'x_x'
        return '#_#' if self.mode == 'on' else '@_@'

    def draw(self):
        if self.mode == 'on':
            gfx.push_clip(*self.win.client_rect())
        shake = math.sin(self.fail_t * 80) * 4 if self.fail_t > 0 else 0
        x, y = self.x + shake, self.y
        gfx.fill(x + 3, y - 3, PW, PH, (0, 0, 0, 60))
        gfx.fill(x, y, PW, PH, WHITE)
        gfx.frame(x, y, PW, PH, BLACK, 2)
        if self.mode == 'on':
            gfx.frame(x + 2, y + 2, PW - 4, PH - 4, ACCENT)
        gfx.text(self.face(), x + PW / 2, y + PH * 0.42, 13, TEXT, align='center')
        ex = x + PW / 2 + self.facing * (PW / 2 - 6)
        gfx.fill(ex - 3, y + PH - 16, 6, 6, BLACK)            # 바라보는 쪽 표시
        if self.held:
            hx, hy = self.hand()
            draw_button(self.held, hx + shake + self.facing * 12, hy, 0.8)
        if self.mode == 'on':
            gfx.pop_clip()

    def draw_hud(self):
        # 작업 표시줄 바로 위: HP 막대, 손 슬롯, Q 쿨타임, 모드
        l, b = 12, TASKBAR_H + 10
        gfx.fill(l - 6, b - 6, 360, 34, (0, 0, 0, 120))
        gfx.text('HP', l, b + 11, 12, WHITE, FONT_BOLD)
        gfx.fill(l + 26, b + 6, 200, 10, (60, 60, 60))
        k = self.hp / MAX_HP
        gfx.fill(l + 26, b + 6, int(200 * k), 10, (19, 161, 14) if k > 0.3 else CLOSE_RED)
        sx = l + 238
        gfx.frame(sx, b, 34, 22, (200, 200, 200))
        if self.held:
            draw_button(self.held, sx + 17, b + 11, 0.85)
        q = 'Q' if self.eat_cd <= 0 else '%d' % math.ceil(self.eat_cd)
        gfx.text(q, sx + 46, b + 11, 12, WHITE if self.eat_cd <= 0 else (150, 150, 150), FONT_BOLD)
        gfx.text('Shift ' + self.mode.upper(), sx + 66, b + 11, 12, ACCENT_LIGHT if self.mode == 'on' else WHITE)


def draw_crosshair(mx, my):
    for dx, dy in ((1, 1), (0, 0)):
        c = BLACK if dx else CLOSE_RED
        gfx.line(mx - 12 + dx, my + dy, mx - 4 + dx, my + dy, c)
        gfx.line(mx + 4 + dx, my + dy, mx + 12 + dx, my + dy, c)
        gfx.line(mx + dx, my - 12 + dy, mx + dx, my - 4 + dy, c)
        gfx.line(mx + dx, my + 4 + dy, mx + dx, my + 12 + dy, c)
    gfx.fill(mx - 1, my - 1, 3, 3, CLOSE_RED)
