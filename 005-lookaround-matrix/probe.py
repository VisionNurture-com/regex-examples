#!/usr/bin/env python3
"""この環境でどの機能が使えるかを、実際にコンパイルして調べる。

正規表現の機能は「ある言語では書けて、別の言語では書けない」ことが多い。
表を暗記するより、**使う前に自分の環境に聞く**ほうが確実である。

このスクリプトは Python 側を調べる。JavaScript 側は probe.mjs が同じ形式で出す。
"""

import re
import sys

FEATURES = [
    ("先読み (?=...)", r"foo(?=bar)"),
    ("否定先読み (?!...)", r"foo(?!bar)"),
    ("後読み (?<=...)（固定長）", r"(?<=¥)\d+"),
    ("後読み (?<=...)（可変長）", r"(?<=\d+)円"),
    ("名前付きキャプチャ", r"(?P<year>\d{4})"),
    ("アトミックグループ (?>...)", r"(?>a+)b"),
    ("所有量指定子 a*+", r"a*+b"),
    ("所有量指定子 a++", r"a++b"),
    ("後方参照 \\1", r"(\w+) \1"),
    ("Unicode プロパティ \\p{...}", r"\p{Han}"),
]


def main() -> int:
    print(f"Python {sys.version.split()[0]} の対応状況\n")
    ok = ng = 0
    for label, pattern in FEATURES:
        try:
            re.compile(pattern)
            print(f"  ✅ {label:<32} {pattern}")
            ok += 1
        except re.error as e:
            print(f"  ❌ {label:<32} {pattern}  → {e}")
            ng += 1
    print(f"\n  使える {ok} / 使えない {ng}")
    print("\n注: コンパイルが通ることと、意図どおり動くことは別です。")
    print("    動作は各章のスクリプトで確かめてください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
