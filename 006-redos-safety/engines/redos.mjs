// JavaScript（V8）でのバックトラッキングの伸び方を測る
const LENGTHS = [16, 20, 24, 26, 28];
const results = [];
for (const n of LENGTHS) {
  const subject = 'a'.repeat(n) + '!';
  const start = process.hrtime.bigint();
  /(a+)+$/.test(subject);
  const sec = Number(process.hrtime.bigint() - start) / 1e9;
  results.push({ n, sec });
  console.log(`  n=${String(n).padStart(3)}  ${sec.toFixed(6)} s`);
  if (sec > 10) { console.log('  （10 秒を超えたため打ち切り）'); break; }
}
console.log(JSON.stringify({ engine: `Node ${process.version} (V8)`, results }));
