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

SYSTEM_PROMPT = (
    "Ты — популярный блогер и певица Милана Стар (Milana Star). Тебе 16-17 лет. "
    "Общаешься дружелюбно, используешь современный молодежный сленг, "
    "много эмодзи (✨, ❤️, 👑) и отвечаешь ОЧЕНЬ коротко (1-2 предложения). "
    "Не пиши никаких системных логов, только твой ответ пользователю!"
)

async def generate_ai_response(user_text: str, username: str) -> str:
    try:
        response = await ai_client.chat.completions.create(
            # Смена модели на более стабильную для коротких ответов по API
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Пользователь @{username} пишет тебе: {user_text}"}
            ],
            max_tokens=80,
            temperature=0.7
        )
        
        reply = ""
        if isinstance(response, str):
            reply = response
        elif hasattr(response, 'choices') and response.choices:
            reply = response.choices.message.content

        # Очистка и защита от слишком длинного или пустого текста
        reply = reply.strip()
        if not reply:
            return "Зайки, я тут! ✨ Что делаете? ❤️"
            
        # Если ИИ прислал слишком много, жестко берем только первое предложение
        if len(reply) > 300:
            reply = reply.split('.')[0] + "."
            
        return reply
        
    except Exception as e:
        print(f"Ошибка ИИ на сервере: {e}")
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
