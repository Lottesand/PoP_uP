# 그림판: 마우스로 그리고 지우고 채운다. 그린 선은 Shift ON으로 이 창에 들어오면 밟을 수 있는 발판이 된다.
# 캔버스는 4px 칸으로 된 도트판이라 게임 도트와 굵기가 같다.
import ctypes
from collections import deque

import pico2d.pico2d as p2
from pico2d import Image
from sdl2 import SDL_CreateTexture, SDL_UpdateTexture, SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_STREAMING

import gfx
import uiblocks
import apps
from apps import App
from config import *

CW, CH = 200, 120                  # 캔버스 칸 수
CELL = 4                           # 한 칸 = 화면 4px
RIBBON_TABS_H, RIBBON_H, STATUS_H = 24, 92, 24
TOOLS = [('pencil', '연필', 1), ('brush', '브러시', 3), ('eraser', '지우개', 5), ('fill', '채우기', 0)]
COLORS = [(0, 0, 0), (127, 127, 127), (136, 0, 21), (237, 28, 36), (255, 127, 39), (255, 242, 0),
          (34, 177, 76), (0, 162, 232), (63, 72, 204), (163, 73, 164), (255, 255, 255), (195, 195, 195)]
PAPER = (255, 255, 255)


class Paint(App):
    group = 'paint'
    key, icon = 'paint', 'paint'
    size = (CW * CELL + 60, CH * CELL + 220)
    min_size = (520, 400)

    def __init__(self):
        self.pixels = bytearray(b'\xff' * (CW * CH * 4))      # RGBA, 처음엔 흰 종이
        self.ink = bytearray(CW * CH)                         # 칠해진 칸 (발판 계산용)
        self.color, self.tool = (0, 0, 0), 'pencil'
        self.texture = None
        self.dirty = True
        self.drawing = False
        self.last = None
        self.canvas = (0, 0, 0, 0)
        self.ui = []                                          # (사각형, 할 일)
        self.cursor_cell = None
        self.plat_cache = None
        self.file = None                                      # 저장한 그림 파일 (fs 노드)

    @property
    def title(self):
        return (self.file.name if self.file else '제목 없음') + ' - 그림판'

    # ---------------------------------------------------------------- 저장
    def save(self):
        """Ctrl+S / [저장]: 하얀 칸은 투명으로, 칠한 부분만 잘라 바탕 화면에 .png로 저장하고 사진 앱으로 연다"""
        import fs
        import shell
        from drawing import Drawing
        picture = Drawing.from_canvas(self.pixels, CW, CH)
        if picture is None:
            shell.error('그림판', '저장할 그림이 없습니다.', '', '캔버스에 무언가를 그린 다음 저장하세요.')
            return None
        if self.file is None or self.file.parent is None:
            desk = fs.DESKTOP_FOLDER
            self.file = desk.add(fs.Node(desk.unique_name('그림', '.png'), fs.FILE, icon='image_file'))
        self.file.picture = picture
        shell.open_node(self.file)
        return self.file

    def shortcut(self, key):
        from sdl2 import SDLK_s
        if key == SDLK_s:
            self.save()
            return True
        return False

    # ---------------------------------------------------------------- 칠하기
    def set_cell(self, cx, cy, c):
        if 0 <= cx < CW and 0 <= cy < CH:
            i = (cy * CW + cx) * 4
            self.pixels[i:i + 3] = bytes(c)
            self.ink[cy * CW + cx] = 0 if c == PAPER else 1

    def stamp(self, cx, cy):
        size = dict((t, s) for t, _, s in TOOLS)[self.tool]
        c = PAPER if self.tool == 'eraser' else self.color
        r = size // 2
        for dy in range(-r, size - r):
            for dx in range(-r, size - r):
                self.set_cell(cx + dx, cy + dy, c)
        self.changed()

    def stroke(self, a, b):
        (x0, y0), (x1, y1) = a, b
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.stamp(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n))

    def flood(self, cx, cy):
        """페인트통: 같은 색으로 이어진 칸을 모두 바꾼다"""
        def at(x, y):
            i = (y * CW + x) * 4
            return tuple(self.pixels[i:i + 3])
        old = at(cx, cy)
        if old == self.color:
            return
        todo = deque([(cx, cy)])
        seen = {(cx, cy)}
        while todo:
            x, y = todo.popleft()
            self.set_cell(x, y, self.color)
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < CW and 0 <= ny < CH and (nx, ny) not in seen and at(nx, ny) == old:
                    seen.add((nx, ny))
                    todo.append((nx, ny))
        self.changed()

    def changed(self):
        self.dirty = True
        self.plat_cache = None

    def clear(self):
        self.pixels[:] = b'\xff' * (CW * CH * 4)
        self.ink[:] = bytes(CW * CH)
        self.changed()

    # ---------------------------------------------------------------- 마우스
    def cell_at(self, mx, my):
        l, b, w, h = self.canvas
        if not (l <= mx < l + w and b <= my < b + h):
            return None
        return int((mx - l) // CELL), int((b + h - 1 - my) // CELL)

    def mouse_down(self, mx, my, now):
        for (l, b, w, h), act in self.ui:
            if l <= mx < l + w and b <= my < b + h:
                act()
                return
        cell = self.cell_at(mx, my)
        if cell is None:
            return
        if self.tool == 'fill':
            self.flood(*cell)
            return
        self.drawing = True
        self.last = cell
        self.stamp(*cell)

    def mouse_drag(self, mx, my):
        self.cursor_cell = self.cell_at(mx, my)
        if not self.drawing:
            return
        l, b, w, h = self.canvas
        cell = (min(CW - 1, max(0, int((mx - l) // CELL))), min(CH - 1, max(0, int((b + h - 1 - my) // CELL))))
        self.stroke(self.last, cell)
        self.last = cell

    def mouse_move(self, mx, my):
        self.cursor_cell = self.cell_at(mx, my) if mx is not None else None

    def mouse_up(self, mx, my):
        self.drawing = False

    # ---------------------------------------------------------------- 발판
    def platforms(self):
        """칠해진 칸 중 바로 위가 빈 칸인 윗면을 발판으로 (창 안에서 밟고 올라설 수 있다)"""
        if self.plat_cache is None:
            segs = []
            for y in range(CH):
                x = 0
                while x < CW:
                    if self.ink[y * CW + x] and (y == 0 or not self.ink[(y - 1) * CW + x]):
                        x0 = x
                        while x < CW and self.ink[y * CW + x] and (y == 0 or not self.ink[(y - 1) * CW + x]):
                            x += 1
                        segs.append((x0, x, y))
                    else:
                        x += 1
            self.plat_cache = segs
        l, b, w, h = self.canvas
        top = b + h
        return [(l + x0 * CELL, l + x1 * CELL, top - y * CELL) for x0, x1, y in self.plat_cache]

    # ---------------------------------------------------------------- 그리기
    def upload(self):
        if self.texture is None:
            tex = SDL_CreateTexture(p2.renderer, SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_STREAMING, CW, CH)
            self.texture = Image(tex)
        if self.dirty:
            buf = (ctypes.c_ubyte * len(self.pixels)).from_buffer(self.pixels)
            SDL_UpdateTexture(self.texture.texture, None, buf, CW * 4)
            self.dirty = False

    def button(self, l, b, w, h, label, on, act):
        gfx.fill(l, b, w, h, (204, 232, 255) if on else (245, 246, 247))
        gfx.frame(l, b, w, h, (153, 209, 255) if on else (220, 220, 220))
        gfx.text(label, l + w / 2, b + h / 2, 12, align='center')
        self.ui.append(((l, b, w, h), act))
        uiblocks.add('btn:' + label, l, b, w, h)

    def draw(self, l, b, w, h, active):
        top = b + h
        self.ui = []
        gfx.fill(l, b, w, h, (201, 211, 226))
        # 리본 탭
        gfx.fill(l, top - RIBBON_TABS_H, w, RIBBON_TABS_H, WHITE)
        gfx.fill(l, top - RIBBON_TABS_H, 50, RIBBON_TABS_H, (25, 121, 202))
        gfx.text('파일', l + 25, top - 12, 12, WHITE, align='center')
        gfx.text('홈', l + 70, top - 12, 12)
        gfx.text('보기', l + 104, top - 12, 12)
        for key, x0, tw in (('파일', l, 50), ('홈', l + 54, 32), ('보기', l + 86, 36)):
            uiblocks.add('ribbon:' + key, x0, top - RIBBON_TABS_H, tw, RIBBON_TABS_H)
        ry = top - RIBBON_TABS_H - RIBBON_H
        gfx.fill(l, ry, w, RIBBON_H, (245, 246, 247))
        gfx.line(l, ry, l + w, ry, (218, 219, 220))
        # 도구
        x = l + 10
        for i, (tool, label, size) in enumerate(TOOLS):
            bx, by = x + (i % 2) * 64, ry + 52 - (i // 2) * 30
            self.button(bx, by, 60, 26, label, self.tool == tool, lambda t=tool: setattr(self, 'tool', t))
        gfx.text('도구', x + 62, ry + 10, 12, (90, 90, 90), align='center')
        x += 140
        gfx.line(x, ry + 6, x, ry + RIBBON_H - 6, (226, 227, 228))
        self.button(x + 10, ry + 52, 70, 26, '모두 지우기', False, self.clear)
        self.button(x + 10, ry + 22, 70, 26, '저장 (Ctrl+S)', False, self.save)
        gfx.text('이미지', x + 45, ry + 10, 12, (90, 90, 90), align='center')
        x += 90
        gfx.line(x, ry + 6, x, ry + RIBBON_H - 6, (226, 227, 228))
        # 색 1 (지금 색) + 팔레트
        gfx.fill(x + 12, ry + 30, 40, 40, self.color)
        gfx.frame(x + 10, ry + 28, 44, 44, (60, 60, 60), 2)
        gfx.text('색 1', x + 32, ry + 10, 12, (90, 90, 90), align='center')
        x += 66
        for i, c in enumerate(COLORS):
            sx, sy = x + (i % 6) * 24, ry + 54 - (i // 6) * 24
            gfx.fill(sx, sy, 20, 20, c)
            gfx.frame(sx, sy, 20, 20, (60, 60, 60) if c == self.color else (160, 160, 160), 2 if c == self.color else 1)
            self.ui.append(((sx, sy, 20, 20), lambda c=c: setattr(self, 'color', c)))
            uiblocks.add('color:%d' % i, sx, sy, 20, 20)
        gfx.text('색', x + 70, ry + 10, 12, (90, 90, 90), align='center')
        # 캔버스
        self.canvas = (l + 6, ry - 6 - CH * CELL, CW * CELL, CH * CELL)
        cl, cb, cw, ch = self.canvas
        gfx.fill(cl + 3, cb - 3, cw, ch, (150, 160, 175))           # 종이 그림자
        self.upload()
        self.texture.draw_to_origin(cl, cb, cw, ch)
        # 상태 표시줄
        gfx.fill(l, b, w, STATUS_H, (240, 240, 240))
        if self.cursor_cell:
            gfx.text('%d, %dpx' % (self.cursor_cell[0] * CELL, self.cursor_cell[1] * CELL), l + 30, b + 12, 12)
        gfx.text('%d × %d픽셀' % (cw, ch), l + 200, b + 12, 12)


apps.APPS['paint'] = Paint
