# 윈도우 10 오른쪽 클릭 메뉴 (하위 메뉴 포함)
import gfx
from config import *

ITEM_H, SEP_H, PAD = 22, 9, 3
MENU_BG = (242, 242, 242)
MENU_BORDER = (204, 204, 204)
HOT = (145, 201, 247, 110)
DISABLED = (160, 160, 160)


class Item:
    def __init__(self, label, action=None, sub=None, enabled=None, bold=False):
        self.label, self.action, self.sub, self.bold = label, action, sub, bold
        self.enabled = enabled if enabled is not None else (action is not None or sub is not None)


SEP = None


class ContextMenu:
    def __init__(self, items, x, y, parent_w=0):
        self.items = items
        self.hover = None
        self.sub = None
        self.w = max(200, max(gfx.text_width(i.label, 12) for i in items if i) + 34 + 40)
        self.h = PAD * 2 + sum(ITEM_H if i else SEP_H for i in items)
        # 화면 밖으로 나가면 반대쪽으로 펼친다
        if x + self.w > W:
            x = x - self.w - parent_w
        top = y
        if top - self.h < 0:
            top = min(H, top + self.h if parent_w == 0 else self.h)
        self.l, self.top = max(0, x), top

    def rows(self):
        y = self.top - PAD
        for i, item in enumerate(self.items):
            h = ITEM_H if item else SEP_H
            yield i, item, y - h, h
            y -= h

    def inside(self, mx, my):
        return self.l <= mx < self.l + self.w and self.top - self.h <= my < self.top

    def contains(self, mx, my):
        return self.inside(mx, my) or (self.sub is not None and self.sub.contains(mx, my))

    def row_at(self, mx, my):
        if not self.inside(mx, my):
            return None
        for i, item, b, h in self.rows():
            if b <= my < b + h:
                return i if item else None
        return None

    def mouse_move(self, mx, my):
        if self.sub and self.sub.contains(mx, my):
            self.sub.mouse_move(mx, my)
            return
        i = self.row_at(mx, my)
        if i is None:
            if not self.inside(mx, my) and self.sub is None:
                self.hover = None
            return
        if i != self.hover:
            self.hover = i
            self.sub = None
            item = self.items[i]
            if item.sub and item.enabled:
                for j, it, b, h in self.rows():
                    if j == i:
                        self.sub = ContextMenu(item.sub, self.l + self.w - 2, b + h + PAD, self.w)

    def click(self, mx, my):
        """메뉴 안을 눌렀으면 True. 실행할 일이 있으면 실행한다. 메뉴를 닫아야 하면 'close'"""
        if self.sub and self.sub.contains(mx, my):
            return self.sub.click(mx, my)
        i = self.row_at(mx, my)
        if i is None:
            return True
        item = self.items[i]
        if item.enabled and item.action:
            item.action()
            return 'close'
        return True

    def draw(self):
        l, b = self.l, self.top - self.h
        gfx.shadow(l, b, self.w, self.h, 6, 50)
        gfx.fill(l, b, self.w, self.h, MENU_BG)
        gfx.frame(l, b, self.w, self.h, MENU_BORDER)
        for i, item, rb, rh in self.rows():
            if item is None:
                gfx.line(l + 30, rb + rh // 2, l + self.w - 3, rb + rh // 2, (215, 215, 215))
                continue
            if i == self.hover and item.enabled:
                gfx.fill(l + 2, rb, self.w - 4, rh, HOT)
            c = TEXT if item.enabled else DISABLED
            gfx.text(item.label, l + 34, rb + rh / 2, 12, c, FONT_BOLD if item.bold else FONT)
            if item.sub:
                gfx.symbol('', l + self.w - 14, rb + rh / 2, 8, c)
        if self.sub:
            self.sub.draw()
