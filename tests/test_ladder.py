import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, game_framework, play_mode as pm
from config import *
open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []
def check(n, c): ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)
def step(sec):
    for _ in range(max(1, int(sec * 60))):
        pm.update(); clear_canvas(); pm.render()
P = pm.player
pm.monsters.clear()
pm.open_app('documents'); win = pm.wm.active
win.x, win.y, win.w, win.h = 300, 60, 900, 700
step(0.1)
sl, sb, sw, sh = win.app.ladders()[0]
# OFF: 창 뒤 스크롤바를 W로 타고 올라가기
P.x, P.y = sl - 10, TASKBAR_H; step(0.3)
pm.key_down(pm.SDLK_w); step(4.0)
check('OFF: climbs window scrollbar to its top', P.ladder is not None and abs(P.y - (sb + sh - 10)) < 1)
pm.player.key('up', False); pm.key_down(pm.SDLK_SPACE); step(1.0); pm.player.key('jump', False); step(0.5)
check('jump off ladder top lands on title bar', P.ground is win)
# ON: 창 안 바닥에서 스크롤바 타고 위로 → 닫기 버튼에 닿음
P.x = sl - 30; P.enter(win); step(1.5)
check('inside window on floor', P.mode == 'on' and P.ground == 'floor')
P.x = sl - 20; step(0.1)
pm.key_down(pm.SDLK_w); step(3.0); pm.player.key('up', False)
name, bl, bb, bw, bh = win.caption_buttons()[0]
pm.mouse_down(bl + 10, bb + 10)
check('climbed scrollbar inside can reach close button', P.held == 'close')
# S로 내려가서 바닥에 닿으면 놓음
pm.key_down(pm.SDLK_s); step(4.0); pm.player.key('down', False); step(0.2)
check('climbing down releases at bottom', P.ladder is None and P.ground == 'floor')
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
