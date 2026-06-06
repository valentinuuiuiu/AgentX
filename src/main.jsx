import './react-polyfill'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { Web3ContextProvider } from './contexts/Web3Context'
import { NotificationProvider } from './contexts/NotificationContext'

console.log('main.jsx executing'); // Debug log

// ============================================================
// SES Lockdown Recovery: MetaMask's lockdown strips React.forwardRef
// and other APIs. This guard ensures they're available.
// Error: "can't access property 'forwardRef' of undefined" (Surface.js:16)
// ============================================================
try {
  if (typeof React.forwardRef !== 'function') {
    console.error('[SES Recovery] React.forwardRef is missing! MetaMask SES lockdown may have stripped it.');
    React.forwardRef = function(render) {
      return React.memo(function ForwardRef(props, ref) {
        return render(props, ref);
      });
    };
    console.log('[SES Recovery] React.forwardRef polyfill installed');
  }
  if (typeof React.createRef !== 'function') {
    React.createRef = function() {
      return { current: null };
    };
    console.log('[SES Recovery] React.createRef polyfill installed');
  }
  if (typeof React.memo !== 'function') {
    React.memo = function(component) { return component; };
    console.log('[SES Recovery] React.memo polyfill installed');
  }
} catch (e) {
  console.warn('[SES Recovery] Could not patch React (may be frozen):', e.message);
}

// Ensure root element exists
const rootElement = document.getElementById('root')
if (!rootElement) {
  const root = document.createElement('div')
  root.id = 'root'
  document.body.appendChild(root)
}

// Create root and render app
const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(
  <React.StrictMode>
    <NotificationProvider>
      <Web3ContextProvider>
        <App />
      </Web3ContextProvider>
    </NotificationProvider>
  </React.StrictMode>
)