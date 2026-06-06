#!/usr/bin/env python3
"""Simple script to get chat ID from bot updates"""
import asyncio
from telegram import Bot

TOKEN = "8337308834:AAGR2TKJLDbDTft6Q2M_7o9jf8tcpMESAx0"

async def main():
    bot = Bot(TOKEN)
    
    # Get updates
    updates = await bot.get_updates(limit=10)
    print(f"Found {len(updates)} updates")
    
    for update in updates:
        print(f"Update: {update.to_dict()}")
        if update.message:
            chat_id = update.message.chat.id
            username = update.message.from_user.username
            text = update.message.text
            print(f"\n✅ Chat ID: {chat_id}")
            print(f"From: @{username}")
            print(f"Text: {text}")
            
            # Send confirmation
            await bot.send_message(
                chat_id=chat_id,
                text="✅ Hermes received your message!\n\nChat ID captured. Rehoboam Signals is now configured for you."
            )
            return chat_id
    
    return None

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print(f"\n🎯 Your Chat ID: {result}")
        print("Add this to .env as: ADMIN_CHAT_ID=" + str(result))
    else:
        print("\n❌ No messages found. Send a message to @web4_bot_nobot first!")
