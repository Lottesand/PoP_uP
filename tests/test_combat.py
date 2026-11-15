import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, fs, game_framework, play_mode as pm, level, screenshot
from monsters import BugWorm, Caret, Bomber
from player import Thrown
from config import *
open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []
def check(n, c): ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)
def step(sec):
    for _ in range(max(1, int(sec * 60))):
        pm.update(); clear_canvas(); pm.render()
P = pm.player
check('monsters placed in 5 folders', len(pm.monsters) == 17)
pm.open_app('documents'); win = pm.wm.active
win.x, win.y, win.w, win.h = 300, 120, 1000, 600
step(0.5)
bugs = [m for m in pm.monsters if m.folder is fs.DOCUMENTS]
check('folder monsters active in its window', all(m.win is win for m in bugs))
other = [m for m in pm.monsters if m.folder is not fs.DOCUMENTS]
check('other folders monsters inactive', all(m.win is None for m in other))
check('bugs are scattered top-down (no gravity)', len({round(m.ry) for m in bugs}) > 1)
# 창 안으로 들어가서 바닥에 서기
l, b, w, h = win.rect(); P.x, P.y = l + 300, b + 40
P.enter(win); step(1.5)
check('player lands on explorer floor (status bar top)', P.mode == 'on' and abs(P.y - win.app.floor[2]) < 1)
# 버그와 닿으면 데미지 10
hp = P.hp
for _ in range(400):
    pm.update()
    if P.hp < hp: break
check('bug contact hurts 10', hp - P.hp == 10 and P.invincible > 0)
# 기본 무기: 찌르기로 8 데미지
bug = next(m for m in pm.monsters if m.folder is fs.DOCUMENTS)
bug.stun, bug.vx = 5, 0
hp0 = bug.hp
P.poke_cd = 0
P.x = bug.rect()[0] - 60; P.y = bug.rect()[1]
pm.poke(*bug.center())
check('poke hits monster for 8', hp0 - bug.hp == 8)
# 닫기 버튼 던지기: 관통으로 두 마리 모두
bugs = [m for m in pm.monsters if m.folder is fs.DOCUMENTS]
for i, m in enumerate(bugs): m.stun = 5; m.vx = m.vy = 0; m.rx, m.ry = 160 + i * 70, 40   # 한 줄로 세운다
by = bugs[0].center()[1]
x0 = win.app.content[0] + 10
t = Thrown('close', x0, by, 1400, 0, win); pm.thrown.append(t)
for m in bugs: m.hp = 20
step(1.0)
check('close button pierces 3 bugs in a row (25 dmg kills)', not any(m in pm.monsters for m in bugs))
# 최소화 버튼: 기절 + 로고 카운트 리셋
pm.wm.close(win); step(0.2)
hid = level.find(fs.DOCUMENTS, '숨겨진 폴더')
pm.player.force_out(); pm.shell.open_folder(hid); win2 = pm.wm.active
win2.x, win2.y, win2.w, win2.h = 300, 120, 1000, 600
step(0.3)
bomb = next(m for m in pm.monsters if isinstance(m, Bomber) and m.folder is hid)
caret = next(m for m in pm.monsters if isinstance(m, Caret) and m.folder is hid)
l, b, w, h = win2.rect(); P.x, P.y, P.ground, P.switch_cd = bomb.center()[0] - 140, b + h, win2, 0
P.enter(win2); step(0.1)
P.invincible = 99; caret.stun = 99
for _ in range(240):
    pm.update()
    if bomb.state == 'count': break
check('bomber chases and starts countdown', bomb.state == 'count')
bomb.hit(10, 'min', 0)
check('minimize hit resets countdown and stuns', bomb.state == 'chase' and bomb.stun > 0)
# 자폭: 반경 안 데미지 + 발판 갈라짐
P.invincible = 0; P.hp = 100
bomb.stun = 0; bomb.state, bomb.fuse = 'count', 0.01
bx, byy = bomb.center()
P.x = bx - 24
pm.update(); step(0.1)
check('explosion hurts 30', P.hp == 70)
node, (il, ib, iw, ih) = win2.app.items[0]
pm.explode(win2, il + iw / 2, ib + ih, 60, 0)
check('explosion splits item platforms', node.cuts and not any(x0 < il + iw / 2 < x1 and y == ib + ih for x0, x1, y in win2.app.platforms()))
# 캐럿 숫자탄
P.invincible = 0; caret.stun = 0; caret.timer = 0
fired = False
for _ in range(200):
    pm.update()
    if pm.bullets: fired = True; break
check('caret fires digit bullet', fired and 0 <= pm.bullets[0].value <= 9)
P.invincible = 0; hp = P.hp; d = pm.bullets[0]; val = d.value
for _ in range(300):
    pm.update()
    if d.dead: break
check('digit bullet hits for its value', d.dead and hp - P.hp in (val, 0))
screenshot.shot(os.path.join(OUT, '8_combat.png'))
# 버그 출현: 폴더 창을 열어 두면 2.5초 뒤, 그 뒤로 6초마다 가장자리에서 튀어나온다 (한 폴더 최대 4마리)
level.SPAWNING = True
P.force_out()
dl = level.find(fs.ROOT, '다운로드')
pm.shell.open_folder(dl); dwin = pm.wm.active
dwin.x, dwin.y, dwin.w, dwin.h = 200, 300, 900, 500
step(2.2)
first = [m for m in pm.monsters if m.folder is dl]
check('a bug crawls in from an edge after 2s', len(first) == 1)
step(3.1)
check('another bug 3s later', sum(1 for m in pm.monsters if m.folder is dl) == 2)
step(30)
dl_bugs = [m for m in pm.monsters if m.folder is dl]
check('at most 7 bugs per folder', len(dl_bugs) == 7)
# 창 안에 들어가면 사방에서 포인터 쪽으로 기어온다
P.enter(dwin); P.invincible = 99
def dist(m):
    mx, my = m.center(); px, py = P.center()
    return ((mx - px) ** 2 + (my - py) ** 2) ** 0.5
d0 = sum(dist(m) for m in dl_bugs)
step(1.5)
check('bugs crawl toward the pointer', sum(dist(m) for m in dl_bugs) < d0 * 0.8)
check('bugs come from different directions', len({round(m.ry / 60) for m in dl_bugs}) > 2)
level.SPAWNING = False
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
