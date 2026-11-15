# PoP_uP 실행:  python main.py
from pico2d import open_canvas, close_canvas, hide_lattice

import game_framework
import gfx
import textbox
import boot_mode
from config import W, H

open_canvas(W, H, sync=True)
hide_lattice()
gfx.init()
textbox.init()
game_framework.run(boot_mode)
close_canvas()
