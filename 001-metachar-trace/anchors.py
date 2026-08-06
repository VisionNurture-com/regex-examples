#!/usr/bin/env python3
"""$ が指す「末尾」に、末尾の改行が含まれるかどうかを確かめる。

`^ABC$` は「ABC だけの行」を表すと説明されることが多い。ところが入力の末尾に
改行が 1 つ残っていると、実行系によって結果が割れる。ファイルやフォームから
読んだ文字列には改行が残りがちなので、入力チェックで表に出やすい。

ここでは同じ入力を Python と JavaScript にかけて、割れることと、
割れない書き方（\\Z）があることを実測で示す。

使い方:
    python3 anchors.py
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import save  # noqa: E402

# 末尾に改行が 1 つ残っている入力と、改行が途中にある入力
SUBJECTS = [
    {"id": "trailing_lf", "label": r'"ABC\n"', "value": "ABC\n", "note": "末尾に改行"},
    {
        "id": "inner_lf",
        "label": r'"ABC\nDEF"',
        "value": "ABC\nDEF",
        "note": "改行の後にも文字がある",
    },
]

PY_PATTERNS = [
    {"id": "dollar", "label": "^ABC$", "pattern": r"^ABC$"},
    {"id": "upper_z", "label": r"^ABC\Z", "pattern": r"^ABC\Z"},
    {"id": "both_z", "label": r"\AABC\Z", "pattern": r"\AABC\Z"},
]


def show_subjects() -> None:
    for s in SUBJECTS:
        print(f"  入力 {s['label']:<12} {s['note']}")
    print()


def run_python() -> list[dict]:
    print("■ Python で試す")
    print("  " + "パターン".ljust(10) + "".join(s["label"].ljust(14) for s in SUBJECTS))
    print("  " + "-" * 40)

    rows = []
    for p in PY_PATTERNS:
        results = {}
        cells = ""
        for s in SUBJECTS:
            hit = re.search(p["pattern"], s["value"]) is not None
            results[s["id"]] = hit
            cells += ("一致" if hit else "不一致").ljust(12)
        print("  " + p["label"].ljust(14) + cells)
        rows.append({"pattern": p["pattern"], "results": results})
    print()
    return rows


NODE_SCRIPT = r"""
const subjects = [
  { id: "trailing_lf", value: "ABC\n" },
  { id: "inner_lf", value: "ABC\nDEF" },
];
const out = {};
for (const s of subjects) out[s.id] = /^ABC$/.test(s.value);
console.log(JSON.stringify(out));
"""


def run_javascript() -> dict | None:
    print("■ 同じ入力を JavaScript にかける")
    node = shutil.which("node")
    if node is None:
        print("  node が見つからないため飛ばします\n")
        return None

    proc = subprocess.run(
        [node, "-e", NODE_SCRIPT], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        print(f"  node の実行に失敗しました: {proc.stderr.strip()}\n")
        return None

    results = json.loads(proc.stdout)
    version = subprocess.run(
        [node, "--version"], capture_output=True, text=True, check=False
    ).stdout.strip()

    print(f"  node {version}")
    for s in SUBJECTS:
        hit = results[s["id"]]
        print(f"    /^ABC$/ | {s['label']:<12} → {'一致' if hit else '不一致'}")
    print()
    return {"version": version, "pattern": "/^ABC$/", "results": results}


def main() -> int:
    show_subjects()
    python_rows = run_python()
    js_row = run_javascript()

    print("■ 読み取れること（実測に基づく）")
    print("  Python の $ は、末尾に改行が 1 つある文字列にも一致する")
    print("  JavaScript の $ は一致しない。同じパターンでも結果が割れる")
    print("  改行が途中にある入力は、どちらも一致しない（許すのは末尾の 1 つだけ）")
    print(r"  末尾の改行まで拒みたいときは、Python では $ の代わりに \Z を使う")

    path = save(
        "001-anchors-trailing-newline",
        {
            "python": {"version": sys.version.split()[0], "rows": python_rows},
            "javascript": js_row,
        },
    )
    print(f"\n測定結果を保存しました: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
