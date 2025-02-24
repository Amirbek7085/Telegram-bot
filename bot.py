import telebot
import json
import os
from flask import Flask
import threading

# **TOKEN va ADMIN ID**
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Getting token from environment variable
ADMIN_ID = [1330483263, 8104720367]  # Bir nechta adminlar uchun ro'yxat

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

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🎬 Kod orqali film topish", callback_data="check_movie_code"))

    bot.send_message(user_id, "✅ <b>Salom! Kinolar botiga xush kelibsiz.</b>
🔑 <i>Iltimos, kodni kiriting yoki quyidagi tugmani bosing.</i>", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "check_movie_code")
def ask_for_code(call):
    bot.send_message(call.message.chat.id, "🔑 Iltimos, film kodini kiriting:")
    bot.register_next_step_handler(call.message, verify_movie_code)

# **Kino kodlarini nazorat qilish**
@bot.message_handler(commands=['kodlar'])
def list_codes(message):
    if message.chat.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Bu buyruq faqat adminlar uchun.")
        return

    if not movies:
        bot.send_message(message.chat.id, "📂 Hozircha hech qanday kino kodlari yo‘q.")
        return

    text = "🔑 <b>Kino kodlari ro‘yxati:</b>

"
    for movie_id, movie in movies.items():
        text += f"🎬 <b>{movie['name']}</b>
"
        text += f"🔑 Kod: {movie['code']}

"

    bot.send_message(message.chat.id, text)

# **Barcha obunachilarga xabar yuborish**
@bot.message_handler(commands=['sendall'])
def broadcast_message(message):
    if message.chat.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Bu buyruq faqat adminlar uchun.")
        return

    bot.send_message(message.chat.id, "📩 Obunachilarga yuboriladigan xabarni yozing:")
    bot.register_next_step_handler(message, send_to_all)

def send_to_all(message):
    text = message.text.strip()

    if not text:
        bot.send_message(message.chat.id, "❌ Xabar bo‘sh bo‘lishi mumkin emas.")
        return

    count = 0
    for user_id in views.keys():
        try:
            bot.send_message(user_id, f"📢 Yangilik:

{text}")
            count += 1
        except Exception:
            pass

    bot.send_message(message.chat.id, f"✅ Xabar {count} ta obunachiga yuborildi.")

# **Flask server**
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    print("🤖 Bot ishlamoqda...")
    
    # Flask serverni alohida threadda ishga tushiramiz
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()

    # Botni ishga tushiramiz
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
