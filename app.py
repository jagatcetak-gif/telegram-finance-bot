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

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    sheet.append_row([message.text])
    bot.reply_to(message, "Data tersimpan ke Google Sheet!")

# =========================
# Start Bot
# =========================

print("Bot started...")
bot.polling()
