import os
import sys

from pico2d import *
import pico2d.pico2d as pico2d_core   # 반투명 그리기용 renderer 접근

from config import *
from player import Input
from world import World
from render import draw_world


def load_fonts():
    path = next((p for p in FONT_PATHS if os.path.exists(p)), None)
    if path is None:
        raise IOError('한글 폰트를 찾지 못했습니다: config.FONT_PATHS 를 확인하세요')
    return {'small': load_font(path, 13), 'font': load_font(path, 16), 'big': load_font(path, 26)}


def handle_events():
    global running, world
    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
        elif event.type in (SDL_KEYDOWN, SDL_KEYUP):
            down = event.type == SDL_KEYDOWN
            if event.key == SDLK_a:
                inp.left = down
            elif event.key == SDLK_d:
                inp.right = down
            elif event.key == SDLK_w:
                inp.up = down
            elif event.key == SDLK_s:
                inp.down = down
            elif not down:
                pass
            elif event.key == SDLK_ESCAPE:
                running = False
            elif event.key == SDLK_SPACE:
                inp.jump = True
            elif event.key in (SDLK_LSHIFT, SDLK_RSHIFT):
                world.toggle_wall_mode()
            elif event.key == SDLK_e:
                world.interact()
            elif event.key == SDLK_r:
                world = World()
        elif event.type in (SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDL_MOUSEBUTTONUP):
            mx, my = event.x, CANVAS_H - 1 - event.y   # pico2d 는 y 가 위로 증가
            if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
                world.mouse_down(mx, my, get_time())
            elif event.type == SDL_MOUSEMOTION:
                world.mouse_move(mx, my)
            elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_LEFT:
                world.mouse_up()


# 실행: python main.py [seed]   (seed 를 주면 같은 컴퓨터가 다시 만들어진다)
seed = int(sys.argv[1]) if len(sys.argv) > 1 else None

open_canvas(CANVAS_W, CANVAS_H)
hide_lattice()
SDL_SetRenderDrawBlendMode(pico2d_core.renderer, SDL_BLENDMODE_BLEND)
fonts = load_fonts()
world = World(seed)
inp = Input()
running = True
last = get_time()

while running:
    handle_events()
    now = get_time()
    dt, last = min(now - last, 0.05), now
    world.update(dt, inp)
    draw_world(world, fonts)
    delay(0.005)

close_canvas()
