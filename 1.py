import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.telegram import TelegramAPIServer
from openai import AsyncOpenAI
from aiohttp import web

TELEGRAM_TOKEN = "8957069453:AAELr_YP0y4QrlliwKSvv8OxZ5_qiwp58bQ"
OPENROUTER_API_KEY = "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"

# Зеркало Telegram (работает без блокировок за рубежом и в РФ)
local_server = TelegramAPIServer.from_base("https://vkrf.ru")
bot = Bot(token=TELEGRAM_TOKEN, server=local_server)
dp = Dispatcher()

# Зеркало OpenRouter для стабильности
ai_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://ru.net"  # <--- ИСПРАВЛЕНО
)

SYSTEM_PROMPT = (
    "Ты — популярный блогер и певица Милана Стар (Milana Star). Тебе 16-17 лет. "
    "Общаешься дружелюбно, используешь сленг, эмодзи (✨, ❤️, 👑) и отвечаешь коротко."
)

async def generate_ai_response(user_text: str, username: str) -> str:
    try:
        response = await ai_client.chat.completions.create(
            model="google/gemma-3-27b-it:free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Пользователь @{username} пишет тебе: {user_text}"}
            ],
            max_tokens=150
        )
        return response.choices.message.content
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        return "Ой, залагало что-то! ✨ Напишите позже! ❤️"

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

# --- Заглушка веб-сервера для Render.com ---
async def handle_ping(request):
    return web.Response(text="Бот Миланы работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000) # Render слушает этот порт по умолчанию
    await site.start()

async def main():
    await start_web_server() # Запускаем веб-порт для сервера
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
