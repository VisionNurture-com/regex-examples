# 007 — 同一パターンを複数の実行系にかける

対応記事: 正規表現の方言

## 動かす

```bash
bash matrix.sh       # 同じ機能を複数の実行系にかけて通るかを見る
bash bsd-vs-gnu.sh   # BSD grep と GNU grep を同じ実行の中で並べる
bash port.sh         # 同じ意図を BRE / ERE / Python / JavaScript で書き分ける対応表を作る
```

`make 007` で 3 本まとめて実行できます。

数千のパターンと 20 万行を扱う 2 つは外部の道具が要るため、別の入口にしてあります。
**道具が見つからない環境では飛ばして終わる**ので、失敗にはなりません。

```bash
bash hyperscan/run.sh      # make 007-hyperscan と同じ（要 Vectorscan + C コンパイラ）
bash postgres/compare.sh   # make 007-postgres と同じ（要 Docker）
```

## 何が出るか

### matrix.sh

数字クラス・最短マッチ・先読み・アトミックグループ・後方参照を、
grep（BRE / ERE / PCRE）・sed・Python・Node.js にかけた結果の一覧です。

同じ環境でも書き方によって通ったり通らなかったりすることが分かります。

### bsd-vs-gnu.sh

同じパターンを BSD grep と GNU grep の両方にかけ、割れる箇所を 1 つの表に並べます。
CI では 2 環境のログを見比べる必要がありますが、**1 台に両方の grep がある場合**は
これで同時に確かめられます（macOS + Homebrew の `ggrep` など）。

片方しか見つからない環境では、見つかったほうだけを表示します。

### port.sh

移植のための対応表です。5 つの「やりたいこと」を BRE / ERE / Python / JavaScript の
4 系統で書き分け、**通ってほしい入力に一致し、通ってほしくない入力に一致しない**ことを
両方確かめて ○ を出します。

BRE で記号がそのままの文字として扱われる様子と、系統をまたいでも同じ意味になる
書き方（文字クラス・アンカー）も併せて出します。

`\d` の行だけは 4 系統で割れます。Python は全角数字も数字として拾い、JavaScript は
半角だけを拾います。`[0-9]` と書き替えれば 4 系統で揃うところまで出します。

### hyperscan/run.sh

`scale.c` をビルドして実行します。同じ 8 MB の入力に対してパターン数を
1 / 10 / 100 / 1000 と増やし、コンパイル時間とスキャン時間の伸び方を分けて測ります。

パターン数を 1000 倍にしても、スキャンは 1 回のままです。伸びるのはコンパイル側だけです。

### postgres/compare.sh

20 万行のテーブルに対する正規表現検索の実行計画を、トライグラムインデックスの
有無で比べます。`Index Cond` に正規表現が現れるかどうかが読みどころです。

先に PostgreSQL のコンテナを起動しておきます。

```bash
docker run -d --name regex-pg -e POSTGRES_PASSWORD=devpass -p 55432:5432 postgres:18
```

## 実装上の注意

判定に `eval` を使っていません。パターンにバックスラッシュが含まれるため、
文字列を組み立てて `eval` に渡すと引用符の層でバックスラッシュが失われ、
「対応していない」という誤った結果が出ます。実際にこの書き方で 2 件取り違えました。

## 必要なもの

Python、Node.js、grep、sed（pcre2grep があれば PCRE 系も測ります）

`hyperscan/run.sh` は Vectorscan（macOS: `brew install vectorscan` / Ubuntu: `libhyperscan-dev`）と
C コンパイラ、`postgres/compare.sh` は Docker を使います。どちらも無ければ飛ばします。
