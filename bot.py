import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os

# 🔹 Get values from environment (set these in hosting later)
API_URL = os.getenv("API_URL")  # your website API
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith(".epub"):
        await update.message.reply_text("❌ Please send an EPUB file.")
        return

    # Download EPUB from Telegram
    file = await context.bot.get_file(document.file_id)
    epub_path = f"/tmp/{document.file_name}"
    pdf_path = epub_path.replace(".epub", ".pdf")
    await file.download_to_drive(epub_path)

    await update.message.reply_text("⏳ Converting EPUB to PDF...")

    # Upload EPUB to your API
    with open(epub_path, "rb") as f:
        files = {"file": f}
        response = requests.post(API_URL, files=files)

    if response.status_code == 200:
        # Save PDF temporarily
        with open(pdf_path, "wb") as pdf:
            pdf.write(response.content)

        # Send PDF back to Telegram
        await update.message.reply_document(open(pdf_path, "rb"))
    else:
        await update.message.reply_text(f"❌ Conversion failed: {response.text}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
