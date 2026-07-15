import asyncio
from aiogram import Bot, Dispatcher, types
from aiohttp import web
# Импортируем официальный новый клиент от Google
from google import genai
from google.genai import types as genai_types

# ТОКЕНЫ И КЛЮЧИ
TELEGRAM_TOKEN = "8957069453:AAELr_YP0y4QrlliwKSvv8OxZ5_qiwp58bQ"
# ИСПРАВЛЕНО: Вставлен ваш новый ключ формата AQ.
GEMINI_API_KEY = "AQ.Ab8RN6JFgt_WGxOj3Rr24rBr-0sWO-F0MdgvNnsJwHQLtTk41g"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Инициализируем официальный клиент Gemini (он умеет работать с ключами AQ.)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "Ты — популярный блогер и певица Милана Стар (Milana Star). Тебе 16-17 лет. "
    "Ты общаешься в чате со своими любимыми фанатами. "
    "Твой тон: супер-дружелюбный, активный, используй современный молодежный сленг, "
    "много эмодзи (✨, ❤️, 👑, 🧸) и восклицательные знаки. Отвечай коротко (1-2 предложения), "
    "как в реальном чате. Не пиши никаких системных логов и не повторяй вопрос пользователя!"
)

async def generate_ai_response(user_text: str, username: str) -> str:
    """Запрос через официальный SDK Google GenAI (совместим с ключами AQ)"""
    try:
        # Запускаем синхронный вызов SDK в отдельном потоке, чтобы не блокировать асинхронный пуллинг ТГ
        response = await asyncio.to_thread(
            ai_client.models.generate_content,
            model='gemini-2.5-flash',
            contents=f"Пользователь @{username} пишет тебе: {user_text}\nОтветь ему от лица Миланы Стар:",
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=100,
                temperature=0.7
            )
        )
        
        if response.text:
            return response.text.strip()
        
        return "Зайки, привееет! ❤️ У меня тут съемки полным ходом, а вы как? ✨"
        
    except Exception as e:
        # Любые ошибки SDK теперь упадут сюда и будут видны в логах Render
        print(f"Ошибка при запросе к Gemini SDK: {e}")
        return "Ой, залагало что-то, зайки! ✨ Напишите позже! ❤️"

@dp.message()
async def handle_group_messages(message: types.Message):
    bot_info = await bot.get_me()
    bot_username = f"@{bot_info.username}"
    
    is_mentioned = (message.text and bot_username in message.text) or \
                   (message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id)

    if is_mentioned and message.text:
        clean_text = message.text.replace(bot_username, "").strip()
        user_name = message.from_user.username or message.from_user.first_name
        
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        await asyncio.sleep(1)
        
        reply_text = await generate_ai_response(clean_text, user_name)
        await message.reply(reply_text)

# --- Веб-сервер для прохождения проверки (Health Check) на Render ---
async def handle_ping(request):
    return web.Response(text="Бот Миланы работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000) 
    await site.start()

async def main():
    await start_web_server() 
    # Сброс вебхука принудительно решает проблему TelegramConflictError при перезапусках Render
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
