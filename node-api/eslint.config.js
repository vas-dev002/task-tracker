// @ts-check
const eslint = require('@eslint/js');
const tseslint = require('typescript-eslint');
const eslintPluginPrettierRecommended = require('eslint-plugin-prettier/recommended');

module.exports = tseslint.config({
  files: ['src/**/*.ts'],
  extends: [
    eslint.configs.recommended,
    // @ts-ignore
    ...tseslint.configs.recommended,
    // @ts-ignore
    ...tseslint.configs.stylistic,
    // @ts-ignore
    eslintPluginPrettierRecommended,
  ],
});
