# pixelfx(https://github.com/patch-gg/pixelfx)의 렌더러로 포인터 도트 캐릭터를 스프라이트 시트로 뽑아 game/assets에 넣는다.
#   git clone https://github.com/patch-gg/pixelfx ../pixelfx     (PoP_uP 옆에 한 번만)
#   python tools/build_sprites.py [pixelfx 폴더]                  (Node 18 이상 필요)
#
# 윈도우 10처럼 단순하고 둔탁하게: 게임에서는 도트를 4배로 키워 그린다.
# 적: tools/pixelfx_fx/bug.js, caret.js, winlogo.js → game/assets/sprites/<이름>.png (줄 = 상태)
# 포인터: tools/pixelfx_fx/pointer.js를 pixelfx의 src/fx/custom/에 복사해서 표정·모드별로 뽑는다.
#   game/assets/sprites/pointer_<mode>_<face>.png : 줄 = 상태(STATES 순서), 칸 = 12프레임
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, 'game', 'assets')

STATES = ['idle', 'run', 'jump', 'fall', 'climb', 'hurt', 'poke']
FACES = ['calm', 'angry', 'dizzy']
MODES = ['off', 'on']
FRAMES = 12
FPS = 12


def node(pixelfx, *args):
    r = subprocess.run(['node', *args], cwd=pixelfx, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit('pixelfx 실패: %s' % r.stderr)
    return r.stdout.strip()


def frames_of(png, meta):
    sheet = Image.open(png).convert('RGBA')
    j = json.load(open(meta, encoding='utf-8'))
    out = []
    for fr in j['frames']:
        r = fr['frame']
        out.append(sheet.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])))
    return out, j['meta']['pixelfx']


# ==================================================================== 포인터
def build_pointer(pixelfx, tmp):
    custom = os.path.join(pixelfx, 'src', 'fx', 'custom')
    os.makedirs(custom, exist_ok=True)
    shutil.copy(os.path.join(HERE, 'pixelfx_fx', 'pointer.js'), os.path.join(custom, 'pointer.js'))
    out_dir = os.path.join(ASSETS, 'sprites')
    os.makedirs(out_dir, exist_ok=True)
    cell = origin = None
    for mode in MODES:
        for face in FACES:
            rows = []
            for state in STATES:
                out = os.path.join(tmp, 'pointer', mode, face, state)
                node(pixelfx, 'tools/render.mjs', 'custom/pointer', '--sheet', '--no-actor', '--out', out,
                     '--opts', json.dumps({'state': state, 'face': face, 'mode': mode}))
                base = os.path.join(out, 'custom', 'pointer', 'pointer')
                frames, meta = frames_of(base + '.png', base + '.json')
                rows.append(frames[:FRAMES])
                cell, origin = meta['frameSize'], meta['pivot']
            sheet = Image.new('RGBA', (cell[0] * FRAMES, cell[1] * len(STATES)))
            for r, frames in enumerate(rows):
                for c, f in enumerate(frames):
                    sheet.paste(f, (c * cell[0], r * cell[1]))
            sheet.save(os.path.join(out_dir, 'pointer_%s_%s.png' % (mode, face)))
    with open(os.path.join(out_dir, 'pointer.json'), 'w', encoding='utf-8') as f:
        json.dump({'states': STATES, 'cell': cell, 'frames': FRAMES, 'fps': FPS, 'origin': origin}, f, indent=1)
    print('pointer: %d sheets, cell %s' % (len(MODES) * len(FACES), cell))


# ==================================================================== 적
ENEMIES = {
    'bug': ['crawl', 'dash', 'rest', 'stun', 'hurt'],
    'caret': ['idle', 'aim', 'shoot', 'stun', 'hurt'],
    'winlogo': ['walk', 'chase', 'count', 'stun', 'hurt'],
}


def build_enemies(pixelfx, tmp):
    custom = os.path.join(pixelfx, 'src', 'fx', 'custom')
    out_dir = os.path.join(ASSETS, 'sprites')
    for name, states in ENEMIES.items():
        shutil.copy(os.path.join(HERE, 'pixelfx_fx', name + '.js'), os.path.join(custom, name + '.js'))
        rows = []
        for state in states:
            out = os.path.join(tmp, name, state)
            node(pixelfx, 'tools/render.mjs', 'custom/' + name, '--sheet', '--no-actor', '--out', out,
                 '--opts', json.dumps({'state': state}))
            base = os.path.join(out, 'custom', name, name)
            frames, meta = frames_of(base + '.png', base + '.json')
            rows.append(frames[:FRAMES])
            cell, origin = meta['frameSize'], meta['pivot']
        sheet = Image.new('RGBA', (cell[0] * FRAMES, cell[1] * len(states)))
        for r, frames in enumerate(rows):
            for c, f in enumerate(frames):
                sheet.paste(f, (c * cell[0], r * cell[1]))
        sheet.save(os.path.join(out_dir, name + '.png'))
        with open(os.path.join(out_dir, name + '.json'), 'w', encoding='utf-8') as f:
            json.dump({'states': states, 'cell': cell, 'frames': FRAMES, 'fps': FPS, 'origin': origin}, f, indent=1)
        print('%s: %d states, cell %s' % (name, len(states), cell))


def main():
    pixelfx = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '..', 'pixelfx'))
    if not os.path.exists(os.path.join(pixelfx, 'tools', 'render.mjs')):
        raise SystemExit('pixelfx 체크아웃을 찾을 수 없습니다: %s' % pixelfx)
    with tempfile.TemporaryDirectory() as tmp:
        build_pointer(pixelfx, tmp)
        build_enemies(pixelfx, tmp)


if __name__ == '__main__':
    main()
