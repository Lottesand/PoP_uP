import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, game_framework, play_mode as pm, screenshot
import player as pl
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []


def check(n, c):
    ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)


def step(sec):
    for _ in range(max(1, int(sec * 60))):
        pm.update()


P = pm.player
step(0.3)
# ---------------------------------------------------------------- 2단 점프
P.key('jump', True)
top = P.y
for _ in range(20):
    pm.update(); top = max(top, P.y)
P.key('jump', False); P.key('jump', True)          # 공중에서 한 번 더
for _ in range(10):
    pm.update(); top = max(top, P.y)
P.key('jump', False); P.key('jump', True)          # 세 번째는 안 된다
vy = P.vy
check('no third jump in the air', P.ground is None and P.air_jumps == 0 and P.vy == vy)
P.key('jump', False)
for _ in range(50):
    pm.update(); top = max(top, P.y)
check('double jump goes higher than one jump (150px)', top - TASKBAR_H > 200)
step(1.5)
check('landing refills the air jump', P.ground == 'taskbar' and P.air_jumps == 1)

# ---------------------------------------------------------------- 대쉬 (Shift ON, 빈손 우클릭)
pm.right_down(P.x + 500, P.y + 30)
check('no dash in Shift OFF (right click is the OS menu)', P.dash_t == 0)
pm.shell.close_menu()
pm.key_down(pm.SDLK_LSHIFT)
step(0.4)
x0, y0 = P.x, P.y
pm.right_down(P.x + 500, P.y + 32)                  # 오른쪽
check('right click with empty hand dashes', P.dash_t > 0 and P.dash_dir == (1.0, 0.0))
check('invincible while dashing', not P.hurt(10, P.x + 100) and P.hp == pl.MAX_HP)
step(0.2)
check('dash covers about 150px to the right', 130 <= P.x - x0 <= 200 and abs(P.y - y0) < 1)
pm.right_down(P.x + 500, P.y + 32)
check('dash cooldown', P.dash_t == 0)
step(0.5)
# 8방향으로 맞춘다: 오른쪽 위 비스듬히 조준 → 정확히 45도
cx, cy = P.center()
pm.right_down(cx + 100, cy + 80)
d = P.dash_dir
check('aim snaps to 8 directions (45 deg)', abs(d[0] - d[1]) < 1e-6 and d[0] > 0.7)
step(0.6)
# 공중 대쉬는 한 번만
P.key('jump', True); step(0.1)
cx, cy = P.center()
first = P.dash(cx - 300, cy)
step(0.16)
P.dash_cd = 0                                       # 쿨타임은 지났다고 치고
second = P.dash(cx - 300, cy)
check('one dash per airtime', first and P.ground is None and second is False)
P.key('jump', False)
step(1.5)
check('landing refills the air dash', P.air_dash)
# 버튼을 들고 있으면 우클릭은 던지기
P.held = 'min'
pm.right_down(P.x + 300, P.y + 30)
check('holding a button: right click throws, not dash', P.held is None and len(pm.thrown) == 1 and P.dash_t == 0)
step(0.5)
# 창 안에서 대쉬해도 벽을 못 넘는다
pm.open_app('documents'); win = pm.wm.active
win.x, win.y, win.w, win.h = 300, 200, 700, 500
step(0.1)
P.enter(win)
cl, cb, cw, chh = win.client_rect()
P.x = cl + 40; step(0.6)
P.dash_cd = 0
P.dash(cl - 500, P.center()[1])
step(0.3)
check('dash inside a window stops at its wall', abs(P.x - cl) < 1)
clear_canvas(); pm.render()
screenshot.shot(os.path.join(OUT, 'moves.png'))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
