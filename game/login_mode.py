# 윈도우 10 잠금 화면 → 로그인 화면. [로그인] 버튼이 게임 시작 버튼이다.
# 잠금 화면: 배경화면 위에 큰 시계와 날짜. 클릭 · 아무 키 · 위로 끌기면 위로 밀려 올라가며 로그인 화면이 나온다.
# 로그인 화면: 흐린 배경화면, 사용자 사진 · 이름 · [로그인] 버튼, 오른쪽 아래 네트워크 · 접근성 · 전원 (종료/다시 시작).
import math
import time
from pico2d import *

import game_framework
import gfx
import boot_mode
import desktop
from config import *

USER = 'PoP_uP'
SLIDE = 0.35                    # 잠금 화면이 밀려 올라가는 시간
WELCOME = 1.8                   # '환영합니다' 시간
BTN_W, BTN_H = 296, 40
DAYS = '월화수목금토일'

state = 'lock'                  # lock → slide → login → welcome
t = 0.0                         # 지금 상태가 된 뒤 흐른 시간
mouse = (0, 0)
press_y = None                  # 잠금 화면을 누른 높이 (위로 끌기)
drag_dy = 0.0
power_open = False
wallpaper = None


def init():
    global state, t, power_open, press_y, drag_dy, wallpaper
    state, t, power_open, press_y, drag_dy = 'lock', 0.0, False, None, 0.0
    wallpaper = desktop.wallpaper_name()
    gfx.set_cursor('arrow')


def finish():
    pass


def pause():
    pass


def resume():
    pass


def go(new):
    global state, t
    state, t = new, 0.0


# ------------------------------------------------------------ 자리
def avatar_center():
    return W // 2, H // 2 + 150


def button_rect():
    return W // 2 - BTN_W // 2, H // 2 - 70, BTN_W, BTN_H


def corner_buttons():
    """오른쪽 아래 기호 버튼: (이름, l, b, w, h)"""
    out = []
    for i, name in enumerate(('power', 'access', 'network')):
        out.append((name, W - 70 - i * 56, 24, 48, 48))
    return out


def power_items():
    l, b = W - 70 - 160 + 48, 84
    return [(name, l, b + (2 - i) * 40, 160, 40) for i, name in enumerate(('절전', '시스템 종료', '다시 시작'))]


def inside(mx, my, r):
    l, b, w, h = r
    return l <= mx < l + w and b <= my < b + h


# ------------------------------------------------------------ 입력
def unlock():
    if state == 'lock':
        go('slide')


def login():
    if state == 'login':
        go('welcome')


def click(mx, my):
    global power_open
    if state == 'lock':
        unlock()
        return
    if state != 'login':
        return
    if power_open:
        power_open = False
        for name, *r in power_items():
            if inside(mx, my, r):
                if name == '시스템 종료':
                    game_framework.quit()
                elif name == '다시 시작':
                    game_framework.change_mode(boot_mode)
                return
        return
    for name, *r in corner_buttons():
        if inside(mx, my, r):
            power_open = name == 'power'
            return
    if inside(mx, my, button_rect()):
        login()
        return
    ax, ay = avatar_center()
    if (mx - ax) ** 2 + (my - ay) ** 2 <= 96 ** 2:
        login()


def handle_events():
    global mouse, press_y, drag_dy, power_open
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN:
            if event.key == SDLK_ESCAPE:
                power_open = False
            elif state == 'lock':
                unlock()
            elif event.key in (SDLK_RETURN, SDLK_KP_ENTER, SDLK_SPACE):
                login()
        elif event.type in (SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP):
            mx, my = event.x, H - 1 - event.y
            mouse = (mx, my)
            if event.type == SDL_MOUSEMOTION:
                if press_y is not None and state == 'lock':
                    drag_dy = max(0.0, my - press_y)       # 잠금 화면은 위로만 끌린다
            elif event.button != SDL_BUTTON_LEFT:
                continue
            elif event.type == SDL_MOUSEBUTTONDOWN:
                if state == 'lock':
                    press_y, drag_dy = my, 0.0
                else:
                    click(mx, my)
            else:
                if state == 'lock' and press_y is not None:
                    press_y = None
                    unlock()                               # 클릭이든 위로 끌기든 열린다


def update():
    global t
    t += min(game_framework.frame_time, 1 / 30)
    if state == 'slide' and t >= SLIDE:
        go('login')
    elif state == 'welcome' and t >= WELCOME:
        import play_mode
        game_framework.change_mode(play_mode)


# ------------------------------------------------------------ 그리기
def draw_person(cx, cy, r, bg, fg):
    """윈도우 10 기본 사용자 사진: 회색 동그라미 안 흰 사람 모양"""
    gfx.circle(cx, cy, r, bg)
    gfx.push_clip(cx - r, cy - r, 2 * r, 2 * r)
    hr = int(r * 0.30)
    gfx.circle(cx, cy + int(r * 0.22), hr, fg)                       # 머리
    sr = int(r * 0.62)
    body_y = cy - int(r * 0.78)
    for dy in range(-r, sr + 1):                                    # 어깨 (반원, 아래는 동그라미 끝까지)
        dx = int((sr * sr - max(0, dy) ** 2) ** 0.5)
        y = body_y + dy
        # 큰 동그라미 밖은 그리지 않는다
        lim = int(max(0, r * r - (y - cy) ** 2) ** 0.5)
        x0, x1 = max(cx - dx, cx - lim), min(cx + dx, cx + lim)
        if x1 > x0:
            gfx.fill(x0, y, x1 - x0, 1, fg)
    gfx.pop_clip()


def draw_login():
    gfx.blurred(wallpaper, 0, 0, W, H)
    gfx.fill(0, 0, W, H, (0, 0, 0, 70))
    ax, ay = avatar_center()
    draw_person(ax, ay, 96, (199, 199, 199), (255, 255, 255))
    gfx.text(USER, W // 2, ay - 140, 40, WHITE, FONT_SEMILIGHT, align='center')
    if state == 'welcome':
        boot_mode.draw_spinner(W // 2 - 120, H // 2 - 50, t)
        gfx.text('환영합니다', W // 2 - 70, H // 2 - 50, 22, WHITE, FONT_SEMILIGHT)
    else:
        l, b, w, h = button_rect()
        hot = inside(*mouse, button_rect()) and state == 'login' and not power_open
        gfx.fill(l, b, w, h, (255, 255, 255, 90 if hot else 50))
        gfx.frame(l, b, w, h, (255, 255, 255, 200 if hot else 120), 2)
        gfx.text('로그인', l + w / 2, b + h / 2, 15, WHITE, align='center')
    # 왼쪽 아래: 사용자 목록 (하나뿐이고 골라져 있다)
    gfx.fill(16, 24, 300, 64, (255, 255, 255, 50))
    draw_person(16 + 32, 24 + 32, 22, (199, 199, 199), (255, 255, 255))
    gfx.text(USER, 16 + 66, 24 + 32, 15, WHITE)
    # 오른쪽 아래 기호 버튼
    glyph = {'power': '', 'access': '', 'network': ''}
    for name, l, b, w, h in corner_buttons():
        if inside(*mouse, (l, b, w, h)) or (name == 'power' and power_open):
            gfx.fill(l, b, w, h, (255, 255, 255, 50))
        gfx.symbol(glyph[name], l + w / 2, b + h / 2, 20, WHITE)
    if power_open:
        items = power_items()
        l, b = items[-1][1], items[-1][2]
        gfx.fill(l, b, 160, 120, (43, 43, 43))
        gfx.frame(l, b, 160, 120, (90, 90, 90))
        for name, il, ib, iw, ih in items:
            if inside(*mouse, (il, ib, iw, ih)):
                gfx.fill(il, ib, iw, ih, (65, 65, 65))
            gfx.text(name, il + 14, ib + ih / 2, 15, WHITE)


def draw_lock(offset):
    gfx.image(wallpaper).draw_to_origin(0, int(offset), W, H)
    gfx.fill(0, int(offset), W, H, (0, 0, 0, 40))
    now = time.localtime()
    clock = '%d:%02d' % (now.tm_hour, now.tm_min)
    date = '%d월 %d일 %s요일' % (now.tm_mon, now.tm_mday, DAYS[now.tm_wday])
    x, y = 70, int(offset) + 300
    gfx.text(clock, x, y, 128, WHITE, FONT_SEMILIGHT)
    gfx.text(date, x + 6, y - 110, 48, WHITE, FONT_SEMILIGHT)
    for i, g in enumerate(('', '')):            # 네트워크 · 배터리
        gfx.symbol(g, W - 50 - i * 40, int(offset) + 50, 18, WHITE)
    if state == 'lock' and t > 1.2:                         # 잠시 가만히 있으면 안내
        a = int(190 + 50 * math.sin(t * 2.5))
        gfx.text('클릭하거나 아무 키나 눌러 잠금 해제', W // 2, int(offset) + 60, 15, (255, 255, 255, a), align='center')


def render():
    if state == 'lock':
        draw_lock(drag_dy)
    elif state == 'slide':
        k = min(1.0, t / SLIDE)
        k = 1 - (1 - k) ** 3                                # 빨리 올라가다가 끝에서 느려진다
        draw_login()
        draw_lock(drag_dy + (H - drag_dy) * k)
    else:
        draw_login()


def draw():
    clear_canvas()
    render()
    update_canvas()
