class Rect:
    """좌하단 (x, y) 기준 사각형. pico2d 좌표계(위로 갈수록 y 증가)와 같다."""

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def l(self):
        return self.x

    @property
    def b(self):
        return self.y

    @property
    def r(self):
        return self.x + self.w

    @property
    def t(self):
        return self.y + self.h

    def overlaps(self, o, eps=0.0):
        # 변이 맞닿기만 한 건 겹침이 아니다
        return (self.l < o.r - eps and o.l < self.r - eps and
                self.b < o.t - eps and o.b < self.t - eps)

    def contains(self, o):
        return o.l >= self.l and o.r <= self.r and o.b >= self.b and o.t <= self.t

    def contains_point(self, px, py):
        return self.l <= px <= self.r and self.b <= py <= self.t

    def inflate(self, d):
        return Rect(self.x - d, self.y - d, self.w + 2 * d, self.h + 2 * d)

    def __repr__(self):
        return f'Rect({self.x:.0f}, {self.y:.0f}, {self.w:.0f}, {self.h:.0f})'
