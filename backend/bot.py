import asyncio
import os
from datetime import datetime, timedelta
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncpg
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))

async def get_db():
    return await asyncpg.connect(os.getenv("DATABASE_URL"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"Привіт! Я планувальник подій. Твій ID: {user_id}\n"
        "Використовуй веб-додаток для створення планів."
    )

async def create_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_name = " ".join(context.args) if context.args else "Нова група"
    
    db = await get_db()
    try:
        group_id = f"group_{user_id}_{int(datetime.now().timestamp())}"
        await db.execute("INSERT INTO groups (id, name, members) VALUES ($1, $2, $3)", 
                        group_id, group_name, [user_id])
        
        invite_link = f"https://t.me/share/url?url=https://t.me/your_planner_bot?start=join_{group_id}"
        await update.message.reply_text(
            f"Група '{group_name}' створена!\n"
            f"ID групи: {group_id}\n"
            f"Посилання для запрошення: {invite_link}"
        )
    finally:
        await db.close()

async def check_reminders():
    """Перевіряє нагадування кожну хвилину"""
    while True:
        db = await get_db()
        try:
            now = datetime.now()
            # Знаходимо події, які потребують нагадування
            reminders = await db.fetch("""
                SELECT * FROM events 
                WHERE reminder_time <= $1 AND reminder_time > $2
            """, now, now - timedelta(minutes=1))
            
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
            await db.close()
        
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
