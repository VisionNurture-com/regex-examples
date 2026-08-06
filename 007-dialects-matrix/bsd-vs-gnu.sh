#!/usr/bin/env bash
# BSD grep と GNU grep に同じパターンをかけて、割れる箇所を並べる。
#
# matrix.sh は 1 つの環境で「その機能が使えるか」を測る。CI では macOS と
# Ubuntu の両方で回るため、2 つの結果を見比べれば差は分かる。だがそれには
# 2 環境ぶんのログが要る。
#
# ここでは **1 台の中に両方の grep がある場合**に、同じ実行の中で並べる。
# macOS で Homebrew の grep（ggrep）を入れていると、この形で比べられる。
# 片方しか無い環境では、見つかったほうだけを表示する。
set -uo pipefail

find_bsd() {
  if [ -x /usr/bin/grep ] && /usr/bin/grep --version 2>&1 | head -1 | grep -q BSD; then
    echo /usr/bin/grep
  fi
}

find_gnu() {
  for candidate in ggrep /opt/homebrew/opt/grep/libexec/gnubin/grep /usr/bin/grep /bin/grep; do
    local path
    path=$(command -v "$candidate" 2>/dev/null) || continue
    if "$path" --version 2>&1 | head -1 | grep -q "GNU grep"; then
      echo "$path"
      return
    fi
  done
}

BSD=$(find_bsd)
GNU=$(find_gnu)

[ -n "$BSD" ] && printf "BSD: %s\n" "$("$BSD" --version 2>&1 | head -1)" || echo "BSD: 見つかりません"
[ -n "$GNU" ] && printf "GNU: %s\n" "$("$GNU" --version 2>&1 | head -1)" || echo "GNU: 見つかりません"
echo

if [ -z "$BSD" ] && [ -z "$GNU" ]; then
  echo "比較できる grep がありません。"
  exit 0
fi

run() {  # run <grep パス> <入力> <引数...>
  local cmd="$1" input="$2"; shift 2
  [ -z "$cmd" ] && { printf "—"; return; }
  printf '%s\n' "$input" | "$cmd" -q "$@" 2>/dev/null && printf "○" || printf "×"
}

t() {  # t <ラベル> <入力> <引数...>
  local label="$1" input="$2"; shift 2
  printf "  %-38s BSD %s   GNU %s\n" \
    "$label" "$(run "$BSD" "$input" "$@")" "$(run "$GNU" "$input" "$@")"
}

echo "■ 同じパターンを両方の grep にかける"
t 'grep -E の \d が数字 123 に一致' 'abc123' -E '\d{3}'
t 'grep -E の \d が文字 ddd に一致' 'abcddd' -E '\d{3}'
t 'grep -E の \w が英数字に一致'    'abc'    -E '\w{3}'
t 'grep -E の \s が空白に一致'      'a b'    -E 'a\sb'
t 'grep -E の後方参照 (ab)\1'       'abab'   -E '(ab)\1'
t 'grep -P（PCRE）が使える'         'foo1'   -P 'foo(?=1)'
echo

echo "■ 最短マッチ <.*?> で最初のタグだけ取れるか"
for pair in "BSD:$BSD" "GNU:$GNU"; do
  name=${pair%%:*}
  cmd=${pair#*:}
  if [ -z "$cmd" ]; then
    printf "  %-10s （見つかりません）\n" "$name"
    continue
  fi
  out=$(printf '<a><b>\n' | "$cmd" -Eo '<.*?>' 2>/dev/null | head -1)
  printf "  %-10s '<.*?>' の 1 件目 → %s\n" "$name" "${out:-（出力なし）}"
done
echo

echo "■ 読み取れること（実測に基づく）"
echo "  \\d の解釈が正反対になる。BSD は数字、GNU は文字の d として扱う"
echo "  \\w と \\s と後方参照は両方で同じに働く。割れるのは \\d と -P と最短マッチ"
echo "  最短マッチは BSD では効き、GNU では最長まで取る"
