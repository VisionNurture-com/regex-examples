#!/usr/bin/env node
/**
 * ReDoS 検出ツールの結果を、実測した挙動と突き合わせる。
 *
 * 検出ツールの比較は「どれだけ見つけたか」で語られることが多いが、
 * 安全なパターンを危険と言ってしまう側（誤検出）を測った資料は見当たらない。
 * ここでは正解ラベルを人の主張ではなく **実測** で決める。
 *
 *   1. 各パターンに攻撃文字列を長さを変えて与え、実行時間を測る
 *   2. 入力を伸ばしたときに時間が跳ね上がるものを「危険」とする
 *   3. その正解に対して各ツールの判定を突き合わせる
 *
 * 対象は JavaScript の正規表現エンジン（各ツールが解析対象にしているもの）。
 */

import { writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const RESULTS = join(HERE, '..', '..', 'tools', 'results');

// 依存が入っていないと ERR_MODULE_NOT_FOUND のスタックだけが出て、
// 何をすればよいのかが読み取れない。先に確かめて手順のほうを出す。
if (!existsSync(join(HERE, '..', 'node_modules'))) {
  console.error('006-redos-safety/node_modules がありません。先に依存を入れてください。');
  console.error('  cd 006-redos-safety && npm ci');
  process.exit(1);
}

const { default: safeRegex } = await import('safe-regex');
const { isSafe } = await import('redos-detector');
const { checkSync } = await import('recheck');

/** 攻撃文字列を長さ n で作る関数つきのパターン一覧 */
const CORPUS = [
  // --- 危険とされる定番の形 ---
  { name: '(a+)+$', re: /(a+)+$/, attack: (n) => 'a'.repeat(n) + '!' },
  { name: '(a|a)*$', re: /(a|a)*$/, attack: (n) => 'a'.repeat(n) + '!' },
  { name: '(x+x+)+y', re: /(x+x+)+y/, attack: (n) => 'x'.repeat(n) + '!' },
  { name: '([a-zA-Z]+)*$', re: /([a-zA-Z]+)*$/, attack: (n) => 'a'.repeat(n) + '!' },
  { name: '(a*)*b', re: /(a*)*b/, attack: (n) => 'a'.repeat(n) + '!' },
  { name: '(\\w+\\s?)*$', re: /(\w+\s?)*$/, attack: (n) => 'a'.repeat(n) + '!' },
  { name: '^(\\d+)+$', re: /^(\d+)+$/, attack: (n) => '1'.repeat(n) + '!' },

  // --- 安全なはずの形 ---
  { name: '^a+$', re: /^a+$/, attack: (n) => 'a'.repeat(n) + '!' },
  { name: '^[^>]*>$', re: /^[^>]*>$/, attack: (n) => 'x'.repeat(n) + '!' },
  { name: '^\\d{4}-\\d{2}-\\d{2}$', re: /^\d{4}-\d{2}-\d{2}$/, attack: (n) => '1'.repeat(n) },
  { name: '^[\\w.+-]+@[\\w-]+\\.[\\w.-]+$', re: /^[\w.+-]+@[\w-]+\.[\w.-]+$/, attack: (n) => 'a'.repeat(n) + '@' },
  { name: '^https?://[\\w./%-]+$', re: /^https?:\/\/[\w./%-]+$/, attack: (n) => 'https://' + 'a'.repeat(n) + ' ' },
  { name: '^\\d{3}-\\d{4}$', re: /^\d{3}-\d{4}$/, attack: (n) => '1'.repeat(n) },
];

const GROUND_TRUTH_LENGTHS = [10, 14, 18, 22, 26];
const ABORT_SEC = 2.0;
// 入力を 4 文字伸ばしたときに時間が何倍になるかで判定する。
// 絶対時間のしきい値で判定すると、爆発しているが上限に届いていないものを
// 「安全」と取り違える（1 秒のしきい値で実際に 5 件取り違えた）。
const GROWTH_FACTOR = 3.0;

// 1 回きりで測ると、最初の（短い）条件だけが割高に出て倍率が小さく見える。
// 実測（2026-08-05・(a+)+$）: そのまま測ると 4 文字あたり 9.6 倍だが、下記のとおり測ると 15.4 倍。
// tools/measure.py の timed_min と同じ方針を JavaScript 側にも置く。
const WARMUP_RUNS = 5;
const REPEAT_UNDER_SEC = 0.01;
const MAX_REPEATS = 15;

/** 1 回測り、短時間で終わったときだけ追加でまわして最小値を返す */
function timedMin(fn) {
  let start = process.hrtime.bigint();
  fn();
  let best = Number(process.hrtime.bigint() - start) / 1e9;

  if (best < REPEAT_UNDER_SEC) {
    for (let i = 1; i < MAX_REPEATS; i += 1) {
      start = process.hrtime.bigint();
      fn();
      best = Math.min(best, Number(process.hrtime.bigint() - start) / 1e9);
    }
  }
  return best;
}

/** 実測で危険かどうかを決める */
function measureGroundTruth(entry) {
  const warm = entry.attack(12);
  for (let i = 0; i < WARMUP_RUNS; i += 1) entry.re.test(warm);

  const timings = [];
  for (const n of GROUND_TRUTH_LENGTHS) {
    const subject = entry.attack(n);
    const elapsed = timedMin(() => entry.re.test(subject));
    timings.push({ n, sec: elapsed });
    if (elapsed > ABORT_SEC) break;
  }
  const worst = timings[timings.length - 1];
  if (worst.sec > ABORT_SEC) {
    return { vulnerable: true, reason: '上限時間を超えた', timings, worstSec: worst.sec, growth: null };
  }

  // 意味のある時間が出ている区間だけで倍率を見る（測定誤差どうしの割り算を避ける）。
  // 最小値を採るようにしたことで、安全なパターンは n をいくつにしても 41 ナノ秒で並んだ。
  // これは計時の分解能そのもので、割り算しても意味が出ない。「時間が伸びない」と報告する。
  const measurable = timings.filter((t) => t.sec > 1e-5);
  if (measurable.length < 2) {
    return { vulnerable: false, reason: '時間が伸びない', timings, worstSec: worst.sec, growth: null };
  }
  const first = measurable[0];
  const last = measurable[measurable.length - 1];
  const steps = (last.n - first.n) / 4;
  const growth = steps > 0 ? Math.pow(last.sec / first.sec, 1 / steps) : 1;

  return {
    vulnerable: growth >= GROWTH_FACTOR,
    reason: `4 文字あたり ${growth.toFixed(1)} 倍`,
    timings,
    worstSec: worst.sec,
    growth,
  };
}

function runDetectors(entry) {
  const out = {};

  // safe-regex: true = 安全
  try {
    out['safe-regex'] = safeRegex(entry.re) ? 'safe' : 'vulnerable';
  } catch (e) {
    out['safe-regex'] = 'error';
  }

  // redos-detector: isSafe は真偽値ではなく { safe, score, trails } を返す。
  // 返り値をそのまま条件式に置くとオブジェクトは常に真になり、
  // 全件「安全」という誤った結果になる（実際にこれで 7 件取り違えた）。
  try {
    out['redos-detector'] = isSafe(entry.re).safe ? 'safe' : 'vulnerable';
  } catch (e) {
    out['redos-detector'] = 'error';
  }

  // recheck: status が vulnerable / safe / unknown
  try {
    const result = checkSync(entry.re.source, entry.re.flags);
    out['recheck'] = result.status;
  } catch (e) {
    out['recheck'] = 'error';
  }

  return out;
}

function verdictMark(verdict, truth) {
  if (verdict === 'error') return '⚠️';
  const saidVulnerable = verdict === 'vulnerable';
  if (saidVulnerable === truth) return '✅';
  return saidVulnerable ? '🟡' : '❌'; // 🟡 = 誤検出 / ❌ = 見逃し
}

function main() {
  console.log('正解ラベルは実測で決めます。');
  console.log(`攻撃文字列の長さ ${GROUND_TRUTH_LENGTHS.join(' / ')} で試し、`);
  console.log(`入力 4 文字あたりの時間が ${GROWTH_FACTOR} 倍以上に伸びるものを「危険」とします。\n`);

  const rows = [];
  const tools = ['safe-regex', 'redos-detector', 'recheck'];
  const tally = Object.fromEntries(tools.map((t) => [t, { hit: 0, miss: 0, falseAlarm: 0, error: 0 }]));

  const header = `${'パターン'.padEnd(34)}${'実測'.padEnd(26)}${tools.map((t) => t.padEnd(18)).join('')}`;
  console.log(header);
  console.log('-'.repeat(header.length));

  for (const entry of CORPUS) {
    const truth = measureGroundTruth(entry);
    const verdicts = runDetectors(entry);
    const truthLabel = truth.vulnerable
      ? `危険 ${truth.reason}`
      : `安全 ${truth.reason}`;

    let line = `${entry.name.padEnd(34)}${truthLabel.padEnd(26)}`;
    for (const tool of tools) {
      const mark = verdictMark(verdicts[tool], truth.vulnerable);
      line += `${mark} ${verdicts[tool]}`.padEnd(18);
      if (verdicts[tool] === 'error') tally[tool].error++;
      else if (mark === '✅') tally[tool].hit++;
      else if (mark === '🟡') tally[tool].falseAlarm++;
      else tally[tool].miss++;
    }
    console.log(line);
    rows.push({ pattern: entry.name, truth, verdicts });
  }

  const vulnerableCount = rows.filter((r) => r.truth.vulnerable).length;
  const safeCount = rows.length - vulnerableCount;

  console.log(`\n実測の内訳: 危険 ${vulnerableCount} 件 / 安全 ${safeCount} 件\n`);
  console.log(`${'ツール'.padEnd(20)}${'一致'.padEnd(8)}${'見逃し'.padEnd(10)}${'誤検出'.padEnd(10)}エラー`);
  console.log('-'.repeat(58));
  for (const tool of tools) {
    const t = tally[tool];
    console.log(
      `${tool.padEnd(20)}${String(t.hit).padEnd(8)}${String(t.miss).padEnd(10)}${String(t.falseAlarm).padEnd(10)}${t.error}`,
    );
  }

  console.log('\n凡例: ✅ 実測と一致 / ❌ 見逃し（危険を安全と判定）/ 🟡 誤検出（安全を危険と判定）');

  mkdirSync(RESULTS, { recursive: true });
  const path = join(RESULTS, '006-detector-comparison.json');
  writeFileSync(
    path,
    JSON.stringify(
      {
        measurement: '006-detector-comparison',
        node: process.version,
        growthFactor: GROWTH_FACTOR,
        abortSec: ABORT_SEC,
        lengths: GROUND_TRUTH_LENGTHS,
        rows,
        tally,
      },
      null,
      2,
    ) + '\n',
    'utf-8',
  );
  console.log(`\n測定結果を保存しました: ${path}`);
}

main();
