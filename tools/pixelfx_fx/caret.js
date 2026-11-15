// 캐럿: 글자 입력 커서(I자). 7 x 13 칸, 게임에서 4배로 그린다. 가로대 사이 기둥에 눈이 있다.
//   options.state: idle | aim | shoot | stun | hurt
import { hex } from "../../core/index.js";

export const STATES = {
  idle: { duration: 1.0, frames: 2 },      // 입력 커서처럼 깜빡인다
  aim: { duration: 0.25, frames: 2 },      // 빨갛게 떨며 조준
  shoot: { duration: 1.0, frames: 1 },     // 쏜 반동으로 뒤로 젖혀짐
  stun: { duration: 0.5, frames: 2 },
  hurt: { duration: 0.25, frames: 2 },
};

export const meta = {
  name: "Caret",
  desc: "A text-input caret with eyes on its stem: blinks, shivers red while aiming, kicks back when it fires.",
  tags: ["enemy", "caret", "loop"],
  size: [12, 16],
  origin: [6, 14],
  duration: 1.0,
  loop: true,
  fps: 12,
  bg: "dark",
  options: { state: "idle", seed: 1 },
};

const INK = hex("#1b1b1b"), DIM = hex("#8a8a8a"), RED = hex("#e81123"), EYE = hex("#ffffff"), FLASH = hex("#ffffff");

export function draw(p, t, o) {
  const st = STATES[o.state] ? o.state : "idle";
  const S = STATES[st], f = Math.floor((t / S.duration) * S.frames) % S.frames;
  let c = INK, dx = 0, lean = 0;
  if (st === "idle" && f === 1) c = DIM;
  if (st === "aim") { c = RED; dx = f ? 1 : -1; }
  if (st === "shoot") lean = -1;
  if (st === "hurt" && f === 1) c = FLASH;
  const sway = st === "stun" ? (f ? 1 : -1) : 0;
  const x0 = -3 + dx, top = -13;
  const at = (x, y, col) => p.px(x0 + x + (y < 6 ? lean + sway : 0), top + y, col);
  // 위 가로대 (7칸), 눈이 있는 머리 (5칸), 기둥 (3칸 굵기), 아래 가로대
  for (let x = 0; x < 7; x++) { at(x, 0, c); at(x, 12, c); }
  for (let y = 1; y <= 5; y++) for (let x = 1; x <= 5; x++) at(x, y, c);
  for (let y = 6; y < 12; y++) for (let x = 2; x <= 4; x++) at(x, y, c);
  at(1, 11, c); at(5, 11, c);
  // 눈 (기둥 위쪽): 기절하면 감고, 조준하면 노려본다
  if (!(st === "hurt" && f === 1)) {
    if (st === "stun") { at(2, 4, EYE); at(4, 4, EYE); }
    else { at(2, 3, EYE); at(4, 3, EYE); at(2, 4, EYE); at(4, 4, EYE); }
    if (st === "aim") { at(2, 3, c); at(4, 3, c); }
  }
}
