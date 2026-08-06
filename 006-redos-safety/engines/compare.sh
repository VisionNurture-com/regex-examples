#!/usr/bin/env bash
# 同じ (a+)+$ に同じ入力（a を n 個並べて ! を足したもの）を与え、実行系だけを替えて測る。
#
# bench.py が測るのは「同じ実行系の中で、書き方を替えるとどうなるか」である。
# ここで測るのは「同じ書き方のまま、実行系を替えるとどうなるか」で、軸が違う。
#
# 見つからない実行系は飛ばす。環境ごとに並ぶ行が変わることを前提にしている。
set -uo pipefail
cd "$(dirname "$0")"

MAX_N=28

run_python() {
  echo "■ Python — 戻りながら探す"
  python3 - "$MAX_N" <<'PY'
import re, sys, time
pat = re.compile(r"(a+)+$")
# bench.py と同じくウォームアップを取る。1 回目だけが割高だと最初の倍率が小さく出る。
for _ in range(3):
    pat.search("a" * 12 + "!")
for n in (16, 20, 24, 26, int(sys.argv[1])):
    subject = "a" * n + "!"
    start = time.perf_counter()
    pat.search(subject)
    sec = time.perf_counter() - start
    print(f"  n={n:3}  {sec:.6f} s")
    if sec > 60:
        print("  （60 秒を超えたため打ち切り）")
        break
PY
  echo
}

run_node() {
  command -v node >/dev/null 2>&1 || { echo "■ JavaScript — node が見つからないため省略"; echo; return; }
  echo "■ JavaScript（V8）— 戻りながら探す"
  node redos.mjs | /usr/bin/grep -v '^{'
  echo
}

run_go() {
  command -v go >/dev/null 2>&1 || { echo "■ Go — go が見つからないため省略"; echo; return; }
  echo "■ Go（RE2）— 戻らない"
  go run redos.go 2>/dev/null | /usr/bin/grep -v '^{'
  echo
}

run_dotnet() {
  command -v dotnet >/dev/null 2>&1 || { echo "■ .NET — dotnet が見つからないため省略"; echo; return; }
  echo "■ .NET — 既定は戻りながら探し、NonBacktracking は戻らない"
  dotnet run redos.cs 2>/dev/null
  echo
}

run_rust() {
  command -v cargo >/dev/null 2>&1 || { echo "■ Rust — cargo が見つからないため省略"; echo; return; }
  echo "■ Rust（regex クレート）— 戻らない"
  (cd rust && cargo run --quiet 2>/dev/null)
  echo
}

echo "パターン: (a+)+\$   入力: a を n 個並べて ! を足したもの"
echo "n を 16 から $MAX_N まで増やし、同じ書き方のまま実行系だけを替えます。"
echo

run_python
run_node
run_go
run_dotnet
run_rust

echo "■ 読み取れること（実測に基づく）"
echo "  戻りながら探す方式（Python / JavaScript / .NET 既定）は n を増やすと桁で伸びる"
echo "  戻らない方式（Go / Rust / .NET NonBacktracking）は n を増やしても伸びない"
echo "  ただし戻らない方式は後方参照や先読みを受け付けない。速さではなく方式の違いである"
