#!/usr/bin/env python3
"""後読みが無い実行系へ、同じ意図のパターンを移す。

matrix.py で分かったとおり、Go と Rust には後読みが無い。ではそこで同じことを
どう書くのか。

  肯定後読み  → キャプチャで置き換えられる（結果は一致する）
  否定後読み  → 単純には置き換えられない。しかも書き方そのものに落とし穴がある

最後に、置き換えたパターンが本当に全実行系で通るのかを matrix.py と同じ
ハーネスで確かめる。
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).parent))
import matrix  # noqa: E402
from measure import save  # noqa: E402

PRICE = "価格は ¥1200 です"
MIXED = "¥1200 と 300 円"

# 移植の前後で結果が変わらないかを確かめる組
PORT_FEATURES = [
    {
        "id": "lookbehind",
        "label": "後読み (?<=¥)\\d+",
        "subject": PRICE,
        "expected": "1200",
        "pattern": r"(?<=¥)\d+",
    },
    {
        "id": "captured",
        "label": "キャプチャ ¥(\\d+)",
        "subject": PRICE,
        "expected": "¥1200",
        "pattern": r"¥(\d+)",
    },
]


def show_python() -> dict:
    print("■ Python で書き比べる")
    print(f"  対象: {PRICE}")
    rows = {}
    for label, pattern in [("肯定後読み", r"(?<=¥)\d+"), ("キャプチャ", r"¥(\d+)")]:
        found = re.findall(pattern, PRICE)
        rows[label] = {"pattern": pattern, "found": found}
        print(f"    {label:<8} {pattern:<12} → {found}")

    print(f"\n  対象: {MIXED}")
    for label, pattern in [("否定後読み", r"(?<!¥)\d+"), ("境界つき", r"(?<!¥)\b\d+")]:
        found = re.findall(pattern, MIXED)
        rows[label] = {"pattern": pattern, "found": found}
        print(f"    {label:<8} {pattern:<12} → {found}")
    print()
    return rows


def show_engines() -> dict:
    """移植前後のパターンを、matrix.py と同じ実行系ぜんぶにかける。"""
    matrix.FEATURES = PORT_FEATURES
    engines = matrix.available_engines()
    print("■ 移植の前と後を全実行系にかける")
    print("  実行系: " + " / ".join(name for name, _ in engines) + "\n")

    table = {name: runner() for name, runner in engines}
    names = [name for name, _ in engines]

    header = "パターン".ljust(22) + "".join(n[:12].ljust(14) for n in names)
    print(header)
    print("-" * len(header))

    rows = []
    for f in PORT_FEATURES:
        judged = {n: table[n].get(f["id"], "ERROR:未実行") for n in names}
        print(f["label"].ljust(18) + "".join(matrix.mark(judged[n]).ljust(14) for n in names))
        rows.append({"id": f["id"], "label": f["label"], "results": judged})

    print("\n■ ○ にならなかった理由（先頭 1 行）")
    for row in rows:
        for name in names:
            if row["results"][name] != "OK":
                print(f"  {row['label']:<20} {name:<18} {row['results'][name]}")
    print()
    return {"engines": names, "features": rows}


def main() -> int:
    python_rows = show_python()
    engine_rows = show_engines()
    print("■ 読み取れること（実測に基づく）")
    print("  肯定後読みはキャプチャで置き換えられる。取れる文字列は同じになる")
    print("  置き換えたパターンは、後読みを持たない実行系でも通る")
    print("  否定後読みは、数字の途中から始まってしまうため単純な置き換えでは足りない")
    print("  単語境界を足すと意図どおりになる。移した先で結果を必ず突き合わせること")
    path = save("005-lookaround-port", {"python": python_rows, **engine_rows})
    print(f"\n測定結果を保存しました: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
