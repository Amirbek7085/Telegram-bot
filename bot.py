import telebot
import json
import os

# **TOKEN va ADMIN ID**
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Getting token from environment variable
ADMIN_ID = 1330483263  # <<< BU YERGA ADMIN ID-INGIZNI YOZING

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# **Fayllar**
MOVIES_FILE = "movies.json"
VIEWS_FILE = "views.json"
CHANNELS_FILE = "channels.json"
CODES_FILE = "codes.json"

# **JSON ma'lumotlarni yuklash va saqlash**
def load_data(file, default):
    try:
        if os.path.exists(file):
            with open(file, "r") as f:
                return json.load(f)
    except json.JSONDecodeError:
        return default
    return default

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

movies = load_data(MOVIES_FILE, {})
views = load_data(VIEWS_FILE, {})
channels = load_data(CHANNELS_FILE, [])
codes = load_data(CODES_FILE, {})

# **START - Obunani tekshirish**
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if not check_subscription(user_id):
        send_subscription_message(user_id)
        return
    bot.send_message(user_id, "✅ <b>Salom! Kinolar botiga xush kelibsiz.</b>\n🔑 <i>Iltimos, kodni kiriting.</i>")

def send_subscription_message(user_id):
    if not channels:
        bot.send_message(user_id, "🚀 Botga xush kelibsiz! Hozircha hech qanday kanalga obuna talab qilinmaydi.")
        return

    text = "🚀 Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:\n\n"
    for ch in channels:
        text += f"🔹 <a href='https://t.me/{ch}'>{ch}</a>\n"
    text += "\n✅ A'zo bo'lgandan keyin pastdagi tugma orqali tekshiring."

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🔄 Tekshirish", callback_data="check_subscription"))

    bot.send_message(user_id, text, reply_markup=keyboard, disable_web_page_preview=True)

def check_subscription(user_id):
    """Foydalanuvchi barcha kanallarga obuna bo'lganligini tekshiradi."""
    if not channels:
        return True  # Agar kanal ro'yxati bo'sh bo'lsa, tekshirish shart emas

    for ch in channels:
        try:
            status = bot.get_chat_member(f"@{ch}", user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False  # Agar obuna bo'lmasa
        except telebot.apihelper.ApiTelegramException as e:
            if "member list is inaccessible" in str(e):
                print(f"Xatolik: Bot '{ch}' kanalida admin emas")
                return False
            elif "chat not found" in str(e):
                print(f"Xatolik: '{ch}' kanali topilmadi")
                return False
            else:
                print(f"Telegram API xatolik: {e}")  # Boshqa Telegram API xatoliklarni konsolga chiqarish
                return False
        except Exception as e:
            print(f"Kutilmagan xatolik: {e}")  # Boshqa xatoliklarni konsolga chiqarish
            return False

    return True  # Agar barcha kanallarga obuna bo'lsa, True qaytaradi

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def verify_subscription(call):
    user_id = call.message.chat.id
    if check_subscription(user_id):
        bot.send_message(user_id, "✅ Siz barcha kanallarga a'zo bo'lgansiz! Endi botdan foydalanishingiz mumkin.")
    else:
        send_subscription_message(user_id)  # Agar obuna bo'lmasa, yana so'raymiz

# **ADMIN PANELI**
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Bu buyruq faqat adminlar uchun.")
        return

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🎬 Filmlarni boshqarish", "🔑 Kodlarni sozlash")
    keyboard.row("📢 Homiy kanallar", "📊 Statistika")
    keyboard.row("⚙️ Sozlamalar", "🔙 Orqaga")

    bot.send_message(message.chat.id, "🛠 <b>Admin paneliga xush kelibsiz!</b>", reply_markup=keyboard)

# **Filmlarni boshqarish**
@bot.message_handler(func=lambda message: message.text == "🎬 Filmlarni boshqarish")
def manage_movies(message):
    if message.chat.id != ADMIN_ID:
        return

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("➕ Yangi film qo'shish", "🗑 Filmni o'chirish")
    keyboard.row("📂 Film ro'yxati", "🔙 Orqaga")

    bot.send_message(message.chat.id, "🎥 <b>Filmlarni boshqarish</b>", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "➕ Yangi film qo'shish")
def add_movie(message):
    if message.chat.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "🎬 Kino nomini kiriting:")
    bot.register_next_step_handler(message, get_movie_name)

def get_movie_name(message):
    movie_name = message.text.strip()
    bot.send_message(message.chat.id, "📁 Kinoga fayl yoki link yuboring:")
    bot.register_next_step_handler(message, lambda m: save_movie(message.chat.id, movie_name, m))

def save_movie(admin_id, movie_name, message):
    if message.content_type not in ["video", "text"]:
        bot.send_message(admin_id, "❌ Xatolik! Kino sifatida video yoki link yuboring.")
        return

    movie_id = str(len(movies) + 1)
    movies[movie_id] = {
        "name": movie_name,
        "file_id": message.video.file_id if message.content_type == "video" else message.text,
        "views": 0,
        "code": f"KINO-{movie_id}"
    }
    save_data(MOVIES_FILE, movies)

    bot.send_message(admin_id, f"✅ Kino saqlandi!\n🎬 <b>{movie_name}</b>\n🔑 Kod: {movies[movie_id]['code']}")

@bot.message_handler(func=lambda message: message.text == "📂 Film ro'yxati")
def list_movies(message):
    if message.chat.id != ADMIN_ID:
        return

    if not movies:
        bot.send_message(message.chat.id, "📂 Hozircha filmlar yo'q.")
        return

    text = "📂 <b>Filmlar ro'yxati:</b>\n\n"
    for movie_id, movie in movies.items():
        text += f"🎬 <b>{movie['name']}</b>\n"
        text += f"🔑 Kod: {movie['code']}\n"
        text += f"👁 Ko'rishlar: {movie['views']}\n\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == "🗑 Filmni o'chirish")
def delete_movie_prompt(message):
    if message.chat.id != ADMIN_ID:
        return

    if not movies:
        bot.send_message(message.chat.id, "📂 Hozircha filmlar yo'q.")
        return

    bot.send_message(message.chat.id, "🗑 O'chirmoqchi bo'lgan film kodini kiriting:")
    bot.register_next_step_handler(message, delete_movie)

def delete_movie(message):
    movie_code = message.text.strip()

    # Find movie by code
    movie_id = None
    for mid, movie in movies.items():
        if movie['code'] == movie_code:
            movie_id = mid
            break

    if movie_id is None:
        bot.send_message(message.chat.id, "❌ Bunday kodli film topilmadi.")
        return

    movie_name = movies[movie_id]['name']
    del movies[movie_id]
    save_data(MOVIES_FILE, movies)

    bot.send_message(message.chat.id, f"✅ Film o'chirildi:\n🎬 <b>{movie_name}</b>")

# **Homiy kanallarni boshqarish**
@bot.message_handler(func=lambda message: message.text == "📢 Homiy kanallar")
def manage_channels(message):
    if message.chat.id != ADMIN_ID:
        return

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("➕ Kanal qo'shish", "❌ Kanal o'chirish")
    keyboard.row("📋 Kanallar ro'yxati", "🔙 Orqaga")

    bot.send_message(message.chat.id, "📢 <b>Homiy kanallarni boshqarish</b>", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "➕ Kanal qo'shish")
def add_channel_prompt(message):
    if message.chat.id != ADMIN_ID:
        return

    bot.send_message(message.chat.id, "➕ Qo'shmoqchi bo'lgan kanal usernameni kiriting:\n(Masalan: 'MyChannel' yoki 'mychannel')")
    bot.register_next_step_handler(message, add_channel)

def add_channel(message):
    channel = message.text.strip()

    # Remove @ if present
    if channel.startswith('@'):
        channel = channel[1:]

    # Check if channel already exists
    if channel in channels:
        bot.send_message(message.chat.id, "❌ Bu kanal allaqachon qo'shilgan!")
        return

    try:
        # Try to get channel info to verify it exists
        bot.get_chat(f"@{channel}")

        # Add channel
        channels.append(channel)
        save_data(CHANNELS_FILE, channels)

        bot.send_message(message.chat.id, f"✅ Kanal @{channel} muvaffaqiyatli qo'shildi!")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Xatolik! Kanal topilmadi yoki bot kanalga admin emas.")

@bot.message_handler(func=lambda message: message.text == "❌ Kanal o'chirish")
def remove_channel_prompt(message):
    if message.chat.id != ADMIN_ID:
        return

    if not channels:
        bot.send_message(message.chat.id, "📢 Hozircha kanallar yo'q.")
        return

    bot.send_message(message.chat.id, "❌ O'chirmoqchi bo'lgan kanal usernameni kiriting:")
    bot.register_next_step_handler(message, remove_channel)

def remove_channel(message):
    channel = message.text.strip()

    # Remove @ if present
    if channel.startswith('@'):
        channel = channel[1:]

    if channel not in channels:
        bot.send_message(message.chat.id, "❌ Bunday kanal topilmadi!")
        return

    channels.remove(channel)
    save_data(CHANNELS_FILE, channels)

    bot.send_message(message.chat.id, f"✅ Kanal @{channel} muvaffaqiyatli o'chirildi!")

@bot.message_handler(func=lambda message: message.text == "📋 Kanallar ro'yxati")
def list_channels(message):
    if message.chat.id != ADMIN_ID:
        return

    if not channels:
        bot.send_message(message.chat.id, "📢 Hozircha kanallar yo'q.")
        return

    text = "📢 <b>Homiy kanallar ro'yxati:</b>\n\n"
    for i, channel in enumerate(channels, 1):
        text += f"{i}. @{channel}\n"

    bot.send_message(message.chat.id, text)

# **Statistika ko'rish**
@bot.message_handler(func=lambda message: message.text == "📊 Statistika")
def show_statistics(message):
    if message.chat.id != ADMIN_ID:
        return

    user_count = len(views)  
    total_views = sum(views.values()) if views else 0

    text = f"📊 <b>Statistika</b>\n\n👤 <b>Foydalanuvchilar:</b> {user_count}\n🎬 <b>Jami ko'rishlar:</b> {total_views}"
    bot.send_message(message.chat.id, text)

# **Sozlamalar bo'limi**
@bot.message_handler(func=lambda message: message.text == "⚙️ Sozlamalar")
def settings(message):
    if message.chat.id != ADMIN_ID:
        return

    bot.send_message(message.chat.id, "⚙️ <b>Sozlamalar bo'limi hozircha mavjud emas.</b>")

# **Orqaga qaytish**
@bot.message_handler(func=lambda message: message.text and "Orqaga" in message.text)
def back_to_admin(message):
    if message.chat.id != ADMIN_ID:
        return
    admin_panel(message)

# Add code verification handler
@bot.message_handler(func=lambda message: True)
def verify_movie_code(message):
    user_id = str(message.chat.id)
    code = message.text.strip()

    # Find movie by code
    movie = None
    for m in movies.values():
        if m['code'] == code:
            movie = m
            break

    if movie is None:
        bot.send_message(message.chat.id, "❌ Noto'g'ri kod kiritildi.")
        return

    # Update views
    if user_id not in views:
        views[user_id] = 0
    views[user_id] += 1
    save_data(VIEWS_FILE, views)

    # Send movie
    if isinstance(movie['file_id'], str) and movie['file_id'].startswith('http'):
        text = f"🎬 <b>{movie['name']}</b>\n\n"
        text += f"🔗 Link: {movie['file_id']}"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_video(message.chat.id, movie['file_id'], caption=f"🎬 <b>{movie['name']}</b>")

# **BOTNI ISHLATISH**
if __name__ == '__main__':
    print("🤖 Bot ishlamoqda...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)