# 구간 1 (파일 관리자)에 등장하는 몬스터 배치
import fs
from monsters import KINDS


def find(parent, *names):
    node = parent
    for name in names:
        node = next(c for c in node.children if c.name == name)
    return node


# (폴더, [(종류, 내용 영역 왼쪽에서의 x)])
def encounters():
    docs = fs.DOCUMENTS
    return [
        (docs, [('bug', 260), ('bug', 470)]),
        (find(docs, '과제'), [('caret', 320), ('bug', 140)]),
        (find(docs, '사진 백업'), [('bug', 120), ('bug', 300), ('bug', 480)]),
        (find(docs, '숨겨진 폴더'), [('bomber', 400), ('caret', 180)]),
        (find(docs, '숨겨진 폴더', '설정'), [('caret', 460), ('bug', 220), ('bomber', 560)]),
    ]


def spawn():
    return [KINDS[kind](folder, rx) for folder, specs in encounters() for kind, rx in specs]


def window_for(folder, wm):
    """그 폴더를 보여 주는 가장 앞의 창"""
    for win in reversed(wm.visible()):
        if getattr(win.app, 'node', None) is folder and win.app.content[2] > 0:
            return win
    return None
