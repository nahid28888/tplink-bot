import sqlite3
import requests
import telebot
from telebot import types

BOT_TOKEN = "8403826808:AAHqc79KJlurchIRb8uvS4nRUzrfYKnW3sU"
ADMIN_ID = 5851941158  # আপনার টেলিগ্রাম আইডি

BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjZhNTQ3MzA4NjU0OTk0MmVmNWI5ZTRjMCIsImlhdCI6MTc5MDgzNjI0MywiZXhwIjoxNzkwOTIyNjQzfQ.LiTVHG4-xr76Zexf860HRI-Z7CIdO7kVV9_nyIqQbYk"

HEADERS = {
    'accept': '*/*',
    'authorization': f'Bearer {BEARER_TOKEN}',
    'origin': 'https://rewards.excelbd.com',
    'referer': 'https://rewards.excelbd.com/submission-list',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
}

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# ডাটাবেস সেটআপ
def get_db():
    conn = sqlite3.connect('database.db')
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
    return conn

# API থেকে অটো itemId খোঁজার ফাংশন
def get_scheme_details(model_name):
    try:
        url = f"https://rewards.excelbd.com/api/v1/scheme-configs/available-scheme?brand=TP-LINK&item={model_name.replace(' ', '+')}&role=isp-employee"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get('status') and data.get('data'):
                return data['data'].get('_id') or data['data'].get('itemId') or data['data'].get('item')
    except Exception as e:
        print(f"Error: {e}")
    return None

# মূল কিবোর্ড বাটন (বাটন ইংলিশে, এডমিন বাটন শুধু আপনার আইডিতেই দেখাবে)
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📥 Submit Router", "📊 My Submissions", "💰 My Balance", "💸 Withdraw", "📞 Contact Helpline")
    if user_id == ADMIN_ID:
        markup.add("⚙️ Admin Control Panel")
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    name = message.from_user.first_name or "ইউজার"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (chat_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, name, points, total_submits) VALUES (?, ?, 0, 0)", (chat_id, name))
        conn.commit()
    conn.close()

    bot.send_message(
        chat_id, 
        f"👋 **স্বাগতম {name}!**\n\nTP-Link রাউটার সাবমিশন ও রিওয়ার্ড বটে আপনাকে স্বাগতম। কাজ শুরু করতে নিচের বাটনগুলো ব্যবহার করুন:", 
        parse_mode="Markdown",
        reply_markup=main_menu(chat_id)
    )

# 💰 ব্যালেন্স চেক
@bot.message_handler(func=lambda msg: msg.text == "💰 My Balance")
def my_balance(message):
    chat_id = message.chat.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT points, total_submits FROM users WHERE user_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    
    pts = row[0] if row else 0
    submits = row[1] if row else 0
    
    bot.send_message(
        chat_id, 
        f"💳 **আপনার অ্যাকাউন্ট ব্যালেন্স:**\n\n"
        f"🪙 মোট পয়েন্ট: `{pts}` পয়েন্ট\n"
        f"📦 মোট সাবমিট করেছেন: `{submits}` টি\n\n"
        f"*(প্রতিটি সফল রাউটার সাবমিটে পাবেন ৫ পয়েন্ট)*", 
        parse_mode="Markdown"
    )

# 📊 সাবমিশন হিস্ট্রি
@bot.message_handler(func=lambda msg: msg.text == "📊 My Submissions")
def my_submissions(message):
    chat_id = message.chat.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT total_submits FROM users WHERE user_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    
    submits = row[0] if row else 0
    bot.send_message(
        chat_id, 
        f"📊 **আপনার সাবমিশন হিস্ট্রি:**\n\n"
        f"✅ মোট সফলভাবে সাবমিট হয়েছে: `{submits}` টি রাউটার।", 
        parse_mode="Markdown"
    )

# 💸 উইথড্র অপশন
@bot.message_handler(func=lambda msg: msg.text == "💸 Withdraw")
def withdraw_notice(message):
    bot.send_message(
        message.chat.id,
        "📢 **উইথড্র নোটিশ:**\n\n"
        "📅 **প্রতিটি মাসের ১৫ তারিখে উইথড্র অপশন চালু করা হয়।**\n"
        "অনুগহ করে ১৫ তারিখ পর্যন্ত অপেক্ষা করুন এবং আপনার পয়েন্ট জমা রাখুন।\n\n"
        "কোনো বিষয়ে জানার থাকলে হেল্পলাইনে যোগাযোগ করুন।",
        parse_mode="Markdown"
    )

# 📞 হেল্পলাইন ও কন্টাক্ট
@bot.message_handler(func=lambda msg: msg.text == "📞 Contact Helpline")
def contact_helpline(message):
    text = (
        "🎧 **MASTER MIND TEAM সাপোর্ট হেল্পলাইন**\n\n"
        "আপনার কোনো সমস্যা বা প্রশ্ন থাকলে সরাসরি আমাদের সাথে যোগাযোগ করতে পারেন:\n\n"
        "💬 **Telegram:** @nahid_mmt\n"
        "📞 **WhatsApp:** 01303637752\n\n"
        "⏰ *আমাদের টিম আপনাকে সবসময় সাহায্য করতে প্রস্তুত!*"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💬 Telegram Admin", url="https://t.me/nahid_mmt"),
        types.InlineKeyboardButton("📞 WhatsApp Support", url="https://wa.me/8801303637752")
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

# 📥 রাউটার সাবমিশন ধাপসমূহ
@bot.message_handler(func=lambda msg: msg.text == "📥 Submit Router")
def start_submit(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'step': 'AWAITING_MODEL'}
    bot.send_message(
        chat_id, 
        "✏️ **রাউটারের Model এর নাম লিখুন:**\n\n"
        "যেমন: `ARCHER C50 AC1200`, `Archer C6`, `TL-WR840N 300Mbps`, `C54` ইত্যাদি।",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id].get('step') == 'AWAITING_MODEL')
def handle_model(message):
    chat_id = message.chat.id
    model_name = message.text.strip()
    bot.send_message(chat_id, f"🔍 `{model_name}` এর তথ্য যাচাই করা হচ্ছে...", parse_mode="Markdown")
    
    item_id = get_scheme_details(model_name)
    if not item_id:
        bot.send_message(chat_id, "❌ মডেলটি পাওয়া যায়নি! অনুগ্রহ করে সঠিক মডেল নাম লিখুন (যেমন: Archer C6)।")
        return

    user_states[chat_id] = {'model_name': model_name, 'item_id': item_id, 'step': 'AWAITING_SERIAL'}
    bot.send_message(chat_id, "✅ মডেল সঠিক আছে!\n\n২. এবার রাউটারের **Serial Number (S/N)** টাইপ করে পাঠান:", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id].get('step') == 'AWAITING_SERIAL')
def handle_serial(message):
    chat_id = message.chat.id
    user_states[chat_id]['serial'] = message.text.strip()
    user_states[chat_id]['step'] = 'AWAITING_PHOTO'
    bot.send_message(chat_id, "৩. এবার রাউটারের পিছনের স্টিকারের স্পষ্ট **ছবি (Photo)** তুলে পাঠান:")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    if chat_id in user_states and user_states[chat_id].get('step') == 'AWAITING_PHOTO':
        bot.send_message(chat_id, "⏳ সার্ভারে সাবমিট করা হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        item_id = user_states[chat_id]['item_id']
        serial = user_states[chat_id]['serial']
        
        payload = {'itemId': item_id, 'productSerial': serial}
        files = {'product_image': ('submission.jpg', downloaded_file, 'image/jpeg')}
        
        try:
            res = requests.post('https://rewards.excelbd.com/api/v1/benefit-submissions', headers=HEADERS, data=payload, files=files)
            if res.status_code in [200, 201]:
                conn = get_db()
                cursor = conn.cursor()
                # প্রতিটি সাবমিশনে ৫ পয়েন্ট যোগ
                cursor.execute("UPDATE users SET points = points + 5, total_submits = total_submits + 1 WHERE user_id = ?", (chat_id,))
                conn.commit()
                conn.close()
                bot.send_message(chat_id, f"✅ **সফলভাবে সাবমিট হয়েছে!**\n\nসিরিয়াল নম্বর: `{serial}`\n➕ আপনার অ্যাকাউন্টে **+৫ পয়েন্ট** যোগ করা হয়েছে!", parse_mode="Markdown")
            else:
                err_text = res.json().get('message', res.text) if res.headers.get('content-type') == 'application/json' else res.text
                bot.send_message(chat_id, f"❌ **ওয়েবসাইট এরর:**\n`{err_text}`", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ সিস্টেমে ত্রুটি: {str(e)}")
            
        del user_states[chat_id]

# ⚙️ শুধুমাত্র এডমিন কন্ট্রোল প্যানেল (আপনার আইডি ছাড়া কেউ দেখতে পারবে না)
@bot.message_handler(func=lambda msg: msg.text == "⚙️ Admin Control Panel" and msg.chat.id == ADMIN_ID)
def admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👥 User List & Points", callback_data="admin_users"),
        types.InlineKeyboardButton("➕ Add/Deduct Points", callback_data="admin_manage_pts")
    )
    bot.send_message(message.chat.id, "⚙️ **স্বাগতম বস! এডমিন কন্ট্রোল প্যানেল:**", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_actions(call):
    if call.message.chat.id != ADMIN_ID:
        return
        
    if call.data == "admin_users":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, points, total_submits FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        msg = "👥 **ইউজারদের তালিকা ও পয়েন্ট:**\n\n"
        for r in rows:
            msg += f"👤 **নাম:** {r[1]}\n🆔 **আইডি:** `{r[0]}`\n🪙 **পয়েন্ট:** {r[2]} | 📦 **সাবমিট:** {r[3]}\n-------------------\n"
        bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")

    elif call.data == "admin_manage_pts":
        bot.send_message(
            ADMIN_ID, 
            "✏️ **পয়েন্ট বাড়ানো বা কাটার নিয়ম:**\n\n"
            "• পয়েন্ট কাটতে লিখুন: `/cut <ইউজার_আইডি> <পয়েন্ট>`\n"
            "• পয়েন্ট দিতে লিখুন: `/add <ইউজার_আইডি> <পয়েন্ট>`\n\n"
            "উদাহরণ: `/cut 12345678 10` (১০ পয়েন্ট কেটে নেওয়া হবে)",
            parse_mode="Markdown"
        )

# এডমিন দ্বারা পয়েন্ট যোগ/কাটার কমান্ড
@bot.message_handler(commands=['cut', 'add'])
def manage_points(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        cmd, target_id, amount = message.text.split()
        target_id = int(target_id)
        amount = int(amount)
        
        conn = get_db()
        cursor = conn.cursor()
        if cmd == '/add':
            cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, target_id))
            bot.send_message(ADMIN_ID, f"✅ ইউজার `{target_id}` এর অ্যাকাউন্টে {amount} পয়েন্ট যোগ করা হয়েছে।")
            bot.send_message(target_id, f"🎉 এডমিন আপনার অ্যাকাউন্টে **+{amount} পয়েন্ট** যোগ করেছেন!")
        elif cmd == '/cut':
            cursor.execute("UPDATE users SET points = points - ? WHERE user_id = ?", (amount, target_id))
            bot.send_message(ADMIN_ID, f"✅ ইউজার `{target_id}` এর অ্যাকাউন্ট থেকে {amount} পয়েন্ট কেটে নেওয়া হয়েছে।")
            bot.send_message(target_id, f"⚠️ এডমিন আপনার অ্যাকাউন্ট থেকে **-{amount} পয়েন্ট** কেটে নিয়েছেন।")
        conn.commit()
        conn.close()
    except Exception as e:
        bot.send_message(ADMIN_ID, "❌ ফরম্যাট সঠিক নয়! উদাহরণ: `/cut 12345678 10`")

bot.infinity_polling()
