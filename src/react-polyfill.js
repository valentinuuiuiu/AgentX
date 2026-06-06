import * as React from 'react';

// Ensure React is available globally before any component or library imports run.
// This is critical for SES/MetaMask lockdown compatibility when libraries
// access React APIs through module namespace bindings.
const fallbackMemo = typeof React.memo === 'function'
  ? React.memo
  : component => component;

const forwardRefImpl = typeof React.forwardRef === 'function'
  ? React.forwardRef
  : render => fallbackMemo(function ForwardRef(props, ref) {
      return render(props, ref);
    });

const createRefImpl = typeof React.createRef === 'function'
  ? React.createRef
  : function () {
      return { current: null };
    };

const memoImpl = typeof React.memo === 'function'
  ? React.memo
  : component => component;

const safeReact = {
  ...React,
  forwardRef: forwardRefImpl,
  memo: memoImpl,
  createRef: createRefImpl,
  createContext: typeof React.createContext === 'function' ? React.createContext : defaultValue => ({ Provider: () => null, Consumer: () => null, defaultValue }),
  createElement: typeof React.createElement === 'function' ? React.createElement : () => null,
  cloneElement: typeof React.cloneElement === 'function' ? React.cloneElement : element => element,
  isValidElement: typeof React.isValidElement === 'function' ? React.isValidElement : () => false,
  Component: React.Component,
  Fragment: React.Fragment,
  Children: typeof React.Children === 'object' && React.Children !== null ? React.Children : {
    map: (children, fn) => Array.isArray(children) ? children.map(fn) : [],
    toArray: children => Array.isArray(children) ? children : [children],
  },
  useRef: typeof React.useRef === 'function' ? React.useRef : createRefImpl,
  useMemo: typeof React.useMemo === 'function' ? React.useMemo : callback => callback(),
  useCallback: typeof React.useCallback === 'function' ? React.useCallback : callback => callback,
  useContext: typeof React.useContext === 'function' ? React.useContext : () => null,
  useEffect: typeof React.useEffect === 'function' ? React.useEffect : () => {},
  useLayoutEffect: typeof React.useLayoutEffect === 'function' ? React.useLayoutEffect : () => {},
};

if (typeof globalThis.React !== 'object' || globalThis.React === null) {
  globalThis.React = safeReact;
} else {
  try {
    Object.assign(globalThis.React, safeReact);
  } catch (e) {
    // globalThis.React may be frozen by SES lockdown; that's OK -
    // the inline HTML script and ses-polyfill.js already set it up
    console.warn('[react-polyfill] Could not assign to globalThis.React (may be frozen):', e.message);
  }
}

export default React;
