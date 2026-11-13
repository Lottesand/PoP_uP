# 부팅 화면: 검은 바탕에 파란 창 로고와 돌아가는 점들
# 처음 켤 때는 끝나면 play_mode로 바꾸고, 블루스크린 뒤 재부팅이면 pop_mode로 멈춰 둔 플레이 모드로 돌아간다.
import math
from pico2d import *

import game_framework
import gfx
from config import *

DURATION = 2.2
reboot = False
t = 0.0


def init():
    global t
    t = 0.0


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events():
    global t
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN:
            t = DURATION                 # 아무 키나 누르면 건너뛴다


def update():
    global t, reboot
    t += min(game_framework.frame_time, 1 / 30)
    if t >= DURATION:
        if reboot:
            reboot = False
            game_framework.pop_mode()
        else:
            import play_mode
            game_framework.change_mode(play_mode)


def draw_logo(cx, cy, size, color):
    g = max(2, size // 22)
    half = (size - g) // 2
    for dx, dy in ((0, 0), (half + g, 0), (0, half + g), (half + g, half + g)):
        gfx.fill(cx - size / 2 + dx, cy - size / 2 + dy, half, half, color)


def draw_spinner(cx, cy, t):
    # 다섯 점이 원을 따라 서로 조금씩 늦게 돈다
    for i in range(5):
        a = math.pi / 2 - (t * 4.2 - i * 0.32) % (2 * math.pi)
        x, y = cx + 22 * math.cos(a), cy + 22 * math.sin(a)
        gfx.circle(x, y, 3, WHITE)


def render():
    gfx.fill(0, 0, W, H, BLACK)
    if t > 0.2:
        draw_logo(W // 2, H // 2 + 60, 150, ACCENT)
    if t > 0.6:
        draw_spinner(W // 2, H // 4, t)


def draw():
    clear_canvas()
    render()
    update_canvas()
