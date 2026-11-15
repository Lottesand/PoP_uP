import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
from sdl2 import SDLK_s, KMOD_LCTRL, SDL_KEYDOWN
import gfx, fs, textbox, game_framework, play_mode as pm, screenshot
import paint, photos, drawing
from monsters import BugWorm
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); textbox.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []


def check(n, c):
    ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)


def step(sec):
    for _ in range(max(1, int(sec * 60))):
        pm.update(); clear_canvas(); pm.render()


def ctrl(sym):
    ev = textbox.Event(SDL_KEYDOWN)
    ev.key, ev.mod, ev.repeat = sym, KMOD_LCTRL, 0
    return pm.ctrl_shortcut(ev)


P = pm.player
# ---------------------------------------------------------------- 그림 분석
red = (237, 28, 36)
spear = drawing.Drawing([[red] * 40 for _ in range(4)])
check('long thin red drawing = fire spear', spear.shape == 'spear' and spear.element == 'fire')
blob = drawing.Drawing([[(0, 0, 0)] * 30 for _ in range(30)])
check('big black square = heavy blade, slower and stronger', blob.shape == 'blade' and blob.element == 'heavy'
      and blob.damage > spear.damage and blob.swing_time > spear.swing_time)
check('weapon length is kept in a playable range', drawing.LONG_MIN <= spear.length <= drawing.LONG_MAX
      and drawing.LONG_MIN <= blob.length <= drawing.LONG_MAX)

# ---------------------------------------------------------------- 예시 그림 (그림판 없이 줍는 무기)
import level
backup = level.find(fs.DOCUMENTS, '사진 백업')
samples = {n.name: n.picture for n in backup.children}
check('photo backup has 2 sample weapons', set(samples) == {'불꽃 창.png', '얼음 망치.png'}
      and all(p is not None for p in samples.values()))
fire, ice = samples['불꽃 창.png'], samples['얼음 망치.png']
check('sample 1: flame spear = fire spear', fire.shape == 'spear' and fire.element == 'fire')
check('sample 2: ice hammer = ice blade', ice.shape == 'blade' and ice.element == 'ice')
pm.shell.open_folder(backup); bwin = pm.wm.active
bwin.x, bwin.y, bwin.w, bwin.h = 300, 300, 800, 460
step(0.2)
screenshot.shot(os.path.join(OUT, 'drawing_samples.png'))
node = next(n for n in backup.children if n.name == '얼음 망치.png')
pm.shell.open_node(node); swin = pm.wm.active
check('sample opens in the photos app', isinstance(swin.app, photos.Photos) and swin.app.drawing is ice)
pm.key_down(pm.SDLK_LSHIFT)
P.enter(swin, (swin.x + 100, swin.y + 200)); P.invincible = 99
step(1.0)
pl, pb, pw, ph = swin.app.picture_rect
pm.mouse_down(pl + pw / 2, pb + ph / 2); pm.mouse_up(pl + pw / 2, pb + ph / 2)
check('sample picture can be picked up as a weapon', P.weapon is ice)
P.drop_weapon()
P.force_out()
for win in list(pm.wm.windows):
    pm.wm.close(win)
step(0.3)

# ---------------------------------------------------------------- 그림판에서 그리고 Ctrl+S
pm.open_app('paint'); pwin = pm.wm.active
pwin.x, pwin.y = 80, 200
step(0.1)
app = pwin.app
ctrl(SDLK_s); step(0.1)
check('saving an empty canvas shows an error', pm.wm.active.app.title == '그림판')
pm.wm.close(pm.wm.active)
pm.wm.focus(pwin)
app.color = (0, 162, 232)                    # 파란 칼: 손잡이 + 넓은 날
app.tool = 'brush'
app.stroke((40, 60), (100, 60))
app.stroke((40, 50), (40, 70))
check('Ctrl+S in paint saves', ctrl(SDLK_s))
step(0.1)
node = next((n for n in fs.DESKTOP_FOLDER.children if n.name == '그림.png'), None)
check('saved as 그림.png on the desktop with an image icon', node is not None and node.icon == 'image_file')
pic = node.picture
check('white is cut away: only the inked box remains', (pic.w, pic.h) == (63, 23)
      and pic.cells[0][30] is None and pic.cells[11][30] == (0, 162, 232))
check('blue drawing = ice, long one = spear', pic.element == 'ice' and pic.shape == 'spear')
check('paint title shows the file name', app.title == '그림.png - 그림판')
vwin = pm.wm.active
check('photos window opens right after saving', isinstance(vwin.app, photos.Photos) and vwin.app.drawing is pic)
vwin.x, vwin.y = 900, 140
step(0.2)
screenshot.shot(os.path.join(OUT, 'drawing_photos.png'))

# ---------------------------------------------------------------- 사진 창에 들어가서 그림 집기
pm.key_down(pm.SDLK_LSHIFT)
P.enter(vwin, (vwin.x + 100, vwin.y + 200)); P.invincible = 99
step(1.0)
pl, pb, pw, ph = vwin.app.picture_rect
pm.mouse_down(pl + pw / 2, pb + ph / 2); pm.mouse_up(pl + pw / 2, pb + ph / 2)
check('left click on the picture equips it', P.weapon is pic)
step(0.3)
screenshot.shot(os.path.join(OUT, 'drawing_equipped.png'))

# ---------------------------------------------------------------- 몬스터 창에서 휘두르기
pm.wm.close(vwin); step(0.1)
pm.open_app('documents'); win = pm.wm.active
win.x, win.y, win.w, win.h = 300, 120, 1000, 600
step(0.2)
P.enter(win); P.invincible = 99
step(1.0)
check('weapon carried into another window', P.inside and P.win is win and P.weapon is pic)
bugs = [m for m in pm.monsters if m.folder is fs.DOCUMENTS]
for m in bugs:
    m.stun, m.vx, m.vy = 99, 0, 0
target = bugs[0]
cl, cb, cw, ch = win.app.content
P.x = cl + 200
step(0.2)
hx, hy = P.hand()
target.rx = hx + pic.length * 0.7 - cl - target.w / 2
target.ry = hy - cb - target.h / 2
for m in bugs[1:]:
    m.rx, m.ry = 700, 300
hp0 = target.hp
P.swing_cd = 0
P.invincible = 0                             # 버그는 기절 중이라 안전 (깜빡임 없이 찍으려고)
pm.poke(hx + 300, hy + 200)
step(0.1)
screenshot.shot(os.path.join(OUT, 'drawing_swing.png'))
step(0.3)
check('swing hits the bug the drawing touches', hp0 - target.hp == pic.damage)
check('ice: hit bug is slowed', target.slow > 0)
check('one hit per bug per swing', len(P.swing_hits) == 1)
far = bugs[1]
check('bug far away is not hit', far.hp == far.max_hp)

# ---------------------------------------------------------------- 우클릭 던지기
far.hp = 999
fx, fy = far.center()
hx, hy = P.hand()
pm.right_down(fx, fy + (fx - hx) * 0.18)
check('right click throws the drawing', P.weapon is None and pm.thrown and pm.thrown[-1].name == 'drawing')
for _ in range(60):
    pm.update()
    if far.hp < 999:
        break
check('thrown drawing hits for 1.5x', 999 - far.hp == int(pic.damage * 1.5))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
