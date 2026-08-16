import os
import sqlite3
import random
from datetime import datetime, timedelta

import telebot
from telebot import types
from flask import Flask
from threading import Thread


# ============================================================
# SOZLAMALAR
# ============================================================

TOKEN = "8816940858:AAEwDQ94ues00rcG1RVkNMPumQh7Xxgfowc"

ADMIN_ID = 8753350906

# Majburiy obuna kanallari
CHANNELS = [
    "@max_films01",
    "@reklamuchun1",
    "@uzmafia02"
]

# Reklama kanali
AD_CHANNEL = "https://t.me/reklamuchun1"

# To'lov karta raqamini shu yerga o'zingiz qo'ying
CARD_NUMBER = "BU_YERGA_KARTA_RAQAMINI_QOYING"

CARD_OWNER = "Obidjonova M"


bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


# ============================================================
# FLASK — 24/7 UCHUN
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Kino Bot 24/7 ishlayapti! ✅"


def run_server():
    app.run(host="0.0.0.0", port=10000)


Thread(target=run_server, daemon=True).start()


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "kino_bot.db"


def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            lang TEXT DEFAULT 'uz',
            banned INTEGER DEFAULT 0,
            vip_until TEXT DEFAULT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            movie_type TEXT DEFAULT 'normal'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pending_movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            video_id TEXT,
            code TEXT,
            movie_type TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS vip_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            period INTEGER,
            status TEXT DEFAULT 'waiting'
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ============================================================
# USERLAR
# ============================================================

def add_user(user):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, lang, banned)
        VALUES (?, ?, 'uz', 0)
    """, (
        user.id,
        user.username or ""
    ))

    cur.execute("""
        UPDATE users
        SET username=?
        WHERE user_id=?
    """, (
        user.username or "",
        user.id
    ))

    conn.commit()
    conn.close()


def get_lang(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT lang FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    return row["lang"] if row else "uz"


def set_lang(user_id, lang):
    conn = get_db()
    conn.execute(
        "UPDATE users SET lang=? WHERE user_id=?",
        (lang, user_id)
    )
    conn.commit()
    conn.close()


def is_banned(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT banned FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    return bool(row and row["banned"])


def ban_user(user_id):
    conn = get_db()
    conn.execute(
        "UPDATE users SET banned=1 WHERE user_id=?",
        (user_id,)
    )
    conn.commit()
    conn.close()


# ============================================================
# VIP TIZIMI
# ============================================================

def get_vip_until(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT vip_until FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    if not row or not row["vip_until"]:
        return None

    try:
        return datetime.fromisoformat(row["vip_until"])
    except:
        return None


def is_vip(user_id):
    if user_id == ADMIN_ID:
        return True

    vip_until = get_vip_until(user_id)

    if not vip_until:
        return False

    if datetime.now() >= vip_until:
        # VIP muddati tugadi
        conn = get_db()
        conn.execute(
            "UPDATE users SET vip_until=NULL WHERE user_id=?",
            (user_id,)
        )
        conn.commit()
        conn.close()
        return False

    return True


def activate_vip(user_id, months):
    now = datetime.now()
    old_until = get_vip_until(user_id)

    if old_until and old_until > now:
        start = old_until
    else:
        start = now

    # Oylarni taxminan 30 kun hisoblaymiz
    new_until = start + timedelta(days=30 * months)

    conn = get_db()
    conn.execute(
        "UPDATE users SET vip_until=? WHERE user_id=?",
        (new_until.isoformat(), user_id)
    )
    conn.commit()
    conn.close()

    return new_until


# ============================================================
# MAJBURIY OBUNA
# ============================================================

def check_subscription(user_id):
    if user_id == ADMIN_ID:
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


def subscription_menu(user_id):
    lang = get_lang(user_id)

    texts = {
        "uz": "✨ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
        "ru": "✨ Для использования бота подпишитесь на каналы:",
        "en": "✨ Please subscribe to the channels to use the bot:"
    }

    buttons = {
        "uz": "📢 Kanalga obuna bo'lish",
        "ru": "📢 Подписаться",
        "en": "📢 Subscribe"
    }

    check_text = {
        "uz": "🔄 Tekshirish",
        "ru": "🔄 Проверить",
        "en": "🔄 Check"
    }

    vip_text = {
        "uz": "💎 VIP Obuna",
        "ru": "💎 VIP Подписка",
        "en": "💎 VIP Subscription"
    }

    markup = types.InlineKeyboardMarkup()

    for channel in CHANNELS:
        markup.add(
            types.InlineKeyboardButton(
                buttons[lang],
                url=f"https://t.me/{channel.replace('@', '')}"
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            check_text[lang],
            callback_data="check_sub"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            vip_text[lang],
            callback_data="vip_menu"
        )
    )

    return texts[lang], markup


# ============================================================
# MATNLAR
# ============================================================

TEXTS = {
    "uz": {
        "menu": "✅ Asosiy menyu:",
        "search": "🔍 Qidirish",
        "random": "🎲 Tasodifiy",
        "recommend": "💡 Kino tavsiya qilish",
        "personal": "📬 Shaxsiy kino qo'shish",
        "admin": "🎬 Admin orqali kino qo'shish",
        "vip": "💎 Premium Obuna",
        "lang": "🌐 Tilni o'zgartirish",
        "normal": "🎬 Oddiy video qo'shish",
        "vip_video": "💎 VIP video qo'shish"
    },

    "ru": {
        "menu": "✅ Главное меню:",
        "search": "🔍 Поиск",
        "random": "🎲 Случайный",
        "recommend": "💡 Рекомендовать фильм",
        "personal": "📬 Добавить свой фильм",
        "admin": "🎬 Добавить через админа",
        "vip": "💎 VIP Подписка",
        "lang": "🌐 Сменить язык",
        "normal": "🎬 Добавить обычное видео",
        "vip_video": "💎 Добавить VIP видео"
    },

    "en": {
        "menu": "✅ Main Menu:",
        "search": "🔍 Search",
        "random": "🎲 Random",
        "recommend": "💡 Recommend Film",
        "personal": "📬 Add Personal Film",
        "admin": "🎬 Add via Admin",
        "vip": "💎 Premium Subscription",
        "lang": "🌐 Change Language",
        "normal": "🎬 Add Normal Video",
        "vip_video": "💎 Add VIP Video"
    }
}


def t(user_id, key):
    return TEXTS[get_lang(user_id)][key]


# ============================================================
# ASOSIY MENU
# ============================================================

def show_main_menu(chat_id, user_id):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        t(user_id, "search"),
        t(user_id, "random")
    )

    markup.row(
        t(user_id, "recommend"),
        t(user_id, "personal")
    )

    markup.row(
        t(user_id, "admin"),
        t(user_id, "vip")
    )

    markup.row(
        t(user_id, "lang")
    )

    if user_id == ADMIN_ID:
        markup.row(
            t(user_id, "normal"),
            t(user_id, "vip_video")
        )

    bot.send_message(
        chat_id,
        t(user_id, "menu"),
        reply_markup=markup
    )


# ============================================================
# START
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    add_user(message.from_user)

    if is_banned(user_id):
        bot.send_message(
            message.chat.id,
            "❌ Siz botdan bloklangansiz."
        )
        return

    if not check_subscription(user_id):
        text, markup = subscription_menu(user_id)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=markup
        )
        return

    show_main_menu(
        message.chat.id,
        user_id
    )


# ============================================================
# OBUNANI TEKSHIRISH
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "check_sub"
)
def check_sub_callback(call):
    user_id = call.from_user.id

    if check_subscription(user_id):
        bot.answer_callback_query(
            call.id,
            "✅ Barcha kanallarga obuna bo'lgansiz!"
        )

        try:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
        except:
            pass

        show_main_menu(
            call.message.chat.id,
            user_id
        )

    else:
        bot.answer_callback_query(
            call.id,
            "❌ Hali barcha kanallarga obuna bo'lmagansiz!",
            show_alert=True
        )


# ============================================================
# VIP MENU
# ============================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["vip"],
        TEXTS["ru"]["vip"],
        TEXTS["en"]["vip"]
    ]
)
def vip_menu_message(message):
    send_vip_menu(
        message.chat.id,
        message.from_user.id
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "vip_menu"
)
def vip_menu_callback(call):
    send_vip_menu(
        call.message.chat.id,
        call.from_user.id
    )

    bot.answer_callback_query(call.id)


def send_vip_menu(chat_id, user_id):
    lang = get_lang(user_id)

    markup = types.InlineKeyboardMarkup()

    if lang == "uz":

        markup.add(
            types.InlineKeyboardButton(
                "1 oylik — 15,000 so'm",
                callback_data="pay_1"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "3 oylik — 22,000 so'm",
                callback_data="pay_3"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "6 oylik — 35,000 so'm",
                callback_data="pay_6"
            )
        )

        text = "💎 <b>Premium Obuna</b>\n\nTarifni tanlang:"

    elif lang == "ru":

        markup.add(
            types.InlineKeyboardButton(
                "1 месяц — 200 руб",
                callback_data="pay_1"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "3 месяца — 370 руб",
                callback_data="pay_3"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "6 месяцев — 450 руб",
                callback_data="pay_6"
            )
        )

        text = "💎 <b>VIP Подписка</b>\n\nВыберите тариф:"

    else:

        markup.add(
            types.InlineKeyboardButton(
                "1 Month — $12",
                callback_data="pay_1"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "3 Months — $15",
                callback_data="pay_3"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "6 Months — $22",
                callback_data="pay_6"
            )
        )

        text = "💎 <b>Premium Subscription</b>\n\nChoose your plan:"

    bot.send_message(
        chat_id,
        text,
        reply_markup=markup
    )


# ============================================================
# TO'LOV
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("pay_")
)
def payment_selected(call):

    user_id = call.from_user.id
    period = int(call.data.split("_")[1])

    lang = get_lang(user_id)

    prices = {
        "uz": {
            1: "15,000 so'm",
            3: "22,000 so'm",
            6: "35,000 so'm"
        },
        "ru": {
            1: "200 руб",
            3: "370 руб",
            6: "450 руб"
        },
        "en": {
            1: "$12",
            3: "$15",
            6: "$22"
        }
    }

    price = prices[lang][period]

    text = (
        f"💎 <b>{period} oylik VIP</b>\n"
        f"💰 Narx: <b>{price}</b>\n\n"
        f"💳 <b>Karta:</b>\n"
        f"<code>{</CARD_NUMBER} = "6262 5701 4806 4381">\n\n"
        f"👤 <b>Karta egasi:</b> {"Obidjonova M"}\n\n"
        f"📸 To'lovni amalga oshirgach, "
        f"chek/skrinshotni shu botga yuboring.\n\n"
        f"Admin tekshiradi. Tasdiqlansa VIP avtomatik faollashadi. ✅"
    )

    conn = get_db()

    conn.execute(
        """
        INSERT INTO vip_payments
        (user_id, username, period, status)
        VALUES (?, ?, ?, 'waiting')
        """,
        (
            user_id,
            call.from_user.username or "",
            period
        )
    )

    conn.commit()
    conn.close()

    bot.send_message(
        call.message.chat.id,
        text
    )

    bot.answer_callback_query(call.id)


# ============================================================
# HOLATLAR
# ============================================================

user_states = {}


# ============================================================
# TIL
# ============================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["lang"],
        TEXTS["ru"]["lang"],
        TEXTS["en"]["lang"]
    ]
)
def language_menu(message):

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "🇺🇿 O'zbekcha",
            callback_data="lang_uz"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "🇷🇺 Русский",
            callback_data="lang_ru"
        )
    )

    markup.add(
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
def language_selected(call):

    lang = call.data.split("_")[1]

    set_lang(
        call.from_user.id,
        lang
    )

    bot.answer_callback_query(
        call.id,
        "✅ Til o'zgartirildi!"
    )

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

    show_main_menu(
        call.message.chat.id,
        call.from_user.id
    )


# ============================================================
# ADMIN — ODDIY VIDEO
# ============================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["normal"],
        TEXTS["ru"]["normal"],
        TEXTS["en"]["normal"]
    ]
)
def admin_normal_video(message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[ADMIN_ID] = {
        "step": "admin_video",
        "type": "normal"
    }

    bot.send_message(
        message.chat.id,
        "🎬 Oddiy videoni yuboring:"
    )


# ============================================================
# ADMIN — VIP VIDEO
# ============================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["vip_video"],
        TEXTS["ru"]["vip_video"],
        TEXTS["en"]["vip_video"]
    ]
)
def admin_vip_video(message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[ADMIN_ID] = {
        "step": "admin_video",
        "type": "vip"
    }

    bot.send_message(
        message.chat.id,
        "💎 VIP videoni yuboring:"
    )


# ============================================================
# ADMIN ORQALI KINO
# ============================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["admin"],
        TEXTS["ru"]["admin"],
        TEXTS["en"]["admin"]
    ]
)
def admin_add_start(message):

    user_states[message.from_user.id] = {
        "step": "user_admin_video"
    }

    bot.send_message(
        message.chat.id,
        "📤 Adminga yuborish uchun videoni yuboring:"
    )


# ============================================================
# SHAXSIY KINO
# ============================================================

@bot.message_handler(
    func=lambda m: m.text in [
        TEXTS["uz"]["personal"],
        TEXTS["ru"]["personal"],
        TEXTS["en"]["personal"]
    ]
)
def personal_start(message):

    user_states[message.from_user.id] = {
        "step": "personal_video"
    }

    bot.send_message(
        message.chat.id,
        "📤 Shaxsiy kino videosini yuboring:"
    )


# ============================================================
# TAQIQLANGAN SO'ZLAR
# ============================================================

BANNED_WORDS = [
    "porno",
    "porn",
    "sex",
    "xxx",
    "uyatsiz",
    "diniy"
]


def contains_banned(text):
    text = (text or "").lower()

    for word in BANNED_WORDS:
        if word in text:
            return True

    return False


# ============================================================
# ADMIN TO'LOV CHEKINI QABUL QILISH
# ============================================================

@bot.message_handler(
    content_types=["photo"]
)
def handle_photo(message):

    user_id = message.from_user.id

    add_user(message.from_user)

    if is_banned(user_id):
        return

    state = user_states.get(user_id)

    if state == "waiting_payment":
        pass

    # Oxirgi waiting paymentni topamiz
    conn = get_db()

    payment = conn.execute(
        """
        SELECT *
        FROM vip_payments
        WHERE user_id=?
        AND status='waiting'
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    if not payment:
        bot.reply_to(
            message,
            "❌ Avval VIP tarifini tanlang."
        )
        return

    # Admin uchun chek
    markup = types.InlineKeyboa
