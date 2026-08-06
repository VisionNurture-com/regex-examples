#!/usr/bin/env python3
"""同じ意図の置換を 4 つの実行系にかけて、結果の差分を出す。

置換の教材は「Python では \\1、JavaScript では $1」という対応表で終わることが多い。
だが実際に事故になるのは、**呼び出した番号がどこで終わるか**の判断が実行系ごとに
違う点である。番号の直後に何を書くかで結果が変わる。

ここでは 1 つの入力に対し、同じ意図の 5 つのテンプレートを
Python / JavaScript / sed / Rust にかけ、出力をそのまま並べる。

テンプレートは実行系ごとに書き下しで持つ（文字列から機械的に組み立てると、
シェルを経由する過程でバックスラッシュが失われる。本リポジトリの 007 で実際に
起きた事故のため、ここでは意図的に冗長な書き方を選んでいる）。
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import save  # noqa: E402

HERE = Path(__file__).parent
INPUT = "納品日は 2026-06-12 です"
PY_PATTERN = r"(\d{4})-(\d{2})-(\d{2})"
SED_PATTERN = "([0-9]{4})-([0-9]{2})-([0-9]{2})"

# (意図, Python, JavaScript, sed, Rust)
CASES = [
    ("区切りを / にして並べ替える", r"\3/\2/\1", "$3/$2/$1", r"\3\/\2\/\1", "$3/$2/$1"),
    ("日本語を挟む", r"\1年\2月\3日", "$1年$2月$3日", r"\1年\2月\3日", "$1年$2月$3日"),
    ("_ で連結する", r"\1_\2_\3", "$1_$2_$3", r"\1_\2_\3", "$1_$2_$3"),
    ("英字を直後に続ける", r"\1abc", "$1abc", r"\1abc", "$1abc"),
    ("数字を直後に続ける", r"\10", "$10", r"\10", "$10"),
]

JS_SOURCE = """
const [input, template] = process.argv.slice(1);
const re = /(\\d{4})-(\\d{2})-(\\d{2})/;
process.stdout.write(input.replace(re, template));
"""


def run_python(template: str) -> str:
    try:
        return re.sub(PY_PATTERN, template, INPUT)
    except re.error as exc:
        return f"エラー: {type(exc).__name__}: {exc}"


def run_node(template: str) -> str:
    proc = subprocess.run(
        ["node", "-e", JS_SOURCE, INPUT, template],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return f"エラー: {proc.stderr.strip().splitlines()[0]}"
    return proc.stdout


def run_sed(template: str) -> str:
    proc = subprocess.run(
        ["sed", "-E", f"s/{SED_PATTERN}/{template}/"],
        input=INPUT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return f"エラー: {proc.stderr.strip().splitlines()[0]}"
    return proc.stdout.rstrip("\n")


def run_rust(template: str) -> str:
    proc = subprocess.run(
        ["cargo", "run", "--quiet", "--", INPUT, template],
        cwd=HERE / "rust",
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return f"エラー: {proc.stderr.strip().splitlines()[-1]}"
    return proc.stdout.rstrip("\n")


def main() -> int:
    have_node = shutil.which("node") is not None
    have_rust = shutil.which("cargo") is not None and (HERE / "rust" / "Cargo.toml").exists()

    print(f"入力: {INPUT}")
    print(f"パターン: {PY_PATTERN}\n")
    if not have_node:
        print("※ node が見つからないため JavaScript 列は省略します")
    if not have_rust:
        print("※ cargo が見つからないため Rust 列は省略します")

    rows = []
    for intent, py_tpl, js_tpl, sed_tpl, rs_tpl in CASES:
        row = {
            "intent": intent,
            "engines": {
                "Python": {"template": py_tpl, "output": run_python(py_tpl)},
                "sed": {"template": sed_tpl, "output": run_sed(sed_tpl)},
            },
        }
        if have_node:
            row["engines"]["JavaScript"] = {"template": js_tpl, "output": run_node(js_tpl)}
        if have_rust:
            row["engines"]["Rust"] = {"template": rs_tpl, "output": run_rust(rs_tpl)}

        outputs = {v["output"] for v in row["engines"].values()}
        row["agreed"] = len(outputs) == 1
        rows.append(row)

        print(f"■ {intent}")
        for engine in ("Python", "JavaScript", "sed", "Rust"):
            if engine not in row["engines"]:
                continue
            item = row["engines"][engine]
            print(f"   {engine:<11} {item['template']:<14} → {item['output']}")
        print(f"   {'一致' if row['agreed'] else '★ 実行系で結果が分かれた'}\n")

    split = [r["intent"] for r in rows if not r["agreed"]]
    print(f"結果が分かれた条件: {len(split)} / {len(rows)} 件")
    for intent in split:
        print(f"  ・{intent}")

    path = save("004-group-replace-matrix", {"input": INPUT, "pattern": PY_PATTERN, "cases": rows})
    print(f"\n測定結果を保存しました: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
