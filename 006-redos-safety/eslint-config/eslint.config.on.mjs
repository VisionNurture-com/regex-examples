// 設定あり: 正規表現の危険な形を検出するルールを有効にする
import regexp from 'eslint-plugin-regexp';

export default [
  {
    files: ['**/*.js'],
    languageOptions: { ecmaVersion: 2026, sourceType: 'module' },
    plugins: { regexp },
    rules: {
      // 入力の伸びに対して処理時間が跳ね上がる形を検出する
      'regexp/no-super-linear-backtracking': 'error',
    },
  },
];
