# 프로그램 열기·오류 창·오른쪽 클릭 메뉴처럼 여러 곳에서 쓰는 "운영체제" 기능
import fs
import apps
import browser                  # apps.APPS['browser']를 채운다
import paint                    # apps.APPS['paint']를 채운다
import breaker                  # apps.APPS['breaker']를 채운다
import photos
import drawing
from context_menu import ContextMenu


def attach_samples():
    """예시 그림 파일(사진 백업 폴더 · 바탕 화면)에 실제 그림을 붙인다"""
    todo = [fs.DOCUMENTS, fs.DESKTOP_FOLDER]
    while todo:
        folder = todo.pop()
        for node in folder.children:
            if node.kind == fs.FILE and node.name in fs.SAMPLE_PICTURES:
                node.picture = drawing.sample(fs.SAMPLE_PICTURES[node.name])
            elif node.kind == fs.FOLDER:
                todo.append(node)


attach_samples()

wm = None          # play_mode가 init에서 넣어 준다
menu = None        # 지금 열린 오른쪽 클릭 메뉴
drag = None        # 탐색기 창에서 끌고 있는 항목 (노드, 누른 x, 누른 y) - 창들 위에 아이콘을 그린다
on_player = None   # (노드, x, y) → 포인터 위에 놓였으면 장착하고 True. play_mode가 넣어 준다
over_player = None  # (노드, x, y) → 포인터 위에 끌고 와서 장착할 수 있으면 True


# ---------------------------------------------------------------- 끌어 놓기 (바탕화면 ⇄ 폴더 창)
def drop_target(mx, my, node):
    """(mx, my)에 놓으면 들어갈 (폴더, 바탕화면 칸). 놓을 수 없으면 (None, None)
    폴더 창 안 → 그 창 폴더 (커서 밑이 폴더 항목이면 그 폴더) / 창 밖 → 바탕 화면 (커서 밑이 폴더 아이콘이면 그 폴더)"""
    import desktop
    from config import TASKBAR_H
    win, part = wm.hit(mx, my)
    if win is not None:
        folder = getattr(win.app, 'node', None)
        if part[0] != 'client' or folder is None or not folder.is_container():
            return None, None
        item = win.app.item_at(mx, my) if hasattr(win.app, 'item_at') else None
        if item is not None and item is not node and item.is_container():
            return item.resolve(), None
        return folder.resolve(), None
    if my < TASKBAR_H:
        return None, None
    for icon in fs.DESKTOP_FOLDER.children:
        if icon.pos is None or icon is node:
            continue
        l, b, w, h = desktop.cell_rect(*icon.pos)
        if l <= mx < l + w and b <= my < b + h:
            return (icon.resolve(), None) if icon.is_container() else (fs.DESKTOP_FOLDER, desktop.cell_at(mx, my))
    return fs.DESKTOP_FOLDER, desktop.cell_at(mx, my)


def drop(node, mx, my):
    """끌던 항목을 놓는다: 다른 폴더면 옮기고, 바탕 화면이면 놓은 칸에 둔다. 옮겼으면 True"""
    import desktop
    if on_player is not None and on_player(node, mx, my):
        return True                     # 그림 파일을 포인터 위에 놓으면 무기로 장착 (파일은 그 자리에 남는다)
    target, cell = drop_target(mx, my, node)
    if target is None:
        return False
    if target is not node.parent and not fs.move(node, target):
        return False
    if target is fs.DESKTOP_FOLDER and cell is not None:
        used = {n.pos for n in fs.DESKTOP_FOLDER.children if n is not node and n.pos is not None}
        node.pos = cell if cell not in used else desktop.nearest_free(used, cell)
    return True


def drop_label(node, mx, my):
    """끌고 있는 동안 커서 옆 안내: '→ 바탕 화면(으)로 이동'"""
    if over_player is not None and over_player(node, mx, my):
        return '+ 포인터에게 무기로 장착'
    target, cell = drop_target(mx, my, node)
    if target is None or target is node.parent:
        return None
    if target.kind == fs.RECYCLE:
        return '→ 휴지통(으)로 이동'
    return '→ %s(으)로 이동' % target.name


def show_menu(items, x, y):
    global menu
    menu = ContextMenu(items, x, y) if items else None


def close_menu():
    global menu
    menu = None


def window_of(app):
    for win in wm.windows:
        if win.app is app:
            return win
    return None


def close(app):
    win = window_of(app)
    if win:
        wm.close(win)


def error(title, *lines):
    wm.open(apps.MessageBox(title, lines))


def denied(node):
    error(node.name, '%s에 액세스할 수 없습니다.' % node.name, '', '액세스가 거부되었습니다.')


def open_folder(node):
    import explorer
    node = node.resolve()
    if node.locked:
        denied(node)
        return
    for win in wm.windows:
        if getattr(win.app, 'node', None) is node and win.app.group == 'explorer':
            wm.focus(win)
            return
    wm.open(explorer.Explorer(node))


def open_text(node):
    win = wm.find('notepad:%d' % node.id)
    if win:
        wm.focus(win)
    else:
        wm.open(apps.Notepad(node))


def open_node(node):
    node = node.resolve()
    if node.locked:
        denied(node)
    elif node.is_container():
        open_folder(node)
    elif node.kind == fs.APP:
        open_key(node.app)
    elif node is fs.BREAKER:
        open_key('breaker')
    elif getattr(node, 'picture', None) is not None:
        photos.open_picture(wm, node)
    elif node.custom_icon in (None, 'text_file'):
        open_text(node)
    else:
        error(node.name, '이 파일을 열 수 있는 앱이 없습니다.')


def open_key(key):
    """시작 메뉴·작업 표시줄 단추가 쓰는 프로그램 키"""
    folders = {'this_pc': fs.ROOT, 'recycle_bin': fs.TRASH, 'documents': fs.DOCUMENTS, 'explorer': fs.QUICK_ACCESS}
    if key in folders:
        open_folder(folders[key])
    elif key == 'notepad':
        wm.open(apps.Notepad(None))
    elif key in apps.APPS:
        win = wm.find(key)
        if win:
            wm.focus(win)
        else:
            wm.open(apps.APPS[key]())
