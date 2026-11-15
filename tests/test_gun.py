import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, fs, game_framework, play_mode as pm, screenshot
import debuggun, drawing
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []


def check(n, c):
    ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)


def step(sec):
    for _ in range(max(1, int(sec * 60))):
        pm.update(); clear_canvas(); pm.render()


P = pm.player
# ---------------------------------------------------------------- VS Code에서 [실행 및 디버그] 아이콘 뜯기
pm.open_app('vscode'); vwin = pm.wm.active
vwin.x, vwin.y = 200, 200
step(0.1)
vs = vwin.app
check('VS Code shows the run & debug icon', not vs.debug_taken and vs.debug_rect[2] > 0)
screenshot.shot(os.path.join(OUT, 'gun_vscode.png'))
pm.key_down(pm.SDLK_LSHIFT)
P.enter(vwin, (vwin.x + 300, vwin.y + 200)); P.invincible = 99
step(1.0)
dl, db, dw, dh = vs.debug_rect
pm.mouse_down(dl + dw / 2, db + dh / 2); pm.mouse_up(dl + dw / 2, db + dh / 2)
check('clicking the icon inside VS Code takes the debug gun', P.has('gun') and vs.debug_taken)
step(0.2)
check('icon slot is empty while held', vs.touches_debug(dl + dw / 2, db + dh / 2) is False)
screenshot.shot(os.path.join(OUT, 'gun_take.png'))

# ---------------------------------------------------------------- 폴더 창에서 중단점 쏘기
pm.wm.close(vwin); step(0.1)
pm.open_app('documents'); win = pm.wm.active
win.x, win.y, win.w, win.h = 300, 120, 1000, 600
step(0.2)
P.enter(win); P.invincible = 99
step(1.0)
bugs = [m for m in pm.monsters if m.folder is fs.DOCUMENTS]
for m in bugs:
    m.stun, m.vx, m.vy = 0, 0, 0
cl, cb, cw, ch = win.app.content
P.x = cl + 60
step(0.2)
target, other = bugs[0], bugs[1:]
hx, hy = P.hand()
target.rx, target.ry = 520, hy - cb - target.h / 2
for i, m in enumerate(other):
    m.rx, m.ry = 300 + i * 60, 380
    m.stun = 99
target.stun = 0
P.invincible = 0
tx, ty = target.center()
pm.mouse_down(tx, ty); pm.mouse_up(tx, ty)
check('left click fires a breakpoint', any(t.name == 'breakpoint' for t in pm.thrown) and P.shot_cd > 0)
pm.mouse_down(tx, ty)
check('fire rate: 0.4 s', sum(1 for t in pm.thrown if t.name == 'breakpoint') == 1)
step(0.1)
screenshot.shot(os.path.join(OUT, 'gun_shoot.png'))
step(0.3)
check('breakpoint hits for 6 and freezes the bug', target.hp == target.max_hp - 6 and target.stun > 1.0
      and target.slow > 0)
check('shot is gone after the first hit', not any(t.name == 'breakpoint' for t in pm.thrown))

# ---------------------------------------------------------------- F5 Run 대쉬
step(0.5)
for m in bugs:
    m.stun, m.vx, m.vy = 99, 0, 0
    m.hp = m.max_hp
P.x = cl + 40
step(0.4)
line = bugs[:3]
for i, m in enumerate(line):
    m.rx, m.ry = 140 + i * 90, P.y - cb + 10
x0 = P.x
pm.right_down(P.x + 600, P.y + 32)
check('right click = F5 Run dash', P.dash_t > 0 and P.dash_power == debuggun.F5_DAMAGE and P.f5_cd > 0)
step(0.5)
check('F5 dash goes about 400px', 330 <= P.x - x0 <= 460)
check('F5 dash pierces every bug on the way for 20', all(m.hp == m.max_hp - 20 for m in line))
pm.right_down(P.x + 600, P.y + 32)
check('F5 cooldown 4 s (and no plain dash while holding the gun)', P.dash_t == 0)

# ---------------------------------------------------------------- E 버리기 · 무기 바꾸기
pm.key_down(pm.SDLK_e)
check('E drops the gun and the icon goes back to VS Code', P.weapon is None and not vs.debug_taken)
P.take_weapon(debuggun.DebugGun(vs)); vs.debug_taken = True
pic = drawing.Drawing([[(237, 28, 36)] * 20 for _ in range(6)])
P.take_weapon(pic)
check('one special weapon at a time: taking a drawing returns the icon', P.weapon is pic and not vs.debug_taken)

# ---------------------------------------------------------------- 창 밖에서 쏘면 테두리에 금
P.drop_weapon()
P.take_weapon(debuggun.DebugGun(vs)); vs.debug_taken = True
P.force_out()
win.x, win.y = 700, 200
P.x, P.y = 100, TASKBAR_H
step(0.5)
pm.key_down(pm.SDLK_LSHIFT)                  # 창 밖 공격 모드
step(0.4)
l, b, w, h = win.rect()
for i in range(4):
    P.shot_cd = 0
    pm.mouse_down(l + 10, b + 100)
    step(0.6)
check('shots crack a window from outside, but only up to 2', P.mode == 'on' and len(win.cracks) == 2 and not P.inside)
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
