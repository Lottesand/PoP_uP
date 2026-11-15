import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import ctypes
import pico2d.pico2d as p2
from sdl2 import SDL_RenderReadPixels, SDL_PIXELFORMAT_ABGR8888
from PIL import Image
import gfx, game_framework as gf, boot_mode, login_mode as lm
from config import *

open_canvas(W, H); hide_lattice(); gfx.init()
gf.frame_time = 1 / 60
gf.stack = [boot_mode]; boot_mode.init()
ok = []


def check(n, c):
    ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)


def step(n=1):
    for _ in range(n):
        gf.stack[-1].update()


def shot(name):
    clear_canvas(); gf.stack[-1].render()
    buf = (ctypes.c_ubyte * (W * H * 4))()
    SDL_RenderReadPixels(p2.renderer, None, SDL_PIXELFORMAT_ABGR8888, buf, W * 4)
    Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(OUT, name))


step(150)
check('first boot goes to the lock screen', gf.stack[-1] is lm and lm.state == 'lock')
step(90)
shot('login_lock.png')
lm.click(500, 500)
check('clicking the lock screen starts sliding it up', lm.state == 'slide')
step(10)
shot('login_slide.png')
step(20)
check('after the slide the login screen shows', lm.state == 'login')
lm.mouse = (W // 2, H // 2 - 50)
shot('login.png')
# 전원 메뉴
name, l, b, w, h = lm.corner_buttons()[0]
lm.click(l + 5, b + 5)
check('the power button opens the power menu', lm.power_open)
shot('login_power.png')
lm.click(10, H - 10)
check('clicking elsewhere closes it', not lm.power_open and lm.state == 'login')
# 로그인 = 게임 시작
l, b, w, h = lm.button_rect()
lm.click(l + w / 2, b + h / 2)
check('[로그인] button starts the welcome screen', lm.state == 'welcome')
step(30)
shot('login_welcome.png')
import play_mode
play_mode.TUTORIAL = False; play_mode.level.SPAWNING = False
step(100)
check('after "환영합니다" the game (desktop) starts', gf.stack[-1] is play_mode)
# 다시 시작 → 부팅 화면
gf.stack = [lm]; lm.init(); lm.go('login')
lm.power_open = True
it = next(i for i in lm.power_items() if i[0] == '다시 시작')
lm.click(it[1] + 5, it[2] + 5)
check('다시 시작 goes back to the boot screen', gf.stack[-1] is boot_mode)
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
