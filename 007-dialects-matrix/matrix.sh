#!/usr/bin/env bash
# 同じパターンを複数の実行系にかけて、通るかどうかを一覧にする。
#
# 「grep では動いたのに Python では動かない」の正体は、
# 採用している規格の差（BRE / ERE / PCRE / ECMAScript）と、
# 実装の差（BSD / GNU）の二段階にある。
#
# 実装上の注意: 判定に eval を使わない。
# パターンはバックスラッシュを含むため、文字列を組み立てて eval に渡すと
# 引用符の層でバックスラッシュが失われ、「対応していない」という誤った結果が出る。
# 実際にこの書き方で node と grep の 2 件を取り違えた。コマンドは配列で直接渡す。
set -uo pipefail

# macOS の素の grep は環境によって別実装に差し替わっていることがある。
# 記事が対象とするのはシステムの grep なので、フルパスで呼ぶ。
GREP=/usr/bin/grep
SED=/usr/bin/sed

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf "  %-36s ○\n" "$label"
  else
    printf "  %-36s ×\n" "$label"
  fi
}

# 文字列を標準入力から渡して判定するための小さなラッパ
grep_in() {  # grep_in <入力> <grep 引数...>
  local input="$1"; shift
  printf '%s\n' "$input" | "$GREP" "$@"
}

echo "実行系の版"
printf "  grep      : %s\n" "$("$GREP" --version 2>&1 | head -1)"
printf "  sed       : %s\n" "$("$SED" --version 2>&1 | head -1 || echo 'BSD sed（--version なし）')"
printf "  python3   : %s\n" "$(python3 --version 2>&1)"
printf "  node      : %s\n" "$(node --version 2>&1)"
command -v pcre2grep >/dev/null 2>&1 && printf "  pcre2grep : %s\n" "$(pcre2grep --version 2>&1 | head -1)"
echo

echo "■ 数字 3 個にマッチさせる"
check "grep（BRE・素の grep）" grep_in 'abc123' '[0-9]\{3\}'
check "grep -E（ERE）" grep_in 'abc123' -E '[0-9]{3}'
check "grep -E の \\d が数字に一致するか" grep_in 'abc123' -E '\d{3}'
check "grep -E の \\d が d の字に一致するか" grep_in 'abcddd' -E '\d{3}'
check "python3 の \\d" python3 -c 'import re,sys; sys.exit(0 if re.search(r"\d{3}", "abc123") else 1)'
check "node の \\d" node -e 'process.exit(/\d{3}/.test("abc123") ? 0 : 1)'
echo

echo "■ 最短マッチ <.*?> でタグ 1 個だけを取れるか"
check "grep -Eo" bash -c 'printf "<a><b>\n" | /usr/bin/grep -Eo "<.*?>" | head -1 | /usr/bin/grep -qx "<a>"'
check "python3" python3 -c 'import re,sys; sys.exit(0 if re.search(r"<.*?>", "<a><b>").group()=="<a>" else 1)'
check "node" node -e 'process.exit("<a><b>".match(/<.*?>/)[0]==="<a>" ? 0 : 1)'
echo

echo "■ 先読み・後読みが使えるか"
check "grep -E（ERE には無い）" grep_in 'foo1' -E 'foo(?=1)'
check "grep -P（PCRE・GNU のみ）" grep_in 'foo1' -P 'foo(?=1)'
if command -v pcre2grep >/dev/null 2>&1; then
  check "pcre2grep（macOS の代替）" bash -c 'printf "foo1\n" | pcre2grep "foo(?=1)"'
fi
check "python3" python3 -c 'import re,sys; sys.exit(0 if re.search(r"foo(?=1)", "foo1") else 1)'
check "node" node -e 'process.exit(/foo(?=1)/.test("foo1") ? 0 : 1)'
echo

echo "■ 可変長の後読みが使えるか"
check "python3（固定長のみ）" python3 -c 'import re,sys; re.compile(r"(?<=\d+)円"); sys.exit(0)'
check "node（ES2018 以降は可変長も可）" node -e 'new RegExp("(?<=\\d+)円"); process.exit(0)'
echo

echo "■ アトミックグループ・所有量指定子が使えるか"
check "python3 アトミック (?>a+)b" python3 -c 'import re,sys; sys.exit(0 if re.match(r"(?>a+)b", "aaab") else 1)'
check "python3 所有 a*+b" python3 -c 'import re,sys; sys.exit(0 if re.match(r"a*+b", "aaab") else 1)'
check "node アトミック (?>a+)b" node -e 'new RegExp("(?>a+)b"); process.exit(0)'
check "node 所有 a*+b" node -e 'new RegExp("a*+b"); process.exit(0)'
echo

echo "■ sed -E で後方参照が使えるか（重複した語を消す）"
check "sed -E" bash -c 'printf "the the cat\n" | /usr/bin/sed -E "s/([a-z]+) \1/\1/" | /usr/bin/grep -qx "the cat"'
echo

echo "注: ○ は「そのコマンドが成功した」だけを意味します。"
echo "    意図どおりの結果かは、各章のスクリプトで確かめてください。"
