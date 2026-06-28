#!/usr/bin/env node
// codex_goal_watch.mjs — opt-in 요금가드 워처 (Codex flavor, 벤더중립 가드의 Codex 절반)
//
// 왜 워처인가: Claude는 Stop 훅(command, continue:false)으로 /goal 루프를 인-훅 정지할 수 있지만,
// Codex의 /goal 런타임은 Stop 훅 continue:false를 무시한다(실측). 네이티브 정지 = app-server
// JSON-RPC `thread/goal/clear`. 그래서 외부 워처가 폴링하다 한도 초과 시 활성 goal thread를 clear한다.
//
// 가드 *정책*은 워처가 갖지 않는다 — `coach --guard-check`(usage-coach)가 단일 정본으로 판정한다
// (guard-enabled 플래그·7일 하이브리드 OR·pace/floor 모두 거기서). 워처는 그 결정을 *집행*만 한다.
//   coach --guard-check 계약: 통과 = exit 0 + 무출력 / 정지 = exit≠0 또는 stdout에 사유 1줄.
//   coach 미설치/조회실패 = fail-open(정지하지 않음 — 작업 안 죽임).
//
// 전제: 같은 머신에서 `codex remote-control start`로 공유 데몬이 떠 있고, 사용자의 대화형 /goal
// 세션이 그 데몬에 붙어 있다. 워처는 `codex app-server proxy`로 같은 데몬에 JSON-RPC로 접속해
// 현재 로드된(활성) thread만 열거(`thread/loaded/list`)하고 goal이 있는 것을 clear한다.
//
// 실행:  node _shared/guard/codex_goal_watch.mjs
// 환경:  GUARD_INTERVAL=초(기본 60) · GUARD_SOCK=소켓경로(생략 시 기본 control socket)
//        GUARD_PROVIDERS=coach에 넘길 provider(기본 codex)
// 정지:  Ctrl-C. 가드 자체를 끄려면 `coach guard off`(워처는 coach 결정을 따르므로 즉시 무력화).

import { spawn } from "node:child_process";
import readline from "node:readline";

const INTERVAL_MS = Math.max(5, parseInt(process.env.GUARD_INTERVAL || "60", 10)) * 1000;
const SOCK = process.env.GUARD_SOCK || "";
const PROVIDERS = process.env.GUARD_PROVIDERS || "codex";

const log = (...a) => console.log(new Date().toISOString(), ...a);

// ── coach --guard-check: 단일 정본 판정. true=정지해야 함, false=통과/판정불가(fail-open) ──
function shouldStop() {
  return new Promise((resolve) => {
    // command -v 로 coach 부재 시 fail-open(정지 안 함). 셸 경유라 PATH 함정도 흡수.
    const sh = `command -v coach >/dev/null 2>&1 && coach --guard-check --providers ${PROVIDERS}`;
    const child = spawn("/bin/sh", ["-c", sh], { stdio: ["ignore", "pipe", "pipe"] });
    let out = "";
    child.stdout.on("data", (d) => (out += d));
    const timer = setTimeout(() => child.kill("SIGTERM"), 30000);
    child.on("close", (code) => {
      clearTimeout(timer);
      // coach 부재 → sh exit 0 + 무출력 → 통과. 정지 = exit≠0 또는 사유 출력.
      const stop = code !== 0 || out.trim().length > 0;
      resolve({ stop, reason: out.trim() || (code !== 0 ? `coach --guard-check exit ${code}` : "") });
    });
    child.on("error", () => { clearTimeout(timer); resolve({ stop: false, reason: "" }); });
  });
}

// ── app-server JSON-RPC over `codex app-server proxy` (stdio ↔ control socket) ──
let app = null;
let nextId = 1;
const pending = new Map();

function startProxy() {
  const args = ["app-server", "proxy"];
  if (SOCK) args.push("--sock", SOCK);
  app = spawn("codex", args, { stdio: ["pipe", "pipe", "pipe"] });
  app.stderr.on("data", (d) => log("[proxy.stderr]", d.toString().trim()));
  app.on("exit", (code, sig) => {
    log("[proxy.exit]", code, sig);
    for (const [, e] of pending) e.reject(new Error("proxy exited"));
    pending.clear();
    process.exit(code === 0 ? 0 : 1);
  });
  const rl = readline.createInterface({ input: app.stdout });
  rl.on("line", (raw) => {
    let msg;
    try { msg = JSON.parse(raw); } catch { return; }
    if (Object.prototype.hasOwnProperty.call(msg, "id") && pending.has(msg.id)) {
      const e = pending.get(msg.id);
      pending.delete(msg.id);
      e.resolve(msg);
    }
  });
}

function request(method, params = {}, timeoutMs = 30000) {
  const id = nextId++;
  app.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => { pending.delete(id); reject(new Error(`timeout ${method}`)); }, timeoutMs);
    pending.set(id, { resolve: (m) => { clearTimeout(t); resolve(m); }, reject: (e) => { clearTimeout(t); reject(e); } });
  });
}

const threadIdOf = (it) => it?.id || it?.threadId || it?.thread?.id || null;

// 현재 로드된 thread 중 active goal을 가진 것을 clear. 반환 = clear한 threadId 배열.
async function clearActiveGoals(reason) {
  const cleared = [];
  let cursor = null;
  do {
    const r = await request("thread/loaded/list", cursor ? { cursor } : {});
    const data = r?.result?.data || [];
    for (const it of data) {
      const tid = threadIdOf(it);
      if (!tid) continue;
      let goal = null;
      try { goal = (await request("thread/goal/get", { threadId: tid }))?.result?.goal; } catch { continue; }
      if (!goal) continue; // goal 없음 → 건너뜀
      try {
        const c = await request("thread/goal/clear", { threadId: tid });
        if (c?.result?.cleared) { cleared.push(tid); log("[CLEARED]", tid, "—", reason); }
      } catch (e) { log("[clear.error]", tid, String(e)); }
    }
    cursor = r?.result?.nextCursor || null;
  } while (cursor);
  return cleared;
}

async function tick() {
  let decision;
  try { decision = await shouldStop(); } catch { return; } // 판정 실패 → fail-open
  if (!decision.stop) return;
  log("[GUARD]", "한도 초과 판정 —", decision.reason, "→ 활성 goal thread clear 시도");
  try { await clearActiveGoals(decision.reason); } catch (e) { log("[guard.error]", String(e)); }
}

async function main() {
  startProxy();
  await request("initialize", {
    clientInfo: { name: "codex-goal-guard-watch", version: "1" },
    capabilities: { experimentalApi: true, requestAttestation: false },
  }).catch((e) => { log("[initialize.error]", String(e)); process.exit(1); });
  log("요금가드 워처 시작 — interval", INTERVAL_MS / 1000 + "s, providers", PROVIDERS,
      "(가드 on/off는 `coach guard on/off`)");
  await tick();
  setInterval(tick, INTERVAL_MS);
}

process.on("SIGINT", () => { log("종료합니다."); if (app && !app.killed) app.kill("SIGTERM"); process.exit(0); });
main().catch((e) => { log("[fatal]", String(e)); process.exit(1); });
