// 検査対象のサンプル。危険な形と安全な形を混ぜてある。

// 危険: 量指定子が入れ子になっている
const nested = /(a+)+$/;

// 危険: 選択肢が同じものを指している
const ambiguous = /(a|a)*$/;

// 安全: 入れ子がない
const flat = /^a+$/;

// 安全: 止まる文字を指定している
const bounded = /^[^>]*>$/;

export { nested, ambiguous, flat, bounded };
