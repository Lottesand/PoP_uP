# 창 안에 그려지는 프로그램 화면들. draw(l, b, w, h, active)는 창의 내용 영역을 받는다.
import time
import gfx
from config import *

G_BACK, G_FWD, G_REFRESH, G_SEARCH = '\uE72B', '\uE72A', '\uE72C', '\uE721'


class App:
    key = 'app'            # 같은 키의 창은 하나만 연다
    group = 'app'          # 작업 표시줄 단추 묶음
    title = ''
    icon = 'folder'
    size = (800, 520)
    caption = ('min', 'max', 'close')
    resizable = True
    taskbar = True
    center = False

    def draw(self, l, b, w, h, active):
        gfx.fill(l, b, w, h, WHITE)

    def mouse_down(self, mx, my, now):
        pass

    def mouse_move(self, mx, my):
        pass

    def context(self, mx, my):
        return None

    def wheel(self, dy):
        pass


# ==================================================================== 메시지 상자
class MessageBox(App):
    group = 'dialog'
    icon = 'explorer'
    caption = ('close',)
    resizable = False
    taskbar = False
    center = True
    _count = 0

    def __init__(self, title, lines, kind='error'):
        MessageBox._count += 1
        self.key = 'dialog#%d' % MessageBox._count
        self.title, self.lines, self.kind = title, list(lines), kind
        w = max(gfx.text_width(ln, 12) for ln in self.lines) + 100
        self.size = (max(360, w), TITLE_H + 40 + 20 * len(self.lines) + 50)
        self.button = (0, 0, 0, 0)

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, WHITE)
        cy = top - 24 - 10 * (len(self.lines) - 1)
        gfx.circle(l + 38, cy, 16, CLOSE_RED if self.kind == 'error' else ACCENT)
        gfx.symbol('\uE8BB' if self.kind == 'error' else '\uE946', l + 38, cy, 14, WHITE)
        for i, ln in enumerate(self.lines):
            gfx.text(ln, l + 68, top - 24 - i * 20, 12)
        gfx.fill(l, b, w, 46, (240, 240, 240))
        self.button = (l + w - 100, b + 11, 88, 24)
        bl, bb, bw, bh = self.button
        gfx.fill(bl, bb, bw, bh, (225, 225, 225))
        gfx.frame(bl, bb, bw, bh, ACCENT if active else (173, 173, 173))
        gfx.text('확인', bl + bw / 2, bb + bh / 2, 12, align='center')

    def mouse_down(self, mx, my, now):
        bl, bb, bw, bh = self.button
        if bl <= mx < bl + bw and bb <= my < bb + bh:
            import shell
            shell.close(self)


# ==================================================================== 메모장
class Notepad(App):
    group = 'notepad'
    icon = 'notepad'
    size = (640, 460)
    _count = 0

    def __init__(self, node):
        Notepad._count += 1
        self.node = node
        self.key = 'notepad:%d' % node.id if node else 'notepad#%d' % Notepad._count

    @property
    def title(self):
        return (self.node.name if self.node else '제목 없음') + ' - Windows 메모장'

    @property
    def lines(self):
        return self.node.lines if self.node else []

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, WHITE)
        x = l + 8
        for m in ('파일(F)', '편집(E)', '서식(O)', '보기(V)', '도움말(H)'):
            x += gfx.text(m, x, top - 10, 12) + 14
        gfx.line(l, top - 20, l + w, top - 20, (240, 240, 240))
        for i, ln in enumerate(self.lines):
            gfx.text(ln, l + 6, top - 34 - i * 20, 14)
        if active and int(time.time() * 2) % 2 == 0:
            gfx.fill(l + 6, top - 44, 1, 18, TEXT)
        # 상태 표시줄 · 스크롤바
        gfx.fill(l, b, w, 22, (240, 240, 240))
        gfx.line(l, b + 22, l + w, b + 22, (220, 220, 220))
        x = l + w - 30
        for part in ('UTF-8', 'Windows (CRLF)', '100%', 'Ln 1, Col 1'):
            x -= gfx.text(part, x, b + 11, 12, align='right') + 34
            gfx.line(x + 18, b + 2, x + 18, b + 20, (210, 210, 210))
        gfx.fill(l + w - 17, b + 22, 17, h - 42, (240, 240, 240))


# ==================================================================== 웹 브라우저 (인터넷 끊김)
DINO = [
    '..........######..',
    '.........##.######',
    '.........#########',
    '.........#########',
    '.........#####....',
    '.........########.',
    '#.......#####.....',
    '#.....#######.....',
    '##...#########....',
    '###.##########....',
    '##############....',
    '.############.....',
    '..##########......',
    '...########.......',
    '....###..##.......',
    '....##....#.......',
    '....#.....#.......',
    '....##....##......',
]


def draw_dino(l, b, px, color=(83, 83, 83)):
    rows = len(DINO)
    for r, row in enumerate(DINO):
        for c, ch in enumerate(row):
            if ch == '#':
                gfx.fill(l + c * px, b + (rows - 1 - r) * px, px, px, color)


class Browser(App):
    group = 'browser'
    key, title, icon = 'browser', '새 탭 - Chrome', 'browser'
    size = (1000, 640)

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, WHITE)
        # 탭 줄
        gfx.fill(l, top - 34, w, 34, (222, 225, 230) if active else (232, 234, 237))
        gfx.fill(l + 8, top - 34, 230, 28, WHITE)
        gfx.icon('browser', 16, l + 20, top - 28)
        gfx.text('인터넷 연결 없음', l + 44, top - 20, 12)
        gfx.symbol('\uE711', l + 222, top - 20, 8, (90, 90, 90))
        gfx.symbol('\uE710', l + 256, top - 20, 10, (90, 90, 90))
        # 도구 모음 · 주소창
        y = top - 34 - 38
        for i, g in enumerate((G_BACK, G_FWD, G_REFRESH)):
            gfx.symbol(g, l + 22 + i * 34, y + 19, 12, (160, 160, 160) if i < 2 else (90, 90, 90))
        gfx.fill(l + 118, y + 5, w - 170, 28, (241, 243, 244))
        gfx.symbol('\uE946', l + 136, y + 19, 12, (90, 90, 90))
        gfx.text('chrome://network-error', l + 156, y + 19, 14, (60, 60, 60))
        gfx.symbol('\uE712', l + w - 26, y + 19, 12, (90, 90, 90))
        gfx.line(l, y, l + w, y, (218, 220, 224))
        # 오류 페이지
        cx = l + max(60, (w - 600) // 2)
        cy = y - 90
        draw_dino(cx, cy - 72, 4)
        gfx.text('인터넷에 연결되어 있지 않음', cx, cy - 110, 24, (32, 33, 36))
        gfx.text('다음 방법을 시도해 보세요.', cx, cy - 150, 14, (95, 99, 104))
        for i, tip in enumerate(('네트워크 케이블, 모뎀, 라우터 확인', 'Wi-Fi에 다시 연결')):
            gfx.fill(cx + 22, cy - 178 - i * 24, 4, 4, (95, 99, 104))
            gfx.text(tip, cx + 34, cy - 176 - i * 24, 14, (95, 99, 104))
        gfx.text('ERR_INTERNET_DISCONNECTED', cx, cy - 240, 12, (117, 117, 117))


# ==================================================================== 그림판
class Paint(App):
    group = 'paint'
    key, title, icon = 'paint', '제목 없음 - 그림판', 'paint'
    size = (860, 600)

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, (201, 211, 226))
        gfx.fill(l, top - 24, w, 24, WHITE)
        gfx.fill(l, top - 24, 50, 24, (25, 121, 202))
        gfx.text('파일', l + 25, top - 12, 12, WHITE, align='center')
        gfx.text('홈', l + 70, top - 12, 12)
        gfx.text('보기', l + 104, top - 12, 12)
        ry = top - 24 - 92
        gfx.fill(l, ry, w, 92, (245, 246, 247))
        gfx.line(l, ry, l + w, ry, (218, 219, 220))
        groups = (('클립보드', 70), ('이미지', 110), ('도구', 120), ('브러시', 60), ('도형', 170), ('크기', 50), ('색', 240))
        x = l + 6
        for name, gw in groups:
            gfx.text(name, x + gw / 2, ry + 10, 12, (90, 90, 90), align='center')
            gfx.line(x + gw + 3, ry + 6, x + gw + 3, ry + 86, (226, 227, 228))
            if name == '도구':
                for i in range(6):
                    tx, ty = x + 12 + (i % 3) * 32, ry + 66 - (i // 3) * 28
                    gfx.frame(tx, ty - 10, 24, 22, (200, 200, 200))
                    if i == 1:
                        gfx.fill(tx + 4, ty - 6, 16, 14, (60, 120, 200))     # 페인트통
            if name == '색':
                cols = [(0, 0, 0), (127, 127, 127), (136, 0, 21), (237, 28, 36), (255, 127, 39), (255, 242, 0),
                        (34, 177, 76), (0, 162, 232), (63, 72, 204), (163, 73, 164)]
                for i, c in enumerate(cols):
                    gfx.fill(x + 10 + i * 22, ry + 56, 18, 18, c)
                    gfx.frame(x + 10 + i * 22, ry + 56, 18, 18, (160, 160, 160))
            x += gw + 8
        cw, chh = min(w - 20, 640), min(ry - b - 40, 400)
        gfx.fill(l + 6, ry - 6 - chh, cw, chh, WHITE)
        gfx.fill(l, b, w, 24, (240, 240, 240))
        gfx.text('%d × %d픽셀' % (cw, chh), l + 200, b + 12, 12)


# ==================================================================== Visual Studio Code
CODE = [
    [('def ', (86, 156, 214)), ('escape', (220, 220, 170)), ('(pointer):', (212, 212, 212))],
    [('    ', None), ('if ', (197, 134, 192)), ('not ', (86, 156, 214)), ('pointer.has_key(', (212, 212, 212)),
     ("'usb'", (206, 145, 120)), ('):', (212, 212, 212))],
    [('        ', None), ('raise ', (197, 134, 192)), ('PermissionError', (78, 201, 176)),
     ('(', (212, 212, 212)), ("'E: 접근 거부'", (206, 145, 120)), (')', (212, 212, 212))],
    [('    ', None), ('zip_file ', (156, 220, 254)), ('= ', (212, 212, 212)), ('compress', (220, 220, 170)),
     ('(pointer)', (212, 212, 212))],
    [('    ', None), ('usb.', (156, 220, 254)), ('copy', (220, 220, 170)), ('(zip_file)', (212, 212, 212))],
    [('    ', None), ('usb.', (156, 220, 254)), ('safely_remove', (220, 220, 170)), ('()', (212, 212, 212))],
]


class VSCode(App):
    group = 'vscode'
    key, title, icon = 'vscode', 'escape.py - Visual Studio Code', 'vscode'
    size = (960, 600)

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, (30, 30, 30))
        gfx.fill(l, b + 22, 48, h - 22, (51, 51, 51))
        for i, g in enumerate(('\uE8A5', G_SEARCH, '\uE8CB', '\uEBE8')):
            gfx.symbol(g, l + 24, top - 28 - i * 48, 18, (200, 200, 200) if i == 0 else (130, 130, 130))
        gfx.fill(l + 48, b + 22, 200, h - 22, (37, 37, 38))
        gfx.text('탐색기', l + 64, top - 18, 11, (187, 187, 187))
        for i, name in enumerate(('escape.py', 'pointer.py', 'usb_key.txt')):
            if i == 0:
                gfx.fill(l + 48, top - 54 - i * 22, 200, 22, (55, 55, 61))
            gfx.text(name, l + 76, top - 43 - i * 22, 13, (204, 204, 204))
        gfx.fill(l + 248, top - 35, 140, 35, (30, 30, 30))
        gfx.fill(l + 388, top - 35, w - 388, 35, (37, 37, 38))
        gfx.text('escape.py', l + 268, top - 17, 13, WHITE)
        for i, row in enumerate(CODE):
            y = top - 60 - i * 20
            gfx.text(str(i + 1), l + 290, y, 13, (133, 133, 133), align='right')
            if i == 1:
                gfx.fill(l + 258, y - 6, 12, 12, (229, 20, 0))     # 중단점
            x = l + 310
            for s, c in row:
                x += gfx.text(s, x, y, 13, c) if c else gfx.text_width(s, 13)
        gfx.fill(l, b, w, 22, (0, 122, 204))
        gfx.text('Python 3.15', l + w - 20, b + 11, 12, WHITE, align='right')
        gfx.text('main', l + 30, b + 11, 12, WHITE)


# ==================================================================== 카카오톡
class Kakao(App):
    group = 'kakao'
    key, title, icon = 'kakao', '카카오톡', 'kakao'
    size = (380, 600)

    def draw(self, l, b, w, h, active):
        gfx.fill(l, b, w, h, (254, 229, 0))
        cx, cy = l + w / 2, b + h * 0.62
        gfx.icon('kakao', 48, cx - 24, cy - 24)
        gfx.fill(cx - 120, cy - 110, 240, 40, WHITE)
        gfx.text('카카오계정 (이메일 또는 전화번호)', cx - 110, cy - 90, 12, (170, 170, 170))
        gfx.fill(cx - 120, cy - 151, 240, 40, WHITE)
        gfx.text('비밀번호', cx - 110, cy - 131, 12, (170, 170, 170))
        gfx.fill(cx - 120, cy - 200, 240, 40, (246, 246, 246))
        gfx.text('로그인', cx, cy - 180, 13, (180, 180, 180), align='center')


# ==================================================================== 명령 프롬프트
class Terminal(App):
    group = 'terminal'
    key, title, icon = 'terminal', '명령 프롬프트', 'terminal'
    size = (720, 420)

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, (12, 12, 12))
        lines = ['Microsoft Windows [Version 10.0.19045.5247]', '(c) Microsoft Corporation. All rights reserved.', '',
                 'C:\\Users\\Pointer>']
        for i, ln in enumerate(lines):
            gfx.text(ln, l + 6, top - 14 - i * 18, 14, (204, 204, 204))
        if active and int(time.time() * 2) % 2 == 0:
            gfx.fill(l + 8 + gfx.text_width(lines[-1], 14), top - 14 - 3 * 18 - 8, 9, 3, (204, 204, 204))


# ==================================================================== 프로그램 목록
APPS = {'browser': Browser, 'paint': Paint, 'vscode': VSCode, 'kakao': Kakao, 'terminal': Terminal}
