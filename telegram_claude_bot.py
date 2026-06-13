import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

# --- Config (set these as environment variables) ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# --- Setup ---
logging.basicConfig(level=logging.INFO)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Store conversation history per user
conversations = {}

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm Claude, your AI assistant.\n"
        "Just send me a message and I'll reply!\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/clear - Clear conversation history"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversations[user_id] = []
    await update.message.reply_text("🗑️ Conversation history cleared!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Initialize history for new users
    if user_id not in conversations:
        conversations[user_id] = []

    # Add user message to history
    conversations[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Keep last 20 messages to avoid token limits
    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        # Call Claude API
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="You are a helpful AI assistant called Claude, made by Anthropic. Be concise and friendly.",
            messages=conversations[user_id]
        )

        assistant_reply = response.content[0].text

        # Add Claude's reply to history
        conversations[user_id].append({
            "role": "assistant",
            "content": assistant_reply
        })

        await update.message.reply_text(assistant_reply)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text(
            "⚠️ Something went wrong. Please try again."
        )

# --- Main ---
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
