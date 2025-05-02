import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
from dotenv import load_dotenv

# Загрузка переменных из .env файла (например, для токена)
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Подключение к базе данных
conn = sqlite3.connect("referrals.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referred_by INTEGER,
    points INTEGER DEFAULT 0,
    name TEXT
)
""")
conn.commit()

# Функция ранга
def get_rank(points):
    if points >= 20:
        return "🌟 Легенда"
    elif points >= 10:
        return "🔥 Лидер"
    elif points >= 5:
        return "🚀 Активист"
    else:
        return "👶 Новичок"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    name = user.full_name
    args = context.args
    referrer = int(args[0]) if args else None

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (user_id, referred_by, points, name) VALUES (?, ?, ?, ?)",
            (user_id, referrer, 0, name)
        )
        if referrer:
            cursor.execute(
                "UPDATE users SET points = points + 1 WHERE user_id = ?",
                (referrer,)
            )
        conn.commit()

    ref_link = f"https://t.me/XP_STARS_bot?start={user_id}"
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    points_result = cursor.fetchone()
    points = points_result[0] if points_result else 0
    rank = get_rank(points)

    keyboard = [
        [InlineKeyboardButton("👤 Профиль", callback_data='profile')],
        [InlineKeyboardButton("👥 Приглашённые", callback_data='myrefs')],
        [InlineKeyboardButton("🏆 Топ", callback_data='top')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"⭐️ Добро пожаловать в XP STARS, {name}!\n\n"
        f"🔗 Твоя реферальная ссылка:\n{ref_link}\n\n"
        f"🎖️ Твой ранг: {rank}"
    )

    with open('banner.jpg', 'rb') as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=caption,
            reply_markup=reply_markup
        )

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — начать\n"
        "/profile — профиль\n"
        "/myrefs — приглашённые\n"
        "/top — топ\n"
        "/about — о боте"
    )

# /profile
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    name = user.full_name
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    points = result[0] if result else 0
    rank = get_rank(points)
    msg = f"👤 Профиль: {name}\n🏅 Баллы: {points}\n🎖️ Ранг: {rank}"
    if update.callback_query:
        await update.callback_query.message.reply_text(msg)
    else:
        await update.message.reply_text(msg)

# /myrefs
async def myrefs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,))
    count = cursor.fetchone()[0]
    msg = f"👥 Ты пригласил {count} человек(а)."
    if update.callback_query:
        await update.callback_query.message.reply_text(msg)
    else:
        await update.message.reply_text(msg)

# /top
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 5")
    rows = cursor.fetchall()
    msg = "🏆 Топ-5 пользователей:\n"
    for i, (name, pts) in enumerate(rows, start=1):
        rank = get_rank(pts)
        msg += f"{i}. {name} — {pts} баллов ({rank})\n"

    if update.callback_query:
        await update.callback_query.message.reply_text(msg)
    else:
        await update.message.reply_text(msg)

# /about
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "XP STARS — бот с реферальной системой.\n"
        "Приглашай друзей, получай баллы и поднимайся в топ!"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(text)
    else:
        await update.message.reply_text(text)

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'profile':
        await profile(update, context)
    elif data == 'myrefs':
        await myrefs(update, context)
    elif data == 'top':
        await top(update, context)

# Запуск
def main():
    app = Application.builder().token(TOKEN).build()  # Используем токен из .env
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("myrefs", myrefs))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("XP_STARS_bot запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
