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
import breaker
check('breaker is an exe with the exe icon', fs.BREAKER.name.endswith('.exe') and fs.BREAKER.icon == 'exe')
shell.open_node(fs.BREAKER); step(0.3)
bwin = pm.wm.active
app = bwin.app
check('opening it shows the breaker program', isinstance(app, breaker.Breaker) and bwin.app.title == '인터넷 차단기')
guards = [m for m in pm.monsters if m.folder is fs.BREAKER]
check('bugs live inside the log box', len(guards) == len(level.BREAKER_BUGS) and all(m.win is bwin for m in guards))
cl, cb, cw, ch = app.content
check('log box is the monsters stage', all(cl <= m.rect()[0] and m.rect()[0] + m.w <= cl + cw for m in guards))
screenshot.shot(os.path.join(OUT, '10_breaker.png'))
l_, b_, w_, h_ = app.buttons['on']
pm.mouse_down(l_ + 5, b_ + 5); pm.mouse_up(l_ + 5, b_ + 5); step(0.1)
check('[켜기] is locked while bugs remain', not app.ready and not apps.Browser.online)
for m in guards[:-1]:
    m.hit(999, 'poke', 0)
step(0.1)
check('kills are logged newest first', app.log[0] == '[제거] 버그 제거됨 (3/4)' and not app.ready)
guards[-1].hit(999, 'poke', 0)
step(0.1)
check('all bugs dead -> [켜기] unlocked', app.ready and app.enabled('on') and not app.enabled('off'))
# 창 안에 들어가서 [켜기]를 밟는다
P.enter(bwin, (l_ + 20, b_ + 80))
P.x, P.y, P.vy = l_ + 30, b_ + 120, 0
step(1.0)
check('stepping on [켜기] inside the window -> section 1 clear, section 2 starts', P.inside and pm.section.state == 'web')
check('online: taskbar and chrome', pm.taskbar.online and apps.Browser.online)
check('clear dialog shown', pm.wm.active.app.title == '구간 1 클리어')
screenshot.shot(os.path.join(OUT, '11_clear.png'))
check('status turns green: connected', app.log[0].startswith('[해제]') and app.enabled('off') and not app.enabled('on'))
pm.shell.close(pm.wm.active.app); step(0.1)
l_, b_, w_, h_ = app.buttons['off']
app.mouse_down(l_ + 5, b_ + 5, 0)
check('[끄기] blocks the internet again', not apps.Browser.online and not pm.taskbar.online)
step(0.1)
check('still standing on [켜기] presses it again', apps.Browser.online)
app.mouse_down(l_ + 5, b_ + 5, 0)
l_, b_, w_, h_ = app.buttons['on']
app.mouse_down(l_ + 5, b_ + 5, 0); step(0.1)
check('[켜기] by mouse reconnects', apps.Browser.online and pm.taskbar.online)
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
