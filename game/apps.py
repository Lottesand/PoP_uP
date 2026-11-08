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


# ==================================================================== 프로그램 목록
def documents():
    return Explorer('documents', '문서', 'folder', ['내 PC', '문서'],
                    [('folder', '과제'), ('folder', '사진 백업'), ('folder', '숨겨진 폴더'),
                     ('text_file', '탈출 계획.txt'), ('text_file', 'readme.txt'), ('usb', 'USB 열쇠 (잠김)')])


def recycle_bin():
    return Explorer('recycle_bin', '휴지통', 'recycle_bin', ['휴지통'],
                    [('text_file', '비밀번호 힌트.txt'), ('folder', '옛날 드라이버'), ('text_file', 'key_part_2.txt')],
                    ribbon=('파일', '홈', '공유', '보기', '관리'))
