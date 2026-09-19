#!/usr/bin/env python3
"""1 行に同じ形が複数あるとき、書き方で「取り出せる中身」が変わることを確かめる。

bench.py と why.py は 1 か所だけマッチさせて速さを測った。実務のログは
1 行に同じ形のフィールドが複数並ぶ。そこでは速さより先に **取り出した結果
そのもの** が書き方で変わる。

  実験 D: 引用符で囲まれた 3 つのフィールドを取り出す（貪欲 / 最短 / 否定クラス）
  実験 E: 回数を決め打つ {n} だけでは足りない場合を見る
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import format_sec, measure, save  # noqa: E402

ROWS = 20_000

PATTERNS = {
    "貪欲 \".*\"": r'".*"',
    "最短 \".*?\"": r'".*?"',
    "否定クラス \"[^\"]*\"": r'"[^"]*"',
}


def build_log(rows: int) -> str:
    """引用符フィールドを 3 つ持つアクセスログを組み立てる。"""
    line = (
        '203.0.113.{n} - - [03/Aug/2026:10:15:{s:02d} +0900] '
        '"GET /articles/regex-003 HTTP/1.1" 200 5120 '
        '"https://example.com/index" "Mozilla/5.0 (X11; Linux x86_64)"'
    )
    return "\n".join(line.format(n=i % 254 + 1, s=i % 60) for i in range(rows))


def experiment_c(log: str) -> dict:
    print(f"■ 実験 D: {ROWS:,} 行から引用符フィールドを取り出す")
    print(f"  1 行に 3 つあるので、正しく取れれば {ROWS * 3:,} 件になります。\n")
    first_line = log.split("\n", 1)[0]
    rows = {}
    for label, pattern in PATTERNS.items():
        compiled = re.compile(pattern)
        found = compiled.findall(log)
        stat = measure(lambda: compiled.findall(log))
        sample = compiled.findall(first_line)
        rows[label] = {
            "pattern": pattern,
            "count": len(found),
            "first_line_count": len(sample),
            "first_line_head": sample[0] if sample else None,
            **stat,
        }
        head = sample[0] if sample else ""
        print(f"  {label:<22} 取得 {len(found):>7,} 件   {format_sec(stat['min_sec']):>9}")
        print(f"  {'':<22} 1 行目の 1 件目（{len(head):>3} 文字）: {head[:56]}{'…' if len(head) > 56 else ''}")
    print()
    return rows


def experiment_d(log: str) -> dict:
    print("■ 実験 E: ステータスコード 200 だけを取り出したい")
    first_line = log.split("\n", 1)[0]
    probes = {
        "回数を指定しない \\d+": r"\d+",
        "3 回に決め打つ \\d{3}": r"\d{3}",
        "前後の境界も足す \\b\\d{3}\\b": r"\b\d{3}\b",
        "置かれる場所も指定する \" (\\d{3}) ": r'" (\d{3}) ',
    }
    rows = {}
    for label, pattern in probes.items():
        sample = re.findall(pattern, first_line)
        total = len(re.findall(pattern, log))
        rows[label] = {"pattern": pattern, "first_line": sample, "count": total}
        print(f"  {label:<28} 1 行目 {len(sample):>2} 件: {sample}")
    print()
    return rows


def main() -> int:
    log = build_log(ROWS)
    print(f"ログの全長 {len(log):,} 文字（{ROWS:,} 行）\n")
    c = experiment_c(log)
    d = experiment_d(log)
    save("003-quantifier-extract", {"rows": ROWS, "experiment_c": c, "experiment_d": d})
    print("■ 読み取れること（実測に基づく）")
    print("  貪欲は 1 行を 1 件にまとめてしまう。件数も中身も壊れる")
    print("  最短と否定クラスは同じ件数を返す。ここでは結果が一致する")
    print("  速さでは否定クラスが有利。結果が同じなら速いほうを選べる")
    print("  {n} で回数を決めても、長い数字の一部を拾う。境界の指定が要る")
    print("  境界を足しても 3 桁の数字なら何でも拾う。場所の指定まで要る")
    return 0


if __name__ == "__main__":
    sys.exit(main())
