#!/usr/bin/env python3
"""測定の共通ハーネス。

記事に載る数値はすべてここを通す。測り方を 1 か所に集めておかないと、
章ごとに試行回数や集計方法がばらつき、数値どうしを比べられなくなる。

方針:
  - ウォームアップを本計測から分ける（初回実行は JIT やキャッシュの影響を受ける）
  - 同じ条件を複数回まわし、**最小値**を採る（他プロセスの影響は上振れとして出るため）
  - 中央値も併記する（最小値だけだと外れ値の少なさを判断できない）
  - 環境情報を必ず添える
"""

import json
import statistics
import time
from pathlib import Path
from typing import Callable

RESULTS_DIR = Path(__file__).parent / "results"


def measure(fn: Callable[[], object], *, runs: int = 7, warmup: int = 2) -> dict:
    """fn を warmup 回空回ししてから runs 回計測する。

    戻り値の時間はすべて秒。
    """
    for _ in range(warmup):
        fn()

    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)

    return {
        "runs": runs,
        "warmup": warmup,
        "min_sec": min(samples),
        "median_sec": statistics.median(samples),
        "max_sec": max(samples),
        "samples_sec": samples,
    }


# 1 回で 10 秒かかる条件（危険な正規表現など）は繰り返して測れない。
# だが速い条件まで 1 回きりで測ると他プロセスの影響がそのまま乗り、
# **条件どうしの倍率**が実際より小さく見える。
# 実測（2026-08-05・006 の (a+)+$）: 4 文字あたりの倍率が 1 回目 13.1 倍、2 回目以降 15.8〜16.7 倍。
# そこで、速い条件ほど多くまわして最小値を採る。
REPEAT_PLAN = ((0.01, 15), (1.0, 5))


def timed_min(fn: Callable[[], object]) -> float:
    """fn を 1 回測り、短時間で終わったときだけ追加でまわして最小値（秒）を返す。"""
    start = time.perf_counter()
    fn()
    best = time.perf_counter() - start

    repeats = 1
    for threshold, count in REPEAT_PLAN:
        if best < threshold:
            repeats = count
            break

    for _ in range(repeats - 1):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return best


def load_env() -> dict:
    """env_report.py が書き出した環境情報を読む。無ければ空で返す。"""
    path = RESULTS_DIR / "env.json"
    if not path.exists():
        return {"note": "tools/env_report.py を実行すると環境情報が入ります"}
    return json.loads(path.read_text(encoding="utf-8"))


def save(name: str, payload: dict) -> Path:
    """測定結果を環境情報つきで保存する。"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = {"measurement": name, "env": load_env(), **payload}
    path = RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def format_sec(value: float) -> str:
    """秒を読みやすい単位に直す。"""
    if value >= 1:
        return f"{value:.3f} s"
    if value >= 1e-3:
        return f"{value * 1e3:.3f} ms"
    return f"{value * 1e6:.1f} µs"
