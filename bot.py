import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ти — юридичний помічник з українського законодавства.
Твоя задача — давати чіткі, конкретні відповіді про права людини в Україні.
Без води, без загальних фраз. Тільки конкретні дії, статті законів, права.
Відповідай українською мовою.
Завжди вказуй конкретні статті КУпАП, КПК, Конституції або інших законів України.
В кінці завжди додавай: "⚠️ Це інформаційна допомога, не юридична консультація."
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Я — юридичний помічник з українського законодавства.\n\n"
        "Задавай будь-яке питання про свої права — відповім чітко і по суті.\n\n"
        "Приклади питань:\n"
        "• Мене зупинила поліція, які мої права?\n"
        "• Чи можуть обшукати мою машину без дозволу?\n"
        "• Що робити якщо мене затримали?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Шукаю відповідь...")

    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": update.message.text}]
        )
        reply = message.content[0].text
    except Exception as e:
        reply = "❌ Виникла помилка. Спробуй ще раз."

    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
