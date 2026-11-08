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
