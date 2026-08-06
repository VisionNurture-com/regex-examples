#!/usr/bin/env python3
"""正規表現が固まる（ReDoS）様子と、記法だけで止められることを測る。

危険なパターンに対する定番の助言は「量指定子のネストを避ける」「入力長を制限する」
だが、Python 3.11 以降はアトミックグループと所有量指定子が使えるようになった。
**エンジンを替えず、記法だけで**止められるかを実測する。

⚠️ 危険な形は入力長を小さく保っている。本番のコードには持ち込まないこと。
"""

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import format_sec, save, timed_min  # noqa: E402

VARIANTS = {
    "危険 (a+)+$": r"(a+)+$",
    "アトミック (?>(a+)+)$": r"(?>(a+)+)$",
    "所有 (a+)++$": r"(a+)++$",
    "安全 a+$": r"a+$",
}

LENGTHS = [16, 20, 24, 26, 28]
GIVE_UP_SEC = 10.0

# 記事は「手元で試すなら 28 文字まで」と案内している。その根拠を測るための追加モード。
# 既定の測定に混ぜると 1 回あたり数分かかるため、--limit を付けたときだけ走らせる。
LIMIT_LENGTHS = [28, 32]

# プロセス起動直後にあたる最初の条件だけが割高に出ると、そこからの倍率が実際より
# 小さく見える（実測: 4 文字あたり 13.1 倍 と 16.4 倍で割れた）。短い入力で空回ししてから
# 本計測に入り、条件ごとの繰り返しは tools/measure.py の timed_min に任せる。
WARMUP_N = 12
WARMUP_RUNS = 3


def warm_up(compiled: "re.Pattern[str]") -> None:
    """短い入力で数回空回しし、1 回目だけが遅くなるのを防ぐ。"""
    subject = "a" * WARMUP_N + "!"
    for _ in range(WARMUP_RUNS):
        compiled.search(subject)


def measure_limit() -> int:
    """28 文字という目安を超えると待ち時間がどうなるかを測る。"""
    print("目安の 28 文字を超えたときに何が起きるかを、危険な形だけで測ります。")
    print("1 条件で数分かかります。本番のコードやサーバー上では実行しないでください。\n")

    pattern = VARIANTS["危険 (a+)+$"]
    compiled = re.compile(pattern)
    warm_up(compiled)
    rows = []
    previous = None

    print(f"{'n':>4}{'実行時間':>16}{'前の行からの倍率':>20}")
    print("-" * 42)

    for n in LIMIT_LENGTHS:
        subject = "a" * n + "!"
        start = time.perf_counter()
        compiled.search(subject)
        elapsed = time.perf_counter() - start

        ratio = elapsed / previous if previous else None
        ratio_cell = f"{ratio:.1f} 倍" if ratio else "—"
        print(f"{n:>4}{format_sec(elapsed):>16}{ratio_cell:>20}")

        rows.append({"n": n, "elapsed_sec": elapsed, "ratio_from_previous": ratio})
        previous = elapsed

    path = save("006-redos-limit", {"pattern": pattern, "rows": rows})
    print(f"\n測定結果を保存しました: {path}")
    print("\n注: 1 回きりの実行時間です。これより長い入力は測っていません。")
    return 0


def main() -> int:
    print("入力は 'a' を n 個並べた末尾に '!' を付けたもの（マッチしない形）です。")
    print(f"1 条件が {GIVE_UP_SEC:.0f} 秒を超えた時点で、その書き方は以降の測定を打ち切ります。")
    print("短時間で終わった条件は複数回まわして最小値を採ります。\n")

    header = f"{'n':>4}" + "".join(f"{label:>22}" for label in VARIANTS)
    print(header)
    print("-" * len(header))

    gave_up: set[str] = set()
    rows = []

    compiled_variants = {label: re.compile(p) for label, p in VARIANTS.items()}
    for compiled in compiled_variants.values():
        warm_up(compiled)

    for n in LENGTHS:
        subject = "a" * n + "!"
        row = {"n": n, "variants": {}}
        cells = f"{n:>4}"

        for label, pattern in VARIANTS.items():
            if label in gave_up:
                cells += f"{'（打ち切り済）':>19}"
                row["variants"][label] = {"pattern": pattern, "skipped": True}
                continue

            compiled = compiled_variants[label]
            elapsed = timed_min(lambda: compiled.search(subject))

            row["variants"][label] = {"pattern": pattern, "elapsed_sec": elapsed}
            cells += f"{format_sec(elapsed):>22}"
            if elapsed > GIVE_UP_SEC:
                gave_up.add(label)

        rows.append(row)
        print(cells)

    path = save("006-redos-bench", {"give_up_sec": GIVE_UP_SEC, "rows": rows})
    print(f"\n測定結果を保存しました: {path}")
    print("\n注: 1 秒以上かかった条件は 1 回きりの実行時間です。")
    return 0


if __name__ == "__main__":
    sys.exit(measure_limit() if "--limit" in sys.argv[1:] else main())
