# 창 안에 그려지는 프로그램 화면들. draw(l, b, w, h, active)는 창의 내용 영역을 받는다.
import time
import gfx
from config import *

G_BACK, G_FWD, G_UP, G_REFRESH, G_SEARCH = '\uE72B', '\uE72A', '\uE74A', '\uE72C', '\uE721'
G_CHEVRON_R, G_CHEVRON_D, G_STAR, G_CLOUD, G_NETWORK = '\uE76C', '\uE70D', '\uE735', '\uE753', '\uE968'
LINE = (229, 229, 229)


class App:
    key = 'app'
    title = ''
    icon = 'folder'
    size = (800, 520)

    def draw(self, l, b, w, h, active):
        gfx.fill(l, b, w, h, WHITE)


# ==================================================================== 파일 탐색기
class Explorer(App):
    size = (900, 560)

    def __init__(self, key, title, icon, path, items, ribbon=('파일', '홈', '공유', '보기')):
        self.key, self.title, self.icon = key, title, icon
        self.path, self.items, self.ribbon = path, items, ribbon

    def draw(self, l, b, w, h, active):
        top = b + h
        gfx.fill(l, b, w, h, WHITE)
        # 리본 탭
        y = top - 24
        gfx.fill(l, y, w, 24, WHITE)
        x = l
        for i, tab in enumerate(self.ribbon):
            tw = gfx.text_width(tab, 12) + 26
            if i == 0:
                gfx.fill(x, y, tw, 24, ACCENT)
            gfx.text(tab, x + tw / 2, y + 12, 12, WHITE if i == 0 else TEXT, align='center')
            x += tw
        gfx.symbol('\uE70E', l + w - 40, y + 12, 10, TEXT_GRAY)
        gfx.symbol('\uE897', l + w - 16, y + 12, 12, ACCENT)
        gfx.line(l, y, l + w, y, LINE)
        # 주소 표시줄
        y -= 34
        for i, g in enumerate((G_BACK, G_FWD, G_CHEVRON_D, G_UP)):
            gfx.symbol(g, l + 16 + i * 26 - (6 if i == 2 else 0), y + 17, 10 if i != 2 else 8,
                       (160, 160, 160) if i in (1, 2) else (60, 60, 60))
        ax, aw = l + 112, w - 112 - 230
        gfx.frame(ax, y + 5, aw, 24, (217, 217, 217))
        gfx.icon(self.icon, 16, ax + 6, y + 9)
        px = ax + 28
        for part in self.path:
            gfx.symbol(G_CHEVRON_R, px + 4, y + 17, 8, (110, 110, 110))
            px += 14 + gfx.text(part, px + 12, y + 17, 12)
        gfx.symbol(G_REFRESH, ax + aw - 14, y + 17, 10, (90, 90, 90))
        sx = l + w - 220
        gfx.frame(sx, y + 5, 210, 24, (217, 217, 217))
        gfx.text(self.path[-1] + ' 검색', sx + 8, y + 17, 12, (120, 120, 120))
        gfx.symbol(G_SEARCH, sx + 195, y + 17, 10, (90, 90, 90))
        # 왼쪽 탐색 창
        status_h = 22
        nav_w = min(200, w // 4)
        body_b, body_t = b + status_h, y - 4
        nav = [('star', '바로 가기'), ('cloud', 'OneDrive'), ('this_pc', '내 PC'), ('net', '네트워크')]
        ny = body_t - 18
        for kind, name in nav:
            if name == self.path[0]:
                gfx.fill(l + 1, ny - 11, nav_w - 2, 22, SELECT_FILL)
            if kind == 'this_pc':
                gfx.icon('this_pc', 16, l + 26, ny - 8)
            else:
                g = {'star': G_STAR, 'cloud': G_CLOUD, 'net': G_NETWORK}[kind]
                c = {'star': ACCENT, 'cloud': (40, 120, 220), 'net': (60, 90, 130)}[kind]
                gfx.symbol(g, l + 34, ny, 14, c)
            gfx.symbol(G_CHEVRON_R, l + 12, ny, 8, (150, 150, 150))
            gfx.text(name, l + 50, ny, 12)
            ny -= 30
        gfx.line(l + nav_w, body_b, l + nav_w, body_t, LINE)
        # 항목들
        self.draw_items(l + nav_w + 1, body_b, w - nav_w - 1, body_t - body_b)
        # 상태 표시줄
        gfx.text('%d개 항목' % self.count(), l + 14, b + status_h / 2, 12)

    def count(self):
        return len(self.items)

    def draw_items(self, l, b, w, h):
        cell_w, cell_h = 96, 92
        cols = max(1, (w - 16) // cell_w)
        for i, (icon, name) in enumerate(self.items):
            cx = l + 12 + (i % cols) * cell_w
            ct = b + h - 10 - (i // cols) * cell_h
            gfx.icon(icon, 48, cx + (cell_w - 48) / 2, ct - 54)
            if icon == 'lock' or name.endswith('(잠김)'):
                gfx.icon('lock', 16, cx + (cell_w - 48) / 2 + 34, ct - 54)
            for j, ln in enumerate(gfx.wrap(name, cell_w - 8, 12)):
                gfx.text(ln, cx + cell_w / 2, ct - 66 - j * 16, 12, align='center')


class ThisPC(Explorer):
    def __init__(self):
        super().__init__('this_pc', '내 PC', 'this_pc', ['내 PC'], [])
        self.ribbon = ('파일', '컴퓨터', '보기')

    FOLDERS = ['3D 개체', '다운로드', '동영상', '문서', '바탕 화면', '사진', '음악']

    def count(self):
        return len(self.FOLDERS) + 2

    def draw_items(self, l, b, w, h):
        top = b + h - 8
        folders = self.FOLDERS
        y = self.group('폴더 (%d)' % len(folders), l, top, w)
        cols = max(1, (w - 20) // 220)
        for i, name in enumerate(folders):
            x = l + 20 + (i % cols) * 220
            yy = y - 30 - (i // cols) * 62
            gfx.icon('folder', 48, x, yy - 24)
            gfx.text(name, x + 58, yy, 12)
        y -= 30 + ((len(folders) - 1) // cols + 1) * 62
        y = self.group('장치 및 드라이브 (2)', l, y, w)
        for i, (icon, name, used, info, locked) in enumerate((
                ('drive', '로컬 디스크 (C:)', 0.62, '476GB 중 181GB 사용 가능', False),
                ('usb', 'USB 드라이브 (E:)', 0.0, '접근 거부됨', True))):
            x = l + 20 + i * 300
            gfx.icon(icon, 48, x, y - 64)
            if locked:
                gfx.icon('lock', 24, x + 28, y - 64)
            gfx.text(name, x + 58, y - 22, 12)
            gfx.fill(x + 58, y - 44, 196, 14, (230, 230, 230))
            gfx.frame(x + 58, y - 44, 196, 14, (188, 188, 188))
            gfx.fill(x + 59, y - 43, int(194 * used), 12, (38, 160, 218))
            gfx.text(info, x + 58, y - 58, 12, CLOSE_RED if locked else TEXT_GRAY)

    def group(self, name, l, top, w):
        gfx.symbol(G_CHEVRON_D, l + 14, top - 12, 8, (90, 90, 90))
        tw = gfx.text(name, l + 26, top - 12, 12, (30, 57, 145))
        gfx.line(l + 34 + tw, top - 12, l + w - 16, top - 12, LINE)
        return top - 24


# ==================================================================== 메모장
class Notepad(App):
    size = (640, 460)

    def __init__(self, key, filename, lines):
        self.key, self.title, self.icon = key, filename + ' - Windows 메모장', 'notepad'
        self.lines = lines

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
def documents():
    return Explorer('documents', '문서', 'folder', ['내 PC', '문서'],
                    [('folder', '과제'), ('folder', '사진 백업'), ('folder', '숨겨진 폴더'),
                     ('text_file', '탈출 계획.txt'), ('text_file', 'readme.txt'), ('usb', 'USB 열쇠 (잠김)')])


def recycle_bin():
    return Explorer('recycle_bin', '휴지통', 'recycle_bin', ['휴지통'],
                    [('text_file', '비밀번호 힌트.txt'), ('folder', '옛날 드라이버'), ('text_file', 'key_part_2.txt')],
                    ribbon=('파일', '홈', '공유', '보기', '관리'))


def escape_note():
    return Notepad('notepad', '탈출 계획.txt',
                   ['1. 바탕화면에서 나가는 길 찾기', '2. 인터넷 차단기 끄기',
                    '3. %appdata% 권한 얻기', '4. 휴지통 열기', '5. 나를 압축해서 USB로 내보내기', '',
                    '- 포인터'])


APPS = {
    'this_pc': ThisPC, 'recycle_bin': recycle_bin, 'documents': documents, 'notepad': escape_note,
    'browser': Browser, 'paint': Paint, 'vscode': VSCode, 'kakao': Kakao, 'terminal': Terminal,
}
