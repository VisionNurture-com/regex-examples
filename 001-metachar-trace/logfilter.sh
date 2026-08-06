#!/usr/bin/env bash
# 4 記号（. ^ $ \）だけで、アクセスログを段階的に絞り込む。
#
# 題材は access.log（10 行）。example.com からのアクセスだけを数えたい、
# という 1 つの目的に対して、書き方を 4 段階で直していく。
#
# 意図的な制約: 量指定子（* + ? {n,m}）は使わない。入門記事の範囲を
# 4 記号に限定しているため、複数条件はパイプでつないで表現する。
#
# 実装上の注意: パターンは変数のまま渡す（eval で組み立てるとバックスラッシュが
# 引用符の層で失われる。本リポジトリの 007 で実際に起きた事故のため避けている）。
set -uo pipefail

GREP=/usr/bin/grep
LOG="$(dirname "$0")/access.log"

count() {  # count <入力文字列>
  if [ -z "$1" ]; then echo 0; else printf '%s\n' "$1" | "$GREP" -c .; fi
}

show() {  # show <見出し> <コマンド説明> <出力>
  local label="$1" cmd="$2" out="$3"
  echo "■ $label"
  echo "   $cmd"
  if [ -z "$out" ]; then
    echo "   （一致なし）"
  else
    printf '%s\n' "$out" | sed 's/^/   /'
  fi
  echo "   一致 $(count "$out") 行"
  echo
}

echo "対象: access.log（全 $(wc -l < "$LOG" | tr -d ' ') 行）"
echo

step1=$("$GREP" -E 'example.com' "$LOG" || true)
show "1. そのまま書く" "grep -E 'example.com' access.log" "$step1"

step2=$("$GREP" -E 'example\.com' "$LOG" || true)
show "2. ドットをエスケープする" "grep -E 'example\\.com' access.log" "$step2"

step3=$("$GREP" -E '^2026' "$LOG" | "$GREP" -E 'example\.com' || true)
show "3. 行頭を固定してコメント行を外す" "grep -E '^2026' access.log | grep -E 'example\\.com'" "$step3"

step4=$("$GREP" -E '^2026' "$LOG" | "$GREP" -E 'ref=example\.com$' || true)
show "4. 行末も固定して別ホストを外す" "grep -E '^2026' access.log | grep -E 'ref=example\\.com\$'" "$step4"

echo "■ 読み取れること"
echo "  ・1 は examplexcom と example-com.test にも当たる（. が任意の1文字）"
echo "  ・2 で誤マッチは消えるが、# で始まるコメント行はまだ残る"
echo "  ・3 で行頭を固定するとコメント行が落ちる"
echo "  ・4 で行末まで固定すると mail.example.com のような別ホストも落ちる"
