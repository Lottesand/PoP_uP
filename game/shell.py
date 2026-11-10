# 프로그램 열기·오류 창·오른쪽 클릭 메뉴처럼 여러 곳에서 쓰는 "운영체제" 기능
import fs
import apps
from context_menu import ContextMenu

wm = None          # play_mode가 init에서 넣어 준다
menu = None        # 지금 열린 오른쪽 클릭 메뉴


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
