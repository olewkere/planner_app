import asyncio
import os
from datetime import datetime, timedelta
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import sqlite3
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))

def get_db():
    try:
        db = sqlite3.connect('planner.db')
        db.row_factory = sqlite3.Row
        return db
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"Привіт! Я планувальник подій. Твій ID: {user_id}\n"
        "Використовуй веб-додаток для створення планів.\n\n"
        "Команди:\n"
        "/creategroup - створити групу\n"
        "/mygroups - показати мої групи\n"
        "/myevents - показати мої події"
    )

async def create_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_name = " ".join(context.args) if context.args else "Нова група"

    db = get_db()
    if not db:
        await update.message.reply_text("Помилка підключення до бази даних.")
        return

    cursor = db.cursor()
    try:
        group_id = f"group_{user_id}_{int(datetime.now().timestamp())}"
        cursor.execute("INSERT INTO groups (id, name, members, owner_id) VALUES (?, ?, ?, ?)", 
                      (group_id, group_name, str([user_id]), user_id))
        db.commit()

        invite_link = f"https://t.me/share/url?url=https://t.me/your_planner_bot?start=join_{group_id}"
        await update.message.reply_text(
            f"Група '{group_name}' створена!\n"
            f"ID групи: {group_id}\n"
            f"Посилання для запрошення: {invite_link}\n\n"
            "Надішли це посилання друзям, щоб вони приєдналися до групи!"
        )
    finally:
        cursor.close()
        db.close()

async def my_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    db = get_db()
    if not db:
        await update.message.reply_text("Помилка підключення до бази даних.")
        return

    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM groups WHERE owner_id = ? OR ? IN (SELECT json_extract(members, '$') FROM groups)", 
                      (user_id, user_id))
        groups = cursor.fetchall()
        
        if not groups:
            await update.message.reply_text("У вас немає груп.")
            return
        
        message = "Ваші групи:\n\n"
        for group in groups:
            members = JSON.parse(group['members'] || '[]')
            member_count = len(members)
            message += f"📁 {group['name']}\n"
            message += f"ID: {group['id']}\n"
            message += f"Учасників: {member_count}\n"
            message += f"Створена: {group['created_at']}\n\n"
        
        await update.message.reply_text(message)
    finally:
        cursor.close()
        db.close()

async def my_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    db = get_db()
    if not db:
        await update.message.reply_text("Помилка підключення до бази даних.")
        return

    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM events WHERE user_id = ? ORDER BY event_time", (user_id,))
        events = cursor.fetchall()
        
        if not events:
            await update.message.reply_text("У вас немає подій.")
            return
        
        message = "Ваші події:\n\n"
        for event in events:
            event_time = datetime.fromisoformat(event['event_time'])
            reminder_time = datetime.fromisoformat(event['reminder_time'])
            
            message += f"📅 {event['title']}\n"
            if event['description']:
                message += f"Опис: {event['description']}\n"
            message += f"Час: {event_time.strftime('%d.%m.%Y %H:%M')}\n"
            message += f"Нагадування: {reminder_time.strftime('%d.%m.%Y %H:%M')}\n"
            if event['group_id']:
                message += f"Група: {event['group_id']}\n"
            message += "\n"
        
        await update.message.reply_text(message)
    finally:
        cursor.close()
        db.close()

async def check_reminders():
    """Перевіряє нагадування кожну хвилину"""
    while True:
        db = get_db()
        if not db:
            print("Warning: Could not connect to database for reminders.")
            await asyncio.sleep(60)
            continue

        cursor = db.cursor()
        try:
            now = datetime.now()
            # Знаходимо події, які потребують нагадування
            cursor.execute("""
                SELECT * FROM events
                WHERE reminder_time <= ? AND reminder_time > ?
            """, (now, now - timedelta(minutes=1)))

            reminders = cursor.fetchall()

            for reminder in reminders:
                message = f"🔔 Нагадування!\n\n"
                message += f"Подія: {reminder['title']}\n"
                if reminder['description']:
                    message += f"Опис: {reminder['description']}\n"
                message += f"Час: {reminder['event_time']}\n"

                if reminder['group_id']:
                    message += f"Група: {reminder['group_id']}"

                await bot.send_message(chat_id=reminder['user_id'], text=message)

        finally:
            cursor.close()
            db.close()

        await asyncio.sleep(60)  # Перевіряємо кожну хвилину

async def main():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("creategroup", create_group))
    application.add_handler(CommandHandler("mygroups", my_groups))
    application.add_handler(CommandHandler("myevents", my_events))

    # Запускаємо перевірку нагадувань в окремому завданні
    asyncio.create_task(check_reminders())

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main()) 
