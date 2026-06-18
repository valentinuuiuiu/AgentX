import asyncio
import json
import logging
import websockets
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - HUB - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AntigravityHub:
    def __init__(self, host=None, port=None):
        self.host = host or os.getenv('HUB_HOST', '127.0.0.1')
        self.port = int(port or os.getenv('HUB_PORT', 4444))
        self.clients = set()

    async def register(self, websocket):
        """Register a new client connection."""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Received from client: {data.get('type', 'unknown')}")

                    # Echo response
                    response = {
                        "status": "received",
                        "timestamp": datetime.utcnow().isoformat(),
                        "echo": data
                    }
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON")
                    await websocket.send(json.dumps({"error": "invalid_json"}))
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed")
        except Exception as e:
            logger.error(f"Error handling hub message: {e}")
        finally:
            self.clients.remove(websocket)

    async def start(self):
        """Start the WebSocket hub."""
        logger.info(f"Starting Antigravity Hub on ws://{self.host}:{self.port}")
        # Secure the server with message size limits
        async with websockets.serve(
            self.register,
            self.host,
            self.port,
            max_size=1024 * 1024,  # 1MB limit
            ping_interval=20,
            ping_timeout=20
        ):
            # Use a future that we never set to keep the server running
            await asyncio.Future()

if __name__ == "__main__":
    hub = AntigravityHub()
    try:
        asyncio.run(hub.start())
    except KeyboardInterrupt:
        logger.info("Hub shutting down")
