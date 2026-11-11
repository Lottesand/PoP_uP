# 바탕화면: 배경화면 + 바탕 화면 폴더(fs.DESKTOP_FOLDER)의 아이콘들.
# 아이콘은 격자 칸 (열, 행)에 놓이고, 끌어서 다른 칸·폴더·휴지통·탐색기 창으로 옮길 수 있다.
import os
import gfx
import fs
import shell
from context_menu import Item, SEP
from config import *

LABEL_W = ICON_CELL_W - 6
ROWS = (H - TASKBAR_H - 4) // ICON_CELL_H
COLS = W // ICON_CELL_W
DRAG_START = 5


def noop():
    pass


def wallpaper_name():
    for name in WALLPAPERS:
        if os.path.exists(os.path.join(ASSETS, name)):
            return name
    return WALLPAPERS[-1]


def cell_rect(col, row):
    return 2 + col * ICON_CELL_W, H - 2 - (row + 1) * ICON_CELL_H, ICON_CELL_W, ICON_CELL_H


def cell_at(mx, my):
    col = min(COLS - 1, max(0, int(mx - 2) // ICON_CELL_W))
    row = min(ROWS - 1, max(0, int(H - 2 - my) // ICON_CELL_H))
    return col, row


class Desktop:
    def __init__(self):
        self.folder = fs.DESKTOP_FOLDER
        self.wallpaper = wallpaper_name()
        self.hover = None
        self.selected = None
        self.focused = False           # 바탕화면을 마지막으로 클릭했는가 (선택 색이 진해진다)
        self.last_click = (None, -1.0)
        self.press = None              # (노드, 누른 x, y)
        self.dragging = False
        self.mouse = (0, 0)
        self.drop = None               # 끌고 있는 아이콘을 놓으면 들어갈 노드

    # ---------------------------------------------------------------- 칸 배치
    def items(self):
        used = set()
        for node in self.folder.children:
            if node.pos is not None and node.pos not in used:
                used.add(node.pos)
            else:
                node.pos = None
        for node in self.folder.children:
            if node.pos is None:
                node.pos = self.free_cell(used)
                used.add(node.pos)
        return self.folder.children

    def free_cell(self, used, near=None):
        cells = [(c, r) for c in range(COLS) for r in range(ROWS) if (c, r) not in used]
        if near is None:
            return cells[0]
        return min(cells, key=lambda cr: (cr[0] - near[0]) ** 2 + (cr[1] - near[1]) ** 2)

    def node_at(self, mx, my):
        for node in self.items():
            l, b, w, h = cell_rect(*node.pos)
            if l <= mx < l + w and b <= my < b + h:
                return node
        return None

    # ---------------------------------------------------------------- 마우스
    def mouse_move(self, mx, my, over_other):
        self.mouse = (mx, my)
        if self.press:
            node, px, py = self.press
            if not self.dragging and abs(mx - px) + abs(my - py) >= DRAG_START:
                self.dragging = True
            if self.dragging:
                self.drop = self.drop_target(mx, my)
                return True
        self.hover = None if over_other else self.node_at(mx, my)
        return False

    def drop_target(self, mx, my):
        win, part = shell.wm.hit(mx, my)
        if win:
            folder = getattr(win.app, 'node', None)
            return folder if part[0] == 'client' and folder is not None else None
        node = self.node_at(mx, my)
        if node is None or node is self.press[0]:
            return None
        return node if node.is_container() else None

    def mouse_down(self, mx, my, now):
        node = self.node_at(mx, my)
        self.focused = True
        self.selected = node
        if node is None:
            return
        self.press = (node, mx, my)
        last, t = self.last_click
        self.last_click = (node, now)
        if last is node and now - t < DOUBLE_CLICK:
            self.last_click = (None, -1.0)
            self.press = None
            shell.open_node(node)

    def mouse_up(self, mx, my):
        if self.press and self.dragging:
            node = self.press[0]
            target = self.drop_target(mx, my)
            if target is not None:
                fs.move(node, target)
            elif shell.wm.hit(mx, my)[0] is None and my >= TASKBAR_H:
                used = {n.pos for n in self.folder.children if n is not node}
                want = cell_at(mx, my)
                node.pos = want if want not in used else self.free_cell(used, want)
        self.press = None
        self.dragging = False
        self.drop = None

    def context(self, mx, my):
        node = self.node_at(mx, my)
        self.focused = True
        self.selected = node
        if node is not None:
            return [Item('열기(O)', lambda: shell.open_node(node), bold=True), SEP,
                    Item('잘라내기(T)'), Item('복사(C)'), SEP, Item('바로 가기 만들기(S)'),
                    Item('삭제(D)', lambda: self.delete(node), enabled=fs.deletable(node)),
                    Item('이름 바꾸기(M)'), SEP, Item('속성(R)')]
        cell = cell_at(mx, my)

        def make(fn):
            def run():
                new = fn(self.folder)
                used = {n.pos for n in self.folder.children if n is not new}
                new.pos = cell if cell not in used else self.free_cell(used, cell)
                self.selected = new
            return run

        return [Item('보기(V)', sub=[Item('큰 아이콘(R)', noop), Item('보통 아이콘(M)', noop),
                                    Item('작은 아이콘(N)', noop), SEP, Item('아이콘 자동 정렬(A)', noop),
                                    Item('아이콘을 그리드에 맞춤(I)', noop), SEP,
                                    Item('바탕 화면 아이콘 표시(D)', noop)]),
                Item('정렬 기준(O)', sub=[Item('이름', noop), Item('크기', noop), Item('항목 유형', noop),
                                       Item('수정한 날짜', noop)]),
                Item('새로 고침(E)', noop), SEP,
                Item('붙여넣기(P)'), Item('바로 가기 붙여넣기(S)'), SEP,
                Item('새로 만들기(X)', sub=[Item('폴더(F)', make(fs.new_folder)), Item('바로 가기(S)'), SEP,
                                         Item('텍스트 문서', make(fs.new_text))]), SEP,
                Item('디스플레이 설정(D)', noop), Item('개인 설정(R)', noop)]

    def delete(self, node):
        if fs.delete(node) and self.selected is node:
            self.selected = None

    # ---------------------------------------------------------------- 그리기
    def draw(self):
        gfx.image(self.wallpaper).draw_to_origin(0, 0, W, H)
        dragged = self.press[0] if self.dragging else None
        for node in self.items():
            l, b, w, h = cell_rect(*node.pos)
            self.draw_icon(node, l, b + h, node is self.selected, node is self.hover or node is self.drop,
                           0.5 if node is dragged else None)

    def draw_drag(self):
        # 끌고 있는 아이콘은 창들보다 위에 반투명하게 그린다
        if not self.dragging:
            return
        node, px, py = self.press
        l, b, w, h = cell_rect(*node.pos)
        mx, my = self.mouse
        self.draw_icon(node, l + mx - px, b + h + my - py, False, False, 0.6)

    def draw_icon(self, node, l, top, selected, hot, alpha):
        w = ICON_CELL_W
        lines = gfx.wrap(node.name, LABEL_W, 12, max_lines=4 if selected else 2)
        box_h = 4 + 48 + 6 + 16 * len(lines) + 4
        if selected:
            c = (204, 232, 255, 110) if self.focused else (255, 255, 255, 50)
            gfx.fill(l + 1, top - box_h, w - 2, box_h, c)
            gfx.frame(l + 1, top - box_h, w - 2, box_h, (153, 209, 255, 160) if self.focused else (255, 255, 255, 80))
        elif hot:
            gfx.fill(l + 1, top - box_h, w - 2, box_h, (255, 255, 255, 40))
            gfx.frame(l + 1, top - box_h, w - 2, box_h, (255, 255, 255, 70))
        ix, ib = l + (w - 48) / 2, top - 4 - 48
        gfx.icon(node.icon, 48, ix, ib, alpha)
        if node.kind in (fs.LINK, fs.APP) and node.resolve().kind not in (fs.THIS_PC, fs.RECYCLE):
            gfx.shortcut_arrow(ix, ib)
        a = 255 if alpha is None else int(255 * alpha)
        for j, ln in enumerate(lines):
            y = ib - 6 - 8 - j * 16
            gfx.text(ln, l + w / 2 + 1, y - 1, 12, (0, 0, 0, int(a * 0.7)), align='center')
            gfx.text(ln, l + w / 2, y, 12, (255, 255, 255, a), align='center')
