"""컴퓨터 한 대를 랜덤으로 만든다: 폴더 구조, PIN 위치, PIN 번호, 아이콘 배치, 금고 위치."""
from config import *
from os_window import OSWindow, Icon, Plate, Key, Shelf, Vault

ROOT_NAMES = ['문서', '사진', '다운로드', '게임', '과제', '음악']
SUB_NAMES = ['백업', '새 폴더', '2025', '임시', '중요', '보관함', '스크린샷', '압축해제']
DECOY_FILES = [
    ('장보기.txt', ['우유, 계란, 라면', '휴지 꼭 사기']),
    ('과제.txt', ['2DGP 기획서 마감', '발표 영상 1분 30초!!']),
    ('PIN_old.txt', ['금고 PIN (만료됨)', '{fake}', '새 번호는 다른 폴더에']),
    ('readme.txt', ['이 컴퓨터는 감시 중입니다', '수상한 파일 발견 시 신고']),
    ('일기.txt', ['오늘 바탕화면에서', '작은 사람을 본 것 같다...']),
]

FOLDER_SIZE = (300, 220)
MEMO_SIZE = (280, 150)


def _random_pos(rng, w, h):
    return rng.randint(220, CANVAS_W - w - 40), rng.randint(TASKBAR_H + 20, CANVAS_H - h - 10)


def _layout_icons(win):
    for i, ic in enumerate(win.icons):
        col, row = i % 4, i // 4
        ic.lx, ic.ly = 14 + col * 68, win.design_h - 58 - row * 66


def _memo(rng, wid, title, lines):
    w = OSWindow(wid, title, 'memo', *_random_pos(rng, *MEMO_SIZE), *MEMO_SIZE)
    w.lines = lines
    return w


def generate(rng):
    """반환: (windows, desktop_icons, pin)"""
    windows = []
    pin = ''.join(rng.choice('0123456789') for _ in range(4))
    fake = ''.join(rng.choice('0123456789') for _ in range(4))
    next_id = [0]

    def new_id():
        next_id[0] += 1
        return next_id[0]

    # 폴더 트리 (깊이 2)
    roots = rng.sample(ROOT_NAMES, 3)
    sub_pool = rng.sample(SUB_NAMES, len(SUB_NAMES))
    decoys = rng.sample(DECOY_FILES, len(DECOY_FILES))
    leaf_folders = []
    root_icons = []
    for name in roots:
        root = OSWindow(new_id(), name, 'folder', *_random_pos(rng, *FOLDER_SIZE), *FOLDER_SIZE)
        windows.append(root)
        root_icons.append(Icon(name, root.wid, 'folder'))
        for _ in range(rng.randint(1, 2)):
            sub_name = sub_pool.pop()
            sub = OSWindow(new_id(), f'{name}\\{sub_name}', 'folder', *_random_pos(rng, *FOLDER_SIZE), *FOLDER_SIZE)
            windows.append(sub)
            root.icons.append(Icon(sub_name, sub.wid, 'folder'))
            leaf_folders.append(sub)
        if decoys and rng.random() < 0.8:
            fname, lines = decoys.pop()
            memo = _memo(rng, new_id(), fname, [ln.format(fake=fake) for ln in lines])
            windows.append(memo)
            root.icons.append(Icon(fname, memo.wid, 'file'))

    # 진짜 PIN 메모는 랜덤 하위 폴더 안에, 나머지 하위 폴더에도 미끼 파일을 섞는다
    pin_folder = rng.choice(leaf_folders)
    pin_memo = _memo(rng, new_id(), 'PIN.txt', ['금고 PIN', pin, '계산기 발판을 순서대로 밟을 것'])
    windows.append(pin_memo)
    pin_folder.icons.append(Icon('PIN.txt', pin_memo.wid, 'file'))
    for sub in leaf_folders:
        if sub is not pin_folder and decoys:
            fname, lines = decoys.pop()
            memo = _memo(rng, new_id(), fname, [ln.format(fake=fake) for ln in lines])
            windows.append(memo)
            sub.icons.append(Icon(fname, memo.wid, 'file'))
    for win in windows:
        if win.kind == 'folder':
            rng.shuffle(win.icons)
            _layout_icons(win)

    # 계산기: 숫자 발판 2줄 + 열쇠가 나올 선반
    calc = OSWindow(new_id(), '계산기', 'calc', *_random_pos(rng, 340, 330), 340, 330)
    digits = list('1234567890')
    for i, d in enumerate(digits[:5]):
        calc.items.append(Plate(14 + i * 58, 0, d))
    for i, d in enumerate(digits[5:]):
        calc.items.append(Plate(40 + i * 58, 90, d))
    calc.items.append(Shelf(10, 180, 80, 10))
    calc.items.append(Key(40, 192))
    windows.append(calc)

    # 금고: 처음부터 열려 있지만 "응답 없음"이라 움직일 수 없고, 높은 곳에 있다
    safe_x = rng.randint(640, CANVAS_W - 340)
    safe_y = rng.randint(430, CANVAS_H - 210)
    safe = OSWindow(new_id(), '금고.exe', 'safe', safe_x, safe_y, 300, 200, frozen=True)
    safe.items.append(Vault(180, 0))
    safe.opened = True
    windows.insert(0, safe)   # 맨 아래 레이어

    # 바탕화면 아이콘: 왼쪽 줄에 랜덤 순서로
    desk_icons = root_icons + [Icon('계산기', calc.wid, 'app')]
    rng.shuffle(desk_icons)
    for i, ic in enumerate(desk_icons):
        ic.x, ic.y = 30, CANVAS_H - 90 - i * 80

    return windows, desk_icons, pin
