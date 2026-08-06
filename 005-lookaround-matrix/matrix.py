#!/usr/bin/env python3
"""同じ機能を 7 つの実行系にかけて、使えるかどうかを一覧にする。

先読み・後読みの解説は「Python では使える」「JavaScript では制限がある」といった
断片で語られがちである。ここでは 9 つの機能を同じ条件で全実行系にかけ、
**コンパイルが通るか**ではなく**意図どおりマッチするか**まで確かめる。

判定は 3 段階で記録する。

  OK     期待した文字列にマッチした
  NG     コンパイルは通ったが、マッチしない / 別の文字列にマッチした
  ERROR  コンパイルの時点で拒否された

「書けるが意図と違う結果になる」を「使える」と数えないための区別である。
実行系が見つからない場合はその列を省略する（環境ごとに結果が違うのが正しい）。
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from measure import save  # noqa: E402

HERE = Path(__file__).parent
ENGINES_DIR = HERE / "engines"

# id, ラベル, 対象文字列, 期待するマッチ, 既定パターン, 実行系ごとの上書き
FEATURES = [
    {
        "id": "lookahead",
        "label": "先読み (?=...)",
        "subject": "foobar",
        "expected": "foo",
        "pattern": r"foo(?=bar)",
    },
    {
        "id": "neg_lookahead",
        "label": "否定先読み (?!...)",
        "subject": "foobaz",
        "expected": "foo",
        "pattern": r"foo(?!bar)",
    },
    {
        "id": "lookbehind_fixed",
        "label": "後読み（固定長）",
        "subject": "A123",
        "expected": "123",
        "pattern": r"(?<=A)\d+",
    },
    {
        "id": "lookbehind_var",
        "label": "後読み（可変長）",
        "subject": "1234円",
        "expected": "円",
        "pattern": r"(?<=\d+)円",
    },
    {
        "id": "named_group",
        "label": "名前付きキャプチャ",
        "subject": "2026-06-12",
        "expected": "2026",
        "pattern": r"(?<year>\d{4})",
        "overrides": {"Python": r"(?P<year>\d{4})", "Go (RE2)": r"(?P<year>\d{4})"},
    },
    {
        "id": "atomic",
        "label": "アトミックグループ（書ける）",
        "subject": "aaab",
        "expected": "aaab",
        "pattern": r"(?>a+)b",
    },
    {
        # 書けるだけでは足りない。アトミックグループは一度取った文字を戻さないため、
        # (?>a+)a は "aaa" に一致しないのが正しい。一致するなら「ただの丸かっこ」である。
        "id": "atomic_semantics",
        "label": "アトミックグループ（戻らない）",
        "subject": "aaa",
        "expected": "",
        "expect_none": True,
        "pattern": r"(?>a+)a",
    },
    {
        "id": "possessive",
        "label": "所有量指定子（書ける）",
        "subject": "aaab",
        "expected": "aaab",
        "pattern": r"a++b",
    },
    {
        # 同じ理由で a++a も "aaa" に一致しないのが正しい。
        "id": "possessive_semantics",
        "label": "所有量指定子（戻らない）",
        "subject": "aaa",
        "expected": "",
        "expect_none": True,
        "pattern": r"a++a",
    },
    {
        "id": "backref",
        "label": "後方参照 \\1",
        "subject": "the the cat",
        "expected": "the the",
        "pattern": r"(\w+) \1",
    },
    {
        # Unicode プロパティは綴りが実行系ごとに違う。同じ綴りで揃えると
        # 「対応していない」と「綴りが違う」を取り違えるため、各実行系の書き方で問う。
        "id": "uniprop",
        "label": "Unicode プロパティ \\p{...}",
        "subject": "漢字テスト",
        "expected": "漢字",
        "pattern": r"\p{Han}+",
        "overrides": {
            "JavaScript (Node)": r"\p{Script=Han}+",
            ".NET": r"\p{IsCJKUnifiedIdeographs}+",
        },
        "flags": {"JavaScript (Node)": "u"},
    },
]


def rows_for(engine: str) -> str:
    """実行系ごとの入力 TSV を作る。"""
    lines = []
    for f in FEATURES:
        pattern = f.get("overrides", {}).get(engine, f["pattern"])
        flags = f.get("flags", {}).get(engine, "")
        lines.append("\t".join([f["id"], pattern, f["subject"], f["expected"], flags]))
    return "\n".join(lines) + "\n"


def run_batch(engine: str, cmd: list[str], cwd: Path | None = None) -> dict:
    """1 回の呼び出しで全機能を判定する実行系（Node / Go / Rust / .NET）。"""
    proc = subprocess.run(
        cmd, input=rows_for(engine), capture_output=True, text=True, cwd=cwd
    )
    results = {}
    for line in proc.stdout.splitlines():
        if "\t" not in line:
            continue
        fid, status = line.split("\t", 1)
        results[fid] = status
    if not results:
        err = proc.stderr.strip().splitlines()
        results = {f["id"]: f"ERROR:{err[-1] if err else '実行できませんでした'}" for f in FEATURES}
    return results


def run_python() -> dict:
    import re

    results = {}
    for f in FEATURES:
        pattern = f.get("overrides", {}).get("Python", f["pattern"])
        try:
            m = re.search(pattern, f["subject"])
        except re.error as exc:
            results[f["id"]] = f"ERROR:{exc}"
            continue
        if not m:
            results[f["id"]] = "NG:none"
        elif m.group() == f["expected"]:
            results[f["id"]] = "OK"
        else:
            results[f["id"]] = f"NG:{m.group()}"
    return results


def run_cli(engine: str, base_cmd: list[str]) -> dict:
    """1 機能ずつ呼ぶ実行系（grep -E / pcre2grep）。-o の出力で判定する。"""
    results = {}
    for f in FEATURES:
        pattern = f.get("overrides", {}).get(engine, f["pattern"])
        proc = subprocess.run(
            base_cmd + [pattern],
            input=f["subject"] + "\n",
            capture_output=True,
            text=True,
        )
        got = proc.stdout.splitlines()
        if proc.returncode >= 2:
            msg = proc.stderr.strip().splitlines()
            results[f["id"]] = f"ERROR:{msg[0] if msg else '拒否されました'}"
        elif not got:
            results[f["id"]] = "NG:none"
        elif got[0] == f["expected"]:
            results[f["id"]] = "OK"
        else:
            results[f["id"]] = f"NG:{got[0]}"
    return results


def available_engines() -> list[tuple[str, callable]]:
    engines: list[tuple[str, callable]] = [("Python", run_python)]

    if shutil.which("node"):
        engines.append(
            ("JavaScript (Node)", lambda: run_batch("JavaScript (Node)", ["node", str(ENGINES_DIR / "probe.mjs")]))
        )
    if shutil.which("go"):
        engines.append(
            ("Go (RE2)", lambda: run_batch("Go (RE2)", ["go", "run", str(ENGINES_DIR / "probe.go")]))
        )
    if shutil.which("cargo") and (ENGINES_DIR / "rust" / "Cargo.toml").exists():
        engines.append(
            ("Rust (regex)", lambda: run_batch("Rust (regex)", ["cargo", "run", "--quiet"], ENGINES_DIR / "rust"))
        )
    if shutil.which("dotnet"):
        engines.append(
            (".NET", lambda: run_batch(".NET", ["dotnet", "run", str(ENGINES_DIR / "probe.cs")]))
        )
    if shutil.which("pcre2grep"):
        # -u は UTF-8 として扱う指定。付けないと \p{Han} が日本語に当たらない
        engines.append(("pcre2grep", lambda: run_cli("pcre2grep", ["pcre2grep", "-u", "-o"])))
    engines.append(("grep -E", lambda: run_cli("grep -E", ["/usr/bin/grep", "-Eo"])))
    return engines


def judge(feature: dict, status: str) -> str:
    """「一致しないのが正解」の条件を、実行系の生の判定から読み替える。"""
    if not feature.get("expect_none"):
        return status
    if status.startswith("ERROR"):
        return status
    if status == "NG:none":
        return "OK"
    return f"NG:戻ってしまった（{status.removeprefix('NG:').removeprefix('OK')}）"


def mark(status: str) -> str:
    return "○" if status == "OK" else "×"


def main() -> int:
    engines = available_engines()
    print("この環境で使える実行系: " + " / ".join(name for name, _ in engines) + "\n")

    table = {}
    for name, runner in engines:
        print(f"  {name} を実行中...", flush=True)
        table[name] = runner()
    print()

    names = [name for name, _ in engines]
    header = "機能".ljust(26) + "".join(n[:12].ljust(14) for n in names)
    print(header)
    print("-" * len(header))

    rows = []
    for f in FEATURES:
        judged = {n: judge(f, table[n].get(f["id"], "ERROR:未実行")) for n in names}
        print(f["label"].ljust(20) + "".join(mark(judged[n]).ljust(14) for n in names))
        rows.append(
            {
                "id": f["id"],
                "label": f["label"],
                "subject": f["subject"],
                "expected": "（一致しないこと）" if f.get("expect_none") else f["expected"],
                "results": judged,
            }
        )

    print("\n■ ○ にならなかった理由（先頭 1 行）")
    for row in rows:
        for name in names:
            status = row["results"][name]
            if status != "OK":
                print(f"  {row['label']:<24} {name:<18} {status}")

    path = save("005-feature-matrix", {"engines": names, "features": rows})
    print(f"\n測定結果を保存しました: {path}")
    print("注: ○ は「期待した文字列にマッチした」を意味します。書けることと意図どおり動くことは別です。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
