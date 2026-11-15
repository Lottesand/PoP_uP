# 창 안에 그려지는 프로그램 화면들. draw(l, b, w, h, active)는 창의 내용 영역을 받는다.
import time
import gfx
import textbox
from config import *

G_BACK, G_FWD, G_REFRESH, G_SEARCH = '\uE72B', '\uE72A', '\uE72C', '\uE721'


class App:
    key = 'app'            # 같은 키의 창은 하나만 연다
    group = 'app'          # 작업 표시줄 단추 묶음
    title = ''
    icon = 'folder'
    size = (800, 520)
    min_size = (WIN_MIN_W, WIN_MIN_H)
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

    def platforms(self):
        """창 안(Shift ON)에서 밟을 수 있는 발판 (x0, x1, y). 화면 좌표"""
        return []

    def ladders(self):
        """W/S로 오르내리는 스크롤바 사각형들 (l, b, w, h). 화면 좌표"""
        return []


# ==================================================================== 메시지 상자
class MessageBox(App):
    group = 'dialog'
    icon = 'explorer'
    caption = ('close',)
    resizable = False
    taskbar = False
    center = True
    _count = 0

    def __init__(self, title, lines, kind='error', on_ok=None, pos=None):
        MessageBox._count += 1
        self.key = 'dialog#%d' % MessageBox._count
        self.title, self.lines, self.kind = title, list(lines), kind
        self.on_ok = on_ok              # [확인]을 누르거나 밟았을 때 할 일
        self.pos = pos                  # (x, y)를 주면 가운데 대신 그 자리에 연다
        self.center = pos is None
        w = max(gfx.text_width(ln, 12) for ln in self.lines) + 100
        self.size = (max(360, w), TITLE_H + 40 + 20 * len(self.lines) + 50)
        self.button = (0, 0, 0, 0)

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, WHITE)
        cy = top - 24 - 10 * (len(self.lines) - 1)
        if self.kind == 'warning':
            gfx.triangle(l + 38, cy, 34, (255, 185, 0))
            gfx.text('!', l + 38, cy - 3, 20, BLACK, FONT_BOLD, align='center')
        else:
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

    def platforms(self):
        # 포인터가 창 안에서 [확인] 단추를 밟을 수 있다
        bl, bb, bw, bh = self.button
        return [(bl, bl + bw, bb + bh)] if bw else []

    def press(self):
        import shell
        shell.close(self)
        if self.on_ok:
            self.on_ok()

    def stepped_by(self, player):
        bl, bb, bw, bh = self.button
        return bw and abs(player.y - (bb + bh)) < 1 and player.x + 42 > bl and player.x + 6 < bl + bw

    def mouse_down(self, mx, my, now):
        bl, bb, bw, bh = self.button
        if bl <= mx < bl + bw and bb <= my < bb + bh:
            self.press()


# ==================================================================== 메모장
class Notepad(App):
    group = 'notepad'
    icon = 'notepad'
    size = (640, 460)
    LINE_H, FONT_SIZE = 20, 14
    _count = 0

    def __init__(self, node):
        Notepad._count += 1
        self.node = node
        self.key = 'notepad:%d' % node.id if node else 'notepad#%d' % Notepad._count
        self.box = textbox.TextBox(self, list(node.lines) if node else [''], multiline=True, on_save=self.save)
        self.area = (0, 0, 0, 0)
        self.first = 0                 # 맨 위에 보이는 줄

    @property
    def title(self):
        name = self.node.name if self.node else '제목 없음'
        return ('*' if self.box.dirty else '') + name + ' - Windows 메모장'

    @property
    def lines(self):
        return self.box.lines

    def save(self):
        """Ctrl+S: 파일에 쓴다. 제목 없는 문서는 바탕 화면에 새 텍스트 문서로 저장한다"""
        import fs
        if self.node is None:
            self.node = fs.DESKTOP_FOLDER.add(fs.Node(fs.DESKTOP_FOLDER.unique_name('제목 없음', '.txt'), fs.FILE))
        self.node.lines = list(self.box.lines)
        self.box.dirty = False

    def mouse_down(self, mx, my, now):
        l, b, w, h = self.area
        if l <= mx < l + w and b <= my < b + h:
            textbox.set_focus(self.box)
            self.box.click(mx, my, l + 6, b + h - 4 + self.first * self.LINE_H, self.LINE_H, self.FONT_SIZE)

    def wheel(self, dy):
        self.first = max(0, min(len(self.box.lines) - 1, self.first - dy * 3))

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, WHITE)
        x = l + 8
        for m in ('파일(F)', '편집(E)', '서식(O)', '보기(V)', '도움말(H)'):
            x += gfx.text(m, x, top - 10, 12) + 14
        gfx.line(l, top - 20, l + w, top - 20, (240, 240, 240))
        # 글자 영역: 커서가 보이도록 위아래로 넘긴다
        self.area = (l, b + 22, w - 17, h - 42)
        rows = max(1, int((h - 46) // self.LINE_H))
        if self.box.row < self.first:
            self.first = self.box.row
        elif self.box.row >= self.first + rows:
            self.first = self.box.row - rows + 1
        gfx.push_clip(*self.area)
        self.box.draw(l + 6, top - 24, self.LINE_H, self.FONT_SIZE, TEXT, textbox.focus is self.box,
                      self.first, rows + 1)
        gfx.pop_clip()
        # 상태 표시줄 · 스크롤바
        gfx.fill(l, b, w, 22, (240, 240, 240))
        gfx.line(l, b + 22, l + w, b + 22, (220, 220, 220))
        x = l + w - 30
        pos = 'Ln %d, Col %d' % (self.box.row + 1, self.box.col + 1)
        for part in ('UTF-8', 'Windows (CRLF)', '100%', pos):
            x -= gfx.text(part, x, b + 11, 12, align='right') + 34
            gfx.line(x + 18, b + 2, x + 18, b + 20, (210, 210, 210))
        self.scrollbar = (l + w - 17, b + 22, 17, h - 42)
        gfx.fill(*self.scrollbar, (240, 240, 240))
        n = max(1, len(self.box.lines))
        bar_h = max(30, (h - 76) * min(1.0, rows / n))
        k = self.first / max(1, n - rows) if n > rows else 0
        gfx.fill(l + w - 13, top - 37 - bar_h - (h - 76 - bar_h) * k, 9, bar_h, (194, 194, 194))

    def ladders(self):
        return [self.scrollbar] if hasattr(self, 'scrollbar') else []


# ==================================================================== 웹 브라우저 오류 화면의 공룡 (browser.py가 씀)
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
APPS = {'paint': Paint, 'vscode': VSCode, 'kakao': Kakao, 'terminal': Terminal}
