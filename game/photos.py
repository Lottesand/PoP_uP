# 사진 앱: 그림판에서 저장한 그림(.png)을 연다. 하얀 칸은 투명이라 어두운 배경이 비쳐 보인다.
# 공격 모드로 이 창에 들어와서 그림을 좌클릭하면 그 그림을 무기로 든다 (drawing.py).
import gfx
import apps
from apps import App
from config import *

BG, BAR, BAR_TEXT = (24, 24, 24), (43, 43, 43), (230, 230, 230)
TOOLBAR_H, INFO_H = 44, 92
GL_ZOOM, GL_ROTATE, GL_DELETE, GL_EDIT, GL_SHARE, GL_MORE = (
    '\uE71E', '\uE7AD', '\uE74D', '\uE70F', '\uE72D', '\uE712')


class Photos(App):
    group = 'photos'
    icon = 'image_file'
    size = (900, 660)
    min_size = (480, 420)

    def __init__(self, node):
        self.node = None                # 몬스터가 사는 폴더가 아니다 (탐색기 노드와 겹치지 않게)
        self.file = node
        self.key = 'photos:%d' % node.id
        self.picture_rect = (0, 0, 0, 0)

    @property
    def drawing(self):
        return self.file.picture

    @property
    def title(self):
        return self.file.name + ' - 사진'

    def touches_picture(self, mx, my):
        l, b, w, h = self.picture_rect
        return l - 8 <= mx < l + w + 8 and b - 8 <= my < b + h + 8

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, BG)
        # 위 도구 모음
        gfx.fill(l, top - TOOLBAR_H, w, TOOLBAR_H, BAR)
        gfx.text(self.file.name, l + 16, top - TOOLBAR_H / 2, 13, BAR_TEXT)
        x = l + w - 28
        for g in (GL_MORE, GL_SHARE, GL_EDIT, GL_DELETE, GL_ROTATE, GL_ZOOM):
            gfx.symbol(g, x, top - TOOLBAR_H / 2, 14, BAR_TEXT)
            x -= 46
        # 그림 (칸 하나를 최대 4px로)
        area = (l + 30, b + INFO_H + 20, w - 60, h - TOOLBAR_H - INFO_H - 40)
        self.picture_rect = self.drawing.draw_fit(*area, max_px=4)
        # 아래 정보: 무기 능력
        gfx.fill(l, b, w, INFO_H, (32, 32, 32))
        gfx.line(l, b + INFO_H, l + w, b + INFO_H, (60, 60, 60))
        gfx.fill(l + 16, b + INFO_H - 30, 10, 10, self.drawing.color)
        gfx.text('무기로 쓰면', l + 34, b + INFO_H - 25, 12, (160, 160, 160))
        for i, line in enumerate(self.drawing.info()):
            gfx.text(line, l + 120, b + INFO_H - 25 - i * 22, 13, BAR_TEXT)


def open_picture(wm, node):
    return wm.open(Photos(node))
