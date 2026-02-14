import os
import telebot
import gspread
import json
from google.oauth2.service_account import Credentials

# =========================
# Telegram Setup
# =========================

TOKEN = os.environ["BOT_TOKEN"]
bot = telebot.TeleBot(TOKEN)

# =========================
# Google Sheets Setup
# =========================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=scope
)

client = gspread.authorize(creds)

# Ganti dengan nama sheet kamu
sheet = client.open("FinanceBot").sheet1

# =========================
# Command Handler
# =========================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Bot aktif dan terhubung ke Google Sheet!")

from datetime import datetime

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        parts = message.text.split()

        nominal = parts[0]
        kategori = parts[1] if len(parts) > 1 else "-"
        catatan = " ".join(parts[2:]) if len(parts) > 2 else "-"

        tanggal = datetime.now().strftime("%d-%m-%Y")

        sheet.append_row([tanggal, nominal, kategori, catatan])

        bot.reply_to(message, "Data tersimpan dengan format kolom!")
    
    except Exception as e:
        bot.reply_to(message, f"Terjadi error: {e}")


# =========================
# Start Bot
# =========================

print("Bot started...")
bot.polling()
