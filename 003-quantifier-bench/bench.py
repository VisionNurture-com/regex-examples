#!/usr/bin/env python3
"""貪欲・最短・否定文字クラスの実行時間を測る。

入門記事では「`.*` が食べすぎるなら `.*?`（最短）にしよう」と教わる。
挙動の説明としては正しいが、**速さの話としても正しいのか**は別問題である。
ここでは 3 つの書き方を同じ入力にかけて実測する。

  A) <.*>     貪欲
  B) <.*?>    最短
  C) <[^>]*>  否定文字クラス

タグの中身の長さと、その後ろに続く無関係なテキストの長さを振って、
書き方の差がどこで開くかを見る。
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import format_sec, measure, save  # noqa: E402

PATTERNS = {
    "貪欲 <.*>": r"<.*>",
    "最短 <.*?>": r"<.*?>",
    "否定クラス <[^>]*>": r"<[^>]*>",
}

# (タグ内の文字数, タグの後ろに続く無関係な文字数)
CASES = [
    (10, 100),
    (100, 1_000),
    (200, 2_000),
    (400, 8_000),
]

ITERATIONS = 2_000


def build_subject(inner: int, trailing: int) -> str:
    return "<" + "x" * inner + ">" + "y" * trailing


def main() -> int:
    results = []
    print(f"1 条件あたり {ITERATIONS} 回検索した時間を測ります。\n")

    for inner, trailing in CASES:
        subject = build_subject(inner, trailing)
        print(f"■ タグ内 {inner} 文字 / 後続 {trailing} 文字（全長 {len(subject)}）")

        row = {"inner": inner, "trailing": trailing, "length": len(subject), "patterns": {}}
        baseline = None

        for label, pattern in PATTERNS.items():
            compiled = re.compile(pattern)

            def run() -> None:
                for _ in range(ITERATIONS):
                    compiled.search(subject)

            stat = measure(run)
            matched = compiled.search(subject)
            row["patterns"][label] = {
                "pattern": pattern,
                "matched_length": len(matched.group()) if matched else None,
                **stat,
            }

            if baseline is None:
                baseline = stat["min_sec"]
            ratio = baseline / stat["min_sec"]
            print(
                f"   {label:<20} {format_sec(stat['min_sec']):>10}"
                f"   貪欲比 {ratio:>4.1f} 倍速い"
                f"   マッチ長 {len(matched.group()) if matched else '-'}"
            )
        results.append(row)
        print()

    path = save("003-quantifier-bench", {"iterations": ITERATIONS, "cases": results})
    print(f"測定結果を保存しました: {path}")
    print("\n注: 最小値で比較しています（他プロセスの影響は上振れとして出るため）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
