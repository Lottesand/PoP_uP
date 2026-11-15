# 구간 1 (파일 관리자)에 등장하는 몬스터 배치
import fs
from monsters import KINDS
from config import TASKBAR_H


def find(parent, *names):
    node = parent
    for name in names:
        node = next(c for c in node.children if c.name == name)
    return node


# (폴더, [(종류, 내용 영역 왼쪽에서의 x)])
def encounters():
    docs = fs.DOCUMENTS
    return [
        (docs, [('bug', 260), ('bug', 470)]),
        (find(docs, '과제'), [('caret', 320), ('bug', 140)]),
        (find(docs, '사진 백업'), [('bug', 120), ('bug', 300), ('bug', 480)]),
        (find(docs, '숨겨진 폴더'), [('bomber', 400), ('caret', 180)]),
        (find(docs, '숨겨진 폴더', '설정'), [('caret', 460), ('bug', 220), ('bomber', 560)]),
    ]


def spawn():
    return [KINDS[kind](folder, rx) for folder, specs in encounters() for kind, rx in specs]


def window_for(folder, wm):
    """그 폴더를 보여 주는 가장 앞의 창"""
    for win in reversed(wm.visible()):
        if getattr(win.app, 'node', None) is folder and win.app.content[2] > 0:
            return win
    return None


# ==================================================================== 구간 0~1 진행
class Section:
    """부팅 경고창 [확인] 밟기 → 파일 관리자 탐험 → 인터넷 차단기 끄기 → 클리어"""

    def __init__(self):
        self.state = 'warning'          # warning | explore | clear
        self.time = 0.0
        self.deaths = 0
        self.hints = set()

    def start(self, game):
        import apps
        game.wm.open(apps.MessageBox('시스템 경고', [
            'USB 드라이브(E:)가 잠겼습니다. 이 PC에서 나갈 수 없습니다.',
            'A/D: 이동   Space: 점프   Shift: 창 안으로 들어가기',
            '이 창 안으로 들어가서 [확인] 단추를 밟으세요.'], 'warning', self.begin, (230, TASKBAR_H + 20)))

    def begin(self):
        import toast
        self.state = 'explore'
        toast.show('인터넷이 차단되어 있습니다', '문서 폴더 어딘가에 숨은 인터넷 차단기를', '찾아서 끄세요.')
        toast.show('탐색기', '마우스로 폴더를 더블클릭하면 들어갑니다.', '창을 끌어 발판을 만들 수 있습니다 (Shift OFF).')

    def hint(self, key, title, *lines):
        import toast
        if key not in self.hints:
            self.hints.add(key)
            toast.show(title, *lines)

    def update(self, dt, game):
        if self.state != 'explore':
            return
        self.time += dt
        p = game.player
        if p.mode == 'on':
            self.hint('enter', '창 안으로 들어왔습니다', 'Shift를 다시 누르면 제목 표시줄 위로 튀어나옵니다.')
            if any(m.win is p.win for m in game.monsters):
                self.hint('monster', 'OS의 버그가 나타났습니다', '좌클릭: 가까운 창 버튼(─ ☐ ✕) 뜯기',
                          '우클릭: 조준한 곳으로 던지기')
            if p.win.app.ladders() and p.win.client_rect()[3] > 320:
                self.hint('ladder', '높은 곳에 닿지 않나요?', 'W/S: 오른쪽 스크롤바를 사다리처럼 오르내리기')
        if p.hp <= 60:
            self.hint('heal', 'HP가 줄었습니다', 'Q: 들고 있는 버튼을 먹어 HP 12 회복 (8초마다)')
        if p.mode == 'on' and p.ground is not None and fs.BREAKER.custom_icon == 'breaker_on':
            for node, (l, b, w, h) in getattr(p.win.app, 'items', []):
                if node is fs.BREAKER and abs(p.y - (b + h)) < 1 and p.x + 42 > l and p.x + 6 < l + w:
                    self.clear(game)

    def clear(self, game):
        import apps
        import toast
        fs.BREAKER.custom_icon = 'breaker_off'
        self.state = 'clear'
        apps.Browser.online = True
        game.taskbar.online = True
        toast.show('인터넷에 연결됨', '네트워크 연결이 복구되었습니다.', icon='browser')
        m, s = divmod(int(self.time), 60)
        game.wm.open(apps.MessageBox('구간 1 클리어', [
            '인터넷 차단기를 껐습니다. 인터넷에 연결되었습니다.',
            '걸린 시간 %d분 %02d초 · 블루스크린 %d번' % (m, s, self.deaths),
            '다음 구간: 웹 브라우저 (준비 중)'], 'info'))
