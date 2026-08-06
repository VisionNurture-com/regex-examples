#!/usr/bin/env bash
# データベースの中で正規表現を使うと何が起きるかを、実行計画の変化で見る。
#
# 「設定を入れた」と「設定が効いている」は別の話である。
# インデックスを作る前と後で、同じクエリの実行計画がどう変わるかを並べる。
#
# 前提: コンテナで PostgreSQL を起動しておく
#   docker run -d --name regex-pg -e POSTGRES_PASSWORD=devpass -p 55432:5432 postgres:18
set -uo pipefail

CONTAINER="${PG_CONTAINER:-regex-pg}"
ROWS="${ROWS:-200000}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker が見つかりません。この測定は飛ばします。"
  exit 0
fi

if ! docker exec "$CONTAINER" pg_isready -U postgres >/dev/null 2>&1; then
  echo "PostgreSQL のコンテナ '$CONTAINER' が起動していません。この測定は飛ばします。"
  echo "  docker run -d --name regex-pg -e POSTGRES_PASSWORD=devpass -p 55432:5432 postgres:18"
  exit 0
fi

echo "PostgreSQL: $(docker exec "$CONTAINER" psql -U postgres -tAc 'SHOW server_version')"
echo "行数: $ROWS"
echo

docker exec -i "$CONTAINER" psql -U postgres -v ON_ERROR_STOP=1 <<SQL
\\set QUIET on
CREATE EXTENSION IF NOT EXISTS pg_trgm;
DROP TABLE IF EXISTS logs;
CREATE TABLE logs(id serial primary key, msg text);
INSERT INTO logs(msg)
SELECT 'user' || g || ' action=login status=' ||
       (CASE WHEN g % 7 = 0 THEN 'fail' ELSE 'ok' END)
FROM generate_series(1, $ROWS) g;
ANALYZE logs;
\\set QUIET off

\\echo '■ インデックスなし'
EXPLAIN (ANALYZE, TIMING OFF, SUMMARY ON, COSTS OFF)
SELECT count(*) FROM logs WHERE msg ~ 'status=fail';

\\echo ''
\\echo '■ トライグラムインデックスを作る'
CREATE INDEX logs_msg_trgm ON logs USING gin (msg gin_trgm_ops);
ANALYZE logs;

\\echo ''
\\echo '■ インデックスあり（同じクエリ）'
EXPLAIN (ANALYZE, TIMING OFF, SUMMARY ON, COSTS OFF)
SELECT count(*) FROM logs WHERE msg ~ 'status=fail';
SQL

echo
echo "■ 読み取れること"
echo "  ・インデックスなしでは全行を読み、条件に合わない行を捨てている（Seq Scan）"
echo "  ・インデックスありでは正規表現の条件がインデックス側に降りる（Bitmap Index Scan）"
echo "  ・つまり DB の中の正規表現は「必ず全件走査」ではない"
echo "  → 効いているかどうかは EXPLAIN の行を見て判断する。速くなった気がする、では確かめたことにならない"
