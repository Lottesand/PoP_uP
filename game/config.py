# 화면 크기, 윈도우 10 치수, 색, 폰트 경로
import os

W, H = 1920, 1080
ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, 'assets')

# 윈도우 10 (배율 100%) 기준 치수
TASKBAR_H = 40
TITLE_H = 31
CAPTION_BTN_W = 46
RESIZE_GRIP = 6
WIN_MIN_W, WIN_MIN_H = 240, 160
ICON_CELL_W, ICON_CELL_H = 76, 92
DOUBLE_CLICK = 0.4

# 윈도우 10 한국어판처럼 영문·숫자는 Segoe UI, 한글은 맑은 고딕으로 그린다
_FONTS = 'C:/Windows/Fonts/'
FONT = 'regular'
FONT_BOLD = 'bold'
FONT_SEMILIGHT = 'light'
UI_FONTS = {
    'regular': (_FONTS + 'segoeui.ttf', _FONTS + 'malgun.ttf'),
    'bold': (_FONTS + 'segoeuib.ttf', _FONTS + 'malgunbd.ttf'),
    'light': (_FONTS + 'segoeuisl.ttf', _FONTS + 'malgunsl.ttf'),
}
FONT_SYMBOL = _FONTS + 'segmdl2.ttf'   # Segoe MDL2 Assets: 윈도우 10 UI 기호

# assets/wallpaper_custom.jpg(또는 .png)를 넣으면 그 그림을 배경화면으로 쓴다
WALLPAPERS = ('wallpaper_custom.jpg', 'wallpaper_custom.png', 'wallpaper.png')

# 색 (r, g, b[, a])
ACCENT = (0, 120, 215)
ACCENT_LIGHT = (118, 185, 237)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TEXT = (0, 0, 0)
TEXT_GRAY = (110, 110, 110)
TITLE_INACTIVE = (153, 153, 153)
BORDER_ACTIVE = (24, 131, 215)
BORDER_INACTIVE = (170, 170, 170)
CLOSE_RED = (232, 17, 35)
CLOSE_RED_PRESSED = (241, 112, 122)
HOVER_GRAY = (229, 229, 229)
PRESSED_GRAY = (204, 204, 204)
TASKBAR_BG = (16, 16, 16, 230)
SELECT_FILL = (204, 232, 255)
SELECT_BORDER = (153, 209, 255)
