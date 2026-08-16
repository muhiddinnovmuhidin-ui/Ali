import os
from flask import Flask
from threading import Thread
import telebot
from telebot import types

TOKEN = "8816940858:AAEwDQ94ues00rcG1RVkNMPumQh7Xxgfowc"
ADMIN_ID = 8816940858

CHANNELS = ["@max_films01", "@reklamuchun1", "@uzmafia02"]

bot = telebot.TeleBot(TOKEN)

users_lang = {}      
vip_users = {}       
banned_users = set() 
user_states = {}     
movies_db = {}       

BANNED_WORDS = ["porno", "sex", "sins", "uyatsiz", "diniy"]

app = Flask('')
@app.route('/')
def home():
    return "Kino Bot 24/7 ishlayapti!"

def run():
    app.run(host='0.0.0.0', port=10000)

Thread(target=run).start()

def check_sub(user_id):
    if user_id == ADMIN_ID:
        return True
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

TEXTS = {
    'uz': {
        'menu': "✅ Asosiy menyu:",
        'sub_text': "✨ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
        'sub_btn': "📢 Kanalga obuna bo'lish",
        'check': "🔄 Tekshirish",
        'vip_menu': "💎 Premium Obuna",
        'search': "🔍 Qidirish",
        'random': "🎲 Tasodifiy",
        'recommend': "💡 Kino tavsiya qilish",
        'personal_add': "📬 Shaxsiy kino qo'shish",
        'admin_add': "🎬 Admin orqali kino qo'shish",
        'lang_change': "🌐 Tilni o'zgartirish",
        'oddiy_video': "🎬 Oddiy video qo'shish",
        'vip_video': "💎 VIP video qo'shish"
    },
    'ru': {
        'menu': "✅ Главное меню:",
        'sub_text': "✨ Для использования бота подпишитесь на каналы:",
        'sub_btn': "📢 Подписаться",
        'check': "🔄 Проверить",
        'vip_menu': "💎 VIP Подписка",
        'search': "🔍 Поиск",
        'random': "🎲 Случайный",
        'recommend': "💡 Рекомендовать фильм",
        'personal_add': "📬 Добавить фильм (Личный)",
        'admin_add': "🎬 Добавить через админа",
        'lang_change': "🌐 Сменить язык",
        'oddiy_video': "🎬 Добавить обычное видео",
        'vip_video': "💎 Добавить VIP видео"
    },
    'en': {
        'menu': "✅ Main Menu:",
        'sub_text': "✨ Please subscribe to the channels to use the bot:",
        'sub_btn': "📢 Subscribe",
        'check': "🔄 Check",
        'vip_menu': "💎 Premium Subscription",
        'search': "🔍 Search",
        'random': "🎲 Random",
        'recommend': "💡 Recommend Film",
        'personal_add': "📬 Add Film (Personal)",
        'admin_add': "🎬 Add via Admin",
        'lang_change': "🌐 Change Language",
        'oddiy_video': "🎬 Add normal video",
        'vip_video': "💎 Add VIP video"
    }
}

def get_text(user_id, key):
    lang = users_lang.get(user_id, 'uz')
    return TEXTS.get(lang, TEXTS['uz']).get(key, key)

def show_main_menu(chat_id, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(get_text(user_id, 'search'), get_text(user_id, 'random'))
    markup.row(get_text(user_id, 'recommend'), get_text(user_id, 'personal_add'))
    markup.row(get_text(user_id, 'admin_add'), get_text(user_id, 'vip_menu'))
    markup.row(get_text(user_id, 'lang_change'))
    
    if user_id == ADMIN_ID:
        markup.row(get_text(user_id, 'oddiy_video'), get_text(user_id, 'vip_video'))
        
    bot.send_message(chat_id, get_text(user_id, 'menu'), reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in banned_users:
        bot.send_message(message.chat.id, "❌ Siz botdan bloklangansiz!")
        return

    if user_id not in vip_users and not check_sub(user_id):
        lang = users_lang.get(user_id, 'uz')
        markup = types.InlineKeyboardMarkup()
        for ch in CHANNELS:
            markup.add(types.InlineKeyboardButton(TEXTS[lang]['sub_btn'], url=f"https://t.me/{ch.replace('@', '')}"))
        markup.add(types.InlineKeyboardButton(TEXTS[lang]['check'], callback_data="check_subscription"))
        markup.add(types.InlineKeyboardButton(TEXTS[lang]['vip_menu'], callback_data="btn_vip_menu"))
        
        bot.send_message(message.chat.id, TEXTS[lang]['sub_text'], reply_markup=markup)
        return

    show_main_menu(message.chat.id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_sub(call):
    user_id = call.from_user.id
    if check_sub(user_id):
        bot.answer_callback_query(call.id, "Rahmat! Obuna tasdiqlandi ✅")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_main_menu(call.message.chat.id, user_id)
    else:
        bot.answer_callback_query(call.id, "Siz hali hamma kanalga obuna bo'lmadingiz! ❌", show_alert=True)

# --- TILNI O'ZGARTIRISH ---
@bot.message_handler(func=lambda message: message.text in [TEXTS['uz']['lang_change'], TEXTS['ru']['lang_change'], TEXTS['en']['lang_change']])
def change_language_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("O'zbekcha 🇺🇿", callback_data="lang_uz"),
        types.InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
        types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")
    )
    bot.send_message(message.chat.id, "Tilni tanlang / Выберите язык / Choose language:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def lang_select(call):
    user_id = call.from_user.id
    lang = call.data.split("_")[1]
    users_lang[user_id] = lang
    bot.answer_callback_query(call.id, "Til o'zgartirildi! ✅")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    show_main_menu(call.message.chat.id, user_id)

# --- VIP OBUNA ---
@bot.message_handler(func=lambda message: message.text in [TEXTS['uz']['vip_menu'], TEXTS['ru']['vip_menu'], TEXTS['en']['vip_menu']])
def vip_subscription_menu_msg(message):
    vip_subscription_menu(message)

@bot.callback_query_handler(func=lambda call: call.data == "btn_vip_menu")
def vip_subscription_menu_call(call):
    vip_subscription_menu(call)

def vip_subscription_menu(event):
    chat_id = event.message.chat.id if hasattr(event, 'message') else event.chat.id
    user_id = event.from_user.id
    lang = users_lang.get(user_id, 'uz')
    
    markup = types.InlineKeyboardMarkup()
    if lang == 'ru':
        markup.add(types.InlineKeyboardButton("1 месяц — 300 руб", callback_data="pay_ru_1"))
        markup.add(types.InlineKeyboardButton("3 месяца — 400 руб", callback_data="pay_ru_3"))
        markup.add(types.InlineKeyboardButton("6 месяцев — 450 руб", callback_data="pay_ru_6"))
        text = "💎 **VIP Подписка**\nВыберите тариф:"
    elif lang == 'en':
        markup.add(types.InlineKeyboardButton("1 Month — $12", callback_data="pay_en_1"))
        markup.add(types.InlineKeyboardButton("3 Months — $15", callback_data="pay_en_3"))
        markup.add(types.InlineKeyboardButton("6 Months — $22", callback_data="pay_en_6"))
        text = "💎 **Premium Subscription**\nChoose your plan:"
    else:
        markup.add(types.InlineKeyboardButton("1 oylik — 15,000 so'm", callback_data="pay_uz_1"))
        markup.add(types.InlineKeyboardButton("3 oylik — 20,000 so'm", callback_data="pay_uz_3"))
        markup.add(types.InlineKeyboardButton("6 oylik — 35,000 so'm", callback_data="pay_uz_6"))
        text = "💎 **Premium Obuna**\nTarifni tanlang:"

    if hasattr(event, 'message') and not isinstance(event, types.CallbackQuery):
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def vip_payment_details(call):
    data_parts = call.data.split("_")
    lang, period = data_parts[1], data_parts[2]
    
    prices = {
        ("uz", "1"): "15,000 so'm", ("uz", "3"): "20,000 so'm", ("uz", "6"): "35,000 so'm",
        ("ru", "1"): "300 рубл", ("ru", "3"): "400 рубл", ("ru", "6"): "450 рубл",
        ("en", "1"): "12 dollar", ("en", "3"): "15 dollar", ("en", "6"): "22 dollar"
    }
    price = prices.get((lang, period), "15,000 so'm")
    
    text = (
        f"💎 **Tarif:** {period} oylik ({price})\n\n"
        f"💳 **Karta raqam:** `6262 5701 4806 4381`\n"
        f"👤 **Karta egasi:** Obidjonova M\n\n"
        f"📸 Pulni o'tkazgach, to'lov chekining **skrinshotini** shu botga yuboring. Admin tasdiqlagach VIP obuna avtomatik ochiladi!"
    )
    user_states[call.from_user.id] = f"waiting_for_check_{period}"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

# --- QOLGAN TUGMALAR ---
@bot.message_handler(func=lambda message: message.text in [TEXTS['uz']['recommend'], TEXTS['ru']['recommend'], TEXTS['en']['recommend']])
def recommend_movie(message):
    user_states[message.from_user.id] = "recommending_movie"
    bot.send_message(message.chat.id, "✍️ Ko'rmoqchi bo'lgan kinosingiz nomini yozib yuboring, adminga yuboramiz:")

@bot.message_handler(func=lambda message: message.text in [TEXTS['uz']['personal_add'], TEXTS['ru']['personal_add'], TEXTS['en']['personal_add']])
def personal_add_movie(message):
    user_states[message.from_user.id] = "personal_add_video"
    bot.send_message(message.chat.id, "📤 Shaxsiy kino videosini yuboring:")

@bot.message_handler(func=lambda message: message.text in [TEXTS['uz']['admin_add'], TEXTS['ru']['admin_add'], TEXTS['en']['admin_add']])
def admin_add_movie(message):
    user_states[message.from_user.id] = "admin_add_video"
    bot.send_message(message.chat.id, "📤 Adminga yuborish uchun kino videosini yuboring:")

@bot.message_handler(func=lambda message: message.text in [TEXTS['uz']['random'], TEXTS['ru']['random'], TEXTS['en']['random']])
def random_movie(message):
    if not movies_db:
        bot.send_message(message.chat.id, "❌ Hozircha bazada kinolar yo'q.")
    else:
        import random
        code = random.choice(list(movies_db.keys()))
        video_id = movies_db[code]
        bot.send_video(message.chat.id, video_id, caption=f"🎲 Tasodifiy kino (Kodi: `{code}`)", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text in [TEXTS['uz']['search'], TEXTS['ru']['search'], TEXTS['en']['search']])
def search_hint(message):
    bot.send_message(message.chat.id, "🔎 Kino topish uchun kino **kodini** yuboring (masalan: `1`, `7` yoki `m1`):", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text in [TEXTS['uz']['oddiy_video'], TEXTS['ru']['oddiy_video'], TEXTS['en']['oddiy_video']])
def admin_oddiy_start(message):
    if message.from_user.id == ADMIN_ID:
        user_states[message.from_user.id] = {"step": "admin_direct_wait_video", "type": "oddiy"}
        bot.send_message(message.chat.id, "📤 Oddiy videoni yuboring:")

@bot.message_handler(func=lambda message: message.text in [TEXTS['uz']['vip_video'], TEXTS['ru']['vip_video'], TEXTS['en']['vip_video']])
def admin_vip_start(message):
    if message.from_user.id == ADMIN_ID:
        user_states[message.from_user.id] = {"step": "admin_direct_wait_video", "type": "vip"}
        bot.send_message(message.chat.id, "📤 VIP videoni yuboring:")

# --- XABARLARNI QAYTA ISHLASH ---
@bot.message_handler(content_types=['text', 'video', 'photo'])
def handle_all_inputs(message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    state = user_states.get(user_id)
    text = message.text or message.caption or ""

    if user_id == ADMIN_ID:
        if message.video and isinstance(state, dict) and state.get("step") == "admin_direct_wait_video":
            user_states[user_id]["video"] = message.video.file_id
            user_states[user_id]["step"] = "admin_direct_wait_code"
            bot.reply_to(message, "🔢 Video qabul qilindi. Endi kodini yuboring:")
            return

        if isinstance(state, dict) and state.get("step") == "admin_direct_wait_code":
            v_type = state["type"]
            code = text.strip()
            video_id = state["video"]
            movies_db[code] = video_id
            user_states.pop(user_id, None)
            bot.reply_to(message, f"✅ Muvaffaqiyatli! `{code}` kodli **{v_type.upper()}** video bazaga qo'shildi.", parse_mode="Markdown")
            return

    if state and state.startswith("waiting_for_check_"):
        if message.photo:
            period = state.split("_")[-1]
            user_states.pop(user_id, None)
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"vip_yes_{user_id}_{period}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"vip_no_{user_id}")
            )
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            bot.send_message(ADMIN_ID, f"👤 Foydalanuvchi: @{message.from_user.username} ({user_id})\n💎 Tarif: {period} oylik VIP obuna so'rayapti.", reply_markup=markup)
            bot.reply_to(message, "✅ Chekingiz adminga yuborildi! Tez orada tekshirib ulab berishadi.")
            return
        else:
            bot.reply_to(message, "❌ Iltimos, to'lov chekining rasmini (skrinshot) yuboring!")
            return

    if state == "recommending_movie":
        user_states.pop(user_id, None)
        bot.send_message(ADMIN_ID, f"💡 **Yangi kino tavsiyasi:**\nKimdan: @{message.from_user.username} ({user_id})\nKino: {text}")
        bot.reply_to(message, "✅ Tavsiyangiz adminga yuborildi!")
        return

    if state == "personal_add_video" and message.video:
        for word in BANNED_WORDS:
            if word in text.lower():
                banned_users.add(user_id)
                user_states.pop(user_id, None)
                bot.reply_to(message, "❌ Taqiqlangan kontent aniqlandi! Siz botdan bloklandingiz (ban).")
                return
        user_states[user_id] = {"video": message.video.file_id, "step": "personal_get_code"}
        bot.reply_to(message, "🔢 Bu kino uchun kod yuboring:")
        return

    if isinstance(state, dict) and state.get("step") == "personal_get_code":
        code = text.strip()
        video_id = state.get("video")
        movies_db[code] = video_id
        user_states.pop(user_id, None)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Reklama berish", url="https://t.me/reklamuchun1"))
        markup.add(types.InlineKeyboardButton("💎 Premium Obuna", callback_data="btn_vip_menu"))
        
        bot.send_message(message.chat.id, f"✅ Kino muvaffaqiyatli bazaga qo'shildi! Kodi: `{code}`", reply_markup=markup, parse_mode="Markdown")
        return

    if state == "admin_add_video" and message.video:
        user_states[user_id] = {"video": message.video.file_id, "step": "admin_get_code"}
        bot.reply_to(message, "🔢 Bu kino uchun kod yuboring:")
        return

    if isinstance(state, dict) and state.get("step") == "admin_get_code":
        code = text.strip()
        video_id = state.get("video")
        user_states.pop(user_id, None)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Qo'shish", callback_data=f"add_yes_{user_id}_{code}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"add_no")
        )
        bot.send_video(ADMIN_ID, video_id, caption=f"🎬 Yangi kino taklifi!\nKodi: `{code}`\nKimdan: @{message.from_user.username} ({user_id})", reply_markup=markup, parse_mode="Markdown")
        bot.reply_to(message, "✅ Kino tekshiruv uchun adminga yuborildi!")
        return

    code = text.strip()
    if code in movies_db:
        bot.send_video(message.chat.id, movies_db[code], caption=f"🎬 Siz so'ragan kino! Kodi: `{code}`", parse_mode="Markdown")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Reklama", url="https://t.me/reklamuchun1"))
        markup.add(types.InlineKeyboardButton("💎 Premium Obuna", callback_data="btn_vip_menu"))
        bot.reply_to(message, f"❌ `{code}` kodi bo'yicha kino topilmadi.", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("vip_"))
def admin_vip_control(call):
    data = call.data.split("_")
    action = data[1]
    
    if action == "yes":
        user_id = int(data[2])
        period = data[3]
        vip_users[user_id] = period
        bot.send_message(user_id, "🎉 Tabriklaymiz! Sizning VIP obunangiz admin tomonidan tasdiqlandi va faollashtirildi! ✅")
        bot.answer_callback_query(call.id, "VIP tasdiqlandi! ✅")
    else:
        user_id = int(data[2])
        bot.send_message(user_id, "❌ To'lov chekingiz rad etildi.")
        bot.answer_callback_query(call.id, "Rad etildi ❌")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
def admin_movie_control(call):
    data = call.data.split("_")
    action = data[1]
    
    if action == "yes":
        code = data[3]
        if call.message.video:
            movies_db[code] = call.message.video.file_id
        bot.answer_callback_query(call.id, f"Kino {code} kodi bilan bazaga qo'shildi! ✅")
        bot.edit_message_caption(caption=call.message.caption + "\n\n✅ HOLATI: Bazaga qo'shildi va tasdiqlandi!", chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Kino rad etildi ❌")
        bot.delete_message(call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    bot.infinity_polling()
    
