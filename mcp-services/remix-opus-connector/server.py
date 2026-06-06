import os
import json
import logging
import threading
import time
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("remix_opus_production")

app = Flask(__name__)

# --- CONFIGURATION ---
SESSION_DIR = os.path.expanduser("~/.remix_opus_session")
REMIX_URL = "https://remix.ethereum.org/"
# Adjust these based on the actual Remix UI elements
CHAT_ICON_SELECTOR = "div[title='Solidity Copilot'], .ai-chat-icon"
CHAT_INPUT_SELECTOR = "textarea[placeholder*='Ask Claude'], .remix-ai-chat-input"
RESPONSE_SELECTOR = ".remix-ai-chat-msg-assistant:last-child"

# --- GLOBAL BROWSER STATE ---
class BrowserManager:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.lock = threading.Lock()
        self.playwright = None

    def start(self):
        with self.lock:
            if not self.browser:
                logger.info("Starting production browser instance with persistent context...")
                self.playwright = sync_playwright().start()
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=SESSION_DIR,
                    headless=True, # Set to False if you want to watch the shift work
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                self.page = self.context.new_page()
                self.page.goto(REMIX_URL, wait_until="networkidle")
                logger.info("Remix IDE loaded and persistent session active.")

    def query(self, prompt):
        with self.lock:
            if not self.page:
                self.start()
            
            try:
                logger.info(f"Sending prompt to Opus 4.6: {prompt[:50]}...")
                
                # Ensure Chat panel is open
                if not self.page.is_visible(CHAT_INPUT_SELECTOR):
                    self.page.click(CHAT_ICON_SELECTOR)
                    self.page.wait_for_selector(CHAT_INPUT_SELECTOR)

                # Send query
                self.page.fill(CHAT_INPUT_SELECTOR, prompt)
                self.page.keyboard.press("Enter")
                
                # Wait for response (Opus can be slow, 60s timeout)
                logger.info("Waiting for Opus response...")
                self.page.wait_for_selector(RESPONSE_SELECTOR, timeout=60000)
                
                # Stability delay for streaming
                time.sleep(2) 
                
                content = self.page.inner_text(RESPONSE_SELECTOR)
                logger.info("Response retrieved successfully.")
                return content
            except Exception as e:
                logger.error(f"Browser Interaction Error: {e}")
                # Refresh page on failure to reset state
                self.page.reload()
                raise e

bm = BrowserManager()

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completion():
    try:
        data = request.json
        messages = data.get("messages", [])
        prompt = messages[-1]["content"] if messages else ""
        
        response_text = bm.query(prompt)
        
        return jsonify({
            "id": f"remix-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "claude-opus-4.6-remix",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop"
            }]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "browser_active": bm.page is not None,
        "session_dir": SESSION_DIR
    })

if __name__ == "__main__":
    # Pre-start the browser to minimize first-request latency
    threading.Thread(target=bm.start).start()
    
    port = int(os.environ.get("PORT", 3010))
    logger.info(f"Remix Opus Production Connector starting on port {port}")
    app.run(host='0.0.0.0', port=port, threaded=True)
