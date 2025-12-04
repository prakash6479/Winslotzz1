import telebot
from telebot import types
import sqlite3
import datetime
import random
import string
import os
from flask import Flask, request # NEW: For Webhook/Render Hosting

# --- 1. Configuration (UPDATED) ---
BOT_TOKEN = '8481818955:AAFRdwHiHDB9OnEQ4Sjo7SoMcg60bBvBuhc' 
CHANNEL_USERNAME = '@Testing55551' 
ADMIN_USERNAME_PRIMARY = '@Fasttaget'
ADMIN_USERNAME_SECONDARY = '@Winslotz' 
# Updated Admin IDs list
ADMIN_IDS = [7762779824, 7565458414, 8174647079] 
REFERRER_REWARD = 15.00 
REFERRED_BONUS = 5.00   
DB_NAME = 'winslotzz_bot.db' 

# RENDER Configuration (Your URL)
WEBHOOK_URL = "https://winslotzz1.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------
# --- 2. Flask and Webhook Setup (MANDATORY FOR RENDER) ---
# ----------------------------------------------------
# Flask app must be named 'app' for Gunicorn/Render to work
app = Flask(__name__) 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return 'OK', 200
        else:
            return 'Content-Type Error', 403
    
    # Simple message to confirm the bot is running
    return 'Winslotzz Bot is Running (Webhook Active)', 200

def set_webhook_url():
    """Sets the webhook URL on Telegram, essential for Render/Heroku."""
    try:
        # Clear any old webhooks
        bot.remove_webhook()
        # Set the new webhook URL
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"Webhook set to: {WEBHOOK_URL}")
    except Exception as e:
        print(f"Error setting webhook: {e}")


# --- 3. Game Data (Unchanged) ---
GAME_URLS = {
    "🔥 FireKirin": "https://start.firekirin.xyz:8580/index.html",
    "✨ MilkyWay": "http://milkywayapp.xyz:8580/index.html",
    "💰 Moolah": "https://moolah.vip:8888",
    "🎰 Vegas Roll": "https://www.vegas-roll.com/m",
    "💎 Loot Game": "https://m.lootgame777.com",
    "👑 RM777": "https://rm777.net",
    "⭐ Junva777": "http://dl.juwa777.com/",
    "🚀 Rising Star": "http://risingstar.vip:8580/index.html",
    "🌟 Vegas-X": "http://vegas-x.org/",
    "Vault GameVault": "http://download.gamevault999.com",
    "🐼 PandaMaster": "https://pandamaster.vip:8888/index.html",
    "🐅 UltraPanda": "http://www.ultrapanda.mobi/",
    "🃏 HighRollerSweep": "https://highrollersweep.cc",
    "⚙️ MegaSpinSweeps": "https://www.megaspinsweeps.com/index.html",
    "🌌 OrionStars": "https://start.orionstars.vip:8580/index.html",
    "🍀 PasaSweeps": "https://pasasweeps.net/",
    "🕹️ Vblink777": "https://www.vblink777.club",
    "🌃 LasVegasSweeps": "http://m.lasvegassweeps.com/",
    "🌀 CashFrenzy": "http://www.cashfrenzy777.com/m",
    "🏠 GameRoom777": "https://www.gameroom777.com",
    "🤵 Noble777": "http://web.noble777.com:8008/",
}

# ----------------------------------------------------
# --- 4. Database Functions (Unchanged Logic) ---
# ----------------------------------------------------

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            join_date TEXT,
            referral_code TEXT UNIQUE,
            referrer_id INTEGER,
            total_deposits REAL DEFAULT 0.0,
            total_referral_earnings REAL DEFAULT 0.0, 
            verified INTEGER DEFAULT 1
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            referred_id INTEGER UNIQUE,
            reward_amount REAL,
            date TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            status TEXT, 
            method TEXT,
            request_date TEXT,
            approve_date TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            game_name TEXT,
            click_time TEXT
        )
    ''')
    try:
        c.execute('ALTER TABLE users ADD COLUMN total_referral_earnings REAL DEFAULT 0.0')
    except sqlite3.OperationalError:
        pass 

    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def register_user(user_id, username, referrer_id=None):
    conn = get_db_connection()
    c = conn.cursor()
    join_date = datetime.datetime.now().isoformat()
    ref_code = generate_referral_code()

    try:
        c.execute('''
            INSERT INTO users (user_id, username, join_date, referral_code, referrer_id, verified, total_deposits)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        ''', (user_id, username, join_date, ref_code, referrer_id, REFERRED_BONUS if referrer_id else 0.0))
        conn.commit()

        if referrer_id:
            c.execute('''
                INSERT INTO referrals (referrer_id, referred_id, reward_amount, date)
                VALUES (?, ?, ?, ?)
            ''', (referrer_id, user_id, REFERRER_REWARD, join_date))
            
            c.execute('''
                UPDATE users SET total_referral_earnings = total_referral_earnings + ? WHERE user_id = ?
            ''', (REFERRER_REWARD, referrer_id))
            conn.commit()
            
            return True, 'referral_success'
        
        return True, 'success'
    except sqlite3.IntegrityError:
        return False, 'exists'
    finally:
        conn.close()

def get_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def get_total_referrals(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_user_referral_earnings(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT total_referral_earnings FROM users WHERE user_id = ?', (user_id,))
    earnings = c.fetchone()
    conn.close()
    return earnings[0] if earnings else 0.0

def get_all_user_ids():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    user_ids = [row[0] for row in c.fetchall()]
    conn.close()
    return user_ids
    
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id, username FROM users ORDER BY join_date DESC')
    users = c.fetchall()
    conn.close()
    return users
    
def get_user_admin_view(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    referrals_count = c.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,)).fetchone()[0]
    total_earnings = user[7] if user else 0.0
    payments = c.execute('SELECT id, amount, status, request_date FROM payments WHERE user_id = ? ORDER BY request_date DESC', (user_id,)).fetchall()
    clicks = c.execute('SELECT game_name, COUNT(*) FROM clicks WHERE user_id = ? GROUP BY game_name', (user_id,)).fetchall()
    conn.close()
    return user, referrals_count, total_earnings, payments, clicks
    
def add_payment_request(user_id, amount, method):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    request_date = datetime.datetime.now().isoformat()
    c.execute('''
        INSERT INTO payments (user_id, amount, status, method, request_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, amount, 'Pending', method, request_date))
    payment_id = c.lastrowid
    conn.commit()
    conn.close()
    return payment_id

def update_payment_status(payment_id, status, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    approve_date = datetime.datetime.now().isoformat() if status == 'Approved' else None
    
    c.execute('UPDATE payments SET status = ?, approve_date = ? WHERE id = ?', (status, approve_date, payment_id))
    
    if status == 'Approved':
        c.execute('SELECT amount FROM payments WHERE id = ?', (payment_id,))
        amount = c.fetchone()[0]
        c.execute('UPDATE users SET total_deposits = total_deposits + ? WHERE user_id = ?', (amount, user_id))

    conn.commit()
    conn.close()

# ----------------------------------------------------
# --- 5. Keyboard Markup Functions (Unchanged) ---
# ----------------------------------------------------

def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('🎮 Games'),
        types.KeyboardButton('🤝 Refer & Earn'),
        types.KeyboardButton('💳 Add Funds'),
        types.KeyboardButton('📊 My Stats'),
        types.KeyboardButton('🔔 Join Our Channel'),
        types.KeyboardButton('❓ Help')
    )
    return markup

def games_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for game_name, url in GAME_URLS.items():
        buttons.append(types.InlineKeyboardButton(text=game_name, callback_data=f"game_{game_name}"))
        
    markup.add(*buttons)
    # Uses back_edit logic (message text will be removed/edited)
    markup.add(types.InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_edit")) 
    return markup

def back_to_main_markup_send():
    markup = types.InlineKeyboardMarkup()
    # Uses back_send logic (message text will remain)
    markup.add(types.InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_send"))
    return markup

def back_to_main_markup_edit():
    markup = types.InlineKeyboardMarkup()
    # Uses back_edit logic (message text will be removed/edited)
    markup.add(types.InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_edit"))
    return markup

def admin_panel_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text="🏆 Overall Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"),
        types.InlineKeyboardButton(text="👥 View All Users", callback_data="admin_users"),
    )
    return markup

# ----------------------------------------------------
# --- 6. Core Utility Functions (Updated Text) ---
# ----------------------------------------------------

def send_main_menu(chat_id, text="🚀 **Main Menu** - Choose an option:", reply_markup=None):
    if reply_markup is None:
        reply_markup = main_menu_markup()
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=reply_markup)

def send_welcome_message(message):
    text = (
        "🥳 **Welcome to Winslotzz Premium Bot!** 👑\n\n"
        "You have full access to our **21 high-payout games** and the **Refer & Earn** program.\n\n"
        "Select an option below to get started!"
    )
    send_main_menu(message.chat.id, text)

# ----------------------------------------------------
# --- 7. User Handlers (Permanent Link Fix Verified) ---
# ----------------------------------------------------

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else str(user_id)
    
    referrer_id = None
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        conn = get_db_connection()
        c = conn.cursor()
        # Ensure the referrer is a valid user
        c.execute('SELECT user_id FROM users WHERE referral_code = ?', (ref_code,))
        referrer_data = c.fetchone()
        conn.close()
        if referrer_data:
            referrer_id = referrer_data[0]
            
    success, status = register_user(user_id, username, referrer_id)

    if success and status == 'referral_success':
        bot.send_message(user_id, f"🏆 **Welcome Bonus!** You received **${REFERRED_BONUS:.2f} USD** for joining via a friend's link! 🤝", parse_mode='Markdown')
        try:
             bot.send_message(referrer_id, f"🌟 **Reward Alert!** User `@{username}` joined using your link. You earned **${REFERRER_REWARD:.2f} USD**! 💰", parse_mode='Markdown')
        except Exception:
             pass 
    elif not success and status == 'exists':
        pass

    send_welcome_message(message)

@bot.message_handler(func=lambda message: message.text in ['🎮 Games', '/games'])
def handle_games(message):
    text = "🎰 **Game Lobby** - Choose your game! 🚀\n\n_Click any game to launch its direct URL._"
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=games_markup())

@bot.message_handler(func=lambda message: message.text in ['🤝 Refer & Earn', '/refer'])
def handle_refer(message):
    user = get_user(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "Error: User data not found. Please try /start.")
        return

    # User's permanent referral code is fetched from the database (user[4])
    referral_code = user[4]
    bot_username = bot.get_me().username # The link requires the Bot's username
    
    # PERMANENT LINK GENERATION
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    total_refs = get_total_referrals(message.chat.id)
    total_earnings = get_user_referral_earnings(message.chat.id)

    text = (
        "🤝 **Refer & Earn Program** 💰\n\n"
        f"Invite friends and earn **${REFERRER_REWARD:.2f} USD** for every successful signup! The referred user also gets a **${REFERRED_BONUS:.2f} USD** bonus!\n\n"
        "🔗 **Your Unique Referral Link (PERMANENT):**\n"
        f"`{referral_link}`\n\n"
        f"🏆 **Your Referrals:** **{total_refs}** users referred so far!\n"
        f"💸 **Total Referral Earnings:** **${total_earnings:.2f} USD**\n\n"
        "⚠️ **WITHDRAWAL NOTICE:** To withdraw your referral earnings, you **must contact the Admin** directly.\n"
        "**Available Withdrawal Methods:** **Chime, Crypto, and USDT.**"
    )
    
    markup = types.InlineKeyboardMarkup()
    # Updated Admin Usernames in the message
    markup.add(
        types.InlineKeyboardButton(text=f"💬 Contact Admin for Withdrawal ({ADMIN_USERNAME_PRIMARY})", url=f"https://t.me/{ADMIN_USERNAME_PRIMARY.replace('@', '')}"),
        types.InlineKeyboardButton(text=f"💬 Contact Admin for Withdrawal ({ADMIN_USERNAME_SECONDARY})", url=f"https://t.me/{ADMIN_USERNAME_SECONDARY.replace('@', '')}")
    )
    markup.add(types.InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_send")) 
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['💳 Add Funds', '/addfunds'])
def handle_add_funds(message):
    
    text = (
        "💸 **Deposit Service** 24/7 ⏰\n\n"
        "To **DEPOSIT** funds, you **must contact the Admin** directly.\n"
        "**Available Deposit Methods:** **Chime, Crypto, and USDT.**\n\n"
        "👇 **Contact the Admin:**\n"
        f"👑 **Admin Usernames:** **{ADMIN_USERNAME_PRIMARY}** OR **{ADMIN_USERNAME_SECONDARY}**"
    )
    
    markup = types.InlineKeyboardMarkup()
    # Updated Admin Usernames in the message
    markup.add(
        types.InlineKeyboardButton(text=f"💬 Contact Admin for Deposit ({ADMIN_USERNAME_PRIMARY})", url=f"https://t.me/{ADMIN_USERNAME_PRIMARY.replace('@', '')}"),
        types.InlineKeyboardButton(text=f"💬 Contact Admin for Deposit ({ADMIN_USERNAME_SECONDARY})", url=f"https://t.me/{ADMIN_USERNAME_SECONDARY.replace('@', '')}")
    )
    markup.add(types.InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_send")) 
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['📊 My Stats', '/mystats'])
def handle_mystats(message):
    user = get_user(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "Error: User data not found. Please try /start.")
        return
        
    user_id = user[1]
    total_deposits = user[6] 
    total_refs = get_total_referrals(user_id)
    total_ref_earnings = get_user_referral_earnings(user_id)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT game_name, COUNT(*) as count
        FROM clicks
        WHERE user_id = ?
        GROUP BY game_name
        ORDER BY count DESC
    ''', (user_id,))
    click_stats = c.fetchall()
    conn.close()
    
    game_list = "\n".join([f"- **{name.split(' ')[-1]}:** {count} clicks" for name, count in click_stats[:5]])
    if not game_list:
        game_list = "No games played yet."
        
    text = (
        "🏆 **Your Personal Stats** 📊\n\n"
        f"👤 **Your ID:** `{user_id}`\n"
        f"💰 **Total Funds (Deposits + Bonus):** **${total_deposits:.2f} USD**\n"
        f"🤝 **Referrals Made:** **{total_refs}** users\n"
        f"💸 **Referral Earnings:** **${total_ref_earnings:.2f} USD**\n\n"
        "🔥 **Your Top 5 Games:**\n"
        f"{game_list}\n\n"
        "**Action Required:**\n"
        f"To **deposit or withdraw**, contact Admin:\n"
        f"**{ADMIN_USERNAME_PRIMARY}** OR **{ADMIN_USERNAME_SECONDARY}**\n"
        "**Available Methods:** **Chime, Crypto, and USDT.**"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=back_to_main_markup_edit())

@bot.message_handler(func=lambda message: message.text == '🔔 Join Our Channel')
def handle_join_channel(message):
    if CHANNEL_USERNAME:
        text = (
            "📢 **Official Channel** 👑\n\n"
            "All the latest news, updates, and major announcements are posted here.\n\n"
            "👇 **Click to Join:**"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(text="Join Now! 🚀", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
        )
        markup.add(types.InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_send")) 
        
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Error: Channel link is not configured by the admin.", reply_markup=back_to_main_markup_send())

@bot.message_handler(func=lambda message: message.text in ['❓ Help', '/help'])
def handle_help(message):
    text = (
        "❓ **Help & Guide**\n\n"
        "Here are the main commands and features:\n\n"
        "1. **🎮 Games** (`/games`): Access the 21 direct-URL games.\n"
        "2. **🤝 Refer & Earn** (`/refer`): Get your unique link and earn rewards.\n"
        "3. **💳 Add Funds** (`/addfunds`): *Contact the Admin* for instant fund deposit.\n"
        "4. **📊 My Stats** (`/mystats`): View your deposits, referrals, and top games.\n"
        "5. **🔔 Join Our Channel**: See the latest updates and news.\n"
        f"6. **Admin Support:** For issues, queries, or **Deposit/Withdrawal**, contact our Admin(s):\n"
        f"**{ADMIN_USERNAME_PRIMARY}** OR **{ADMIN_USERNAME_SECONDARY}**.\n\n"
        "**Payment Methods:** **Chime, Crypto, and USDT.**\n\n"
        "Thank you for being a **Winslotzz Premium** member! 👑"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=back_to_main_markup_edit())
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('game_'))
def handle_game_click(call):
    game_name_full = call.data[5:]
    user_id = call.from_user.id
    
    conn = get_db_connection()
    c = conn.cursor()
    click_time = datetime.datetime.now().isoformat()
    c.execute('''
        INSERT INTO clicks (user_id, game_name, click_time)
        VALUES (?, ?, ?)
    ''', (user_id, game_name_full, click_time))
    conn.commit()
    conn.close()
    
    url = GAME_URLS.get(game_name_full, "https://example.com/error")
    
    alert_text = f"🔥 Launching **{game_name_full.split(' ')[-1]}**! Good luck! 🚀"
    
    bot.answer_callback_query(
        callback_query_id=call.id, 
        text=alert_text, 
        show_alert=True
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text=f"▶️ Go to {game_name_full}", url=url))
    markup.add(types.InlineKeyboardButton(text="🔙 Back to Games", callback_data="back_games_menu_edit")) 
    
    bot.send_message(call.message.chat.id, 
                     f"**{game_name_full}** is ready! Tap the button below to play:", 
                     parse_mode='Markdown',
                     reply_markup=markup)

# --- CALLBACK HANDLER FOR BACK BUTTONS ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('back_'))
def handle_back_buttons(call):
    chat_id = call.message.chat.id
    action = call.data[5:]
    
    bot.answer_callback_query(call.id)
    
    text = "🚀 **Main Menu** - Choose an option:"
    
    if action == 'send':
        # Send New Message logic (for Refer, Add Funds, Channel)
        send_main_menu(chat_id, text)
        
    elif action == 'edit':
        # Edit Message logic (for Games, Stats, Help)
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=main_menu_markup()
            )
        except Exception:
            send_main_menu(chat_id, text)
            
    elif action == 'games_menu_edit':
        # Back to Games Menu logic (uses Edit)
        text = "🎰 **Game Lobby** - Choose your game! 🚀\n\n_Click any game to launch its direct URL._"
        try:
             bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=games_markup()
            )
        except Exception:
            bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=games_markup())

# ----------------------------------------------------
# --- 8. Admin Handlers (Unchanged Logic) ---
# ----------------------------------------------------

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ **Access Denied:** You are not authorized to use the admin panel.", parse_mode='Markdown')
        return

    text = "👑 **Admin Panel** 🏆\n\n*Select an option to view platform data and manage announcements.*\n\n**To manually add funds after receiving payment, use:**\n`/approve [Request_ID] [User_ID] [Amount]`"
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=admin_panel_markup())

@bot.message_handler(commands=['approve'])
def handle_manual_approval(message):
    if message.from_user.id not in ADMIN_IDS: return

    try:
        parts = message.text.split()
        if len(parts) != 4:
            raise ValueError("Invalid number of arguments")
            
        dummy_id = int(parts[1]) 
        user_id = int(parts[2])
        amount = float(parts[3])
        method = "Admin Manual" 
        
        payment_id = add_payment_request(user_id, amount, method)
        update_payment_status(payment_id, 'Approved', user_id)
        
        bot.send_message(message.chat.id, 
                         f"✅ **Manual Approval Success!**\n"
                         f"Payment ID `{payment_id}` for **${amount:.2f} USD** approved for User ID `{user_id}`.\n"
                         f"User notified.",
                         parse_mode='Markdown')

        user_message = (
            f"✅ **Payment Status Update!**\n\n"
            f"Your fund addition of **${amount:.2f} USD** has been **APPROVED** by the admin.\n"
            f"🎉 **Funds Added!** You can now enjoy the games! 🎮"
        )
        try:
            bot.send_message(user_id, user_message, parse_mode='Markdown', reply_markup=main_menu_markup())
        except Exception: 
            pass 

    except Exception as e:
        bot.send_message(message.chat.id, 
                         f"❌ **Approval Error:** {e}\n\n"
                         f"Use format: `/approve [Dummy_ID] [User_ID] [Amount]`\n"
                         f"Example: `/approve 1 123456789 100.00`",
                         parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'admin_broadcast')
def handle_broadcast_init(call):
    if call.from_user.id not in ADMIN_IDS: return
    
    bot.answer_callback_query(call.id, "Starting Broadcast...")
    
    message_text = "📢 **BROADCAST MODE ACTIVATED!**\n\nPlease reply to this message with the exact text you want to broadcast to ALL users."
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=message_text,
        parse_mode='Markdown'
    )
    
    bot.register_next_step_handler(call.message, process_broadcast_message)

def process_broadcast_message(message):
    if message.from_user.id not in ADMIN_IDS: return
    
    broadcast_text = message.text
    user_ids = get_all_user_ids()
    sent_count = 0
    failed_count = 0
    
    final_message = "📢 **ADMIN ANNOUNCEMENT** 👑\n\n" + broadcast_text
    
    for user_id in user_ids:
        try:
            bot.send_message(user_id, final_message, parse_mode='Markdown')
            sent_count += 1
        except Exception as e:
            print(f"Failed to send broadcast to user {user_id}: {e}")
            failed_count += 1
            
    report_text = (
        "✅ **Broadcast Completed!**\n\n"
        f"Total Users: **{len(user_ids)}**\n"
        f"Messages Sent: **{sent_count}**\n"
        f"Messages Failed (Blocked/Error): **{failed_count}**"
    )
    
    bot.send_message(message.chat.id, report_text, parse_mode='Markdown', reply_markup=admin_panel_markup())


@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callbacks(call):
    conn = get_db_connection()
    c = conn.cursor()
    
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    action = call.data[6:]

    if action == 'stats':
        total_users = c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        total_referrals = c.execute('SELECT COUNT(*) FROM referrals').fetchone()[0]
        total_deposits_all = c.execute('SELECT SUM(total_deposits) FROM users').fetchone()[0] or 0.0
        
        top_games = c.execute('''
            SELECT game_name, COUNT(*) as count
            FROM clicks
            GROUP BY game_name
            ORDER BY count DESC
            LIMIT 5
        ''').fetchall()
        
        top_games_list = "\n".join([f"- **{name.split(' ')[-1]}:** {count} clicks" for name, count in top_games])
        if not top_games_list:
            top_games_list = "No game clicks recorded yet."
        
        text = (
            "🏆 **Overall Platform Statistics** 📊\n\n"
            f"👤 **Total Registered Users:** **{total_users}**\n"
            f"🤝 **Total Referrals Tracked:** **{total_referrals}**\n"
            f"💰 **Total Funds in Circulation (Deposits+Bonus):** **${total_deposits_all:.2f} USD**\n\n"
            f"🔥 **Top 5 Most Clicked Games:**\n"
            f"{top_games_list}\n\n"
            f"📝 _Note: Deposits are manually logged via /approve._"
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, parse_mode='Markdown', reply_markup=admin_panel_markup())

    elif action == 'users':
        users = get_all_users()
        if not users:
            text = "❌ **No Users Found**"
        else:
            text = "👥 **All Users Summary** (Showing latest 10)\n\n"
            for user_id, username in users[:10]:
                text += (
                    f"**ID:** `{user_id}`\n"
                    f"**Username:** @{username or 'N/A'}\n"
                    f"--- \n"
                )
            text += "\n_Use /admin_user [ID] for full details._"
        
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, parse_mode='Markdown', reply_markup=admin_panel_markup())
        
    conn.close()


@bot.message_handler(commands=['admin_user'])
def handle_admin_user_details(message):
    if message.from_user.id not in ADMIN_IDS: return

    try:
        target_user_id = int(message.text.split()[1])
    except:
        bot.send_message(message.chat.id, "❌ **Invalid format.** Use: `/admin_user [USER_ID]`", parse_mode='Markdown')
        return

    user, refs, earnings, payments, clicks = get_user_admin_view(target_user_id)
    
    if not user:
        bot.send_message(message.chat.id, f"❌ **Error:** User ID `{target_user_id}` not found.", parse_mode='Markdown')
        return

    user_text = (
        "👤 **User Details** 👑\n\n"
        f"**ID:** `{user[1]}`\n"
        f"**Username:** @{user[2] or 'N/A'}\n"
        f"**Join Date:** {user[3].split('T')[0]}\n"
        f"**Ref Code:** `{user[4]}`\n"
        f"**Referrer ID:** `{user[5] or 'N/A'}`\n"
        f"**Total Funds (Deposits+Bonus):** **${user[6]:.2f} USD**\n"
        f"**Total Referral Earnings:** **${user[7]:.2f} USD**\n"
        f"**Total Referrals:** **{refs}**\n"
    )

    payment_list = "\n".join([f"- ID:{p[0]} | **${p[1]:.2f} USD** | Status: **{p[2]}** ({p[3].split('T')[0]})" for p in payments[:5]])
    if not payment_list: payment_list = "No payments recorded."
    user_text += f"\n\n💳 **Latest 5 Payments:**\n{payment_list}"

    click_list = "\n".join([f"- **{c[0].split(' ')[-1]}:** {c[1]} clicks" for c in clicks[:5]])
    if not click_list: click_list = "No game clicks recorded."
    user_text += f"\n\n🎮 **Top 5 Game Clicks:**\n{click_list}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="💬 Chat with User", url=f"tg://user?id={target_user_id}"))

    bot.send_message(message.chat.id, user_text, parse_mode='Markdown', reply_markup=markup)

# ----------------------------------------------------
# --- 9. Main Execution (MODIFIED FOR RENDER) ---
# ----------------------------------------------------

if __name__ == '__main__':
    print("Initializing Database...")
    init_db()
    
    # Set the webhook URL when the bot starts
    set_webhook_url()
    
    print("Bot setup complete. Ready for Render Webhook deployment (Gunicorn will run the app).")
    
    # This block is required to run the Flask app locally if not using gunicorn, 
    # but Gunicorn/Render handles the execution using the 'app' variable.
    # It should not be necessary for Render, but kept for robustness.
    # app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000))) 
