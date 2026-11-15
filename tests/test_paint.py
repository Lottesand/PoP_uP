import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, game_framework, play_mode as pm, screenshot
import paint
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []


def check(n, c):
    ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)


def frame():
    clear_canvas(); pm.render()


def px(app, cx, cy):
    i = (cy * paint.CW + cx) * 4
    return tuple(app.pixels[i:i + 3])


def screen(app, cx, cy):
    l, b, w, h = app.canvas
    return l + cx * paint.CELL + 2, b + h - 1 - cy * paint.CELL - 2


def click_ui(app, label):
    for (l, b, w, h), act in app.ui:
        if act.__defaults__ and label in act.__defaults__:
            pm.mouse_down(l + 3, b + 3); pm.mouse_up(l + 3, b + 3); frame()
            return
    raise KeyError(label)


pm.open_app('paint'); win = pm.wm.active
win.x, win.y = 100, 120
frame()
app = win.app
# 연필로 가로줄 끌어 그리기
x0, y0 = screen(app, 10, 60)
x1, y1 = screen(app, 90, 60)
pm.mouse_down(x0, y0)
for k in range(1, 9):
    pm.mouse_move(x0 + (x1 - x0) * k / 8, y0)
pm.mouse_up(x1, y1); frame()
check('drag with pencil draws a line', all(px(app, x, 60) == (0, 0, 0) for x in range(10, 91)))
check('pencil is 1 cell thick', px(app, 50, 59) == (255, 255, 255) and px(app, 50, 61) == (255, 255, 255))
# 색 바꾸고 브러시
click_ui(app, (237, 28, 36))
click_ui(app, 'brush')
x, y = screen(app, 40, 30)
pm.mouse_down(x, y); pm.mouse_up(x, y); frame()
check('brush paints 3x3 in the picked color', all(px(app, 40 + dx, 30 + dy) == (237, 28, 36)
                                                   for dx in (-1, 0, 1) for dy in (-1, 0, 1)))
# 지우개
click_ui(app, 'eraser')
x, y = screen(app, 50, 60)
pm.mouse_down(x, y); pm.mouse_up(x, y); frame()
check('eraser clears 5x5', px(app, 48, 60) == (255, 255, 255) and px(app, 52, 60) == (255, 255, 255) and px(app, 46, 60) == (0, 0, 0))
# 채우기: 닫힌 네모 안만 채운다
click_ui(app, (0, 0, 0))
click_ui(app, 'pencil')
for a, b2 in (((120, 20), (160, 20)), ((160, 20), (160, 50)), ((160, 50), (120, 50)), ((120, 50), (120, 20))):
    app.stroke(a, b2)
click_ui(app, (34, 177, 76))
click_ui(app, 'fill')
x, y = screen(app, 140, 35)
pm.mouse_down(x, y); pm.mouse_up(x, y); frame()
check('fill paints inside the closed box only', px(app, 140, 35) == (34, 177, 76) and px(app, 170, 35) == (255, 255, 255))
# 그린 선이 창 안 발판이 된다
click_ui(app, 'pencil')
app.stroke((60, 100), (120, 100))
P = pm.player
cl, cb, cw, ch = app.canvas
P.x, P.y = cl + 80 * paint.CELL, cb + ch - 70 * paint.CELL
P.enter(win, (P.x + 24, P.y + 32))
for _ in range(90):
    pm.update()
line_top = cb + ch - 100 * paint.CELL
check('pointer lands on the drawn line', P.inside and P.ground is not None and abs(P.y - line_top) < 1)
frame()
screenshot.shot(os.path.join(OUT, 'paint.png'))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
