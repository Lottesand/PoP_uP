import os
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'game'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
from pico2d import open_canvas, close_canvas, hide_lattice, clear_canvas
from sdl2 import SDLK_RETURN, SDLK_t, SDLK_w, SDLK_n, SDLK_l, KMOD_LCTRL, SDL_KEYDOWN
import gfx, textbox, game_framework, play_mode as pm, screenshot
import browser
from config import *

open_canvas(W, H); hide_lattice(); gfx.init(); textbox.init(); pm.TUTORIAL = False; pm.level.SPAWNING = False; pm.init()
game_framework.frame_time = 1 / 60
ok = []


def check(n, c):
    ok.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n)


def frame():
    clear_canvas(); pm.render()


def ctrl(sym):
    ev = textbox.Event(SDL_KEYDOWN)
    ev.key, ev.mod, ev.repeat = sym, KMOD_LCTRL, 0
    return pm.ctrl_shortcut(ev)


def enter():
    ev = textbox.Event(SDL_KEYDOWN)
    ev.key, ev.mod = SDLK_RETURN, 0
    pm.typing_key(ev)
    frame()


def click(x, y):
    pm.mouse_down(x, y); pm.mouse_up(x, y); frame()


def click_rect(r):
    click(r[0] + r[2] / 2, r[1] + r[3] / 2)


def link_to(app, prefix):
    return next(r for r, u in app.links if isinstance(u, str) and u.startswith(prefix))


browser.Browser.online = True
pm.open_app('browser'); win = pm.wm.active
win.x, win.y = 160, 120
frame()
ch = win.app
check('opens on the Google home page', ch.url == 'google.com' and ch.page_title == 'Google')
screenshot.shot(os.path.join(OUT, 'chrome_google.png'))

# 구글 검색 → 결과 페이지 (사이트 + 동영상)
click_rect(ch.search_rect)
check('google search box takes focus', textbox.focus is ch.search)
textbox.focus.insert('버그')
enter()
check('google results page', ch.url.startswith('google.com/search?q=') and ch.page_title == '버그 - Google 검색')
check('results list sites and youtube videos', any(u == 'bug.report' for r, u in ch.links)
      and any(isinstance(u, str) and u.startswith('youtube.com/watch') for r, u in ch.links))
screenshot.shot(os.path.join(OUT, 'chrome_results.png'))

# 결과의 동영상 → 유튜브 보기 화면, 재생 중
click_rect(link_to(ch, 'youtube.com/watch'))
check('video result opens the watch page', ch.url == 'youtube.com/watch?v=v3' and ch.tab.playing)
for _ in range(90):
    frame()
check('video time advances while playing', 1.2 < ch.tab.video_t < 1.8)
click_rect(ch.player_rect)
t = ch.tab.video_t
for _ in range(30):
    frame()
check('click on the player pauses', not ch.tab.playing and ch.tab.video_t == t)
screenshot.shot(os.path.join(OUT, 'chrome_watch.png'))

# 새 탭(+ 단추) → 주소창에 youtube.com
tabs_before = len(ch.tabs)
click_rect(ch.new_tab_rect)
check('+ opens a new tab on Google', len(ch.tabs) == tabs_before + 1 and ch.active == 1 and ch.url == 'google.com')
check('Ctrl+L focuses the address bar', ctrl(SDLK_l) and textbox.focus is ch.address)
textbox.focus.set_text('youtube.com')
enter()
check('youtube home', ch.url == 'youtube.com' and ch.page_title == 'YouTube'
      and sum(1 for r, u in ch.links if isinstance(u, str) and u.startswith('youtube.com/watch')) == len(browser.VIDEOS))
screenshot.shot(os.path.join(OUT, 'chrome_youtube.png'))

# 유튜브 검색
click_rect(ch.ysearch_rect)
check('youtube search box focused', textbox.focus is ch.ysearch)
textbox.focus.insert('공룡')
enter()
check('youtube search results', ch.url.startswith('youtube.com/results') and
      [u for r, u in ch.links if isinstance(u, str) and u.startswith('youtube.com/watch')] == ['youtube.com/watch?v=v4'])
screenshot.shot(os.path.join(OUT, 'chrome_ytsearch.png'))

# 탭 전환 · 탭마다 따로 기록
click_rect(ch.tab_rects[0][0])
check('click a tab switches to it', ch.active == 0 and ch.url == 'youtube.com/watch?v=v3')
check('each tab keeps its own history', ch.back[-1].startswith('google.com/search') and
      ch.tabs[1].back == ['google.com', 'youtube.com'])
check('Ctrl+T new tab', ctrl(SDLK_t) and len(ch.tabs) == 3 and ch.active == 2)
check('Ctrl+W closes the tab', ctrl(SDLK_w) and len(ch.tabs) == 2)
frame()
r, i, close = ch.tab_rects[1]
click_rect(close)
check('tab x closes that tab', len(ch.tabs) == 1 and ch.url == 'youtube.com/watch?v=v3')

# 새 창
n = len(pm.wm.windows)
check('Ctrl+N opens a new Chrome window', ctrl(SDLK_n) and len(pm.wm.windows) == n + 1)
win2 = pm.wm.active
check('new window is a separate Chrome', win2.app is not ch and win2.app.group == 'browser'
      and win2.app.url == 'google.com' and win2.x == win.x + 40)
frame()
# ⋮ 메뉴 → 새 창
click_rect(win2.app.menu_rect)
check('menu opens', pm.shell.menu is not None)
pm.shell.close_menu()
pm.shell.wm.close(win2)

# 마지막 탭을 닫으면 창이 닫힌다
pm.wm.focus(win)
ctrl(SDLK_w)
check('closing the last tab closes the window', win not in pm.wm.windows)
browser.Browser.online = False
close_canvas()
print('%d/%d passed' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
