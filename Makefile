.PHONY: help env all extra 001 002 003 004 005 006 006-deps 006-engines 006-limit 007 007-hyperscan 007-postgres clean

help:
	@echo "regex-examples — 章ごとに実行できます"
	@echo ""
	@echo "  make env    環境情報を記録する（測定前に 1 回）"
	@echo "  make 001    パターンがどこで失敗したかを出力する"
	@echo "  make 002    日本語入力が文字クラスでどう扱われるか"
	@echo "  make 003    量指定子の実行時間を測る"
	@echo "  make 004    同じ置換を 4 つの実行系で書き比べる"
	@echo "  make 005    先読み・アトミックが自分の環境で使えるか調べる"
	@echo "  make 006    ReDoS の再現と回避、検出ツールと ESLint 設定の比較"
	@echo "  make 007    同一パターンを複数の実行系にかけて差分を出す"
	@echo "  make all    上記を全部実行する"
	@echo ""
	@echo "  時間のかかる測定"
	@echo "  make 006-limit      28 文字を超えたときの待ち時間（3 分ほどかかります）"
	@echo ""
	@echo "  外部の道具が要る測定（無い環境では飛ばします）"
	@echo "  make 006-engines    同じパターンを Python / JS / Go / .NET / Rust で測る"
	@echo "  make 007-hyperscan  パターン数を増やしたときのスキャン時間（要 Vectorscan）"
	@echo "  make 007-postgres   DB 側の正規表現と実行計画（要 Docker）"
	@echo "  make extra          上記 3 つをまとめて実行する"

env:
	python3 tools/env_report.py

001:
	python3 001-metachar-trace/trace.py 'a.c' 'abbc'
	python3 001-metachar-trace/anchors.py
	bash 001-metachar-trace/logfilter.sh

002:
	python3 002-charclass-unicode/matrix.py
	node 002-charclass-unicode/matrix.mjs
	python3 002-charclass-unicode/formcheck.py

003:
	python3 003-quantifier-bench/bench.py
	python3 003-quantifier-bench/why.py
	python3 003-quantifier-bench/extract.py

004:
	bash 004-group-replace/run.sh
	python3 004-group-replace/matrix.py
	python3 004-group-replace/scope.py
	python3 004-group-replace/bench_capture.py

005:
	python3 005-lookaround-matrix/probe.py
	python3 005-lookaround-matrix/matrix.py
	python3 005-lookaround-matrix/port.py

# 検出ツールと ESLint プラグインは npm 依存を使う。
# 入っていない状態で走らせると「検査が失敗した」と「依存が無い」を取り違える。
006-deps:
	@if [ ! -d 006-redos-safety/node_modules ]; then \
	  echo "→ 006 の依存を入れます（npm ci）"; \
	  cd 006-redos-safety && npm ci; \
	fi

006: 006-deps
	python3 006-redos-safety/bench.py
	python3 006-redos-safety/rewrite.py
	node 006-redos-safety/detectors/compare.mjs
	bash 006-redos-safety/eslint-config/compare.sh

007:
	bash 007-dialects-matrix/matrix.sh
	bash 007-dialects-matrix/bsd-vs-gnu.sh
	bash 007-dialects-matrix/port.sh

all: env 001 002 003 004 005 006 007

# 「手元で試すなら 28 文字まで」という案内の根拠を測る。
# 1 回あたり数分かかるため all には入れず、必要なときだけ呼ぶ。
006-limit:
	python3 006-redos-safety/bench.py --limit

# ここから下は外部の道具（.NET / Go / Rust / Vectorscan / Docker）が要る測定。
# 見つからない道具は飛ばすので、どの環境で走らせても失敗しない。
006-engines:
	bash 006-redos-safety/engines/compare.sh

007-hyperscan:
	bash 007-dialects-matrix/hyperscan/run.sh

007-postgres:
	bash 007-dialects-matrix/postgres/compare.sh

extra: 006-engines 007-hyperscan 007-postgres

clean:
	rm -f tools/results/*.json
