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


# ------------------------------------------------------------ 클리핑
def push_clip(l, b, w, h):
    if _clips:
        pl, pb, pw, ph = _clips[-1]
        nl, nb = max(l, pl), max(b, pb)
        nr, nt = min(l + w, pl + pw), min(b + h, pb + ph)
        l, b, w, h = nl, nb, max(0, nr - nl), max(0, nt - nb)
    _clips.append((l, b, w, h))
    SDL_RenderSetClipRect(p2.renderer, _sdl_rect(l, b, w, h))


def pop_clip():
    _clips.pop()
    if _clips:
        SDL_RenderSetClipRect(p2.renderer, _sdl_rect(*_clips[-1]))
    else:
        SDL_RenderSetClipRect(p2.renderer, None)


# ------------------------------------------------------------ 글자
def _font(path, size):
    key = (path, size)
    if key not in _fonts:
        f = TTF_OpenFont(path.encode('utf-8'), size)
        if not f:
            raise IOError('cannot load font ' + path)
        _fonts[key] = f
    return _fonts[key]


def text_image(s, size=12, color=config.TEXT, font=config.FONT):
    # Font.draw는 부를 때마다 텍스처를 만들어서 느리다. 같은 글자는 한 번만 만든다.
    key = (s, size, color[:3], font)
    img = _texts.get(key)
    if img is None:
        if len(_texts) > 3000:
            _texts.clear()
        surface = TTF_RenderUTF8_Blended(_font(font, size), s.encode('utf-8'), SDL_Color(*color[:3]))
        if not surface:
            return None
        texture = SDL_CreateTextureFromSurface(p2.renderer, surface)
        SDL_FreeSurface(surface)
        img = Image(texture)
        _texts[key] = img
    return img


def text_width(s, size=12, font=config.FONT):
    img = text_image(s, size, config.TEXT, font) if s else None
    return img.w if img else 0


def text(s, x, cy, size=12, color=config.TEXT, font=config.FONT, align='left'):
    """cy를 세로 가운데로 글자를 그린다. 그린 폭을 돌려준다."""
    if not s:
        return 0
    img = text_image(s, size, color, font)
    if img is None:
        return 0
    if align == 'center':
        x -= img.w / 2
    elif align == 'right':
        x -= img.w
    if len(color) > 3:
        img.opacify(color[3] / 255)
    img.draw_to_origin(int(x), int(cy - img.h / 2))
    if len(color) > 3:
        img.opacify(1)
    return img.w


def symbol(code, x, cy, size=10, color=config.TEXT, align='center'):
    # Segoe MDL2 Assets 기호 (예: '\uE8BB' 닫기)
    return text(code, x, cy, size, color, config.FONT_SYMBOL, align)
