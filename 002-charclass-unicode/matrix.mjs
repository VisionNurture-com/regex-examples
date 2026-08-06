#!/usr/bin/env node
/**
 * 同じ日本語入力を JavaScript の正規表現にかけて、Python との差を見る。
 *
 * Python 側（matrix.py）と並べて読むと、文字クラスの判定そのものより
 * 「1 文字をどう数えるか」の違いが効いてくることが分かる。
 */

const SUBJECTS = [
  ['半角数字', '0123'],
  ['全角数字', '０１２３'],
  ['丸数字', '①②③'],
  ['半角英字', 'abc'],
  ['全角英字', 'ａｂｃ'],
  ['漢字', '日本語'],
  ['半角カナ', 'ｱｲｳ'],
  ['絵文字（BMP 外）', '🍣🍺'],
  ['結合文字（が = か + 濁点）', 'が'],
];

const CLASSES = [
  ['\\d', (s) => /^(?:\d)+$/.test(s)],
  ['[0-9]', (s) => /^(?:[0-9])+$/.test(s)],
  ['\\w', (s) => /^(?:\w)+$/.test(s)],
  ['.', (s) => /^(?:.)+$/.test(s)],
];

const mark = (ok) => (ok ? '○' : '×');

console.log(`Node ${process.version}\n`);

let header = '入力'.padEnd(30) + '例'.padEnd(12);
for (const [label] of CLASSES) header += label.padEnd(8);
header += 'length  実文字数';
console.log(header);
console.log('-'.repeat(header.length));

for (const [label, text] of SUBJECTS) {
  let line = label.padEnd(30) + text.padEnd(12);
  for (const [, test] of CLASSES) line += mark(test(text)).padEnd(8);
  // length は UTF-16 の単位数、[...text] は符号位置の数
  line += String(text.length).padEnd(8) + String([...text].length);
  console.log(line);
}

console.log('\n■ ドットは絵文字を 1 文字として扱えるか');
const emoji = '🍣';
console.log(`  /^.$/ が ${emoji} に一致するか        : ${mark(/^.$/.test(emoji))}  ← u フラグなし`);
console.log(`  /^.$/u が ${emoji} に一致するか       : ${mark(/^.$/u.test(emoji))}  ← u フラグあり`);
console.log(`  "${emoji}".length                     : ${emoji.length}（UTF-16 の単位数）`);
console.log(`  [..."${emoji}"].length               : ${[...emoji].length}（符号位置の数）`);

console.log('\n■ Unicode プロパティ（Python の標準 re には無い）');
console.log(`  /^\\p{Script=Han}+$/u が 日本語 に一致 : ${mark(/^\p{Script=Han}+$/u.test('日本語'))}`);
console.log(`  /^\\p{Nd}+$/u が ０１２３ に一致       : ${mark(/^\p{Nd}+$/u.test('０１２３'))}`);

console.log('\n■ v フラグ（ES2024）の集合演算');
try {
  const subtraction = new RegExp('^[\\p{ASCII}--[0-9]]+$', 'v');
  console.log(`  集合差 [\\p{ASCII}--[0-9]] が abc に一致 : ${mark(subtraction.test('abc'))}`);
  console.log(`  同じものが 123 に一致                   : ${mark(subtraction.test('123'))}  ← 数字は引かれている`);
  const intersection = new RegExp('^[\\p{Script=Han}&&\\p{Letter}]+$', 'v');
  console.log(`  積集合 [\\p{Script=Han}&&\\p{Letter}] が 日本語 に一致 : ${mark(intersection.test('日本語'))}`);
} catch (e) {
  console.log(`  v フラグが使えません: ${e.message}`);
}

console.log('\n■ 覚えておくこと');
console.log('  ・\\d は JavaScript では半角数字だけです（Python は全角にも一致します）');
console.log('  ・u フラグなしのドットは絵文字を 2 つに割ります');
console.log('  ・結合文字は見た目が 1 文字でも 2 つの符号位置です');
console.log('  ・文字クラスの引き算・積は v フラグ（ES2024・Node 20.12 以降）で書けます');
