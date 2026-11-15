// PoP_uP 주인공 "포인터": 윈도우 10 손가락 커서. 12 x 16 칸의 둔탁한 도트로, 게임에서는 4배로 키워 그린다.
// tools/build_sprites.py가 pixelfx 체크아웃의 src/fx/custom/에 복사해서 상태·표정·모드별 스프라이트 시트로 뽑는다.
//   options.state: idle | run | jump | fall | climb | hurt | poke
//   options.face : calm (@_@) | angry (#_#) | dizzy (x_x)
//   options.mode : off (검은 테두리) | on (창 안: 윈도우 파란 테두리)
import { hex } from "../../core/index.js";

const STATES = {
  idle: { duration: 1.0, frames: 2 },
  run: { duration: 0.5, frames: 2 },
  jump: { duration: 1.0, frames: 1 },
  fall: { duration: 1.0, frames: 1 },
  climb: { duration: 0.5, frames: 2 },
  hurt: { duration: 0.25, frames: 2 },
  poke: { duration: 1.0, frames: 1 },
};

export const meta = {
  name: "Pointer",
  desc: "PoP_uP's hero: a chunky Windows hand cursor with a face on its palm, on two stubby feet.",
  tags: ["character", "cursor", "hand", "hero", "loop"],
  size: [20, 22],
  origin: [10, 20],
  duration: 1.0,                      // 모든 상태 주기가 1초를 나눠 떨어지게 맞췄다 (한 시트 = 12프레임)
  loop: true,
  fps: 12,
  bg: "dark",
  options: { state: "idle", face: "calm", mode: "off", seed: 1 },
};

const INK = hex("#000000"), WHITE = hex("#ffffff"), GRAY = hex("#c8c8c8"), BLUE = hex("#0078d7"),
  RED = hex("#e81123"), DARK = hex("#2b2b2b");

// 몸 (12 x 13). K 테두리, W 흰 손, G 오른쪽 그늘, C 소매
const HAND = [
  "....KK......",
  "...KWWK.....",
  "...KWWK.....",
  "...KWWKKK...",
  "...KWWKWWKK.",
  ".KKKWWWWWWGK",
  "KWWKWWWWWWGK",
  "KWWWWWWWWWGK",
  ".KWWWWWWWWGK",
  "..KWWWWWWWGK",
  "...KWWWWWGK.",
  "...KCCCCCCK.",
  "...KKKKKKKK.",
];

function frameOf(t, state) {
  const s = STATES[state];
  return Math.floor((t / s.duration) * s.frames) % s.frames;
}

// 몸 위아래 (dy)와 두 발의 x 위치, 발 들림
function poseOf(state, f) {
  switch (state) {
    case "run": return { dy: f ? -1 : 0, feet: f ? [[3, -1], [7, 0]] : [[3, 0], [7, -1]] };
    case "jump": return { dy: -1, feet: [[4, -1], [6, -1]] };
    case "fall": return { dy: 0, feet: [[2, 0], [8, 0]] };
    case "climb": return { dy: f ? -1 : 0, feet: f ? [[4, -1], [6, 0]] : [[4, 0], [6, -1]] };
    case "hurt": return { dy: 0, feet: [[3, 0], [7, 0]] };
    case "poke": return { dy: -1, feet: [[1, 0], [8, 0]] };        // 찌르기: 몸을 쭉 펴고 다리를 벌려 버틴다
    default: return { dy: f ? 1 : 0, feet: [[3, 0], [7, 0]] };
  }
}

export function draw(p, t, o) {
  const state = o.state in STATES ? o.state : "idle";
  const f = frameOf(t, state);
  const pose = poseOf(state, f);
  const face = state === "hurt" ? "dizzy" : o.face;
  const flash = state === "hurt" && f === 1;
  const edge = flash ? RED : o.mode === "on" ? BLUE : INK;
  const ox = -6, oy = -15 + pose.dy;          // 소매 아랫줄이 y = -3, 그 밑 두 줄이 발

  for (const [fx, lift] of pose.feet) p.rect(ox + fx, -2 + lift, 3, 2, DARK);
  HAND.forEach((row, y) => [...row].forEach((k, x) => {
    if (k === ".") return;
    const c = { K: edge, W: flash ? hex("#ffd0d4") : WHITE, G: GRAY, C: DARK }[k];
    p.px(ox + x, oy + y, c);
  }));

  // 손바닥 표정: 눈 둘 (x 4, 7), 입 (x 5~6)
  const ey = oy + 7;
  if (face === "dizzy") {
    for (const ex of [4, 7]) { p.px(ox + ex, ey - 1, INK); p.px(ox + ex + 1, ey, INK); p.px(ox + ex, ey + 1, INK); }
  } else {
    const blink = state === "idle" && t % 1 > 0.85;
    for (const ex of [4, 7]) {
      p.px(ox + ex, ey, INK);
      if (!blink) p.px(ox + ex, ey - 1, INK);
    }
    if (face === "angry") { p.px(ox + 3, ey - 2, INK); p.px(ox + 8, ey - 2, INK); }
  }
  p.px(ox + 5, oy + 9, INK);
  p.px(ox + 6, oy + 9, INK);
}
