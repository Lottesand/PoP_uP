"""창 없이 게임 규칙만 검사한다.  실행: python test_rules.py"""
from config import *
from os_window import Plate, Key, Vault
from player import Input
from world import World, BIN_POS

DT = 1 / 60


def run(world, frames, **keys):
    inp = Input()
    for k, v in keys.items():
        setattr(inp, k, v)
    for _ in range(frames):
        world.update(DT, inp)


def first_folder(world):
    return next(w for w in world.windows if w.kind == 'folder')


def setup_window(world, x, y, w=300, h=220):
    win = first_folder(world)
    win.opened = True
    world.bring_to_front(win)
    win.x, win.y, win.w, win.h = x, y, w, h
    return win


def test_wall_off_passes_behind_window():
    w = World(1)
    setup_window(w, 300, TASKBAR_H, 300, 200)   # 바닥에 붙은 창
    w.player.place(250, TASKBAR_H)
    run(w, 90, right=True)
    assert w.player.x > 600, w.player.x          # 창 뒤로 그냥 지나간다
    assert w.deaths == 0


def test_wall_on_blocks_and_can_stand_on_top():
    w = World(1)
    win = setup_window(w, 300, TASKBAR_H, 300, 80)
    w.toggle_wall_mode()
    w.player.place(250, TASKBAR_H)
    run(w, 90, right=True)
    assert w.player.x <= 300 - PLAYER_W + 0.01    # 벽에 막힌다
    w.player.place(400, win.outer.t + 30)
    run(w, 60)
    assert abs(w.player.y - win.outer.t) < 0.01 and w.player.ground_ref is win


def test_wall_on_while_overlapping_squashes():
    w = World(1)
    setup_window(w, 200, TASKBAR_H, 300, 200)
    w.player.place(250, TASKBAR_H)
    w.toggle_wall_mode()
    run(w, 1)
    assert w.deaths == 1 and (w.player.x, w.player.y) == BIN_POS and not w.wall_mode


def test_break_in_and_ride_window():
    w = World(1)
    win = setup_window(w, 300, TASKBAR_H, 300, 200)
    w.toggle_wall_mode()
    w.player.place(300 - PLAYER_W, TASKBAR_H)
    w.interact()
    assert w.layer is win
    assert win.content.contains(w.player.rect())
    run(w, 30)
    before = (w.player.x, w.player.y)
    win.move_to(win.x + 100, win.y + 150)        # 마우스로 창을 옮기면
    run(w, 1)
    assert abs(w.player.x - (before[0] + 100)) < 0.01   # 안에 있던 스틱맨도 따라온다


def test_resize_squashes_player_inside():
    w = World(1)
    win = setup_window(w, 300, TASKBAR_H, 300, 200)
    w.toggle_wall_mode()
    w.player.place(300 - PLAYER_W, TASKBAR_H)
    w.interact()
    run(w, 10)
    win.resize_to(win.x + 160, win.y + win.h - 10)  # 최소 크기까지 줄여도 높이는 남는다
    run(w, 1)
    assert w.deaths == 0
    win.min_h = 20
    win.resize_to(win.x + 160, win.y + win.h - 30)  # 내용 높이 < 스틱맨 키
    run(w, 1)
    assert w.deaths == 1


def test_exit_side_to_desktop():
    w = World(1)
    win = setup_window(w, 300, TASKBAR_H, 300, 200)
    w.toggle_wall_mode()
    w.player.place(300 - PLAYER_W, TASKBAR_H)
    w.interact()
    run(w, 30, left=True)
    w.interact()
    assert w.layer is None
    assert w.player.rect().r <= win.outer.l


def test_close_window_while_inside_ejects():
    w = World(1)
    win = setup_window(w, 300, TASKBAR_H, 300, 200)
    w.toggle_wall_mode()
    w.player.place(300 - PLAYER_W, TASKBAR_H)
    w.interact()
    w.close_window(win)
    assert w.layer is None and not win.opened


def test_frozen_window_cannot_move():
    w = World(1)
    safe = next(x for x in w.windows if x.kind == 'safe')
    x0, y0 = safe.x, safe.y
    t = safe.title_rect
    w.mouse_down(t.l + 20, t.b + 5, 0.0)
    w.mouse_move(t.l - 200, t.b - 200)
    w.mouse_up()
    assert (safe.x, safe.y) == (x0, y0)
    assert '응답' in w.msg


def test_double_click_opens_and_drag_moves():
    w = World(1)
    ic = w.desk_icons[0]
    w.mouse_down(ic.x + 10, ic.y + 10, 1.0)
    w.mouse_down(ic.x + 10, ic.y + 10, 1.2)
    win = w.by_id[ic.target]
    assert win.opened and w.top_window() is win
    x0, y0 = win.x, win.y
    t = win.title_rect
    w.mouse_down(t.l + 30, t.b + 5, 3.0)
    w.mouse_move(t.l + 80, t.b - 45)
    w.mouse_up()
    assert (win.x - x0, win.y - y0) == (50, -50)


def test_pin_key_vault_escape():
    w = World(7)
    calc = next(x for x in w.windows if x.kind == 'calc')
    calc.opened = True
    w.bring_to_front(calc)
    calc.x, calc.y = 300, TASKBAR_H
    w.layer = calc
    plates = {it.digit: it for it in calc.items if isinstance(it, Plate)}
    for d in w.pin:
        r = plates[d].rect(calc)
        w.player.place(r.l + 10, r.t + 20)
        run(w, 40)
        w.player.place(calc.content.l + 100, calc.content.t - 60)   # 발판에서 내려온다
        run(w, 5)
    key = next(it for it in calc.items if isinstance(it, Key))
    assert key.active, w.entered
    kr = key.rect(calc)
    w.player.place(kr.l, kr.b)
    run(w, 1)
    assert w.player.has_key

    safe = next(x for x in w.windows if x.kind == 'safe')
    w.layer = safe
    vault = next(it for it in safe.items if isinstance(it, Vault))
    vr = vault.rect(safe)
    w.player.place(vr.l - PLAYER_W - 1, safe.content.b)
    run(w, 1)
    assert vault.opened and not w.player.has_key
    run(w, 30, right=True)
    assert w.won


def test_wrong_pin_resets():
    w = World(7)
    calc = next(x for x in w.windows if x.kind == 'calc')
    calc.opened = True
    w.bring_to_front(calc)
    w.layer = calc
    wrong = '0000' if w.pin != '0000' else '1111'
    plates = {it.digit: it for it in calc.items if isinstance(it, Plate)}
    for d in wrong:
        r = plates[d].rect(calc)
        w.player.place(r.l + 10, r.t + 20)
        run(w, 40)
        w.player.place(calc.content.l + 100, calc.content.t - 60)
        run(w, 5)
    assert w.entered == '' and 'PIN 오류' in w.msg


def test_random_is_seeded():
    a, b, c = World(3), World(3), World(4)
    sig = lambda w: (w.pin, [i.name for i in w.desk_icons], [x.title for x in w.windows])
    assert sig(a) == sig(b)
    assert sig(a) != sig(c)
    # PIN.txt 는 항상 어딘가의 폴더 안에 하나 있다
    for s in range(30):
        w = World(s)
        holders = [x for x in w.windows if any(i.name == 'PIN.txt' for i in x.icons)]
        assert len(holders) == 1
        pin_memo = next(x for x in w.windows if x.title == 'PIN.txt')
        assert w.pin in pin_memo.lines


if __name__ == '__main__':
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_')]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print('PASS', name)
        except AssertionError as e:
            failed += 1
            print('FAIL', name, e)
    print(f'{len(tests) - failed}/{len(tests)} passed')
    raise SystemExit(1 if failed else 0)
