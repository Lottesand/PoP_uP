# 바탕화면 플레이 모드: 바탕화면 · 창 · 작업 표시줄 · 시작 메뉴 · 오른쪽 클릭 메뉴에 마우스 입력을 나눠 준다
from pico2d import *

import sys
import random
import pico2d.pico2d
import game_framework
import gfx
import fs
import shell
import level
import toast
import textbox
from monsters import BugWorm, Popup
from fx import PokeTrail, Spark, Ring
from config import *
from desktop import Desktop
from taskbar import Taskbar, group_windows
from start_menu import StartMenu
from os_window import WindowManager
from player import Pointer, draw_crosshair, POKE_DAMAGE, BREAK_HITS

desktop = None
taskbar = None
start = None
wm = None
player = None
thrown = []
monsters = []
bullets = []
effects = []
spawner = None
hitstop = 0.0                      # 맞는 순간 세상이 잠깐 멈춘다 (남은 초)
shake_t, shake_amp = 0.0, 0         # 화면 흔들림
checkpoint = (160, TASKBAR_H)      # HP 0 → 블루스크린 → 재부팅 뒤 여기서 다시 시작
section = None
TUTORIAL = True                    # False면 시작 경고창 없이 (테스트용)
dead_t = 0.0
mouse = (0, 0)
cursor_hidden = False
PLAYER_KEYS = {SDLK_a: 'left', SDLK_d: 'right', SDLK_w: 'up', SDLK_s: 'down', SDLK_SPACE: 'jump'}


def open_app(key):
    shell.open_key(key)


def init():
    global desktop, taskbar, start, wm, player, thrown, spawner
    wm = WindowManager()
    shell.wm = wm
    shell.close_menu()
    desktop = Desktop()
    taskbar = Taskbar()
    start = StartMenu()
    player = Pointer(*checkpoint)
    thrown = []
    monsters[:] = level.spawn()
    spawner = level.Spawner()
    bullets.clear()
    effects.clear()
    toast.clear()
    global section
    section = level.Section()
    if TUTORIAL:
        section.start(sys.modules[__name__])
    else:
        section.state = 'explore'


def finish():
    pass


def pause():
    pass


def resume():
    if player.dead:
        respawn()


def respawn():
    global player, dead_t
    player = Pointer(*checkpoint)
    thrown.clear()
    dead_t = 0.0
    section.deaths += 1


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
    textbox.set_focus(None)            # 입력란을 다시 누르면 그 프로그램이 다시 잡는다
    if player.mode == 'on':
        if not player.grab(mx, my, wm) and not take_picture(mx, my):
            poke(mx, my)
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
        t = player.throw(mx, my) or player.throw_weapon(mx, my)
        if t:
            thrown.append(t)
        elif player.f5(mx, my):
            px, py = player.center()
            effects.append(Ring(player.win if player.inside else player.layer, px, py, 40, (229, 20, 0),
                                clip=player.inside))
        elif player.dash(mx, my):
            px, py = player.center()
            effects.append(Spark(player.win if player.inside else player.layer, px, py - 20, WHITE, 6,
                                 clip=player.inside))
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
    textbox.set_focus(None)
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
    elif key == SDLK_e:
        player.drop_weapon()
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


def ctrl_shortcut(event):
    """Ctrl + 키를 맨 위 창의 앱에 먼저 준다 (Chrome의 Ctrl+T/W/N/L 등). 가져갔으면 True"""
    if not event.mod & KMOD_CTRL or event.repeat or wm.active is None:
        return False
    hook = getattr(wm.active.app, 'shortcut', None)
    return bool(hook and hook(event.key))


def typing_key(event):
    """입력란에 글자를 넣는 중이면 키를 입력란으로 보낸다. 가져갔으면 True"""
    box = textbox.focus
    if box is None:
        return False
    if event.key == SDLK_ESCAPE:
        textbox.set_focus(None)
    elif event.key == SDLK_s and event.mod & KMOD_CTRL and box.on_save:
        box.on_save()
    else:
        box.key(event.key, event.mod)
    return True


def handle_events():
    for event in textbox.get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_TEXTINPUT:
            if textbox.focus:
                textbox.focus.insert(event.text)
        elif event.type == SDL_TEXTEDITING:
            if textbox.focus:
                textbox.focus.compose(event.text)
        elif event.type == SDL_KEYDOWN:
            if ctrl_shortcut(event):
                continue
            if typing_key(event) or event.repeat:
                continue
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
    global cursor_hidden, dead_t, hitstop, shake_t
    dt = min(game_framework.frame_time, 1 / 30)
    shake_t = max(0.0, shake_t - dt)
    if hitstop > 0:
        hitstop -= dt                   # 멈춘 동안은 아무것도 움직이지 않는다
        return
    wm.update(dt)
    box = textbox.focus
    if box is not None:
        # 글자를 치는 동안 포인터는 멈춘다. 입력란 주인 창이 앞에서 사라지면 입력도 끝난다
        player.left = player.right = player.up = player.down = False
        if wm.active is None or wm.active.app is not box.owner:
            textbox.set_focus(None)
    player.update(dt, wm)
    if player.dead:
        dead_t += dt
        if dead_t >= 0.6:               # x_x 표정을 잠깐 보여 준 뒤 블루스크린
            dead_t = -99
            import bsod_mode
            game_framework.push_mode(bsod_mode)
    for t in thrown:
        t.update(dt)
    update_world(dt)
    section.update(dt, sys.modules[__name__])
    toast.update(dt)
    # 창 안에서 메시지 상자의 [확인]을 밟으면 누른 것과 같다
    if player.inside and player.ground is not None and hasattr(player.win.app, 'stepped_by') \
            and player.win.app.stepped_by(player):
        player.win.app.press()
    thrown[:] = [t for t in thrown if not t.dead]
    # 침투 모드에서만 실제 마우스 커서를 숨긴다 (창이 닫혀 밖으로 밀려나도 다시 보이게)
    if (player.mode == 'on') != cursor_hidden:
        cursor_hidden = player.mode == 'on'
        if cursor_hidden:
            hide_cursor()
        else:
            show_cursor()


# ---------------------------------------------------------------- 전투
def impact(stop, shake, amp):
    """타격감: 잠깐 멈춤 + 화면 흔들림 (더 센 쪽을 남긴다)"""
    global hitstop, shake_t, shake_amp
    hitstop = max(hitstop, stop)
    shake_t = max(shake_t, shake)
    shake_amp = max(shake_amp if shake_t > 0 else 0, amp)


def take_picture(mx, my):
    """특수 무기 집기: 사진 창의 그림, VS Code의 [실행 및 디버그] 아이콘 (창 안에서 좌클릭)"""
    if not player.inside:
        return False
    app = player.win.app
    if hasattr(app, 'touches_debug') and app.touches_debug(mx, my):
        from debuggun import DebugGun
        player.take_weapon(DebugGun(app))
        app.debug_taken = True
        px, py = player.center()
        effects.append(Ring(player.win, px, py + 10, 46, player.weapon.color))
        effects.append(Popup(player.win, px, py + 50, '디버그 건!', player.weapon.color, 18))
        section.hint('gun', '디버그 건', '좌클릭: 중단점 발사 (맞은 적은 1.5초 얼어붙음)',
                     '우클릭: F5 Run 대쉬 (4초마다)   E: 버리기')
        return True
    if not hasattr(app, 'touches_picture') or not app.touches_picture(mx, my) or player.weapon is app.drawing:
        return False
    player.take_weapon(app.drawing)
    px, py = player.center()
    effects.append(Ring(player.win, px, py + 10, 46, player.weapon.color))
    effects.append(Popup(player.win, px, py + 50, '무기 장착!', player.weapon.color, 18))
    section.hint('weapon', '그림 무기', '좌클릭: 휘두르기 (그림의 모양대로 맞는다)',
                 '우클릭: 던지기 (사진 창에서 다시 집을 수 있음)')
    return True


def poke(mx, my):
    """기본 무기 찌르기: 창 안이면 몬스터를, 창 밖이면 창 테두리를 찌른다. 그림 무기를 들었으면 휘두른다"""
    if player.has('gun'):
        shot = player.shoot(mx, my)
        if shot:
            thrown.append(shot)
        return
    if player.weapon is not None:
        tip = player.swing(mx, my)
        if tip is None:
            return
        tx, ty = tip
        swing_hits()                        # 첫 프레임에 닿은 적도 바로 맞는다
    else:
        tip = player.poke(mx, my)
        if tip is None:
            return
        tx, ty = tip
        hx, hy = player.hand()
        effects.append(PokeTrail(player.win if player.inside else player.layer, hx, hy, tx, ty,
                                 clip=player.inside))
    layer = player.win if player.inside else player.layer
    if player.inside and player.weapon is None:
        for m in monsters:
            if m.win is not player.win or m.dead:
                continue                    # 다른 폴더 몬스터는 창이 없어서 위치도 없다
            l, b, w, h = m.rect()
            if l - 12 <= tx <= l + w + 12 and b - 12 <= ty <= b + h + 12:
                m.hit(POKE_DAMAGE, 'poke', player.center()[0])
                effects.append(Spark(m.win, tx, ty))
                impact(0.03, 0.08, 2)
                effects.append(Popup(m.win, *m.center(), str(POKE_DAMAGE), (255, 200, 0)))
                return
    if player.inside:
        # 안쪽에서 창 테두리(내용 영역 가장자리)를 찔렀으면 금이 가고, 세 번째에 깨고 나간다
        win = player.win
        cl, cb, cw, ch = win.client_rect()
        edge = 10
        if cl + edge <= tx <= cl + cw - edge and cb + edge <= ty <= cb + ch - edge:
            return
        x, y = min(max(tx, cl), cl + cw), min(max(ty, cb), cb + ch)
        effects.append(Spark(win, x, y, (120, 120, 120), clip=False))
        if win.crack(x, y) >= BREAK_HITS:
            effects.append(Ring(win, x, y, 40, (60, 60, 60), clip=False))
            win.shatter()
            player.break_out(win, (x, y))
        return
    win = wm.hit(tx, ty)[0]
    if win is None or win in player.ghosts:
        return
    effects.append(Spark(layer, tx, ty, (120, 120, 120), clip=False))
    if win.crack(tx, ty) >= BREAK_HITS:
        effects.append(Ring(layer, tx, ty, 40, (60, 60, 60), clip=False))
        win.shatter()
        wm.focus(win)
        player.enter(win, (tx, ty))


def platforms(win):
    return win.app.platforms()


def overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def explode(win, x, y, radius, damage):
    effects.append(Ring(win, x, y, radius))
    impact(0.08, 0.35, 10)
    effects.append(Spark(win, x, y, (255, 140, 0), 8))
    px, py = player.center()
    if player.win is win and (px - x) ** 2 + (py - y) ** 2 <= radius ** 2:
        hurt_player(damage, x)
    for m in monsters:
        if m.win is win and not m.dead:
            mx, my = m.center()
            if (mx - x) ** 2 + (my - y) ** 2 <= radius ** 2:
                m.hit(damage, 'blast', x)
                effects.append(Popup(win, mx, my + 20, str(damage)))
    if hasattr(win.app, 'split_at'):
        win.app.split_at(x, y, radius)


def hurt_player(damage, from_x):
    if player.hurt(damage, from_x):
        px, py = player.center()
        effects.append(Spark(player.win if player.inside else player.layer, px, py, CLOSE_RED, clip=player.inside))
        impact(0.05, 0.18, 5)
        effects.append(Popup(player.win, px, py + 44, '-%d' % damage))
        return True
    return False


def swing_hits():
    """그림 무기를 휘두르는 동안: 그림의 칠한 칸이 닿은 몬스터를 한 번씩 맞힌다"""
    if not player.has('drawing') or player.swing_t <= 0 or not player.inside:
        return
    pts = player.weapon_points()
    w = player.weapon
    for m in monsters:
        if m.win is not player.win or m.dead or m in player.swing_hits:
            continue
        l, b, mw, mh = m.rect()
        hit = next(((x, y) for x, y in pts if l - 4 <= x <= l + mw + 4 and b - 4 <= y <= b + mh + 4), None)
        if hit is None:
            continue
        player.swing_hits.append(m)
        damage = w.strike(m, sys.modules[__name__], player.center()[0])
        effects.append(Spark(m.win, hit[0], hit[1], w.color, 8))
        effects.append(Popup(m.win, *m.center(), str(damage), w.color, 20))
        impact(0.05, 0.15, 4 if damage < 20 else 7)


def dash_hits():
    """F5 Run 대쉬: 지나가며 닿은 적을 한 번씩 관통 데미지"""
    if not player.dash_power or player.dash_t <= 0 or not player.inside:
        return
    body = (player.x, player.y, 48, 64)
    for m in monsters:
        if m.win is player.win and not m.dead and m not in player.dash_hits and overlap(body, m.rect()):
            player.dash_hits.append(m)
            m.hit(player.dash_power, 'f5', player.center()[0])
            mx, my = m.center()
            effects.append(Spark(m.win, mx, my, (229, 20, 0), 10))
            effects.append(Popup(m.win, mx, my + 24, str(player.dash_power), (229, 20, 0), 22))
            impact(0.05, 0.15, 6)


def shot_walls():
    """창 밖에서 쏜 중단점이 창에 맞으면 테두리에 금을 낸다 (부수고 들어가는 마지막 한 번은 직접 찔러야 한다)"""
    for t in thrown:
        if t.name != 'breakpoint' or t.win is not None or t.dead:
            continue
        win = wm.hit(t.x, t.y)[0]
        if win is None or win in player.ghosts:
            continue
        t.dead = True
        effects.append(Spark(player.layer, t.x, t.y, (229, 20, 0), 6, clip=False))
        if len(win.cracks) < BREAK_HITS - 1:
            win.crack(t.x, t.y)


def fight():
    swing_hits()
    dash_hits()
    shot_walls()
    for t in thrown:
        for m in monsters:
            if t.win is None or t.dead or m.dead or m.win is not t.win or m in t.hits:
                continue                    # 창 밖에서 던진 버튼은 몬스터(창 안에만 있음)를 못 맞힌다
            if overlap(t.rect(), m.rect()):
                if hasattr(t, 'strike'):
                    t.strike(m, sys.modules[__name__])
                else:
                    m.hit(t.damage, t.name, t.x)
                t.struck(m)
                mx, my = m.center()
                heavy = t.name == 'close'
                effects.append(Spark(m.win, mx, my, CLOSE_RED if heavy else (255, 200, 0), 10))
                effects.append(Ring(m.win, mx, my, 34, WHITE))
                effects.append(Popup(m.win, mx, my + 24, str(t.damage), (255, 200, 0), 22))
                impact(0.07 if heavy else 0.05, 0.2, 7 if heavy else 5)
    if not player.inside or player.dead:
        return
    body = (player.x, player.y, 48, 64)
    for m in monsters:
        if m.win is player.win and not m.dead and m.contact_damage and overlap(body, m.rect()):
            if hurt_player(m.contact_damage, m.center()[0]) and isinstance(m, BugWorm):
                m.bounce(player.center())
    for d in bullets:
        if d.win is player.win and overlap(body, d.rect()):
            d.dead = True
            hurt_player(d.value, d.x)


def update_world(dt):
    game = sys.modules[__name__]
    spawner.update(dt, game)
    player.pull = (0.0, 0.0)                # 블랙홀이 이번 프레임에 다시 정한다
    for m in monsters:
        m.win = level.window_for(m.folder, wm)
        if m.win is not None:
            m.update(dt, game)
    for d in bullets + effects:
        d.update(dt, game)
    fight()
    monsters[:] = [m for m in monsters if not m.dead]
    bullets[:] = [d for d in bullets if not d.dead]
    effects[:] = [e for e in effects if not e.dead]


def draw_layer(win):
    """win 창 바로 위 층(None이면 바탕화면 층)에 있는 몬스터·탄·포인터·던진 버튼"""
    for m in monsters:
        if m.win is win and win is not None:
            m.draw()
    for d in bullets + effects:
        if d.win is win:
            d.draw()
    for t in thrown:
        if t.win is win:
            t.draw()
    if player.layer is win:
        player.draw()


def render():
    if shake_t > 0:
        # SDL 뷰포트는 음수 위치를 못 받아서, 0~진폭 사이로만 밀고 드러난 가장자리는 검게 둔다
        amp = max(1, int(shake_amp * min(1.0, shake_t / 0.2)))
        gfx.fill(0, 0, W, H, BLACK)
        SDL_RenderSetViewport(pico2d.pico2d.renderer, SDL_Rect(random.randint(0, amp), random.randint(0, amp), W, H))
    draw_scene()
    SDL_RenderSetViewport(pico2d.pico2d.renderer, None)


def draw_scene():
    desktop.draw()
    draw_layer(None)
    wm.draw(draw_layer)
    desktop.draw_drag()
    taskbar.draw(wm, start.open)
    player.draw_hud()
    draw_boss_bar()
    toast.draw()
    start.draw()
    if shell.menu:
        shell.menu.draw()
    if player.mode == 'on':
        draw_crosshair(*mouse)


def draw_boss_bar():
    """보스가 보이는 창에 있으면 화면 위쪽 가운데에 이름과 큰 HP 막대"""
    boss = next((m for m in monsters if getattr(m, 'boss', False) and m.win is not None and not m.dead), None)
    if boss is None:
        return
    w, l, y = 720, (W - 720) // 2, H - 64
    gfx.fill(l - 12, y - 12, w + 24, 50, (0, 0, 0, 170))
    gfx.text(boss.title, l, y + 26, 14, WHITE, FONT_BOLD)
    if getattr(boss, 'phase', 1) == 2:
        gfx.text('2페이즈', l + w, y + 26, 12, (255, 120, 120), FONT_BOLD, align='right')
    gfx.fill(l, y, w, 12, (60, 60, 60))
    k = max(0, boss.hp) / boss.max_hp
    gfx.fill(l, y, int(w * k), 12, CLOSE_RED if getattr(boss, 'state', '') != 'stagger' else (255, 200, 0))
    gfx.frame(l, y, w, 12, (200, 200, 200))
    gfx.text('%d / %d' % (max(0, boss.hp), boss.max_hp), l + w / 2, y + 6, 10, WHITE, FONT_BOLD, align='center')


def draw():
    clear_canvas()
    render()
    update_canvas()
