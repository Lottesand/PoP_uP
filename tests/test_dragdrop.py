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
# ---------------------------------------------------------------- 그림 파일을 포인터에게 끌어다 놓으면 장착
P = pm.player
for w in list(pm.wm.windows):
    pm.wm.close(w)
backup = level.find(fs.DOCUMENTS, '사진 백업')
shell.open_folder(backup); bw = pm.wm.active
bw.x, bw.y, bw.w, bw.h = 700, 300, 800, 460
P.x, P.y = 300, TASKBAR_H
for _ in range(20):
    pm.update()
frame()
spear, x, y = item_center(bw, '불꽃 창.png')
px, py = P.center()
label = drag(x, y, px, py, 'dnd_equip.png')
check('dragging a picture over the pointer says it will equip', label == '+ 포인터에게 무기로 장착')
check('dropping a picture on the pointer equips it as a weapon', P.weapon is spear.picture)
check('the picture file stays where it was', spear.parent is backup)
# 바탕 화면의 그림 아이콘도
hammer = next(n for n in backup.children if n.name == '얼음 망치.png')
fs.move(hammer, fs.DESKTOP_FOLDER); hammer.pos = None
frame()
hx, hy = desk_center(hammer)
pm.desktop.last_click = (None, -1.0)
drag(hx, hy, px, py)
check('desktop picture icon dropped on the pointer swaps the weapon', P.weapon is hammer.picture
      and hammer.parent is fs.DESKTOP_FOLDER)
# 그림이 아닌 파일은 장착되지 않고 그냥 바탕 화면으로
note = next(n for n in fs.DESKTOP_FOLDER.children if n.name == '탈출 계획.txt')
nx, ny = desk_center(note)
pm.desktop.last_click = (None, -1.0)
label = drag(nx, ny, px, py)
check('non-picture files are not equipped', P.weapon is hammer.picture and label != '+ 포인터에게 무기로 장착')
# ---------------------------------------------------------------- 바탕 화면 파란 선택 상자
for w in list(pm.wm.windows):
    pm.wm.close(w)
P.drop_weapon()
for _ in range(10):
    pm.update()
frame()
D = pm.desktop
icons = [n for n in D.items() if n.pos[0] == 0][:4]          # 첫 줄 위에서 4개
l0, b0, w0, h0 = desktop.cell_rect(*icons[0].pos)
l3, b3, w3, h3 = desktop.cell_rect(*icons[3].pos)
pm.mouse_down(l0 + w0 + 40, b0 + h0 - 10)
for k in range(1, 9):
    pm.mouse_move(l0 + w0 + 40 - (w0) * k / 8, b0 + h0 - 10 - (b0 + h0 - b3 - 20) * k / 8)
frame()
screenshot.shot(os.path.join(OUT, 'band.png'))
check('dragging on empty desktop draws a selection box', D.band_rect() is not None)
check('the box selects every icon it touches', set(icons) <= set(D.picked))
pm.mouse_up(*D.mouse)
check('releasing ends the box but keeps the selection', D.band is None and set(icons) <= set(D.picked))
# 선택한 아이콘을 하나 끌면 다 같이 움직인다
before = {n: n.pos for n in icons}
lx, ly = desk_center(icons[0])
D.last_click = (None, -1.0)
drag(lx, ly, lx + desktop.ICON_CELL_W * 3, ly)
check('dragging one of the selected icons moves the whole group 3 columns', all(n.pos == (before[n][0] + 3, before[n][1])
                                                                            for n in icons))
# 선택 상자는 누르고 있는 동안 포인터의 발판
P.x, P.y, P.vy = 900, 420, 0
for _ in range(5):
    pm.update()
pm.mouse_down(860, 300)
pm.mouse_move(1000, 200)
for _ in range(60):
    pm.mouse_move(1000, 200); pm.update()
check('the pointer lands on the selection box while it is held', P.ground == 'band' and abs(P.y - 300) < 1)
for k in range(1, 11):
    pm.mouse_move(1000, 200)
    D.band = (860, 300 + 10 * k, 1000, 200)
    pm.update()
check('raising the box lifts the pointer standing on it', abs(P.y - 400) < 1 and P.ground == 'band')
frame()
screenshot.shot(os.path.join(OUT, 'band_platform.png'))
pm.mouse_up(1000, 200)
for _ in range(90):
    pm.update()
check('letting go of the mouse drops the pointer', P.ground == 'taskbar')
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
