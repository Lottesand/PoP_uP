# 구간별 몬스터 배치와 구간 진행 (구간 1 파일 관리자 · 2 웹 브라우저 · 3 %appdata%)
import random
import fs
from monsters import KINDS, BugWorm
from config import TASKBAR_H

# 버그는 폴더 창을 열어 두면 창 가장자리에서 계속 튀어나온다
SPAWNING = True                 # 테스트에서 끈다
SPAWN_FIRST, SPAWN_EVERY = 2.0, 3.0
MAX_BUGS = 7                    # 한 폴더에 동시에 있을 수 있는 버그 수
EDGES = ('left', 'top', 'right', 'bottom')


def find(parent, *names):
    node = parent
    for name in names:
        node = next(c for c in node.children if c.name == name)
    return node


# (폴더, [(종류, 내용 영역 왼쪽에서의 x)])
def encounters():
    docs = fs.DOCUMENTS
    return [
        (docs, [('bug', 180), ('bug', 360), ('bug', 540)]),
        (find(docs, '과제'), [('caret', 320), ('bug', 140), ('bug', 480)]),
        (find(docs, '사진 백업'), [('bug', 100), ('bug', 240), ('bug', 380), ('bug', 520)]),
        (find(docs, '숨겨진 폴더'), [('bomber', 400), ('caret', 180), ('bug', 560)]),
        (find(docs, '숨겨진 폴더', '설정'), [('caret', 460), ('bug', 220), ('bug', 340), ('bomber', 560)]),
        (fs.BREAKER, BREAKER_BUGS),     # 인터넷 차단기.exe의 로그 상자 안
    ]


BREAKER_BUGS = [('bug', 60), ('bug', 260), ('bug', 440), ('caret', 300)]


def spawn():
    # 버그는 높이도 여기저기 (위에서 내려다본 바닥이라서), 나머지는 바닥에 선다
    return [KINDS[kind](folder, rx) if kind == 'bug' else KINDS[kind](folder, rx, 0.0)
            for folder, specs in encounters() for kind, rx in specs]


class Spawner:
    """보이는 폴더 창마다 일정 시간이 지나면 버그가 네 가장자리를 돌아가며 기어 나온다"""

    def __init__(self):
        self.timers = {}            # 폴더 id → 다음 출현까지 남은 초
        self.count = 0

    def update(self, dt, game):
        if not SPAWNING:
            return
        shown = set()
        for win in game.wm.visible():
            folder = getattr(win.app, 'node', None)
            if folder is None or folder.kind != fs.FOLDER or folder.locked or win.app.content[2] <= 0 \
                    or folder is fs.TEMP:       # 보스 방에는 버그가 따로 나오지 않는다
                continue
            if folder.id in shown or window_for(folder, game.wm) is not win:
                continue
            shown.add(folder.id)
            t = self.timers.get(folder.id, SPAWN_FIRST) - dt
            if t <= 0:
                t = SPAWN_EVERY
                if sum(1 for m in game.monsters if m.folder is folder and isinstance(m, BugWorm)) < MAX_BUGS:
                    cw, ch = win.app.content[2], win.app.content[3]
                    self.count += 1
                    edge = EDGES[self.count % 4]                  # 네 방향을 돌아가며
                    along = random.uniform(0.15, 0.85)
                    rx = {'left': 0, 'right': cw - BugWorm.w}.get(edge, along * (cw - BugWorm.w))
                    ry = {'bottom': 0, 'top': ch - BugWorm.h}.get(edge, along * (ch - BugWorm.h))
                    bug = BugWorm(folder, rx, ry)
                    bug.burst_in(edge)
                    game.monsters.append(bug)
            self.timers[folder.id] = t


def window_for(folder, wm):
    """그 폴더를 보여 주는 가장 앞의 창"""
    for win in reversed(wm.visible()):
        if getattr(win.app, 'node', None) is folder and win.app.content[2] > 0:
            return win
    return None


# ==================================================================== 구간 0~1 진행
class Section:
    """구간 진행
    warning   부팅 경고창 [확인] 밟기
    explore   구간 1 파일 관리자: 인터넷 차단기.exe의 버그 잡고 [켜기] → 인터넷 연결
    web       구간 2 웹 브라우저: Chrome 안 캐럿 · 로고 → 검색창 뒤에서 크롬 공룡 → %appdata% 권한
    appdata   구간 3 %appdata%: 깊은 폴더의 몬스터 → Local/Temp의 블랙홀 (시스템 파일 지키기) → 휴지통 해제
    done      다음 구간(휴지통) 준비 중
    """
    NUMBER = {'explore': 1, 'web': 2, 'appdata': 3}

    def __init__(self):
        self.state = 'warning'
        self.time = 0.0
        self.deaths = 0
        self.hints = set()
        self.breaker_left = len(BREAKER_BUGS)     # 차단기 로그에 남은 버그
        self.dino = None
        self.hole = None

    def start(self, game):
        import apps
        game.wm.open(apps.MessageBox('시스템 경고', [
            'USB 드라이브(E:)가 잠겼습니다. 이 PC에서 나갈 수 없습니다.',
            'A/D: 이동   Space: 점프   Shift: 공격 모드   좌클릭: 찌르기',
            '공격 모드에서 이 창 테두리를 세 번 찔러 부수고 들어가서 [확인]을 밟으세요.'],
            'warning', self.begin, (230, TASKBAR_H + 20)))

    def begin(self):
        import toast
        self.state = 'explore'
        toast.show('인터넷이 차단되어 있습니다', '문서 폴더 어딘가에 숨은 인터넷 차단기.exe를', '찾아서 실행하고 인터넷을 켜세요.')
        toast.show('탐색기', '마우스로 폴더를 더블클릭하면 들어갑니다.', '창을 끌어 발판을 만들 수 있습니다 (Shift OFF).')

    def hint(self, key, title, *lines):
        import toast
        if key not in self.hints:
            self.hints.add(key)
            toast.show(title, *lines)

    # ---------------------------------------------------------------- 매 프레임
    def update(self, dt, game):
        self.watch_breaker(game)
        if self.state in ('warning', 'done'):
            return
        self.time += dt
        self.common_hints(game)
        if self.state == 'web':
            self.update_web(game)
        elif self.state == 'appdata':
            self.update_appdata(game)

    def common_hints(self, game):
        p = game.player
        if p.mode == 'on' and not p.inside:
            self.hint('attack', '공격 모드', '창이 벽이 됩니다. 좌클릭으로 창 테두리를 세 번 찌르면',
                      '부서지면서 그 창 안으로 들어갑니다.')
        if p.inside:
            self.hint('enter', '창 안으로 들어왔습니다', 'Shift를 꺼도 창 안에 그대로 있습니다.',
                      '나가려면 공격 모드에서 테두리를 안쪽에서 세 번 찌르세요.')
            if any(m.win is p.win for m in game.monsters):
                self.hint('monster', 'OS의 버그가 나타났습니다', '좌클릭: 가까운 창 버튼(─ ☐ ✕) 뜯기',
                          '우클릭: 조준한 곳으로 던지기')
            if p.win.app.ladders() and p.win.client_rect()[3] > 320:
                self.hint('ladder', '높은 곳에 닿지 않나요?', 'W/S: 오른쪽 스크롤바를 사다리처럼 오르내리기')
        if p.hp <= 60:
            self.hint('heal', 'HP가 줄었습니다', 'Q: 들고 있는 버튼을 먹어 HP 12 회복 (8초마다)')
        win = game.wm.find('breaker')
        if win is not None and not win.app.ready and self.state == 'explore':
            self.hint('breaker', '로그 안에 버그가 숨어 있습니다', 'Shift로 차단기 창을 부수고 들어가 버그를 모두 잡으면',
                      '[켜기] 단추가 살아납니다. 누르거나 밟으세요.')

    def watch_breaker(self, game):
        """차단기 창이 열려 있으면 버그 수를 세서 로그에 남기고, 다 잡으면 [켜기]를 살린다"""
        win = game.wm.find('breaker')
        left = sum(1 for m in game.monsters if m.folder is fs.BREAKER and not m.dead)
        if win is None:
            self.breaker_left = left
            return
        app = win.app
        app.on_change = lambda on: self.set_online(game, on)
        total = len(BREAKER_BUGS)
        while self.breaker_left > left:
            self.breaker_left -= 1
            app.add_log('[제거] 버그 제거됨 (%d/%d)' % (total - self.breaker_left, total))
        if left == 0 and not app.ready:
            app.add_log('[알림] 버그가 모두 사라졌습니다. [켜기] 잠금 해제')
        app.ready = left == 0

    def set_online(self, game, on):
        import apps
        if on and self.state == 'explore':
            self.clear(game)
            return
        apps.Browser.online = on
        game.taskbar.online = on

    def report(self, game, title, *lines):
        import apps
        m, s = divmod(int(self.time), 60)
        game.wm.open(apps.MessageBox(title, list(lines) + ['걸린 시간 %d분 %02d초 · 블루스크린 %d번' % (m, s, self.deaths)],
                                     'info'))

    def save_checkpoint(self, game):
        p = game.player
        game.checkpoint = (160, TASKBAR_H) if p.inside else (p.x, max(TASKBAR_H, p.y))

    # ---------------------------------------------------------------- 구간 1 → 2
    def clear(self, game):
        import apps
        import toast
        apps.Browser.online = True
        game.taskbar.online = True
        toast.show('인터넷에 연결됨', '네트워크 연결이 복구되었습니다.', icon='browser')
        self.report(game, '구간 1 클리어', '인터넷 차단기를 해제했습니다. 인터넷에 연결되었습니다.',
                    '다음 구간: 웹 브라우저 - Chrome에서 이상한 신호가 잡힙니다.')
        self.start_web(game)

    def start_web(self, game):
        import toast
        self.state = 'web'
        fs.TRASH.locked = True                    # 블랙홀을 잡을 때까지 휴지통은 잠긴다
        game.monsters.extend(KINDS[k](fs.WEB, rx, 0.0) for k, rx in WEB_WAVE)
        self.save_checkpoint(game)
        toast.show('구간 2: 웹 브라우저', 'Chrome 안에 버그가 숨어들었습니다.', 'Chrome을 열고 창을 부수고 들어가세요.',
                   icon='browser')

    def update_web(self, game):
        p = game.player
        if self.dino is None:
            wave = [m for m in game.monsters if m.folder is fs.WEB and not m.dead]
            win = level_window(fs.WEB, game.wm)
            if not wave and win is not None and p.win is win:
                self.ambush(game, win)
        elif self.dino.dead:
            self.clear_web(game)

    def ambush(self, game, win):
        """웨이브를 다 잡으면 구글 검색창 뒤에서 크롬 공룡이 튀어나온다"""
        import toast
        from bosses import ChromeDino
        app = win.app
        l, b, w, h = app.content
        sl, sb, sw, sh = app.search_rect if app.search_rect[2] else (l + w / 2 - 60, b + h / 2, 120, 40)
        self.dino = ChromeDino(fs.WEB, min(max(0, sl + sw / 2 - l - ChromeDino.w / 2), w - ChromeDino.w),
                               max(0, sb - b))
        self.dino.vy = 600
        game.monsters.append(self.dino)
        game.impact(0.08, 0.4, 10)
        toast.show('검색창 뒤에서 무언가가 튀어나왔다!', '크롬 공룡: 착지 직후 1초 경직 동안만 제대로 맞습니다.',
                   '선인장은 점프로, 꼬리 치기(!)는 거리를 벌려서 피하세요.', icon='browser')

    def clear_web(self, game):
        import toast
        self.state = 'appdata'
        fs.APPDATA.locked = False
        game.monsters.extend(spawn_appdata())
        self.hole = next(m for m in game.monsters if m.__class__.__name__ == 'Blackhole')
        self.save_checkpoint(game)
        toast.show('%appdata% 접근 권한을 얻었습니다', '내 PC > 로컬 디스크 (C:) > Users > Pointer > AppData',
                   '가장 깊은 Local > Temp에서 무언가가 파일을 삼키고 있습니다.')
        self.report(game, '구간 2 클리어', '크롬 공룡을 쓰러뜨렸습니다. %appdata% 접근 권한을 얻었습니다.',
                    '다음 구간: %appdata% - 가장 깊은 폴더로 가세요.')

    # ---------------------------------------------------------------- 구간 3
    def update_appdata(self, game):
        p = game.player
        if p.inside and p.win is level_window(fs.TEMP, game.wm):
            self.hint('hole', '파일 융합 블랙홀', '빨아들일 때는 스크롤바(W/S)를 붙잡고 버티세요.',
                      '시스템 파일을 때리면 블랙홀 반대쪽으로 밀어낼 수 있습니다 (삼키면 HP +100).')
        if self.hole is not None and self.hole.dead:
            self.clear_appdata(game)

    def clear_appdata(self, game):
        import toast
        self.state = 'done'
        fs.TRASH.locked = False
        saved = sum(1 for m in game.monsters if m.folder is fs.TEMP and getattr(m, 'guard', False) and not m.dead)
        self.save_checkpoint(game)
        toast.show('휴지통 잠금 해제', '블랙홀이 사라지고 휴지통이 열렸습니다.')
        self.report(game, '구간 3 클리어', '파일 융합 블랙홀을 쓰러뜨렸습니다. 휴지통이 열렸습니다.',
                    '지켜 낸 시스템 파일 %d / %d' % (saved, len(SYS_FILES)), '다음 구간: 휴지통 (준비 중)')

    def skip_to(self, game, state):
        """테스트 · 디버그용: 그 구간이 막 시작된 상태로 바로 간다"""
        import apps
        if state in ('web', 'appdata'):
            apps.Browser.online = game.taskbar.online = True
            self.start_web(game)
        if state == 'appdata':
            self.dino = type('Dead', (), {'dead': True})()
            self.clear_web(game)
            for win in list(game.wm.windows):
                if win.app.title.startswith('구간'):
                    game.wm.close(win)


def level_window(folder, wm):
    return window_for(folder, wm)


# 구간 2: Chrome 안 웨이브 (공룡은 다 잡고 나서 검색창 뒤에서)
WEB_WAVE = [('caret', 120), ('bomber', 520), ('caret', 820)]
# 구간 3: 블랙홀이 노리는 시스템 파일
SYS_FILES = [('pointer.sys', 'text_file', 80, 60), ('usb_driver.inf', 'text_file', 80, 330),
             ('desktop.ini', 'text_file', 700, 330)]


def spawn_appdata():
    from bosses import Blackhole, SysFile
    out = [KINDS[k](folder, rx) if k == 'bug' else KINDS[k](folder, rx, 0.0)
           for folder, specs in ((fs.APPDATA, [('bug', 160), ('bug', 420), ('caret', 300)]),
                                 (fs.ROAMING, [('bug', 120), ('bug', 300), ('bomber', 500)]),
                                 (fs.LOCAL, [('caret', 200), ('bomber', 460), ('bug', 340)]))
           for k, rx in specs]
    out.append(Blackhole(fs.TEMP, 0, 0))
    out += [SysFile(fs.TEMP, rx, ry, name, icon) for name, icon, rx, ry in SYS_FILES]
    return out
