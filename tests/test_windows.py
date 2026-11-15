import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice
import gfx, play_mode as pm
from config import *
open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
import pico2d.pico2d as p2
t = [100.0]
p2.get_time = lambda: t[0]
pm.get_time = lambda: t[0]
def click(x, y, dt=1.0):
    t[0] += dt; pm.mouse_down(x, y); pm.mouse_up(x, y)
ok = []
def check(name, cond): ok.append(cond); print(('PASS ' if cond else 'FAIL ') + name)
# 바탕화면 아이콘 더블클릭으로 열기 (내 PC = 0번 칸)
import desktop as dk; pm.desktop.items(); l, b, w, h = dk.cell_rect(*pm.desktop.folder.children[0].pos)
click(l + 30, b + h - 30); click(l + 30, b + h - 30, 0.2)
win = pm.wm.active; check('double click opens', win is not None and pm.wm.active is win)
# 제목 표시줄 끌기
x0, y0 = win.x, win.y
tx, ty = win.x + 200, win.y + win.h - 15
t[0] += 1; pm.mouse_down(tx, ty); pm.mouse_move(tx + 100, ty - 50); pm.mouse_up(tx + 100, ty - 50)
check('drag moves', (win.x, win.y) == (x0 + 100, y0 - 50))
# 오른쪽 아래 크기 조절
w0, h0, top0 = win.w, win.h, win.y + win.h
t[0] += 1; pm.mouse_down(win.x + win.w + 2, win.y - 2); pm.mouse_move(win.x + win.w + 82, win.y - 42); pm.mouse_up(0, 0)
check('resize br', (win.w, win.h, win.y + win.h) == (w0 + 80, h0 + 40, top0))
# 제목 더블클릭 최대화 → 다시 복원
click(win.x + 300, win.y + win.h - 15); click(win.x + 300, win.y + win.h - 15, 0.2)
check('title dblclick max', win.state == 'max')
click(*[v for v in (W // 2, H - 15)]); click(W // 2, H - 15, 0.2)
check('title dblclick restore', win.state == 'normal')
# 최소화 버튼 → 작업 표시줄 단추로 복원
name, bl, bb, bw, bh = win.caption_buttons()[2]
click(bl + 10, bb + 10)
check('minimize', win.state == 'min' and pm.wm.active is not win)
zx = [x for n, x, w in pm.taskbar.zones(pm.wm) if n == ('app', 'explorer')][0]
click(zx + 10, 20)
check('taskbar restore', win.state == 'normal' and pm.wm.active is win)
click(zx + 10, 20)
check('taskbar minimize active', win.state == 'min')
# 시작 메뉴로 메모장 열기
click(10, 10)
check('start opens', pm.start.open)
key, (il, ib, iw, ih) = [it for it in pm.start.items() if it[0] == 'notepad'][0]
click(il + 20, ib + 10)
check('start launches notepad', pm.wm.active.app.group == 'notepad' and not pm.start.open)
# 닫기 버튼
np_ = pm.wm.active; name, bl, bb, bw, bh = np_.caption_buttons()[0]
click(bl + 10, bb + 10)
check('close', all(w.app.group != 'notepad' for w in pm.wm.windows))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
