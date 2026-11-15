# 창 안의 UI 조각(탐색 창 줄, 리본 탭, 툴바 단추, 메뉴, 색 칸 ...)을 창 버튼처럼 뜯어 들 수 있게 한다.
# 프로그램은 그리면서 add(키, 사각형)으로 "여기 집을 수 있는 조각이 있다"고 알리기만 하면 된다.
# 뜯는 순간 화면에 그려진 그 부분을 그대로 떠서(스냅샷) 들고, 뜯긴 자리는 10초 동안 빈 홈으로 남는다.
import ctypes
import math

import pico2d.pico2d as p2
from pico2d import Image
from sdl2 import (SDL_Rect, SDL_RenderReadPixels, SDL_CreateTexture, SDL_UpdateTexture, SDL_SetTextureBlendMode,
                  SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_STATIC, SDL_BLENDMODE_BLEND)

import gfx
from config import *

RESPAWN = 10.0
MIN_SIZE = 8
current = None                  # 지금 그리는 창의 조각 목록 (OSWindow.draw가 열고 닫는다)
pending = []                    # 뜯었지만 아직 화면을 뜨지 못한 조각 (다음 render 끝에서 뜬다)


def add(key, l, b, w, h):
    """프로그램이 그리면서 부른다: 이 사각형은 뜯어 갈 수 있는 조각"""
    if current is not None and w >= MIN_SIZE and h >= MIN_SIZE:
        current.append((key, (l, b, w, h)))


class UIBlock:
    """뜯어 든 UI 조각. 던지면 크기만큼 아프고, 먹으면 버튼처럼 회복된다"""
    kind = 'block'

    def __init__(self, win, key, rect):
        self.win, self.key = win, key
        l, b, w, h = rect
        self.rect = (int(l), int(b), max(1, int(w)), max(1, int(h)))
        self.w, self.h = self.rect[2], self.rect[3]
        self.image = None
        self.bg = (240, 240, 240)
        self.damage = int(min(24, max(6, 6 + math.sqrt(self.w * self.h) / 6)))
        self.pierce = 2 if self.w * self.h >= 4000 else 1

    def capture(self, ox=0, oy=0):
        """지금 화면에서 그 사각형을 떠 온다. (ox, oy) = 화면 흔들림으로 밀린 만큼"""
        l, b, w, h = self.rect
        r = SDL_Rect(l + ox, H - b - h + oy, w, h)
        buf = (ctypes.c_ubyte * (w * h * 4))()
        SDL_RenderReadPixels(p2.renderer, r, SDL_PIXELFORMAT_ABGR8888, buf, w * 4)
        # 빈 홈 색: 조각 바로 아래(바깥) 한 점 = 그 조각 뒤 바탕. 그게 창 밖이면 조각 모서리 색
        under = (ctypes.c_ubyte * 4)()
        cl, cb, cw, ch = self.win.client_rect()
        if cb <= b - 3:
            SDL_RenderReadPixels(p2.renderer, SDL_Rect(l + w // 2 + ox, H - (b - 3) - 1 + oy, 1, 1),
                                 SDL_PIXELFORMAT_ABGR8888, under, 4)
            self.bg = (under[0], under[1], under[2])
        else:
            self.bg = (buf[0], buf[1], buf[2])
        for i in range(3, w * h * 4, 4):
            buf[i] = 255
        tex = SDL_CreateTexture(p2.renderer, SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_STATIC, w, h)
        SDL_SetTextureBlendMode(tex, SDL_BLENDMODE_BLEND)
        SDL_UpdateTexture(tex, None, buf, w * 4)
        self.image = Image(tex)

    def fit(self, max_w, max_h):
        return min(1.0, max_w / self.w, max_h / self.h)

    def draw(self, cx, cy, scale=1.0, xscale=1.0):
        w, h = self.w * scale * abs(xscale), self.h * scale
        if self.image is None:
            gfx.fill(cx - w / 2, cy - h / 2, w, h, (220, 220, 220))
        else:
            self.image.draw(cx, cy, max(1, w), max(1, h))
        gfx.frame(cx - w / 2, cy - h / 2, w, h, (90, 90, 90))


def tear(win, key, rect):
    """조각을 뜯는다: 들 UIBlock을 돌려준다 (화면은 다음 render 끝에서 뜬다)"""
    block = UIBlock(win, key, rect)
    pending.append(block)
    win.torn_blocks[key] = RESPAWN
    win.torn_colors[key] = None             # 뜨기 전까지는 아직 그대로 보인다
    return block


def capture_pending(ox=0, oy=0):
    """render 끝에서: 뜯은 조각의 원래 모습을 떠 두고, 그 자리를 빈 홈으로 바꾼다"""
    for block in pending:
        block.capture(ox, oy)
        block.win.torn_colors[block.key] = block.bg
    pending.clear()


def draw_holes(win):
    """뜯긴 자리: 바탕색으로 비우고 점선 테두리"""
    for key, rect in win.blocks:
        color = win.torn_colors.get(key)
        if key not in win.torn_blocks or color is None:
            continue
        l, b, w, h = rect
        gfx.fill(l, b, w, h, color)
        dark = sum(color) < 380
        line = (110, 110, 110) if dark else (190, 190, 190)
        for x in range(int(l), int(l + w), 6):
            gfx.fill(x, b, 3, 1, line)
            gfx.fill(x, b + h - 1, 3, 1, line)
        for y in range(int(b), int(b + h), 6):
            gfx.fill(l, y, 1, 3, line)
            gfx.fill(l + w - 1, y, 1, 3, line)


def block_at(win, mx, my):
    for key, (l, b, w, h) in reversed(win.blocks):
        if key not in win.torn_blocks and l <= mx < l + w and b <= my < b + h:
            return key, (l, b, w, h)
    return None


def torn_at(win, mx, my):
    return any(key in win.torn_blocks and l <= mx < l + w and b <= my < b + h for key, (l, b, w, h) in win.blocks)
