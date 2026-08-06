#!/usr/bin/env bash
# 設定の有無で検出結果がどう変わるかを並べて出す。
#
# 「設定を入れた」と「設定が効いている」は別の話である。
# 設定を入れない場合・1 ルールだけ入れた場合・推奨設定を使った場合の
# 3 通りを同じファイルにかけて、出てくるものと終了コードを比べる。
set -uo pipefail
cd "$(dirname "$0")/.."

TARGET=eslint-config/sample.js

# 依存が入っていない状態で走らせると ESLint は終了コード 2 で落ちる。
# それを「検出あり」と数えると、環境の不備が測定結果に化ける。
if [ ! -d node_modules ]; then
  echo "006-redos-safety/node_modules がありません。先に依存を入れてください。"
  echo "  cd 006-redos-safety && npm ci"
  exit 1
fi

# ESLint の終了コード: 0 = 指摘なし / 1 = 指摘あり / 2 = 設定・依存のエラー
run_case() {
  local label="$1" config="$2"
  echo "■ $label"
  local output
  output=$(npx eslint --config "$config" "$TARGET" 2>&1)
  local code=$?
  echo "  終了コード: $code"
  case "$code" in
    0)
      echo "  検出: なし"
      ;;
    1)
      local errors
      errors=$(printf '%s\n' "$output" | /usr/bin/grep -c "  error  " || true)
      echo "  検出件数: $errors"
      printf '%s\n' "$output" | /usr/bin/grep "  error  " | /usr/bin/sed 's/^/    /' | cut -c1-150
      ;;
    *)
      echo "  ESLint が設定または依存のエラーで終了しました（検出結果ではありません）"
      printf '%s\n' "$output" | head -5 | /usr/bin/sed 's/^/    /'
      ;;
  esac
  echo
}

echo "対象ファイル: $TARGET"
echo "  危険な形 2 つ（(a+)+\$ と (a|a)*\$）と安全な形 2 つを含む"
echo

run_case "設定なし" eslint-config/eslint.config.off.mjs
run_case "no-super-linear-backtracking だけ有効" eslint-config/eslint.config.on.mjs
run_case "プラグインの推奨設定" eslint-config/eslint.config.recommended.mjs

echo "■ 読み取れること"
echo "  ・設定を入れなければ、危険な形が 2 つあっても検査は成功で終わる"
echo "  ・1 つのルールだけ有効にすると (a|a)* を取りこぼす"
echo "  ・推奨設定では no-dupe-disjunctions という別のルールがそれを拾う"
echo "  → 危険の種類ごとに担当するルールが違う。1 つ入れて安心しない"
