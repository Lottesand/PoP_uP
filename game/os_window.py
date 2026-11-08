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
        return [(name, r - CAPTION_BTN_W * (i + 1), top - TITLE_H + e, CAPTION_BTN_W, TITLE_H - e)
                for i, name in enumerate(('close', 'max', 'min'))]

    # ---------------------------------------------------------------- 마우스 판정
    def hit(self, mx, my):
        """('resize', 가장자리 문자열) / ('close'|'max'|'min'|'title'|'client', None) / None"""
        l, b, w, h = self.rect()
        r, t = l + w, b + h
        if self.state == 'normal':
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
