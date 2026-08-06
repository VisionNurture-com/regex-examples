#!/usr/bin/env python3
"""同じ置換を「何件に適用するか」の既定が実行系ごとに違うことを確かめる。

matrix.py は「番号の直後をどこまで読むか」の差を測った。ここで測るのは
もう 1 つの差、**既定で何件置換するか** である。

入力に同じ形の日付を 2 つ置き、既定の書き方と、全件を明示した書き方の
両方を 4 つの実行系にかける。Python だけが既定で全件を置換する。
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import save  # noqa: E402

HERE = Path(__file__).parent
INPUT = "納品日は 2026-06-12、出荷日は 2026-07-01 です"
PY_PATTERN = r"(\d{4})-(\d{2})-(\d{2})"
SED_PATTERN = "([0-9]{4})-([0-9]{2})-([0-9]{2})"

JS_SOURCE = """
const [input, flags] = process.argv.slice(1);
const re = new RegExp("(\\\\d{4})-(\\\\d{2})-(\\\\d{2})", flags);
process.stdout.write(input.replace(re, "$3/$2/$1"));
"""


def run_node(flags: str) -> str:
    proc = subprocess.run(
        ["node", "-e", JS_SOURCE, INPUT, flags],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return f"エラー: {proc.stderr.strip().splitlines()[0]}"
    return proc.stdout


def run_sed(suffix: str) -> str:
    proc = subprocess.run(
        ["sed", "-E", f"s/{SED_PATTERN}/\\3\\/\\2\\/\\1/{suffix}"],
        input=INPUT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return f"エラー: {proc.stderr.strip().splitlines()[0]}"
    return proc.stdout.rstrip("\n")


def run_rust(mode: str) -> str:
    proc = subprocess.run(
        ["cargo", "run", "--quiet", "--", INPUT, "$3/$2/$1", mode],
        cwd=HERE / "rust",
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return f"エラー: {proc.stderr.strip().splitlines()[-1]}"
    return proc.stdout.rstrip("\n")


def count_replaced(text: str) -> int:
    """置換された箇所の数。元の形が残っていないかの答え合わせに使う。"""
    return len(re.findall(PY_PATTERN, INPUT)) - len(re.findall(PY_PATTERN, text))


# --- ここから: 各実行系で「何件置換したか」を受け取る手段を比べる ---

JS_COUNT_SOURCE = """
const input = process.argv[1];
const re = new RegExp("(\\\\d{4})-(\\\\d{2})-(\\\\d{2})", "g");
let n = 0;
input.replace(re, (m, y, mo, d) => { n += 1; return d + "/" + mo + "/" + y; });
process.stdout.write(String(n));
"""

GREP_PATTERN = "[0-9]{4}-[0-9]{2}-[0-9]{2}"


def count_node() -> int:
    """JavaScript は replace の第 2 引数に関数を渡し、呼ばれた回数を数える。"""
    proc = subprocess.run(
        ["node", "-e", JS_COUNT_SOURCE, INPUT], capture_output=True, text=True
    )
    return int(proc.stdout.strip()) if proc.returncode == 0 else -1


def count_sed() -> int:
    """sed には件数を返す仕組みが無いので grep -Eo で取り出して数える。"""
    proc = subprocess.run(
        ["grep", "-Eo", GREP_PATTERN], input=INPUT, capture_output=True, text=True
    )
    return len([line for line in proc.stdout.splitlines() if line])


def count_rust() -> int:
    """Rust の replace 系は件数を返さない。find_iter で数える。"""
    proc = subprocess.run(
        ["cargo", "run", "--quiet", "--", INPUT, "$3/$2/$1", "count"],
        cwd=HERE / "rust",
        capture_output=True,
        text=True,
    )
    return int(proc.stdout.strip()) if proc.returncode == 0 else -1


def main() -> int:
    have_node = shutil.which("node") is not None
    have_rust = shutil.which("cargo") is not None and (HERE / "rust" / "Cargo.toml").exists()

    print(f"入力: {INPUT}")
    print(f"入力に含まれる日付: {len(re.findall(PY_PATTERN, INPUT))} 件\n")
    if not have_node:
        print("※ node が見つからないため JavaScript 行は省略します")
    if not have_rust:
        print("※ cargo が見つからないため Rust 行は省略します")

    # (実行系, 既定の書き方, 既定の結果, 全件の書き方, 全件の結果)
    rows = [
        ("Python", "re.sub(...)", re.sub(PY_PATTERN, r"\3/\2/\1", INPUT),
         "既定のまま全件", re.sub(PY_PATTERN, r"\3/\2/\1", INPUT)),
        ("sed", "s/.../.../", run_sed(""), "s/.../.../g", run_sed("g")),
    ]
    if have_node:
        rows.insert(1, ("JavaScript", "replace(/.../)", run_node(""),
                        "replace(/.../g)", run_node("g")))
    if have_rust:
        rows.append(("Rust", "re.replace(...)", run_rust("first"),
                     "re.replace_all(...)", run_rust("all")))

    print("■ 既定の書き方で置換する")
    result = []
    for engine, default_form, default_out, all_form, all_out in rows:
        n_default = count_replaced(default_out)
        n_all = count_replaced(all_out)
        result.append({
            "engine": engine,
            "default": {"form": default_form, "output": default_out, "replaced": n_default},
            "explicit_all": {"form": all_form, "output": all_out, "replaced": n_all},
        })
        print(f"   {engine:<11} {default_form:<20} 置換 {n_default} 件 → {default_out}")

    print("\n■ 全件を明示して置換する")
    for item in result:
        print(f"   {item['engine']:<11} {item['explicit_all']['form']:<20} "
              f"置換 {item['explicit_all']['replaced']} 件 → {item['explicit_all']['output']}")

    defaults = {item["default"]["replaced"] for item in result}
    print(f"\n既定の置換件数: {sorted(defaults)}"
          f"{' ★ 実行系で食い違った' if len(defaults) > 1 else ''}")

    # 置換が何件行われたかは、Python なら subn で直接受け取れる。
    replaced, n = re.subn(PY_PATTERN, r"\3/\2/\1", INPUT)
    print("\n■ 何件置換されたかを受け取る（Python の re.subn）")
    print(f"   置換後: {replaced}")
    print(f"   件数  : {n}")

    # 件数を受け取る手段は実行系ごとに違う。同じ入力で何件と数えられるかを並べる。
    print("\n■ 4 実行系で件数を数える")
    counts = [("Python", "re.subn(...) の 2 つ目の戻り値", n)]
    if have_node:
        counts.append(("JavaScript", "replace(re, 関数) の関数が呼ばれた回数", count_node()))
    counts.append(("sed", f"仕組みが無い。grep -Eo '{GREP_PATTERN}' | wc -l", count_sed()))
    if have_rust:
        counts.append(("Rust", "re.find_iter(s).count()", count_rust()))
    for engine, how, value in counts:
        print(f"   {engine:<11} {value} 件   {how}")

    path = save("004-group-replace-scope", {
        "input": INPUT,
        "engines": result,
        "subn_count": n,
        "count_methods": [{"engine": e, "how": h, "count": v} for e, h, v in counts],
    })
    print(f"\n測定結果を保存しました: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
