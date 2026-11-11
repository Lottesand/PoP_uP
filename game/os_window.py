# 윈도우 10 창 (OSWindow)과 창 관리자 (WindowManager)
# 창 사각형은 (left, bottom, width, height). 제목 표시줄은 창의 맨 위 TITLE_H 높이.
import gfx
from config import *

MIN, MAX, RESTORE, CLOSE = '\uE921', '\uE922', '\uE923', '\uE8BB'


class OSWindow:
    def __init__(self, app, x, y, w, h):
        self.app = app
        self.x, self.y, self.w, self.h = x, y, w, h
        self.state = 'normal'          # normal | max | min
        self.saved_state = 'normal'    # 최소화 직전 상태 (복원할 때 씀)

    @property
    def title(self):
        return self.app.title

    def rect(self):
        if self.state == 'max':
            return 0, TASKBAR_H, W, H - TASKBAR_H
        return self.x, self.y, self.w, self.h

    def client_rect(self):
        l, b, w, h = self.rect()
        e = 0 if self.state == 'max' else 1
        return l + e, b + e, w - 2 * e, h - TITLE_H - e

    def caption_buttons(self):
        l, b, w, h = self.rect()
        e = 0 if self.state == 'max' else 1
        top, r = b + h - e, l + w - e
        names = [n for n in ('close', 'max', 'min') if n in self.app.caption]
        return [(name, r - CAPTION_BTN_W * (i + 1), top - TITLE_H + e, CAPTION_BTN_W, TITLE_H - e)
                for i, name in enumerate(names)]

    # ---------------------------------------------------------------- 마우스 판정
    def hit(self, mx, my):
        """('resize', 가장자리 문자열) / ('close'|'max'|'min'|'title'|'client', None) / None"""
        l, b, w, h = self.rect()
        r, t = l + w, b + h
        if self.state == 'normal' and self.app.resizable:
            g = RESIZE_GRIP
            if l - g <= mx < r + g and b - g <= my < t + g:
                edge = ''
                if my >= t - 2:
                    edge += 't'
                elif my < b + 2:
                    edge += 'b'
                if mx < l + 2:
                    edge += 'l'
                elif mx >= r - 2:
                    edge += 'r'
                if edge and not (edge == 't' and my < t):
                    return 'resize', edge
        if not (l <= mx < r and b <= my < t):
            return None
        if my >= t - TITLE_H:
            for name, bl, bb, bw, bh in self.caption_buttons():
                if bl <= mx < bl + bw:
                    return name, None
            return 'title', None
        return 'client', None

    # ---------------------------------------------------------------- 상태 바꾸기
    def toggle_max(self):
        if not self.app.resizable:
            return
        if self.state == 'max':
            self.state = 'normal'
        else:
            self.state = 'max'

    def restore_for_drag(self, mx, my):
        # 최대화된 창을 끌면 원래 크기로 돌아가면서 마우스가 제목 표시줄의 같은 비율 위치에 오게 한다
        k = mx / W
        self.state = 'normal'
        self.x = int(mx - self.w * k)
        self.y = int(my + TITLE_H / 2 - self.h)

    def clamp(self):
        self.x = max(80 - self.w, min(W - 80, self.x))
        top = self.y + self.h
        top = max(TASKBAR_H + TITLE_H, min(H, top))
        self.y = top - self.h

    def resize(self, edge, start, dx, dy):
        x, y, w, h = start
        if 'l' in edge:
            nw = max(WIN_MIN_W, w - dx)
            x, w = x + w - nw, nw
        if 'r' in edge:
            w = max(WIN_MIN_W, w + dx)
        if 'b' in edge:
            nh = max(WIN_MIN_H, h - dy)
            y, h = y + h - nh, nh
        if 't' in edge:
            h = max(WIN_MIN_H, min(H - y, h + dy))
        self.x, self.y, self.w, self.h = x, y, w, h

    # ---------------------------------------------------------------- 그리기
    def draw(self, active, hover=None, pressed=None):
        l, b, w, h = self.rect()
        if self.state == 'normal':
            gfx.shadow(l, b, w, h, 14 if active else 8, 46 if active else 30)
        gfx.fill(l, b, w, h, WHITE)

        cl, cb, cw, ch = self.client_rect()
        gfx.push_clip(cl, cb, cw, ch)
        self.app.draw(cl, cb, cw, ch, active)
        gfx.pop_clip()

        # 제목 표시줄
        top = b + h
        gfx.push_clip(l, b, w, h)
        gfx.fill(l, top - TITLE_H, w, TITLE_H, WHITE)
        cy = top - TITLE_H / 2
        gfx.icon(self.app.icon, 16, l + 8, cy - 8)
        tc = TEXT if active else TITLE_INACTIVE
        gfx.text(self.title, l + 32, cy, 12, tc)
        for name, bl, bb, bw, bh in self.caption_buttons():
            gc = tc
            if name == hover or name == pressed:
                if name == 'close':
                    gfx.fill(bl, bb, bw, bh, CLOSE_RED_PRESSED if name == pressed else CLOSE_RED)
                    gc = WHITE
                else:
                    gfx.fill(bl, bb, bw, bh, PRESSED_GRAY if name == pressed else HOVER_GRAY)
                    gc = TEXT
            glyph = {'min': MIN, 'max': RESTORE if self.state == 'max' else MAX, 'close': CLOSE}[name]
            gfx.symbol(glyph, bl + bw / 2, bb + bh / 2, 10, gc)
        gfx.pop_clip()

        if self.state == 'normal':
            gfx.frame(l, b, w, h, BORDER_ACTIVE if active else BORDER_INACTIVE)


class WindowManager:
    def __init__(self):
        self.windows = []              # 뒤 → 앞 순서
        self.active = None
        self.hover = None              # (창, 버튼 이름)
        self.pressed = None            # (창, 버튼 이름)
        self.drag = None               # ('move', 창, 시작 마우스, 시작 사각형) / ('resize', 창, 가장자리, ...)
        self.last_title_click = (None, -1.0)
        self.cascade = 0

    # ---------------------------------------------------------------- 열기 · 닫기 · 순서
    def find(self, key):
        for win in self.windows:
            if win.app.key == key:
                return win
        return None

    def open(self, app):
        win = self.find(app.key)
        if win:
            self.focus(win)
            return win
        w, h = app.size
        if app.center:
            x, y = (W - w) // 2, (H + TASKBAR_H - h) // 2
        else:
            x = 140 + 32 * (self.cascade % 8)
            y = max(TASKBAR_H + 10, H - 90 - 32 * (self.cascade % 8) - h)
            self.cascade += 1
        win = OSWindow(app, x, y, w, h)
        self.windows.append(win)
        self.focus(win)
        return win

    def close(self, win):
        self.windows.remove(win)
        if self.active is win:
            self.active = None
            self._activate_top()

    def minimize(self, win):
        win.saved_state = win.state
        win.state = 'min'
        if self.active is win:
            self.active = None
            self._activate_top()

    def focus(self, win):
        if win.state == 'min':
            win.state = win.saved_state
        self.windows.remove(win)
        self.windows.append(win)
        self.active = win

    def _activate_top(self):
        for win in reversed(self.windows):
            if win.state != 'min':
                self.active = win
                return

    def deactivate(self):
        self.active = None

    def visible(self):
        return [w for w in self.windows if w.state != 'min']

    # ---------------------------------------------------------------- 마우스
    def hit(self, mx, my):
        for win in reversed(self.visible()):
            part = win.hit(mx, my)
            if part:
                return win, part
        return None, None

    def cursor_for(self, mx, my):
        if self.drag and self.drag[0] == 'resize':
            return _EDGE_CURSOR[self.drag[2]]
        win, part = self.hit(mx, my)
        if part and part[0] == 'resize':
            return _EDGE_CURSOR[part[1]]
        return 'arrow'

    def mouse_move(self, mx, my):
        if self.drag:
            kind, win, extra, (sx, sy), start = self.drag
            dx, dy = mx - sx, my - sy
            if kind == 'move':
                if win.state == 'max':
                    if abs(dx) + abs(dy) < 4:
                        return
                    win.restore_for_drag(mx, my)
                    self.drag = ('move', win, None, (mx, my), (win.x, win.y, win.w, win.h))
                    return
                win.x, win.y = start[0] + dx, start[1] + dy
                win.clamp()
            else:
                win.resize(extra, start, dx, dy)
            return
        win, part = self.hit(mx, my)
        self.hover = (win, part[0]) if part and part[0] in ('min', 'max', 'close') else None
        for w in self.visible():
            if w is win and part and part[0] == 'client':
                w.app.mouse_move(mx, my)
            else:
                w.app.mouse_move(None, None)

    def context(self, mx, my):
        """오른쪽 클릭: 창 위면 메뉴 항목 목록(없으면 []), 창 밖이면 None"""
        from context_menu import Item, SEP
        win, part = self.hit(mx, my)
        if not win:
            return None
        self.focus(win)
        if part[0] == 'client':
            return win.app.context(mx, my) or []
        if part[0] == 'resize':
            return []
        big = win.state == 'max'
        return [Item('이전 크기로(R)', win.toggle_max, enabled=big and win.app.resizable),
                Item('이동(M)', enabled=False), Item('크기 조정(S)', enabled=False),
                Item('최소화(N)', lambda: self.minimize(win), enabled='min' in win.app.caption),
                Item('최대화(X)', win.toggle_max, enabled=not big and win.app.resizable), SEP,
                Item('닫기(C)', lambda: self.close(win), bold=True)]

    def wheel(self, mx, my, dy):
        win, part = self.hit(mx, my)
        if win and part[0] == 'client':
            win.app.wheel(dy)

    def mouse_down(self, mx, my, now):
        win, part = self.hit(mx, my)
        if not win:
            return False
        self.focus(win)
        kind, edge = part
        start = (win.x, win.y, win.w, win.h)
        if kind == 'resize':
            self.drag = ('resize', win, edge, (mx, my), start)
        elif kind in ('min', 'max', 'close'):
            self.pressed = (win, kind)
        elif kind == 'title':
            last_win, last_t = self.last_title_click
            if last_win is win and now - last_t < DOUBLE_CLICK:
                win.toggle_max()
                self.last_title_click = (None, -1.0)
                return True
            self.last_title_click = (win, now)
            self.drag = ('move', win, None, (mx, my), start)
        elif kind == 'client':
            win.app.mouse_down(mx, my, now)
        return True

    def mouse_up(self, mx, my):
        self.drag = None
        if self.pressed:
            win, name = self.pressed
            self.pressed = None
            part = win.hit(mx, my)
            if part and part[0] == name:
                if name == 'close':
                    self.close(win)
                elif name == 'max':
                    win.toggle_max()
                else:
                    self.minimize(win)

    # ---------------------------------------------------------------- 그리기
    def draw(self):
        for win in self.visible():
            hover = self.hover[1] if self.hover and self.hover[0] is win else None
            pressed = self.pressed[1] if self.pressed and self.pressed[0] is win else None
            win.draw(win is self.active, hover, pressed)


_EDGE_CURSOR = {'l': 'we', 'r': 'we', 't': 'ns', 'b': 'ns',
                'tl': 'nwse', 'br': 'nwse', 'tr': 'nesw', 'bl': 'nesw'}
