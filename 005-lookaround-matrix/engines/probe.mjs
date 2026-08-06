// 機能判定の JavaScript 側。matrix.py から TSV を受け取り、判定結果を TSV で返す。
//
// 入力 1 行: id \t pattern \t subject \t expected \t flags
// 出力 1 行: id \t OK | NG:<実際にマッチした文字列> | ERROR:<メッセージ>
import { createInterface } from "node:readline";

const rl = createInterface({ input: process.stdin });

for await (const line of rl) {
  if (!line.trim()) continue;
  const [id, pattern, subject, expected, flags] = line.split("\t");
  let result;
  try {
    const re = new RegExp(pattern, flags || "");
    const m = subject.match(re);
    if (!m) {
      result = "NG:none";
    } else {
      result = m[0] === expected ? "OK" : `NG:${m[0]}`;
    }
  } catch (e) {
    result = `ERROR:${e.message.split("\n")[0]}`;
  }
  process.stdout.write(`${id}\t${result}\n`);
}
