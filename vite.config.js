
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';
import rechartsSesFixPlugin from './vite-plugin-recharts-ses-fix.js';

/**
 * Vite plugin to inject SES lockdown polyfill as the FIRST script in the HTML.
 * MetaMask's lockdown-install.js strips React.forwardRef and other intrinsics,
 * so this polyfill must run before anything else to save/restore those APIs.
 */
function sesPolyfillPlugin() {
  return {
    name: 'ses-polyfill-inject',
    transformIndexHtml(html) {
      return html.replace(
        /<head([^>]*)>/,
        `<head$1>
    <script>if (typeof window.React !== 'object' || window.React === null) { window.React = { memo: function(c){return c}, forwardRef: function(render){return function ForwardRef(props,ref){return render(props,ref)}}, createRef: function(){return{current:null}}, createContext: function(defaultValue){return{Provider:function(){return null},Consumer:function(){return null},defaultValue:defaultValue}}, createElement: function(){return null}, cloneElement: function(element){return element}, isValidElement: function(){return false}, useRef: function(initialValue){return{current:initialValue}}, useMemo: function(fn){return fn()}, useCallback: function(fn){return fn}, useContext: function(){return null}, useEffect: function(){}, useLayoutEffect: function(){}, Fragment: null, Children: { map: function(children, fn){return Array.isArray(children)?children.map(fn):[]}, toArray: function(children){return Array.isArray(children)?children:[children]} } }; }</script>
    <script src="/ses-polyfill.js"><\/script>`
      );
    },
    enforce: 'pre', // Run before other plugins
  };
}

export default defineConfig({
  plugins: [sesPolyfillPlugin(), rechartsSesFixPlugin(), react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@styles': path.resolve(__dirname, './src/styles'),
    }
  },
  css: {
    modules: {
      localsConvention: 'camelCaseOnly',
      generateScopedName: '[name]__[local]___[hash:base64:5]',
    },
    preprocessorOptions: {
      scss: {
        additionalData: '',
      },
    },
  },
  define: {
    // Prevent duplicate imports
    'global': 'globalThis',
    // WebSocket Configuration
    'process.env.VITE_WS_BASE_URL': JSON.stringify(process.env.VITE_WS_BASE_URL),
    'process.env.WS_MAX_RECONNECT_ATTEMPTS': JSON.stringify(process.env.WS_MAX_RECONNECT_ATTEMPTS),
    'process.env.WS_RECONNECT_INTERVAL': JSON.stringify(process.env.WS_RECONNECT_INTERVAL),
    
    // Web3 Configuration
    'process.env.VITE_ALCHEMY_API_KEY': JSON.stringify(process.env.VITE_ALCHEMY_API_KEY),
    'process.env.VITE_INFURA_API_KEY': JSON.stringify(process.env.VITE_INFURA_API_KEY),
    'process.env.VITE_ETHEREUM_RPC_URL': JSON.stringify(process.env.VITE_ETHEREUM_RPC_URL),
    'process.env.VITE_ARBITRUM_RPC_URL': JSON.stringify(process.env.VITE_ARBITRUM_RPC_URL),
    'process.env.VITE_OPTIMISM_RPC_URL': JSON.stringify(process.env.VITE_OPTIMISM_RPC_URL),
    'process.env.VITE_POLYGON_RPC_URL': JSON.stringify(process.env.VITE_POLYGON_RPC_URL),
    
    // Wallet Addresses
    'process.env.VITE_METAMASK_WALLET_ADDRESS': JSON.stringify(process.env.VITE_METAMASK_WALLET_ADDRESS),
    'process.env.VITE_TALISMAN_DOT_WALLET_ADDRESS': JSON.stringify(process.env.VITE_TALISMAN_DOT_WALLET_ADDRESS),
    
    // Price Feed APIs
    'process.env.VITE_CHAINLINK_FEEDS_API_KEY': JSON.stringify(process.env.VITE_CHAINLINK_FEEDS_API_KEY),
    'process.env.VITE_COINGECKO_API_KEY': JSON.stringify(process.env.VITE_COINGECKO_API_KEY),
    
    // Environment Configuration
    'process.env.PYTHON_ENV': JSON.stringify(process.env.PYTHON_ENV),
    'process.env.PYTHON_LOG_LEVEL': JSON.stringify(process.env.PYTHON_LOG_LEVEL),
    
    // AI/ML Configuration
    'process.env.OPENAI_API_KEY': JSON.stringify(process.env.OPENAI_API_KEY),
    'process.env.HUGGINGFACE_API_KEY': JSON.stringify(process.env.HUGGINGFACE_API_KEY),
    'process.env.OPENROUTER_API_KEY': JSON.stringify(process.env.OPENROUTER_API_KEY),
    
    // Database Configuration
    'process.env.DB_HOST': JSON.stringify(process.env.DB_HOST),
    'process.env.DB_PORT': JSON.stringify(process.env.DB_PORT),
    'process.env.DB_NAME': JSON.stringify(process.env.DB_NAME),
    'process.env.DB_USER': JSON.stringify(process.env.DB_USER),
    'process.env.DB_PASSWORD': JSON.stringify(process.env.DB_PASSWORD),
    
    // Security Configuration
    'process.env.JWT_SECRET': JSON.stringify(process.env.JWT_SECRET),
    'process.env.ENCRYPTION_KEY': JSON.stringify(process.env.ENCRYPTION_KEY),
    
    // API Rate Limiting
    'process.env.RATE_LIMIT_REQUESTS': JSON.stringify(process.env.RATE_LIMIT_REQUESTS),
    'process.env.RATE_LIMIT_WINDOW_MS': JSON.stringify(process.env.RATE_LIMIT_WINDOW_MS),
    
    // Trading Configuration
    'process.env.MAX_SLIPPAGE_PERCENT': JSON.stringify(process.env.MAX_SLIPPAGE_PERCENT),
    'process.env.GAS_PRICE_MULTIPLIER': JSON.stringify(process.env.GAS_PRICE_MULTIPLIER),
    'process.env.PORTFOLIO_REBALANCE_THRESHOLD': JSON.stringify(process.env.PORTFOLIO_REBALANCE_THRESHOLD),
    
    // Monitoring
    'process.env.SENTRY_DSN': JSON.stringify(process.env.SENTRY_DSN)
  },
  server: {
    host: '0.0.0.0',
    port: 5001,  // Standard port for the frontend
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5002',  // Proxy to the backend API server
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:5002',    // Proxy to the backend WebSocket
        ws: true,
        changeOrigin: true,
        secure: false
      },
      '/binance': {
        target: 'https://api.binance.com',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/binance/, ''),
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
      }
    },
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '.replit.dev',
      '.spock.replit.dev'
    ],
    fs: {
      strict: false,
      allow: ['..']
    }
  },
  publicDir: 'public',
  build: {
    outDir: 'dist',
    sourcemap: true,
    assetsDir: 'assets',
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html')
      },
      external: ['lockdown-install'],
      output: {
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            // Put all vendor code in a single chunk to avoid circular dependencies
            return 'vendor';
          }
        }
      }
    },
    target: 'es2020'
  },
  optimizeDeps: {
    exclude: ['lockdown-install'],
    include: [
      'react',
      'react-dom',
      'ethers',
      '@web3-react/core',
      '@web3-react/injected-connector',
      'class-variance-authority',
      'clsx',
      'tailwind-merge',
    ],
    esbuildOptions: {
      define: {
        global: 'globalThis'
      },
      target: 'es2020',
      supported: { bigint: true }
    }
  }
});
