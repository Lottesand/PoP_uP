import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, fs, shell, game_framework, play_mode as pm, level, screenshot, desktop
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []


def check(n, c):
    ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)


def frame():
    clear_canvas(); pm.render()


def drag(x0, y0, x1, y1, shot=None):
    pm.mouse_down(x0, y0)
    for k in range(1, 11):
        pm.mouse_move(x0 + (x1 - x0) * k / 10, y0 + (y1 - y0) * k / 10)
    frame()
    if shot:
        screenshot.shot(os.path.join(OUT, shot))
    label = shell.drop_label(shell.drag[0], x1, y1) if shell.drag else None
    pm.mouse_up(x1, y1)
    frame()
    return label


def item_center(win, name):
    node, (l, b, w, h) = next(x for x in win.app.items if x[0].name == name)
    return node, l + w / 2, b + h / 2


def desk_center(node):
    l, b, w, h = desktop.cell_rect(*node.pos)
    return l + w / 2, b + h / 2


pm.open_app('documents'); win = pm.wm.active
win.x, win.y, win.w, win.h = 700, 300, 900, 520
frame()
# ---------------------------------------------------------------- 폴더 → 바탕 화면
node, x, y = item_center(win, 'readme.txt')
label = drag(x, y, 400, 900, 'dnd_to_desktop.png')
check('dragging shows "→ 바탕 화면(으)로 이동"', label == '→ 바탕 화면(으)로 이동')
check('folder file dropped on the desktop moves there', node.parent is fs.DESKTOP_FOLDER)
check('it lands in the cell under the cursor', node.pos == desktop.cell_at(400, 900))
check('the folder window no longer lists it', all(n is not node for n, r in win.app.items))
# ---------------------------------------------------------------- 바탕 화면 → 폴더 창
x, y = desk_center(node)
drag(x, y, win.x + 600, win.y + 150)
check('desktop file dropped into a folder window moves into that folder', node.parent is fs.DOCUMENTS)
# 폴더 항목 위에 놓으면 그 폴더 안으로
node.parent.remove(node); fs.DESKTOP_FOLDER.add(node); node.pos = None   # 빈 칸에 자리 잡는다
frame()
x, y = desk_center(node)
hw, fx, fy = item_center(win, '과제')
pm.desktop.last_click = (None, -1.0)        # 방금 같은 아이콘을 눌렀던 게 더블클릭으로 잡히지 않게
label = drag(x, y, fx, fy)
check('dropped on a folder item inside the window goes into that folder', node.parent is hw)
# ---------------------------------------------------------------- 폴더 창 → 다른 폴더 창
shell.open_folder(hw); win2 = pm.wm.active
win2.x, win2.y, win2.w, win2.h = 60, 120, 600, 400
frame()
n2, x, y = item_center(win2, 'readme.txt')
drag(x, y, win.x + 700, win.y + 120)
check('folder window → another folder window', n2.parent is fs.DOCUMENTS)
# ---------------------------------------------------------------- 폴더 항목 → 바탕 화면 폴더 아이콘(휴지통)
trash_icon = next(n for n in fs.DESKTOP_FOLDER.children if n.name == '휴지통')
n3, x, y = item_center(win2, '제출 목록.txt')
tx, ty = desk_center(trash_icon)
pm.wm.focus(win2); frame()
label = drag(x, y, tx, ty)
check('onto the desktop recycle bin icon → deleted', label == '→ 휴지통(으)로 이동' and n3.parent is fs.TRASH)
# ---------------------------------------------------------------- 같은 폴더 안에서는 그대로, 잠긴 건 못 옮김
n4, x, y = item_center(win, '숨겨진 폴더')
drag(x, y, x + 120, y - 60)
check('dropping inside its own folder keeps it there', n4.parent is fs.DOCUMENTS)
usb, x, y = item_center(win, 'USB 열쇠')
drag(x, y, 300, 700)
check('locked items cannot be dragged out', usb.parent is fs.DOCUMENTS)
screenshot.shot(os.path.join(OUT, 'dnd_after.png'))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
