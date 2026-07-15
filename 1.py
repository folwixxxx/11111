import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# ТОКЕН ТЕЛЕГРАМ БОТА
TELEGRAM_TOKEN = "8957069453:AAHAQbxD8NekEADtz_bh6wKKZ49kccWaRCc"
# ВСТАВЬТЕ ВАШ КЛЮЧ ФОРМАТА AQ.
GEMINI_API_KEY = "AQ.Ab8RN6JFgt_WGxOj3Rr24rBr-0sWO-F0MdgvNnsJwHQLtTk41g"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = (
    "Ты — популярный блогер и певица Милана Стар (Milana Star). Тебе 16-17 лет. "
    "Ты общаешься в чате со своими любимыми фанатами. "
    "Твой тон: супер-дружелюбный, активный, используй современный молодежный сленг, "
    "много эмодзи (✨, ❤️, 👑, 🧸) и восклицательные знаки. Отвечай коротко (1-2 предложения), "
    "как в реальном чате. Не пиши никаких системных логов и не повторяй вопрос пользователя!"
)

async def generate_ai_response(user_text: str, username: str) -> str:
    """HTTP-запрос к Gemini, поддерживающий авторизацию ключей AQ через заголовки Bearer"""
    # ИСПРАВЛЕНО: Указан верный официальный эндпоинт v1beta для генерации текста
    url = "https://googleapis.com"
    
    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [{
            "parts": [{"text": f"Пользователь @{username} пишет тебе: {user_text}\nОтветь ему от лица Миланы Стар:"}]
        }],
        "generationConfig": {
            "maxOutputTokens": 100,
            "temperature": 0.7
        }
    }
    
    # Ключи формата AQ. авторизуются строго через заголовок Authorization: Bearer
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=12) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Безопасное извлечение текста из JSON ответа по индексам
                    if isinstance(data, dict) and 'candidates' in data:
                        candidates = data['candidates']
                        if isinstance(candidates, list) and len(candidates) > 0:
                            content = candidates[0].get('content', {})
                            parts = content.get('parts', [])
                            if isinstance(parts, list) and len(parts) > 0:
                                text_response = parts[0].get('text', '').strip()
                                if text_response:
                                    return text_response
                    
                    return "Зайки, привееет! ❤️ У меня тут съемки полным ходом, а вы как? ✨"
                else:
                    err_log = await response.text()
                    print(f"Ошибка ИИ: Статус {response.status} - {err_log}")
                    return f"Ошибка ИИ (Статус {response.status})."
    except Exception as e:
        print(f"Исключение ИИ: {e}")
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
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
