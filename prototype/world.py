"""게임 규칙 전부. pico2d 창 없이도 돌아가므로 test_rules.py 에서 그대로 테스트한다.

레이어 규칙
- 스틱맨은 항상 어떤 레이어 안에 있다: 바탕화면(layer=None) 또는 어떤 창(layer=그 창).
- 내 레이어보다 위(z가 큰)에 있는 창들:
    벽 모드 OFF -> 충돌 없음, 스틱맨이 그 창에 가려진다
    벽 모드 ON  -> 단단한 벽/발판이 된다. 겹친 채로 ON 이 되면 찌부되어 죽는다
- 벽 모드 ON 에서 위쪽 창 벽에 붙어 E -> 벽을 부수고 그 창(프로그램) 안으로 들어간다
- 창 안에서 좌/우/천장 벽에 붙어 E -> 그 창 밖, 아래쪽 레이어로 나간다
"""
import random

from config import *
from geometry import Rect
from os_window import Plate, Key, Vault
from player import Stickman
import level

BIN_POS = (CANVAS_W - 90, TASKBAR_H)


class World:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        rng = random.Random(self.seed)
        self.windows, self.desk_icons, self.pin = level.generate(rng)
        self.by_id = {w.wid: w for w in self.windows}
        self.player = Stickman(200, TASKBAR_H)
        self.layer = None
        self.wall_mode = False
        self.entered = ''
        self.time = 0.0
        self.deaths = 0
        self.won = False
        self.msg, self.msg_time = '바탕화면에 갇혔다! 금고.exe 안의 EXIT 로 탈출하자', 4.0
        self.drag = None             # ('move' | 'resize', 창, 오프셋x, 오프셋y)
        self.last_click = (None, -10.0)

    # ------------------------------------------------------------ 레이어 / z 순서
    def z(self, win):
        return -1 if win is None else self.windows.index(win)

    def open_windows(self):
        return [w for w in self.windows if w.opened]

    def windows_above(self, layer):
        lz = self.z(layer)
        return [w for w in self.open_windows() if self.z(w) > lz]

    def top_window(self):
        ws = self.open_windows()
        return ws[-1] if ws else None

    def layer_name(self):
        return '바탕화면' if self.layer is None else self.layer.title

    def say(self, text, sec=2.5):
        self.msg, self.msg_time = text, sec

    def bring_to_front(self, win):
        if win.frozen:
            return
        self.windows.remove(win)
        self.windows.append(win)

    def open_window(self, wid):
        win = self.by_id[wid]
        win.opened = True
        self.bring_to_front(win)

    def close_window(self, win):
        if self.layer is win:
            # 들어가 있던 창이 닫히면 그 자리 아래 레이어로 떨어진다
            self.layer = self.layer_under(win, self.player.rect())
            self.clamp_to_layer()
        if self.player.ground_ref is win:
            self.player.ground_ref = None
        win.opened = False
        if self.drag and self.drag[1] is win:
            self.drag = None

    def layer_under(self, win, rect):
        """win 보다 아래에서 rect 를 품을 수 있는 가장 위 창. 없으면 바탕화면(None)."""
        for w in reversed(self.open_windows()):
            if self.z(w) < self.z(win) and w.content.contains(rect):
                return w
        return None

    def clamp_to_layer(self):
        p = self.player
        if self.layer is None:
            p.x = max(0, min(p.x, CANVAS_W - PLAYER_W))
            p.y = max(TASKBAR_H, min(p.y, CANVAS_H - PLAYER_H))

    # ------------------------------------------------------------ 충돌체
    def solids_for(self, layer):
        out = []
        if layer is None:
            out.append((Rect(-100, -100, CANVAS_W + 200, TASKBAR_H + 100), 'floor'))
            out.append((Rect(-100, 0, 100, CANVAS_H + 100), 'wall'))
            out.append((Rect(CANVAS_W, 0, 100, CANVAS_H + 100), 'wall'))
            out.append((Rect(-100, CANVAS_H, CANVAS_W + 200, 100), 'wall'))
        else:
            c = layer.content
            out.append((Rect(c.l - 50, c.b - 50, c.w + 100, 50), 'wall'))
            out.append((Rect(c.l - 50, c.t, c.w + 100, 50), 'wall'))
            out.append((Rect(c.l - 50, c.b, 50, c.h), 'wall'))
            out.append((Rect(c.r, c.b, 50, c.h), 'wall'))
            for it in layer.visible_items():
                if it.solid:
                    out.append((it.rect(layer), it))
        if self.wall_mode:
            for w in self.windows_above(layer):
                out.append((w.outer, w))
        return out

    # ------------------------------------------------------------ 마우스
    def mouse_down(self, mx, my, now):
        for w in reversed(self.open_windows()):
            if not w.outer.contains_point(mx, my):
                continue
            if w.frozen:
                self.say(f'"{w.title}" 이(가) 응답하지 않습니다')
                return
            self.bring_to_front(w)
            if w.close_rect.contains_point(mx, my):
                self.close_window(w)
            elif w.grip_rect.contains_point(mx, my):
                self.drag = ('resize', w, 0, 0)
            elif w.title_rect.contains_point(mx, my):
                self.drag = ('move', w, mx - w.x, my - w.y)
            else:
                icon = w.icon_at(mx, my)
                if icon:
                    self.click_icon(icon, now)
            return
        for ic in self.desk_icons:
            if ic.rect_at(ic.x, ic.y).inflate(6).contains_point(mx, my):
                self.click_icon(ic, now)
                return

    def click_icon(self, icon, now):
        last, t = self.last_click
        if last is icon and now - t <= DOUBLE_CLICK:
            self.open_window(icon.target)
            self.last_click = (None, -10.0)
        else:
            self.last_click = (icon, now)

    def mouse_move(self, mx, my):
        if not self.drag:
            return
        mode, w, ox, oy = self.drag
        if mode == 'move':
            w.move_to(mx - ox, my - oy)
        else:
            w.resize_to(mx, my)

    def mouse_up(self):
        self.drag = None

    # ------------------------------------------------------------ 키보드
    def toggle_wall_mode(self):
        self.wall_mode = not self.wall_mode
        self.say('벽 모드 ON: 위에 있는 창이 벽이 된다' if self.wall_mode else '벽 모드 OFF: 위에 있는 창 뒤로 숨는다', 1.5)

    def interact(self):
        p = self.player
        pr = p.rect()
        probe = pr.inflate(TOUCH)
        if self.wall_mode:
            for w in reversed(self.windows_above(self.layer)):
                if probe.overlaps(w.outer):
                    self.try_enter(w)
                    return
        if self.layer is not None:
            c = self.layer.content
            if pr.l - c.l <= TOUCH:
                self.try_exit('left')
                return
            if c.r - pr.r <= TOUCH:
                self.try_exit('right')
                return
            if c.t - pr.t <= TOUCH:
                self.try_exit('top')
                return
        self.say('붙어 있는 벽이 없다' if self.wall_mode else '벽 모드(Shift)를 켜야 벽을 부술 수 있다', 1.5)

    def _blocked(self, rect, layer):
        return any(rect.overlaps(s) for s, _ in self.solids_for(layer))

    def try_enter(self, win):
        p, c = self.player, win.content
        if c.w < PLAYER_W or c.h < PLAYER_H:
            self.say('창이 너무 작아서 들어갈 수 없다')
            return
        bx = max(c.l, min(p.x, c.r - PLAYER_W))
        by = max(c.b, min(p.y, c.t - PLAYER_H))
        # 바로 그 자리가 발판 등에 막혀 있으면 가까운 빈자리를 찾는다 (위쪽 우선)
        spot = None
        for dy in range(0, int(c.h), 4):
            for dx in (0, 8, -8, 16, -16, 32, -32, 64, -64):
                nx = max(c.l, min(bx + dx, c.r - PLAYER_W))
                ny = min(by + dy, c.t - PLAYER_H)
                if not self._blocked(Rect(nx, ny, PLAYER_W, PLAYER_H), win):
                    spot = (nx, ny)
                    break
            if spot:
                break
        if spot is None:
            self.say('들어갈 자리가 막혀 있다')
            return
        nx, ny = spot
        self.layer = win
        p.place(nx, ny)
        self.say(f'[{win.title}] 의 벽을 부수고 침투!', 1.5)

    def try_exit(self, side):
        p, w = self.player, self.layer
        o = w.outer
        x, y = p.x, p.y
        if side == 'left':
            x = o.l - PLAYER_W - 0.5
        elif side == 'right':
            x = o.r + 0.5
        else:
            y = o.t + 0.5
        target = Rect(x, y, PLAYER_W, PLAYER_H)
        dest = self.layer_under(w, target)
        if dest is None:
            x = max(0, min(x, CANVAS_W - PLAYER_W))
            y = max(TASKBAR_H, min(y, CANVAS_H - PLAYER_H))
            target = Rect(x, y, PLAYER_W, PLAYER_H)
        if self._blocked(target, dest):
            self.say('나갈 자리가 막혀 있다')
            return
        self.layer = dest
        p.place(x, y)
        self.say(f'{self.layer_name()} (으)로 빠져나왔다', 1.5)

    # ------------------------------------------------------------ 사망 / 갱신
    def kill(self, reason):
        self.deaths += 1
        self.layer = None
        self.wall_mode = False
        self.player.place(*BIN_POS)
        self.say(f'{reason}  -> 휴지통에서 부활 (+{DEATH_PENALTY}초)', 3.0)

    def score_time(self):
        return self.time + self.deaths * DEATH_PENALTY

    def update(self, dt, inp):
        if self.won:
            return
        self.time += dt
        self.msg_time = max(0.0, self.msg_time - dt)
        p = self.player

        # 1) 창이 움직였으면 같이 움직인다 (들어가 있는 창, 또는 밟고 있는 창)
        carrier = self.layer if self.layer is not None else None
        if carrier is None and p.ground_ref in self.windows:
            carrier = p.ground_ref
        if carrier is not None:
            p.x += carrier.moved_dx
            p.y += carrier.moved_dy
        for w in self.windows:
            w.moved_dx = w.moved_dy = 0.0

        # 2) 창 크기가 줄어서 안에 있던 스틱맨이 끼었는지
        if self.layer is not None:
            c = self.layer.content
            if c.w < PLAYER_W or c.h < PLAYER_H:
                self.kill('창 크기에 끼여 찌부됐다')
                return
            p.x = max(c.l, min(p.x, c.r - PLAYER_W))
            p.y = max(c.b, min(p.y, c.t - PLAYER_H))
            for it in self.layer.visible_items():
                if it.solid and p.rect().overlaps(it.rect(self.layer), 0.5):
                    self.kill('창 안의 물체에 끼여 찌부됐다')
                    return

        # 3) 벽 모드에서 위쪽 창과 겹쳐 있으면 찌부
        if self.wall_mode:
            for w in self.windows_above(self.layer):
                if p.rect().overlaps(w.outer, 0.5):
                    self.kill(f'[{w.title}] 창에 깔려 찌부됐다')
                    return

        # 4) 물리 (빠른 낙하에도 뚫지 않도록 잘게 나눠서)
        solids = self.solids_for(self.layer)
        ladder = self.layer.ladder if self.layer is not None else None
        prev_ground = p.ground_ref
        steps = max(1, int(dt / (1 / 120)) + 1)
        jump = inp.jump
        for i in range(steps):
            inp.jump = jump and i == 0
            p.step(dt / steps, inp, solids, ladder)
        inp.jump = False

        # 5) 창 안의 물체
        if self.layer is not None:
            self.update_items(prev_ground, dt)

    def update_items(self, prev_ground, dt):
        p, win = self.player, self.layer
        pr = p.rect()
        for it in win.items:
            if isinstance(it, Plate):
                it.flash = max(0.0, it.flash - dt)
        for it in win.visible_items():
            if isinstance(it, Plate) and p.ground_ref is it and prev_ground is not it:
                self.press_digit(win, it)
            elif isinstance(it, Key) and pr.overlaps(it.rect(win)):
                it.active = False
                p.has_key = True
                self.say('열쇠를 얻었다! 금고로 가자')
            elif isinstance(it, Vault):
                vr = it.rect(win)
                if not it.opened and p.has_key and pr.inflate(TOUCH).overlaps(vr):
                    it.opened = True
                    p.has_key = False
                    self.say('철컥! 금고가 열렸다')
                elif it.opened and pr.overlaps(vr):
                    self.won = True

    def press_digit(self, win, plate):
        key = next(it for it in win.items if isinstance(it, Key))
        if key.active or self.player.has_key or self.entered == 'OK':
            return
        plate.flash = 0.3
        self.entered += plate.digit
        if len(self.entered) < 4:
            return
        if self.entered == self.pin:
            self.entered = 'OK'
            key.active = True
            self.say('PIN 일치! 계산기 선반에 열쇠가 나타났다')
        else:
            self.entered = ''
            self.say('PIN 오류. 처음부터 다시')
