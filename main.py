import os
import json
import time
import random
from threading import Thread, Lock

from flask import Flask
import telebot
from telebot import types


# =========================================================
#                    SOZLAMALAR
# =========================================================

# MUHIM:
# Eski tokeningizni ishlatmang.
# BotFather -> /revoke orqali eski tokenni bekor qiling
# va yangi tokenni shu yerga qo'ying.

BOT_TOKEN = os.getenv("8816940858:AAEwDQ94ues00rcG1RVkNMPumQh7Xxgfowc"")

ADMIN_ID = 8753350906

# Majburiy obuna kanallari
CHANNELS = [
    "@max_films01",
    "@reklamuchun1",
    "@uzmafia02"
]

# Reklama kanali
AD_CHANNEL_URL = "https://t.me/reklamuchun1"

# VIP to'lov ma'lumotlari
CARD_NUMBER = "6262 5701 4806 4381"
CARD_OWNER = "Obidjonova M"

# Ma'lumotlarni saqlash fayli
DATA_FILE = "bot_data.json"

# Bir vaqtning o'zida fayl yozishda xavfsizlik
db_lock = Lock()


# =========================================================
#                  VIP TARIFLARI
# =========================================================

VIP_PLANS = {
    "uz": {
        "1": {"price": "15 000 so'm", "days": 30},
        "3": {"price": "22 000 so'm", "days": 90},
        "6": {"price": "35 000 so'm", "days": 180},
    },
    "ru": {
        "1": {"price": "200 руб", "days": 30},
        "3": {"price": "370 руб", "days": 90},
        "6": {"price": "450 руб", "days": 180},
    },
    "en": {
        "1": {"price": "$12", "days": 30},
        "3": {"price": "$15", "days": 90},
        "6": {"price": "$22", "days": 180},
    }
}


# =========================================================
#                 TAQIQLANGAN SO'ZLAR
# =========================================================

BANNED_WORDS = [
    "porno",
    "porn",
    "pornography",
    "sex",
    "seks",
    "uyatsiz",
    "18+",
    "xxx",
    "diniy"
]


# =========================================================
#                    BOT
# =========================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


# =========================================================
#                 MA'LUMOTLAR BAZASI
# =========================================================

default_db = {
    "users_lang": {},
    "vip_users": {},
    "banned_users": [],
    "user_states": {},
    "movies": {},
    "pending_payments": {}
}


def load_db():
    if not os.path.exists(DATA_FILE):
        return default_db.copy()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for key in default_db:
            if key not in data:
                data[key] = default_db[key]

        return data

    except Exception:
        return default_db.copy()


db = load_db()


def save_db():
    with db_lock:
        temp_file = DATA_FILE + ".tmp"

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(
                db,
                f,
                ensure_ascii=False,
                indent=2
            )

        os.replace(temp_file, DATA_FILE)


# =========================================================
#                   FLASK 24/7
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Kino Bot 24/7 ishlayapti! ✅"


@app.route("/health")
def health():
    return "OK"


def run_server():
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000))
    )


# =========================================================
#                       TILLAR
# =========================================================

TEXTS = {

    "uz": {
        "menu": "✅ <b>Asosiy menyu</b>",
        "search": "🔍 Qidirish",
        "random": "🎲 Tasodifiy",
        "recommend": "💡 Kino tavsiya qilish",
        "personal_add": "📬 Shaxsiy kino qo'shish",
        "admin_add": "🎬 Admin orqali kino qo'shish",
        "vip": "💎 VIP Obuna",
        "language": "🌐 Tilni o'zgartirish",
        "normal_add": "🎬 Oddiy video qo'shish",
        "vip_add": "💎 VIP video qo'shish",
        "sub_text": (
            "✨ <b>Botdan foydalanish uchun quyidagi kanallarga "
            "obuna bo'ling:</b>"
        ),
        "subscribe": "📢 Kanalga obuna bo'lish",
        "check": "🔄 Tekshirish",
        "back": "🔙 Orqaga",
        "send_code": "🔢 Kino kodini yuboring:",
        "not_found": "❌ Bu kod bo'yicha kino topilmadi.",
        "no_movies": "❌ Hozircha bazada kino yo'q.",
    },

    "ru": {
        "menu": "✅ <b>Главное меню</b>",
        "search": "🔍 Поиск",
        "random": "🎲 Случайный",
        "recommend": "💡 Рекомендовать фильм",
        "personal_add": "📬 Добавить фильм",
        "admin_add": "🎬 Добавить через админа",
        "vip": "💎 VIP Подписка",
        "language": "🌐 Сменить язык",
        "normal_add": "🎬 Добавить обычное видео",
        "vip_add": "💎 Добавить VIP видео",
        "sub_text": (
            "✨ <b>Чтобы пользоваться ботом, "
            "подпишитесь на каналы:</b>"
        ),
        "subscribe": "📢 Подписаться",
        "check": "🔄 Проверить",
        "back": "🔙 Назад",
        "send_code": "🔢 Отправьте код фильма:",
        "not_found": "❌ Фильм с таким кодом не найден.",
        "no_movies": "❌ В базе пока нет фильмов.",
    },

    "en": {
        "menu": "✅ <b>Main Menu</b>",
        "search": "🔍 Search",
        "random": "🎲 Random",
        "recommend": "💡 Recommend Film",
        "personal_add": "📬 Add Film",
        "admin_add": "🎬 Add via Admin",
        "vip": "💎 Premium",
        "language": "🌐 Change Language",
        "normal_add": "🎬 Add normal video",
        "vip_add": "💎 Add VIP video",
        "sub_text": (
            "✨ <b>Please subscribe to the channels "
            "to use the bot:</b>"
        ),
        "subscribe": "📢 Subscribe",
        "check": "🔄 Check",
        "back": "🔙 Back",
        "send_code": "🔢 Send movie code:",
        "not_found": "❌ Movie with this code was not found.",
        "no_movies": "❌ There are no movies in the database.",
    }
}


def get_lang(user_id):
    return db["users_lang"].get(str(user_id), "uz")


def text(user_id, key):
    lang = get_lang(user_id)
    return TEXTS[lang].get(key, key)


# =========================================================
#                    VIP TEKSHIRISH
# =========================================================

def is_vip(user_id):
    user = db["vip_users"].get(str(user_id))

    if not user:
        return False

    expires_at = user.get("expires_at", 0)

    if time.time() >= expires_at:
        db["vip_users"].pop(str(user_id), None)
        save_db()
        return False

    return True


def activate_vip(user_id, period):
    lang = get_lang(user_id)

    if lang not in VIP_PLANS:
        lang = "uz"

    plan = VIP_PLANS[lang].get(period)

    if not plan:
        plan = VIP_PLANS["uz"]["1"]

    expires_at = int(time.time()) + (
        plan["days"] * 24 * 60 * 60
    )

    db["vip_users"][str(user_id)] = {
        "period": period,
        "expires_at": expires_at,
        "activated_at": int(time.time())
    }

    save_db()


# =========================================================
#                 MAJBURIY OBUNA
# =========================================================

def check_subscription(user_id):

    # Admin uchun majburiy obuna shart emas
    if user_id == ADMIN_ID:
        return True

    # VIP foydalanuvchiga ham majburiy obuna kerak emas
    if is_vip(user_id):
        return True

    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)

            if member.status not in [
                "member",
                "administrator",
                "creator"
            ]:
                return False

        except Exception:
            return False

    return True


def subscription_keyboard(user_id):

    lang = get_lang(user_id)

    markup = types.InlineKeyboardMarkup()

    for channel in CHANNELS:

        channel_name = channel.replace("@", "")

        markup.add(
            types.InlineKeyboardButton(
                TEXTS[lang]["subscribe"],
                url=f"https://t.me/{channel_name}"
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            TEXTS[lang]["check"],
            callback_data="check_sub"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            TEXTS[lang]["vip"],
            callback_data="vip_menu"
        )
    )

    return markup


# =========================================================
#                   ASOSIY MENU
# =========================================================

def show_main_menu(chat_id, user_id):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        text(user_id, "search"),
        text(user_id, "random")
    )

    markup.row(
        text(user_id, "recommend"),
        text(user_id, "personal_add")
    )

    markup.row(
        text(user_id, "admin_add"),
        text(user_id, "vip")
    )

    markup.row(
        text(user_id, "language")
    )

    # Faqat admin ko'radi
    if user_id == ADMIN_ID:
        markup.row(
            text(user_id, "normal_add"),
            text(user_id, "vip_add")
        )

    bot.send_message(
        chat_id,
        text(user_id, "menu"),
        reply_markup=markup
    )


# =========================================================
#                       START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id

    if str(user_id) in db["banned_users"]:
        bot.send_message(
            message.chat.id,
            "❌ Siz botdan bloklangansiz."
        )
        return

    if not check_subscription(user_id):

        bot.send_message(
            message.chat.id,
            text(user_id, "sub_text"),
            reply_markup=subscription_keyboard(user_id)
        )

        return

    show_main_menu(
        message.chat.id,
        user_id
    )


# =========================================================
#              MAJBURIY OBUNANI TEKSHIRISH
# =========================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "check_sub"
)
def check_sub_callback(call):

    user_id = call.from_user.id

    if check_subscription(user_id):

        bot.answer_callback_query(
            call.id,
            "Obuna tasdiqlandi! ✅"
        )

        try:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass

        show_main_menu(
            call.message.chat.id,
            user_id
        )

    else:

        bot.answer_callback_query(
            call.id,
            "Hali barcha kanallarga obuna bo'lmagansiz! ❌",
            show_alert=True
        )


# =========================================================
#                     TIL
# =========================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["language"],
        TEXTS["ru"]["language"],
        TEXTS["en"]["language"]
    ]
)
def language_menu(message):

    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "🇺🇿 O'zbekcha",
            callback_data="lang_uz"
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            "🇷🇺 Русский",
            callback_data="lang_ru"
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            "🇬🇧 English",
            callback_data="lang_en"
        )
    )

    bot.send_message(
        message.chat.id,
        "🌐 Tilni tanlang:",
        reply_markup=markup
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("lang_")
)
def language_callback(call):

    lang = call.data.split("_")[1]
    user_id = call.from_user.id

    if lang not in ["uz", "ru", "en"]:
        return

    db["users_lang"][str(user_id)] = lang
    save_db()

    bot.answer_callback_query(
        call.id,
        "Til o'zgartirildi! ✅"
    )

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except Exception:
        pass

    show_main_menu(
        call.message.chat.id,
        user_id
    )


# =========================================================
#                    VIP MENU
# =========================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["vip"],
        TEXTS["ru"]["vip"],
        TEXTS["en"]["vip"]
    ]
)
def vip_menu_message(message):

    show_vip_menu(
        message.chat.id,
        message.from_user.id
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "vip_menu"
)
def vip_menu_callback(call):

    show_vip_menu(
        call.message.chat.id,
        call.from_user.id
    )

    bot.answer_callback_query(call.id)


def show_vip_menu(chat_id, user_id):

    lang = get_lang(user_id)

    markup = types.InlineKeyboardMarkup()

    plans = VIP_PLANS[lang]

    markup.add(
        types.InlineKeyboardButton(
            f"1 oy — {plans['1']['price']}",
            callback_data=f"pay_{lang}_1"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            f"3 oy — {plans['3']['price']}",
            callback_data=f"pay_{lang}_3"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            f"6 oy — {plans['6']['price']}",
            callback_data=f"pay_{lang}_6"
        )
    )

    if is_vip(user_id):

        vip = db["vip_users"][str(user_id)]

        expires = time.strftime(
            "%d.%m.%Y %H:%M",
            time.localtime(vip["expires_at"])
        )

        bot.send_message(
            chat_id,
            f"💎 <b>Sizda VIP faol.</b>\n\n"
            f"⏳ Tugash vaqti: <b>{expires}</b>",
            reply_markup=markup
        )

    else:

        bot.send_message(
            chat_id,
            "💎 <b>VIP Obuna</b>\n\n"
            "Tarifni tanlang:",
            reply_markup=markup
        )


# =========================================================
#                 VIP TO'LOV MA'LUMOTI
# =========================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("pay_")
)
def payment_details(call):

    parts = call.data.split("_")

    lang = parts[1]
    period = parts[2]

    if lang not in VIP_PLANS:
        lang = "uz"

    plan = VIP_PLANS[lang].get(period)

    if not plan:
        bot.answer_callback_query(
            call.id,
            "Tarif topilmadi.",
            show_alert=True
        )
        return

    user_id = call.from_user.id

    db["user_states"][str(user_id)] = {
        "step": "waiting_payment",
        "period": period,
        "lang": lang
    }

    save_db()

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        f"💎 <b>VIP — {period} oy</b>\n\n"
        f"💰 Narxi: <b>{plan['price']}</b>\n\n"
        f"💳 <b>Karta:</b>\n"
        f"<code>{CARD_NUMBER}</code>\n\n"
        f"👤 <b>Karta egasi:</b>\n"
        f"{CARD_OWNER}\n\n"
        f"📸 To'lovni amalga oshirgach, "
        f"<b>chek/skrinshotni shu botga yuboring.</b>\n\n"
        f"Admin chekni tekshiradi.\n"
        f"✅ Tasdiqlansa VIP faollashadi.\n"
        f"❌ Rad etilsa VIP berilmaydi."
    )


# =========================================================
#                  QIDIRISH
# =========================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["search"],
        TEXTS["ru"]["search"],
        TEXTS["en"]["search"]
    ]
)
def search_movie(message):

    user_id = message.from_user.id

    db["user_states"][str(user_id)] = {
        "step": "search"
    }

    save_db()

    bot.send_message(
        message.chat.id,
        text(user_id, "send_code")
    )


# =========================================================
#                 RANDOM KINO
# =========================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["random"],
        TEXTS["ru"]["random"],
        TEXTS["en"]["random"]
    ]
)
def random_movie(message):

    user_id = message.from_user.id

    if not db["movies"]:

        bot.send_message(
            message.chat.id,
            text(user_id, "no_movies")
        )

        return

    available = []

    vip = is_vip(user_id)

    for code, movie in db["movies"].items():

        if movie.get("type") == "normal":
            available.append((code, movie))

        elif movie.get("type") == "vip" and vip:
            available.append((code, movie))

    if not available:

        bot.send_message(
            message.chat.id,
            "❌ Siz uchun mavjud kino topilmadi."
        )

        return

    code, movie = random.choice(available)

    send_movie(
        message.chat.id,
        user_id,
        code,
        movie
    )


# =========================================================
#                    VIDEO YUBORISH
# =========================================================

def send_movie(chat_id, user_id, code, movie):

    movie_type = movie.get("type", "normal")

    if movie_type == "vip" and not is_vip(user_id):

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "💎 VIP Obuna",
                callback_data="vip_menu"
            )
        )

        bot.send_message(
            chat_id,
            "🔒 Bu kino faqat VIP foydalanuvchilar uchun.",
            reply_markup=markup
        )

        return

    caption = (
        f"🎬 <b>Kino kodi:</b> <code>{code}</code>\n\n"
        f"Tomosha qiling! 🍿"
    )

    bot.send_video(
        chat_id,
        movie["file_id"],
        caption=caption
    )

    # VIP reklamasiz
    if not is_vip(user_id):

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "📢 Reklama",
                url=AD_CHANNEL_URL
            )
        )

        bot.send_message(
            chat_id,
            "📢 Reklama hamkorimiz:",
            reply_markup=markup
        )


# =========================================================
#                KINO TAVSIYA QILISH
# =========================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["recommend"],
        TEXTS["ru"]["recommend"],
        TEXTS["en"]["recommend"]
    ]
)
def recommend_movie(message):

    user_id = message.from_user.id

    db["user_states"][str(user_id)] = {
        "step": "recommend"
    }

    save_db()

    bot.send_message(
        message.chat.id,
        "✍️ Ko'rmoqchi bo'lgan kino nomini yozing:"
    )


# =========================================================
#               SHAXSIY KINO QO'SHISH
# =========================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["personal_add"],
        TEXTS["ru"]["personal_add"],
        TEXTS["en"]["personal_add"]
    ]
)
def personal_add_start(message):

    user_id = message.from_user.id

    db["user_states"][str(user_id)] = {
        "step": "personal_wait_video"
    }

    save_db()

    bot.send_message(
        message.chat.id,
        "📤 Kino videosini yuboring:"
    )


# =========================================================
#              ADMIN ORQALI KINO QO'SHISH
# =========================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["admin_add"],
        TEXTS["ru"]["admin_add"],
        TEXTS["en"]["admin_add"]
    ]
    
