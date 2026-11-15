# Chrome: 탭, 새 창, 주소창, 구글(첫 화면·검색 결과), 유튜브(홈·검색·영상 보기), 게임 속 가상 사이트.
# 인터넷 차단기.exe에서 [켜기]를 누르기 전(Browser.online = False)에는 어디로 가든 공룡 오류 화면이 뜬다.
import math
from urllib.parse import quote, unquote

import gfx
import textbox
import apps
import game_framework
from apps import App, draw_dino, G_BACK, G_FWD, G_REFRESH, G_SEARCH
from context_menu import Item
from config import *

HOME = 'google.com'
YT = 'youtube.com'
TAB_H, BAR_H = 34, 38
BLUE_LINK, GRAY, DARK = (26, 13, 171), (77, 81, 86), (32, 33, 36)
G_COLORS = ((66, 133, 244), (234, 67, 53), (251, 188, 5), (66, 133, 244), (52, 168, 83), (234, 67, 53))
YT_RED, YT_TEXT, YT_GRAY = (255, 0, 0), (15, 15, 15), (96, 96, 96)
GL_MIC, GL_CAMERA, GL_APPS, GL_MORE, GL_CLOSE, GL_PLUS = '\uE720', '\uE722', '\uE8A9', '\uE712', '\uE711', '\uE710'
GL_HOME, GL_MENU, GL_BELL, GL_VIDEO, GL_LIKE, GL_DISLIKE, GL_SHARE, GL_PAUSE = (
    '\uE80F', '\uE700', '\uEA8F', '\uE714', '\uE8E1', '\uE8E0', '\uE72D', '\uE769')

# 주소 → (제목, 검색어, 본문). 본문 줄: ('h1', 글) ('p', 글) ('link', 글, 주소) ('gap',)
SITES = {
    'pop.up/wiki/포인터': ('포인터 - PoP_uP 위키', '포인터 커서 손 주인공 pointer', [
        ('h1', '포인터'),
        ('p', '포인터는 이 PC의 바탕화면에 갇힌 손가락 커서다. 손바닥에 표정이 있고, 화가 나면 테두리가 파랗게 변한다.'),
        ('p', 'Shift를 누르면 공격 모드가 되어 창이 벽처럼 단단해진다. 손가락으로 창 테두리를 세 번 찌르면 창이 깨지고 그 안으로 들어갈 수 있다.'),
        ('p', '창 안에서는 제목 표시줄의 ─ ☐ ✕ 단추를 뜯어 던지거나 먹어서 HP를 회복한다.'),
        ('gap',),
        ('link', 'USB 드라이브 (E:) 문서 보기', 'pop.up/wiki/USB'),
        ('link', '바탕화면 탈출 가이드', 'escape.guide'),
    ]),
    'pop.up/wiki/USB': ('USB 드라이브 - PoP_uP 위키', 'usb 드라이브 e: 잠김 탈출', [
        ('h1', 'USB 드라이브 (E:)'),
        ('p', '이 PC에서 밖으로 나갈 수 있는 유일한 통로. 지금은 접근이 거부되어 있다.'),
        ('p', '잠금을 풀려면 %appdata% 깊은 곳의 권한과 휴지통에 버려진 열쇠 조각이 필요하다는 소문이 있다.'),
        ('gap',),
        ('link', '포인터 문서로 돌아가기', 'pop.up/wiki/포인터'),
    ]),
    'escape.guide': ('바탕화면 탈출 가이드', '탈출 가이드 공략 escape 힌트', [
        ('h1', '바탕화면 탈출 가이드'),
        ('p', '1. 인터넷 차단기.exe - 문서 > 숨겨진 폴더 > 설정. 로그 속 버그를 다 잡으면 [켜기]가 살아난다. (완료!)'),
        ('p', '2. 웹 브라우저 - 텍스트 상자 뒤에 숨은 공룡을 조심할 것. 착지 직후 1초 동안 움직이지 못한다.'),
        ('p', '3. %appdata% - 파일을 빨아들이는 블랙홀이 산다. 스크롤바를 붙잡고 버텨라.'),
        ('p', '4. 휴지통 - 지운 파일을 끌어서 되살리면 자물쇠의 위치를 알 수 있다.'),
        ('p', '5. 나를 압축해서 USB로. 안전하게 제거를 누르면 끝.'),
        ('gap',),
        ('link', '버그 신고 게시판', 'bug.report'),
    ]),
    'bug.report': ('버그 신고 게시판', '버그 벌레 캐럿 윈도우 로고 몬스터 신고', [
        ('h1', '버그 신고 게시판'),
        ('link', '[신고] 폴더 창 구석에서 초록 벌레가 기어 나옵니다 (24)', 'bug.report/1'),
        ('link', '[신고] 깜빡이는 캐럿이 숫자를 쏴요. 9 맞으면 아픕니다 (31)', 'bug.report/2'),
        ('link', '[긴급] 윈도우 로고가 3, 2, 1 세고 터졌습니다 (58)', 'bug.report/3'),
    ]),
    'bug.report/1': ('버그 벌레 - 버그 신고 게시판', '버그 벌레', [
        ('h1', '[신고] 초록 벌레'),
        ('p', '사방에서 천천히 몰려옵니다. 닫기 단추는 일렬로 선 벌레를 세 마리까지 꿰뚫어요.'),
        ('link', '목록으로', 'bug.report'),
    ]),
    'bug.report/2': ('캐럿 - 버그 신고 게시판', '캐럿', [
        ('h1', '[신고] 숫자 쏘는 캐럿'),
        ('p', '빨갛게 떨리면 0.5초 뒤에 쏩니다. 숫자가 곧 데미지라서 0이면 안 아파요.'),
        ('link', '목록으로', 'bug.report'),
    ]),
    'bug.report/3': ('윈도우 로고 - 버그 신고 게시판', '윈도우 로고 폭발', [
        ('h1', '[긴급] 터지는 윈도우 로고'),
        ('p', '최소화 단추를 맞히면 카운트다운이 처음부터 다시 시작됩니다. 터지면 아이콘 발판이 갈라져요.'),
        ('link', '목록으로', 'bug.report'),
    ]),
    'windows.com/stopcode': ('중지 코드 - Windows', '블루스크린 중지 코드 stopcode pointer_hp_zero', [
        ('h1', '중지 코드: POINTER_HP_ZERO'),
        ('p', '포인터의 HP가 0이 되면 PC가 다시 시작됩니다. 다시 시작하면 마지막 체크포인트에서 이어집니다.'),
        ('p', '해결 방법: 들고 있는 창 단추를 Q로 먹으면 HP가 12 회복됩니다 (8초마다).'),
    ]),
    YT: ('YouTube', '유튜브 youtube 동영상 영상', [('p', '동영상을 보고 공유하고 업로드하세요.')]),
}

# 유튜브 영상: (id, 제목, 채널, 그림, 길이(초), 조회수, 올린 때)
VIDEOS = [
    ('v1', '바탕화면 탈출 1편 - 포인터 첫 실황', '포인터TV', 'pointer', 754, '조회수 3.4만회', '2일 전'),
    ('v2', '블루스크린 모음집 (POINTER_HP_ZERO)', '윈도우 박물관', 'bsod', 482, '조회수 120만회', '1년 전'),
    ('v3', '초록 버그 떼 7마리 다 잡기', '버그헌터', 'bug', 347, '조회수 8.9천회', '5시간 전'),
    ('v4', '크롬 공룡 무한 점프 1시간', '오프라인 게이머', 'dino', 3600, '조회수 77만회', '3개월 전'),
    ('v5', '윈도우 10 로고 10시간 보기', '소리 상자', 'windows', 36000, '조회수 410만회', '4년 전'),
    ('v6', '창 테두리 세 번 찌르면 생기는 일', 'PoP_uP 공식', 'crack', 201, '조회수 2.1만회', '1주 전'),
    ('v7', '그림판으로 다리 그려서 건너기', '그림판 장인', 'paint', 375, '조회수 5.5만회', '2주 전'),
    ('v8', '휴지통에서 열쇠 찾는 법 (스포 주의)', '탈출 가이드', 'trash', 549, '조회수 1.4만회', '6일 전'),
]
VIDEO = {v[0]: v for v in VIDEOS}
CHANNEL_COLORS = [(234, 67, 53), (66, 133, 244), (52, 168, 83), (251, 188, 5), (163, 73, 164), (0, 162, 232)]


def clock(sec):
    sec = int(sec)
    h, m, s = sec // 3600, sec // 60 % 60, sec % 60
    return '%d:%02d:%02d' % (h, m, s) if h else '%d:%02d' % (m, s)


def page_of(url):
    """주소 → (탭 제목, 본문). 구글 · 유튜브는 본문 대신 None (따로 그린다)"""
    if url == HOME:
        return 'Google', None
    if url.startswith(HOME + '/search?q='):
        return unquote(url.split('=', 1)[1]) + ' - Google 검색', None
    if url == YT:
        return 'YouTube', None
    if url.startswith(YT + '/results?search_query='):
        return unquote(url.split('=', 1)[1]) + ' - YouTube', None
    if url.startswith(YT + '/watch?v='):
        v = VIDEO.get(url.split('=', 1)[1])
        return (v[1] + ' - YouTube') if v else 'YouTube', None
    if url in SITES:
        title, keys, body = SITES[url]
        return title, body
    return url, [('error', url)]


def search_sites(q):
    words = [w.lower() for w in q.split() if w]
    return [(u, t) for u, (t, keys, body) in SITES.items() if any(w in (t + ' ' + keys).lower() for w in words)]


def search_videos(q):
    words = [w.lower() for w in q.split() if w]
    return [v for v in VIDEOS if any(w in (v[1] + ' ' + v[2] + ' ' + v[3]).lower() for w in words)]


def normalize(text):
    """주소창에 친 글 → 주소. 점이 있고 띄어쓰기가 없으면 주소, 아니면 구글 검색"""
    t = text.strip()
    for scheme in ('https://', 'http://'):
        if t.startswith(scheme):
            t = t[len(scheme):]
    t = t.rstrip('/')
    if t and '.' in t and ' ' not in t:
        return t[4:] if t.startswith('www.') else t
    return HOME + '/search?q=' + quote(t)


# ==================================================================== 영상 그림 (썸네일 · 재생 화면)
def draw_art(kind, l, b, w, h, t=0.0):
    """영상 한 장면. t가 흐르면 움직인다"""
    gfx.push_clip(l, b, w, h)
    if kind == 'bsod':
        gfx.fill(l, b, w, h, (0, 120, 215))
        gfx.text(':(', l + w * 0.12, b + h * 0.62, max(8, int(h * 0.35)), WHITE, FONT_SEMILIGHT)
        gfx.fill(l + w * 0.12, b + h * 0.25, w * 0.6 * min(1, (t * 0.2) % 1.2), max(2, h * 0.05), WHITE)
        gfx.frame(l + w * 0.12, b + h * 0.25, w * 0.6, max(2, h * 0.05), WHITE)
    elif kind == 'dino':
        gfx.fill(l, b, w, h, (247, 247, 247))
        gfx.fill(l, b + h * 0.25, w, 2, (83, 83, 83))
        jump = abs(math.sin(t * 3)) * h * 0.25
        draw_dino(l + w * 0.15, b + h * 0.25 + jump, max(1, int(h / 60)))
        cx = l + w - (t * w * 0.4) % (w + 40)
        gfx.fill(cx, b + h * 0.25, max(4, w * 0.03), h * 0.18, (83, 83, 83))
    elif kind == 'windows':
        gfx.fill(l, b, w, h, (4, 18, 48))
        s = h * 0.18
        g = s * 0.1
        cx, cy = l + w / 2, b + h / 2
        glow = int(140 + 100 * abs(math.sin(t)))
        for dx in (-1, 0):
            for dy in (-1, 0):
                gfx.fill(cx + dx * s + (g if dx == 0 else -g), cy + dy * s + (g if dy == 0 else -g), s, s,
                         (0, glow // 2 + 40, min(255, glow + 60)))
    elif kind == 'bug':
        gfx.fill(l, b, w, h, WHITE)
        k = max(1, h / 112)
        for i in range(7):
            a = i * 0.9 + t * 0.6
            x = l + w / 2 + math.cos(a) * w * 0.3
            y = b + h / 2 + math.sin(a) * h * 0.3
            gfx.fill(x - 6 * k, y - 4 * k, 12 * k, 9 * k, (46, 139, 58))
            gfx.fill(x - 3 * k, y + 5 * k, 6 * k, 3 * k, (46, 139, 58))
            gfx.fill(x - 8 * k, y - 2 * k, 16 * k, 2 * k, (46, 139, 58))
        gfx.fill(l + w / 2 - 6 * k, b + h / 2 - 8 * k, 12 * k, 16 * k, BLACK)
    else:                               # pointer · crack · paint · trash: 포인터가 지나가는 장면
        bg = {'pointer': (11, 30, 70), 'crack': (240, 240, 240), 'paint': WHITE, 'trash': (230, 238, 246)}[kind]
        gfx.fill(l, b, w, h, bg)
        if kind == 'crack':
            gfx.frame(l + w * 0.2, b + h * 0.2, w * 0.6, h * 0.6, (24, 131, 215), 2)
            for n in range(1 + int(t) % 3):
                gfx.line(l + w * 0.8, b + h * 0.5, l + w * (0.86 + 0.04 * n), b + h * (0.3 + 0.15 * n), (40, 40, 40))
        if kind == 'paint':
            for n in range(6):
                gfx.fill(l + w * 0.1 + n * w * 0.13, b + h * (0.3 + 0.06 * math.sin(n + t)), w * 0.12, 4,
                         CHANNEL_COLORS[n])
        if kind == 'trash':
            gfx.icon('recycle_bin', 48, l + w * 0.7, b + h / 2 - 24)
        if kind == 'pointer':
            for n in range(5):
                gfx.icon('folder', 32, l + w * (0.1 + 0.18 * n), b + h * 0.7)
        import sprites
        px = l + (w * 0.1 + t * w * 0.12) % (w * 0.8)
        sprites.pointer().draw('on' if kind == 'crack' else 'off', 'calm', 'run', t, px + 24, b + h * 0.12)
    gfx.pop_clip()


class Tab:
    def __init__(self, url=HOME):
        self.url = url
        self.back, self.fwd = [], []
        self.scroll = 0
        self.video_t = 0.0             # 보고 있는 영상 위치 (초)
        self.playing = False


class Browser(App):
    group = 'browser'
    icon = 'browser'
    size = (1100, 720)
    min_size = (560, 380)
    online = False                      # 구간 1에서 인터넷 차단기.exe의 [켜기]를 누르면 True
    windows_made = 0

    def __init__(self, key='browser'):
        self.key = key                  # 첫 창은 'browser', 새 창은 'browser#2'처럼 따로
        self.tabs = [Tab()]
        self.active = 0
        self.address = textbox.TextBox(self, [''], on_enter=lambda s: self.go(normalize(s)))
        self.search = textbox.TextBox(self, [''], on_enter=self.google)
        self.ysearch = textbox.TextBox(self, [''], on_enter=self.youtube)
        self.buttons, self.links, self.tab_rects = {}, [], []
        self.omnibox = self.search_rect = self.ysearch_rect = self.new_tab_rect = self.menu_rect = (0, 0, 0, 0)
        self.player_rect = (0, 0, 0, 0)
        import fs
        self.node = fs.WEB              # 구간 2 몬스터 · 크롬 공룡은 Chrome 창 페이지 영역에 산다
        self.content = (0, 0, 0, 0)     # 페이지 영역 (몬스터의 무대)
        self.steps = []                 # 창 안에서 밟을 수 있는 발판 (검색창 · 단추 윗면)

    def platforms(self):
        return self.steps

    # ---------------------------------------------------------------- 탭
    @property
    def tab(self):
        return self.tabs[self.active]

    url = property(lambda self: self.tab.url)
    back = property(lambda self: self.tab.back)
    fwd = property(lambda self: self.tab.fwd)

    def new_tab(self, url=HOME):
        self.tabs.append(Tab(url))
        self.active = len(self.tabs) - 1
        self.search.set_text('')
        textbox.set_focus(None)

    def switch_tab(self, i):
        self.active = i
        textbox.set_focus(None)
        url = self.url
        self.search.set_text(unquote(url.split('=', 1)[1]) if url.startswith(HOME + '/search?q=') else '')

    def close_tab(self, i=None):
        import shell
        i = self.active if i is None else i
        if len(self.tabs) == 1:
            textbox.set_focus(None)
            shell.close(self)
            return
        del self.tabs[i]
        self.switch_tab(min(self.active if self.active < i else max(0, self.active - 1), len(self.tabs) - 1))

    def new_window(self):
        import shell
        Browser.windows_made += 1
        me = shell.window_of(self)
        win = shell.wm.open(Browser('browser#%d' % (Browser.windows_made + 1)))
        if me:
            win.x, win.y = me.x + 40, me.y - 40
            win.clamp()
        return win

    def shortcut(self, key):
        """Ctrl + 키. 처리했으면 True"""
        from sdl2 import SDLK_t, SDLK_w, SDLK_n, SDLK_l, SDLK_TAB
        if key == SDLK_t:
            self.new_tab()
        elif key == SDLK_w:
            self.close_tab()
        elif key == SDLK_n:
            self.new_window()
        elif key == SDLK_l:
            self.address.set_text(self.display_url())
            textbox.set_focus(self.address)
        elif key == SDLK_TAB:
            self.switch_tab((self.active + 1) % len(self.tabs))
        else:
            return False
        return True

    @property
    def page_title(self):
        return self.title_of(self.tab)

    def title_of(self, tab):
        return page_of(tab.url)[0] if self.online else '인터넷 연결 없음'

    @property
    def title(self):
        return self.page_title + ' - Chrome'

    # ---------------------------------------------------------------- 이동
    def go(self, url, record=True):
        tab = self.tab
        if record and url != tab.url:
            tab.back.append(tab.url)
            tab.fwd.clear()
        tab.url = url
        tab.scroll = 0
        tab.video_t, tab.playing = 0.0, url.startswith(YT + '/watch')
        textbox.set_focus(None)
        if url.startswith(HOME + '/search?q='):
            self.search.set_text(unquote(url.split('=', 1)[1]))
        elif url == HOME:
            self.search.set_text('')
        if url.startswith(YT + '/results?search_query='):
            self.ysearch.set_text(unquote(url.split('=', 1)[1]))

    def google(self, q):
        if q.strip():
            self.go(normalize(q) if '.' in q and ' ' not in q.strip() else HOME + '/search?q=' + quote(q.strip()))

    def youtube(self, q):
        if q.strip():
            self.go(YT + '/results?search_query=' + quote(q.strip()))

    def go_back(self):
        if self.tab.back:
            self.tab.fwd.append(self.tab.url)
            self.go(self.tab.back.pop(), record=False)

    def go_forward(self):
        if self.tab.fwd:
            self.tab.back.append(self.tab.url)
            self.go(self.tab.fwd.pop(), record=False)

    def display_url(self):
        return '' if self.url == HOME else unquote(self.url)

    # ---------------------------------------------------------------- 마우스
    def mouse_down(self, mx, my, now):
        import shell
        inside = lambda r: r[0] <= mx < r[0] + r[2] and r[1] <= my < r[1] + r[3]
        for r, i, close in self.tab_rects:
            if inside(close):
                self.close_tab(i)
                return
            if inside(r):
                self.switch_tab(i)
                return
        if inside(self.new_tab_rect):
            self.new_tab()
            return
        if inside(self.menu_rect):
            l, b, w, h = self.menu_rect
            shell.show_menu([Item('새 탭              Ctrl+T', self.new_tab),
                             Item('새 창              Ctrl+N', self.new_window),
                             Item('탭 닫기          Ctrl+W', self.close_tab)], l - 200, b)
            return
        for name, r in self.buttons.items():
            if inside(r):
                {'back': self.go_back, 'fwd': self.go_forward, 'refresh': lambda: None,
                 'home': lambda: self.go(HOME)}[name]()
                return
        if inside(self.omnibox):
            self.address.set_text(self.display_url())
            textbox.set_focus(self.address)
            return
        if not self.online:
            return
        if inside(self.search_rect):
            textbox.set_focus(self.search)
            return
        if inside(self.ysearch_rect):
            textbox.set_focus(self.ysearch)
            return
        if inside(self.player_rect):
            self.tab.playing = not self.tab.playing
            return
        for r, url in self.links:
            if inside(r):
                if callable(url):
                    url()
                else:
                    self.go(url)
                return

    def wheel(self, dy):
        self.tab.scroll = max(0, self.tab.scroll - dy * 60)

    # ---------------------------------------------------------------- 그리기
    def draw(self, l, b, w, h, active):
        top = b + h
        tab = self.tab
        if tab.playing:
            v = VIDEO.get(self.url.split('=', 1)[-1])
            tab.video_t = min(v[4], tab.video_t + game_framework.frame_time) if v else 0
            if v and tab.video_t >= v[4]:
                tab.playing = False
        gfx.fill(l, b, w, h, WHITE)
        self.draw_tabs(l, top, w, active)
        y = top - TAB_H - BAR_H
        self.draw_toolbar(l, y, w)
        self.links = []
        self.search_rect = self.ysearch_rect = self.player_rect = (0, 0, 0, 0)
        self.content = (l, b, w, y - b)
        self.steps = []
        gfx.push_clip(l, b, w, y - b)
        url = self.url
        if not self.online:
            self.draw_offline(l, y, w)
        elif url == HOME:
            self.draw_google_home(l, b, w, y)
        elif url.startswith(HOME + '/search?q='):
            self.draw_google_results(l, b, w, y, unquote(url.split('=', 1)[1]))
        elif url == YT or url.startswith(YT + '/results?search_query='):
            q = unquote(url.split('=', 1)[1]) if '=' in url else None
            self.draw_youtube_home(l, b, w, y, q)
        elif url.startswith(YT + '/watch?v='):
            self.draw_youtube_watch(l, b, w, y, url.split('=', 1)[1])
        else:
            self.draw_page(l, b, w, y)
        gfx.pop_clip()

    def favicon(self, url, x, cy):
        if not self.online:
            gfx.icon('browser', 16, x, cy - 8)
        elif url.startswith(HOME):
            gfx.text('G', x + 8, cy, 14, (66, 133, 244), FONT_BOLD, align='center')
        elif url.startswith(YT):
            gfx.round_rect(x, cy - 6, 17, 12, 3, YT_RED)
            gfx.play_triangle(x + 9, cy, 6, WHITE)
        else:
            gfx.symbol('\uE774', x + 8, cy, 13, (95, 99, 104))

    def draw_tabs(self, l, top, w, active):
        gfx.fill(l, top - TAB_H, w, TAB_H, (222, 225, 230) if active else (232, 234, 237))
        n = len(self.tabs)
        tw = int(max(70, min(240, (w - 120) / n)))
        self.tab_rects = []
        x = l + 8
        for i, tab in enumerate(self.tabs):
            on = i == self.active
            if on:
                gfx.round_rect(x, top - TAB_H, tw, 30, 8, WHITE)
                gfx.fill(x, top - TAB_H, tw, 10, WHITE)
            elif i + 1 != self.active and i + 1 < n:
                gfx.fill(x + tw - 1, top - TAB_H + 9, 1, 16, (160, 164, 170))
            cy = top - TAB_H + 15
            self.favicon(tab.url, x + 12, cy)
            title = self.title_of(tab)
            room = tw - 64
            while gfx.text_width(title, 12) > room and len(title) > 1:
                title = title[:-2] + '…'
            gfx.text(title, x + 36, cy, 12, DARK)
            close = (x + tw - 26, cy - 9, 18, 18)
            gfx.symbol(GL_CLOSE, x + tw - 17, cy, 8, (90, 90, 90))
            self.tab_rects.append(((x, top - TAB_H, tw, 30), i, close))
            x += tw
        self.new_tab_rect = (x + 6, top - TAB_H + 4, 26, 26)
        gfx.symbol(GL_PLUS, x + 19, top - TAB_H + 17, 11, (60, 64, 67))

    def draw_toolbar(self, l, y, w):
        cy = y + BAR_H / 2
        self.buttons = {'back': (l + 8, y + 4, 28, 30), 'fwd': (l + 42, y + 4, 28, 30),
                        'refresh': (l + 76, y + 4, 28, 30), 'home': (l + 110, y + 4, 28, 30)}
        on = {'back': bool(self.back), 'fwd': bool(self.fwd), 'refresh': True, 'home': True}
        for name, g in (('back', G_BACK), ('fwd', G_FWD), ('refresh', G_REFRESH), ('home', GL_HOME)):
            bl, bb, bw, bh = self.buttons[name]
            gfx.symbol(g, bl + bw / 2, cy, 12, (90, 90, 90) if on[name] else (190, 190, 190))
        self.omnibox = (l + 148, y + 5, w - 200, 28)
        ol, ob, ow, oh = self.omnibox
        focused = textbox.focus is self.address
        if focused:
            gfx.round_rect(ol, ob, ow, oh, 14, (26, 115, 232))
            gfx.round_rect(ol + 2, ob + 2, ow - 4, oh - 4, 12, WHITE)
            gfx.push_clip(ol, ob, ow - 14, oh)
            self.address.draw(ol + 36, ob + oh, oh, 14, DARK, True)
            gfx.pop_clip()
        else:
            gfx.round_rect(ol, ob, ow, oh, 14, (241, 243, 244))
            shown = self.display_url() or 'Google에서 검색하거나 URL을 입력하세요'
            gfx.text(shown, ol + 36, cy, 14, (60, 60, 60) if self.display_url() else (110, 110, 110))
        gfx.symbol('\uE72E' if self.online else '\uE7BA', ol + 18, cy, 12, (90, 90, 90))
        self.menu_rect = (l + w - 40, y + 4, 30, 30)
        gfx.symbol(GL_MORE, l + w - 26, cy, 12, (90, 90, 90))
        gfx.line(l, y, l + w, y, (218, 220, 224))

    # ---------------------------------------------------------------- 오류 · 가상 사이트
    def draw_offline(self, l, y, w):
        cx = l + max(60, (w - 600) // 2)
        cy = y - 90
        draw_dino(cx, cy - 72, 4)
        gfx.text('인터넷에 연결되어 있지 않음', cx, cy - 110, 24, DARK)
        gfx.text('다음 방법을 시도해 보세요.', cx, cy - 150, 14, (95, 99, 104))
        for i, tip in enumerate(('네트워크 케이블, 모뎀, 라우터 확인', 'Wi-Fi에 다시 연결')):
            gfx.fill(cx + 22, cy - 178 - i * 24, 4, 4, (95, 99, 104))
            gfx.text(tip, cx + 34, cy - 176 - i * 24, 14, (95, 99, 104))
        gfx.text('ERR_INTERNET_DISCONNECTED', cx, cy - 240, 12, (117, 117, 117))

    def draw_page(self, l, b, w, y):
        title, body = page_of(self.url)
        x0, width = l + 48, min(w - 96, 760)
        cy = y - 40 + self.tab.scroll
        for part in body:
            kind = part[0]
            if kind == 'h1':
                gfx.text(part[1], x0, cy, 26, DARK, FONT_BOLD)
                cy -= 50
            elif kind == 'p':
                for ln in gfx.wrap(part[1], width, 15, max_lines=6):
                    gfx.text(ln, x0, cy, 15, DARK)
                    cy -= 24
                cy -= 10
            elif kind == 'gap':
                cy -= 16
            elif kind == 'link':
                tw = gfx.text(part[1], x0, cy, 15, BLUE_LINK)
                gfx.fill(x0, cy - 10, tw, 1, BLUE_LINK)
                self.links.append(((x0, cy - 12, tw, 24), part[2]))
                cy -= 30
            elif kind == 'error':
                gfx.icon('text_file', 48, x0, cy - 40)
                gfx.text('사이트에 연결할 수 없음', x0, cy - 80, 24, DARK)
                gfx.text('%s의 서버 IP 주소를 찾을 수 없습니다.' % part[1], x0, cy - 120, 14, (95, 99, 104))
                gfx.text('ERR_NAME_NOT_RESOLVED', x0, cy - 160, 12, (117, 117, 117))
                cy -= 200

    # ---------------------------------------------------------------- 구글
    def google_logo(self, x, cy, size):
        for ch, c in zip('Google', G_COLORS):
            x += gfx.text(ch, x, cy, size, c, FONT_BOLD)
        return x

    def profile(self, cx, cy, r=16, c=(26, 115, 232)):
        gfx.circle(cx, cy, r, c)
        gfx.text('P', cx, cy, r - 1, WHITE, FONT_BOLD, align='center')

    def search_pill(self, l, b, w, h, box, focused):
        if focused:
            gfx.round_rect(l - 1, b - 3, w + 2, h + 4, h // 2 + 2, (223, 225, 229))
        gfx.round_frame(l, b, w, h, h // 2, (210, 212, 216) if focused else (223, 225, 229))
        gfx.symbol(G_SEARCH, l + 24, b + h / 2, 14, (154, 160, 166))
        gfx.push_clip(l + 44, b, w - 120, h)
        box.draw(l + 50, b + h - (h - 24) / 2, 24, 16, DARK, focused)
        gfx.pop_clip()
        gfx.symbol(GL_MIC, l + w - 70, b + h / 2, 16, (66, 133, 244))
        gfx.symbol(GL_CAMERA, l + w - 34, b + h / 2, 16, (52, 168, 83))

    def draw_google_home(self, l, b, w, y):
        # 위 오른쪽: Gmail · 이미지 · 앱 · 프로필
        gfx.text('Gmail', l + w - 190, y - 30, 13, DARK)
        gfx.text('이미지', l + w - 140, y - 30, 13, DARK)
        gfx.symbol(GL_APPS, l + w - 74, y - 30, 16, (95, 99, 104))
        self.profile(l + w - 36, y - 30)
        cx = l + w / 2
        cy = y - max(150, (y - b) * 0.3)
        logo_w = sum(gfx.text_width(ch, 72, FONT_BOLD) for ch in 'Google')
        self.google_logo(cx - logo_w / 2, cy, 72)
        sw = min(584, w - 80)
        self.search_rect = (cx - sw / 2, cy - 100, sw, 46)
        self.search_pill(*self.search_rect, self.search, textbox.focus is self.search)
        self.steps.append((cx - sw / 2 + 20, cx + sw / 2 - 20, cy - 54))
        for i, label in enumerate(('Google 검색', "I'm Feeling Lucky")):
            bx = cx - 148 + i * 156
            gfx.round_rect(bx, cy - 170, 140, 36, 4, (248, 249, 250))
            gfx.text(label, bx + 70, cy - 152, 14, (60, 64, 67), align='center')
            act = (lambda: self.google(self.search.text)) if i == 0 else (lambda: self.go('escape.guide'))
            self.links.append(((bx, cy - 170, 140, 36), act))
            self.steps.append((bx, bx + 140, cy - 134))
        x = cx - (gfx.text_width('Google 제공 서비스:  English', 13)) / 2
        x += gfx.text('Google 제공 서비스:  ', x, cy - 210, 13, (77, 81, 86))
        gfx.text('English', x, cy - 210, 13, BLUE_LINK)
        # 바로가기: 유튜브 · 탈출 가이드 · 위키 · 버그 신고
        shortcuts = ((YT, 'YouTube'), ('escape.guide', '탈출 가이드'), ('pop.up/wiki/포인터', 'PoP_uP 위키'),
                     ('bug.report', '버그 신고'), (None, '바로가기 추가'))
        sx = cx - len(shortcuts) * 56
        for i, (u, label) in enumerate(shortcuts):
            bx, by = sx + i * 112 + 16, cy - 330
            gfx.circle(bx + 40, by + 70, 24, (241, 243, 244))
            if u == YT:
                gfx.round_rect(bx + 28, by + 62, 25, 17, 4, YT_RED)
                gfx.play_triangle(bx + 41, by + 70, 8, WHITE)
            elif u is None:
                gfx.symbol(GL_PLUS, bx + 40, by + 70, 14, DARK)
            else:
                gfx.text(u[:1].upper(), bx + 40, by + 70, 16, (95, 99, 104), FONT_BOLD, align='center')
            gfx.text(label, bx + 40, by + 30, 12, DARK, align='center')
            if u:
                self.links.append(((bx, by + 16, 80, 84), u))
        # 바닥: 대한민국 + 링크들
        gfx.fill(l, b, w, 92, (242, 242, 242))
        gfx.line(l, b + 46, l + w, b + 46, (218, 220, 224))
        gfx.text('대한민국', l + 30, b + 69, 14, (112, 117, 122))
        x = l + 30
        for label in ('광고', '비즈니스', '검색의 원리'):
            x += gfx.text(label, x, b + 23, 14, (112, 117, 122)) + 28
        x = l + w - 30
        for label in ('설정', '약관', '개인정보처리방침'):
            x -= gfx.text_width(label, 14)
            gfx.text(label, x, b + 23, 14, (112, 117, 122))
            x -= 28

    def draw_google_results(self, l, b, w, y, q):
        top = y + self.tab.scroll
        self.google_logo(l + 28, top - 38, 28)
        sw = min(690, w - 260)
        self.search_rect = (l + 170, top - 60, sw, 44)
        self.search_pill(*self.search_rect, self.search, textbox.focus is self.search)
        gfx.symbol(GL_APPS, l + w - 74, top - 38, 16, (95, 99, 104))
        self.profile(l + w - 36, top - 38)
        # 검색 종류 탭
        x = l + 180
        for i, label in enumerate(('전체', '이미지', '동영상', '뉴스', '쇼핑', '더보기')):
            tw = gfx.text(label, x, top - 90, 14, (26, 115, 232) if i == 0 else (95, 99, 104))
            if i == 0:
                gfx.fill(x - 4, top - 108, tw + 8, 3, (26, 115, 232))
            if label == '동영상':
                self.links.append(((x - 4, top - 106, tw + 8, 30), YT + '/results?search_query=' + quote(q)))
            x += tw + 30
        gfx.line(l, top - 108, l + w, top - 108, (235, 235, 235))
        sites = search_sites(q)
        videos = search_videos(q)
        x0, width = l + 180, min(650, w - 220)
        gfx.text('검색결과 약 %d개 (0.%02d초)' % (len(sites) + len(videos), 20 + len(q) % 60), x0, top - 132,
                 13, (112, 117, 122))
        cy = top - 172
        for k, hit in enumerate(sites + [None]):
            if k == min(1, len(sites)) and videos:
                cy = self.video_block(videos, x0, cy)
            if hit is None:
                break
            u, t = hit
            name = u.split('/')[0]
            gfx.circle(x0 + 13, cy, 13, (241, 243, 244))
            gfx.text(name[:1].upper(), x0 + 13, cy, 12, (95, 99, 104), FONT_BOLD, align='center')
            gfx.text(name, x0 + 34, cy + 8, 14, DARK)
            gfx.text('https://' + u.replace('/', ' › '), x0 + 34, cy - 10, 12, GRAY)
            cy -= 40
            tw = gfx.text(t, x0, cy, 20, BLUE_LINK)
            self.links.append(((x0, cy - 14, tw, 28), u))
            cy -= 26
            snippet = next((p[1] for p in SITES[u][2] if p[0] == 'p'), t)
            for ln in gfx.wrap(snippet, width, 14, max_lines=2):
                gfx.text(ln, x0, cy, 14, GRAY)
                cy -= 22
            cy -= 22
        if not sites and not videos:
            gfx.text("'%s'에 대한 검색결과가 없습니다." % q, x0, cy, 15, DARK)
            gfx.text('검색어의 철자가 정확한지 확인하거나 다른 검색어를 입력해 보세요.', x0, cy - 30, 14, GRAY)

    def video_block(self, videos, x0, cy):
        """검색 결과 사이의 '동영상' 묶음 (썸네일 3개). 다음 줄 y를 돌려준다"""
        gfx.text('동영상', x0, cy, 20, DARK)
        cy -= 24
        for i, v in enumerate(videos[:3]):
            tl, tb = x0 + i * 214, cy - 112
            draw_art(v[3], tl, tb, 200, 112)
            gfx.round_rect(tl + 158, tb + 6, 38, 18, 3, (0, 0, 0, 200))
            gfx.text(clock(v[4]), tl + 177, tb + 15, 11, WHITE, align='center')
            for j, ln in enumerate(gfx.wrap(v[1], 200, 14, max_lines=2)):
                gfx.text(ln, tl, tb - 18 - j * 20, 14, BLUE_LINK)
            gfx.text('YouTube · ' + v[2], tl, tb - 62, 12, GRAY)
            self.links.append(((tl, tb - 70, 200, 182), YT + '/watch?v=' + v[0]))
        return cy - 220

    # ---------------------------------------------------------------- 유튜브
    def youtube_logo(self, x, cy):
        gfx.round_rect(x, cy - 10, 29, 20, 5, YT_RED)
        gfx.play_triangle(x + 15, cy, 9, WHITE)
        tw = gfx.text('YouTube', x + 33, cy, 19, YT_TEXT, FONT_BOLD)
        gfx.text('KR', x + 35 + tw, cy + 8, 9, YT_GRAY)
        self.links.append(((x, cy - 12, tw + 50, 24), YT))

    def youtube_bar(self, l, w, top):
        gfx.symbol(GL_MENU, l + 28, top - 28, 16, YT_TEXT)
        self.youtube_logo(l + 58, top - 28)
        sw = max(160, min(560, w - 520))
        sx = l + w / 2 - sw / 2 - 32
        self.ysearch_rect = (sx, top - 46, sw, 38)
        focused = textbox.focus is self.ysearch
        gfx.round_frame(sx, top - 46, sw + 64, 38, 19, (26, 115, 232) if focused else (211, 211, 211))
        gfx.round_rect(sx + sw, top - 45, 63, 36, 18, (248, 248, 248))
        gfx.fill(sx + sw, top - 45, 20, 36, (248, 248, 248))
        gfx.fill(sx + sw, top - 45, 1, 36, (211, 211, 211))
        gfx.symbol(G_SEARCH, sx + sw + 30, top - 27, 16, YT_TEXT)
        gfx.push_clip(sx + 16, top - 46, sw - 24, 38)
        if self.ysearch.text or focused:
            self.ysearch.draw(sx + 18, top - 15, 24, 15, YT_TEXT, focused)
        else:
            gfx.text('검색', sx + 18, top - 27, 15, (136, 136, 136))
        gfx.pop_clip()
        gfx.circle(sx + sw + 100, top - 27, 19, (242, 242, 242))
        gfx.symbol(GL_MIC, sx + sw + 100, top - 27, 15, YT_TEXT)
        gfx.symbol(GL_VIDEO, l + w - 120, top - 28, 17, YT_TEXT)
        gfx.symbol(GL_BELL, l + w - 76, top - 28, 17, YT_TEXT)
        self.profile(l + w - 34, top - 28, 15, (163, 73, 164))

    def thumb(self, v, x, top, tw, th, t=0.0):
        draw_art(v[3], x, top - th, tw, th, t)
        gfx.round_rect(x + tw - 50, top - th + 6, 44, 20, 4, (0, 0, 0, 210))
        gfx.text(clock(v[4]), x + tw - 28, top - th + 16, 12, WHITE, FONT_BOLD, align='center')

    def avatar(self, v, cx, cy, r):
        gfx.circle(cx, cy, r, CHANNEL_COLORS[VIDEOS.index(v) % len(CHANNEL_COLORS)])
        gfx.text(v[2][:1], cx, cy, max(9, int(r * 0.7)), WHITE, FONT_BOLD, align='center')

    def video_card(self, v, x, top, cw):
        th = int(cw * 9 / 16)
        self.thumb(v, x, top, cw, th)
        self.avatar(v, x + 18, top - th - 30, 18)
        lines = gfx.wrap(v[1], cw - 50, 15, FONT_BOLD, max_lines=2)
        for j, ln in enumerate(lines):
            gfx.text(ln, x + 46, top - th - 22 - j * 22, 15, YT_TEXT, FONT_BOLD)
        y = top - th - 22 - len(lines) * 22
        gfx.text(v[2], x + 46, y - 2, 13, YT_GRAY)
        gfx.text('%s · %s' % (v[5], v[6]), x + 46, y - 22, 13, YT_GRAY)
        self.links.append(((x, top - th - 100, cw, th + 100), YT + '/watch?v=' + v[0]))

    def draw_youtube_home(self, l, b, w, y, q):
        top = y + self.tab.scroll
        self.youtube_bar(l, w, top)
        # 왼쪽 메뉴
        side = 220 if w > 900 else 0
        if side:
            menu = ((GL_HOME, '홈'), ('\uE8B2', 'Shorts'), ('\uE8F1', '구독'), (None, None),
                    ('\uE77B', '내 페이지'), ('\uE81C', '시청 기록'), ('\uE8A5', '재생목록'), ('\uE823', '나중에 볼 동영상'))
            for i, (g, label) in enumerate(menu):
                yy = top - 92 - i * 44
                if g is None:
                    gfx.line(l + 12, yy + 10, l + side - 12, yy + 10, (229, 229, 229))
                    continue
                home = i == 0 and q is None
                if home:
                    gfx.round_rect(l + 12, yy - 20, side - 24, 40, 10, (242, 242, 242))
                gfx.symbol(g, l + 40, yy, 17, YT_TEXT)
                gfx.text(label, l + 76, yy, 14, YT_TEXT, FONT_BOLD if home else FONT)
                if i == 0:
                    self.links.append(((l + 12, yy - 20, side - 24, 40), YT))
        x0 = l + side + 16
        if q is None:
            # 주제 칩
            cx = x0
            for i, label in enumerate(('전체', '게임', '음악', '실시간', '윈도우', '최근에 업로드된 동영상')):
                tw = gfx.text_width(label, 14) + 24
                gfx.round_rect(cx, top - 102, tw, 32, 8, YT_TEXT if i == 0 else (242, 242, 242))
                gfx.text(label, cx + tw / 2, top - 86, 14, WHITE if i == 0 else YT_TEXT, align='center')
                cx += tw + 12
            cols = max(1, (w - side - 32) // 300)
            cw = (w - side - 32 - (cols - 1) * 16) // cols
            row_top = top - 126
            for i, v in enumerate(VIDEOS):
                if i and i % cols == 0:
                    row_top -= int(cw * 9 / 16) + 124
                self.video_card(v, x0 + (i % cols) * (cw + 16), row_top, cw)
        else:
            found = search_videos(q)
            cy = top - 80
            if not found:
                gfx.text("'%s'에 대한 검색결과가 없습니다." % q, x0, cy - 20, 16, YT_TEXT)
                gfx.text('다른 검색어를 사용해 보거나 검색 필터를 삭제하세요.', x0, cy - 50, 14, YT_GRAY)
            tw_ = min(360, (w - side) // 2)
            th = int(tw_ * 9 / 16)
            for v in found:
                self.thumb(v, x0, cy, tw_, th)
                tx = x0 + tw_ + 16
                gfx.text(v[1], tx, cy - 14, 18, YT_TEXT)
                gfx.text('%s · %s' % (v[5], v[6]), tx, cy - 40, 12, YT_GRAY)
                self.avatar(v, tx + 12, cy - 68, 12)
                gfx.text(v[2], tx + 32, cy - 68, 12, YT_GRAY)
                self.links.append(((x0, cy - th, w - side - 32, th), YT + '/watch?v=' + v[0]))
                cy -= th + 16

    def draw_youtube_watch(self, l, b, w, y, vid):
        v = VIDEO.get(vid)
        top = y + self.tab.scroll
        self.youtube_bar(l, w, top)
        if v is None:
            gfx.text('동영상을 재생할 수 없습니다.', l + 40, top - 100, 18, YT_TEXT)
            return
        tab = self.tab
        side = 400 if w > 1000 else 0
        pw = w - side - 48 - (16 if side else 0)
        ph = int(pw * 9 / 16)
        px, pt = l + 24, top - 70
        self.player_rect = (px, pt - ph + 40, pw, ph - 40)
        gfx.fill(px, pt - ph, pw, ph, BLACK)
        draw_art(v[3], px, pt - ph, pw, ph, tab.video_t)
        # 아래 조작 막대: 진행 막대, 재생/일시정지, 시간
        k = tab.video_t / max(1, v[4])
        gfx.fill(px, pt - ph, pw, 44, (0, 0, 0, 140))
        gfx.fill(px + 12, pt - ph + 40, pw - 24, 4, (255, 255, 255, 90))
        gfx.fill(px + 12, pt - ph + 40, (pw - 24) * k, 4, YT_RED)
        gfx.circle(px + 12 + (pw - 24) * k, pt - ph + 42, 6, YT_RED)
        if tab.playing:
            gfx.symbol(GL_PAUSE, px + 30, pt - ph + 18, 16, WHITE)
        else:
            gfx.play_triangle(px + 30, pt - ph + 18, 16, WHITE)
            gfx.round_rect(px + pw / 2 - 34, pt - ph / 2 - 24, 68, 48, 12, (255, 0, 0, 230))
            gfx.play_triangle(px + pw / 2 + 2, pt - ph / 2, 22, WHITE)
        self.links.append(((px + 14, pt - ph + 2, 34, 32), lambda: setattr(tab, 'playing', not tab.playing)))
        gfx.text('%s / %s' % (clock(tab.video_t), clock(v[4])), px + 56, pt - ph + 18, 13, WHITE)
        # 제목 · 채널 · 버튼
        cy = pt - ph - 30
        gfx.text(v[1], px, cy, 20, YT_TEXT, FONT_BOLD)
        cy -= 46
        self.avatar(v, px + 20, cy, 20)
        gfx.text(v[2], px + 50, cy + 9, 15, YT_TEXT, FONT_BOLD)
        gfx.text('구독자 %d.%d만명' % (len(v[2]) + 1, len(v[1]) % 10), px + 50, cy - 11, 12, YT_GRAY)
        sx = px + 60 + max(gfx.text_width(v[2], 15, FONT_BOLD), 90) + 20
        gfx.round_rect(sx, cy - 18, 70, 36, 18, YT_TEXT)
        gfx.text('구독', sx + 35, cy, 14, WHITE, FONT_BOLD, align='center')
        bx = px + pw - 250
        gfx.round_rect(bx, cy - 18, 130, 36, 18, (242, 242, 242))
        gfx.symbol(GL_LIKE, bx + 22, cy, 15, YT_TEXT)
        gfx.text('%d천' % (len(v[1]) * 3), bx + 40, cy, 14, YT_TEXT, FONT_BOLD)
        gfx.fill(bx + 86, cy - 11, 1, 22, (204, 204, 204))
        gfx.symbol(GL_DISLIKE, bx + 106, cy, 15, YT_TEXT)
        gfx.round_rect(bx + 140, cy - 18, 100, 36, 18, (242, 242, 242))
        gfx.symbol(GL_SHARE, bx + 164, cy, 14, YT_TEXT)
        gfx.text('공유', bx + 182, cy, 14, YT_TEXT, FONT_BOLD)
        # 설명
        cy -= 34
        gfx.round_rect(px, cy - 74, pw, 74, 12, (242, 242, 242))
        gfx.text('%s  %s' % (v[5], v[6]), px + 14, cy - 20, 14, YT_TEXT, FONT_BOLD)
        gfx.text('PoP_uP 세계관 영상입니다. 좋아요와 구독 부탁드립니다!', px + 14, cy - 48, 14, YT_TEXT)
        # 오른쪽: 다음 동영상
        if side:
            rx, ry = l + w - side - 16, top - 70
            for o in VIDEOS:
                if o is v:
                    continue
                self.thumb(o, rx, ry, 168, 94)
                for j, ln in enumerate(gfx.wrap(o[1], side - 184, 14, FONT_BOLD, max_lines=2)):
                    gfx.text(ln, rx + 178, ry - 12 - j * 20, 14, YT_TEXT, FONT_BOLD)
                gfx.text(o[2], rx + 178, ry - 58, 12, YT_GRAY)
                gfx.text('%s · %s' % (o[5], o[6]), rx + 178, ry - 76, 12, YT_GRAY)
                self.links.append(((rx, ry - 94, side, 94), YT + '/watch?v=' + o[0]))
                ry -= 104


apps.Browser = Browser                  # 예전 이름으로 부르는 곳(구간 진행 · 테스트)도 이 Chrome을 쓰게
apps.APPS['browser'] = Browser
