#!/usr/bin/env bash
# 同じ意図を BRE / ERE / Python / JavaScript でどう書き分けるかを、実行して確かめる。
#
# matrix.sh は「その機能が使えるか」を測った。ここで作るのは移植のための
# 対応表である。同じことをやりたいとき、系統ごとに何をどう書き替えるのか。
#
# 実装上の注意: eval を使わない（バックスラッシュが引用符の層で失われるため）。
set -uo pipefail

GREP=/usr/bin/grep

if command -v node >/dev/null 2>&1; then HAS_NODE=1; else HAS_NODE=0; fi

# 判定: 通ってほしい入力に一致し、通ってほしくない入力に一致しないなら ○
judge_grep() {  # judge_grep <yes> <no> <grep 引数...>
  local yes="$1" no="$2"; shift 2
  printf '%s\n' "$yes" | "$GREP" -q "$@" 2>/dev/null || return 1
  printf '%s\n' "$no" | "$GREP" -q "$@" 2>/dev/null && return 1
  return 0
}

judge_py() {  # judge_py <yes> <no> <pattern>
  python3 - "$1" "$2" "$3" <<'PY' 2>/dev/null
import re, sys
yes, no, pattern = sys.argv[1], sys.argv[2], sys.argv[3]
ok = bool(re.search(pattern, yes)) and not re.search(pattern, no)
sys.exit(0 if ok else 1)
PY
}

judge_js() {  # judge_js <yes> <no> <pattern>
  [ "$HAS_NODE" -eq 1 ] || return 2
  node -e '
const [yes, no, pattern] = process.argv.slice(1);
let re;
try { re = new RegExp(pattern); } catch (e) { process.exit(1); }
process.exit(re.test(yes) && !re.test(no) ? 0 : 1);
' "$1" "$2" "$3" 2>/dev/null
}

mark() {
  case "$1" in
    0) printf "○" ;;
    2) printf "—" ;;   # その実行系が手元に無い
    *) printf "×" ;;
  esac
}

row() {  # row <やりたいこと> <yes> <no> <BRE> <ERE> <Python> <JavaScript>
  local intent="$1" yes="$2" no="$3" bre="$4" ere="$5" py="$6" js="$7"
  judge_grep "$yes" "$no" "$bre";      local b=$?
  judge_grep "$yes" "$no" -E "$ere";   local e=$?
  judge_py   "$yes" "$no" "$py";       local p=$?
  judge_js   "$yes" "$no" "$js";       local j=$?
  printf "  %-16s %-18s %s   %-14s %s   %-14s %s   %-14s %s\n" \
    "$intent" "$bre" "$(mark $b)" "$ere" "$(mark $e)" "$py" "$(mark $p)" "$js" "$(mark $j)"
}

echo "実行系の版"
printf "  grep    : %s\n" "$("$GREP" --version 2>&1 | head -1)"
printf "  python3 : %s\n" "$(python3 --version 2>&1)"
if [ "$HAS_NODE" -eq 1 ]; then
  printf "  node    : %s\n" "$(node --version 2>&1)"
else
  printf "  node    : 見つかりません（JavaScript の列は — になります）\n"
fi
echo

echo "■ 同じ意図を 4 つの系統で書き分ける"
printf "  %-16s %-18s %s   %-14s %s   %-14s %s   %-14s %s\n" \
  "やりたいこと" "BRE（素の grep）" " " "ERE（grep -E）" " " "Python" " " "JavaScript" " "
echo "  ---------------------------------------------------------------------------------------------------------"
row "数字 3 桁"    "abc123"  "abcxyz"   '[0-9]\{3\}'        '[0-9]{3}'      '[0-9]{3}'      '[0-9]{3}'
row "b が 1 個以上" "abbb"    "ac"       'ab\+'              'ab+'           'ab+'           'ab+'
row "b が 0 か 1 個" "ac"      "abbc"     '^ab\{0,1\}c$'      '^ab?c$'        '^ab?c$'        '^ab?c$'
row "cat か dog"  "hotdog"  "bird"     '\(cat\|dog\)'      '(cat|dog)'     '(cat|dog)'     '(cat|dog)'
row "同じ語の重複"  "the the" "the cat"  '\([a-z]\+\) \1'    '([a-z]+) \1'   '([a-z]+) \1'   '([a-z]+) \1'
echo

# ここだけ「通ってほしくない入力」を全角数字にしてある。
# \d の担当範囲が系統ごとに違うため、同じ書き方でも結果が割れる。
echo "■ 同じ \\d が同じ範囲を指すとは限らない"
printf "  %-16s %-18s %s   %-14s %s   %-14s %s   %-14s %s\n" \
  "やりたいこと" "BRE（素の grep）" " " "ERE（grep -E）" " " "Python" " " "JavaScript" " "
echo "  ---------------------------------------------------------------------------------------------------------"
row "半角数字だけ 3 桁" "abc123" "abc１２３" '[0-9]\{3\}' '[0-9]{3}' '\d{3}' '\d{3}'
row "（書き替えた形）"   "abc123" "abc１２３" '[0-9]\{3\}' '[0-9]{3}' '[0-9]{3}' '[0-9]{3}'
echo

echo "■ BRE では記号がそのままの文字になる"
printf '%s\n' "abbb" | "$GREP" -q 'ab+' 2>/dev/null \
  && echo "  'ab+' が abbb に一致した   ○（+ が量指定子として働いた）" \
  || echo "  'ab+' が abbb に一致した   ×（+ はただの文字として扱われた）"
printf '%s\n' "ab+" | "$GREP" -q 'ab+' 2>/dev/null \
  && echo "  'ab+' が ab+ に一致した    ○（+ という文字そのものに当たった）" \
  || echo "  'ab+' が ab+ に一致した    ×"
echo

echo "■ 系統をまたいでも同じ意味になる書き方"
echo "  （それぞれ一致してほしい入力を添えて確かめます）"
while IFS='|' read -r pattern sample; do
  printf '%s\n' "$sample" | "$GREP" -q "$pattern" 2>/dev/null; b=$?
  printf '%s\n' "$sample" | "$GREP" -qE "$pattern" 2>/dev/null; e=$?
  python3 -c "import re,sys; sys.exit(0 if re.search(sys.argv[1], sys.argv[2]) else 1)" \
    "$pattern" "$sample" 2>/dev/null; p=$?
  if [ "$HAS_NODE" -eq 1 ]; then
    node -e 'process.exit(new RegExp(process.argv[1]).test(process.argv[2]) ? 0 : 1)' \
      "$pattern" "$sample" 2>/dev/null; j=$?
  else
    j=2
  fi
  printf "  %-10s 入力 %-10s BRE %s   ERE %s   Python %s   JavaScript %s\n" \
    "$pattern" "$sample" "$(mark $b)" "$(mark $e)" "$(mark $p)" "$(mark $j)"
done <<'EOF'
[0-9]|abc123
[a-z]|abc123
^abc|abc123
abc$|123abc
[^0-9]|abc123
EOF
echo

echo "■ 読み取れること（実測に基づく）"
echo "  BRE では + ? { } ( ) | にバックスラッシュが要る。付け忘れるとただの文字になる"
echo "  文字クラスとアンカーは 4 系統で同じに書ける。移植で壊れにくい"
echo "  最短マッチは書き替えでは移せない（該当する書き方が BRE / ERE に無い）"
echo "  \\d は Python が全角数字も拾い、JavaScript は半角だけを拾う。[0-9] と書けば揃う"
