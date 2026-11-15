# Chrome: 주소창에 입력하고, 검색하고, 링크를 눌러 게임 속 가상 웹사이트를 돌아다닌다.
# 인터넷 차단기를 끄기 전(Browser.online = False)에는 어디로 가든 공룡 오류 화면이 뜬다.
from urllib.parse import quote, unquote

import gfx
import textbox
import apps
from apps import App, draw_dino, G_BACK, G_FWD, G_REFRESH, G_SEARCH
from config import *

HOME = 'google.com'
BLUE_LINK, GREEN_URL, GRAY = (26, 13, 171), (0, 102, 33), (77, 81, 86)
TAB_H, BAR_H = 34, 38

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
        ('p', '1. 인터넷 차단기 끄기 - 문서 > 숨겨진 폴더 > 설정. 차단기 위에 올라서면 내려간다. (완료!)'),
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
}


def page_of(url):
    """주소 → (제목, 본문). 검색 주소면 검색 결과, 모르는 주소면 오류 화면"""
    if url == HOME:
        return '새 탭', None
    if url.startswith(HOME + '/search?q='):
        q = unquote(url.split('=', 1)[1])
        words = [w.lower() for w in q.split() if w]
        hits = [(u, t) for u, (t, keys, body) in SITES.items()
                if any(w in (t + ' ' + keys).lower() for w in words)]
        body = [('stat', '검색결과 약 %d개' % len(hits))]
        for u, t in hits:
            snippet = next((x[1] for x in SITES[u][2] if x[0] == 'p'), '')
            body += [('result', t, u, snippet)]
        if not hits:
            body += [('p', "'%s'와(과) 일치하는 검색결과가 없습니다." % q), ('link', '바탕화면 탈출 가이드', 'escape.guide')]
        return q + ' - Google 검색', body
    if url in SITES:
        title, keys, body = SITES[url]
        return title, body
    return url, [('error', url)]


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


class Browser(App):
    group = 'browser'
    key, icon = 'browser', 'browser'
    size = (1000, 640)
    min_size = (520, 360)
    online = False                      # 구간 1에서 인터넷 차단기를 끄면 True

    def __init__(self):
        self.url = HOME
        self.back, self.fwd = [], []
        self.scroll = 0
        self.address = textbox.TextBox(self, [''], on_enter=lambda s: self.go(normalize(s)))
        self.search = textbox.TextBox(self, [''], on_enter=lambda s: s.strip() and self.go(normalize(s)))
        self.buttons, self.links = {}, []
        self.omnibox = self.search_rect = (0, 0, 0, 0)

    @property
    def page_title(self):
        return page_of(self.url)[0] if self.online else '인터넷 연결 없음'

    @property
    def title(self):
        return self.page_title + ' - Chrome'

    # ---------------------------------------------------------------- 이동
    def go(self, url, record=True):
        if record and url != self.url:
            self.back.append(self.url)
            self.fwd.clear()
        self.url = url
        self.scroll = 0
        textbox.set_focus(None)

    def go_back(self):
        if self.back:
            self.fwd.append(self.url)
            self.go(self.back.pop(), record=False)

    def go_forward(self):
        if self.fwd:
            self.back.append(self.url)
            self.go(self.fwd.pop(), record=False)

    # ---------------------------------------------------------------- 마우스
    def mouse_down(self, mx, my, now):
        inside = lambda r: r[0] <= mx < r[0] + r[2] and r[1] <= my < r[1] + r[3]
        for name, r in self.buttons.items():
            if inside(r):
                {'back': self.go_back, 'fwd': self.go_forward, 'refresh': lambda: None,
                 'home': lambda: self.go(HOME)}[name]()
                return
        if inside(self.omnibox):
            self.address.set_text(self.display_url())
            textbox.set_focus(self.address)
            return
        if self.url == HOME and self.online and inside(self.search_rect):
            textbox.set_focus(self.search)
            return
        for r, url in self.links:
            if inside(r):
                self.go(url)
                return

    def wheel(self, dy):
        self.scroll = max(0, self.scroll - dy * 60)

    def display_url(self):
        return '' if self.url == HOME else self.url

    # ---------------------------------------------------------------- 그리기
    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, WHITE)
        self.draw_tabs(l, top, w, active)
        y = top - TAB_H - BAR_H
        self.draw_toolbar(l, y, w)
        self.links = []
        gfx.push_clip(l, b, w, y - b)
        if not self.online:
            self.draw_offline(l, y, w)
        elif self.url == HOME:
            self.draw_home(l, b, w, y)
        else:
            self.draw_page(l, b, w, y)
        gfx.pop_clip()

    def draw_tabs(self, l, top, w, active):
        gfx.fill(l, top - TAB_H, w, TAB_H, (222, 225, 230) if active else (232, 234, 237))
        gfx.fill(l + 8, top - TAB_H, 240, 28, WHITE)
        gfx.icon('browser', 16, l + 20, top - 28)
        title = self.page_title
        while gfx.text_width(title, 12) > 180 and len(title) > 2:
            title = title[:-2] + '…'
        gfx.text(title, l + 44, top - 20, 12)
        gfx.symbol('\uE711', l + 232, top - 20, 8, (90, 90, 90))
        gfx.symbol('\uE710', l + 266, top - 20, 10, (90, 90, 90))

    def draw_toolbar(self, l, y, w):
        cy = y + BAR_H / 2
        self.buttons = {'back': (l + 8, y + 4, 28, 30), 'fwd': (l + 42, y + 4, 28, 30),
                        'refresh': (l + 76, y + 4, 28, 30), 'home': (l + 110, y + 4, 28, 30)}
        on = {'back': bool(self.back), 'fwd': bool(self.fwd), 'refresh': True, 'home': True}
        for name, g in (('back', G_BACK), ('fwd', G_FWD), ('refresh', G_REFRESH), ('home', '\uE80F')):
            bl, bb, bw, bh = self.buttons[name]
            gfx.symbol(g, bl + bw / 2, cy, 12, (90, 90, 90) if on[name] else (190, 190, 190))
        self.omnibox = (l + 148, y + 5, w - 200, 28)
        ol, ob, ow, oh = self.omnibox
        focused = textbox.focus is self.address
        gfx.fill(ol, ob, ow, oh, WHITE if focused else (241, 243, 244))
        if focused:
            gfx.frame(ol, ob, ow, oh, (26, 115, 232), 2)
            gfx.push_clip(ol, ob, ow, oh)
            self.address.draw(ol + 36, ob + oh, oh, 14, (32, 33, 36), True)
            gfx.pop_clip()
        else:
            shown = self.display_url() or 'Google에서 검색하거나 URL을 입력하세요'
            gfx.text(shown, ol + 36, cy, 14, (60, 60, 60) if self.display_url() else (110, 110, 110))
        gfx.symbol('\uE946' if self.online else '\uE7BA', ol + 18, cy, 12, (90, 90, 90))
        gfx.symbol('\uE712', l + w - 26, cy, 12, (90, 90, 90))
        gfx.line(l, y, l + w, y, (218, 220, 224))

    def draw_offline(self, l, y, w):
        cx = l + max(60, (w - 600) // 2)
        cy = y - 90
        draw_dino(cx, cy - 72, 4)
        gfx.text('인터넷에 연결되어 있지 않음', cx, cy - 110, 24, (32, 33, 36))
        gfx.text('다음 방법을 시도해 보세요.', cx, cy - 150, 14, (95, 99, 104))
        for i, tip in enumerate(('네트워크 케이블, 모뎀, 라우터 확인', 'Wi-Fi에 다시 연결')):
            gfx.fill(cx + 22, cy - 178 - i * 24, 4, 4, (95, 99, 104))
            gfx.text(tip, cx + 34, cy - 176 - i * 24, 14, (95, 99, 104))
        gfx.text('ERR_INTERNET_DISCONNECTED', cx, cy - 240, 12, (117, 117, 117))

    def draw_home(self, l, b, w, y):
        cx, cy = l + w / 2, b + (y - b) * 0.62
        x = cx - 130
        for ch, c in zip('Google', ((66, 133, 244), (234, 67, 53), (251, 188, 5), (66, 133, 244), (52, 168, 83),
                                    (234, 67, 53))):
            x += gfx.text(ch, x, cy, 64, c, FONT_BOLD)
        self.search_rect = (cx - 280, cy - 96, 560, 44)
        sl, sb, sw, sh = self.search_rect
        focused = textbox.focus is self.search
        gfx.fill(sl, sb, sw, sh, WHITE)
        gfx.frame(sl, sb, sw, sh, (26, 115, 232) if focused else (223, 225, 229), 2 if focused else 1)
        gfx.symbol(G_SEARCH, sl + 24, sb + sh / 2, 14, (154, 160, 166))
        gfx.push_clip(sl + 44, sb, sw - 60, sh)
        self.search.draw(sl + 48, sb + sh - 6, sh - 12, 16, (32, 33, 36), focused)
        gfx.pop_clip()
        for i, label in enumerate(('Google 검색', '바탕화면 탈출 가이드')):
            bx = cx - 150 + i * 160
            gfx.fill(bx, sb - 64, 140, 36, (248, 249, 250))
            gfx.text(label, bx + 70, sb - 46, 13, (60, 64, 67), align='center')
            if i == 1:
                self.links.append(((bx, sb - 64, 140, 36), 'escape.guide'))
            else:
                self.links.append(((bx, sb - 64, 140, 36), normalize(self.search.text)))

    def draw_page(self, l, b, w, y):
        title, body = page_of(self.url)
        x0, width = l + 48, min(w - 96, 760)
        cy = y - 40 + self.scroll
        for part in body:
            kind = part[0]
            if kind == 'h1':
                gfx.text(part[1], x0, cy, 26, (32, 33, 36), FONT_BOLD)
                cy -= 50
            elif kind == 'p':
                for ln in gfx.wrap(part[1], width, 15, max_lines=6):
                    gfx.text(ln, x0, cy, 15, (32, 33, 36))
                    cy -= 24
                cy -= 10
            elif kind == 'gap':
                cy -= 16
            elif kind == 'stat':
                gfx.text(part[1], x0, cy, 13, (112, 117, 122))
                cy -= 36
            elif kind == 'link':
                tw = gfx.text(part[1], x0, cy, 15, BLUE_LINK)
                gfx.fill(x0, cy - 10, tw, 1, BLUE_LINK)
                self.links.append(((x0, cy - 12, tw, 24), part[2]))
                cy -= 30
            elif kind == 'result':
                gfx.text('https://' + part[2], x0, cy, 12, GRAY)
                cy -= 26
                tw = gfx.text(part[1], x0, cy, 19, BLUE_LINK)
                self.links.append(((x0, cy - 14, tw, 28), part[2]))
                cy -= 26
                for ln in gfx.wrap(part[3], width, 13, max_lines=2):
                    gfx.text(ln, x0, cy, 13, GRAY)
                    cy -= 20
                cy -= 20
            elif kind == 'error':
                gfx.icon('text_file', 48, x0, cy - 40)
                gfx.text('사이트에 연결할 수 없음', x0, cy - 80, 24, (32, 33, 36))
                gfx.text('%s의 서버 IP 주소를 찾을 수 없습니다.' % part[1], x0, cy - 120, 14, (95, 99, 104))
                gfx.text('ERR_NAME_NOT_RESOLVED', x0, cy - 160, 12, (117, 117, 117))
                cy -= 200


apps.Browser = Browser                  # 예전 이름으로 부르는 곳(구간 진행 · 테스트)도 이 Chrome을 쓰게
apps.APPS['browser'] = Browser
