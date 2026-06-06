/**
 * SES Lockdown Polyfill for MetaMask Compatibility
 *
 * MetaMask injects a SES (Secure EcmaScript) lockdown that strips certain
 * JavaScript intrinsics (like Map.prototype.getOrInsert, Date.prototype.toTemporalInstant)
 * and can break React's forwardRef, createRef, and other APIs used by libraries
 * like recharts, radix-ui, etc.
 *
 * This script MUST run before any other JS to:
 * 1. Save references to React APIs before lockdown strips them
 * 2. Restore them after lockdown completes
 *
 * Error this fixes:
 *   SES_UNCAUGHT_EXCEPTION: TypeError: can't access property "forwardRef" of undefined
 *   at Surface.js:16
 */
(function () {
  'use strict';

  // Save native APIs that SES lockdown might strip
  const saved = {};

  // Ensure a safe React global object exists before any app or library code runs.
  function ensureReactGlobal() {
    if (typeof window.React !== 'object' || window.React === null) {
      try {
        window.React = {};
      } catch (e) {
        return;
      }
    }

    const reactGlobal = window.React;

    if (typeof reactGlobal.memo !== 'function') {
      reactGlobal.memo = reactGlobal.memo || (component => component);
    }
    if (typeof reactGlobal.forwardRef !== 'function') {
      reactGlobal.forwardRef = reactGlobal.forwardRef || (render => reactGlobal.memo(function ForwardRef(props, ref) {
        return render(props, ref);
      }));
    }
    if (typeof reactGlobal.createRef !== 'function') {
      reactGlobal.createRef = reactGlobal.createRef || function () {
        return { current: null };
      };
    }
    if (typeof reactGlobal.createContext !== 'function') {
      reactGlobal.createContext = reactGlobal.createContext || function (defaultValue) {
        return {
          Provider: function () { return null; },
          Consumer: function () { return null; },
          defaultValue
        };
      };
    }
    if (typeof reactGlobal.createElement !== 'function') {
      reactGlobal.createElement = reactGlobal.createElement || function () { return null; };
    }
    if (typeof reactGlobal.useRef !== 'function') {
      reactGlobal.useRef = reactGlobal.useRef || function (initialValue) {
        return { current: initialValue };
      };
    }
  }

  // Wait for React to be available on the global scope, then protect forwardRef
  // This handles both the case where React is loaded before and after lockdown
  function protectReactAPIs() {
    ensureReactGlobal();

    if (typeof window.React === 'object' && window.React !== null) {
      if (!saved.forwardRef && typeof window.React.forwardRef === 'function') {
        saved.forwardRef = window.React.forwardRef;
      }
      if (!saved.createRef && typeof window.React.createRef === 'function') {
        saved.createRef = window.React.createRef;
      }
      if (!saved.createElement && typeof window.React.createElement === 'function') {
        saved.createElement = window.React.createElement;
      }
      if (!saved.createContext && typeof window.React.createContext === 'function') {
        saved.createContext = window.React.createContext;
      }
      if (!saved.memo && typeof window.React.memo === 'function') {
        saved.memo = window.React.memo;
      }
      if (!saved.useRef && typeof window.React.useRef === 'function') {
        saved.useRef = window.React.useRef;
      }
    }
  }

  // Polyfill forwardRef if it gets stripped
  function restoreReactAPIs() {
    ensureReactGlobal();

    if (typeof window.React === 'object' && window.React !== null) {
      if (!window.React.forwardRef && saved.forwardRef) {
        window.React.forwardRef = saved.forwardRef;
      }
      if (!window.React.createRef && saved.createRef) {
        window.React.createRef = saved.createRef;
      }
      if (!window.React.createElement && saved.createElement) {
        window.React.createElement = saved.createElement;
      }
      if (!window.React.createContext && saved.createContext) {
        window.React.createContext = saved.createContext;
      }
      if (!window.React.memo && saved.memo) {
        window.React.memo = saved.memo;
      }
      if (!window.React.useRef && saved.useRef) {
        window.React.useRef = saved.useRef;
      }
    }
  }

  // Save immediately in case React is already loaded
  protectReactAPIs();

  // Also try after DOMContentLoaded and after load (lockdown may run between)
  document.addEventListener('DOMContentLoaded', function () {
    protectReactAPIs();
    restoreReactAPIs();
  });

  window.addEventListener('load', function () {
    protectReactAPIs();
    restoreReactAPIs();
  });

  // Use MutationObserver to detect when React mounts (fallback)
  // and restore APIs periodically for the first few seconds
  let restoreCount = 0;
  const restoreInterval = setInterval(function () {
    protectReactAPIs();
    restoreReactAPIs();
    restoreCount++;
    if (restoreCount > 20) { // Stop after ~10 seconds (20 * 500ms)
      clearInterval(restoreInterval);
    }
  }, 500);

  // Polyfill for Map.prototype.getOrInsert (removed by SES)
  if (typeof Map !== 'undefined' && !Map.prototype.getOrInsert) {
    Map.prototype.getOrInsert = function (key, value) {
      if (this.has(key)) {
        return this.get(key);
      }
      this.set(key, value);
      return value;
    };
  }

  // Polyfill for Map.prototype.getOrInsertComputed (removed by SES)
  if (typeof Map !== 'undefined' && !Map.prototype.getOrInsertComputed) {
    Map.prototype.getOrInsertComputed = function (key, fn) {
      if (this.has(key)) {
        return this.get(key);
      }
      const value = fn();
      this.set(key, value);
      return value;
    };
  }

  // Polyfill for WeakMap.prototype.getOrInsert (removed by SES)
  if (typeof WeakMap !== 'undefined' && !WeakMap.prototype.getOrInsert) {
    WeakMap.prototype.getOrInsert = function (key, value) {
      if (this.has(key)) {
        return this.get(key);
      }
      this.set(key, value);
      return value;
    };
  }

  // Polyfill for WeakMap.prototype.getOrInsertComputed (removed by SES)
  if (typeof WeakMap !== 'undefined' && !WeakMap.prototype.getOrInsertComputed) {
    WeakMap.prototype.getOrInsertComputed = function (key, fn) {
      if (this.has(key)) {
        return this.get(key);
      }
      const value = fn();
      this.set(key, value);
      return value;
    };
  }

  // Polyfill for Date.prototype.toTemporalInstant (removed by SES)
  if (typeof Date !== 'undefined' && !Date.prototype.toTemporalInstant) {
    Date.prototype.toTemporalInstant = function () {
      // Simplified polyfill - returns an object with epochNanoseconds
      const ms = this.getTime();
      const ns = ms * 1e6; // Convert milliseconds to nanoseconds
      return {
        epochNanoseconds: BigInt(ns),
        toString: () => this.toISOString(),
        valueOf: () => ms
      };
    };
  }

  // Global error handler to catch and recover from SES-related errors
  window.addEventListener('error', function (event) {
    if (event.message && (
      event.message.includes('forwardRef') ||
      event.message.includes('getOrInsert') ||
      event.message.includes('toTemporalInstant') ||
      event.message.includes('lockdown')
    )) {
      console.warn('[SES Polyfill] Caught SES-related error, attempting recovery:', event.message);
      restoreReactAPIs();
      // Prevent the error from crashing the app
      event.preventDefault();
      return true;
    }
  });

  // Also handle unhandled promise rejections from SES
  window.addEventListener('unhandledrejection', function (event) {
    if (event.reason && event.reason.message && (
      event.reason.message.includes('forwardRef') ||
      event.reason.message.includes('getOrInsert') ||
      event.reason.message.includes('lockdown')
    )) {
      console.warn('[SES Polyfill] Caught SES-related promise rejection:', event.reason.message);
      restoreReactAPIs();
      event.preventDefault();
    }
  });

  console.log('[SES Polyfill] SES lockdown compatibility shim loaded');
})();