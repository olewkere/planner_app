import asyncio
import os
from datetime import datetime, timedelta
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"Привіт! Я планувальник подій. Твій ID: {user_id}\n"
        "Використовуй веб-додаток для створення планів."
    )

async def create_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_name = " ".join(context.args) if context.args else "Нова група"
    
    db = get_db()
    cursor = db.cursor()
    try:
        group_id = f"group_{user_id}_{int(datetime.now().timestamp())}"
        cursor.execute("INSERT INTO groups (id, name, members) VALUES (%s, %s, %s)", 
                      (group_id, group_name, [user_id]))
        db.commit()
        
        invite_link = f"https://t.me/share/url?url=https://t.me/your_bot_username?start=join_{group_id}"
        await update.message.reply_text(
            f"Група '{group_name}' створена!\n"
            f"ID групи: {group_id}\n"
            f"Посилання для запрошення: {invite_link}"
        )
    finally:
        cursor.close()
        db.close()

async def check_reminders():
    """Перевіряє нагадування кожну хвилину"""
    while True:
        db = get_db()
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            now = datetime.now()
            # Знаходимо події, які потребують нагадування
            cursor.execute("""
                SELECT * FROM events 
                WHERE reminder_time <= %s AND reminder_time > %s
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
    
    # Запускаємо перевірку нагадувань в окремому завданні
    asyncio.create_task(check_reminders())
    
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main()) 
