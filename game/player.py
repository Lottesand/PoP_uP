# 주인공 포인터. 아직 그림이 없어서 직사각형 + 손바닥 표정으로 그린다.
#
# Shift OFF (OS 제어 모드): 창의 제목 표시줄 윗면과 작업 표시줄 윗면을 밟고 다닌다.
#   창 안쪽(내용 영역)은 뒤로 지나간다. 마지막으로 밟은 창 바로 위 층에 그려져서, 그보다 앞의 창에는 가려진다.
# Shift ON (공격 모드): 마우스가 조준선이 되고 창들이 단단한 벽이 된다. 기본 무기는 손가락 찌르기(좌클릭).
#   창 테두리를 세 번 찌르면 금이 가다 부서지고, 부서진 자리로 그 창 안에 들어간다.
#   창 안에서는 그 창의 내용 영역이 무대가 되고(가장자리는 벽), Shift를 꺼도 창 안에 그대로 있다.
#   나가려면 공격 모드에서 창 테두리를 안쪽에서 세 번 찔러 깬다.
import math
import gfx
import sprites
from config import *

PW, PH = 48, 64
RUN_SPEED = 360
CLIMB_SPEED = 240
GRAVITY = 2700
JUMP_SPEED = 900                # 최대 약 150px
JUMP_CUT = 0.45                 # 점프 키를 일찍 떼면 상승 속도를 이만큼 남긴다
SWITCH_COOLDOWN = 0.3
GRAB_RANGE = 160
THROW_SPEED = 1400
THROW_GRAVITY = 600
EAT_HEAL, EAT_COOLDOWN = 12, 8.0
POKE_REACH, POKE_TIME, POKE_COOLDOWN, POKE_DAMAGE = 60, 0.16, 0.28, 8
AIR_JUMPS, AIR_JUMP_SPEED = 1, 820    # 2단 점프: 공중에서 한 번 더
DASH_SPEED, DASH_TIME, DASH_COOLDOWN = 1100, 0.14, 0.45   # 대쉬: 약 150px, 그동안 무적
BREAK_HITS = 3                  # 창 테두리를 이만큼 찌르면 부서진다
BUTTON_RESPAWN = 10.0
MAX_HP = 100
INVINCIBLE = 1.0               # 맞은 뒤 무적 시간
KNOCKBACK = 300

GLYPH = {'min': '\uE921', 'max': '\uE922', 'close': '\uE8BB'}
FACES = {'@_@': 'calm', '#_#': 'angry', 'x_x': 'dizzy'}     # \uD45C\uC815 \u2192 \uC2A4\uD504\uB77C\uC774\uD2B8 \uC2DC\uD2B8


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
# 버튼 무기 (데미지, 효과): 닫기 = 3마리까지 관통, 최소화 = 1초 기절, 최대화 = 바닥에 닿으면 2초 굴러가며 최대 5번
DAMAGE = {'close': 25, 'min': 10, 'max': 8}
PIERCE = 3
ROLL_TIME, ROLL_SPEED, ROLL_HITS = 2.0, 520, 5


class Thrown:
    def __init__(self, name, x, y, vx, vy, win):
        self.name, self.x, self.y, self.vx, self.vy = name, x, y, vx, vy
        self.win = win                  # 창 안에서 던졌으면 그 창 (그 창 층에, 그 창 안에서만 날아간다)
        self.age = 0.0
        self.dead = False
        self.hits = []                  # 이미 맞힌 몬스터 (같은 몬스터는 한 번만)
        self.rolling = 0.0
        self.trail = []                 # 지난 위치 몇 개 (잔상)

    @property
    def damage(self):
        return DAMAGE[self.name]

    def rect(self):
        return self.x - 15, self.y - 11, 30, 22

    def struck(self, monster):
        """몬스터를 맞혔다. 무기마다 계속 날아갈지 정한다"""
        self.hits.append(monster)
        if self.name == 'min':
            self.dead = True
        elif self.name == 'close' and len(self.hits) >= PIERCE:
            self.dead = True
        elif self.name == 'max' and len(self.hits) >= ROLL_HITS:
            self.dead = True

    def bounds(self):
        if self.win is not None:
            return self.win.client_rect()
        return 0, TASKBAR_H, W, H - TASKBAR_H

    def update(self, dt):
        self.age += dt
        self.trail = ([(self.x, self.y)] + self.trail)[:4]
        l, b, w, h = self.bounds()
        if self.rolling > 0:
            # 최대화 버튼: 바닥을 굴러간다
            self.rolling -= dt
            self.x += self.vx * dt
            if self.rolling <= 0 or not l + 12 <= self.x <= l + w - 12:
                self.dead = True
            return
        self.vy -= THROW_GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.win is not None and self.win.state == 'min':
            self.dead = True
        if self.name == 'max' and self.y <= b + 11 and l + 12 <= self.x <= l + w - 12:
            self.y, self.vy = b + 11, 0.0
            self.vx = math.copysign(ROLL_SPEED, self.vx or 1)
            self.rolling = ROLL_TIME
            self.hits = []
            return
        if not (l + 12 <= self.x <= l + w - 12 and b + 8 <= self.y <= b + h - 8) or self.age > 3:
            self.dead = True

    def draw(self):
        if self.win is not None:
            gfx.push_clip(*self.win.client_rect())
        for i, (x, y) in enumerate(self.trail[1:]):
            s = 14 - i * 4
            gfx.fill(int(x) // 4 * 4 - s // 2, int(y) // 4 * 4 - s // 2, s, s,
                     (CLOSE_RED if self.name == 'close' else (180, 180, 180)) + (150 - i * 45,))
        spin = abs(math.cos(self.age * 22))           # 동전처럼 빙글빙글 돈다
        draw_button(self.name, self.x, self.y, 1.0, max(0.2, spin))
        if self.win is not None:
            gfx.pop_clip()


def draw_button(name, cx, cy, scale=1.0, xscale=1.0):
    w, h = 30 * scale * xscale, 22 * scale
    l, b = cx - w / 2, cy - h / 2
    if name == 'close':
        gfx.fill(l, b, w, h, CLOSE_RED)
        c = WHITE
    else:
        gfx.fill(l, b, w, h, (238, 238, 238))
        c = TEXT
    gfx.frame(l, b, w, h, (90, 90, 90))
    if xscale > 0.5:
        gfx.symbol(GLYPH[name], cx, cy, int(9 * scale), c)


# ==================================================================== 포인터
class Pointer:
    def __init__(self, x=160, y=TASKBAR_H):
        self.x, self.y = x, y           # 왼쪽 아래
        self.vx = self.vy = 0.0
        self.mode = 'off'
        self.win = None                 # ON에서 들어가 있는 창 (None이면 창 밖 공격 모드)
        self.ghosts = set()             # Shift ON 순간 겹쳐 있던 창: 빠져나올 때까지는 벽이 아니다
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
        self.weapon = None              # 특수 무기 하나: 그림(drawing.Drawing) 또는 디버그 건(debuggun.DebugGun)
        self.shot_cd = self.f5_cd = self.recoil = 0.0
        self.dash_speed = DASH_SPEED
        self.dash_power = 0             # F5 대쉬: 지나가며 닿은 적에게 주는 데미지
        self.dash_hits = []
        self.pull = (0.0, 0.0)          # 블랙홀이 끌어당기는 속도 (매 프레임 새로 정해진다, 사다리에선 무시)
        self.swing_t = self.swing_len = self.swing_cd = 0.0
        self.swing_from = self.swing_to = 0.0
        self.swing_hits = []            # 이번 휘두르기에 이미 맞힌 몬스터
        self.swing_aim = 0.0            # 휘두를 때 조준한 각도
        self.swing_trail = []           # 지난 몇 프레임의 무기 자세 (잔상 · 칼끝 궤적)
        self.eat_cd = 0.0
        self.switch_cd = 0.0
        self.fail_t = 0.0               # 전환 실패 흔들림
        self.hurt_t = 0.0               # x_x 표정
        self.invincible = 0.0
        self.kb = 0.0                   # 넉백 가로 속도 (점점 줄어든다)
        self.dead = False
        self.anim_t = 0.0
        self.poke_t = 0.0               # 찌르는 중 (남은 시간)
        self.poke_cd = 0.0
        self.poke_dir = (1.0, 0.0)
        self.air_jumps = AIR_JUMPS      # 남은 공중 점프 (땅·사다리에 닿으면 다시 찬다)
        self.dash_t = self.dash_cd = 0.0
        self.dash_dir = (1.0, 0.0)
        self.air_dash = True            # 공중에서는 대쉬 한 번 (땅에 닿으면 다시)
        self.dash_trail = []            # 대쉬 잔상 위치
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
            elif down and self.air_jumps > 0 and not self.dead:
                self.air_jumps -= 1          # 2단 점프
                self.vy = AIR_JUMP_SPEED
                self.dash_t = 0.0
            elif not down and self.vy > 0:
                self.vy *= JUMP_CUT

    @property
    def inside(self):
        return self.win is not None

    def toggle(self, wm):
        if self.switch_cd > 0:
            return False
        if self.mode == 'off':
            self.mode = 'on'
            self.ghosts = {w for w in wm.visible() if self.overlaps(w.rect())}
        else:
            self.mode = 'off'           # 창 안이면 그대로 창 안 (마우스만 다시 윈도우 조작용)
        self.switch_cd = SWITCH_COOLDOWN
        return True

    def overlaps(self, rect):
        l, b, w, h = rect
        return self.x < l + w and self.x + PW > l and self.y < b + h and self.y + PH > b

    def enter(self, win, at=None):
        """창 안으로 들어간다. at: 부서진 자리 (없으면 지금 자리에서 가장 가까운 곳)"""
        self.mode, self.win, self.layer = 'on', win, win
        l, b, w, h = win.client_rect()
        if at is not None:
            self.x, self.y = at[0] - PW / 2, at[1] - PH / 2
        self.x = min(max(self.x, l), l + w - PW)
        self.y = min(max(self.y, b), b + h - PH)
        self.vy = 0
        self.ground = self.ladder = None
        self.ghosts = set()
        self.set_anchor(win)

    def break_out(self, win, at):
        """창 안쪽에서 테두리를 깨고 나간다: 깬 자리 바로 바깥에 선다 (공격 모드는 그대로)"""
        cl, cb, cw, ch = win.client_rect()
        l, b, w, h = win.rect()
        x, y = at
        side = min((x - cl, 'left'), (cl + cw - x, 'right'), (y - cb, 'bottom'), (cb + ch - y, 'top'))[1]
        self.win = None
        self.ground = self.ladder = None
        self.ghosts = {win}             # 빠져나올 때까지 그 창에 끼지 않게
        self.set_anchor(None)
        if side == 'left':
            self.x, self.y, self.kb = l - PW - 1, y - PH / 2, -250
        elif side == 'right':
            self.x, self.y, self.kb = l + w + 1, y - PH / 2, 250
        elif side == 'bottom':
            self.x, self.y = x - PW / 2, b - PH - 1
        else:
            self.x, self.y = x - PW / 2, b + h + 1
        self.y = max(TASKBAR_H, self.y)
        self.vy = 300

    def force_out(self):
        # 들어가 있던 창이 닫히거나 최소화되면 그 자리에서 밖으로 떨어진다
        self.mode, self.win, self.layer = 'off', None, None
        self.ghosts = set()
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

    def poke(self, mx, my):
        """기본 무기: 조준한 쪽으로 손가락을 찌른다. 찌른 끝 위치를 돌려준다 (쿨타임 중이면 None)"""
        if self.mode != 'on' or self.poke_cd > 0 or self.dead:
            return None
        hx, hy = self.hand()
        dx, dy = mx - hx, my - hy
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
            hx, hy = self.hand()
            dx, dy = mx - hx, my - hy
        d = math.hypot(dx, dy) or 1
        self.poke_dir = (dx / d, dy / d)
        self.poke_t, self.poke_cd = POKE_TIME, POKE_COOLDOWN
        reach = min(POKE_REACH, d)
        return hx + self.poke_dir[0] * reach, hy + self.poke_dir[1] * reach

    # ---------------------------------------------------------------- 그림 무기
    def take_weapon(self, weapon):
        """특수 무기는 하나만: 들고 있던 건 내려놓고 바꿔 든다"""
        if self.weapon is not None and self.weapon is not weapon:
            self.weapon.drop()
        self.weapon = weapon
        self.swing_t = self.swing_cd = 0.0

    def drop_weapon(self):
        """E: 특수 무기 버리기"""
        if self.weapon is None:
            return False
        self.weapon.drop()
        self.weapon = None
        self.swing_t = 0.0
        return True

    def has(self, kind):
        return self.weapon is not None and self.weapon.kind == kind

    def shoot(self, mx, my):
        """디버그 건 좌클릭: 조준 쪽으로 중단점을 쏜다"""
        from debuggun import Shot, SHOT_COOLDOWN
        if self.mode != 'on' or not self.has('gun') or self.shot_cd > 0 or self.dead:
            return None
        hx, hy = self.hand()
        if abs(mx - hx) > 1:
            self.facing = 1 if mx > hx else -1
            hx, hy = self.hand()
        a = math.atan2(my - hy, mx - hx)
        self.shot_cd, self.recoil = SHOT_COOLDOWN, 0.1
        self.poke_dir = (math.cos(a), math.sin(a))
        x, y = self.weapon.muzzle(hx, hy, a)
        return Shot(x, y, a, self.win)

    def f5(self, mx, my):
        """디버그 건 우클릭: F5 Run 대쉬 (멀리, 닿은 적 관통 데미지)"""
        from debuggun import F5_SPEED, F5_TIME, F5_COOLDOWN, F5_DAMAGE
        if not self.has('gun') or self.f5_cd > 0:
            return False
        if not self.dash(mx, my, F5_SPEED, F5_TIME, ignore_cd=True):
            return False
        self.f5_cd = F5_COOLDOWN
        self.dash_power = F5_DAMAGE
        return True

    def swing(self, mx, my):
        """그림 무기로 휘두르기(칼) / 찌르기(창). 닿는 끝 위치를 돌려준다 (쿨타임 중이면 None)"""
        w = self.weapon
        if self.mode != 'on' or self.swing_cd > 0 or self.dead or not self.has('drawing'):
            return None
        hx, hy = self.hand()
        if abs(mx - hx) > 1:
            self.facing = 1 if mx > hx else -1
            hx, hy = self.hand()
        a = math.atan2(my - hy, mx - hx)
        self.swing_from = self.weapon_pose()[2]     # 지금 자세에서 시작한다
        self.swing_aim = a
        self.swing_t = self.swing_len = w.motion_time
        self.swing_cd = w.cooldown
        self.swing_hits = []
        self.swing_trail = []
        self.poke_dir = (math.cos(a), math.sin(a))
        return w.tip(hx, hy, a)

    def rest_angle(self):
        rest = math.radians(60)
        return rest if self.facing > 0 else math.pi - rest

    def swing_k(self):
        return 1 - self.swing_t / self.swing_len if self.swing_t > 0 else 1.0

    def swing_phase(self):
        """'windup' 준비 · 'strike' 내지르기(맞는 때) · 'follow' 넘어가기/버티기(맞는 때) · 'recover' 되돌리기"""
        if self.swing_t <= 0 or not self.has('drawing'):
            return None
        from drawing import BLADE_PHASES, SPEAR_PHASES
        p1, p2, p3 = SPEAR_PHASES if self.weapon.shape == 'spear' else BLADE_PHASES
        k = self.swing_k()
        return 'windup' if k < p1 else 'strike' if k < p2 else 'follow' if k < p3 else 'recover'

    def swing_active(self):
        return self.swing_phase() in ('strike', 'follow')

    def weapon_pose(self):
        """지금 그림 무기를 잡은 (손 x, 손 y, 각도)"""
        from drawing import BLADE_PHASES, SPEAR_PHASES
        hx, hy = self.hand()
        w = self.weapon
        if self.swing_t <= 0:
            return hx, hy, self.rest_angle()
        k, f, a0 = self.swing_k(), self.facing, self.swing_aim
        out = lambda t: 1 - (1 - t) ** 3                # 빠르게 출발해서 멈춘다
        into = lambda t: t * t * t                      # 천천히 출발해서 몰아친다
        both = lambda t: t * t * (3 - 2 * t)
        mix = lambda x, y, t: x + (y - x) * t
        if w.shape == 'spear':
            p1, p2, p3 = SPEAR_PHASES
            if k < p1:                                  # 뒤로 당기며 겨눈다
                t = out(k / p1)
                a, push = mix(self.swing_from, a0, t), -0.3 * t
            elif k < p2:                                # 확 찌른다
                a, push = a0, mix(-0.3, 0.55, out((k - p1) / (p2 - p1)))
            elif k < p3:                                # 끝에서 잠깐 버틴다
                a, push = a0, 0.55
            else:                                       # 거두어들인다
                t = both((k - p3) / (1 - p3))
                a, push = mix(a0, self.rest_angle(), t), mix(0.55, 0.0, t)
            push *= w.length
            return hx + math.cos(a) * push, hy + math.sin(a) * push, a
        p1, p2, p3 = BLADE_PHASES
        up, down, over = a0 + math.radians(120) * f, a0 - math.radians(80) * f, a0 - math.radians(98) * f
        if k < p1:                                      # 머리 위로 크게 들어 올린다
            a = mix(self.swing_from, up, out(k / p1))
        elif k < p2:                                    # 몰아쳐 내려친다
            a = mix(up, down, into((k - p1) / (p2 - p1)) * 0.5 + both((k - p1) / (p2 - p1)) * 0.5)
        elif k < p3:                                    # 힘이 남아 조금 더 넘어간다
            a = mix(down, over, out((k - p2) / (p3 - p2)))
        else:                                           # 제자리로
            a = mix(over, self.rest_angle(), both((k - p3) / (1 - p3)))
        return hx, hy, a

    def draw_swing_fx(self):
        """잔상(속성 색으로 물든 옅은 무기)과 칼끝 궤적(4px 블록 띠)"""
        w = self.weapon
        trail = self.swing_trail
        if len(trail) < 2:
            return
        c = w.color
        bx, by = self.body_lunge()
        for i, (hx, hy, a) in enumerate(trail[1:4]):
            w.draw(hx + bx, hy + by, a, self.facing, alpha=150 - i * 45, tint=c)
        tips = [w.tip(hx + bx, hy + by, a) for hx, hy, a in trail]
        for i in range(len(tips) - 1):
            (x0, y0), (x1, y1) = tips[i], tips[i + 1]
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 4))
            thick = max(1, 3 - i)
            for j in range(n + 1):
                x, y = x0 + (x1 - x0) * j / n, y0 + (y1 - y0) * j / n
                for s in range(thick):
                    ex, ey = (x0 - self.center()[0]), (y0 - self.center()[1])
                    d = math.hypot(ex, ey) or 1
                    sx, sy = x - ex / d * s * 4, y - ey / d * s * 4     # 칼끝에서 손 쪽으로 두께
                    col = WHITE if s == 0 and i < 2 else c
                    gfx.fill(int(sx) // 4 * 4, int(sy) // 4 * 4, 4, 4, col + (230 - i * 40,))
        if w.shape == 'spear':
            hx, hy, a = trail[0]
            tx, ty = w.tip(hx + bx, hy + by, a)
            dx, dy = math.cos(a), math.sin(a)
            nx, ny = -dy, dx
            # 창대 양옆으로 뒤로 흐르는 속도선
            for side, length in ((-12, 70), (12, 50), (-22, 36), (22, 28)):
                for j in range(0, length, 8):
                    x = tx - dx * (24 + j) + nx * side
                    y = ty - dy * (24 + j) + ny * side
                    gfx.fill(int(x) // 4 * 4, int(y) // 4 * 4, 4, 4, (WHITE if j < 16 else c) + (220 - j * 3,))
            if self.swing_phase() == 'follow':
                # 다 뻗은 창끝에서 별 모양으로 번쩍
                k = 1 - (self.swing_k() - 0.4) / 0.16
                for r, col in ((18 * k + 6, c), (10 * k + 4, WHITE)):
                    for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        for s in range(0, int(r), 4):
                            gfx.fill(int(tx + ex * s) // 4 * 4, int(ty + ey * s) // 4 * 4, 4, 4, col)
                gfx.fill(int(tx) // 4 * 4 - 4, int(ty) // 4 * 4 - 4, 12, 12, WHITE)

    def body_lunge(self):
        """휘두르는 동안 몸도 같이: 창은 앞으로 내딛고, 칼은 들 때 뒤로 젖혔다가 내려칠 때 숙인다"""
        phase = self.swing_phase()
        if phase is None:
            return 0.0, 0.0
        a0 = self.swing_aim
        if self.weapon.shape == 'spear':
            hx, hy = self.hand()
            px, py, a = self.weapon_pose()
            return (px - hx) * 0.7, (py - hy) * 0.7
        lean = {'windup': -6, 'strike': 10, 'follow': 8, 'recover': 2}[phase]
        return math.cos(a0) * lean, -abs(lean) * 0.4 if phase in ('strike', 'follow') else 0.0

    def weapon_tip(self):
        hx, hy, a = self.weapon_pose()
        bx, by = self.body_lunge()
        return self.weapon.tip(hx + bx, hy + by, a)

    def weapon_points(self):
        hx, hy, a = self.weapon_pose()
        bx, by = self.body_lunge()
        return self.weapon.points(hx + bx, hy + by, a, self.facing)

    def throw_weapon(self, mx, my):
        """우클릭: 그림 무기를 던진다 (다시 쓰려면 사진 창에서 또 집는다)"""
        from drawing import ThrownDrawing
        if not self.has('drawing') or self.dead:
            return None
        hx, hy = self.hand()
        dx, dy = mx - hx, my - hy
        d = math.hypot(dx, dy) or 1
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        t = ThrownDrawing(self.weapon, hx, hy, dx / d * THROW_SPEED * 0.85, dy / d * THROW_SPEED * 0.85,
                          self.win, self.facing)
        self.weapon = None
        self.swing_t = 0.0
        self.kb = -dx / d * 220
        return t

    def dash(self, mx, my, speed=DASH_SPEED, time=DASH_TIME, ignore_cd=False):
        """빈손 우클릭: 조준선 쪽으로 가장 가까운 8방향 대쉬. 했으면 True"""
        if self.mode != 'on' or (self.dash_cd > 0 and not ignore_cd) or self.dead \
                or (self.ground is None and not self.air_dash):
            return False
        self.dash_speed, self.dash_power, self.dash_hits = speed, 0, []
        cx, cy = self.center()
        a = round(math.atan2(my - cy, mx - cx) / (math.pi / 4)) * (math.pi / 4)
        self.dash_dir = (round(math.cos(a), 6), round(math.sin(a), 6))
        if abs(self.dash_dir[0]) > 0.1:
            self.facing = 1 if self.dash_dir[0] > 0 else -1
        self.dash_t, self.dash_cd = time, DASH_COOLDOWN
        if self.ground is None:
            self.air_dash = False
        self.ground = self.ladder = None
        self.dash_trail = []
        return True

    def throw(self, mx, my):
        if not self.held:
            return None
        hx, hy = self.hand()
        dx, dy = mx - hx, my - hy
        d = math.hypot(dx, dy) or 1
        t = Thrown(self.held, hx, hy, dx / d * THROW_SPEED, dy / d * THROW_SPEED, self.win)
        self.held = None
        self.kb = -dx / d * 220                    # 반동
        self.poke_dir, self.poke_t = (dx / d, dy / d), POKE_TIME
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        return t

    def eat(self):
        if not self.held or self.eat_cd > 0:
            return False
        self.held = None
        self.hp = min(MAX_HP, self.hp + EAT_HEAL)
        self.eat_cd = EAT_COOLDOWN
        return True

    # ---------------------------------------------------------------- 피격
    def hurt(self, damage, from_x):
        """맞았으면 True. 무적 중이거나 이미 쓰러졌으면 무시한다"""
        if self.invincible > 0 or self.dead or damage <= 0 or self.dash_t > 0:
            return False
        self.hp = max(0, self.hp - damage)
        self.invincible = INVINCIBLE
        self.hurt_t = 0.5
        self.kb = KNOCKBACK if self.center()[0] >= from_x else -KNOCKBACK
        self.vy = 320
        self.ground = self.ladder = None
        if self.hp == 0:
            self.dead = True
        return True

    # ---------------------------------------------------------------- 물리
    def update(self, dt, wm):
        self.anim_t += dt
        self.invincible = max(0.0, self.invincible - dt)
        self.hurt_t = max(0.0, self.hurt_t - dt)
        self.kb -= self.kb * min(1.0, 8 * dt)
        if self.dead:
            self.left = self.right = self.up = self.down = False
        self.switch_cd = max(0.0, self.switch_cd - dt)
        self.poke_t = max(0.0, self.poke_t - dt)
        self.poke_cd = max(0.0, self.poke_cd - dt)
        self.dash_cd = max(0.0, self.dash_cd - dt)
        self.swing_t = max(0.0, self.swing_t - dt)
        self.swing_cd = max(0.0, self.swing_cd - dt)
        if self.has('drawing') and self.swing_active():
            self.swing_trail = ([self.weapon_pose()] + self.swing_trail)[:6]
        else:
            self.swing_trail = self.swing_trail[:-1]
        self.shot_cd = max(0.0, self.shot_cd - dt)
        self.f5_cd = max(0.0, self.f5_cd - dt)
        self.recoil = max(0.0, self.recoil - dt)
        if self.ground is not None or self.ladder:
            self.air_jumps, self.air_dash = AIR_JUMPS, True
        self.dash_trail = ([(self.x, self.y)] + self.dash_trail)[:4] if self.dash_t > 0 else \
            self.dash_trail[:-1]
        self.eat_cd = max(0.0, self.eat_cd - dt)
        self.fail_t = max(0.0, self.fail_t - dt)

        visible = wm.visible()
        if self.inside and self.win not in visible:
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
        self.vx = move * RUN_SPEED + self.kb + self.pull[0]
        if self.dash_t > 0:
            # 대쉬 중에는 중력 없이 정한 방향으로만 날아간다
            self.dash_t = max(0.0, self.dash_t - dt)
            self.vx, self.vy = self.dash_dir[0] * self.dash_speed, self.dash_dir[1] * self.dash_speed
            if self.dash_t <= 0:
                self.vy *= 0.35             # 끝나면 살짝만 이어서 날아간다
        if self.mode == 'on' and not self.inside:
            self.move_solid(dt, wm)
            return
        prev_y = self.y
        self.x += self.vx * dt
        if self.dash_t <= 0:
            self.vy -= GRAVITY * dt
        self.y += (self.vy + self.pull[1]) * dt

        if self.inside:
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
        if self.mode == 'on' and not self.inside:
            return None                 # 공격 모드에서 창은 벽이라 스크롤바에 닿지 않는다
        cx, cy = self.center()
        wins = [self.win] if self.inside else reversed(wm.visible())
        for win in wins:
            for i, (l, b, w, h) in enumerate(win.app.ladders()):
                if l - 14 <= cx <= l + w + 14 and b - PH / 2 <= cy <= b + h + PH / 2:
                    if self.inside or wm.hit(l + w / 2, min(cy, b + h - 1))[0] is win:
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
            if self.inside:
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

    def move_solid(self, dt, wm):
        """공격 모드 (창 밖): 보이는 창이 모두 단단한 벽이다. 가로, 세로를 나눠 밀어낸다"""
        visible = wm.visible()
        self.ghosts = {w for w in self.ghosts if w in visible and self.overlaps(w.rect())}
        solids = [w for w in visible if w not in self.ghosts]
        self.layer = visible[-1] if visible else None          # 모든 창보다 앞에 그린다
        px = self.x
        self.x = min(max(self.x + self.vx * dt, 0), W - PW)
        for win in solids:
            l, b, w, h = win.rect()
            if self.overlaps((l, b, w, h)):
                if px + PW <= l + 0.01:
                    self.x = l - PW
                elif px >= l + w - 0.01:
                    self.x = l + w
                else:
                    self.x = px
        py = self.y
        if self.dash_t <= 0:
            self.vy -= GRAVITY * dt
        self.y += self.vy * dt
        self.ground = None
        if self.y <= TASKBAR_H:
            self.y, self.vy, self.ground = TASKBAR_H, 0, 'taskbar'
        if self.y + PH > H:
            self.y, self.vy = H - PH, min(self.vy, 0)
        for win in solids:
            l, b, w, h = win.rect()
            if not self.overlaps((l, b, w, h)):
                continue
            if py >= b + h - 0.01:
                self.y, self.vy, self.ground = b + h, 0, win
            elif py + PH <= b + 0.01:
                self.y, self.vy = b - PH, min(self.vy, 0)
        self.set_anchor(self.ground if self.ground not in (None, 'taskbar') else None)

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

    def anim_state(self):
        if self.hurt_t > 0 or self.dead:
            return 'hurt'
        if self.poke_t > 0 or self.swing_t > 0 or self.recoil > 0:
            return 'poke'
        if self.dash_t > 0:
            return 'jump'
        if self.ladder:
            return 'climb'
        if self.ground is None:
            return 'jump' if self.vy > 0 else 'fall'
        return 'run' if self.left != self.right else 'idle'

    def draw(self):
        if self.invincible > 0 and not self.dead and int(self.invincible * 12) % 2:
            return                      # 무적 중 깜빡임
        if self.inside:
            gfx.push_clip(*self.win.client_rect())
        for i, (tx, ty) in enumerate(self.dash_trail[1:]):
            # 대쉬 잔상: 지나온 자리에 옅은 포인터
            sprites.pointer().draw(self.mode, FACES[self.face()], 'jump', 0, tx + PW / 2, ty, self.facing < 0,
                                   0.45 - i * 0.13)
        shake = math.sin(self.fail_t * 80) * 4 if self.fail_t > 0 else 0
        lunge = 0.0
        if self.poke_t > 0:
            lunge = 14 * math.sin(math.pi * (1 - self.poke_t / POKE_TIME))   # 앞으로 내질렀다 돌아온다
        ox, oy = self.poke_dir[0] * lunge + shake, self.poke_dir[1] * lunge
        if self.has('drawing'):
            bx, by = self.body_lunge()
            ox, oy = ox + bx, oy + by
        sprites.pointer().draw(self.mode, FACES[self.face()], self.anim_state(), self.anim_t,
                               self.x + PW / 2 + ox, self.y + oy, self.facing < 0)
        if self.held:
            hx, hy = self.hand()
            draw_button(self.held, hx + ox + self.facing * 12, hy + oy, 0.8)
        if self.has('drawing'):
            self.draw_swing_fx()
            hx, hy, a = self.weapon_pose()
            bx, by = self.body_lunge()
            self.weapon.draw(hx + bx, hy + by, a, self.facing)
        elif self.has('gun'):
            hx, hy = self.hand()
            a = math.atan2(self.aim[1] - hy, self.aim[0] - hx)
            self.weapon.draw(hx, hy, a, 1 if math.cos(a) >= 0 else -1, self.recoil / 0.1)
        if self.inside:
            gfx.pop_clip()

    def draw_hud(self):
        # 작업 표시줄 바로 위 오른쪽: HP 막대, 손 슬롯, Q 쿨타임, 모드 (왼쪽 아래는 포인터 출발 자리)
        l, b = W - 366, TASKBAR_H + 10
        gfx.fill(l - 6, b - 6, 360, 34, (0, 0, 0, 120))
        gfx.text('HP', l, b + 11, 12, WHITE, FONT_BOLD)
        gfx.fill(l + 26, b + 6, 200, 10, (60, 60, 60))
        k = self.hp / MAX_HP
        gfx.fill(l + 26, b + 6, int(200 * k), 10, (19, 161, 14) if k > 0.3 else CLOSE_RED)
        sx = l + 238
        gfx.frame(sx, b, 34, 22, (200, 200, 200))
        if self.held:
            draw_button(self.held, sx + 17, b + 11, 0.85)
        if self.weapon is not None:
            # 손 칸 왼쪽 위에 그림 무기 칸
            gfx.fill(sx - 2, b + 30, 38, 38, (0, 0, 0, 140))
            gfx.frame(sx - 2, b + 30, 38, 38, self.weapon.color)
            if self.has('drawing'):
                self.weapon.draw_fit(sx + 1, b + 33, 32, 32)
            else:
                self.weapon.draw_icon(sx + 5, b + 37, 24)
                if self.f5_cd > 0:
                    gfx.text('F5 %d' % math.ceil(self.f5_cd), sx + 42, b + 49, 12, (150, 150, 150), FONT_BOLD)
                else:
                    gfx.text('F5', sx + 42, b + 49, 12, WHITE, FONT_BOLD)
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
