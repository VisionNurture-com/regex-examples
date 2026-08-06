#!/usr/bin/env python3
"""キャプチャする丸かっこと、しない丸かっこ (?:) の差を測る。

入門記事は「取り出す必要がないなら (?:) を使う」と書く。理由として速度が
挙げられることも多いが、**どれくらい違うのか**はほとんど書かれていない。
書き方を変えるだけで速くなるなら覚える価値があるし、誤差なら
「読みやすさのために使う」と言い直したほうが正直である。

3 つの条件で比べる。

  A) 日付の 3 グループ       グループが少ない現実的なパターン
  B) 20 グループ             取り出さない丸かっこが積み上がった場合
  C) 量指定子の中のグループ    (foo|bar)+ のように繰り返しごとに記録が発生する場合
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import format_sec, measure, save  # noqa: E402

ITERATIONS = 20_000

CASES = [
    {
        "name": "A 日付の 3 グループ",
        "subject": "納品日は 2026-06-12 です",
        "variants": {
            "キャプチャあり": r"(\d{4})-(\d{2})-(\d{2})",
            "非キャプチャ (?:)": r"(?:\d{4})-(?:\d{2})-(?:\d{2})",
            "かっこなし": r"\d{4}-\d{2}-\d{2}",
        },
    },
    {
        "name": "B 20 グループ",
        "subject": "x" * 20 + "END",
        "variants": {
            "キャプチャあり": "(x)" * 20,
            "非キャプチャ (?:)": "(?:x)" * 20,
            "かっこなし": "x" * 20,
        },
    },
    {
        "name": "C 量指定子の中のグループ",
        "subject": "foobar" * 40 + "!",
        "variants": {
            "キャプチャあり": r"(foo|bar)+",
            "非キャプチャ (?:)": r"(?:foo|bar)+",
        },
    },
]


def main() -> int:
    print(f"1 条件あたり {ITERATIONS:,} 回検索した時間を測ります。\n")
    results = []

    for case in CASES:
        subject = case["subject"]
        print(f"■ {case['name']}（入力 {len(subject)} 文字）")

        row = {"name": case["name"], "subject_length": len(subject), "variants": {}}
        baseline = None

        for label, pattern in case["variants"].items():
            compiled = re.compile(pattern)

            def run() -> None:
                for _ in range(ITERATIONS):
                    compiled.search(subject)

            stat = measure(run)
            matched = compiled.search(subject)
            row["variants"][label] = {
                "pattern": pattern,
                "groups": compiled.groups,
                "matched": matched.group() if matched else None,
                **stat,
            }

            if baseline is None:
                baseline = stat["min_sec"]
            ratio = baseline / stat["min_sec"]
            print(
                f"   {label:<18} グループ数 {compiled.groups:>2}"
                f"   {format_sec(stat['min_sec']):>10}"
                f"   キャプチャあり比 {ratio:>4.2f} 倍"
            )
        results.append(row)
        print()

    path = save("004-group-capture-bench", {"iterations": ITERATIONS, "cases": results})
    print(f"測定結果を保存しました: {path}")
    print("\n注: 最小値で比較しています（他プロセスの影響は上振れとして出るため）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
