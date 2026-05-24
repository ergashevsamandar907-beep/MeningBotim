import asyncio
import sqlite3
import random
import os
from PIL import Image, ImageDraw, ImageFont
import io
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    API_TOKEN = "8718770348:AAFx-3GyNBEGv5gnAnEyOXKh7vYjiPali8U"

ADMIN_ID = 8663125946
KANAL_USERNAME = "@mayahumayahi"
REFERRAL_BONUS = 100

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ====================== VAQTINCHALIK HOLAT ======================
kutish_holati = {}  # {user_id: "taklif"}

def rasm_yasa(ism):
    W, H = (800, 450)
    image = Image.new("RGB", (W, H), color=(20, 40, 80))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 90)
    except:
        font = ImageFont.load_default()
    text = ism.capitalize()
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((W-w)/2, (H-h)/2), text, fill="white", font=font)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def baza_yarat():
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS foydalanuvchilar (
                id INTEGER PRIMARY KEY,
                balans INTEGER DEFAULT 0,
                invited_by INTEGER DEFAULT NULL,
                til TEXT DEFAULT 'uz',
                status TEXT DEFAULT 'idle',
                partner_id INTEGER DEFAULT NULL
            )
        """)
        conn.commit()

def foydalanuvchi_qosh(user_id, referrer_id=None):
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO foydalanuvchilar (id, balans, invited_by, til) VALUES (?, 0, ?, 'uz')", (user_id, referrer_id))
            conn.commit()
            if referrer_id and referrer_id != user_id:
                cursor.execute("UPDATE foydalanuvchilar SET balans = balans + ? WHERE id = ?", (REFERRAL_BONUS, referrer_id))
                conn.commit()
        except:
            pass

def holatni_yangila(user_id, status, partner_id=None):
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE foydalanuvchilar SET status = ?, partner_id = ? WHERE id = ?", (status, partner_id, user_id))
        conn.commit()

def foydalanuvchi_holatini_ol(user_id):
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, partner_id FROM foydalanuvchilar WHERE id = ?", (user_id,))
        res = cursor.fetchone()
        return res if res else ("idle", None)

def suhbatdosh_top(user_id):
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM foydalanuvchilar WHERE status = 'searching' AND id != ?", (user_id,))
        res = cursor.fetchone()
        return res[0] if res else None

def foydalanuvchi_tilini_yangila(user_id, til):
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE foydalanuvchilar SET til = ? WHERE id = ?", (til, user_id))
        conn.commit()

def foydalanuvchi_tilini_ol(user_id):
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT til FROM foydalanuvchilar WHERE id = ?", (user_id,))
        res = cursor.fetchone()
        return res[0] if res else "uz"

def foydalanuvchilar_soni():
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM foydalanuvchilar")
        return cursor.fetchone()[0]

def foydalanuvchi_balansi(user_id):
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balans FROM foydalanuvchilar WHERE id = ?", (user_id,))
        res = cursor.fetchone()
        return res[0] if res else 0

def barcha_foydalanuvchilarni_ol():
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM foydalanuvchilar")
        return cursor.fetchall()

async def youtube_musiqa_qidir(soz):
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch3:{soz} music", download=False)
            natijalar = []
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        natijalar.append({'nomi': entry.get('title', 'Noma\'lum'), 'link': f"https://youtube.com/watch?v={entry['id']}"})
            return natijalar
    except:
        return []

async def azo_bolganmi(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=KANAL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

baza_yarat()

MATNLAR = {
    "uz": {
        "start": "Assalomu alaykum! Botga xush kelibsiz!",
        "btn_ismlar": "🔍 Ismlar",
        "btn_tasodif": "🎲 Tasodifiy",
        "btn_hamkor": "🤝 Hamkorlik",
        "btn_stat": "📊 Statistika",
        "btn_ishlash": "🧠 Bot haqida",
        "btn_profil": "👤 Profil",
        "btn_til": "🌐 Til",
        "btn_taklif": "✍️ Ism taklif qilish",
        "btn_chat": "💬 Suhbat",
        "btn_stop": "❌ To'xtat",
        "btn_musiqa": "🎵 Musiqa",
        "sub_text": "Kanalga a'zo bo'ling!",
        "sub_btn": "A'zo bo'lish",
        "sub_check": "Tekshirish",
        "sub_error": "A'zo emassiz!",
        "sub_success": "Rahmat!",
        "ref_bonus": f"🎉 +{REFERRAL_BONUS} so'm!",
        "stat_text": "📊 {soni} ta",
        "work_text": "Ism yozing",
        "profile_text": "ID: {user_id}\nBalans: {balans}",
        "not_found": "Kechirasiz, bu ism ma'nosi bazamizda yo'q",
        "change_lang": "Til tanlang",
        "lang_changed": "O'zgartirildi",
        "taklif_text": "✍️ Iltimos, bazaga qo'shilishini hohlagan ismni yozing:",
        "taklif_yuborildi": "✅ Rahmat! Taklifingiz adminga yuborildi.",
        "chat_search": "🔍 Suhbatdosh qidirilmoqda...",
        "chat_found": "🎉 Suhbatdosh topildi!",
        "chat_stopped": "❌ Suhbat yakunlandi",
        "chat_partner_stopped": "Suhbatdosh chiqib ketdi",
        "musiqa_text": "🎵 Qo'shiq nomini yozing:",
        "musiqa_topilmadi": "❌ Hech narsa topilmadi"
    },
    "ru": {
        "start": "Здравствуйте! Добро пожаловать!",
        "btn_ismlar": "🔍 Имена",
        "btn_tasodif": "🎲 Случайное",
        "btn_hamkor": "🤝 Партнеры",
        "btn_stat": "📊 Статистика",
        "btn_ishlash": "🧠 О боте",
        "btn_profil": "👤 Профиль",
        "btn_til": "🌐 Язык",
        "btn_taklif": "✍️ Предложить имя",
        "btn_chat": "💬 Чат",
        "btn_stop": "❌ Стоп",
        "btn_musiqa": "🎵 Музыка",
        "sub_text": "Подпишитесь!",
        "sub_btn": "Подписаться",
        "sub_check": "Проверить",
        "sub_error": "Не подписан!",
        "sub_success": "Спасибо!",
        "ref_bonus": f"🎉 +{REFERRAL_BONUS} сум!",
        "stat_text": "📊 {soni}",
        "work_text": "Напишите имя",
        "profile_text": "ID: {user_id}\nБаланс: {balans}",
        "not_found": "Извините, это имя не найдено",
        "change_lang": "Выберите язык",
        "lang_changed": "Изменено",
        "taklif_text": "✍️ Напишите имя для добавления:",
        "taklif_yuborildi": "✅ Спасибо! Предложение отправлено",
        "chat_search": "🔍 Поиск собеседника...",
        "chat_found": "🎉 Собеседник найден!",
        "chat_stopped": "❌ Чат завершен",
        "chat_partner_stopped": "Собеседник вышел",
        "musiqa_text": "🎵 Напишите название песни:",
        "musiqa_topilmadi": "❌ Ничего не найдено"
    },
    "en": {
        "start": "Hello! Welcome!",
        "btn_ismlar": "🔍 Names",
        "btn_tasodif": "🎲 Random",
        "btn_hamkor": "🤝 Referral",
        "btn_stat": "📊 Stats",
        "btn_ishlash": "🧠 About",
        "btn_profil": "👤 Profile",
        "btn_til": "🌐 Language",
        "btn_taklif": "✍️ Suggest name",
        "btn_chat": "💬 Chat",
        "btn_stop": "❌ Stop",
        "btn_musiqa": "🎵 Music",
        "sub_text": "Subscribe!",
        "sub_btn": "Subscribe",
        "sub_check": "Check",
        "sub_error": "Not subscribed!",
        "sub_success": "Thanks!",
        "ref_bonus": f"🎉 +{REFERRAL_BONUS} sum!",
        "stat_text": "📊 {soni}",
        "work_text": "Send name",
        "profile_text": "ID: {user_id}\nBalance: {balans}",
        "not_found": "Sorry, name not found",
        "change_lang": "Choose language",
        "lang_changed": "Changed",
        "taklif_text": "✍️ Send name to add:",
        "taklif_yuborildi": "✅ Thanks! Suggestion sent",
        "chat_search": "🔍 Searching...",
        "chat_found": "🎉 Partner found!",
        "chat_stopped": "❌ Chat stopped",
        "chat_partner_stopped": "Partner left",
        "musiqa_text": "🎵 Enter song name:",
        "musiqa_topilmadi": "❌ Nothing found"
    }
}

def menyu_klaviaturasi(til):
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=MATNLAR[til]["btn_ismlar"]), KeyboardButton(text=MATNLAR[til]["btn_tasodif"])],
        [KeyboardButton(text=MATNLAR[til]["btn_hamkor"]), KeyboardButton(text=MATNLAR[til]["btn_stat"])],
        [KeyboardButton(text=MATNLAR[til]["btn_ishlash"]), KeyboardButton(text=MATNLAR[til]["btn_profil"])],
        [KeyboardButton(text=MATNLAR[til]["btn_taklif"]), KeyboardButton(text=MATNLAR[til]["btn_til"])],
        [KeyboardButton(text=MATNLAR[til]["btn_chat"]), KeyboardButton(text=MATNLAR[til]["btn_musiqa"])]
    ], resize_keyboard=True)

def suhbat_klaviaturasi(til):
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=MATNLAR[til]["btn_stop"])]], resize_keyboard=True)

def til_tanlash_klaviaturasi():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="setlang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")
    ]])

def aazolik_klaviaturasi(til):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=MATNLAR[til]["sub_btn"], url=f"https://t.me/{KANAL_USERNAME.replace('@', '')}")
    ], [
        InlineKeyboardButton(text=MATNLAR[til]["sub_check"], callback_data="check_sub")
    ]])

ISMLAR_MANOSI = {
    "oybek": "Oybek — go'zal",
    "behzod": "Behzod — yaxshi",
    "abbos": "Abbos — jasur"
}

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    foydalanuvchi_qosh(user_id)
    til = foydalanuvchi_tilini_ol(user_id)
    if not await azo_bolganmi(user_id):
        await message.answer(MATNLAR[til]["sub_text"], reply_markup=aazolik_klaviaturasi(til))
        return
    await message.answer(MATNLAR[til]["start"], reply_markup=menyu_klaviaturasi(til))

@dp.callback_query(lambda c: c.data.startswith("setlang_"))
async def change_language_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    yangi_til = callback.data.split("_")[1]
    foydalanuvchi_tilini_yangila(user_id, yangi_til)
    await callback.message.delete()
    await bot.send_message(user_id, MATNLAR[yangi_til]["lang_changed"], reply_markup=menyu_klaviaturasi(yangi_til))

@dp.callback_query(lambda c: c.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    til = foydalanuvchi_tilini_ol(user_id)
    if await azo_bolganmi(user_id):
        await callback.message.delete()
        await bot.send_message(user_id, MATNLAR[til]["sub_success"], reply_markup=menyu_klaviaturasi(til))
    else:
        await callback.answer(MATNLAR[til]["sub_error"], show_alert=True)

@dp.message()
async def bot_messages(message: types.Message):
    user_id = message.from_user.id
    til = foydalanuvchi_tilini_ol(user_id)
    status, partner_id = foydalanuvchi_holatini_ol(user_id)

    if not await azo_bolganmi(user_id):
        await message.answer(MATNLAR[til]["sub_text"], reply_markup=aazolik_klaviaturasi(til))
        return

    text = message.text.strip() if message.text else ""

    # ========== SUHBATNI TO'XTATISH ==========
    if text == MATNLAR[til]["btn_stop"]:
        if status == "chatting" and partner_id:
            partner_til = foydalanuvchi_tilini_ol(partner_id)
            await bot.send_message(partner_id, MATNLAR[partner_til]["chat_partner_stopped"], reply_markup=menyu_klaviaturasi(partner_til))
            holatni_yangila(partner_id, "idle", None)
        holatni_yangila(user_id, "idle", None)
        await message.answer(MATNLAR[til]["chat_stopped"], reply_markup=menyu_klaviaturasi(til))
        return

    # ========== SUHBAT JARAYONIDA ==========
    if status == "chatting" and partner_id:
        try:
            await message.copy_to(chat_id=partner_id)
        except:
            await message.answer("Aloqa uzildi", reply_markup=menyu_klaviaturasi(til))
            holatni_yangila(user_id, "idle", None)
            holatni_yangila(partner_id, "idle", None)
        return

    # ========== ISM TAKLIF QILISH TUGMASI ==========
    if text == MATNLAR[til]["btn_taklif"]:
        kutish_holati[user_id] = "taklif"
        await message.answer(MATNLAR[til]["taklif_text"])
        return

    # ========== MUSIQA QIDIRISH TUGMASI ==========
    if text == MATNLAR[til]["btn_musiqa"]:
        await message.answer(MATNLAR[til]["musiqa_text"])
        return

    # ========== AGAR TAKLIF HOLATIDA BO'LSA ==========
    if user_id in kutish_holati and kutish_holati[user_id] == "taklif":
        # Holatni tozalaymiz
        del kutish_holati[user_id]
        
        # Faqat shu yerda adminga xabar boradi!
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🆕 **Yangi ism taklifi**\n\n"
                f"👤 Kimdan: {message.from_user.full_name}\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"📝 Taklif: <b>{text}</b>"
            )
            await message.answer(MATNLAR[til]["taklif_yuborildi"])
        except:
            await message.answer("Xatolik yuz berdi. Qayta urinib ko'ring.")
        return

    # ========== MUSIQA QIDIRISH ==========
    if text == MATNLAR[til]["btn_musiqa"]:
        await message.answer(MATNLAR[til]["musiqa_text"])
        return

    if text and text not in [MATNLAR[til]["btn_ismlar"], MATNLAR[til]["btn_tasodif"], MATNLAR[til]["btn_hamkor"], 
                             MATNLAR[til]["btn_stat"], MATNLAR[til]["btn_ishlash"], MATNLAR[til]["btn_profil"], 
                             MATNLAR[til]["btn_til"], MATNLAR[til]["btn_taklif"], MATNLAR[til]["btn_chat"], 
                             MATNLAR[til]["btn_stop"], MATNLAR[til]["btn_musiqa"]]:
        if status != "chatting":
            natijalar = await youtube_musiqa_qidir(text)
            if natijalar:
                javob = "🎵 **Topilgan qo'shiqlar:**\n\n"
                for i, q in enumerate(natijalar[:3], 1):
                    javob += f"{i}. {q['nomi'][:40]}\n   🔗 {q['link']}\n\n"
                await message.answer(javob, disable_web_page_preview=True)
            else:
                await message.answer(MATNLAR[til]["musiqa_topilmadi"])
            return

    # ========== MENYU TUGMALARI ==========
    if text == MATNLAR[til]["btn_ismlar"]:
        ismlar = ", ".join(list(ISMLAR_MANOSI.keys()))
        await message.answer(f"📚 Bazadagi ismlar:\n\n{ismlar}")

    elif text == MATNLAR[til]["btn_tasodif"]:
        tasodifiy_ism = random.choice(list(ISMLAR_MANOSI.keys()))
        await message.answer(f"🎲 Tasodifiy ism: {tasodifiy_ism.capitalize()}")

    elif text == MATNLAR[til]["btn_hamkor"]:
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        await message.answer(f"💰 Balans: {foydalanuvchi_balansi(user_id)} so'm\n🔗 Link: <code>{ref_link}</code>")

    elif text == MATNLAR[til]["btn_stat"]:
        await message.answer(MATNLAR[til]["stat_text"].format(soni=foydalanuvchilar_soni()))

    elif text == MATNLAR[til]["btn_ishlash"]:
        await message.answer("Ismlar ma'nosini bilish yoki musiqa qidirish mumkin")

    elif text == MATNLAR[til]["btn_profil"]:
        await message.answer(MATNLAR[til]["profile_text"].format(user_id=user_id, balans=foydalanuvchi_balansi(user_id)))

    elif text == MATNLAR[til]["btn_til"]:
        await message.answer(MATNLAR[til]["change_lang"], reply_markup=til_tanlash_klaviaturasi())

    elif text == MATNLAR[til]["btn_chat"]:
        s_id = suhbatdosh_top(user_id)
        if s_id:
            holatni_yangila(user_id, "chatting", s_id)
            holatni_yangila(s_id, "chatting", user_id)
            await message.answer(MATNLAR[til]["chat_found"], reply_markup=suhbat_klaviaturasi(til))
            await bot.send_message(s_id, MATNLAR[foydalanuvchi_tilini_ol(s_id)]["chat_found"], reply_markup=suhbat_klaviaturasi(foydalanuvchi_tilini_ol(s_id)))
        else:
            holatni_yangila(user_id, "searching", None)
            await message.answer(MATNLAR[til]["chat_search"], reply_markup=suhbat_klaviaturasi(til))

    elif text:
        ism_clean = text.lower().replace("'", "").replace("`", "")
        if ism_clean in ISMLAR_MANOSI:
            await message.answer(f"📌 <b>{text.capitalize()}</b>\n\n{ISMLAR_MANOSI[ism_clean]}")
        else:
            await message.answer(MATNLAR[til]["not_found"])

async def main():
    print(" Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())