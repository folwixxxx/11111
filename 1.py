import asyncio
from aiogram import Bot, Dispatcher, types
from openai import AsyncOpenAI
from aiohttp import web

TELEGRAM_TOKEN = "8957069453:AAELr_YP0y4QrlliwKSvv8OxZ5_qiwp58bQ"
HF_API_TOKEN = "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"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

ai_client = AsyncOpenAI(
    api_key=HF_API_TOKEN,
    base_url="https://huggingface.co"  
)

# Улучшенный промпт, чтобы ИИ понимал задачу точнее
SYSTEM_PROMPT = (
    "Ты — популярный блогер и певица Милана Стар (Milana Star). Тебе 16-17 лет. "
    "Ты общаешься в чате со своими любимыми фанатами. "
    "Твой тон: супер-дружелюбный, активный, используй молодежный сленг, "
    "много эмодзи (✨, ❤️, 👑, 🧸) и восклицательные знаки. Отвечай коротко (1-2 предложения), "
    "как в реальном чате. Не пиши никаких системных логов и не повторяй вопрос пользователя!"
)

async def generate_ai_response(user_text: str, username: str) -> str:
    try:
        response = await ai_client.chat.completions.create(
            # ИСПРАВЛЕНО: Переключено на сверхстабильную модель Llama 3.3
            model="meta-llama/Llama-3.3-70B-Instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Пользователь @{username} пишет тебе: {user_text}"}
            ],
            max_tokens=80,
            temperature=0.8
        )
        
        reply = ""
        if isinstance(response, str):
            reply = response
        elif hasattr(response, 'choices') and response.choices:
            reply = response.choices.message.content

        # ИСПРАВЛЕНО: Безопасная очистка текста без багов со списками
        reply = reply.strip()
        
        # Если ИИ всё-таки вернул пустоту, даем живой рандомный ответ фанатам
        if not reply:
            return "Зайки, привееет! ❤️ У меня тут съемки полным ходом, а вы как? ✨"
            
        # Защита от слишком длинного текста (берем первые 250 символов)
        if len(reply) > 250:
            reply = reply[:250] + "..."
            
        return reply
        
    except Exception as e:
        print(f"Ошибка ИИ на сервере: {e}")
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
