# pico2d에 없는 그리기 도구: 반투명 사각형, 클리핑, 글자 텍스처 캐시, 이미지 캐시, 마우스 커서 모양
# 좌표는 pico2d와 같이 왼쪽 아래가 원점이다. 사각형은 (left, bottom, width, height).
import os
import pico2d.pico2d as p2
from pico2d import load_image, Image
from sdl2 import *
from sdl2.sdlttf import TTF_OpenFont, TTF_RenderUTF8_Blended

import config

_fonts = {}
_texts = {}
_images = {}
_clips = []
_cursors = {}
_cursor_now = None


def init():
    SDL_SetRenderDrawBlendMode(p2.renderer, SDL_BLENDMODE_BLEND)
    for name, kind in (('arrow', SDL_SYSTEM_CURSOR_ARROW), ('we', SDL_SYSTEM_CURSOR_SIZEWE),
                       ('ns', SDL_SYSTEM_CURSOR_SIZENS), ('nwse', SDL_SYSTEM_CURSOR_SIZENWSE),
                       ('nesw', SDL_SYSTEM_CURSOR_SIZENESW), ('hand', SDL_SYSTEM_CURSOR_HAND),
                       ('ibeam', SDL_SYSTEM_CURSOR_IBEAM)):
        _cursors[name] = SDL_CreateSystemCursor(kind)


def set_cursor(name):
    global _cursor_now
    if name != _cursor_now and name in _cursors:
        SDL_SetCursor(_cursors[name])
        _cursor_now = name


def _sdl_rect(l, b, w, h):
    return SDL_Rect(int(l), int(config.H - b - h), int(w), int(h))


def _color(c):
    SDL_SetRenderDrawColor(p2.renderer, c[0], c[1], c[2], c[3] if len(c) > 3 else 255)


def fill(l, b, w, h, c):
    if w <= 0 or h <= 0:
        return
    _color(c)
    SDL_RenderFillRect(p2.renderer, _sdl_rect(l, b, w, h))


def frame(l, b, w, h, c, t=1):
    for i in range(t):
        _color(c)
        SDL_RenderDrawRect(p2.renderer, _sdl_rect(l + i, b + i, w - 2 * i, h - 2 * i))


def line(x1, y1, x2, y2, c):
    _color(c)
    SDL_RenderDrawLine(p2.renderer, int(x1), int(config.H - 1 - y1), int(x2), int(config.H - 1 - y2))


def shadow(l, b, w, h, size=12, alpha=40):
    # 창 바깥으로 점점 옅어지는 그림자
    for i in range(size, 0, -2):
        a = int(alpha * (1 - i / (size + 1)) ** 2)
        fill(l - i, b - i - 2, w + 2 * i, h + 2 * i, (0, 0, 0, a))
