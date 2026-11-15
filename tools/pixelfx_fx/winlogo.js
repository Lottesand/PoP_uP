// 윈도우 로고 폭탄: 네 칸 창 로고에 얼굴과 짧은 다리. 11 x 14 칸, 게임에서 4배로 그린다.
//   options.state: walk | chase | count | stun | hurt
import { hex } from "../../core/index.js";

export const STATES = {
  walk: { duration: 0.5, frames: 2 },
  chase: { duration: 0.25, frames: 2 },
  count: { duration: 0.5, frames: 2 },     // 터지기 전: 칸이 벌어졌다 오므라들며 빨갛게 깜빡
  stun: { duration: 0.5, frames: 2 },
  hurt: { duration: 0.25, frames: 2 },
};

export const meta = {
  name: "Windows logo",
  desc: "A four-pane Windows logo with a face and stubby feet; waddles, runs, then swells and flashes red before it blows.",
  tags: ["enemy", "windows", "bomb", "loop"],
  size: [16, 18],
  origin: [8, 16],
  duration: 1.0,
  loop: true,
  fps: 12,
  bg: "dark",
  options: { state: "walk", seed: 1 },
};

const BLUE = hex("#0078d7"), DEEP = hex("#005a9e"), RED = hex("#e81123"), ORANGE = hex("#ff8c00"),
  INK = hex("#1b1b1b"), EYE = hex("#ffffff"), FLASH = hex("#ffffff");

export function draw(p, t, o) {
  const st = STATES[o.state] ? o.state : "walk";
  const S = STATES[st], f = Math.floor((t / S.duration) * S.frames) % S.frames;
  const gap = st === "count" && f === 1 ? 2 : 1;
  const hot = st === "count";
  const flash = st === "hurt" && f === 1;
  const bob = (st === "walk" || st === "chase") && f ? -1 : 0;
  const size = 5, W = size * 2 + gap;
  const x0 = -Math.floor(W / 2), top = -2 - W + bob;

  // 발
  const step = st === "chase" ? 2 : 1;
  const fl = (st === "walk" || st === "chase") ? (f ? step : -step) : 0;
  p.rect(x0 + 2 + fl, -2, 2, 2, INK);
  p.rect(x0 + W - 4 - fl, -2, 2, 2, INK);
  // 네 칸 (위 두 칸은 밝은 파랑, 아래 두 칸은 조금 진하게)
  for (const [cx, cy, k] of [[0, 0, 0], [size + gap, 0, 0], [0, size + gap, 1], [size + gap, size + gap, 1]]) {
    let c = k ? DEEP : BLUE;
    if (hot) c = f ? RED : (k ? RED : ORANGE);
    if (flash) c = FLASH;
    p.rect(x0 + cx, top + cy, size, size, c);
  }
  // 얼굴: 위 두 칸에 눈, 아래 가운데 틈 위에 입
  if (flash) return;
  const ey = top + 2;
  if (st === "stun") {
    for (const ex of [x0 + 2, x0 + W - 3]) { p.px(ex - 1, ey, EYE); p.px(ex + 1, ey, EYE); p.px(ex, ey + 1, EYE); }
  } else {
    for (const ex of [x0 + 2, x0 + W - 3]) { p.px(ex, ey, EYE); p.px(ex, ey + 1, EYE); }
    if (st === "chase" || hot) {           // 화난 눈썹
      p.px(x0 + 1, ey - 1, INK); p.px(x0 + W - 2, ey - 1, INK);
    }
  }
  const my = top + size + gap + 1;
  if (hot) { p.rect(x0 + Math.floor(W / 2) - 1, my, 3, 2, INK); }      // 겁에 질려 벌린 입
  else { p.rect(x0 + Math.floor(W / 2) - 1, my, 3, 1, INK); }
}
