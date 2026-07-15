import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# ТОКЕН ТЕЛЕГРАМ БОТА (Если снова будет ошибка Conflict, обновите его в @BotFather)
TELEGRAM_TOKEN = "8957069453:AAELr_YP0y4QrlliwKSvv8OxZ5_qiwp58bQ"

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
    """Запрос к бесплатному ИИ через провайдер DuckDuckGo (Ключи не нужны)"""
    init_url = "https://duckduckgo.com"
    chat_url = "https://duckduckgo.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
        "x-vqd-accept": "1"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Шаг 1: Получаем обязательный внутренний токен сессии (VQD)
            async with session.get(init_url, headers=headers) as init_resp:
                if init_resp.status != 200:
                    return "Зайки, привееет! ❤️ У меня тут съемки полным ходом, а вы как? ✨"
                vqd = init_resp.headers.get("x-vqd-4", "")
            
            # Шаг 2: Отправляем запрос в нейросеть (Llama 3)
            headers["x-vqd-4"] = vqd
            payload = {
                "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                "messages": [
                    {"role": "user", "content": f"ИНСТРУКЦИЯ ДЛЯ РОЛИ: {SYSTEM_PROMPT}\n\nПользователь @{username} пишет тебе: {user_text}\nОтветь ему строго по инструкции:"}
                ]
            }
            
            async with session.post(chat_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    raw_text = await response.text()
                    lines = raw_text.split("\n")
                    full_reply = ""
                    
                    # Разбираем потоковый Event-Stream ответ от DuckDuckGo
                    for line in lines:
                        if line.startswith("data: "):
                            data_content = line[6:]
                            if data_content == "[DONE]":
                                break
                            try:
                                import json
                                chunk = json.loads(data_content)
                                if "message" in chunk:
                                    full_reply += chunk["message"]
                            except:
                                pass
                                
                    if full_reply:
                        return full_reply.strip()
                    
                    return "Зайки, привееет! ❤️ У меня тут съемки полным ходом, а вы как? ✨"
                else:
                    print(f"Ошибка ИИ: Статус {response.status}")
                    return "Зайки, привееет! ❤️ У меня тут съемки полным ходом, а вы как? ✨"
    except Exception as e:
        print(f"Критическое исключение ИИ: {e}")
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
    # Сбрасываем старые вебхуки, полностью убирая TelegramConflictError
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
