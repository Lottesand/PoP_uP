import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, fs, shell, play_mode as pm
import desktop as dk
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
t = [100.0]
pm.get_time = lambda: t[0]
ok = []


def check(name, cond):
    ok.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name)


def frame():
    clear_canvas(); pm.render()          # 탐색기는 그릴 때 클릭 영역을 계산한다


def click(x, y, dt=1.0):
    t[0] += dt; pm.mouse_down(x, y); pm.mouse_up(x, y); frame()


def dclick(x, y):
    click(x, y); click(x, y, 0.15)


def drag(x0, y0, x1, y1):
    t[0] += 1; pm.mouse_down(x0, y0)
    for k in range(1, 6):
        pm.mouse_move(x0 + (x1 - x0) * k / 5, y0 + (y1 - y0) * k / 5)
    pm.mouse_up(x1, y1); frame()


def center_of(node):
    l, b, w, h = dk.cell_rect(*node.pos)
    return l + w // 2, b + h - 30


def item_center(app, node):
    for n, (l, b, w, h) in app.items:
        if n is node:
            return l + w // 2, b + h - 20
    raise KeyError(node.name)


def menu_pick(*labels):
    for label in labels:
        menu = shell.menu
        while menu.sub is not None and any(i and i.label.startswith(label) for i in menu.sub.items):
            menu = menu.sub
        for i, item, b, h in menu.rows():
            if item and item.label.startswith(label):
                pm.mouse_move(menu.l + 40, b + h // 2)
                if not item.sub:
                    t[0] += 1; pm.mouse_down(menu.l + 40, b + h // 2); pm.mouse_up(menu.l + 40, b + h // 2)
                break
    frame()


frame()
D = pm.desktop
docs_link = next(n for n in D.folder.children if n.name == '문서')
trash_link = next(n for n in D.folder.children if n.name == '휴지통')

# 1. 바탕화면 '문서' 더블클릭 → 탐색기
dclick(*center_of(docs_link))
win = pm.wm.active; ex = win.app
check('desktop link opens explorer at 문서', ex.node is fs.DOCUMENTS)
# 2. 하위 폴더 더블클릭으로 들어가기
hw = next(n for n in fs.DOCUMENTS.children if n.name == '과제')
dclick(*item_center(ex, hw))
check('double click enters subfolder', ex.node is hw and win.app.title == '과제')
# 3. 뒤로 / 위로
bl, bb, bw, bh = ex.buttons['back']; click(bl + 10, bb + 10)
check('back button', ex.node is fs.DOCUMENTS)
bl, bb, bw, bh = ex.buttons['up']; click(bl + 10, bb + 10)
check('up button', ex.node is fs.ROOT)
bl, bb, bw, bh = ex.buttons['back']; click(bl + 10, bb + 10)
# 4. 오른쪽 클릭 → 새로 만들기 → 폴더
cl, cb, cw, ch = ex.content
pm.right_down(cl + cw - 40, cb + 40); frame()
check('explorer context menu opens', shell.menu is not None)
menu_pick('새로 만들기', '폴더')
new = ex.selected
check('new folder created', new is not None and new.name == '새 폴더' and new.parent is fs.DOCUMENTS and shell.menu is None)
# 5. 빈 폴더 들어가기 → 비어 있음
dclick(*item_center(ex, new))
check('enter empty folder', ex.node is new and not new.children and ex.items == [])
bl, bb, bw, bh = ex.buttons['back']; click(bl + 10, bb + 10)
# 6. 두 번째 새 폴더 이름
pm.right_down(cl + cw - 40, cb + 40); frame(); menu_pick('새로 만들기', '폴더')
check('second new folder numbered', ex.selected.name == '새 폴더 (2)')
# 7. Delete 키 → 휴지통
n2 = ex.selected
pm.key_down(pm.SDLK_DELETE); frame()
check('delete key sends to trash', n2.parent is fs.TRASH)
# 8. 잠긴 파일 열기 → 오류 창
usb = next(n for n in fs.DOCUMENTS.children if n.name == 'USB 열쇠')
dclick(*item_center(ex, usb))
check('locked item shows dialog', pm.wm.active.app.group == 'dialog')
dlg = pm.wm.active.app
bl, bb, bw, bh = dlg.button; click(bl + 10, bb + 10)
check('dialog 확인 closes', pm.wm.find(dlg.key) is None)
pm.wm.close(win); frame()

# 9. 바탕화면 오른쪽 클릭 → 새 폴더 (빈 칸 위치에)
pm.right_down(900, 600); frame()
menu_pick('새로 만들기', '폴더')
dnew = next((n for n in D.folder.children if n.name == '새 폴더'), None)
check('desktop new folder at clicked cell', dnew is not None and dnew.pos == dk.cell_at(900, 600))
# 10. 바탕화면 아이콘 끌어서 다른 칸으로
note = next(n for n in D.folder.children if n.name == '탈출 계획.txt')
old = note.pos
drag(*center_of(note), 700, 500)
check('drag icon to empty cell', note.pos == dk.cell_at(700, 500) and note.pos != old)
# 11. 이미 아이콘이 있는 칸에 놓으면 가까운 빈 칸
drag(*center_of(note), *center_of(next(n for n in D.folder.children if n.name == 'Chrome')))
check('drop on non-folder icon finds free cell', note.parent is D.folder and
      note.pos not in {n.pos for n in D.folder.children if n is not note})
# 12. 폴더 아이콘 위에 놓으면 그 폴더 안으로
drag(*center_of(note), *center_of(dnew))
check('drop onto folder moves inside', note.parent is dnew)
# 13. 휴지통 위에 놓으면 삭제, 휴지통 아이콘이 가득 참
drag(*center_of(dnew), *center_of(trash_link))
check('drop onto recycle bin deletes', dnew.parent is fs.TRASH and fs.TRASH.icon == 'recycle_bin_full')
# 14. 휴지통에서 복원
dclick(*center_of(trash_link))
tex = pm.wm.active.app
pm.right_down(*item_center(tex, dnew)); frame(); menu_pick('복원')
check('restore from trash', dnew.parent is D.folder and dnew.pos is not None)
pm.wm.close(pm.wm.active); frame()
# 15. 탐색기 창 안으로 끌어 놓기
dclick(*center_of(docs_link))
ex = pm.wm.active.app
cl, cb, cw, ch = ex.content
drag(*center_of(dnew), cl + cw // 2, cb + 60)
check('drop onto explorer window moves into its folder', dnew.parent is fs.DOCUMENTS)
# 16. 작업 표시줄: 탐색기 창 두 개가 단추 하나
pm.open_app('this_pc'); frame()
check('explorer windows share one taskbar button', pm.taskbar.apps(pm.wm).count('explorer') == 1 and
      len([g for g in pm.taskbar.apps(pm.wm) if g == 'explorer']) == 1 and len(pm.taskbar.apps(pm.wm)) == 2)
# 17. 주소 표시줄 경로 클릭
pm.open_app('documents'); frame()
ex = pm.wm.active.app
node, x0, x1, b, tt = ex.crumbs[0]
click((x0 + x1) // 2, (b + tt) // 2)
check('breadcrumb click navigates', ex.node is fs.ROOT)
# 18. 내 PC에서 E: 드라이브 → 접근 거부
e = next(n for n in fs.ROOT.children if n.name.startswith('USB'))
dclick(*item_center(ex, e))
check('E: drive denied', pm.wm.active.app.group == 'dialog')
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
