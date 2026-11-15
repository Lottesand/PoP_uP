// 버그 벌레: 기획서의 버그 아이콘처럼 단순한 초록 실루엣 (머리, 더듬이, 가운데가 갈라진 몸, 다리 6개).
// 13 x 12 칸, 게임에서 4배로 그린다.
//   options.state: crawl | dash | rest | stun | hurt
import { hex } from "../../core/index.js";

export const STATES = {
  crawl: { duration: 0.5, frames: 2 },
  dash: { duration: 0.25, frames: 2 },
  rest: { duration: 1.0, frames: 1 },
  stun: { duration: 0.5, frames: 2 },
  hurt: { duration: 0.25, frames: 2 },
};

export const meta = {
  name: "Bug",
  desc: "The plan deck's bug icon as a flat green pixel silhouette, wiggling its legs as it crawls.",
  tags: ["enemy", "bug", "loop"],
  size: [16, 14],
  origin: [8, 13],
  duration: 1.0,
  loop: true,
  fps: 12,
  bg: "dark",
  options: { state: "crawl", seed: 1 },
};

const GREEN = hex("#2e8b3a"), FLASH = hex("#ffffff");

// 몸통 (다리 없이). G = 초록, 가운데 세로 틈이 등딱지 선
const BODY = [
  "...G.....G...",
  "....G...G....",
  "....GGGGG....",
  ".............",
  "...GGG.GGG...",
  "...GGG.GGG...",
  "..GGGG.GGGG..",
  "..GGGG.GGGG..",
  "...GGG.GGG...",
  "....GG.GG....",
];
// 다리: (줄, 왼쪽 끝 x). 오른쪽은 대칭. 프레임마다 위아래로 한 칸씩 번갈아 움직인다
const LEGS = [[4, 1], [7, 0], [9, 1]];

export function draw(p, t, o) {
  const st = STATES[o.state] ? o.state : "crawl";
  const S = STATES[st], f = Math.floor((t / S.duration) * S.frames) % S.frames;
  const c = st === "hurt" && f === 1 ? FLASH : GREEN;
  const upside = st === "stun";
  const lean = st === "dash" ? 1 : 0;                     // 돌진: 윗부분이 앞으로 기운다
  const ox = -6, oy = -11 + (st === "crawl" && f ? -1 : 0);
  const put = (x, y, dx = 0) => p.px(ox + x + dx, oy + (upside ? 9 - y : y), c);

  BODY.forEach((row, y) => [...row].forEach((k, x) => { if (k === "G") put(x, y, y < 4 ? lean : 0); }));
  LEGS.forEach(([y, x], i) => {
    const wiggle = st === "rest" ? 0 : (i + f) % 2 ? -1 : 1;     // 다리를 번갈아 든다
    const ly = y + (st === "crawl" || st === "dash" || upside ? wiggle : 0);
    const reach = st === "rest" ? 1 : 0;
    for (const lx of [x + reach, x + 1 + reach]) {
      put(lx, ly);
      put(12 - lx, ly);                                         // 오른쪽 다리 (좌우 대칭)
    }
  });
}
