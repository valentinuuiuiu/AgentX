/**
 * Vite plugin to fix Recharts compatibility with MetaMask SES lockdown.
 *
 * Recharts 3.x uses a pattern like:
 *   const react = typeof React !== 'undefined' ? React : (typeof globalThis !== 'undefined' ? globalThis.React : undefined);
 *   const memoImpl = react && typeof react.memo === 'function' ? react.memo : (component => component);
 *   const forwardRef = react && typeof react.forwardRef === 'function' ? react.forwardRef : (render => ...);
 *
 * After Rollup bundles this, the `typeof React !== 'undefined'` check always passes
 * (React is a module namespace that's always defined), so the globalThis.React fallback
 * is dead code. When SES lockdown freezes the namespace and strips forwardRef,
 * `react.forwardRef` becomes undefined with no fallback.
 *
 * This plugin removes the `const react = typeof React !== 'undefined' ? React : ...`
 * line entirely, since `import * as React from 'react'` already provides React.
 * The memoImpl/createRefImpl/forwardRef variables then use the imported React directly.
 * Recharts already has fallback implementations for when forwardRef/memo/createRef
 * are missing, so those fallbacks will kick in if SES strips the APIs.
 */
export default function rechartsSesFixPlugin() {
  return {
    name: 'recharts-ses-fix',
    enforce: 'pre',

    transform(code, id) {
      // Only transform Recharts source files
      if (!id.includes('node_modules/recharts')) return null;

      let modified = false;

      // Remove the `const react = typeof React !== 'undefined' ? React : ...` line
      // This line shadows the `import * as React from 'react'` and creates a
      // variable that may point to a frozen namespace without forwardRef.
      // After removal, the `import * as React` is used directly.
      const reactLinePattern = /const\s+react\s*=\s*typeof\s+React\s*!==?\s*['"]undefined['"]\s*\?\s*React\s*:\s*\(?\s*typeof\s+globalThis\s*!==?\s*['"]undefined['"]\s*\?\s*globalThis\.React\s*:\s*undefined\s*\)?\s*;/g;

      if (reactLinePattern.test(code)) {
        code = code.replace(reactLinePattern, '// [SES-fix] removed: const react = typeof React !== "undefined" ? React : globalThis.React');
        modified = true;
      }

      // Replace `react && typeof react.memo === 'function' ? react.memo : ...`
      // with `typeof React.memo === 'function' ? React.memo : ...`
      // (use the imported React directly instead of the local `react` variable)
      code = code.replace(
        /react\s*&&\s*typeof\s+react\.memo\s*===?\s*['"]function['"]\s*\?\s*react\.memo\s*:/g,
        'typeof React.memo === "function" ? React.memo :'
      );

      code = code.replace(
        /react\s*&&\s*typeof\s+react\.createRef\s*===?\s*['"]function['"]\s*\?\s*react\.createRef\s*:/g,
        'typeof React.createRef === "function" ? React.createRef :'
      );

      code = code.replace(
        /react\s*&&\s*typeof\s+react\.forwardRef\s*===?\s*['"]function['"]\s*\?\s*react\.forwardRef\s*:/g,
        'typeof React.forwardRef === "function" ? React.forwardRef :'
      );

      return { code, map: null };
    }
  };
}