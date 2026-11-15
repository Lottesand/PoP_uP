import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import gfx, fs, shell, game_framework, play_mode as pm
import player as pl
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
ok = []
game_framework.frame_time = 1 / 60


def check(name, cond):
    ok.append(bool(cond)); print(('PASS ' if cond else 'FAIL ') + name)


def step(sec=0.5):
    for _ in range(int(sec * 60)):
        pm.update()
        clear_canvas(); pm.render()


def key(k, down=True):
    (pm.key_down if down else lambda kk: pm.player.key(pm.PLAYER_KEYS[kk], False))(k)


P = pm.player
step(0.3)
check('starts standing on taskbar', P.ground == 'taskbar' and P.y == TASKBAR_H)
# 걷기
x0 = P.x
key(pm.SDLK_d); step(0.5); key(pm.SDLK_d, False)
check('walks right ~180px', 170 <= P.x - x0 <= 190)
# 점프 높이
key(pm.SDLK_SPACE)
top = P.y
for _ in range(60):
    pm.update(); top = max(top, P.y)
key(pm.SDLK_SPACE, False); step(0.5)
check('full jump about 150px', 140 <= top - TASKBAR_H <= 160 and P.ground == 'taskbar')
# 짧은 점프 (일찍 떼기)
key(pm.SDLK_SPACE); pm.update(); pm.update(); pm.update(); key(pm.SDLK_SPACE, False)
top = P.y
for _ in range(40):
    pm.update(); top = max(top, P.y)
step(0.5)
check('short hop lower than full jump', top - TASKBAR_H < 90)

# 창 하나 열고 제목 표시줄로 올라가기
pm.open_app('this_pc'); win = pm.wm.active
win.x, win.y, win.w, win.h = 100, 60, 600, 110        # 제목 표시줄 윗면 y=170, 점프로 닿게
P.x, P.y, P.vy = 300, TASKBAR_H, 0; step(0.2)
key(pm.SDLK_SPACE); step(0.8); key(pm.SDLK_SPACE, False); step(0.3)
check('jump through window and land on title bar', P.ground is win and P.y == 170 and P.layer is win)
# 창을 끌면 같이 움직인다
win.x += 50; win.y += 30; step(0.1)
check('rides along when window moves', P.y == 200 and P.ground is win)
# 다른 창이 위를 덮으면 그 부분은 못 밟음
plats = pl.os_platforms(pm.wm)
check('title bar is a platform', any(o is win for *_, o in plats))
# Shift ON: 공격 모드. 아직 창 밖이고 창은 벽이 된다 (제목 표시줄 위에 그대로 서 있다)
pm.key_down(pm.SDLK_LSHIFT); step(0.3)
check('shift on = attack mode, still outside on title bar', P.mode == 'on' and not P.inside and P.ground is win)
# 발밑 창 테두리를 세 번 찌르면 금이 가다 부서지고 그 자리로 들어간다
l, b, w, h = win.rect()
cracks = []
for i in range(3):
    P.poke_cd = 0
    pm.poke(P.x + 24, b + h - 8)
    cracks.append(len(win.cracks))
check('pokes crack the border 1, 2 then break in', cracks[:2] == [1, 2] and P.inside and P.win is win
      and win.hole is not None and not win.cracks)
cl, cb, cw, ch = win.client_rect()
# 들어간 뒤 허공을 찔러도 멈추지 않는다 (몬스터가 없는 창, 다른 폴더 몬스터는 창이 없음)
P.poke_cd = 0
pm.mouse_down(cl + cw / 2, cb + ch / 2)
step(0.3)
P.poke_cd = 0
pm.mouse_down(cl + cw / 2 + 40, cb + ch / 2 - 40)
check('poking empty air inside a window works', P.inside and P.poke_t >= 0)
step(1.0)
check('falls to window floor inside', P.ground == 'floor' and abs(P.y - cb) < 1)
# 창 벽에 막힘
key(pm.SDLK_a); step(2.0); key(pm.SDLK_a, False)
check('left wall blocks inside window', P.x == cl)
# Shift를 꺼도 창 안에 그대로 (쿨타임 0.3초)
pm.key_down(pm.SDLK_LSHIFT); pm.key_down(pm.SDLK_LSHIFT)
check('shift off keeps the pointer inside', P.mode == 'off' and P.inside and P.win is win)
check('switch cooldown blocks instant toggle', P.switch_cd > 0)
step(0.8)
check('still standing inside in Shift OFF', P.inside and P.ground == 'floor')
pm.key_down(pm.SDLK_LSHIFT)
check('shift on again, still inside', P.mode == 'on' and P.inside)
# 한 번만 찌른 금은 4초 뒤 아문다
pm.open_app('documents'); other = pm.wm.active
other.x, other.y, other.w, other.h = 1300, 300, 500, 300
other.crack(1310, 400)
step(4.2)
check('single crack heals after 4s', not other.cracks)
pm.wm.close(other); pm.wm.focus(win); step(0.1)
# 버튼 뜯기: 범위 밖이면 실패
win.x, win.y, win.w, win.h = 100, 120, 600, 160; step(0.2)
name, bl, bb, bw, bh = win.caption_buttons()[0]       # close (오른쪽 끝)
check('grab fails when too far', not P.grab(bl + 10, bb + 10, pm.wm))
# 가까이 가서 뜯기
P.x = bl - 60; step(0.2)
pm.mouse_down(bl + 10, bb + 10)
check('left click grabs nearby close button', P.held == 'close' and 'close' in win.torn)
check('torn button cannot be clicked', win.hit(bl + 10, bb + 10)[0] == 'title')
# 우클릭으로 던지기
cl, cb, cw, ch = win.client_rect()
pm.right_down(cl + 20, cb + 60)
check('right click throws held button', P.held is None and len(pm.thrown) == 1 and pm.thrown[0].win is win)
step(1.0)
check('thrown button disappears at wall', len(pm.thrown) == 0)
# 먹기
name, bl, bb, bw, bh = win.caption_buttons()[2]       # min
P.x = bl - 20; step(0.1)
pm.mouse_down(bl + 10, bb + 10)
P.hp = 50
pm.key_down(pm.SDLK_q)
check('Q eats held button: +12 HP, 8s cooldown', P.hp == 62 and P.held is None and P.eat_cd > 7.9)
# 10초 뒤 버튼 다시 생김
step(10.2)
check('torn buttons respawn after 10s', not win.torn)
# 나가기: 안쪽에서 테두리를 세 번 찌르면 깨고 나간다 (오른쪽 벽)
step(0.5)
cl, cb, cw, ch = win.client_rect()
P.x = cl + cw - 60; step(0.3)
for i in range(3):
    P.poke_cd = 0
    pm.poke(cl + cw + 40, P.center()[1])
    if i < 2:
        check('inner wall cracks (%d)' % (i + 1), len(win.cracks) == i + 1 and P.inside)
l, b, w, h = win.rect()
check('third poke breaks out to the right side', not P.inside and P.mode == 'on' and P.x >= l + w)
step(1.0)
check('lands outside next to the window', not P.inside and P.ground is not None)
pm.key_down(pm.SDLK_LSHIFT); step(0.4)
check('shift off after breaking out', P.mode == 'off' and not P.inside)
# 창 밖 공격 모드에서 Shift → 다시 OFF
P.x, P.y, P.vy = 1600, TASKBAR_H, 0; step(0.5)
pm.key_down(pm.SDLK_LSHIFT); step(0.4)
check('attack mode anywhere', P.mode == 'on' and not P.inside)
pm.key_down(pm.SDLK_LSHIFT)
check('shift again leaves attack mode', P.mode == 'off')
step(0.4)
# Shift ON 순간 겹쳐 있던 창은 빠져나올 때까지 벽이 아니고, 찔러도 안 부서진다
P.x, P.y, P.vy = win.x + 100, win.y + 20, 0
pm.key_down(pm.SDLK_LSHIFT)
check('window overlapping at shift is passable', win in P.ghosts)
P.poke_cd = 0
pm.poke(P.x + 24, P.y + 30)
check('poking that window does nothing', not win.cracks and not P.inside)
step(1.5)
check('falls through it to taskbar', P.ground == 'taskbar' and win not in P.ghosts)
# 공격 모드에서 창은 벽: 옆에서 걸어가면 막힌다
l, b, w, h = win.rect()
win.y = TASKBAR_H
l, b, w, h = win.rect()
P.x = l - pl.PW - 30; step(0.1)
key(pm.SDLK_d); step(0.6); key(pm.SDLK_d, False)
check('window is a wall in attack mode', abs(P.x - (l - pl.PW)) < 1)
# 옆에서 찔러 들어간 뒤 창이 닫히면 밖으로 떨어짐
for i in range(3):
    P.poke_cd = 0
    pm.poke(l + 5, P.y + 40)
check('break in from the side', P.inside and P.win is win)
# 창 밖 공격 모드에서 버튼을 던져도 멈추지 않는다 (창 없는 몬스터와 부딪히지 않음)
pm.thrown.append(pl.Thrown('close', 900, 300, 300, 0, None))
step(0.3)
check('throwing outside windows works', True)
pm.wm.close(win); step(1.5)
check('window closed -> forced out and falls to taskbar', P.mode == 'off' and P.ground == 'taskbar')
# 앞 창이 덮은 제목 표시줄은 밟을 수 없다
pm.open_app('documents'); a = pm.wm.active
a.x, a.y, a.w, a.h = 100, 100, 500, 200
pm.open_app('this_pc'); bwin = pm.wm.active
bwin.x, bwin.y, bwin.w, bwin.h = 50, 200, 300, 200     # a의 제목 표시줄 (y=300)의 x 100~350 부분을 덮음
spans = [(x0, x1) for x0, x1, y, o in pl.os_platforms(pm.wm) if o is a]
check('covered part of title bar is not a platform', spans == [(350, 600)])
# 그리기 스크린샷
clear_canvas(); pm.render()
import screenshot
P.x, P.y = 400, a.y + 30
P.enter(a)
step(0.6)
pm.mouse_move(560, 250)
screenshot.shot(os.path.join(OUT, '5_player_inside.png'))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
