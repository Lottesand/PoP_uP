# 시작 메뉴: 왼쪽 단추 줄 + 앱 목록 + 타일
import gfx
from config import *

MENU_W, MENU_H = 660, 640
RAIL_W, LIST_W = 48, 280

LIST = [
    ('C', None, None), ('browser', 'Chrome', 'browser'),
    ('V', None, None), ('vscode', 'Visual Studio Code', 'vscode'),
    ('ㄱ', None, None), ('paint', '그림판', 'paint'),
    ('ㅁ', None, None), ('terminal', '명령 프롬프트', 'terminal'), ('notepad', '메모장', 'notepad'),
    ('ㅋ', None, None), ('kakao', '카카오톡', 'kakao'),
    ('ㅍ', None, None), ('documents', '파일 탐색기', 'folder'),
]
TILES = [('this_pc', '내 PC', 'this_pc'), ('documents', '문서', 'folder'), ('browser', 'Chrome', 'browser'),
         ('notepad', '메모장', 'notepad'), ('paint', '그림판', 'paint'), ('recycle_bin', '휴지통', 'recycle_bin')]
TILE, GAP = 100, 4


class StartMenu:
    def __init__(self):
        self.open = False
        self.hover = None

    def rect(self):
        return 0, TASKBAR_H, MENU_W, MENU_H

    def contains(self, mx, my):
        l, b, w, h = self.rect()
        return self.open and l <= mx < l + w and b <= my < b + h

    def items(self):
        """(키, 사각형) 목록"""
        l, b, w, h = self.rect()
        top = b + h
        out = []
        y = top - 12
        for key, name, icon in LIST:
            ih = 36
            if name:
                out.append((key, (l + RAIL_W, y - ih, LIST_W, ih)))
            y -= ih
        tx, ty = l + RAIL_W + LIST_W + 8, top - 44
        for i, (key, name, icon) in enumerate(TILES):
            out.append((('tile', key), (tx + (i % 3) * (TILE + GAP), ty - (i // 3 + 1) * (TILE + GAP), TILE, TILE)))
        return out

    def hit(self, mx, my):
        for key, (l, b, w, h) in self.items():
            if l <= mx < l + w and b <= my < b + h:
                return key
        return None

    def click(self, mx, my):
        key = self.hit(mx, my)
        if isinstance(key, tuple):
            key = key[1]
        return key

    def draw(self):
        if not self.open:
            return
        l, b, w, h = self.rect()
        top = b + h
        gfx.fill(l, b, w, h, (31, 31, 31, 250))
        gfx.fill(l, b, RAIL_W, h, (43, 43, 43, 250))
        gfx.symbol('\uE700', l + RAIL_W / 2, top - 24, 16, WHITE)
        for i, g in enumerate(('\uE7E8', '\uE713', '\uE91B', '\uE8A5', '\uE77B')):
            gfx.symbol(g, l + RAIL_W / 2, b + 24 + i * 48, 16, WHITE)

        y = top - 12
        for key, name, icon in LIST:
            ih = 36
            if name is None:
                gfx.text(key, l + RAIL_W + 14, y - ih / 2, 14, WHITE)
            else:
                if self.hover == key:
                    gfx.fill(l + RAIL_W, y - ih, LIST_W, ih, (255, 255, 255, 25))
                gfx.fill(l + RAIL_W + 10, y - ih + 2, 32, 32, ACCENT)
                gfx.icon(icon, 24, l + RAIL_W + 14, y - ih + 6)
                gfx.text(name, l + RAIL_W + 54, y - ih / 2, 14, WHITE)
            y -= ih

        tx = l + RAIL_W + LIST_W + 8
        gfx.text('생산성', tx, top - 26, 12, WHITE)
        for (key, (bl, bb, bw, bh)), (_, name, icon) in zip(self.items()[-len(TILES):], TILES):
            gfx.fill(bl, bb, bw, bh, (0, 99, 177) if self.hover != ('tile', key) else (26, 120, 196))
            if self.hover == ('tile', key):
                gfx.frame(bl, bb, bw, bh, (255, 255, 255, 120), 2)
            gfx.icon(icon, 32, bl + (bw - 32) / 2, bb + bh / 2 - 6)
            gfx.text(name, bl + 8, bb + 14, 12, WHITE)
