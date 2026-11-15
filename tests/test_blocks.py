import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, fs, shell, apps, game_framework, play_mode as pm, screenshot, uiblocks
import player as pl
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []


def check(n, c):
    ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)


def frame():
    clear_canvas(); pm.render()


def step(sec):
    for _ in range(max(1, int(sec * 60))):
        pm.update(); frame()


def block(win, key):
    return next(r for k, r in win.blocks if k == key)


def grab_in(win, key):
    """그 조각 바로 옆에 서서 좌클릭"""
    l, b, w, h = block(win, key)
    P.x, P.y, P.vy = l + w / 2 - 24, b - 70, 0
    pm.mouse_down(l + w / 2, b + h / 2)
    frame()
    return P.held


P = pm.player
# ---------------------------------------------------------------- 탐색기: 탐색 창 '네트워크' 줄, 리본 '파일' 탭
pm.open_app('documents'); win = pm.wm.active
win.x, win.y, win.w, win.h = 300, 150, 1000, 600
step(0.2)
for m in pm.monsters:
    if m.folder is fs.DOCUMENTS:
        m.dead = True
pm.key_down(pm.SDLK_LSHIFT)
P.enter(win, (win.x + 400, win.y + 200)); P.invincible = 99
step(1.0)
keys = [k for k, r in win.blocks]
check('explorer exposes nav rows, ribbon tabs, nav buttons, search', {'nav:네트워크', 'ribbon:파일', 'search',
                                                                     'nav-btn:back'} <= set(keys))
held = grab_in(win, 'nav:네트워크')
check('grab the 네트워크 row', isinstance(held, uiblocks.UIBlock) and 'nav:네트워크' in win.torn_blocks)
check('the grabbed piece is a snapshot of that row', held.image is not None and held.w > 100)
check('its spot becomes an empty slot', win.torn_colors.get('nav:네트워크') is not None)
screenshot.shot(os.path.join(OUT, 'block_nav.png'))
check('cannot grab a second piece with a full hand', grab_in(win, 'ribbon:파일') is held)
# 던지기: 크기만큼 아프다
from monsters import BugWorm
bug = BugWorm(fs.DOCUMENTS, 400, 200); pm.monsters.append(bug)
step(0.1)
bug.stun, bug.vx, bug.vy = 99, 0, 0
P.x, P.y = bug.rect()[0] - 200, bug.rect()[1] - 10
step(0.05)
bx, by = bug.center()
hp = bug.hp
pm.right_down(bx, by)
check('right click throws the piece', P.held is None and pm.thrown and not isinstance(pm.thrown[-1].name, str))
for _ in range(60):
    pm.update()
    if bug.hp < hp or bug.dead:
        break
check('thrown piece hits for its size damage', bug.dead or hp - bug.hp == held.damage)
# 리본 탭 뜯어서 먹기
step(0.3)
P.hp = 50
held2 = grab_in(win, 'ribbon:파일')
check('grab the 파일 ribbon tab', isinstance(held2, uiblocks.UIBlock) and 'ribbon:파일' in win.torn_blocks)
pm.key_down(pm.SDLK_q)
check('Q eats the piece like a button (+12)', P.held is None and P.hp == 62)
frame()
screenshot.shot(os.path.join(OUT, 'block_ribbon.png'))
# 뜯긴 단추는 OS 모드에서도 눌리지 않고, 10초 뒤 돌아온다
pm.key_down(pm.SDLK_LSHIFT)
step(0.4)
back = block(win, 'nav-btn:back')
l, b, w, h = block(win, 'nav:네트워크')
before = win.app.node
pm.mouse_down(l + w / 2, b + h / 2); pm.mouse_up(l + w / 2, b + h / 2)
check('a torn nav row does nothing when clicked', win.app.node is before)
step(10.2)
check('pieces grow back after 10s', not win.torn_blocks)
pm.mouse_down(l + w / 2, b + h / 2); pm.mouse_up(l + w / 2, b + h / 2)
check('after growing back it works again', win.app.node is fs.NETWORK)
pm.key_down(pm.SDLK_LSHIFT)
step(0.3)

# ---------------------------------------------------------------- 다른 프로그램들
def try_app(open_it, key_prefix, label):
    P.force_out()
    for w in list(pm.wm.windows):
        pm.wm.close(w)
    step(0.1)
    open_it(); w = pm.wm.active
    w.x, w.y = 260, 160
    step(0.2)
    pm.key_down(pm.SDLK_LSHIFT)
    P.enter(w, (w.x + 200, w.y + 200)); P.invincible = 99
    step(0.3)
    key = next(k for k, r in w.blocks if k.startswith(key_prefix))
    held = grab_in(w, key)
    check('%s: grab %s' % (label, key), isinstance(held, uiblocks.UIBlock) and key in w.torn_blocks
          and held.image is not None)
    P.held = None
    pm.key_down(pm.SDLK_LSHIFT)
    step(0.2)
    return w


try_app(lambda: pm.open_app('browser'), 'btn:home', 'Chrome toolbar button')
apps.Browser.online = True
w = try_app(lambda: pm.open_app('browser'), 'tab:0', 'Chrome tab')
apps.Browser.online = False
try_app(lambda: pm.open_app('paint'), 'color:3', 'Paint color swatch')
try_app(lambda: pm.open_app('paint'), 'btn:모두 지우기', 'Paint button')
try_app(lambda: pm.open_app('vscode'), 'activity:1', 'VS Code activity icon')
try_app(lambda: pm.open_app('notepad'), 'menu:파일(F)', 'Notepad menu')
try_app(lambda: pm.open_app('kakao'), 'login', 'KakaoTalk login button')
w = try_app(lambda: pm.open_app('terminal'), 'line:0', 'Terminal text line')
frame()
screenshot.shot(os.path.join(OUT, 'block_terminal.png'))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
