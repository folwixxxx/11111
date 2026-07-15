import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# ТОКЕН ТЕЛЕГРАМ БОТА (Обязательно вставьте СВЕЖИЙ токен, который только что дал @BotFather)
TELEGRAM_TOKEN = "8957069453:AAHAQbxD8NekEADtz_bh6wKKZ49kccWaRCc"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Список готовых фраз Миланы Стар со сленгом и эмодзи
MILANA_RESPONSES = [
    "Зайки, привееет! ❤️ У меня тут съемки полным ходом, а вы как? ✨",
    "Оаоаоа, приветики! 🧸 Вы самые лучшие фанаты в мире, обожаю вас! 👑",
    "Привееет! ✨ Забежала в чатик на минутку между репетициями! ❤️ Трек скоро!",
    "Йоу, привет! 👑 Как дела, зайки? Что делаете? ✨",
    "Ой, треш, у меня столько дел сегодня, но вам всегда рада ответить! ❤️🧸",
    "Зайки, спасибо за актив! ✨ Вы просто топ, люблю каждого! ❤️",
    "Приветики! 🧸 Смотрите мои новые рилсы и шортсы, там пушка! 👑",
    "Вау, привееет! ✨ Ловите много-много любви от меня! ❤️❤️❤️"
]

async def generate_ai_response(user_text: str, username: str) -> str:
    """Полностью автономный ответ без внешних запросов и ключей"""
    # Выбираем случайную фразу и подставляем имя пользователя
    response = random.choice(MILANA_RESPONSES)
    if response.startswith("Зайки, привееет!"):
        return response
    return f"@{username}, {response}"

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
        # Имитируем реальное время набора текста
        await asyncio.sleep(1.5)
        
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
    # Сбрасываем старые вебхуки, убирая вечный Conflict в Telegram
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
