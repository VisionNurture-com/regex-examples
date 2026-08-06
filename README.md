# regex-examples

正規表現の「なぜこう動くか」を、手元で出力させて確かめるためのサンプル集です。

記事シリーズ **正規表現 基礎**（全 7 回・[001 から読む](https://www.visionnurture.com/regex_basics_for_beginner_001/)）と一緒に使うコードです。

## ディレクトリ

| パス | 内容 | 対応記事 |
|---|---|---|
| `001-metachar-trace/` | パターンがどこまで進んでどこで失敗したかを出力させる | 001 基本メタ文字 |
| `002-charclass-unicode/` | 日本語入力（全角・丸数字・絵文字）が文字クラスでどう扱われるか | 002 文字クラス |
| `003-quantifier-bench/` | 貪欲・最短・否定文字クラスの実行時間を測る | 003 量指定子 |
| `004-group-replace/` | 同じ置換を Python / JavaScript / sed / Rust で書き比べる | 004 グループ化と置換 |
| `005-lookaround-matrix/` | 先読み・後読み・アトミックグループが自分の環境で使えるか調べる | 005 先読み・後読み |
| `006-redos-safety/` | ReDoS の再現、記法による回避、検出ツールの比較、CI への組み込み | 006 実践パターンと ReDoS |
| `007-dialects-matrix/` | 同一パターンを複数の実行系にかけて差分を出す | 007 方言 |
| `tools/` | 測るためのコードと、環境を書き出すスクリプト | — |
| `tools/results/` | 実行するとここへ実測値（JSON）が保存されます | — |

## 動かす

各章ディレクトリは単体で完結します。前の章を実行していなくても動きます。

```bash
# 自分の環境を書き出す（あとで数値を見比べるときに使う）
python3 tools/env_report.py

# 章ごとに実行する
make 001    # マッチ過程を出力する
make 003    # 量指定子の実行時間を測る

# 全章を実行する
make all
```

`make 006` は初回に `006-redos-safety` で `npm ci` を実行します（検出ツールと ESLint プラグインを使うため）。手で入れる場合は次のとおりです。

```bash
cd 006-redos-safety && npm ci
```

### 外部の道具が要る測定

`.NET` / Go / Rust / Vectorscan / Docker を使う測定は `make all` から分けてあります。**道具が見つからない環境では飛ばして終わる**ので、どこで走らせても失敗しません。

```bash
make 006-engines    # 同じ (a+)+$ を Python / JavaScript / Go / .NET / Rust で測る
make 007-hyperscan  # パターン数を 1→1000 に増やしたときのスキャン時間（要 Vectorscan）
make 007-postgres   # DB 側の正規表現とインデックスの効き方（要 Docker）
make extra          # 上記 3 つをまとめて実行する
```

`007-postgres` は PostgreSQL のコンテナを先に起動しておきます。

```bash
docker run -d --name regex-pg -e POSTGRES_PASSWORD=devpass -p 55432:5432 postgres:18
```

## 記事とこのリポジトリ、どちらを見るか

**コードは記事本文に全文載っています。GitHub を開かなくても読めます。** ここにあるのは同じ内容で、コピーして手元で走らせるためのものです。

- 章ディレクトリに、記事に載っていないコードはありません。記事を読むだけで追試できます
- 記事の数値は `tools/` の計測コードで測ったものです。同じコードを自分の環境で走らせれば測り直せます

## 必要なもの

章によって必要なものが変わります。**その章で使うものだけ**あれば動きます。

| 章 | 必要なもの |
|---|---|
| 001 / 003 | Python 3.11 以降 |
| 002 | Python 3.11 以降、Node.js 20.12 以降（`v` フラグを使うため） |
| 004 | Python、Node.js、sed、（任意）Rust |
| 005 | Python 3.11 以降、Node.js、（任意）Go / Rust / .NET |
| 006 | Python、Node.js、npm |
| 007 | 上記に加えて grep / sed（BSD・GNU の差を見るため） |
| 006-engines | （任意）Go / .NET / Rust — 無い実行系は行ごと飛ばします |
| 007-hyperscan | Vectorscan（macOS: `brew install vectorscan` / Ubuntu: `libhyperscan-dev`）と C コンパイラ |
| 007-postgres | Docker |

> Python 3.11 以降が必要なのは、アトミックグループ `(?>...)` と所有量指定子 `a*+` が 3.11 で追加されたためです。

## この数値をどう読むか

実行時間の**絶対値は環境と回ごとに変わります**。自分の環境で見るべきは、桁の差や倍率のほうです。記事の掲載値と手元の値がずれても、同じ倍率が出ていれば同じ結論になります。

比べるときの手がかりは `tools/results/*.json` にそろえてあります。

- **OS・CPU・各実行系の版**が測定ごとに入っているので、自分の環境と見比べられます
- **試行回数と集計方法**（最小値か中央値か）が書いてあるので、同じ条件で測り直せます
- **ウォームアップは分けて計測**してあります。1 回目だけ遅い分は数値に混ざりません

## ライセンス

MIT License
