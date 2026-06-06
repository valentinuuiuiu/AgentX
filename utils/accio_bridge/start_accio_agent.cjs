/**
 * Accio Headless Bridge for Rehoboam
 * 
 * This script initializes the Accio agent runtime without the Electron GUI.
 * It mocks the Electron environment and exposes the underlying Qwen agent
 * via a local MCP server or simple IPC.
 */

const path = require('path');
const fs = require('fs');

// Path to the extracted Accio application
const ACCIO_PATH = path.resolve(__dirname, '../../../accio_extracted/root/app_unpacked');
const ACCIO_ENTRY = path.join(ACCIO_PATH, 'out/main/index.js');

console.log(`[AccioBridge] Initializing from: ${ACCIO_ENTRY}`);

// --- Process Mocks ---
process.resourcesPath = path.join(ACCIO_PATH, 'resources');
process.versions.electron = '30.0.0'; // Typical version for recent Electron

// --- Electron Mocks with Debug Proxy ---
const appMockBase = {
    whenReady: () => Promise.resolve(),
    on: (event, callback) => {
        console.log(`[AccioBridge] App event registered: ${event}`);
    },
    getPath: (name) => {
        console.log(`[AccioBridge] app.getPath('${name}')`);
        const mockPath = path.join(__dirname, 'mock_data', name || 'unknown');
        if (!fs.existsSync(path.join(__dirname, 'mock_data'))) {
            fs.mkdirSync(path.join(__dirname, 'mock_data'), { recursive: true });
        }
        return mockPath;
    },
    setPath: (name, p) => { console.log(`[AccioBridge] app.setPath('${name}', '${p}')`); },
    isPackaged: true,
    getName: () => 'Accio',
    setName: (name) => { console.log(`[AccioBridge] app.setName('${name}')`); },
    getVersion: () => '0.6.7',
    getAppPath: () => ACCIO_PATH,
    isReady: () => true,
    commandLine: {
        appendSwitch: (s) => console.log(`[AccioBridge] app.commandLine.appendSwitch('${s}')`),
        appendArgument: (a) => console.log(`[AccioBridge] app.commandLine.appendArgument('${a}')`),
    },
    requestSingleInstanceLock: () => {
        console.log('[AccioBridge] app.requestSingleInstanceLock() -> true');
        return true;
    },
    exit: () => { console.log('[AccioBridge] app.exit() called'); },
    setAsDefaultProtocolClient: () => { console.log('[AccioBridge] app.setAsDefaultProtocolClient()'); },
    relaunch: () => { console.log('[AccioBridge] app.relaunch()'); },
    quit: () => { console.log('[AccioBridge] app.quit()'); },
    isDefaultProtocolClient: () => false,
    removeAsDefaultProtocolClient: () => {},
};

const appProxy = new Proxy(appMockBase, {
    get(target, prop) {
        if (!(prop in target)) {
            console.warn(`[AccioBridge] Missing app.${prop.toString()} access!`);
            return () => {};
        }
        return target[prop];
    }
});

const mockElectronBase = {
    app: appProxy,
    safeStorage: {
        isEncryptionAvailable: () => true,
        encryptString: (s) => Buffer.from(s),
        decryptString: (b) => b.toString(),
    },
    ipcMain: {
        on: (channel, callback) => { console.log(`[AccioBridge] ipcMain.on('${channel}')`); },
        handle: (channel, callback) => { console.log(`[AccioBridge] ipcMain.handle('${channel}')`); },
    },
    protocol: {
        registerSchemesAsPrivileged: () => { console.log('[AccioBridge] protocol.registerSchemesAsPrivileged()'); },
        handle: () => { console.log('[AccioBridge] protocol.handle()'); },
    },
    crashReporter: {
        start: () => { console.log('[AccioBridge] crashReporter.start()'); },
    },
    session: {
        defaultSession: {
            resolveProxy: () => Promise.resolve('DIRECT'),
        },
    },
    dialog: {
        showErrorBox: (title, content) => console.error(`[ElectronDialog] ${title}: ${content}`),
    },
    BrowserWindow: class {
        constructor() {
            console.log('[AccioBridge] BrowserWindow suppressed.');
        }
        loadURL() {}
        loadFile() {}
        on() {}
        webContents = {
            on: () => {},
            send: () => {},
            setWindowOpenHandler: () => {},
        };
        show() {}
        hide() {}
        close() {}
    },
    Menu: {
        setApplicationMenu: () => {},
        buildFromTemplate: () => ({}),
    },
    nativeTheme: {
        on: () => {},
    },
    powerMonitor: {
        on: (event, callback) => { console.log(`[AccioBridge] powerMonitor.on('${event}')`); },
        getSystemIdleState: () => 'active',
        getSystemIdleTime: () => 0,
        isOnBatteryPower: () => false,
    },
    net: {
        request: () => ({ on: () => {}, end: () => {} }),
        isOnline: () => true,
    },
    netChangeNotifier: {
        on: () => {},
        off: () => {},
    },
    screen: {
        getPrimaryDisplay: () => ({ bounds: { width: 1920, height: 1080 } }),
        getAllDisplays: () => [{ bounds: { width: 1920, height: 1080 } }],
    },
    clipboard: {
        readText: () => '',
        writeText: () => {},
    },
    globalShortcut: {
        register: () => {},
        unregister: () => {},
    },
    shell: {
        openExternal: () => Promise.resolve(),
        showItemInFolder: () => {},
    },
    Tray: class {
        constructor() {}
        setContextMenu() {}
        setToolTip() {}
        on() {}
    },
};

const mockElectron = new Proxy(mockElectronBase, {
    get(target, prop) {
        if (!(prop in target)) {
            console.warn(`[AccioBridge] Missing electron.${prop.toString()} access!`);
            return {};
        }
        return target[prop];
    }
});

// Insert mock into require cache
// We use a fake path for electron since it doesn't exist
const fakeElectronPath = 'electron';
require.cache[fakeElectronPath] = {
    id: fakeElectronPath,
    filename: fakeElectronPath,
    loaded: true,
    exports: mockElectron
};

// Override Module._load to return our mock when 'electron' is requested
const Module = require('module');
const originalLoad = Module._load;
Module._load = function(request, parent, isMain) {
    if (request === 'electron') {
        return mockElectron;
    }
    return originalLoad.apply(this, arguments);
};

// --- Patch Native Modules Path ---
// Ensure the x64 native modules we installed are prioritized
process.env.NODE_PATH = path.join(ACCIO_PATH, 'node_modules');
require('module').Module._initPaths();

// --- Start the Logic ---
try {
    // We attempt to require the main entry. 
    // This will likely trigger the agent initialization.
    console.log('[AccioBridge] Requiring Accio entry point...');
    const accio = require(ACCIO_ENTRY);
    
    // Accio likely exposes an internal API or starts an MCP server.
    // We will listen for MCP server initialization if possible.
    console.log('[AccioBridge] Accio logic loaded.');
    
    // Accio likely exposes an internal API or starts an MCP server.
    // We will listen for MCP server initialization if possible.
    console.log('[AccioBridge] Accio logic loaded.');
    
    // Try to find session info
    let activeUserId = '';
    try {
        if (accio.SecurityManager && accio.SecurityManager._instance) {
            console.log('[AccioBridge] SecurityManager._instance keys:', Object.keys(accio.SecurityManager._instance));
            // Check for common account ID methods
            const instance = accio.SecurityManager._instance;
            if (instance.getAccountId) activeUserId = instance.getAccountId();
            else if (instance.accountId) activeUserId = instance.accountId;
            else if (instance.userId) activeUserId = instance.userId;
            
            if (activeUserId) console.log('[AccioBridge] Active User ID:', activeUserId);
        }
    } catch (e) {
        console.error('[AccioBridge] Error probing session info:', e.message);
    }
    
    // --- Start a simple HTTP API to talk to Accio ---
    const http = require('http');
    const server = http.createServer(async (req, res) => {
        if (req.url === '/ask' && req.method === 'POST') {
            let body = '';
            req.on('data', chunk => { body += chunk.toString(); });
            req.on('end', async () => {
                try {
                    const data = JSON.parse(body);
                    console.log(`[AccioBridge] Received request: ${data.prompt}`);
                    
                    // Call Accio's internal API
                    // Note: We might need to initialize a session first, 
                    // but let's try the direct approach first.
                    if (accio.apiSendMessage) {
                        console.log('[AccioBridge] apiSendMessage details:', {
                            type: typeof accio.apiSendMessage,
                            source: accio.apiSendMessage.toString().slice(0, 1000)
                        });
                        
                        // Ensure we have a valid to_user_id
                        const userId = activeUserId || 'SYSTEM_REHOBOAM';
                        
                        const response = await accio.apiSendMessage({
                            message: data.prompt,
                            context: data.context || {},
                            to_user_id: userId,
                            from_user_id: 'REHOBOAM_USER'
                        });
                        res.writeHead(200, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify(response));
                    } else {
                        res.writeHead(500);
                        res.end('apiSendMessage not found');
                    }
                } catch (err) {
                    res.writeHead(500);
                    res.end(err.message);
                }
            });
        } else {
            res.writeHead(404);
            res.end();
        }
    });

    const PORT = 4567;
    server.listen(PORT, () => {
        console.log(`[AccioBridge] Headless API listening on http://localhost:${PORT}`);
    });
    
    // Keep the process alive
    setInterval(() => {}, 1000);

} catch (err) {
    console.error('[AccioBridge] Failed to load Accio logic:', err);
    process.exit(1);
}
