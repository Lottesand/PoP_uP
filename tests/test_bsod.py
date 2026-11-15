import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
import ctypes
import gfx, game_framework as gf, play_mode as pm, bsod_mode, boot_mode
import pico2d.pico2d as p2
from sdl2 import SDL_RenderReadPixels, SDL_PIXELFORMAT_ABGR8888
from PIL import Image
from config import *
open_canvas(W, H); hide_lattice(); gfx.init()
gf.frame_time = 1 / 60
pm.TUTORIAL = False; pm.level.SPAWNING = False; gf.stack = [pm]; pm.init()
ok = []
def check(n, c): ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)
def shot(mod, name):
    clear_canvas(); mod.render()
    buf = (ctypes.c_ubyte * (W * H * 4))()
    SDL_RenderReadPixels(p2.renderer, None, SDL_PIXELFORMAT_ABGR8888, buf, W * 4)
    Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(OUT, name))
P = pm.player
P.x = 900; pm.update()
check('hurt deals damage + invincible', P.hurt(30, 800) and P.hp == 70 and P.invincible > 0 and P.kb > 0)
check('invincible ignores next hit', not P.hurt(30, 800) and P.hp == 70)
for _ in range(70): pm.update()
P.hurt(200, 0)
check('hp 0 -> dead', P.dead and P.face() == 'x_x')
for _ in range(50): gf.stack[-1].update()
check('after 0.6s BSOD pushed on top of play', gf.stack[-1] is bsod_mode and gf.stack[0] is pm)
for _ in range(60): gf.stack[-1].update()
shot(bsod_mode, '6_bsod.png')
for _ in range(150): gf.stack[-1].update()
check('BSOD -> reboot screen', gf.stack[-1] is boot_mode)
for _ in range(60): gf.stack[-1].update()
shot(boot_mode, '7_boot.png')
for _ in range(120): gf.stack[-1].update()
check('reboot -> back to play, respawned at checkpoint', gf.stack == [pm] and not pm.player.dead and pm.player.hp == 100
      and (pm.player.x, pm.player.y) == pm.checkpoint)
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
