import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiohttp import web

TELEGRAM_TOKEN = "8957069453:AAELr_YP0y4QrlliwKSvv8OxZ5_qiwp58bQ"
# Твой проверенный ключ API от Google Gemini
GEMINI_API_KEY = "AQ.Ab8RN6KGQidkl5miYRWMC9Qx9U_D3Xi3X5DWXj8lmPU3PszI4w"

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
    """Функция запроса к Google Gemini API через твой ключ"""
    # ИСПРАВЛЕНО: Ссылка собрана строго по официальной документации Google Cloud
    url = f"https://googleapis.com{GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"{SYSTEM_PROMPT}\n\nПользователь @{username} пишет тебе: {user_text}\nОтветь ему от лица Миланы Стар:"
            }]
        }],
        "generationConfig": {
            "maxOutputTokens": 100,
            "temperature": 0.7
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # ИСПРАВЛЕНО: Точный и безопасный путь до сгенерированного текста
                    reply = data['candidates'][0]['content']['parts'][0]['text']
                    return reply.strip()
                else:
                    print(f"Ошибка Gemini API: Статус {response.status}")
                    return "Зайки, привееет! ❤️ У меня тут съемки полным ходом, а вы как? ✨"
    except Exception as e:
        print(f"Исключение при запросе к ИИ: {e}")
        return "Ой, залагало что-то, зайки! ✨ Напишите позже! "

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

# --- Веб-сервер для удержания Render.com в активном состоянии ---
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
