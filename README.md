# Telegram Планувальник

Планувальник подій як Telegram Web App з ботом для нагадувань.

## Структура

- `backend/` - FastAPI сервер + Telegram бот
- `frontend/` - React Web App для Telegram

## Локальний запуск

1. Створіть бота в @BotFather
2. Створіть базу даних на neon.tech
3. Скопіюйте `env.example` в `.env` та заповніть змінні
4. Встановіть залежності:

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

5. Запуск:

```bash
# Backend
cd backend
python main.py

# Бот
python bot.py

# Frontend
cd frontend
npm start
```

## Розгортання на Render

### 1. Підготуйте репозиторій
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Створіть сервіси на Render

**Для API (Backend):**
1. Зайдіть на [render.com](https://render.com)
2. Натисніть "New +" → "Web Service"
3. Підключіть ваш GitHub репозиторій
4. Налаштування:
   - **Name:** `planner-api`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

**Для Frontend:**
1. "New +" → "Static Site"
2. Підключіть той же репозиторій
3. Налаштування:
   - **Name:** `planner-frontend`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/build`
   - **Plan:** Free

### 3. Налаштуйте змінні середовища

**В API сервісі додайте:**
- `DATABASE_URL` - URL вашої Neon.tech бази даних
- `BOT_TOKEN` - токен вашого Telegram бота

**В Frontend сервісі додайте:**
- `REACT_APP_API_URL` - URL вашого API сервісу (наприклад: `https://planner-api.onrender.com`)

### 4. Оновіть бота

В `backend/bot.py` замініть:
```python
invite_link = f"https://t.me/share/url?url=https://t.me/your_bot_username?start=join_{group_id}"
```

На:
```python
invite_link = f"https://t.me/share/url?url=https://t.me/YOUR_BOT_USERNAME?start=join_{group_id}"
```

### 5. Налаштуйте Web App URL

В @BotFather встановіть Web App URL:
```
https://planner-frontend.onrender.com
```

## Функції

- ✅ Створення подій з нагадуваннями
- ✅ Групи для спільного планування
- ✅ Автоматичні нагадування через бота
- ✅ Telegram Web App інтерфейс
- ✅ Без реєстрації (використовує Telegram ID) 