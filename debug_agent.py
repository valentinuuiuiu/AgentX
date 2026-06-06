#!/usr/bin/env python3
"""
🧪 DEBUG AGENT CONNECTION 🧪
Test agent connection and message handling.
"""

import asyncio
import json

async def debug_agent_connection():
    """Debug connection to agent."""
    print("Testing connection to agent on port 10000...")

    try:
        # Connect to agent
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", 10000),
            timeout=5
        )
        print("✅ Connected to agent")

        # Send task assignment
        task = {
            "type": "task_assign",
            "task": {
                "id": "debug_test_1",
                "guna": "sattva",
                "command": "echo 'debug test successful'",
                "description": "Debug connection test"
            }
        }

        print(f"📤 Sending: {json.dumps(task)}")
        writer.write(json.dumps(task).encode() + b"\n")
        await writer.drain()

        # Wait for response
        print("⏳ Waiting for response...")
        response_data = await asyncio.wait_for(reader.readline(), timeout=10)
        response = json.loads(response_data.decode())
        print(f"📥 Received: {response}")

        writer.close()
        await writer.wait_closed()
        print("✅ Connection closed")

    except asyncio.TimeoutError:
        print("❌ Timeout waiting for response")
    except ConnectionRefusedError:
        print("❌ Connection refused")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_agent_connection())