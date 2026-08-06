#!/usr/bin/env python3
"""入力欄に実際に来る値を、3 つの方針で検証して結果を並べる。

郵便番号の検証を例に、次の 3 通りを比べる。

  A) [0-9] だけで書く          半角しか通さない
  B) \\d で書く                 その言語が数字とみなすものを通す
  C) NFKC で揃えてから [0-9]    表記を寄せてから検査する

同じ入力集合に対して結果がどう分かれるかを見ると、
「どれが正しいか」ではなく「何を通したいか」を先に決める必要が分かる。
"""

import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import save  # noqa: E402

# 入力欄に実際に来うる値（利用者の打ち方の揺れ）
SAMPLES = [
    ("半角そのまま", "123-4567"),
    ("全角数字と全角ハイフン", "１２３－４５６７"),
    ("全角数字と半角ハイフン", "１２３-４５６７"),
    ("ハイフンなし", "1234567"),
    ("前後に空白", " 123-4567 "),
    ("丸数字混じり", "①②③-4567"),
    ("桁が足りない", "12-345"),
    ("英字混じり", "12a-4567"),
]

PATTERN = r"[0-9]{3}-[0-9]{4}"
PATTERN_D = r"\d{3}-\d{4}"


def check_a(value: str) -> bool:
    return re.fullmatch(PATTERN, value) is not None


def check_b(value: str) -> bool:
    return re.fullmatch(PATTERN_D, value) is not None


def check_c(value: str) -> bool:
    normalized = unicodedata.normalize("NFKC", value.strip())
    return re.fullmatch(PATTERN, normalized) is not None


CHECKS = [
    ("A [0-9] だけ", check_a),
    ("B \\d で書く", check_b),
    ("C NFKC + [0-9]", check_c),
]


def main() -> int:
    print(f"Python {sys.version.split()[0]}\n")
    print("入力欄に来る値を 3 つの方針で検証します。○ = 通過 / × = 弾く\n")

    header = f"{'入力の種類':<24}{'値':<16}" + "".join(f"{name:<18}" for name, _ in CHECKS)
    print(header)
    print("-" * 92)

    rows = []
    for label, value in SAMPLES:
        results = {name: fn(value) for name, fn in CHECKS}
        marks = "".join(f"{'○' if results[name] else '×':<18}" for name, _ in CHECKS)
        print(f"{label:<24}{value:<16}{marks}")
        rows.append({"label": label, "value": value, "results": results})
    print()

    counts = {name: sum(1 for r in rows if r["results"][name]) for name, _ in CHECKS}
    print("通過した件数: " + " / ".join(f"{name} {counts[name]}件" for name, _ in CHECKS))

    print("\n■ 読み取れること")
    print("  ・A は全角を一切通さない（利用者からは「数字を入れたのに弾かれた」に見える）")
    print("  ・B は全角を通すが、前後の空白とハイフンの全角は通さない")
    print("  ・C は空白を落とし表記を揃えるため通過が最も多い。丸数字まで通る点は仕様判断が要る")

    path = save("002-formcheck", {"pattern": PATTERN, "samples": rows, "counts": counts})
    print(f"\n測定結果を保存しました: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
