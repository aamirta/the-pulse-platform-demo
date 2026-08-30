import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // The react-hooks 7.x recommended preset includes experimental compiler rules
      // (set-state-in-effect, purity) that forbid standard patterns such as data fetching
      // in useEffect and Date.now() in event handlers. We keep the classic hooks rules
      // (rules-of-hooks, exhaustive-deps) and disable the experimental ones for this codebase.
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/set-state-in-render': 'off',
      'react-hooks/purity': 'off',

      // shadcn/ui components and context/hook modules intentionally export helpers alongside components.
      'react-refresh/only-export-components': 'off',

      // Keep TypeScript strictness high.
      '@typescript-eslint/no-explicit-any': 'error',
    },
  },
])
