import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 🔹 Put your tokens here
TELEGRAM_TOKEN = "8476699783:AAEaJDsDyXSLtYG95Wa2sW5eWd6x748ZgvE"
CLOUDCONVERT_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiMDRkNDdlYjUzNmVkOGZiNmZmNDE1NzdlNjQ1NjI4Yjc1MmU1ZjRmNWM5MDM1Mjk0MGRiMzliNzZiNzBmYTIzOTg3YTNhODQ4MjMyZGUxNDQiLCJpYXQiOjE3NTY3ODI0MDIuMzE1MTg2LCJuYmYiOjE3NTY3ODI0MDIuMzE1MTg3LCJleHAiOjQ5MTI0NTYwMDIuMzEwODM3LCJzdWIiOiI3MjgwMjY4OCIsInNjb3BlcyI6WyJ1c2VyLnJlYWQiLCJwcmVzZXQud3JpdGUiLCJwcmVzZXQucmVhZCIsInRhc2sud3JpdGUiLCJ1c2VyLndyaXRlIiwidGFzay5yZWFkIiwid2ViaG9vay53cml0ZSIsIndlYmhvb2sucmVhZCJdfQ.K-3KXEcWFBVyY9tv7z3JA6xsRH0U1_7DmBbBtAkary3Id1o14ygf9yMNRQXbyZIi5MW63DYPJXUiZGLbDwainFK4j2TJAkMjCL5AZkI5ITy2v0uKuFucxhKU1wOBV780wL7d-TcRa5lzC17wOODzK3nFerjphcOKDGegr695epEHgM1K48h3SkJcoFsOIvtIMXMSV__7g_6DQEwL475W1UJUqioBd2vICHMTirmktt2IfEFCjf9uqzgfFECdF9gkbrLxX3mhizoFP2Zeorrg8fK6cGT-OIgngAV7BnjVkukJccbKPW0YMoRsn0TJWwYb7_s1wjkt3QWYZKBaNKwrGNqmOR5qs7ps8w2Kkg6N3QJY6Vc551cjR6EGZpei6kB8moGkMOO8v9ORdW5FEZ8URo38GAXF1fUG9V1d2XruqgWNVO7XdtXd9l_3F0BmI7HWKEPSDnnrQPLCTvKyNus3wghKyS3NgM-lGMNiRQYDJksYHf3hcwekhS9gMY0SYp2zyoAaP32GCUpOV-BqmgkjEHs8rJf3f75LhJ41vPndN4i_moYO5KWT-71btnCDqOjHBFdBYMYJ9HZBG2zYOSLT9XgXS4oW_DphhVd3l26hDzg12rIbq54GjabM8uiFifCUHbLA5wmjuQDNHMBBbEU2DENHaxGQoaDHd_R6jBunx9s
"

# ==================
# Start command
# ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 Send me an EPUB file and I will convert it to PDF!")

# ==================
# Handle EPUB upload
# ==================
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_path = "input.epub"
    await file.download_to_drive(file_path)

    await update.message.reply_text("⏳ Converting your EPUB to PDF...")

    # Step 1: Create job
    job_payload = {
        "tasks": {
            "import": {"operation": "import/upload"},
            "convert": {
                "operation": "convert",
                "input": "import",
                "input_format": "epub",
                "output_format": "pdf"
            },
            "export": {"operation": "export/url", "input": "convert"}
        }
    }

    headers = {"Authorization": f"Bearer {CLOUDCONVERT_API_KEY}"}
    job = requests.post("https://api.cloudconvert.com/v2/jobs", json=job_payload, headers=headers).json()
    upload_url = job["data"]["tasks"][0]["result"]["form"]["url"]
    upload_params = job["data"]["tasks"][0]["result"]["form"]["parameters"]

    # Step 2: Upload EPUB file
    with open(file_path, "rb") as f:
        files = {"file": f}
        requests.post(upload_url, data=upload_params, files=files)

    # Step 3: Wait for conversion result
    job_id = job["data"]["id"]
    while True:
        job_status = requests.get(f"https://api.cloudconvert.com/v2/jobs/{job_id}", headers=headers).json()
        if job_status["data"]["status"] == "finished":
            break

    # Step 4: Download PDF
    export_task = [t for t in job_status["data"]["tasks"] if t["name"] == "export"][0]
    file_url = export_task["result"]["files"][0]["url"]
    output_path = "output.pdf"
    pdf_data = requests.get(file_url).content
    with open(output_path, "wb") as f:
        f.write(pdf_data)

    # Step 5: Send back PDF
    await update.message.reply_document(document=open(output_path, "rb"), filename="converted.pdf")
    await update.message.reply_text("✅ Done! Here’s your PDF.")

# ==================
# Main
# ==================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.MimeType("application/epub+zip"), handle_file))
    app.run_polling()

if __name__ == "__main__":
    main()
