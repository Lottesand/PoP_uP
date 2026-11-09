# 바탕화면 플레이 모드: 바탕화면 · 창 · 작업 표시줄 · 시작 메뉴를 묶어서 마우스 입력을 나눠 준다
from pico2d import *

import game_framework
import gfx
import apps
from config import *
from desktop import Desktop
from taskbar import Taskbar
from start_menu import StartMenu
from os_window import WindowManager

desktop = None
taskbar = None
start = None
wm = None


def open_app(key):
    make = apps.APPS.get(key)
    if make:
        wm.open(make())


def init():
    global desktop, taskbar, start, wm
    desktop = Desktop()
    taskbar = Taskbar()
    start = StartMenu()
    wm = WindowManager()


def finish():
    pass


def pause():
    pass


def resume():
    pass


def taskbar_click(name):
    if name == 'start':
        start.open = not start.open
        return
    start.open = False
    if isinstance(name, tuple):
        key = name[1]
        win = wm.find(key)
        if win is None:
            open_app(key)
        elif win is wm.active and win.state != 'min':
            wm.minimize(win)
        else:
            wm.focus(win)
    elif name == 'desktop':
        for win in wm.windows:
            if win.state != 'min':
                wm.minimize(win)


def mouse_down(mx, my):
    now = get_time()
    if start.open:
        if start.contains(mx, my):
            key = start.click(mx, my)
            if key:
                start.open = False
                open_app(key)
            return
        if taskbar.hit(mx, my, wm) != 'start':
            start.open = False
    name = taskbar.hit(mx, my, wm)
    if name:
        taskbar.pressed = name
        return
    if wm.mouse_down(mx, my, now):
        desktop.focused = False
        return
    wm.deactivate()
    key = desktop.mouse_down(mx, my, now)
    if key:
        open_app(key)


def mouse_up(mx, my):
    wm.mouse_up(mx, my)
    if taskbar.pressed is not None:
        if taskbar.hit(mx, my, wm) == taskbar.pressed:
            taskbar_click(taskbar.pressed)
        taskbar.pressed = None


def mouse_move(mx, my):
    wm.mouse_move(mx, my)
    if wm.drag:
        gfx.set_cursor(wm.cursor_for(mx, my))
        return
    on_menu = start.contains(mx, my)
    start.hover = start.hit(mx, my) if on_menu else None
    taskbar.hover = taskbar.hit(mx, my, wm) if not on_menu else None
    over_window = wm.hit(mx, my)[0] is not None
    if on_menu or taskbar.hover or over_window:
        desktop.hover = None
    else:
        desktop.mouse_move(mx, my)
    gfx.set_cursor('arrow' if on_menu or taskbar.hover else wm.cursor_for(mx, my))


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        elif event.type in (SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP):
            mx, my = event.x, H - 1 - event.y
            if event.type == SDL_MOUSEMOTION:
                mouse_move(mx, my)
            elif event.button == SDL_BUTTON_LEFT:
                if event.type == SDL_MOUSEBUTTONDOWN:
                    mouse_down(mx, my)
                else:
                    mouse_up(mx, my)


def update():
    pass


def render():
    desktop.draw()
    wm.draw()
    taskbar.draw(wm, start.open)
    start.draw()


def draw():
    clear_canvas()
    render()
    update_canvas()
