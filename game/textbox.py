# 글자 입력: SDL 이벤트를 직접 받아 한글 조합(IME)과 키 반복까지 처리한다. 메모장 · 주소창 · 검색창이 쓴다.
# pico2d.get_events는 SDL_TEXTINPUT / SDL_TEXTEDITING을 버려서 한글을 입력할 수 없다.
import ctypes
import time
import pico2d.pico2d as p2
from sdl2 import *

import gfx
from config import *

focus = None                       # 지금 글자를 받고 있는 입력란


class Event:
    def __init__(self, kind):
        self.type = kind
        self.key = self.button = self.x = self.y = None
        self.repeat = 0
        self.mod = 0
        self.text = ''


def get_events():
    """pico2d.get_events와 같은 모양 + 글자 입력 이벤트(text). 키 반복(repeat)도 넘긴다"""
    p2.print_fps()
    SDL_Delay(1)
    e = SDL_Event()
    out = []
    while SDL_PollEvent(ctypes.byref(e)):
        ev = Event(e.type)
        if e.type in (SDL_KEYDOWN, SDL_KEYUP):
            ev.key, ev.repeat, ev.mod = e.key.keysym.sym, e.key.repeat, e.key.keysym.mod
        elif e.type == SDL_MOUSEMOTION:
            ev.x, ev.y = e.motion.x, e.motion.y
        elif e.type in (SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP):
            ev.button, ev.x, ev.y = e.button.button, e.button.x, e.button.y
        elif e.type == SDL_MOUSEWHEEL:
            ev.x, ev.y = e.wheel.x, e.wheel.y
        elif e.type == SDL_TEXTINPUT:
            ev.text = e.text.text.decode('utf-8', 'ignore')
        elif e.type == SDL_TEXTEDITING:
            ev.text = e.edit.text.decode('utf-8', 'ignore')
        elif e.type != SDL_QUIT:
            continue
        out.append(ev)
    return out


def set_focus(box):
    """입력란에 글자를 받게 한다. 입력란이 없을 때는 IME를 꺼서 A/D 같은 조작 키가 한글로 바뀌지 않게 한다"""
    global focus
    if focus is box:
        return
    if focus is not None:
        focus.comp = ''
    focus = box
    if box is None:
        SDL_StopTextInput()
    else:
        SDL_StartTextInput()


def init():
    SDL_SetHint(SDL_HINT_IME_SHOW_UI, b'1')
    set_focus(None)
    SDL_StopTextInput()


class TextBox:
    """한 줄(주소창) 또는 여러 줄(메모장) 입력란. lines를 그대로 고친다"""

    def __init__(self, owner, lines=None, multiline=False, on_enter=None, on_save=None):
        self.owner = owner             # 이 입력란이 들어 있는 프로그램 (그 창이 앞에 있을 때만 입력)
        self.on_save = on_save         # Ctrl+S
        self.lines = lines if lines is not None else ['']
        if not self.lines:
            self.lines.append('')
        self.multiline = multiline
        self.on_enter = on_enter       # 한 줄 입력란에서 Enter
        self.row = len(self.lines) - 1
        self.col = len(self.lines[self.row])
        self.comp = ''                 # 조합 중인 한글 (아직 확정 전)
        self.dirty = False
        self.blink0 = time.time()

    @property
    def text(self):
        return '\n'.join(self.lines)

    def set_text(self, s):
        self.lines[:] = s.split('\n') if self.multiline else [s.replace('\n', ' ')]
        self.row = len(self.lines) - 1
        self.col = len(self.lines[self.row])
        self.comp = ''

    def select_all_end(self):
        self.row = len(self.lines) - 1
        self.col = len(self.lines[self.row])

    # ---------------------------------------------------------------- 입력
    def insert(self, s):
        self.comp = ''
        for i, part in enumerate(s.split('\n')):
            if i:
                if not self.multiline:
                    break
                line = self.lines[self.row]
                self.lines[self.row] = line[:self.col]
                self.lines.insert(self.row + 1, line[self.col:])
                self.row, self.col = self.row + 1, 0
            line = self.lines[self.row]
            self.lines[self.row] = line[:self.col] + part + line[self.col:]
            self.col += len(part)
        self.dirty = True
        self.blink0 = time.time()

    def compose(self, s):
        self.comp = s
        self.blink0 = time.time()

    def key(self, sym, mod=0):
        """처리한 키면 True"""
        line = self.lines[self.row]
        if sym == SDLK_BACKSPACE:
            if self.col > 0:
                self.lines[self.row] = line[:self.col - 1] + line[self.col:]
                self.col -= 1
            elif self.row > 0:
                self.col = len(self.lines[self.row - 1])
                self.lines[self.row - 1] += line
                del self.lines[self.row]
                self.row -= 1
            self.dirty = True
        elif sym == SDLK_DELETE:
            if self.col < len(line):
                self.lines[self.row] = line[:self.col] + line[self.col + 1:]
            elif self.row < len(self.lines) - 1:
                self.lines[self.row] += self.lines.pop(self.row + 1)
            self.dirty = True
        elif sym == SDLK_LEFT:
            if self.col > 0:
                self.col -= 1
            elif self.row > 0:
                self.row -= 1
                self.col = len(self.lines[self.row])
        elif sym == SDLK_RIGHT:
            if self.col < len(line):
                self.col += 1
            elif self.row < len(self.lines) - 1:
                self.row, self.col = self.row + 1, 0
        elif sym == SDLK_UP and self.multiline:
            if self.row > 0:
                self.row -= 1
                self.col = min(self.col, len(self.lines[self.row]))
        elif sym == SDLK_DOWN and self.multiline:
            if self.row < len(self.lines) - 1:
                self.row += 1
                self.col = min(self.col, len(self.lines[self.row]))
        elif sym == SDLK_HOME:
            self.col = 0
        elif sym == SDLK_END:
            self.col = len(line)
        elif sym in (SDLK_RETURN, SDLK_KP_ENTER):
            if self.multiline:
                self.insert('\n')
            elif self.on_enter:
                self.on_enter(self.text)
        else:
            return False
        self.blink0 = time.time()
        return True

    def click(self, x, y, left, top, line_h, size):
        """화면 (x, y)를 눌렀다: 그 자리로 커서를 옮긴다"""
        self.row = min(len(self.lines) - 1, max(0, int((top - y) // line_h)))
        line = self.lines[self.row]
        col = 0
        while col < len(line) and gfx.text_width(line[:col + 1], size) <= x - left:
            col += 1
        self.col = col
        self.blink0 = time.time()

    # ---------------------------------------------------------------- 그리기
    def draw(self, left, top, line_h, size, color=TEXT, focused=False, first=0, rows=None):
        """top = 첫 줄 윗변. first부터 rows줄만 그린다 (메모장 스크롤)"""
        last = len(self.lines) if rows is None else min(len(self.lines), first + rows)
        for i in range(first, last):
            cy = top - (i - first) * line_h - line_h / 2
            line = self.lines[i]
            if i == self.row and self.comp:
                head = line[:self.col]
                x = left + gfx.text(head, left, cy, size, color)
                cw = gfx.text(self.comp, x, cy, size, color)
                gfx.fill(x, cy - line_h / 2 + 2, cw, 2, color)          # 조합 중 밑줄
                gfx.text(line[self.col:], x + cw, cy, size, color)
            else:
                gfx.text(line, left, cy, size, color)
        if focused and first <= self.row < last and int((time.time() - self.blink0) * 2) % 2 == 0:
            x = left + gfx.text_width(self.lines[self.row][:self.col] + self.comp, size)
            cy = top - (self.row - first) * line_h - line_h / 2
            gfx.fill(x, cy - line_h / 2 + 2, 1, line_h - 4, color)
