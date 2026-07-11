import base from "@tayari/config/eslint/base.js";
import nextPlugin from "@next/eslint-plugin-next";

export default [
  ...base,
  {
    plugins: {
      "@next/next": nextPlugin,
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs["core-web-vitals"].rules,
      "@next/next/no-html-link-for-pages": "off",
    },
  },
  {
    ignores: [".next/"],
  },
];
