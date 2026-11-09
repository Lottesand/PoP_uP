# 바탕화면: 배경화면 + 왼쪽 위부터 세로로 쌓이는 아이콘. 더블클릭하면 프로그램을 연다.
import gfx
from config import *

# (프로그램 키, 이름, 아이콘, 바로 가기 화살표 여부)
ICONS = [
    ('this_pc', '내 PC', 'this_pc', False),
    ('recycle_bin', '휴지통', 'recycle_bin', False),
    ('documents', '문서', 'folder', False),
    ('notepad', '탈출 계획.txt', 'text_file', False),
    ('browser', 'Chrome', 'browser', True),
    ('paint', '그림판', 'paint', True),
    ('vscode', 'Visual Studio Code', 'vscode', True),
    ('kakao', '카카오톡', 'kakao', True),
    ('terminal', '명령 프롬프트', 'terminal', True),
]

LABEL_W = ICON_CELL_W - 6


class Desktop:
    def __init__(self):
        self.hover = None
        self.selected = None
        self.focused = False           # 바탕화면을 마지막으로 클릭했는가 (선택 색이 진해진다)
        self.last_click = (None, -1.0)

    def cell(self, i):
        rows = (H - TASKBAR_H - 4) // ICON_CELL_H
        col, row = i // rows, i % rows
        l = 2 + col * ICON_CELL_W
        top = H - 2 - row * ICON_CELL_H
        return l, top - ICON_CELL_H, ICON_CELL_W, ICON_CELL_H

    def hit(self, mx, my):
        for i in range(len(ICONS)):
            l, b, w, h = self.cell(i)
            if l <= mx < l + w and b <= my < b + h:
                return i
        return None

    def mouse_move(self, mx, my):
        self.hover = self.hit(mx, my)

    def mouse_down(self, mx, my, now):
        """더블클릭하면 열 프로그램 키를 돌려준다"""
        i = self.hit(mx, my)
        self.focused = True
        self.selected = i
        if i is None:
            return None
        last_i, last_t = self.last_click
        self.last_click = (i, now)
        if last_i == i and now - last_t < DOUBLE_CLICK:
            self.last_click = (None, -1.0)
            return ICONS[i][0]
        return None

    def draw(self):
        gfx.image('wallpaper.png').draw_to_origin(0, 0, W, H)
        for i, (key, name, icon, shortcut) in enumerate(ICONS):
            l, b, w, h = self.cell(i)
            top = b + h
            lines = gfx.wrap(name, LABEL_W, 12, max_lines=2 if i != self.selected else 4)
            box_h = 4 + 48 + 6 + 16 * len(lines) + 4
            if i == self.selected:
                c = (204, 232, 255, 110) if self.focused else (255, 255, 255, 50)
                gfx.fill(l + 1, top - box_h, w - 2, box_h, c)
                gfx.frame(l + 1, top - box_h, w - 2, box_h, (153, 209, 255, 160) if self.focused else (255, 255, 255, 80))
            elif i == self.hover:
                gfx.fill(l + 1, top - box_h, w - 2, box_h, (255, 255, 255, 40))
                gfx.frame(l + 1, top - box_h, w - 2, box_h, (255, 255, 255, 70))
            ix, ib = l + (w - 48) / 2, top - 4 - 48
            gfx.icon(icon, 48, ix, ib)
            if shortcut:
                draw_shortcut_arrow(ix, ib)
            for j, ln in enumerate(lines):
                y = ib - 6 - 8 - j * 16
                gfx.text(ln, l + w / 2 + 1, y - 1, 12, (0, 0, 0, 170), align='center')
                gfx.text(ln, l + w / 2, y, 12, WHITE, align='center')


def draw_shortcut_arrow(l, b):
    # 바로 가기 아이콘 왼쪽 아래의 작은 화살표
    gfx.fill(l, b, 13, 13, WHITE)
    gfx.frame(l, b, 13, 13, (130, 130, 130))
    c = (0, 84, 166)
    gfx.line(l + 3, b + 3, l + 9, b + 9, c)
    gfx.line(l + 3, b + 4, l + 8, b + 9, c)
    gfx.line(l + 5, b + 9, l + 9, b + 9, c)
    gfx.line(l + 9, b + 5, l + 9, b + 9, c)
