import os
import sys
import time
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
METAMASK_ID = "nkbihfbeogaeaoehlefnkodbefgpgknn"
EXTENSION_PATH = os.path.expanduser("~/snap/chromium/common/chromium/Default/Extensions/nkbihfbeogaeaoehlefnkodbefgpgknn/13.27.0_0")
USER_DATA_DIR = os.path.expanduser("~/.metamask_automation_session")

def connect_metamask():
    print(f"🚀 Starting Playwright with MetaMask from: {EXTENSION_PATH}")
    
    with sync_playwright() as p:
        # Launching persistent context with MetaMask extension
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,  # Extensions only work in headful mode
            args=[
                f"--disable-extensions-except={EXTENSION_PATH}",
                f"--load-extension={EXTENSION_PATH}",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # Give some time for MetaMask to load
        time.sleep(5)
        
        # Check for MetaMask setup page or extension popup
        # The extension home is: chrome-extension://{METAMASK_ID}/home.html
        metamask_page = context.new_page()
        metamask_url = f"chrome-extension://{METAMASK_ID}/home.html"
        metamask_page.goto(metamask_url)
        
        print(f"🌐 MetaMask Home loaded: {metamask_url}")
        print("💡 TIP: If this is a fresh session, you need to import your wallet.")
        
        # Also open Remix for connection
        remix_page = context.new_page()
        remix_page.goto("https://remix.ethereum.org/")
        print("🌐 Remix IDE loaded.")
        
        print("\n⚡ SYSTEM STANDBY ⚡")
        print("Please complete the MetaMask login/import in the browser window.")
        print("Rehoboam agents will then be able to use this session for on-chain shifts.")
        
        # Keep the session alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down connector...")
            context.close()

if __name__ == "__main__":
    if not os.path.exists(EXTENSION_PATH):
        print(f"❌ Error: MetaMask extension not found at {EXTENSION_PATH}")
        sys.exit(1)
    
    connect_metamask()
