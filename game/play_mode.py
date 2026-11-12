# 바탕화면 플레이 모드: 바탕화면 · 창 · 작업 표시줄 · 시작 메뉴 · 오른쪽 클릭 메뉴에 마우스 입력을 나눠 준다
from pico2d import *

import game_framework
import gfx
import fs
import shell
from config import *
from desktop import Desktop
from taskbar import Taskbar, group_windows
from start_menu import StartMenu
from os_window import WindowManager
from player import Pointer, draw_crosshair

desktop = None
taskbar = None
start = None
wm = None
player = None
thrown = []
mouse = (0, 0)
cursor_hidden = False
PLAYER_KEYS = {SDLK_a: 'left', SDLK_d: 'right', SDLK_SPACE: 'jump'}


def open_app(key):
    shell.open_key(key)


def init():
    global desktop, taskbar, start, wm, player, thrown
    wm = WindowManager()
    shell.wm = wm
    shell.close_menu()
    desktop = Desktop()
    taskbar = Taskbar()
    start = StartMenu()
    player = Pointer()
    thrown = []


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
        wins = group_windows(wm, name[1])
        if not wins:
            open_app(name[1])
        elif wm.active in wins:
            wm.minimize(wm.active)
        else:
            wm.focus(wins[-1])
    elif name == 'desktop':
        for win in wm.windows:
            if win.state != 'min':
                wm.minimize(win)


def menu_click(mx, my):
    """열린 오른쪽 클릭 메뉴가 클릭을 가져가면 True"""
    if shell.menu is None:
        return False
    if shell.menu.contains(mx, my):
        if shell.menu.click(mx, my) == 'close':
            shell.close_menu()
        return True
    shell.close_menu()
    return False


def mouse_down(mx, my):
    now = get_time()
    if player.mode == 'on':
        player.grab(mx, my, wm)
        return
    if menu_click(mx, my):
        return
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
    desktop.mouse_down(mx, my, now)


def right_down(mx, my):
    if player.mode == 'on':
        t = player.throw(mx, my)
        if t:
            thrown.append(t)
        return
    shell.close_menu()
    start.open = False
    if taskbar.contains(mx, my):
        return
    items = wm.context(mx, my)
    if items is None:
        wm.deactivate()
        items = desktop.context(mx, my)
    else:
        desktop.focused = False
    shell.show_menu(items, mx, my)


def mouse_up(mx, my):
    wm.mouse_up(mx, my)
    desktop.mouse_up(mx, my)
    if taskbar.pressed is not None:
        if taskbar.hit(mx, my, wm) == taskbar.pressed:
            taskbar_click(taskbar.pressed)
        taskbar.pressed = None


def mouse_move(mx, my):
    global mouse
    mouse = (mx, my)
    player.aim = (mx, my)
    if player.mode == 'on':
        return
    wm.mouse_move(mx, my)
    if wm.drag:
        gfx.set_cursor(wm.cursor_for(mx, my))
        return
    if shell.menu:
        shell.menu.mouse_move(mx, my)
    on_menu = start.contains(mx, my) or (shell.menu is not None and shell.menu.contains(mx, my))
    start.hover = start.hit(mx, my) if start.contains(mx, my) else None
    taskbar.hover = taskbar.hit(mx, my, wm) if not on_menu else None
    over_other = on_menu or taskbar.hover is not None or wm.hit(mx, my)[0] is not None
    if desktop.mouse_move(mx, my, over_other):
        gfx.set_cursor('arrow')
        return
    gfx.set_cursor('arrow' if on_menu or taskbar.hover else wm.cursor_for(mx, my))


def switch_mode():
    if not player.toggle(wm):
        return
    if player.mode == 'on':
        # 침투 모드에서는 마우스가 조준선이 된다: 열린 메뉴와 끌던 창을 놓는다
        shell.close_menu()
        start.open = False
        wm.drag = wm.pressed = None
        desktop.press, desktop.dragging = None, False


def key_down(key):
    if key in PLAYER_KEYS:
        player.key(PLAYER_KEYS[key], True)
    elif key in (SDLK_LSHIFT, SDLK_RSHIFT):
        switch_mode()
    elif key == SDLK_q:
        player.eat()
    elif key == SDLK_ESCAPE:
        if shell.menu or start.open:
            shell.close_menu()
            start.open = False
        else:
            game_framework.quit()
    elif key == SDLK_DELETE:
        app = wm.active.app if wm.active else None
        if app is not None and hasattr(app, 'delete_selected'):
            app.delete_selected()
        elif app is None and desktop.selected is not None:
            desktop.delete(desktop.selected)
    elif key == SDLK_RETURN:
        if wm.active is None and desktop.selected is not None:
            shell.open_node(desktop.selected)
        elif wm.active and getattr(wm.active.app, 'selected', None) is not None:
            wm.active.app.open(wm.active.app.selected)


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN:
            key_down(event.key)
        elif event.type == SDL_KEYUP and event.key in PLAYER_KEYS:
            player.key(PLAYER_KEYS[event.key], False)
        elif event.type == SDL_MOUSEWHEEL:
            wm.wheel(mouse[0], mouse[1], event.y)
        elif event.type in (SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP):
            mx, my = event.x, H - 1 - event.y
            if event.type == SDL_MOUSEMOTION:
                mouse_move(mx, my)
            elif event.button == SDL_BUTTON_LEFT:
                if event.type == SDL_MOUSEBUTTONDOWN:
                    mouse_down(mx, my)
                elif player.mode == 'off':
                    mouse_up(mx, my)
            elif event.button == SDL_BUTTON_RIGHT and event.type == SDL_MOUSEBUTTONDOWN:
                right_down(mx, my)


def update():
    global cursor_hidden
    dt = min(game_framework.frame_time, 1 / 30)
    wm.update(dt)
    player.update(dt, wm)
    for t in thrown:
        t.update(dt)
    thrown[:] = [t for t in thrown if not t.dead]
    # 침투 모드에서만 실제 마우스 커서를 숨긴다 (창이 닫혀 밖으로 밀려나도 다시 보이게)
    if (player.mode == 'on') != cursor_hidden:
        cursor_hidden = player.mode == 'on'
        if cursor_hidden:
            hide_cursor()
        else:
            show_cursor()


def draw_layer(win):
    """win 창 바로 위 층(None이면 바탕화면 층)에 있는 포인터와 던진 버튼"""
    for t in thrown:
        if t.win is win:
            t.draw()
    if player.layer is win:
        player.draw()


def render():
    desktop.draw()
    draw_layer(None)
    wm.draw(draw_layer)
    desktop.draw_drag()
    taskbar.draw(wm, start.open)
    player.draw_hud()
    start.draw()
    if shell.menu:
        shell.menu.draw()
    if player.mode == 'on':
        draw_crosshair(*mouse)


def draw():
    clear_canvas()
    render()
    update_canvas()
