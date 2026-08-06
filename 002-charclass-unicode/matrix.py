#!/usr/bin/env python3
"""日本語の入力が文字クラスでどう扱われるかを一覧にする。

「電話番号の欄に全角で入力されたら弾かれた」という事故は、
文字クラスが何を数字とみなすかを確かめていないところから起きる。

ここでは同じ入力を複数の文字クラスにかけ、さらに Unicode 正規化を
通した場合と通さない場合を並べて出す。
"""

import re
import sys
import unicodedata

SUBJECTS = [
    ("半角数字", "0123"),
    ("全角数字", "０１２３"),
    ("丸数字", "①②③"),
    ("半角英字", "abc"),
    ("全角英字", "ａｂｃ"),
    ("漢字", "日本語"),
    ("半角カナ", "ｱｲｳ"),
    ("絵文字（BMP 外）", "🍣🍺"),
    ("結合文字（が = か + 濁点）", "が"),
]

CLASSES = [
    (r"\d", "数字とみなすか"),
    (r"[0-9]", "半角数字に限るか"),
    (r"\w", "単語構成文字とみなすか"),
    (r".", "1 文字として数えるか"),
]


def probe(pattern: str, text: str) -> str:
    """text 全体がそのクラスの繰り返しで表せるかを見る。"""
    return "○" if re.fullmatch(f"(?:{pattern})+", text) else "×"


def main() -> int:
    print(f"Python {sys.version.split()[0]}\n")

    header = f"{'入力':<26}{'例':<10}" + "".join(f"{p:<8}" for p, _ in CLASSES) + "文字数"
    print(header)
    print("-" * len(header))
    for label, text in SUBJECTS:
        cells = "".join(f"{probe(p, text):<8}" for p, _ in CLASSES)
        print(f"{label:<26}{text:<10}{cells}{len(text)}")

    print("\n■ Unicode 正規化を通すと何が変わるか（NFKC）")
    print(f"{'入力':<26}{'元':<10}{'NFKC 後':<12}{'\\d に一致':<12}")
    print("-" * 62)
    for label, text in SUBJECTS:
        normalized = unicodedata.normalize("NFKC", text)
        before = probe(r"\d", text)
        after = probe(r"\d", normalized)
        changed = "→ 変化あり" if before != after else ""
        print(f"{label:<26}{text:<10}{normalized:<12}{before} → {after}  {changed}")

    print("\n■ 覚えておくこと")
    print("  ・\\d は Python では全角数字にも一致します（[0-9] は一致しません）")
    print("  ・NFC ではなく NFKC を通すと、全角は半角へ、丸数字は数字へ変換されます")
    print("  ・絵文字は Python では 1 文字ですが、JavaScript では 2 単位として扱われます")
    print("    （matrix.mjs で同じ入力を試すと差が見えます）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
