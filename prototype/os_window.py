from pico2d import draw_rectangle, draw_line, draw_circle

from config import *
from geometry import Rect


# ---------------------------------------------------------------- 창 안의 물체
# 위치(lx, ly)는 창 내용 영역 기준 로컬 좌표.
# 창을 아래로 늘려도 물체가 위쪽에 붙어 있도록 "처음 내용 높이(design_h)" 기준으로 계산한다.

class Item:
    solid = False

    def __init__(self, lx, ly, w, h):
        self.lx, self.ly, self.w, self.h = lx, ly, w, h
        self.active = True

    def rect(self, win):
        return Rect(win.content.l + self.lx, win.content.t - win.design_h + self.ly, self.w, self.h)

    def draw(self, win, font):
        pass


class Shelf(Item):
    solid = True

    def draw(self, win, font):
        r = self.rect(win)
        draw_rectangle(r.l, r.b, r.r, r.t, 150, 110, 70, 255, True)


class Plate(Item):
    """계산기 숫자 발판. 위에 착지하면 숫자가 입력된다."""
    solid = True

    def __init__(self, lx, ly, digit):
        super().__init__(lx, ly, 44, 12)
        self.digit = digit
        self.flash = 0.0

    def draw(self, win, font):
        r = self.rect(win)
        c = (255, 230, 120) if self.flash > 0 else (215, 215, 225)
        draw_rectangle(r.l, r.b, r.r, r.t, *c, 255, True)
        draw_rectangle(r.l, r.b, r.r, r.t, 90, 90, 100)
        font.draw(r.l + 17, r.t + 10, self.digit, (60, 60, 70))


class Key(Item):
    def __init__(self, lx, ly):
        super().__init__(lx, ly, 16, 16)
        self.active = False   # PIN 을 맞추면 나타난다

    def draw(self, win, font):
        r = self.rect(win)
        draw_circle(int(r.l + 8), int(r.t - 5), 5, 230, 180, 20, filled=True)
        draw_rectangle(r.l + 7, r.b, r.l + 9, r.t - 8, 230, 180, 20, 255, True)
        draw_rectangle(r.l + 9, r.b + 2, r.l + 13, r.b + 4, 230, 180, 20, 255, True)


class Vault(Item):
    """잠긴 금고. 열쇠를 든 채로 닿으면 열리고, 열린 뒤 들어가면 탈출."""

    def __init__(self, lx, ly):
        super().__init__(lx, ly, 60, 80)
        self.opened = False

    @property
    def solid(self):
        return not self.opened

    def draw(self, win, font):
        r = self.rect(win)
        if self.opened:
            draw_rectangle(r.l, r.b, r.r, r.t, 60, 200, 90, 255, True)
            font.draw(r.l + 12, r.t - 40, 'EXIT', (255, 255, 255))
        else:
            draw_rectangle(r.l, r.b, r.r, r.t, 70, 70, 80, 255, True)
            draw_rectangle(r.l + 22, r.b + 30, r.l + 38, r.b + 46, 230, 180, 20, 255, True)
            draw_circle(int(r.l + 30), int(r.b + 50), 7, 230, 180, 20)


class Icon:
    """더블클릭하면 target 창을 여는 아이콘 (바탕화면, 폴더 창 공용)."""

    def __init__(self, name, target, kind):
        self.name, self.target, self.kind = name, target, kind   # kind: 'folder' / 'file' / 'app'
        self.lx = self.ly = 0
        self.x = self.y = 0    # 바탕화면 아이콘일 때 월드 좌표

    def rect_at(self, x, y):
        return Rect(x, y, 48, 40)

    def draw_at(self, x, y, font, label_color):
        if self.kind == 'folder':
            draw_rectangle(x, y, x + 48, y + 32, 240, 200, 80, 255, True)
            draw_rectangle(x, y + 32, x + 20, y + 38, 240, 200, 80, 255, True)
        elif self.kind == 'file':
            draw_rectangle(x + 10, y, x + 38, y + 40, 250, 250, 250, 255, True)
            draw_rectangle(x + 10, y, x + 38, y + 40, 120, 120, 120)
            for i in range(4):
                draw_line(x + 14, y + 30 - i * 7, x + 34, y + 30 - i * 7, 150, 150, 150)
        else:
            draw_rectangle(x + 4, y, x + 44, y + 40, 90, 110, 140, 255, True)
            draw_rectangle(x + 9, y + 26, x + 39, y + 35, 200, 230, 200, 255, True)
        label = self.name if len(self.name) <= 8 else self.name[:7] + '…'
        font.draw(x - 4, y - 10, label, label_color)


# ---------------------------------------------------------------- 창

class OSWindow:
    def __init__(self, wid, title, kind, x, y, w, h, frozen=False):
        self.wid, self.title, self.kind = wid, title, kind
        self.x, self.y, self.w, self.h = x, y, w, h
        self.frozen = frozen          # 응답 없음: 이동/크기조절/포커스 불가
        self.opened = False
        self.min_w, self.min_h = 160, 110
        self.design_h = self.content.h
        self.items = []
        self.icons = []
        self.lines = []
        self.moved_dx = self.moved_dy = 0.0   # 이번 프레임에 마우스로 움직인 양

    # ---- 영역들
    @property
    def outer(self):
        return Rect(self.x, self.y, self.w, self.h)

    @property
    def content(self):
        return Rect(self.x + BORDER, self.y + BORDER, self.w - 2 * BORDER, self.h - 2 * BORDER - TITLE_H)

    @property
    def title_rect(self):
        return Rect(self.x, self.y + self.h - TITLE_H, self.w, TITLE_H)

    @property
    def close_rect(self):
        return Rect(self.x + self.w - CLOSE_W - 3, self.y + self.h - TITLE_H + 3, CLOSE_W, TITLE_H - 6)

    @property
    def grip_rect(self):
        return Rect(self.x + self.w - GRIP, self.y, GRIP, GRIP)

    @property
    def ladder(self):
        c = self.content
        return Rect(c.r - SCROLL_W, c.b, SCROLL_W, c.h)

    def visible(self, item_rect):
        # pico2d 에는 잘라 그리기(클리핑)가 없으므로, 창 밖으로 조금이라도 나간 물체는 통째로 숨긴다
        return self.content.contains(item_rect)

    def visible_items(self):
        return [it for it in self.items if it.active and self.visible(it.rect(self))]

    def icon_rect(self, icon):
        c = self.content
        return icon.rect_at(c.l + icon.lx, c.t - self.design_h + icon.ly)

    def icon_at(self, px, py):
        for ic in self.icons:
            r = self.icon_rect(ic)
            if self.visible(r) and r.contains_point(px, py):
                return ic
        return None

    # ---- 마우스 조작
    def move_to(self, nx, ny):
        nx = max(60 - self.w, min(nx, CANVAS_W - 60))
        ny = max(TASKBAR_H - self.h + TITLE_H, min(ny, CANVAS_H - self.h))
        self.moved_dx += nx - self.x
        self.moved_dy += ny - self.y
        self.x, self.y = nx, ny

    def resize_to(self, mx, my):
        # 윈도우처럼 좌상단은 고정하고 우하단만 움직인다
        top = self.y + self.h
        self.w = max(self.min_w, min(mx - self.x, CANVAS_W - self.x))
        self.h = max(self.min_h, top - max(my, 0))
        self.y = top - self.h

    # ---- 그리기
    def draw(self, font, small, translucent, focused, extra=None):
        a = 110 if translucent else 255
        o = self.outer
        draw_rectangle(o.l, o.b, o.r, o.t, 195, 195, 205, a, True)
        if self.frozen:
            tc = (140, 140, 140)
        elif focused:
            tc = (20, 70, 170)
        else:
            tc = (110, 125, 160)
        t = self.title_rect
        draw_rectangle(t.l, t.b, t.r, t.t, *tc, a, True)
        title = self.title + ('  (응답 없음)' if self.frozen else '')
        small.draw(t.l + 8, t.b + TITLE_H / 2, title, (255, 255, 255))
        cr = self.close_rect
        draw_rectangle(cr.l, cr.b, cr.r, cr.t, 200, 60, 60, a, True)
        small.draw(cr.l + 7, cr.b + cr.h / 2, 'X', (255, 255, 255))

        c = self.content
        draw_rectangle(c.l, c.b, c.r, c.t, 252, 252, 252, a, True)
        lad = self.ladder
        draw_rectangle(lad.l, lad.b, lad.r, lad.t, 220, 220, 228, a, True)
        draw_rectangle(lad.l + 2, lad.t - 60, lad.r - 2, lad.t - 4, 170, 170, 185, a, True)
        g = self.grip_rect
        for i in range(3):
            draw_line(g.r - 3 - i * 4, g.b + 2, g.r - 2, g.b + 3 + i * 4, 120, 120, 120)

        for ic in self.icons:
            r = self.icon_rect(ic)
            if self.visible(r.inflate(4)):
                ic.draw_at(r.l, r.b, small, (40, 40, 40))
        for i, line in enumerate(self.lines):
            ly = c.t - 18 - i * 24
            if ly - 10 >= c.b:
                max_chars = max(0, int((c.w - SCROLL_W - 16) / 9))
                font.draw(c.l + 10, ly, line[:max_chars], (30, 30, 30))
        if extra:
            extra(self)
        for it in self.visible_items():
            it.draw(self, small)

        if translucent:
            # 벽 모드에서 내 레이어보다 위에 있는 창 = 부술 수 있는 벽
            for d in range(2):
                draw_rectangle(o.l + d, o.b + d, o.r - d, o.t - d, 220, 50, 50)
