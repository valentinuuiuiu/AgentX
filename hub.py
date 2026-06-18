import asyncio
import json
import logging
import websockets
import os
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - HUB - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AntigravityHub:
    def __init__(self, host=None, port=None):
        self.host = host or os.getenv('HUB_HOST', '0.0.0.0')
        self.port = int(port or os.getenv('HUB_PORT', 4444))
        self.clients = {}

    async def register(self, websocket):
        """Register a new client connection."""
        client_address = websocket.remote_address[0]
        self.clients[websocket] = {
            "address": client_address,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Client connected from {client_address}. Total clients: {len(self.clients)}")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"Received {msg_type} from {client_address}")

                    if msg_type == 'handshake':
                        response = {
                            "status": "established",
                            "identity": "Antigravity Hub 1.0",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "client_id": str(id(websocket))
                        }
                    else:
                        # Standard echo for other messages
                        response = {
                            "status": "received",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "echo": data
                        }

                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON from {client_address}")
                    await websocket.send(json.dumps({"error": "invalid_json"}))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed for {client_address}")
        except Exception as e:
            logger.error(f"Error handling hub message from {client_address}: {e}")
        finally:
            if websocket in self.clients:
                del self.clients[websocket]
            logger.info(f"Client removed. Remaining: {len(self.clients)}")

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
            # Keep the server running
            await asyncio.Future()

if __name__ == "__main__":
    hub = AntigravityHub()
    try:
        asyncio.run(hub.start())
    except KeyboardInterrupt:
        logger.info("Hub shutting down")
