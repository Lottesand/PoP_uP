import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, fs, shell, toast, apps, game_framework, play_mode as pm, level, screenshot
from config import *
open_canvas(W, H); hide_lattice(); gfx.init(); pm.init()
game_framework.frame_time = 1 / 60
ok = []
def check(n, c): ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)
def step(sec):
    for _ in range(max(1, int(sec * 60))):
        pm.update(); clear_canvas(); pm.render()
P = pm.player
step(0.2)
dlg = pm.wm.active
check('starts with warning dialog near the pointer', dlg.app.kind == 'warning' and pm.section.state == 'warning')
screenshot.shot(os.path.join(OUT, '9_start.png'))
# 걸어가서 겹친 뒤 Shift → 창 안 → [확인] 위로 점프
dl, db, dw, dh = dlg.rect()
pm.key_down(pm.SDLK_d)
for _ in range(200):
    pm.update()
    if P.x + 48 >= dl - 30: break
pm.player.key('right', False)
pm.key_down(pm.SDLK_LSHIFT)
step(0.5)
check('attack mode: dialog is a wall', P.x + 48 <= dl + 1)
for i in range(3):
    P.poke_cd = 0
    pm.poke(dl + 6, P.y + 40)
step(0.6)
check('broke into the warning dialog', P.mode == 'on' and P.win is dlg)
bl, bb, bw, bh = dlg.app.button
P.x = bl + 10; step(0.1)
pm.key_down(pm.SDLK_SPACE); step(0.8); pm.player.key('jump', False); step(0.3)
check('stepping on [확인] closes dialog and starts exploring', pm.section.state == 'explore' and dlg not in pm.wm.windows)
check('hint toasts shown', len(toast.toasts) >= 2)
check('forced out of closed dialog, back on taskbar', P.mode == 'off')
step(1.0)
# 문서 > 숨겨진 폴더 > 설정 (마우스 더블클릭 대신 탐색기 이동)
shell.open_folder(fs.DOCUMENTS); win = pm.wm.active
win.x, win.y, win.w, win.h = 260, 60, 900, 520
win.app.go(level.find(fs.DOCUMENTS, '숨겨진 폴더')); win.app.go(level.find(fs.DOCUMENTS, '숨겨진 폴더', '설정'))
step(0.3)
check('설정 folder shows breaker and its guards', any(n is fs.BREAKER for n, r in win.app.items)
      and sum(1 for m in pm.monsters if m.win is win) >= 4)
node, (il, ib, iw, ih) = next(x for x in win.app.items if x[0] is fs.BREAKER)
for m in pm.monsters:
    if m.win is win: m.stun = 99
l, b, w, h = win.rect()
P.x, P.y, P.vy, P.ground, P.switch_cd = il + iw / 2 - 24, b + h, 0, win, 0
pm.key_down(pm.SDLK_LSHIFT)
for i in range(3):
    P.poke_cd = 0
    pm.poke(P.x + 24, b + h - 8)
step(1.0)
check('landing on the breaker turns it off -> clear', pm.section.state == 'clear' and fs.BREAKER.icon == 'breaker_off')
check('online: taskbar and chrome', pm.taskbar.online and apps.Browser.online)
check('clear dialog shown', pm.wm.active.app.title == '구간 1 클리어')
screenshot.shot(os.path.join(OUT, '10_clear.png'))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
