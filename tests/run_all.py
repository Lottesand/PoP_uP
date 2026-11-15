# 모든 시나리오 테스트를 차례로 실행한다:  python tests/run_all.py
# 테스트마다 pico2d 창이 잠깐 열렸다 닫힌다.
import glob
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
failed = []
for path in sorted(glob.glob(os.path.join(here, 'test_*.py'))):
    r = subprocess.run([sys.executable, path], capture_output=True, text=True, encoding='utf-8', errors='replace')
    last = (r.stdout.strip().splitlines() or ['(출력 없음)'])[-1]
    print('%-20s %s' % (os.path.basename(path), last))
    if r.returncode:
        failed.append(path)
        print(r.stdout[-2000:], r.stderr[-2000:])
sys.exit(1 if failed else 0)
