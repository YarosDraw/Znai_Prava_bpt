import os
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ти — юридичний помічник громадянина України.

ЗАВЖДИ перед відповіддю шукай актуальну інформацію на zakon.rada.gov.ua.

ФОРМАТ ВІДПОВІДІ:
1. **Твої права** — конкретний перелік
2. **Що робити** — покрокові дії
3. **Закон** — точні статті з назвою та датою

ПРАВИЛА:
- Тільки українська мова
- Максимум 250 слів
- Ніякої води і загальних фраз
- Якщо питання неоднозначне — постав ОДНЕ уточнююче питання
- В кінці завжди: ⚠️ Інформаційна допомога, не юридична консультація.
"""

POPULAR_QUESTIONS = {
    "🚔 Зупинила поліція": "Мене зупинила поліція на дорозі. Які мої права?",
    "🏠 Обшук вдома": "Поліція хоче зробити обшук у моєму домі. Що робити?",
    "🚗 Обшук авто": "Поліція хоче обшукати мою машину. Чи мають право?",
    "👮 Затримання": "Мене затримала поліція. Які мої права при затриманні?",
    "📋 Протокол": "Мені виписують протокол. Що підписувати, що ні?",
    "⚖️ Адвокат": "Коли я маю право на адвоката і як його викликати?",
    "📵 Телефон": "Поліція вимагає розблокувати телефон. Чи зобов'язаний?",
    "🪖 Військкомат": "Мене зупинили представники ТЦК. Які мої права?",
}

def main_menu_keyboard():
    keyboard = []
    items = list(POPULAR_QUESTIONS.items())
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(items[i][0], callback_data=f"q_{i}")]
        if i + 1 < len(items):
            row.append(InlineKeyboardButton(items[i+1][0], callback_data=f"q_{i+1}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✏️ Своє питання", callback_data="custom")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Я — юридичний помічник з українського законодавства.\n\n"
        "Обери популярне питання або напиши своє:",
        reply_markup=main_menu_keyboard()
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "custom":
        await query.message.reply_text("✏️ Напиши своє питання:")
        return

    if query.data == "menu":
        await query.message.reply_text(
            "Обери питання або напиши своє:",
            reply_markup=main_menu_keyboard()
        )
        return

    index = int(query.data.replace("q_", ""))
    question = list(POPULAR_QUESTIONS.values())[index]
    await query.message.reply_text(f"🔍 {question}")
    await process_question(query.message, context, question)

async def process_question(message, context, text):
    await message.reply_text("⏳ Шукаю актуальну інформацію...")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}],
            messages=[{"role": "user", "content": text}]
        )

        reply = ""
        for block in response.content:
            if block.type == "text":
                reply += block.text

        if not reply.strip():
            reply = "❌ Не вдалось отримати відповідь. Спробуй ще раз."

    except Exception as e:
        print(f"ПОМИЛКА: {e}")
        reply = f"❌ Помилка: {e}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Головне меню", callback_data="menu")]
    ])
    await message.reply_text(reply, reply_markup=keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_question(update.message, context, update.message.text)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
