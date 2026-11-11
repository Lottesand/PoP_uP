# 파일 탐색기: 가상 파일 시스템(fs)을 돌아다니는 창
import gfx
import fs
import shell
from apps import App
from context_menu import Item, SEP
from config import *

G_BACK, G_FWD, G_UP, G_REFRESH, G_SEARCH = '', '', '', '', ''
G_CHEVRON_R, G_CHEVRON_D, G_STAR, G_CLOUD, G_NETWORK = '', '', '', '', ''
LINE = (229, 229, 229)
HOVER_FILL, HOVER_BORDER = (229, 243, 255), (229, 243, 255)
SEL_FILL, SEL_BORDER = (204, 232, 255), (153, 209, 255)
SEL_INACTIVE = (217, 217, 217)
CELL_W, CELL_H = 96, 100
STATUS_H, ADDR_H, RIBBON_H = 22, 34, 24


def noop():
    pass


class Explorer(App):
    group = 'explorer'
    size = (900, 560)
    _count = 0

    def __init__(self, node):
        Explorer._count += 1
        self.key = 'explorer#%d' % Explorer._count
        self.node = node
        self.back, self.fwd = [], []
        self.selected = self.hover = None
        self.scroll = 0
        self.last_click = (None, -1.0)
        self.items = []          # 마지막으로 그린 (노드, 사각형)
        self.crumbs = []         # (노드, x0, x1, b, t)
        self.navs = []           # (노드, b, t)
        self.buttons = {}        # 'back' / 'fwd' / 'up' → 사각형
        self.content = (0, 0, 0, 0)
        self.active = False

    @property
    def title(self):
        return self.node.name

    @property
    def icon(self):
        return self.node.icon

    # ---------------------------------------------------------------- 이동
    def go(self, node, record=True):
        node = node.resolve()
        if node is self.node:
            return
        if node.locked:
            shell.denied(node)
            return
        if record:
            self.back.append(self.node)
            self.fwd.clear()
        self.node = node
        self.selected = self.hover = None
        self.scroll = 0

    def go_back(self):
        if self.back:
            self.fwd.append(self.node)
            self.go(self.back.pop(), record=False)

    def go_forward(self):
        if self.fwd:
            self.back.append(self.node)
            self.go(self.fwd.pop(), record=False)

    def go_up(self):
        if self.node.parent:
            self.go(self.node.parent)

    def open(self, node):
        target = node.resolve()
        if target.locked:
            shell.denied(target)
        elif target.is_container() and self.node.kind != fs.RECYCLE:
            self.go(target)
        elif self.node.kind != fs.RECYCLE:
            shell.open_node(node)

    def delete_selected(self):
        if self.selected and fs.delete(self.selected):
            self.selected = None

    # ---------------------------------------------------------------- 마우스
    def item_at(self, mx, my):
        cl, cb, cw, ch = self.content
        if not (cl <= mx < cl + cw and cb <= my < cb + ch):
            return None
        for node, (l, b, w, h) in self.items:
            if l <= mx < l + w and b <= my < b + h:
                return node
        return None

    def mouse_move(self, mx, my):
        self.hover = self.item_at(mx, my) if mx is not None else None

    def mouse_down(self, mx, my, now):
        for name, (l, b, w, h) in self.buttons.items():
            if l <= mx < l + w and b <= my < b + h:
                {'back': self.go_back, 'fwd': self.go_forward, 'up': self.go_up}[name]()
                return
        for node, x0, x1, b, t in self.crumbs:
            if x0 <= mx < x1 and b <= my < t:
                self.go(node)
                return
        for node, b, t in self.navs:
            if self.content[0] - 1 > mx and b <= my < t:
                self.go(node)
                return
        node = self.item_at(mx, my)
        self.selected = node
        if node is None:
            return
        last, t = self.last_click
        self.last_click = (node, now)
        if last is node and now - t < DOUBLE_CLICK:
            self.last_click = (None, -1.0)
            self.open(node)

    def wheel(self, dy):
        self.scroll = max(0, self.scroll - dy * 60)

    def context(self, mx, my):
        cl, cb, cw, ch = self.content
        if not (cl <= mx < cl + cw and cb <= my < cb + ch):
            return None
        node = self.item_at(mx, my)
        here = self.node
        if node is not None:
            self.selected = node
            if here.kind == fs.RECYCLE:
                return [Item('복원(E)', lambda: fs.restore(node), bold=True), SEP,
                        Item('잘라내기(T)'), SEP, Item('삭제(D)', lambda: self.delete_selected()), SEP, Item('속성(R)')]
            return [Item('열기(O)', lambda: self.open(node), bold=True), SEP,
                    Item('잘라내기(T)'), Item('복사(C)'), SEP, Item('바로 가기 만들기(S)'),
                    Item('삭제(D)', lambda: self.delete_selected(), enabled=fs.deletable(node)),
                    Item('이름 바꾸기(M)'), SEP, Item('속성(R)')]
        self.selected = None
        view = [Item('보기(V)', sub=[Item('큰 아이콘(R)', noop), Item('보통 아이콘(M)', noop), Item('자세히(D)', noop)]),
                Item('정렬 기준(O)', sub=[Item('이름', noop), Item('수정한 날짜', noop), Item('유형', noop)]),
                Item('새로 고침(E)', noop), SEP]
        if here.kind == fs.RECYCLE:
            return view + [Item('휴지통 비우기(B)', self.empty_trash, enabled=bool(here.children)), SEP, Item('속성(R)')]

        def make(fn):
            def run():
                self.selected = fn(here)
            return run

        can = fs.can_modify(here)
        return view + [Item('붙여넣기(P)'), Item('바로 가기 붙여넣기(S)'), SEP,
                       Item('새로 만들기(X)', sub=[Item('폴더(F)', make(fs.new_folder)), Item('바로 가기(S)'), SEP,
                                               Item('텍스트 문서', make(fs.new_text))], enabled=can),
                       SEP, Item('속성(R)')]

    def empty_trash(self):
        for node in list(self.node.children):
            fs.delete(node)

    # ---------------------------------------------------------------- 그리기
    def ribbon_tabs(self):
        if self.node.kind == fs.THIS_PC:
            return '파일', '컴퓨터', '보기'
        if self.node.kind == fs.RECYCLE:
            return '파일', '홈', '공유', '보기', '관리'
        return '파일', '홈', '공유', '보기'

    def draw(self, l, b, w, h, active):
        self.active = active
        top = b + h
        gfx.fill(l, b, w, h, WHITE)
        # 리본 탭
        y = top - RIBBON_H
        x = l
        for i, tab in enumerate(self.ribbon_tabs()):
            tw = gfx.text_width(tab, 12) + 26
            if i == 0:
                gfx.fill(x, y, tw, RIBBON_H, (25, 121, 202))
            gfx.text(tab, x + tw / 2, y + RIBBON_H / 2, 12, WHITE if i == 0 else TEXT, align='center')
            x += tw
        gfx.symbol('', l + w - 40, y + 12, 10, TEXT_GRAY)
        gfx.symbol('', l + w - 16, y + 12, 12, ACCENT)
        gfx.line(l, y, l + w, y, LINE)
        # 주소 표시줄
        y -= ADDR_H
        cy = y + ADDR_H / 2
        self.buttons = {'back': (l + 4, y, 24, ADDR_H), 'fwd': (l + 30, y, 24, ADDR_H), 'up': (l + 70, y, 26, ADDR_H)}
        on = {'back': bool(self.back), 'fwd': bool(self.fwd), 'up': self.node.parent is not None}
        for name, g in (('back', G_BACK), ('fwd', G_FWD), ('up', G_UP)):
            bl, bb, bw, bh = self.buttons[name]
            gfx.symbol(g, bl + bw / 2, cy, 10, (60, 60, 60) if on[name] else (190, 190, 190))
        gfx.symbol(G_CHEVRON_D, l + 59, cy, 7, (130, 130, 130))
        ax, aw = l + 104, w - 104 - 230
        gfx.frame(ax, y + 5, aw, 24, (217, 217, 217))
        gfx.icon(self.node.icon, 16, ax + 5, cy - 8)
        px = ax + 26
        self.crumbs = []
        gfx.push_clip(ax + 24, y + 5, aw - 50, 24)
        for node in self.node.chain():
            gfx.symbol(G_CHEVRON_R, px + 5, cy, 7, (110, 110, 110))
            tw = gfx.text(node.name, px + 14, cy, 12)
            self.crumbs.append((node, px + 10, px + 18 + tw, y + 5, y + 29))
            px += tw + 20
        gfx.pop_clip()
        gfx.symbol(G_REFRESH, ax + aw - 14, cy, 10, (90, 90, 90))
        sx = l + w - 220
        gfx.frame(sx, y + 5, 210, 24, (217, 217, 217))
        gfx.text(self.node.name + ' 검색', sx + 8, cy, 12, (120, 120, 120))
        gfx.symbol(G_SEARCH, sx + 195, cy, 10, (90, 90, 90))

        body_b, body_t = b + STATUS_H, y - 4
        nav_w = min(200, w // 4)
        self.draw_nav(l, body_b, nav_w, body_t)
        gfx.line(l + nav_w, body_b, l + nav_w, body_t, LINE)
        self.content = (l + nav_w + 1, body_b, w - nav_w - 1, body_t - body_b)
        gfx.push_clip(*self.content)
        if self.node.kind == fs.THIS_PC:
            self.layout_this_pc(*self.content)
        else:
            self.layout_grid(*self.content)
        gfx.pop_clip()
        # 상태 표시줄
        n = len(self.node.children)
        status = '%d개 항목' % n
        if self.selected is not None:
            status += '      1개 항목 선택함'
        gfx.text(status, l + 14, b + STATUS_H / 2, 12)

    def draw_nav(self, l, b, w, t):
        self.navs = []
        ny = t - 18
        current = self.node.chain()[0]
        for node in fs.NAV:
            if node is current or node is self.node:
                gfx.fill(l + 1, ny - 11, w - 2, 22, SEL_FILL if self.active else SEL_INACTIVE)
            if node.kind == fs.QUICK:
                gfx.symbol(G_STAR, l + 34, ny, 14, ACCENT)
            elif node is fs.ONEDRIVE:
                gfx.symbol(G_CLOUD, l + 34, ny, 14, (40, 120, 220))
            elif node is fs.NETWORK:
                gfx.symbol(G_NETWORK, l + 34, ny, 14, (60, 90, 130))
            else:
                gfx.icon(node.icon, 16, l + 26, ny - 8)
            gfx.symbol(G_CHEVRON_R, l + 12, ny, 7, (150, 150, 150))
            gfx.text(node.name, l + 50, ny, 12)
            self.navs.append((node, ny - 11, ny + 11))
            ny -= 30

    def item_box(self, node, l, b, w, h):
        if node is self.selected:
            fill = SEL_FILL if self.active else SEL_INACTIVE
            gfx.fill(l, b, w, h, fill)
            gfx.frame(l, b, w, h, SEL_BORDER if self.active else SEL_INACTIVE)
        elif node is self.hover:
            gfx.fill(l, b, w, h, HOVER_FILL)

    def layout_grid(self, l, b, w, h):
        self.items = []
        children = self.node.children
        if not children:
            gfx.text('이 폴더는 비어 있습니다.', l + w / 2, b + h - 22, 12, (109, 109, 109), align='center')
            return
        cols = max(1, (w - 16) // CELL_W)
        rows = (len(children) + cols - 1) // cols
        self.scroll = min(self.scroll, max(0, rows * CELL_H + 20 - h))
        for i, node in enumerate(children):
            cx = l + 10 + (i % cols) * CELL_W
            ct = b + h - 6 - (i // cols) * CELL_H + self.scroll
            lines = gfx.wrap(node.name, CELL_W - 10, 12, max_lines=3 if node is self.selected else 2)
            box_h = 4 + 48 + 6 + 16 * len(lines) + 4
            rect = (cx + 2, ct - box_h, CELL_W - 4, box_h)
            self.items.append((node, rect))
            self.item_box(node, *rect)
            ix = cx + (CELL_W - 48) / 2
            gfx.icon(node.icon, 48, ix, ct - 52)
            if node.locked:
                gfx.icon('lock', 16, ix + 34, ct - 52)
            if node.kind in (fs.LINK, fs.APP) and node.parent is not fs.QUICK_ACCESS:
                gfx.shortcut_arrow(ix, ct - 52)
            for j, ln in enumerate(lines):
                gfx.text(ln, cx + CELL_W / 2, ct - 66 - j * 16, 12, align='center')
        if rows * CELL_H + 20 > h:
            gfx.fill(l + w - 17, b, 17, h, (240, 240, 240))
            bar_h = max(30, h * h / (rows * CELL_H + 20))
            k = self.scroll / max(1, rows * CELL_H + 20 - h)
            gfx.fill(l + w - 13, b + h - bar_h - (h - bar_h) * k, 9, bar_h, (194, 194, 194))

    def group_header(self, name, l, top, w):
        gfx.symbol(G_CHEVRON_D, l + 14, top - 12, 8, (90, 90, 90))
        tw = gfx.text(name, l + 26, top - 12, 12, (30, 57, 145))
        gfx.line(l + 34 + tw, top - 12, l + w - 16, top - 12, LINE)
        return top - 24

    def layout_this_pc(self, l, b, w, h):
        self.items = []
        folders = [n for n in self.node.children if n.kind == fs.FOLDER]
        drives = [n for n in self.node.children if n.kind == fs.DRIVE]
        y = self.group_header('폴더 (%d)' % len(folders), l, b + h - 8, w)
        cols = max(1, (w - 20) // 220)
        for i, node in enumerate(folders):
            x = l + 16 + (i % cols) * 220
            yy = y - 34 - (i // cols) * 62
            rect = (x, yy - 28, 210, 56)
            self.items.append((node, rect))
            self.item_box(node, *rect)
            gfx.icon(node.icon, 48, x + 4, yy - 24)
            gfx.text(node.name, x + 60, yy, 12)
        y -= 30 + ((len(folders) - 1) // cols + 1) * 62
        y = self.group_header('장치 및 드라이브 (%d)' % len(drives), l, y, w)
        for i, node in enumerate(drives):
            x = l + 16 + i * 300
            rect = (x, y - 70, 280, 64)
            self.items.append((node, rect))
            self.item_box(node, *rect)
            gfx.icon(node.icon, 48, x + 4, y - 64)
            if node.locked:
                gfx.icon('lock', 24, x + 32, y - 64)
            used = 0.0 if node.locked else 0.62
            gfx.text(node.name, x + 62, y - 22, 12)
            gfx.fill(x + 62, y - 44, 196, 14, (230, 230, 230))
            gfx.frame(x + 62, y - 44, 196, 14, (188, 188, 188))
            gfx.fill(x + 63, y - 43, int(194 * used), 12, (38, 160, 218))
            info = '액세스가 거부되었습니다' if node.locked else '476GB 중 181GB 사용 가능'
            gfx.text(info, x + 62, y - 58, 12, CLOSE_RED if node.locked else TEXT_GRAY)
