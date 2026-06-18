import asyncio
import json
import logging
import websockets
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - HUB - %(message)s')
logger = logging.getLogger(__name__)

class AntigravityHub:
    def __init__(self, host='0.0.0.0', port=4444):
        self.host = host
        self.port = port
        self.clients = set()

    async def register(self, websocket):
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        try:
            async for message in websocket:
                data = json.loads(message)
                logger.info(f"Received from client: {data}")
                # Echo or broadcast logic here
                response = {"status": "received", "timestamp": datetime.now().isoformat()}
                await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
        finally:
            self.clients.remove(websocket)

    async def start(self):
        logger.info(f"Starting Hub on ws://{self.host}:{self.port}")
        async with websockets.serve(self.register, self.host, self.port):
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    hub = AntigravityHub()
    asyncio.run(hub.start())
