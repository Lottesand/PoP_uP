# 블루스크린: HP가 0이 되면 플레이 모드 위에 올라온다. 3초 동안 진행률이 차고 재부팅한다.
import random
from pico2d import *

import game_framework
import gfx
import boot_mode
from config import *

DURATION = 3.0
BLUE = (0, 120, 215)
t = 0.0
_qr = []


def init():
    global t, _qr
    t = 0.0
    rnd = random.Random(7)
    _qr = [(x, y) for x in range(21) for y in range(21) if rnd.random() < 0.45]


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()


def update():
    global t
    t += min(game_framework.frame_time, 1 / 30)
    if t >= DURATION:
        boot_mode.reboot = True
        game_framework.change_mode(boot_mode)


def draw_qr(l, b, size):
    gfx.fill(l, b, size, size, WHITE)
    cell = size / 25
    for x, y in _qr:
        gfx.fill(l + (x + 2) * cell, b + (y + 2) * cell, cell + 0.5, cell + 0.5, BLUE)
    for cx, cy in ((2, 2), (16, 2), (2, 16)):          # 모서리 위치 표시 세 개
        gfx.fill(l + cx * cell, b + cy * cell, 7 * cell, 7 * cell, BLUE)
        gfx.fill(l + (cx + 1) * cell, b + (cy + 1) * cell, 5 * cell, 5 * cell, WHITE)
        gfx.fill(l + (cx + 2) * cell, b + (cy + 2) * cell, 3 * cell, 3 * cell, BLUE)


def render():
    gfx.fill(0, 0, W, H, BLUE)
    l = 230
    gfx.text(':(', l, H - 300, 150, WHITE, FONT_SEMILIGHT)
    gfx.text('PC에 문제가 발생하여 다시 시작해야 합니다. 일부 오류 정보를', l, H - 470, 30, WHITE, FONT_SEMILIGHT)
    gfx.text('수집하고 있으며, 자동으로 다시 시작됩니다.', l, H - 515, 30, WHITE, FONT_SEMILIGHT)
    done = min(100, int(t / DURATION * 100))
    gfx.text('%d%% 완료' % done, l, H - 590, 30, WHITE, FONT_SEMILIGHT)
    draw_qr(l, H - 800, 130)
    tx = l + 160
    gfx.text('이 문제와 가능한 해결 방법에 대한 자세한 내용은 https://www.windows.com/stopcode를', tx, H - 682, 15, WHITE)
    gfx.text('참조하세요.', tx, H - 704, 15, WHITE)
    gfx.text('지원 담당자에게 문의하는 경우 다음 정보를 제공하세요.', tx, H - 744, 13, WHITE)
    gfx.text('중지 코드: POINTER_HP_ZERO', tx, H - 768, 13, WHITE)


def draw():
    clear_canvas()
    render()
    update_canvas()
