# 인터넷 차단기.exe: 윈도우 폼 프로그램처럼 생긴 창.
# 로그 상자 안에 버그들이 산다 (몬스터의 폴더 = fs.BREAKER, 내용 영역 = 로그 상자).
# 다 잡으면 [켜기] 단추가 살아나고, 마우스로 누르거나 창 안에서 밟으면 인터넷이 연결된다.
import gfx
import apps
import fs
from apps import App
from config import *

FORM_BG = (240, 240, 240)
GREEN, RED = (16, 124, 16), (196, 43, 28)
START_LOG = [
    '[시작] 인터넷 차단기 v1.0 실행',
    '[규칙] 모든 프로그램의 외부 연결 차단',
    '[차단] chrome.exe → google.com',
    '[차단] chrome.exe → youtube.com',
    '[경고] 로그에서 알 수 없는 버그 감지',
    '[경고] 버그가 [켜기] 단추를 잠갔습니다',
]


class Breaker(App):
    group = 'breaker'
    key = 'breaker'
    icon = 'exe'
    title = '인터넷 차단기'
    caption = ('min', 'close')          # 크기 고정 폼이라 최대화 단추는 없다
    resizable = False
    center = True
    size = (620, 680)

    def __init__(self):
        self.node = fs.BREAKER          # 몬스터는 이 노드에 살고, 이 창의 로그 상자에서 움직인다
        self.content = (0, 0, 0, 0)     # 로그 상자 안쪽 (몬스터의 무대)
        self.buttons = {'on': (0, 0, 0, 0), 'off': (0, 0, 0, 0)}
        self.ready = False              # 로그의 버그를 다 잡았는가 (Section이 매 프레임 알려 준다)
        self.on_change = None           # 켜기/끄기를 누르면 할 일 (True = 연결). Section이 넣어 준다
        self.log = list(reversed(START_LOG))
        self.killed = 0

    @staticmethod
    def online():
        return apps.Browser.online

    def add_log(self, line):
        self.log.insert(0, line)        # 최신순

    def enabled(self, name):
        return (self.ready and not self.online()) if name == 'on' else self.online()

    # ---------------------------------------------------------------- 누르기
    def press_button(self, name):
        if not self.enabled(name):
            return
        on = name == 'on'
        self.add_log('[해제] 차단 규칙 삭제 → 인터넷 연결됨' if on else '[규칙] 다시 차단 → 인터넷 연결 끊김')
        if self.on_change:
            self.on_change(on)
        else:
            apps.Browser.online = on

    def mouse_down(self, mx, my, now):
        for name, (l, b, w, h) in self.buttons.items():
            if l <= mx < l + w and b <= my < b + h:
                self.press_button(name)
                return

    def platforms(self):
        # 창 안에서 두 단추 윗면에 올라설 수 있다
        return [(l, l + w, b + h) for l, b, w, h in self.buttons.values()]

    def stepped_by(self, player):
        l, b, w, h = self.buttons['on']
        return self.enabled('on') and abs(player.y - (b + h)) < 1 and player.x + 42 > l and player.x + 6 < l + w

    def press(self):
        self.press_button('on')

    # ---------------------------------------------------------------- 그리기
    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, FORM_BG)
        on = self.online()
        status = '현재 상태: 인터넷 연결됨' if on else '현재 상태: 인터넷 차단됨'
        gfx.text(status, l + w / 2, top - 42, 20, GREEN if on else RED, FONT_BOLD, align='center')
        bw, bh = (w - 66) // 2, 62
        self.buttons = {'on': (l + 22, top - 90 - bh, bw, bh), 'off': (l + 44 + bw, top - 90 - bh, bw, bh)}
        for name, label in (('on', '켜기'), ('off', '끄기')):
            bl, bb, bw_, bh_ = self.buttons[name]
            live = self.enabled(name)
            if live:
                gfx.round_rect(bl, bb, bw_, bh_, 4, ACCENT if name == 'on' or active else (173, 173, 173))
                gfx.round_rect(bl + 1, bb + 1, bw_ - 2, bh_ - 2, 3, (253, 253, 253))
            else:
                gfx.round_rect(bl, bb, bw_, bh_, 4, (220, 220, 220))
                gfx.round_rect(bl + 1, bb + 1, bw_ - 2, bh_ - 2, 3, (245, 245, 245))
            gfx.text(label, bl + bw_ / 2, bb + bh_ / 2, 15, BLACK if live else (160, 160, 160), align='center')
        # 로그 상자
        bl, bb, bw_, bh_ = self.buttons['on']
        gfx.text('로그 (최신순)', l + 22, bb - 26, 14, BLACK)
        ll, lb, lw, lh = l + 22, b + 20, w - 44, bb - 46 - (b + 20)
        gfx.fill(ll, lb, lw, lh, (130, 135, 144))
        gfx.fill(ll + 1, lb + 1, lw - 2, lh - 2, WHITE)
        self.content = (ll + 2, lb + 2, lw - 4, lh - 4)
        gfx.push_clip(*self.content)
        for i, line in enumerate(self.log):
            y = lb + lh - 16 - i * 22
            if y < lb:
                break
            color = RED if line.startswith('[경고]') else GREEN if line.startswith(('[해제]', '[제거]')) else BLACK
            gfx.text(line, ll + 8, y, 13, color)
        gfx.pop_clip()


apps.APPS['breaker'] = Breaker
