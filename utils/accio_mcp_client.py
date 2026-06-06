import aiohttp
import json
import asyncio

class AccioClient:
    def __init__(self, base_url="http://localhost:4567"):
        self.base_url = base_url

    async def ask_accio(self, prompt: str):
        """Sends a prompt to the Accio agent helper."""
        url = f"{self.base_url}/ask"
        payload = {"prompt": prompt}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        text = await response.text()
                        return {"error": f"Accio error {response.status}: {text}"}
        except Exception as e:
            return {"error": str(e)}

async def main():
    client = AccioClient()
    print("Asking Accio for help...")
    result = await client.ask_accio("Hello Accio, I am Rehoboam. Can you help me analyze the market impact of a trade?")
    print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
