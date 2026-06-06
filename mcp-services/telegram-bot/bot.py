import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I\'m Hermes' bot. Use /help for commands.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/invite - create an invite link\n/announce <text> - post announcement\n/kick <user_id> - ban user\n/get_chat_id - show this chat id"
    )

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat id: {update.effective_chat.id}")

async def create_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        link = await context.bot.create_chat_invite_link(chat_id=chat_id)
        await update.message.reply_text(f"Invite link: {link.invite_link}")
    except Exception as e:
        await update.message.reply_text(f"Failed to create invite link: {e}")

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /announce your message")
        return
    text = " ".join(context.args)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    await update.message.reply_text("Announcement sent.")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /kick <user_id>")
        return
    try:
        user_id = int(context.args[0])
        await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=user_id)
        await update.message.reply_text(f"User {user_id} banned.")
    except Exception as e:
        await update.message.reply_text(f"Failed to ban user: {e}")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable is required.")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("get_chat_id", get_chat_id))
    app.add_handler(CommandHandler("invite", create_invite))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CommandHandler("kick", kick))

    print("Starting Telegram bot (polling)")
    app.run_polling()

if __name__ == "__main__":
    main()
