# 작업 표시줄: 시작 단추, 검색 상자, 작업 보기, 고정·실행 중인 프로그램, 알림 영역, 시계
import time
import gfx
from config import *

SEARCH_W = 344
BTN_W = 48
PINNED = ['documents', 'browser']
ICON_OF = {'documents': 'folder', 'browser': 'browser', 'this_pc': 'this_pc', 'recycle_bin': 'recycle_bin',
           'notepad': 'notepad', 'paint': 'paint', 'vscode': 'vscode', 'kakao': 'kakao', 'terminal': 'terminal'}


class Taskbar:
    def __init__(self):
        self.hover = None
        self.pressed = None
        self.usb_locked = True

    def contains(self, mx, my):
        return my < TASKBAR_H

    def apps(self, wm):
        keys = list(PINNED)
        for win in wm.windows:
            if win.app.key not in keys:
                keys.append(win.app.key)
        return keys

    def zones(self, wm):
        z = [('start', 0, BTN_W), ('search', BTN_W, SEARCH_W), ('taskview', BTN_W + SEARCH_W, BTN_W)]
        x = BTN_W * 2 + SEARCH_W
        for key in self.apps(wm):
            z.append((('app', key), x, BTN_W))
            x += BTN_W
        r = W
        for name, w in (('desktop', 6), ('action', 40), ('clock', 78), ('ime', 28), ('volume', 28),
                        ('network', 28), ('usb', 28), ('chevron', 24)):
            r -= w
            z.append((name, r, w))
        return z

    def hit(self, mx, my, wm):
        if not self.contains(mx, my):
            return None
        for name, x, w in self.zones(wm):
            if x <= mx < x + w:
                return name
        return None

    def draw(self, wm, start_open):
        gfx.fill(0, 0, W, TASKBAR_H, TASKBAR_BG)
        cy = TASKBAR_H / 2
        for name, x, w in self.zones(wm):
            hot = name == self.hover
            if name == 'start':
                if start_open or hot:
                    gfx.fill(x, 0, w, TASKBAR_H, (255, 255, 255, 40 if start_open else 25))
                gfx.icon('windows_logo', 16, x + 16, cy - 8, 1.0 if hot or start_open else 0.95)
            elif name == 'search':
                gfx.fill(x, 0, w, TASKBAR_H, (243, 243, 243) if not hot else WHITE)
                gfx.symbol('\uE721', x + 22, cy, 14, (30, 30, 30))
                gfx.text('검색하려면 여기에 입력하십시오.', x + 46, cy, 13, (90, 90, 90))
            elif name == 'taskview':
                if hot:
                    gfx.fill(x, 0, w, TASKBAR_H, (255, 255, 255, 25))
                gfx.symbol('\uE7C4', x + w / 2, cy, 16, WHITE)
            elif isinstance(name, tuple):
                self.draw_app(name[1], x, w, wm, hot)
            elif name == 'clock':
                if hot:
                    gfx.fill(x, 0, w, TASKBAR_H, (255, 255, 255, 25))
                t = time.localtime()
                ampm = '오전' if t.tm_hour < 12 else '오후'
                hour = t.tm_hour % 12 or 12
                gfx.text('%s %d:%02d' % (ampm, hour, t.tm_min), x + w / 2, cy + 9, 12, WHITE, align='center')
                gfx.text('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday), x + w / 2, cy - 9, 12, WHITE,
                         align='center')
            elif name == 'desktop':
                gfx.line(x, 0, x, TASKBAR_H, (90, 90, 90))
            else:
                if hot:
                    gfx.fill(x, 0, w, TASKBAR_H, (255, 255, 255, 25))
                glyph = {'action': '\uE91C', 'ime': None, 'volume': '\uE767', 'network': '\uE839',
                         'usb': '\uE88E', 'chevron': '\uE70E'}[name]
                if name == 'ime':
                    gfx.text('가', x + w / 2, cy, 13, WHITE, align='center')
                else:
                    gfx.symbol(glyph, x + w / 2, cy, 15 if name != 'chevron' else 10, WHITE)
                if name == 'network':
                    gfx.fill(x + w / 2 + 2, cy - 11, 9, 9, (255, 185, 0))
                    gfx.text('!', x + w / 2 + 6, cy - 7, 9, BLACK, align='center')
                if name == 'usb' and self.usb_locked:
                    gfx.icon('lock', 16, x + w / 2 + 1, cy - 14)

    def draw_app(self, key, x, w, wm, hot):
        win = wm.find(key)
        active = win is not None and win is wm.active
        if active:
            gfx.fill(x, 0, w, TASKBAR_H, (255, 255, 255, 50 if hot else 38))
        elif hot:
            gfx.fill(x, 0, w, TASKBAR_H, (255, 255, 255, 25))
        gfx.icon(ICON_OF.get(key, 'folder'), 24, x + (w - 24) / 2, TASKBAR_H / 2 - 12)
        if win:
            inset = 0 if active or hot else 4
            gfx.fill(x + inset, 0, w - 2 * inset, 2, ACCENT_LIGHT)
