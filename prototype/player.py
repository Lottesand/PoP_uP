import math

from pico2d import draw_line, draw_circle, draw_rectangle

from config import *
from geometry import Rect


class Input:
    """키보드 상태. left/right/up/down 은 누르고 있는 동안 True, jump 는 누른 그 프레임만 True."""

    def __init__(self):
        self.left = self.right = self.up = self.down = False
        self.jump = False


class Stickman:
    def __init__(self, x, y):
        self.x, self.y = x, y          # 좌하단
        self.vx, self.vy = 0.0, 0.0
        self.face = 1
        self.on_ground = False
        self.ground_ref = None         # 밟고 있는 물체 (창 또는 창 안의 아이템)
        self.climbing = False
        self.has_key = False
        self.walk_phase = 0.0

    def rect(self):
        return Rect(self.x, self.y, PLAYER_W, PLAYER_H)

    def place(self, x, y):
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.climbing = False
        self.on_ground = False
        self.ground_ref = None

    def step(self, dt, inp, solids, ladder):
        """solids: [(Rect, ref)], ladder: 스크롤바 Rect 또는 None"""
        move = int(inp.right) - int(inp.left)
        if move:
            self.face = move
        self.vx = move * RUN_SPEED

        on_ladder = ladder is not None and self.rect().overlaps(ladder)
        if on_ladder and (inp.up or inp.down):
            self.climbing = True
        if not on_ladder:
            self.climbing = False

        if inp.jump and (self.on_ground or self.climbing):
            self.vy = JUMP_V
            self.climbing = False

        if self.climbing:
            self.vy = (int(inp.up) - int(inp.down)) * CLIMB_SPEED
        else:
            self.vy = max(self.vy + GRAVITY * dt, -MAX_FALL)

        # 축을 나눠서 충돌 처리: x 먼저, 그다음 y
        self.x += self.vx * dt
        r = self.rect()
        for s, _ in solids:
            if r.overlaps(s):
                if self.vx > 0:
                    self.x = s.l - PLAYER_W
                elif self.vx < 0:
                    self.x = s.r
                r = self.rect()

        self.y += self.vy * dt
        self.on_ground = False
        self.ground_ref = None
        r = self.rect()
        for s, ref in solids:
            if r.overlaps(s):
                if self.vy <= 0:
                    self.y = s.t
                    self.on_ground = True
                    self.ground_ref = ref
                else:
                    self.y = s.b - PLAYER_H
                self.vy = 0
                r = self.rect()

        if self.on_ground and move:
            self.walk_phase += dt * 12
        elif self.climbing and self.vy:
            self.walk_phase += dt * 10

    def draw(self, wall_mode):
        # 벽 모드(Shift ON)일 때는 빨간 스틱맨
        c = (210, 40, 40) if wall_mode else (20, 20, 20)
        cx = self.x + PLAYER_W / 2
        head_y = self.y + PLAYER_H - 7
        neck_y = self.y + PLAYER_H - 14
        hip_y = self.y + 16
        draw_circle(cx, head_y, 6, *c, filled=True)
        swing = math.sin(self.walk_phase) * 7
        for dx in (0, 1):  # 두 번 그려서 선을 굵게
            draw_line(cx + dx, neck_y, cx + dx, hip_y, *c)
            draw_line(cx + dx, neck_y - 4, cx - 8 + swing * 0.5 + dx, neck_y - 14, *c)
            draw_line(cx + dx, neck_y - 4, cx + 8 - swing * 0.5 + dx, neck_y - 14, *c)
            draw_line(cx + dx, hip_y, cx - 6 + swing + dx, self.y, *c)
            draw_line(cx + dx, hip_y, cx + 6 - swing + dx, self.y, *c)
        if self.has_key:
            kx, ky = cx + 10 * self.face, neck_y - 12
            draw_circle(int(kx), int(ky), 4, 230, 180, 20, filled=True)
            draw_rectangle(kx - 1, ky - 10, kx + 1, ky - 4, 230, 180, 20, 255, True)
