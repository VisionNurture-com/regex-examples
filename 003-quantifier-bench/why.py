#!/usr/bin/env python3
"""なぜ否定文字クラスが速いのかを、条件を分けて確かめる。

bench.py はタグの中身と後続テキストを同時に伸ばしていた。それだと
「どちらが効いているのか」が分からない。ここでは片方ずつ動かす。

  実験 A: タグの中身だけ伸ばす（後続は固定）
  実験 B: 後続テキストだけ伸ばす（タグの中身は固定）
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
ITERATIONS = 2_000


def run(label: str, cases: list[tuple[int, int]]) -> list[dict]:
    print(f"■ {label}")
    rows = []
    for inner, trailing in cases:
        subject = "<" + "x" * inner + ">" + "y" * trailing
        line = f"  中身 {inner:>4} / 後続 {trailing:>5} :"
        row = {"inner": inner, "trailing": trailing, "patterns": {}}
        for name, pattern in PATTERNS.items():
            compiled = re.compile(pattern)

            def go() -> None:
                for _ in range(ITERATIONS):
                    compiled.search(subject)

            stat = measure(go)
            row["patterns"][name] = {"pattern": pattern, **stat}
            line += f"  {name.split()[0]} {format_sec(stat['min_sec']):>9}"
        rows.append(row)
        print(line)
    print()
    return rows


def main() -> int:
    print(f"1 条件あたり {ITERATIONS} 回検索した時間の最小値です。\n")
    a = run("実験 A: タグの中身だけ伸ばす（後続は 2000 で固定）",
            [(50, 2000), (200, 2000), (800, 2000)])
    b = run("実験 B: 後続テキストだけ伸ばす（中身は 200 で固定）",
            [(200, 500), (200, 2000), (200, 8000)])
    save("003-quantifier-why", {"iterations": ITERATIONS, "experiment_a": a, "experiment_b": b})
    print("■ 読み取れること（実測に基づく）")
    print("  実験 A（中身を伸ばす）で伸びるのは最短だけ。貪欲はほとんど変わらない")
    print("  実験 B（後続を伸ばす）で伸びるのは貪欲だけ。最短はほとんど変わらない")
    print("  つまり貪欲と最短は弱点の場所が違う。速い書き方は入力の形で入れ替わる")
    print("  否定クラスはどちらの条件でもほぼ一定で、> に出会った時点で止まる")
    return 0


if __name__ == "__main__":
    sys.exit(main())
