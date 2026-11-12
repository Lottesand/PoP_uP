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
        elif name == 'jump':
            self.jump_held = down
            if down and self.ground is not None:
                self.vy = JUMP_SPEED
                self.ground = None
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
        self.vx = move * RUN_SPEED
        prev_y = self.y
        self.x += self.vx * dt
        self.vy -= GRAVITY * dt
        self.y += self.vy * dt

        if self.mode == 'on':
            self.collide_inside(prev_y)
        else:
            self.collide_os(prev_y, wm)

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
