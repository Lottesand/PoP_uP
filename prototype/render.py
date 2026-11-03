from pico2d import draw_rectangle, draw_line, clear_canvas, update_canvas

from config import *
from world import BIN_POS

HELP = 'A/D 이동  Space 점프  W/S 스크롤바 오르기  Shift 벽 모드  E 벽 부수기/나가기  |  마우스: 창 끌기·크기·X 닫기, 아이콘 더블클릭  |  R 새 컴퓨터'


def draw_calc_display(world, fonts):
    def extra(win):
        c = win.content
        top = c.t - win.design_h + 296
        l, b, r, t = c.l + 110, top - 44, c.r - SCROLL_W - 10, top - 8
        if b < c.b or r <= l:
            return
        draw_rectangle(l, b, r, t, 40, 50, 40, 255, True)
        shown = '열림' if world.entered == 'OK' else (world.entered + '_' * (4 - len(world.entered)))
        fonts['big'].draw(l + 10, (b + t) / 2, f'PIN {shown}', (150, 255, 150))
    return extra


def draw_world(world, fonts):
    font, small = fonts['font'], fonts['small']
    clear_canvas()

    # 바탕화면
    draw_rectangle(0, 0, CANVAS_W, CANVAS_H, 0, 110, 120, 255, True)
    for ic in world.desk_icons:
        ic.draw_at(ic.x, ic.y, small, (255, 255, 255))
    bx, by = BIN_POS
    draw_rectangle(bx, by + 4, bx + 30, by + 40, 200, 210, 220, 255, True)
    draw_rectangle(bx - 3, by + 40, bx + 33, by + 44, 160, 170, 180, 255, True)
    small.draw(bx - 6, by + 54, '휴지통', (255, 255, 255))

    p = world.player
    if world.layer is None:
        p.draw(world.wall_mode)

    top = world.top_window()
    layer_z = world.z(world.layer)
    for w in world.open_windows():
        translucent = world.wall_mode and world.z(w) > layer_z
        extra = draw_calc_display(world, fonts) if w.kind == 'calc' else None
        w.draw(font, small, translucent, w is top, extra)
        if w is world.layer:
            p.draw(world.wall_mode)

    # 작업표시줄 + 상태
    draw_rectangle(0, 0, CANVAS_W, TASKBAR_H, 30, 35, 45, 255, True)
    draw_rectangle(4, 4, 70, TASKBAR_H - 4, 60, 140, 70, 255, True)
    font.draw(16, TASKBAR_H / 2, '시작', (255, 255, 255))
    mode = 'ON' if world.wall_mode else 'OFF'
    status = (f'벽 모드 {mode}   위치: {world.layer_name()}   열쇠: {"있음" if p.has_key else "없음"}'
              f'   시간 {world.score_time():.0f}s   사망 {world.deaths}')
    font.draw(90, TASKBAR_H / 2, status, (255, 120, 120) if world.wall_mode else (230, 230, 230))
    small.draw(CANVAS_W - 120, TASKBAR_H / 2, f'seed {world.seed}', (150, 150, 160))

    draw_rectangle(0, CANVAS_H - 20, CANVAS_W, CANVAS_H, 0, 0, 0, 120, True)
    small.draw(8, CANVAS_H - 10, HELP, (230, 230, 230))

    if world.msg_time > 0:
        w = 14 * len(world.msg) + 40
        x = (CANVAS_W - w) / 2
        draw_rectangle(x, CANVAS_H - 70, x + w, CANVAS_H - 36, 0, 0, 0, 170, True)
        font.draw(x + 20, CANVAS_H - 53, world.msg, (255, 255, 255))

    if world.won:
        draw_rectangle(0, 0, CANVAS_W, CANVAS_H, 0, 0, 0, 170, True)
        fonts['big'].draw(CANVAS_W / 2 - 150, CANVAS_H / 2 + 30, '탈출 성공!', (120, 255, 140))
        font.draw(CANVAS_W / 2 - 150, CANVAS_H / 2 - 20,
                  f'기록 {world.score_time():.1f}초 (사망 {world.deaths}회)   R: 새 컴퓨터', (255, 255, 255))

    update_canvas()
