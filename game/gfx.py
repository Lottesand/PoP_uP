# pico2d에 없는 그리기 도구: 반투명 사각형, 클리핑, 글자 텍스처 캐시, 이미지 캐시, 마우스 커서 모양
# 좌표는 pico2d와 같이 왼쪽 아래가 원점이다. 사각형은 (left, bottom, width, height).
import os
import pico2d.pico2d as p2
from pico2d import load_image, Image
from sdl2 import *
from sdl2.sdlttf import TTF_OpenFont, TTF_RenderUTF8_Blended, TTF_FontAscent, TTF_FontDescent

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


def circle(x, y, r, c):
    _color(c)
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        sy = int(config.H - 1 - (y + dy))
        SDL_RenderDrawLine(p2.renderer, int(x - dx), sy, int(x + dx), sy)


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


def _is_korean(ch):
    o = ord(ch)
    return 0x1100 <= o <= 0x11FF or 0x3000 <= o <= 0x9FFF or 0xAC00 <= o <= 0xD7AF or 0xFF00 <= o <= 0xFFEF


def _runs(s, font):
    """글자를 (조각, 폰트 파일) 묶음으로 나눈다. 공백·기호는 앞 조각에 붙인다."""
    if font not in config.UI_FONTS:
        return [(s, font)]
    latin, korean = config.UI_FONTS[font]
    runs = []
    for ch in s:
        if _is_korean(ch):
            f = korean
        elif ch.isalnum():
            f = latin
        else:
            f = runs[-1][1] if runs else latin
        if runs and runs[-1][1] == f:
            runs[-1][0] += ch
        else:
            runs.append([ch, f])
    return runs


def _render(s, size, color, path):
    # Font.draw는 부를 때마다 텍스처를 만들어서 느리다. 같은 글자는 한 번만 만든다.
    key = (s, size, color[:3], path)
    img = _texts.get(key)
    if img is None:
        if len(_texts) > 4000:
            _texts.clear()
        surface = TTF_RenderUTF8_Blended(_font(path, size), s.encode('utf-8'), SDL_Color(*color[:3]))
        if not surface:
            return None
        texture = SDL_CreateTextureFromSurface(p2.renderer, surface)
        SDL_FreeSurface(surface)
        img = Image(texture)
        _texts[key] = img
    return img


def _baseline_offset(size, font):
    # 세로 가운데(cy)에서 글자 기준선까지의 거리. 한글 폰트 줄 높이를 기준으로 맞춘다.
    key = ('baseline', size, font)
    if key not in _fonts:
        path = config.UI_FONTS[font][1] if font in config.UI_FONTS else font
        f = _font(path, size)
        asc, desc = TTF_FontAscent(f), TTF_FontDescent(f)
        _fonts[key] = (asc + desc) / 2
    return _fonts[key]


def text_width(s, size=12, font=config.FONT):
    w = 0
    for part, path in _runs(s, font):
        img = _render(part, size, config.TEXT, path)
        w += img.w if img else 0
    return w


def text(s, x, cy, size=12, color=config.TEXT, font=config.FONT, align='left'):
    """cy를 세로 가운데로 글자를 그린다. 그린 폭을 돌려준다."""
    if not s:
        return 0
    imgs = [(_render(part, size, color, path), path) for part, path in _runs(s, font)]
    total = sum(img.w for img, path in imgs if img)
    if align == 'center':
        x -= total / 2
    elif align == 'right':
        x -= total
    baseline = cy - _baseline_offset(size, font)
    for img, path in imgs:
        if img is None:
            continue
        top = baseline + TTF_FontAscent(_font(path, size))
        if len(color) > 3:
            img.opacify(color[3] / 255)
        img.draw_to_origin(int(x), int(round(top - img.h)))
        if len(color) > 3:
            img.opacify(1)
        x += img.w
    return total


def symbol(code, x, cy, size=10, color=config.TEXT, align='center'):
    # Segoe MDL2 Assets 기호 (예: '\uE8BB' 닫기)
    return text(code, x, cy, size, color, config.FONT_SYMBOL, align)


def wrap(s, max_w, size=12, font=config.FONT, max_lines=2):
    # 단어 단위로 줄바꿈하고, 한 단어가 너무 길면 글자 단위로 자른다
    lines, cur = [], ''
    for word in s.split(' '):
        trial = word if not cur else cur + ' ' + word
        if text_width(trial, size, font) <= max_w:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        cur = ''
        for ch in word:
            if text_width(cur + ch, size, font) > max_w and cur:
                lines.append(cur)
                cur = ''
            cur += ch
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + '…'
    return lines


# ------------------------------------------------------------ 이미지
def image(name):
    img = _images.get(name)
    if img is None:
        img = load_image(os.path.join(config.ASSETS, name))
        _images[name] = img
    return img


def shortcut_arrow(l, b):
    # 바로 가기 아이콘 왼쪽 아래의 작은 화살표
    fill(l, b, 13, 13, config.WHITE)
    frame(l, b, 13, 13, (130, 130, 130))
    c = (0, 84, 166)
    line(l + 3, b + 3, l + 9, b + 9, c)
    line(l + 3, b + 4, l + 8, b + 9, c)
    line(l + 5, b + 9, l + 9, b + 9, c)
    line(l + 9, b + 5, l + 9, b + 9, c)


def icon(name, size, l, b, alpha=None):
    img = image('icons/%s_%d.png' % (name, size))
    if alpha is not None:
        img.opacify(alpha)
    img.draw_to_origin(int(l), int(b), size, size)
    if alpha is not None:
        img.opacify(1)
