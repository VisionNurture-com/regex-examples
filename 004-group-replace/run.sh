#!/usr/bin/env bash
# 同じ置換を 4 つの実行系で書き比べる。
#
# 題材: 2026-06-12 という日付を 12/06/2026 に並べ替える。
# キャプチャした番号をどう呼び出すかが、実行系ごとに違う。
set -uo pipefail

INPUT="納品日は 2026-06-12 です"
echo "入力: $INPUT"
echo

echo "■ Python — \\1 で呼び出す"
python3 - "$INPUT" <<'PY'
import re, sys
print("  " + re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3/\2/\1", sys.argv[1]))
PY
echo

echo "■ JavaScript — \$1 で呼び出す"
node -e '
const input = process.argv[1];
console.log("  " + input.replace(/(\d{4})-(\d{2})-(\d{2})/, "$3/$2/$1"));
' "$INPUT"
echo

echo "■ sed — \\1 で呼び出す（-E で拡張正規表現）"
echo "  $(printf '%s' "$INPUT" | /usr/bin/sed -E 's/([0-9]{4})-([0-9]{2})-([0-9]{2})/\3\/\2\/\1/')"
echo

if command -v cargo >/dev/null 2>&1; then
  echo "■ Rust — \$1 で呼び出す（regex クレート）"
  RUST_DIR="$(dirname "$0")/rust"
  if [ -f "$RUST_DIR/Cargo.toml" ]; then
    (cd "$RUST_DIR" && cargo run --quiet -- "$INPUT" 2>/dev/null | sed 's/^/  /')
  else
    echo "  （rust/ が未作成のため省略）"
  fi
else
  echo "■ Rust — cargo が見つからないため省略"
fi
echo

echo "■ 覚えておくこと"
echo "  ・呼び出し方が 2 系統ある: \\1 系（Python / sed）と \$1 系（JavaScript / Rust）"
echo "  ・sed は / が区切り文字なので、置換文字列の / を \\/ で打ち消す必要がある"
echo "  ・BSD sed と GNU sed では -E の扱いに差がある（007 で実測する）"
echo
echo "  この 4 つが一致するのは、番号の直後が / のときだけである。"
echo "  番号の後ろに何を書くかで結果が変わる: python3 matrix.py"
