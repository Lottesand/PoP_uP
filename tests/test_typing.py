import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
from sdl2 import SDLK_BACKSPACE, SDLK_RETURN, SDLK_LEFT, SDLK_s, SDLK_d, SDLK_ESCAPE, KMOD_LCTRL, SDL_KEYDOWN
import gfx, fs, shell, textbox, game_framework, play_mode as pm, screenshot
import browser
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); textbox.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []


def check(n, c):
    ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)


def frame():
    clear_canvas(); pm.render()


def key(sym, mod=0):
    ev = textbox.Event(SDL_KEYDOWN)
    ev.key, ev.mod = sym, mod
    if not pm.typing_key(ev):
        pm.key_down(sym)


def click(x, y):
    pm.mouse_down(x, y); pm.mouse_up(x, y); frame()


# ---------------------------------------------------------------- 메모장
note = next(n for n in fs.DESKTOP_FOLDER.children if n.name == '탈출 계획.txt')
shell.open_node(note); frame()
np_ = pm.wm.active.app
l, b, w, h = np_.area
click(l + 200, b + h - 30)                 # 둘째 줄 아무 데나
check('click focuses notepad text', textbox.focus is np_.box and np_.box.row == 1)
np_.box.key(SDLK_RETURN); np_.box.row -= 1  # 둘째 줄 앞에 빈 줄 하나 (Enter 뒤 위로)
np_.box.col = 0
textbox.focus.insert('abc')
textbox.focus.compose('한')
frame()
check('korean composition shown before commit', np_.box.comp == '한' and np_.box.lines[1].startswith('abc'))
textbox.focus.insert('한글')
key(SDLK_BACKSPACE)
check('typing + backspace edits the line', np_.box.lines[1].startswith('abc한') and np_.box.comp == '')
check('title marked as unsaved', np_.title.startswith('*'))
check('file not changed before save', note.lines[1] != np_.box.lines[1])
key(SDLK_s, KMOD_LCTRL)
check('Ctrl+S saves to the file', note.lines == np_.box.lines and not np_.title.startswith('*'))
# 글자 치는 동안 D를 눌러도 포인터는 안 움직인다
x0 = pm.player.x
key(SDLK_d)
for _ in range(20):
    pm.update()
check('typing d does not move the pointer', pm.player.x == x0)
check('player key not pressed while typing', not pm.player.right)
key(SDLK_ESCAPE)
check('Esc ends typing', textbox.focus is None)
# 제목 없는 메모장 저장 → 바탕 화면에 새 파일
pm.open_app('notepad'); frame()
blank = pm.wm.active.app
bl, bb, bw, bh = blank.area
click(bl + 50, bb + bh - 20)
textbox.focus.insert('메모')
key(SDLK_s, KMOD_LCTRL)
check('untitled save creates a desktop file', blank.node is not None and blank.node.parent is fs.DESKTOP_FOLDER
      and blank.node.lines == ['메모'] and blank.node.name == '제목 없음.txt')
screenshot.shot(os.path.join(OUT, 'typing_notepad.png'))
for win in list(pm.wm.windows):
    pm.wm.close(win)

# ---------------------------------------------------------------- Chrome
check('normalize: address vs search', browser.normalize('https://www.escape.guide/') == 'escape.guide'
      and browser.normalize('usb 열쇠').startswith('google.com/search?q='))
pm.open_app('browser'); frame()
ch = pm.wm.active.app
ol, ob, ow, oh = ch.omnibox
click(ol + 50, ob + 10)
textbox.focus.insert('escape.guide')
key(SDLK_RETURN); frame()
check('offline: still dino page', not browser.Browser.online and ch.page_title == '인터넷 연결 없음')
browser.Browser.online = True; frame()
check('online: typed address opened', ch.url == 'escape.guide' and ch.page_title == '바탕화면 탈출 가이드')
r, url = next((r, u) for r, u in ch.links if u == 'bug.report')
click(r[0] + 5, r[1] + 5)
check('link click navigates', ch.url == 'bug.report')
bl_, bb_, bw_, bh_ = ch.buttons['back']
click(bl_ + 5, bb_ + 5)
check('back button', ch.url == 'escape.guide' and ch.fwd == ['bug.report'])
hl, hb, hw, hh = ch.buttons['home']
click(hl + 5, hb + 5)
sl, sb, sw, sh = ch.search_rect
click(sl + 100, sb + 10)
check('home search box focused', textbox.focus is ch.search)
textbox.focus.insert('USB')
key(SDLK_RETURN); frame()
check('search results list matching sites', ch.url.startswith('google.com/search')
      and any(u == 'pop.up/wiki/USB' for r, u in ch.links))
screenshot.shot(os.path.join(OUT, 'typing_search.png'))
ol, ob, ow, oh = ch.omnibox
click(ol + 50, ob + 10)
textbox.focus.set_text('없는사이트.zz')
key(SDLK_RETURN); frame()
check('unknown site shows error page', browser.page_of(ch.url)[1][0][0] == 'error')
browser.Browser.online = False
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
