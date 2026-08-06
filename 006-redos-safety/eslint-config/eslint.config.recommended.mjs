// プラグインの推奨設定をそのまま使う（個別ルールだけを有効にした場合との差を見る）
import regexp from 'eslint-plugin-regexp';

export default [
  regexp.configs['flat/recommended'],
  {
    files: ['**/*.js'],
    languageOptions: { ecmaVersion: 2026, sourceType: 'module' },
  },
];
