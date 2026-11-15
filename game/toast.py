# 윈도우 10 알림(토스트): 작업 표시줄 위 오른쪽에 미끄러져 들어와 몇 초 뒤 사라진다. 튜토리얼 힌트에 쓴다.
import gfx
from config import *

TOAST_W = 364
SHOW = 6.0
SLIDE = 0.25

toasts = []


class Toast:
    def __init__(self, title, lines, icon='windows_logo'):
        self.title, self.lines, self.icon = title, list(lines), icon
        self.t = 0.0
        self.h = 64 + 20 * len(self.lines)

    @property
    def dead(self):
        return self.t >= SHOW


def show(title, *lines, icon='explorer'):
    toasts.append(Toast(title, lines, icon))


def clear():
    toasts.clear()


def update(dt):
    for t in toasts:
        t.t += dt
    toasts[:] = [t for t in toasts if not t.dead]


def draw():
    b = TASKBAR_H + 16
    for t in reversed(toasts):
        k = min(1.0, t.t / SLIDE, (SHOW - t.t) / SLIDE)
        l = W - 16 - TOAST_W * (0.4 + 0.6 * k) if k < 1 else W - 16 - TOAST_W
        a = int(245 * k)
        gfx.fill(l, b, TOAST_W, t.h, (31, 31, 31, a))
        gfx.frame(l, b, TOAST_W, t.h, (70, 70, 70, a))
        top = b + t.h
        gfx.icon(t.icon, 16, l + 14, top - 26, k)
        gfx.text('PoP_uP', l + 38, top - 18, 11, (180, 180, 180, a))
        gfx.text(t.title, l + 14, top - 44, 14, (255, 255, 255, a), FONT_BOLD)
        for i, ln in enumerate(t.lines):
            gfx.text(ln, l + 14, top - 66 - i * 20, 13, (220, 220, 220, a))
        b += t.h + 10
