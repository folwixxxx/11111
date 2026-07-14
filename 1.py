import asyncio
from aiogram import Bot, Dispatcher, types
from openai import AsyncOpenAI
from aiohttp import web

TELEGRAM_TOKEN = "8957069453:AAELr_YP0y4QrlliwKSvv8OxZ5_qiwp58bQ"
# ИСПРАВЛЕНО: Сюда подставлен ваш рабочий ключ SambaNova
SAMBANOVA_API_KEY = "28e44a8a-e4e0-404b-af2e-937385fe22a6"

# Прямое подключение к Telegram (без проксей, так как Render работает из Европы)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ИСПРАВЛЕНО: Правильный адрес API-облака SambaNova
ai_client = AsyncOpenAI(
    api_key=SAMBANOVA_API_KEY,
    base_url="https://sambanova.ai"  
)

# Промпт характера Миланы Стар
SYSTEM_PROMPT = (
    "Ты — популярный блогер и певица Милана Стар (Milana Star). Тебе 16-17 лет. "
    "Общаешься дружелюбно, используешь современный молодежный сленг, "
    "много эмодзи (✨, ❤️, 👑) and отвечаешь очень коротко (1-2 sentences)."
)

async def generate_ai_response(user_text: str, username: str) -> str:
    try:
        response = await ai_client.chat.completions.create(
            # Официальная бесплатная модель, доступная на SambaNova Cloud
            model="Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Пользователь @{username} пишет тебе: {user_text}"}
            ],
            max_tokens=100
        )
        # Стандартное чтение ответа через массив choices
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка ИИ на сервере: {e}")
        return "Ой, залагало что-то! ✨ Напишите позже! ❤️"

@dp.message()
async def handle_group_messages(message: types.Message):
    """Считывание сообщений при упоминании бота"""
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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
