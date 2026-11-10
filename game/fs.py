# 게임 속 가상 파일 시스템: 폴더·파일·바로 가기·드라이브가 나무 구조로 이어진다
FOLDER, FILE, APP, LINK, DRIVE, THIS_PC, RECYCLE, QUICK = (
    'folder', 'file', 'app', 'link', 'drive', 'this_pc', 'recycle', 'quick')
CONTAINERS = (FOLDER, DRIVE, THIS_PC, RECYCLE, QUICK)


class Node:
    _next_id = 0

    def __init__(self, name, kind=FOLDER, children=(), icon=None, lines=None, app=None, target=None, locked=False):
        Node._next_id += 1
        self.id = Node._next_id
        self.name, self.kind = name, kind
        self.children = []
        self.parent = None
        self.custom_icon = icon
        self.lines = list(lines) if lines else []
        self.app = app                  # APP: 실행할 프로그램 키
        self.target = target            # LINK: 가리키는 노드
        self.locked = locked
        self.pos = None                 # 바탕화면 격자 칸 (열, 행)
        self.origin = None              # 휴지통에 들어오기 전 폴더
        for c in children:
            self.add(c)

    def add(self, node):
        node.parent = self
        self.children.append(node)
        return node

    def remove(self, node):
        self.children.remove(node)
        node.parent = None

    @property
    def icon(self):
        if self.kind == LINK:
            return self.target.icon
        if self.custom_icon:
            return self.custom_icon
        if self.kind == FOLDER:
            return 'folder' if self.children else 'folder_empty'
        if self.kind == RECYCLE:
            return 'recycle_bin_full' if self.children else 'recycle_bin'
        return {FILE: 'text_file', THIS_PC: 'this_pc', DRIVE: 'drive', QUICK: 'explorer'}.get(self.kind, 'folder')

    def resolve(self):
        return self.target if self.kind == LINK else self

    def is_container(self):
        return self.resolve().kind in CONTAINERS

    def chain(self):
        """주소 표시줄에 보일 조상 목록 (가장 바깥부터)"""
        out, n = [], self
        while n is not None:
            out.append(n)
            n = n.parent
        return out[::-1]

    def contains(self, node):
        n = node
        while n is not None:
            if n is self:
                return True
            n = n.parent
        return False

    def unique_name(self, base, ext=''):
        names = {c.name for c in self.children}
        if base + ext not in names:
            return base + ext
        i = 2
        while '%s (%d)%s' % (base, i, ext) in names:
            i += 1
        return '%s (%d)%s' % (base, i, ext)


def _free_name(node, dest):
    if all(c.name != node.name for c in dest.children):
        return node.name
    base, dot, ext = node.name.rpartition('.')
    if node.kind != FILE or not base:
        return dest.unique_name(node.name)
    return dest.unique_name(base, dot + ext)


def can_modify(folder):
    return folder.kind in (FOLDER, DRIVE) and not folder.locked


def new_folder(parent):
    return parent.add(Node(parent.unique_name('새 폴더')))


def new_text(parent):
    return parent.add(Node(parent.unique_name('새 텍스트 문서', '.txt'), FILE))


def deletable(node):
    return node.parent is not None and node.parent.kind != THIS_PC and not node.locked and \
        not (node.kind == LINK and node.target.kind in (THIS_PC, RECYCLE))


def delete(node):
    """휴지통으로 보낸다. 휴지통 안에서 지우면 완전히 없앤다."""
    if not deletable(node):
        return False
    parent = node.parent
    parent.remove(node)
    if parent.kind == RECYCLE:
        return True
    node.origin = parent
    node.pos = None
    TRASH.add(node)
    return True


def restore(node):
    if node.parent is not TRASH or node.origin is None:
        return False
    TRASH.remove(node)
    dest = node.origin
    node.name = _free_name(node, dest)
    dest.add(node)
    node.origin = None
    return True


def move(node, dest):
    """node를 dest 폴더로 옮긴다. 옮겼으면 True"""
    dest = dest.resolve()
    if dest.kind == RECYCLE:
        return delete(node)
    if not can_modify(dest) or node.parent is dest or node.contains(dest) or not deletable(node):
        return False
    node.parent.remove(node)
    node.name = _free_name(node, dest)
    node.pos = None
    dest.add(node)
    return True


# ------------------------------------------------------------ 처음 상태
def _txt(name, *lines):
    return Node(name, FILE, lines=lines)


DOCUMENTS = Node('문서', children=[
    Node('과제', children=[_txt('2D게임프로그래밍 기획서.txt', 'PoP_uP 기획서 초안'),
                         _txt('제출 목록.txt', '1차 발표 영상', '2차 발표 영상')]),
    Node('사진 백업', children=[Node('IMG_0001.jpg', FILE, icon='image_file'),
                            Node('IMG_0002.jpg', FILE, icon='image_file')]),
    Node('숨겨진 폴더', children=[Node('설정', children=[_txt('인터넷 차단기.txt', '[차단기]', '상태 = 켜짐')])]),
    _txt('readme.txt', '이 PC의 주인은 자리를 비웠습니다.'),
    Node('USB 열쇠', FILE, icon='usb', locked=True),
])
DESKTOP_FOLDER = Node('바탕 화면')
DOWNLOADS = Node('다운로드')
PICTURES = Node('사진')
ROOT = Node('내 PC', THIS_PC, children=[
    Node('3D 개체'), DOWNLOADS, Node('동영상'), DOCUMENTS, DESKTOP_FOLDER, PICTURES, Node('음악'),
    Node('로컬 디스크 (C:)', DRIVE, children=[
        Node('Program Files', children=[Node('Google', children=[Node('Chrome')]), Node('Microsoft VS Code')]),
        Node('Users', children=[Node('Pointer', children=[Node('AppData', locked=True)])]),
        Node('Windows', children=[Node('System32'), Node('Fonts')]),
    ]),
    Node('USB 드라이브 (E:)', DRIVE, icon='usb', locked=True),
])
TRASH = Node('휴지통', RECYCLE)
for _n, _from in ((_txt('비밀번호 힌트.txt', '힌트: 처음 켠 날짜'), DOCUMENTS),
                  (Node('옛날 드라이버', children=[_txt('driver.inf')]), ROOT.children[7]),
                  (_txt('key_part_2.txt', '열쇠 조각 2/3'), DESKTOP_FOLDER)):
    _n.origin = _from
    TRASH.add(_n)
ONEDRIVE = Node('OneDrive')
NETWORK = Node('네트워크')
QUICK_ACCESS = Node('바로 가기', QUICK, children=[Node(n.name, LINK, target=n)
                                                for n in (DESKTOP_FOLDER, DOWNLOADS, DOCUMENTS, PICTURES)])

for _n in (Node('내 PC', LINK, target=ROOT), Node('휴지통', LINK, target=TRASH), Node('문서', LINK, target=DOCUMENTS),
           _txt('탈출 계획.txt', '1. 바탕화면에서 나가는 길 찾기', '2. 인터넷 차단기 끄기', '3. %appdata% 권한 얻기',
                '4. 휴지통 열기', '5. 나를 압축해서 USB로 내보내기', '', '- 포인터'),
           Node('Chrome', APP, icon='browser', app='browser'), Node('그림판', APP, icon='paint', app='paint'),
           Node('Visual Studio Code', APP, icon='vscode', app='vscode'),
           Node('카카오톡', APP, icon='kakao', app='kakao'),
           Node('명령 프롬프트', APP, icon='terminal', app='terminal')):
    DESKTOP_FOLDER.add(_n)

NAV = [QUICK_ACCESS, ONEDRIVE, ROOT, NETWORK]
