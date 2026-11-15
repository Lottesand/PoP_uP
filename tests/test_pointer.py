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

open_canvas(W, H); hide_lattice(); gfx.init(); pm.TUTORIAL = False; pm.init()
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
# Shift ON: 발밑의 창으로 들어가기
pm.key_down(pm.SDLK_LSHIFT); step(0.1)
cl, cb, cw, ch = win.client_rect()
check('shift enters window under feet', P.mode == 'on' and P.win is win and cl <= P.x <= cl + cw - pl.PW)
step(1.0)
check('falls to window floor inside', P.ground == 'floor' and abs(P.y - cb) < 1)
# 창 벽에 막힘
key(pm.SDLK_a); step(2.0); key(pm.SDLK_a, False)
check('left wall blocks inside window', P.x == cl)
# 쿨타임 0.3초
pm.key_down(pm.SDLK_LSHIFT); pm.key_down(pm.SDLK_LSHIFT)
check('switch cooldown blocks instant toggle', P.mode == 'off' and P.switch_cd > 0)
step(0.8)
pm.key_down(pm.SDLK_LSHIFT); step(0.6)
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
# Shift OFF: 제목 표시줄 위로 튀어나오기
pm.key_down(pm.SDLK_LSHIFT)
l, b, w, h = win.rect()
check('shift off pops out above title bar', P.mode == 'off' and P.y >= b + h and P.vy > 0)
step(1.0)
check('lands back on that title bar', P.ground is win and P.y == b + h)
# 창 위가 아닌 곳에서 Shift → 실패
P.x, P.y, P.vy = 1600, TASKBAR_H, 0; step(0.5)
pm.key_down(pm.SDLK_LSHIFT)
check('shift with no window fails', P.mode == 'off' and P.fail_t > 0)
# 창 안에 있는데 창이 닫히면 밖으로 떨어짐
P.x, P.y = win.x + 100, win.y + 20; step(0.0)
pm.key_down(pm.SDLK_LSHIFT); step(0.1)
check('enter by overlapping', P.mode == 'on')
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
pm.key_down(pm.SDLK_LSHIFT) if P.switch_cd == 0 else None
step(0.6)
pm.mouse_move(560, 250)
screenshot.shot(os.path.join(OUT, '5_player_inside.png'))
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
