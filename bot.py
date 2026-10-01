import telebot
from telebot import types
import requests
import sqlite3
import os

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8403826808:AAHqc79KJlurchIRb8uvS4nRUzrfYKnW3sU"
ADMIN_ID = 5851941158  # আপনার Telegram ID

BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjZhNTQ3MzA4NjU0OTk0MmVmNWI5ZTRjMCIsImlhdCI6MTc5MDgzNjI0MywiZXhwIjoxNzkwOTIyNjQzfQ.LiTVHG4-xr76Zexf860HRI-Z7CIdO7kVV9_nyIqQbYk"

HEADERS = {
    'accept': '*/*',
    'authorization': f'Bearer {BEARER_TOKEN}',
    'origin': 'https://rewards.excelbd.com',
    'referer': 'https://rewards.excelbd.com/submission-list',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
}

ROUTER_MODELS = {
    "ARCHER C50 AC1200": "PASTE_ITEM_ID_HERE",
    "ARCHER C20 AC750": "PASTE_ITEM_ID_HERE",
    "TL-WR840N 300Mbps": "PASTE_ITEM_ID_HERE",
    "TL-WR844N 300Mbps": "PASTE_ITEM_ID_HERE"
}
# --------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# SQLite Database Setup (সহজ ও ১০০% এরর-ফ্রি)
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            points INTEGER DEFAULT 0,
            total_submits INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

user_states = {}

# Command: /start
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    name = message.from_user.first_name or "User"
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (chat_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, name, points, total_submits) VALUES (?, ?, 0, 0)", (chat_id, name))
        conn.commit()
    conn.close()

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📥 Submit Router"),
        types.KeyboardButton("📊 My Submissions"),
        types.KeyboardButton("💰 My Balance"),
        types.KeyboardButton("💸 Withdraw"),
        types.KeyboardButton("📞 Contact Admin")
    )
    if chat_id == ADMIN_ID:
        markup.add(types.KeyboardButton("⚙️ Admin Panel"))

    bot.send_message(chat_id, f"👋 স্বাগতম {name}!\nকাজের জন্য নিচের অপশনগুলো ব্যবহার করুন:", reply_markup=markup)

# Balance Check
@bot.message_handler(func=lambda msg: msg.text == "💰 My Balance")
def my_balance(message):
    chat_id = message.chat.id
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    
    pts = row[0] if row else 0
    taka = pts * 10
    bot.send_message(chat_id, f"💳 **আপনার বর্তমান ব্যালেন্স:**\n\nমোট পয়েন্ট: *{pts}*\nসমপরিমাণ টাকা: *{taka} BDT*", parse_mode="Markdown")

# Submit Router Process
@bot.message_handler(func=lambda msg: msg.text == "📥 Submit Router")
def start_submit(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'step': 'SELECT_MODEL'}
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for m_name, m_id in ROUTER_MODELS.items():
        markup.add(types.InlineKeyboardButton(m_name, callback_data=f"model_{m_id}"))
        
    bot.send_message(chat_id, "১. রাউটারের Model সিলেক্ট করুন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("model_"))
def handle_model_select(call):
    chat_id = call.message.chat.id
    m_id = call.data.split("_")[1]
    user_states[chat_id] = {'item_id': m_id, 'step': 'AWAITING_SERIAL'}
    bot.send_message(chat_id, "২. রাউটারের Serial Number (S/N) লিখুন:")

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id].get('step') == 'AWAITING_SERIAL')
def handle_serial(message):
    chat_id = message.chat.id
    user_states[chat_id]['serial'] = message.text.strip()
    user_states[chat_id]['step'] = 'AWAITING_PHOTO'
    bot.send_message(chat_id, "৩. রাউটারের পিছনের স্টিকারের স্পষ্ট Photo পাঠান:")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    if chat_id in user_states and user_states[chat_id].get('step') == 'AWAITING_PHOTO':
        bot.send_message(chat_id, "⏳ ওয়েবসাইট সার্ভারে সাবমিট করা হচ্ছে...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        item_id = user_states[chat_id]['item_id']
        serial = user_states[chat_id]['serial']
        
        payload = {'itemId': item_id, 'productSerial': serial}
        files = {'product_image': ('submission.jpg', downloaded_file, 'image/jpeg')}
        
        try:
            target_url = 'https://rewards.excelbd.com/api/v1/benefit-submissions'
            res = requests.post(target_url, headers=HEADERS, data=payload, files=files)
            
            if res.status_code in [200, 201]:
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET points = points + 7, total_submits = total_submits + 1 WHERE user_id = ?", (chat_id,))
                conn.commit()
                conn.close()
                bot.send_message(chat_id, f"✅ **সফলভাবে সাবমিট হয়েছে!**\n\nSerial: `{serial}`\n+7 পয়েন্ট যোগ করা হয়েছে!", parse_mode="Markdown")
            else:
                err_text = res.json().get('message', res.text) if res.headers.get('content-type') == 'application/json' else res.text
                bot.send_message(chat_id, f"❌ **ওয়েবসাইট এরর:**\n`{err_text}`", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ সিস্টেমে ত্রুটি: {str(e)}")
            
        del user_states[chat_id]

# Admin Panel
@bot.message_handler(func=lambda msg: msg.text == "⚙️ Admin Panel" and msg.chat.id == ADMIN_ID)
def admin_panel(message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    
    bot.send_message(
        ADMIN_ID, 
        f"🛠 **Admin Dashboard**\n\n• মোট ইউজার: {total_users}",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("🤖 Bot is starting on Render...")
    bot.remove_webhook()
    bot.infinity_polling()
