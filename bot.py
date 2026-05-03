import os
from aiohttp import web
import asyncio
import sqlite3
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ====================== SOZLAMALAR ======================
API_TOKEN = "8718770348:AAGKn5Sk1E8P-JNMzOf8q5JnPEmRvaAZy0M"
ADMIN_ID = 8663125946
KANAL_USERNAME = "@mayahumayahi"

REFERRAL_BONUS = 100

# Default parse_mode sifatida HTML belgilaymiz, Markdown xatolaridan qochish uchun
from aiogram.client.default import DefaultBotProperties

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ====================== BAZA ======================
def baza_yarat():
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS foydalanuvchilar (
                id INTEGER PRIMARY KEY,
                balans INTEGER DEFAULT 0,
                invited_by INTEGER DEFAULT NULL,
                til TEXT DEFAULT 'uz'
            )
        """)
        conn.commit()

def foydalanuvchi_qosh(user_id, referrer_id=None):
    with sqlite3.connect("bot_bazasi.db") as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO foydalanuvchilar (id, balans, invited_by, til) VALUES (?, 0, ?, 'uz')", 
                (user_id, referrer_id)
            )
            conn.commit()
            
            if referrer_id and referrer_id != user_id:
                cursor.execute("UPDATE foydalanuvchilar SET balans = balans + ? WHERE id = ?", 
                             (REFERRAL_BONUS, referrer_id))
                conn.commit()
        except sqlite3.IntegrityError:
            pass

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

# ====================== KANAL TEKSHIRISH ======================
async def aza_bolganmi(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=KANAL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return False

baza_yarat()

# ====================== MATNLAR ======================
MATNLAR = {
    "uz": {
        "start": "Assalomu alaykum! Ism kiriting yoki menyudan foydalaning.",
        "btn_ismlar": "🔍 Ismlar ro'yxati 📋",
        "btn_tasodif": "🎲 Tasodifiy ism 🎲",
        "btn_hamkor": "🤝 Hamkorlik dasturi 🤝",
        "btn_stat": "📊 Statistika 📊",
        "btn_ishlash": "🧠 Bot qanday ishlaydi",
        "btn_profil": "👤 Profilim",
        "btn_til": "🌐 Tilni almashtirish",
        "sub_text": "Botdan foydalanishdan oldin homiy kanalimizga a'zo bo'lishingiz kerak:",
        "sub_btn": "📢 Kanalga a'zo bo'lish",
        "sub_check": "✅ Tasdiqlash",
        "sub_error": "Siz hali kanalga a'zo bo'lmadingiz! ❌",
        "sub_success": "Rahmat! Endi botdan to'liq foydalanishingiz mumkin.",
        "ref_bonus": "🎉 Yangi do'st taklif qildingiz! Sizga {bonus} so'm berildi.",
        "stat_text": "📊 Jami obunachilar: {soni} ta.",
        "work_text": "Tugmalardan foydalaning yoki ism yozib yuboring.",
        "profile_text": "👤 Profilingiz:\n🆔 ID: <code>{user_id}</code>\n💰 Balans: {balans} so'm",
        "not_found": "Kechirasiz, bu ism ma'nosi hali bazamizga qo'shilmagan.",
        "change_lang": "Iltimos, tilni tanlang:",
        "lang_changed": "Til muvaffaqiyatli o'zgartirildi! 🇺🇿"
    },
    "ru": {
        "start": "Здравствуйте! Введите имя или используйте меню.",
        "btn_ismlar": "🔍 Список имен 📋",
        "btn_tasodif": "🎲 Случайное имя 🎲",
        "btn_hamkor": "🤝 Партнерская программа 🤝",
        "btn_stat": "📊 Статистика 📊",
        "btn_ishlash": "🧠 Как работает бот",
        "btn_profil": "👤 Мой профиль",
        "btn_til": "🌐 Сменить язык",
        "sub_text": "Перед использованием бота необходимо подписаться на спонсорский канал:",
        "sub_btn": "📢 Подписаться на канал",
        "sub_check": "✅ Проверить",
        "sub_error": "Вы еще не подписались на канал! ❌",
        "sub_success": "Спасибо! Теперь вы можете полноценно использовать бота.",
        "ref_bonus": "🎉 Вы пригласили нового друга! Вам начислено {bonus} сум.",
        "stat_text": "📊 Всего подписчиков: {soni}.",
        "work_text": "Используйте кнопки или отправьте имя.",
        "profile_text": "👤 Ваш профиль:\n🆔 ID: <code>{user_id}</code>\n💰 Balans: {balans} сум",
        "not_found": "Извините, значение этого имени еще не добавлено в базу.",
        "change_lang": "Пожалуйста, выберите язык:",
        "lang_changed": "Язык успешно изменен! 🇷🇺"
    },
    "en": {
        "start": "Hello! Enter a name or use the menu.",
        "btn_ismlar": "🔍 List of Names 📋",
        "btn_tasodif": "🎲 Random Name 🎲",
        "btn_hamkor": "🤝 Referral Program 🤝",
        "btn_stat": "📊 Statistics 📊",
        "btn_ishlash": "🧠 How the bot works",
        "btn_profil": "👤 My Profile",
        "btn_til": "🌐 Change Language",
        "sub_text": "Before using the bot, you must subscribe to our sponsor channel:",
        "sub_btn": "📢 Subscribe to the channel",
        "sub_check": "✅ Verify",
        "sub_error": "You have not subscribed to the channel yet! ❌",
        "sub_success": "Thank you! Now you can fully use the bot.",
        "ref_bonus": "🎉 You invited a new friend! You earned {bonus} sum.",
        "stat_text": "📊 Total subscribers: {soni}.",
        "work_text": "Use buttons or send a name.",
        "profile_text": "👤 Your profile:\n🆔 ID: <code>{user_id}</code>\n💰 Balance: {balans} sum",
        "not_found": "Sorry, the meaning of this name is not added yet.",
        "change_lang": "Please select a language:",
        "lang_changed": "Language changed successfully! 🇬🇧"
    }
}

# ====================== KLAVIATURALAR ======================
def menyu_klaviaturasi(til):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MATNLAR[til]["btn_ismlar"]), KeyboardButton(text=MATNLAR[til]["btn_tasodif"])],
            [KeyboardButton(text=MATNLAR[til]["btn_hamkor"]), KeyboardButton(text=MATNLAR[til]["btn_stat"])],
            [KeyboardButton(text=MATNLAR[til]["btn_ishlash"]), KeyboardButton(text=MATNLAR[til]["btn_profil"])],
            [KeyboardButton(text=MATNLAR[til]["btn_til"])]
        ],
        resize_keyboard=True
    )

def til_tanlash_klaviaturasi():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")
    ]])

def aazolik_klaviaturasi(til):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=MATNLAR[til]["sub_btn"], url=f"https://t.me/{KANAL_USERNAME.replace('@', '')}")
    ], [
        InlineKeyboardButton(text=MATNLAR[til]["sub_check"], callback_data="check_sub")
    ]])

# ====================== ISMLAR MA'NOSI (Kichik harfda) ======================
ISMLAR_MANOSI = {
    "oybek": "Oybek — oy kabi go'zal, porloq va beklik martabasiga ega bo'lgan yigit.",
    "behzod": "Behzod — yaxshi fe'l-atvorli, aslzoda va barkamol inson.",
    "abbos": "Abbos — qovog'i soliq, jiddiy, dovjigar va jasur o'g'il.",
    "afsona": "Afsona — sehrli hikoya kabi jozibali va sirli qiz.",
    "abdulaziz": "Abdulaziz — aziz va qudratli bo'lgan Allohning bandasi.",
    "asal": "Asal — shirin, yoqimli va hamma suyadigan qiz.",
    "abdulla": "Abdulla — Allohning bandasi, solih va iymonli inson.",
    "aziza": "Aziza — qadrli, hurmatli va eng aziz qiz.",
    "abdurahmon": "Abdurahmon — mehribon va rahmli Allohning bandasi.",
    "bahora": "Bahora — bahor fasli kabi go'zal va yorqin.",
    "abror": "Abror — yaxshilik qiluvchi, pokiza va taqvodor inson.",
    "barchinoy": "Barchinoy — oydek go'zal va xalq dostonlaridagi jasur qiz.",
    "adiz": "Adiz — aziz, qadrli, hurmatga loyiq yigit.",
    "barno": "Barno — kelbatli, chiroyli va jozibali qiz.",
    "adham": "Adham — qora ot kabi kuchli, kelbatli va baquvvat.",
    "charos": "Charos — katta va qora ko'zlari maftunkor bo'lgan qiz.",
    "akbar": "Akbar — ulug', buyuk va eng katta martabaga ega inson.",
    "dildora": "Dildora — dilni o'ziga rom etuvchi, sevimli qiz.",
    "akmal": "Akmal — mukammal, eng yetuk va benuqson yigit.",
    "dilnoza": "Dilnoza — dili nozik, latofatli va suluv qiz.",
    "alisher": "Alisher — Ali kabi jasur va sherdek qudratli inson.",
    "dilrabo": "Dilrabo — go'zalligi bilan ko'ngillarni jalb qiluvchi.",
    "amir": "Amir — hukmdor, yo'lboshchi va boshliq.",
    "durdona": "Durdona — dur donasi kabi qimmatbaho va noyob qiz.",
    "anvar": "Anvar — nurli, yorug' va iqboli baland yigit.",
    "ezoza": "E'zoza — e'zozga loyiq, hurmatli va qadrli qiz.",
    "arslon": "Arslon — sher kabi kuchli, jasur va qo'rqmas.",
    "farangiz": "Farangiz — shuhrat keltiruvchi, yorqin va go'zal.",
    "asad": "Asad — arslon kabi mard, botir va qudratli o'g'il.",
    "fazilat": "Fazilat — yaxshi xulqli, odobli va bilimli qiz.",
    "asadbek": "Asadbek — jasur, mardlar boshlig'i va arslondek qudratli.",
    "feruza": "Feruza — baxt keltiruvchi qimmatbaho moviy tosh kabi.",
    "gozal": "Go'zal — nihoyatda go'zal, chiroyli va latofatli.",
    "gulbahor": "Gulbahor — bahorning ilk va go'zal guli kabi.",
    "aziz": "Aziz — qadrli, hurmatli va qadri baland inson.",
    "azizbek": "Azizbek — ulug'vor, aziz va hurmatga loyiq beklardan biri.",
    "guldona": "Guldona — gullar ichida eng noyob va qadrlisi.",
    "azamat": "Azamat — qaddi-qomati kelbatli, jasur va botir yigit.",
    "gulnora": "Gulnora — anor guli kabi yorqin, qizil va jozibali.",
    "bahodir": "Bahodir — botir, mard, jasur va qo'rqmas jangchi.",
    "gulnoza": "Gulnoza — nozik, latofatli va gul kabi nafis qiz.",
    "bahriddin": "Bahriddin — dinning nuri, ziynati va yorug'ligi.",
    "gulrux": "Gulrux — yuzi gul kabi chiroyli va tiniq qiz.",
    "baxtiyor": "Baxtiyor — baxtli, omadli va doimo quvnoq yuruvchi.",
    "gulsenam": "Gulsenam — mening sevimli gulim, go'zalim.",
    "bekzod": "Bekzod — beklar avlodidan bo'lgan, aslzoda o'g'il.",
    "gulsanam": "Gulsanam — gullar ichida sanam kabi maftunkor bo'lgan.",
    "bobur": "Bobur — sher, yo'lboshchi va jasur jangchi.",
    "gulshoda": "Gulshoda — gullar shodasi kabi go'zal va quvnoq.",
    "botir": "Botir — mard, qo'rqmas, jasoratli yigit.",
    "iroda": "Iroda — matonatli, irodali va qat'iyatli qiz.",
    "diyor": "Diyor — vatan, yurt va do'stona o'lka farzandi.",
    "kamola": "Kamola — kamolga yetgan, odobli va mukammal qiz.",
    "dilshod": "Dilshod — dili shod, quvnoq va baxtiyor yigit.",
    "lobar": "Lobar — xushmuomala, jozibali va yoqimtoy qiz.",
    "doniyor": "Doniyor — Allohning tuhfasi, bilimli va dono inson.",
    "laylo": "Laylo — tungi go'zallik, qora ko'zli va maftunkor.",
    "doston": "Doston — dovrug'i ketgan, mashhur va tillarda doston yigit.",
    "madina": "Madina — muqaddas shahar nomi, madaniyatli qiz.",
    "elbek": "Elbek — yurt boshlig'i, elning bek yigiti.",
    "malika": "Malika — shohona go'zallikka ega, oliynasab qiz.",
    "elmurod": "Elmurod — elning orzusi, xalq kutilgan o'g'il.",
    "maftuna": "Maftuna — o'ziga maftun qiluvchi, jozibali.",
    "elyor": "Elyor — xalq do'sti, el-yurtga yordam beruvchi.",
    "manzura": "Manzura — maqbul bo'lgan, hamma yoqtiradigan qiz.",
    "erkin": "Erkin — hurliksevar, mustaqil va erkin inson.",
    "marjona": "Marjona — dengiz tubidagi qimmatbaho marjon kabi.",
    "farhod": "Farhod — aqlli, zukko va yengilmas pahlavon.",
    "mastura": "Mastura — iffatli, pokiza va iboli qiz.",
    "farrux": "Farrux — chiroyli, go'zal va iqboli baland yigit.",
    "mohigul": "Mohigul — oydek go'zal va gul kabi nafis qiz.",
    "fayzulloh": "Fayzulloh — Allohning marhamati, uyi fayzli farzand.",
    "mohinur": "Mohinur — oyning nuri kabi yorug' va chiroyli.",
    "firdavs": "Firdavs — jannatning eng oliy bog'i kabi go'zal o'g'il.",
    "mubina": "Mubina — ochiq-oydin, tiniq va pokiza qiz.",
    "gayrat": "G'ayrat — harakatchan, shijoatli va intiluvchan yigit.",
    "mukarrama": "Mukarrama — aziz, muqaddas va hurmatga loyiq qiz.",
    "habibulloh": "Habibulloh — Allohning suyukli do'sti, qadrdoni.",
    "munisa": "Munisa — eng yaqin do'st, hamdard va mehribon qiz.",
    "hamid": "Hamid — maqtovga loyiq, yaxshi xulqli yigit.",
    "mushtariy": "Mushtariy — yulduz kabi yorqin va baland martabali.",
    "hasan": "Hasan — chiroyli, go'zal va yaxshi amallar egasi.",
    "muazzam": "Muazzam — ulug'vor, hurmatli va buyuk qiz.",
    "husan": "Husan — yaxshi, go'zal va mukammal farzand.",
    "nafisa": "Nafisa — nozik, nafis va juda go'zal qiz.",
    "ibrohim": "Ibrohim — xalqlarning otasi, ulug' va olijanob inson.",
    "nargiza": "Nargiza — bahoriy go'zal gul kabi latofatli qiz.",
    "nasiba": "Nasiba — rizq-ro'zli, baxtli va ulushli qiz.",
    "ilhom": "Ilhom — ruhlanish, ijodiy ko'tarinkilik egasi.",
    "nilufar": "Nilufar — suvda ochiladigan go'zal va nafis gul.",
    "imron": "Imron — yashovchan, obod qiluvchi va hayotsevar.",
    "nigina": "Nigina — uzuk ko'zi kabi qadrli va chiroyli.",
    "iskandar": "Iskandar — g'olib, himoyachi va buyuk hukmdor.",
    "nigora": "Nigora — chiroyli nigohli, go'zal ko'zli qiz.",
    "islom": "Islom — Allohga bo'ysunuvchi, tinchlik tarafdori.",
    "nodira": "Nodira — noyob, kamyob va juda qadrli qiz.",
    "ismoil": "Ismoil — Alloh eshitdi, ijobat bo'lgan orzu.",
    "nozima": "Nozima — tartibli, odobli va aqlli qiz.",
    "izzat": "Izzat — hurmat-ehtirom va qadr-qimmat egasi.",
    "nozli": "Nozli — nozik, erka va latofatli qiz.",
    "jahongir": "Jahongir — dunyo fath etuvchi, g'olib va jasur.",
    "oydina": "Oydina — oydin, yorug' va kechasi porlovchi.",
    "jamshid": "Jamshid — buyuk hukmdor, porloq va nurli yigit.",
    "oysha": "Oysha — yashovchan, hayotsevar va barakali qiz.",
    "jasur": "Jasur — botir, mard va qo'rqmas inson.",
    "parizod": "Parizod — pari kabi go'zal va jozibali qiz.",
    "javohir": "Javohir — qimmatbaho tosh kabi qadrli va noyob.",
    "rano": "Rano — go'zal va xushbo'y tog' guli kabi.",
    "kamron": "Kamron — maqsadiga yetuvchi, omadli va g'olib.",
    "rayhona": "Rayhona — xushbo'y rayhon guli kabi yoqimli.",
    "laziz": "Laziz — yoqimli, shirin va aziz farzand.",
    "robiya": "Robiya — to'rtinchi farzand, bahor nafasi kabi.",
    "mansur": "Mansur — g'alaba qozonuvchi, doimo ustun keluvchi.",
    "ruxshona": "Ruxshona — yorqin yuzli, chiroyli va kelajagi yorug'.",
    "maqsud": "Maqsud — orzu qilingan, kutilgan va niyat qilingan o'g'il.",
    "sabina": "Sabina — qadimiy qabila nomi, kelbatli va go'zal.",
    "mirfayz": "Mirfayz — fayzli, ulug' va olijanob yigit.",
    "sabrina": "Sabrina — sabr-toqatli, chidamli va matonatli qiz.",
    "murod": "Murod — orzu, niyat va maqsadiga yetishuvchi.",
    "sadaf": "Sadaf — dengiz chig'anoqlaridagi noyob marvarid kabi.",
    "muzaffar": "Muzaffar — g'olib, zafar quchuvchi va omadli.",
    "sajida": "Sajida — Allohga sajda qiluvchi, iymonli qiz.",
    "muhammad": "Muhammad — maqtovga loyiq, ulug' va yaxshi xulqli.",
    "salima": "Salima — sog'-salomat, beg'ubor va pokiza qiz.",
    "navroz": "Navro'z — yangi kun, bahor farzandi.",
    "sarvinoz": "Sarvinoz — sarv daraxti kabi qaddi-qomati go'zal.",
    "nodir": "Nodir — noyob, kamyob va juda qadrli yigit.",
    "sevara": "Sevara — sevimli, hamma yoqtiradigan va sevadigan.",
    "nozim": "Nozim — tartibli, qonun-qoidaga amal qiluvchi.",
    "sitora": "Sitora — tungi osmonning yorqin yulduzi kabi.",
    "shahlo": "Shahlo — katta, qora yoki ko'k ko'zli maftunkor qiz.",
    "olim": "Olim — bilimli, ilmli va zukko inson.",
    "shahnoza": "Shahnoza — shohona latofatga ega, erka va go'zal qiz.",
    "omon": "Omon — sog'-salomat, tinch va xotirjam.",
    "shaxzoda": "Shaxzoda — shohlar avlodidan bo'lgan oliynasab qiz.",
    "orif": "Orif — bilimli, ma'rifatli va dono yigit.",
    "shirin": "Shirin — yoqimli, shirinso'z va mehribon qiz.",
    "ortiq": "Ortiq — boshqalardan ustun, kelbatli o'g'il.",
    "shodiya": "Shodiya — shodlik, quvonch va baxt keltiruvchi.",
    "oybek": "Oybek — oy kabi go'zal va beklar avlodidan bo'lgan.",
    "umida": "Umida — kelajakdan kutilgan orzu va niyat.",
    "otabek": "Otabek — otasi kabi ulug' va beklars boshlig'i.",
    "vasila": "Vasila — yaqinlashtiruvchi, vositachi va suyukli qiz.",
    "oyatulloh": "Oyatulloh — Allohning mo''jizasi, nuri va hujjati.",
    "visola": "Visola — diydor ko'rishish, uchrashish baxti.",
    "ozod": "Ozod — hur, erkin va mustaqil inson.",
    "xadicha": "Xadicha — kutilgandan oldin tug'ilgan, ulug' ayol nomi.",
    "ravshan": "Ravshan — yorug', nurli va kelajagi porloq.",
    "xurshida": "Xurshida — quyosh kabi porloq va nurli qiz.",
    "ramazan": "Ramazan — qutlug' oy farzandi, muborak o'g'il.",
    "yulduz": "Yulduz — yorqin, yorug' va osmondagi yulduz kabi.",
    "rustam": "Rustam — qahramon, pahlavon va juda kuchli yigit.",
    "zarina": "Zarina — tilla rangli, qimmatbaho va oltindek aziz.",
    "sardor": "Sardor — yo'lboshchi, yetakchi va guruh sardori.",
    "zebiniso": "Zebiniso — ayollarning eng go'zali va ziynati.",
    "sarvar": "Sarvar — rahbar, boshliq va yo'lboshchi.",
    "zilola": "Zilola — tiniq, pokiza va zilol suv kabi go'zal qiz.",
    "siroj": "Siroj — chiroq, nur tarqatuvchi va yorug'lik egasi.",
    "ziyoda": "Ziyoda — boshqalardan ortiq, mukammal va ziyod.",
    "sobir": "Sobir — chidamli, sabrli va matonatli yigit.",
    "zohida": "Zohida — taqvodor, Allohga sodiq va pokiza qiz.",
    "solih": "Solih — yaxshi amallar qiluvchi, taqvodor yigit.",
    "zulayxo": "Zulayxo — go'zallikda tengsiz va latofatli qiz.",
    "suhrob": "Suhrob — yaltiroq, qizil rangli la'l kabi qimmatli.",
    "zuhra": "Zuhra — yorqin yulduz kabi porloq va chiroyli.",
    "temur": "Temur — temir kabi mustahkam, irodali va kuchli.",
    "tohir": "Tohir — pok, toza va gunohlardan xoli yigit.",
    "tolqin": "To'lqin — jo'shqin, harakatchan va faol o'g'il.",
    "ulugbek": "Ulug'bek — buyuk, ulug' va eng katta bek.",
    "umid": "Umid — orzu, niyat va kelajakdan kutilgan umid.",
    "usmon": "Usmon — tanti, mard va jasur inson.",
    "xurshid": "Xurshid — quyosh kabi porloq va nurli yigit.",
    "yahyoxon": "Yahyoxon — yashovchi, umri uzoq bo'lgan ulug' inson.",
    "yodgor": "Yodgor — esdalik, ota-onasidan qolgan aziz farzand.",
    "yunus": "Yunus — kaptar, tinchlik va totuvlik elchisi.",
    "yusuf": "Yusuf — husni go'zal, chiroyli va mukammal farzand.",
    "zafar": "Zafar — g'alaba qozonuvchi, muvaffaqiyat egasi.",
    "zokir": "Zokir — Allohni zikr qiluvchi, shukr qiluvchi.",
    "zubayr": "Zubayr — aqlli, kuchli va mard yigit.",
    "zuhriddin": "Zuhriddin — dinning nuri va yorqin yulduzi.",
    "abduqodir": "Abduqodir — hamma narsaga qodir bo'lgan Allohning bandasi.",
    "adiba": "Adiba — odobli, bilimli va ma'rifatli qiz.",
    "ahror": "Ahror — mehribon, saxovatli va pok qalbli inson.",
    "afzal": "Afzal — boshqalardan ustun, afzal va qadrli yigit.",
    "anora": "Anora — anor kabi tiniq, qizil va jozibali qiz.",
    "asilbek": "Asilbek — toza naslli, aslzoda va olijanob yigit.",
    "baxtigul": "Baxtigul — baxtli va gul kabi go'zal hayot kechiruvchi qiz.",
    "bilol": "Bilol — sog'lom, baquvvat va ilk azon aytgan sahoba nomi.",
    "binafsha": "Binafsha — bahorning ilk xushbo'y guli kabi nafis qiz.",
    "bobomurod": "Bobomurod — bobosining niyati va orzusi bilan tug'ilgan o'g'il.",
    "choriyor": "Choriyor — to'rt choriyorga, ya'ni xalifalarga sodiq inson.",
    "dilorom": "Dilorom — dilga orom beruvchi, tinchlantiruvchi va sevimli qiz.",
    "dilmurod": "Dilmurod — dilning orzusi, kutilgan niyati bo'lgan farzand.",
    "dildor": "Dildor — oshiq bo'lgan, doimo sevuvchi va sevimli qiz.",
    "davron": "Davron — yaxshi davr, baxtli zamon farzandi.",
    "diyora": "Diyora — vatan, yurt farzandi, ona yurtini sevuvchi qiz.",
    "eldor": "Eldor — yurtni boshqaruvchi, elga rahbar va yo'lboshchi.",
    "ezoz": "E'zoz — qadrli, hurmatli va e'zozga loyiq yigit.",
    "ergash": "Ergash — o'zidan oldingi akalariga ergashib tug'ilgan o'g'il.",
    "eshmurod": "Eshmurod — orzu qilingan, niyatga erishtiruvchi hamroh.",
    "fariza": "Fariza — farz, Allohning amri bilan dunyoga kelgan qiz.",
    "farid": "Farid — noyob, yagona va tengsiz o'g'il bola.",
    "fazliddin": "Fazliddin — dinning fazilati, ilmi va ulug'vorligi.",
    "dunyo": "Dunyo — olam, borliq, yer yuzi."
}

# ====================== START ======================
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    if referrer_id == user_id:
        referrer_id = None

    foydalanuvchi_qosh(user_id, referrer_id)

    if referrer_id:
        try:
            ref_til = foydalanuvchi_tilini_ol(referrer_id)
            await bot.send_message(referrer_id, MATNLAR[ref_til]["ref_bonus"].format(bonus=REFERRAL_BONUS))
        except:
            pass

    til = foydalanuvchi_tilini_ol(user_id)

    if not await aza_bolganmi(user_id):
        await message.answer(MATNLAR[til]["sub_text"], reply_markup=aazolik_klaviaturasi(til))
        return

    await message.answer(MATNLAR[til]["start"], reply_markup=menyu_klaviaturasi(til))


# ====================== CALLBACKLAR ======================
@dp.callback_query(lambda c: c.data.startswith("setlang_"))
async def change_language_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    yangi_til = callback.data.split("_")[1]

    foydalanuvchi_tilini_yangila(user_id, yangi_til)
    await callback.message.delete()
    await bot.send_message(user_id, MATNLAR[yangi_til]["lang_changed"], 
                         reply_markup=menyu_klaviaturasi(yangi_til))


@dp.callback_query(lambda c: c.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    til = foydalanuvchi_tilini_ol(user_id)

    if await aza_bolganmi(user_id):
        await callback.message.delete()
        await bot.send_message(user_id, MATNLAR[til]["sub_success"], reply_markup=menyu_klaviaturasi(til))
    else:
        await callback.answer(MATNLAR[til]["sub_error"], show_alert=True)


# ====================== ASOSIY XABARLAR ======================
@dp.message()
async def bot_messages(message: types.Message):
    user_id = message.from_user.id
    til = foydalanuvchi_tilini_ol(user_id)

    if not await aza_bolganmi(user_id):
        await message.answer(MATNLAR[til]["sub_text"], reply_markup=aazolik_klaviaturasi(til))
        return

    text = message.text.strip()

    # Tugmalar tekshirish
    if text == MATNLAR[til]["btn_ismlar"]:
        ismlar = ", ".join([k.capitalize() for k in ISMLAR_MANOSI.keys()])
        await message.answer(f"📚 Bazadagi ismlar:\n\n{ismlar}")

    elif text == MATNLAR[til]["btn_tasodif"]:
        tasodifiy_ism = random.choice(list(ISMLAR_MANOSI.keys()))
        mano = ISMLAR_MANOSI[tasodifiy_ism]
        await message.answer(f"🎲 Ism:\n\n📌 <b>{tasodifiy_ism.capitalize()}</b> — {mano}")

    elif text == MATNLAR[til]["btn_hamkor"]:
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        balans = foydalanuvchi_balansi(user_id)
        await message.answer(f"💰 Balans: {balans} so'm\n🔗 Link: <code>{ref_link}</code>")

    elif text == MATNLAR[til]["btn_stat"]:
        soni = foydalanuvchilar_soni()
        await message.answer(MATNLAR[til]["stat_text"].format(soni=soni))

    elif text == MATNLAR[til]["btn_ishlash"]:
        await message.answer(MATNLAR[til]["work_text"])

    elif text == MATNLAR[til]["btn_profil"]:
        balans = foydalanuvchi_balansi(user_id)
        await message.answer(MATNLAR[til]["profile_text"].format(user_id=user_id, balans=balans))

    elif text == MATNLAR[til]["btn_til"]:
        await message.answer(MATNLAR[til]["change_lang"], reply_markup=til_tanlash_klaviaturasi())

    # Ism qidirish
    else:
        # Kirill va lotin o'zgarishlaridagi maxsus belgilarni tozalaymiz
        ism_clean = text.lower().replace("’", "").replace("`", "").replace("'", "").replace("‘", "").replace("o‘", "o").replace("g‘", "g")
        if ism_clean in ISMLAR_MANOSI:
            await message.answer(f"📌 <b>{text.capitalize()}</b>\n\n{ISMLAR_MANOSI[ism_clean]}")
        else:
            await message.answer(MATNLAR[til]["not_found"])


# ====================== BOTNI ISHGA TUSHIRISH ======================
async def main():
    print("---------------------------------------")
    print(" Bot muvaffaqiyatli ishga tushdi!")
    print("---------------------------------------")
    await dp.start_polling(bot)

async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    
    runner = web.AppRunner(app)
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, '0.0.0.0', port)
    loop.run_until_complete(site.start())
    
    print("Bot ishga tushdi...")
    # DIQQAT: O'chirib tashlagan kodingiz ichidagi botni ishga tushiruvchi 
    # oxirgi qatorni aynan shu yerga yozasiz. Masalan:
    dp.run_polling(bot)