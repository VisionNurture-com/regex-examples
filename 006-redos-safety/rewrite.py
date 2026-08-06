#!/usr/bin/env python3
"""入れ子の量指定子を「平ら」に書き換えて止める。

bench.py はアトミックグループと所有量指定子で止めた。だが JavaScript には
どちらも無い。そこで残る手が **パターンそのものの書き換え** である。

書き換えは意味を変えかねない。ここでは短い文字列を総当たりして、
書き換えの前後で判定が一致するかを確かめてから、実行時間を比べる。
最後に「入力長の上限」がどこまで効くのかも測る。

⚠️ 危険な形は入力長を小さく保っている。本番のコードには持ち込まないこと。
"""

import itertools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import format_sec, save, timed_min  # noqa: E402

# 名前の入力欄でよく書かれる形。量指定子の中に量指定子があり、危険な形にあたる。
DANGER = r"^([a-zA-Z]+ ?)+$"

CANDIDATES = {
    "案A 空白で区切って並べる": r"^[a-zA-Z]+( [a-zA-Z]+)*$",
    "案B 末尾の空白も許す": r"^[a-zA-Z]+( [a-zA-Z]+)* ?$",
    "案C 文字クラスにまとめる": r"^[a-zA-Z ]+$",
}

ALPHABET = "ab "
MAX_LEN = 6
LENGTHS = [16, 20, 24, 26, 28]

# bench.py と同じ理由でウォームアップを取る。プロセス起動直後の 1 回目だけが
# 割高に出ると、最初の条件からの倍率が実際より小さく見える。
WARMUP_N = 12
WARMUP_RUNS = 3


def all_strings() -> list[str]:
    out = []
    for n in range(1, MAX_LEN + 1):
        out += ["".join(t) for t in itertools.product(ALPHABET, repeat=n)]
    return out


def check_equivalence(subjects: list[str]) -> dict:
    """書き換えの前後で判定が一致するかを総当たりで確かめる。"""
    print(f"■ 同じ判定になるか（{ALPHABET!r} の組み合わせ {len(subjects):,} 通り）")
    danger = re.compile(DANGER)
    rows = {}
    for label, pattern in CANDIDATES.items():
        flat = re.compile(pattern)
        diffs = [s for s in subjects if bool(danger.fullmatch(s)) != bool(flat.fullmatch(s))]
        rows[label] = {"pattern": pattern, "diff_count": len(diffs), "examples": diffs[:4]}
        mark = "○ 一致" if not diffs else f"× {len(diffs)} 件ちがう"
        print(f"  {label:<22} {pattern:<28} {mark}")
        if diffs:
            print(f"  {'':<22} {'':<28} 例: {diffs[:4]}")
    print()
    return rows


def compare_time(pattern: str) -> dict:
    """危険な形と、同じ判定になった書き換えの実行時間を比べる。"""
    print("■ 実行時間（入力は 'a' を n 個並べた末尾に '!' を付けたもの）")
    danger = re.compile(DANGER)
    flat = re.compile(pattern)
    warm = "a" * WARMUP_N + "!"
    for _ in range(WARMUP_RUNS):
        danger.fullmatch(warm)
        flat.fullmatch(warm)
    rows = []
    for n in LENGTHS:
        subject = "a" * n + "!"
        d = timed_min(lambda: danger.fullmatch(subject))
        f = timed_min(lambda: flat.fullmatch(subject))
        rows.append({"n": n, "danger_sec": d, "flat_sec": f})
        print(f"  n={n:>3}   危険 {format_sec(d):>12}   平ら {format_sec(f):>10}")
    print()
    return rows


def cap_table(rows: list[dict]) -> None:
    """入力長の上限を決めたときに、最悪どれだけ待つことになるか。"""
    print("■ 入力長の上限を決めた場合、最悪の待ち時間はどれくらいか")
    for row in rows:
        print(f"  上限 {row['n']:>3} 文字 → 最悪 {format_sec(row['danger_sec']):>12}")
    print(f"  （測定は {LENGTHS[-1]} 文字まで。これより長い上限は測っていない）")
    print()


def main() -> int:
    subjects = all_strings()
    equivalence = check_equivalence(subjects)

    same = [label for label, r in equivalence.items() if r["diff_count"] == 0]
    if not same:
        print("判定が一致する書き換えが見つかりませんでした。")
        return 1
    chosen = same[0]
    print(f"判定が一致したのは {chosen} です。これで時間を比べます。\n")

    rows = compare_time(CANDIDATES[chosen])
    cap_table(rows)

    print("■ 読み取れること（実測に基づく）")
    print("  平らに書き換えると爆発しない。アトミックグループが無い環境でも止められる")
    print("  ただし書き換えは判定を変えうる。総当たりで突き合わせてから置き換えること")
    print("  文字クラスにまとめる案は速いが、判定が大きく変わってしまう")
    print("  入力長の上限は効くが、何文字までなら許せるかは実測しないと決められない")

    path = save(
        "006-redos-rewrite",
        {"danger": DANGER, "equivalence": equivalence, "chosen": chosen, "timing": rows},
    )
    print(f"\n測定結果を保存しました: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
