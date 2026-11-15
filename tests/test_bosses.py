import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, fs, shell, apps, game_framework, play_mode as pm, level, screenshot
from bosses import ChromeDino, Ptero, Blackhole, SysFile, FloorShot, Shard
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
S = pm.section
# ================================================================ 구간 2: 웹 브라우저
S.skip_to(pm, 'web')
check('section 2 starts: online, trash locked, wave hidden in Chrome', S.state == 'web' and apps.Browser.online
      and fs.TRASH.locked and sum(1 for m in pm.monsters if m.folder is fs.WEB) == len(level.WEB_WAVE))
for win in list(pm.wm.windows):
    pm.wm.close(win)
shell.open_node(fs.TRASH)
check('trash is locked during section 2', pm.wm.active is not None and pm.wm.active.app.title == '휴지통')
pm.wm.close(pm.wm.active)
pm.open_app('browser'); bwin = pm.wm.active
bwin.x, bwin.y = 300, 100
step(0.2)
wave = [m for m in pm.monsters if m.folder is fs.WEB]
check('wave lives in the Chrome page', all(m.win is bwin for m in wave))
pm.key_down(pm.SDLK_LSHIFT)
P.enter(bwin, (bwin.x + 200, bwin.y + 200)); P.invincible = 99
step(0.6)
check('search box and buttons are platforms inside Chrome', len(bwin.app.platforms()) == 3)
check('no dino while the wave is alive', S.dino is None)
for m in wave:
    m.hit(999, 'poke', 0)
step(0.2)
dino = S.dino
check('wave cleared -> dino jumps out from behind the search box', isinstance(dino, ChromeDino) and dino in pm.monsters)
step(1.2)
check('dino lands and staggers (vulnerable)', dino.ry == 0 and dino.state in ('stagger', 'idle', 'windup', 'cactus', 'stomp'))
screenshot.shot(os.path.join(OUT, 'boss_dino.png'))
# 데미지: 경직 중에만 다 들어간다
dino.state, dino.timer = 'idle', 5
hp = dino.hp; dino.hit(20, 'close', 0)
check('outside stagger: half damage', hp - dino.hp == 10)
dino.state, dino.timer = 'stagger', 5
hp = dino.hp; dino.hit(20, 'close', 0)
check('during stagger: full damage', hp - dino.hp == 20)
# 선인장 연속
dino.state, dino.timer, dino.cactus_left = 'cactus', 0, 3
seen = set()
for _ in range(80):
    pm.update()
    seen |= {id(b) for b in pm.bullets if isinstance(b, FloorShot) and b.kind == 'cactus'}
check('network cut: 3 cacti slide along the floor', len(seen) == 3)
# 점프 짓밟기 → 충격파
for b in pm.bullets:
    b.dead = True
dino.state, dino.vy, dino.vx = 'stomp', 1150, 0
for _ in range(120):
    pm.update()
    if dino.state == 'stagger':
        break
check('stomp landing: two shockwaves + stagger', dino.state == 'stagger'
      and sum(1 for b in pm.bullets if isinstance(b, FloorShot) and b.kind == 'wave') == 2)
# 2페이즈
dino.hp = dino.max_hp // 2
step(0.1)
check('phase 2 at half HP: 2 pterodactyls', dino.phase == 2 and sum(1 for m in pm.monsters if isinstance(m, Ptero)) == 2)
step(0.5)
screenshot.shot(os.path.join(OUT, 'boss_dino2.png'))
dino.state = 'stagger'
dino.hit(999, 'close', 0)
step(0.2)
check('dino down -> section 3, %appdata% unlocked', S.state == 'appdata' and not fs.APPDATA.locked)
check('section 2 clear dialog', any(w.app.title == '구간 2 클리어' for w in pm.wm.windows))

# ================================================================ 구간 3: %appdata%
P.force_out()
for win in list(pm.wm.windows):
    pm.wm.close(win)
step(0.2)
check('appdata path: C: > Users > Pointer > AppData > Local > Temp',
      level.find(fs.ROOT, '로컬 디스크 (C:)', 'Users', 'Pointer', 'AppData', 'Local', 'Temp') is fs.TEMP)
check('appdata folders have monsters', all(any(m.folder is f for m in pm.monsters)
                                           for f in (fs.APPDATA, fs.ROAMING, fs.LOCAL)))
shell.open_folder(fs.TEMP); twin = pm.wm.active
twin.x, twin.y, twin.w, twin.h = 300, 80, 1100, 720
step(0.3)
hole = S.hole
files = [m for m in pm.monsters if isinstance(m, SysFile)]
check('blackhole sits in the middle of Temp with 3 system files', hole.win is twin and len(files) == 3
      and all(f.win is twin for f in files))
cl, cb, cw, ch = twin.app.content
hx, hy = hole.center()
check('blackhole is centered', abs(hx - (cl + cw / 2)) < 2)
pm.key_down(pm.SDLK_LSHIFT)
P.enter(twin, (cl + 60, cb + 100)); P.invincible = 99
step(1.0)
x0 = P.x
hole.state, hole.timer = 'suck', 4.0
step(0.5)
check('suck pulls the pointer toward the hole', P.x - x0 > 40)
screenshot.shot(os.path.join(OUT, 'boss_hole.png'))
# 파일을 때리면 블랙홀 반대쪽으로 밀린다
f = files[0]
fx = f.center()[0]
f.hit(8, 'poke', 0)
step(0.2)
check('hitting a system file pushes it away from the hole', abs(f.center()[0] - hx) > abs(fx - hx))
# 삼키면 HP +100
hole.hp = 300
g = files[1]
gx, gy = g.center()
g.rx += hx - gx - 10
g.ry += hy - gy
hole.state, hole.timer = 'suck', 4.0
step(0.3)
check('swallowing a system file heals the hole +100', g.dead and hole.hp == 400)
# 파편 8방향 → 2페이즈 16방향
for b in pm.bullets:
    b.dead = True
hole.state, hole.timer, hole.step = 'rest', 0, 1
pm.update()
check('8 shards in phase 1', sum(1 for b in pm.bullets if isinstance(b, Shard)) == 8)
for b in pm.bullets:
    b.dead = True
hole.hp = 200
hole.state, hole.timer, hole.step = 'rest', 0, 1
pm.update()
check('phase 2: 16 shards', hole.phase == 2 and sum(1 for b in pm.bullets if isinstance(b, Shard)) == 16)
step(0.2)
screenshot.shot(os.path.join(OUT, 'boss_hole2.png'))
hole.hit(999, 'close', 0)
step(0.2)
check('hole down -> trash unlocked, section 3 clear', S.state == 'done' and not fs.TRASH.locked
      and any(w.app.title == '구간 3 클리어' for w in pm.wm.windows))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
