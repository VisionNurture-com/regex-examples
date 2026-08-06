#!/usr/bin/env bash
# scale.c をビルドして実行する。Vectorscan（Hyperscan 互換）が要る。
#
#   macOS   brew install vectorscan
#   Ubuntu  sudo apt install libhyperscan-dev
#
# 見つからない環境では、何が足りないかだけ出して終わる（失敗にはしない）。
set -uo pipefail
cd "$(dirname "$0")"

CC_BIN="${CC:-cc}"
INC=""
LIB=""

for prefix in /opt/homebrew /usr/local; do
  if [ -f "$prefix/include/hs/hs.h" ]; then
    INC="-I$prefix/include"
    LIB="-L$prefix/lib"
    break
  fi
done

if [ -z "$INC" ] && [ ! -f /usr/include/hs/hs.h ]; then
  echo "Vectorscan（hs/hs.h）が見つかりません。この測定は飛ばします。"
  echo "  macOS : brew install vectorscan"
  echo "  Ubuntu: sudo apt install libhyperscan-dev"
  exit 0
fi

# shellcheck disable=SC2086
if ! "$CC_BIN" scale.c -o scale $INC $LIB -lhs 2>/tmp/regex-hs-build.log; then
  echo "ビルドに失敗しました。この測定は飛ばします。"
  sed 's/^/  /' /tmp/regex-hs-build.log | head -5
  exit 0
fi

./scale
