import os
import json
import re
from datetime import datetime

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import A4


# =========================
# ENV VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "FinanceBot")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN belum di-set")

if not GOOGLE_CREDENTIALS:
    raise Exception("GOOGLE_CREDENTIALS belum di-set")


# =========================
# GOOGLE SHEETS CONNECT
# =========================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds_dict = json.loads(GOOGLE_CREDENTIALS)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    scope
)

client = gspread.authorize(creds)

sheet = client.open(SPREADSHEET_NAME).sheet1


# =========================
# AUTO CATEGORY
# =========================

categories = {
    "Makan": ["makan", "bakso", "ayam", "nasi", "kopi"],
    "Transport": ["bensin", "grab", "gojek", "tol"],
    "Belanja": ["belanja", "alfamart", "indomaret", "market"],
    "Tagihan": ["listrik", "air", "wifi", "internet"],
    "Hiburan": ["game", "bioskop", "netflix"],
    "Kesehatan": ["obat", "dokter", "rs"],
    "Pendidikan": ["buku", "kursus", "belajar"],
    "Lainnya": []
}


def detect_category(text):

    text = text.lower()

    for cat, keys in categories.items():
        for k in keys:
            if k in text:
                return cat

    return "Lainnya"


# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "💰 Finance Bot PRO aktif\n\n"
        "Format input:\n"
        "50000 makan bakso\n\n"
        "Command:\n"
        "/summary\n"
        "/report"
    )


# =========================
# HANDLE MESSAGE
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    match = re.match(r"([\d\.]+)\s(.+)", text)

    if not match:
        await update.message.reply_text(
            "Format salah\nContoh:\n50000 makan bakso"
        )
        return

    amount = int(match.group(1).replace(".", ""))
    desc = match.group(2)

    category = detect_category(desc)

    date = datetime.now().strftime("%Y-%m-%d")

    sheet.append_row([
        date,
        desc,
        amount,
        category
    ])

    await update.message.reply_text(
        f"✅ Tersimpan\n"
        f"{desc}\n"
        f"Rp {amount}\n"
        f"Kategori: {category}"
    )


# =========================
# SUMMARY BULANAN
# =========================

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    if df.empty:
        await update.message.reply_text("Belum ada data")
        return

    if "Tanggal" not in df.columns:
        await update.message.reply_text("Format spreadsheet salah")
        return

    df["Tanggal"] = pd.to_datetime(df["Tanggal"])

    now = datetime.now()

    df = df[
        (df["Tanggal"].dt.month == now.month) &
        (df["Tanggal"].dt.year == now.year)
    ]

    if df.empty:
        await update.message.reply_text("Belum ada data bulan ini")
        return

    result = df.groupby("Kategori")["Jumlah"].sum()

    text = "📊 Summary bulan ini\n\n"

    total = 0

    for cat, val in result.items():

        text += f"{cat}: Rp {int(val)}\n"
        total += val

    text += f"\nTOTAL: Rp {int(total)}"

    await update.message.reply_text(text)


# =========================
# GENERATE PDF
# =========================

def generate_report():

    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    if df.empty:
        return None

    df["Tanggal"] = pd.to_datetime(df["Tanggal"])

    now = datetime.now()

    df = df[
        (df["Tanggal"].dt.month == now.month) &
        (df["Tanggal"].dt.year == now.year)
    ]

    if df.empty:
        return None

    summary = df.groupby("Kategori")["Jumlah"].sum().reset_index()

    table_data = [["Kategori", "Total"]]

    for _, row in summary.iterrows():

        table_data.append([
            row["Kategori"],
            int(row["Jumlah"])
        ])

    filename = "report.pdf"

    pdf = SimpleDocTemplate(filename, pagesize=A4)

    table = Table(table_data)

    pdf.build([table])

    return filename


# =========================
# REPORT COMMAND
# =========================

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file = generate_report()

    if not file:
        await update.message.reply_text("Belum ada data bulan ini")
        return

    with open(file, "rb") as f:

        await update.message.reply_document(
            document=f
        )


# =========================
# MAIN
# =========================

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("report", report))

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

print("Bot started")

app.run_polling()
