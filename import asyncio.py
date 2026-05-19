import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = "8718770348:AAGKn5Sk1E8P-JNMzOf8q5JnPEmRvaAZy0M"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(msg: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Qiz qidirish"), KeyboardButton(text="🔍 Yigit qidirish")],
            [KeyboardButton(text="🎲 Tasodifiy qidirish"), KeyboardButton(text="👤 Profil")],
            [KeyboardButton(text="✏️ Profil yaratish"), KeyboardButton(text="🗑 Profil o'chirish")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Tanishuv botiga xush kelibsiz!", reply_markup=keyboard)

@dp.message()
async def echo(msg: types.Message):
    await msg.answer(f"Siz yozdingiz: {msg.text}")

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())