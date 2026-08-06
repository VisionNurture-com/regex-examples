#!/usr/bin/env python3
"""パターンがどこまで進んで、どこで失敗したかを出力する。

正規表現が「マッチしない」とき、返ってくるのは None だけで、
どこまで合っていたのかは分からない。このスクリプトは 3 つの角度から
それを見えるようにする。

  1. パターンを前から少しずつ伸ばし、どこで入力に一致しなくなるかを示す
  2. 開始位置を 1 文字ずつずらし、どこから試してどこで外れたかを示す
  3. Python が内部でパターンをどう解釈したかを出す（re.DEBUG）

使い方:
    python3 trace.py 'a.c' 'abbc'
    python3 trace.py '^cat' 'my cat'
    python3 trace.py 'report\\.txt' 'reportXtxt'
"""

import contextlib
import io
import re
import sys


def valid_prefixes(pattern: str) -> list[str]:
    """パターンの前方部分のうち、それ自体が正規表現として成立するものを集める。

    `a.c` なら a / a. / a.c。`a{2,3}` のように途中が壊れる位置は飛ばす。
    """
    out = []
    for i in range(1, len(pattern) + 1):
        head = pattern[:i]
        try:
            re.compile(head)
        except re.error:
            continue
        out.append(head)
    return out


def show_prefix_progress(pattern: str, subject: str) -> None:
    print("■ パターンをどこまで伸ばせるか（前方から 1 文字ずつ）")
    print(f"  入力: {subject!r}")
    last_ok = None
    for head in valid_prefixes(pattern):
        m = re.match(head, subject)
        if m:
            last_ok = head
            print(f"  ✅ {head:<20} → {subject[m.start():m.end()]!r} まで一致")
        else:
            print(f"  ❌ {head:<20} → ここで一致しなくなる")
            break
    if last_ok == pattern:
        print("  → パターン全体が先頭から一致した")
    elif last_ok is None:
        print("  → 最初の 1 要素すら一致していない")
    else:
        print(f"  → {last_ok} までは合っていて、その次の要素で外れた")
    print()


def show_start_positions(pattern: str, subject: str) -> None:
    print("■ 開始位置をずらすと何が起きるか")
    compiled = re.compile(pattern)
    hit = False
    for pos in range(len(subject) + 1):
        m = compiled.match(subject, pos)
        head = subject[:pos]
        marker = " " * len(head) + "^"
        if m:
            hit = True
            print(f"  位置 {pos:>2}: {marker}  一致 → {m.group()!r}")
            break
        print(f"  位置 {pos:>2}: {marker}  不一致")
    if not hit:
        print("  → どの位置から始めても一致しなかった")
    print()


def show_internal_structure(pattern: str) -> None:
    print("■ Python がこのパターンをどう解釈したか")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        re.compile(pattern, re.DEBUG)
    for line in buf.getvalue().splitlines():
        print(f"  {line}")
    print()


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    pattern, subject = sys.argv[1], sys.argv[2]
    try:
        re.compile(pattern)
    except re.error as e:
        print(f"パターンが正規表現として成立していません: {e}")
        return 1

    print(f"パターン: {pattern}")
    print(f"入力    : {subject!r}")
    print()
    show_prefix_progress(pattern, subject)
    show_start_positions(pattern, subject)
    show_internal_structure(pattern)

    result = re.search(pattern, subject)
    print("■ 結果")
    if result:
        print(f"  マッチ: {result.group()!r}（位置 {result.start()}〜{result.end()}）")
    else:
        print("  マッチしませんでした")
    return 0


if __name__ == "__main__":
    sys.exit(main())
