import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";
import pluginQuery from "@tanstack/eslint-plugin-query";
import simpleImportSort from "eslint-plugin-simple-import-sort";

export default tseslint.config(
  { ignores: ["dist"] },
  {
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommended,
      ...pluginQuery.configs["flat/recommended"],
    ],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      "simple-import-sort": simpleImportSort,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      "import/order": "off",
      "import/first": "off",
      "simple-import-sort/imports": [
        "warn",
        {
          groups: [
            // Note that if you use the `node:` prefix for Node.js builtins,
            // you can avoid this complexity: You can simply use "^node:".
            ["^node:"],
            // Packages. `react` and `@tanstack` related packages come first.
            ["^react$", "^(react-dom|@tanstack)(/.*|$)", "^@?\\w"],
            // Internal packages.
            ["^(server)(/.*|$)"],
            // Side effect imports.
            ["^\\u0000"],
            // @self imports.
            ["^(@self)(/.*|$)\\w"],
            // Parent imports. Put `..` last.
            ["^\\.\\.(?!/?$)", "^\\.\\./?$"],
            // Other relative imports. Put same-folder imports and `.` last.
            ["^\\./(?=.*/)(?!/?$)", "^\\.(?!/?$)", "^\\./?$"],
            // Style imports.
            ["^.+\\.s?css$"],
          ],
        },
      ],
      "simple-import-sort/exports": "warn",
    },
  },
);
