import telebot
from telebot import types
from googletrans import Translator
from flask import Flask
from threading import Thread
import os

# ==========================================
# ១. ផ្នែក KEEP ALIVE (សម្រាប់ RENDER & UPTIMEROBOT)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "I am alive! Bot is running..."

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# ២. ការកំណត់ BOT (CONFIGURATION)
# ==========================================
# យក Token ពី Environment Variable (សុវត្ថិភាពជាង) ឬដាក់ផ្ទាល់ក៏បាន
API_TOKEN = os.environ.get('BOT_TOKEN', '8223217940:AAH1tHD72PojpV0f4VIkzTnUwePpyxuL9Og') 
bot = telebot.TeleBot(API_TOKEN)
translator = Translator()

user_preferences = {} 

LANGUAGES_MAP = {
    'km': '🇰🇭 ខ្មែរ',
    'en': '🇬🇧 អង់គ្លេស',
    'ja': '🇯🇵 ជប៉ុន',
    'ko': '🇰🇷 កូរ៉េ',
    'hi': '🇮🇳 ឥណ្ឌា',
    'zh-cn': '🇨🇳 ចិន',
    'fr': '🇫🇷 បារាំង',
}

# ==========================================
# ៣. ផ្នែក DASHBOARD MENU
# ==========================================
def get_main_dashboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_translate = types.InlineKeyboardButton("🔤 បកប្រែអក្សរ", callback_data='menu_translate')
    btn_photo = types.InlineKeyboardButton("📸 បកប្រែរូបភាព", callback_data='menu_photo')
    btn_voice = types.InlineKeyboardButton("🎙️ បកប្រែសំឡេង", callback_data='menu_voice')
    btn_info = types.InlineKeyboardButton("ℹ️ អំពី Bot", callback_data='menu_info')
    markup.add(btn_translate, btn_photo, btn_voice, btn_info)
    return markup

def get_language_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for code, name in LANGUAGES_MAP.items():
        buttons.append(types.InlineKeyboardButton(name, callback_data=f'set_lang_{code}'))
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🔙 ត្រឡប់ទៅ Dashboard", callback_data='back_home'))
    return markup

def get_back_home_btn():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 ត្រឡប់ទៅ Dashboard", callback_data='back_home'))
    return markup

# ==========================================
# ៤. HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id not in user_preferences:
        user_preferences[message.chat.id] = 'km'
    
    bot.send_message(
        message.chat.id, 
        f"សួស្តី **{message.from_user.first_name}**! 👋\nសូមជ្រើសរើសមុខងារ៖", 
        parse_mode='Markdown', 
        reply_markup=get_main_dashboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == 'back_home':
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🏠 **Dashboard**", reply_markup=get_main_dashboard(), parse_mode='Markdown')
    elif call.data == 'menu_translate':
        current = LANGUAGES_MAP.get(user_preferences.get(chat_id, 'km'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"ភាសាបច្ចុប្បន្ន៖ **{current}**\nសូមជ្រើសរើសភាសា៖", reply_markup=get_language_keyboard(), parse_mode='Markdown')
    elif call.data.startswith('set_lang_'):
        code = call.data.split('_')[2]
        user_preferences[chat_id] = code
        bot.answer_callback_query(call.id, f"ប្តូរទៅជា {LANGUAGES_MAP[code]}")
        bot.send_message(chat_id, f"✅ បានកំណត់ភាសា **{LANGUAGES_MAP[code]}**", parse_mode='Markdown')
    elif call.data == 'menu_info':
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🤖 **Bot Info**\nCreate by: Sinan", reply_markup=get_back_home_btn(), parse_mode='Markdown')
    else:
        bot.answer_callback_query(call.id, "កំពុងអភិវឌ្ឍន៍", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    dest = user_preferences.get(message.chat.id, 'km')
    try:
        translated = translator.translate(message.text, dest=dest)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 ប្តូរភាសា", callback_data='menu_translate'))
        bot.reply_to(message, f"🔤 **បកប្រែ ({LANGUAGES_MAP.get(dest)}):**\n{translated.text}", parse_mode='Markdown', reply_markup=markup)
    except Exception:
        bot.reply_to(message, "Error translating.")

# ==========================================
# ៥. RUN SERVER & BOT
# ==========================================
keep_alive() # ដំណើរការ Web Server
bot.infinity_polling() # ដំណើរការ Bot
