# 정해진 장면을 그려서 PNG로 저장한다 (화면 확인용).
#   python tools/screenshot.py <출력 폴더>
import ctypes
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'game'))

import pico2d.pico2d as p2
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas, update_canvas
from sdl2 import SDL_RenderReadPixels, SDL_PIXELFORMAT_ABGR8888
from PIL import Image

import gfx
import play_mode
from config import W, H


def shot(path):
    clear_canvas()
    play_mode.render()
    buf = (ctypes.c_ubyte * (W * H * 4))()
    SDL_RenderReadPixels(p2.renderer, None, SDL_PIXELFORMAT_ABGR8888, buf, W * 4)
    update_canvas()
    Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(path)
    print('saved', path)


def main(out):
    os.makedirs(out, exist_ok=True)
    open_canvas(W, H)
    hide_lattice()
    gfx.init()
    play_mode.init()
    shot(os.path.join(out, '1_desktop.png'))

    for key in ('this_pc', 'browser', 'documents'):
        play_mode.open_app(key)
    play_mode.desktop.selected = play_mode.desktop.folder.children[3]
    play_mode.mouse_move(W - 46 / 2 - 400, 0)
    shot(os.path.join(out, '2_windows.png'))

    for key in ('vscode', 'paint', 'kakao', 'terminal', 'recycle_bin'):
        play_mode.open_app(key)
    play_mode.start.open = True
    shot(os.path.join(out, '3_more.png'))

    # 오른쪽 클릭 메뉴 → 새로 만들기 하위 메뉴
    play_mode.start.open = False
    play_mode.right_down(1500, 700)
    menu = play_mode.shell.menu
    for i, item, b, h in menu.rows():
        if item and item.label.startswith('새로 만들기'):
            play_mode.mouse_move(menu.l + 40, b + h // 2)
    shot(os.path.join(out, '4_context_menu.png'))
    close_canvas()


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'screenshots')
