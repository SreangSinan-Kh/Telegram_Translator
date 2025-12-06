import telebot
from telebot import types
from deep_translator import GoogleTranslator
from gtts import gTTS
from flask import Flask
from threading import Thread
import os

# ==========================================
# ១. ផ្នែក KEEP ALIVE (Server)
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
# ២. ការកំណត់ BOT
# ==========================================
API_TOKEN = os.environ.get('BOT_TOKEN', '8223217940:AAH1tHD72PojpV0f4VIkzTnUwePpyxuL9Og') 
bot = telebot.TeleBot(API_TOKEN)

user_preferences = {} 

# កែសម្រួលកូដភាសា (សំខាន់: ចិនដាក់ zh-CN)
LANGUAGES_MAP = {
    'km': '🇰🇭 ខ្មែរ',
    'en': '🇬🇧 អង់គ្លេស',
    'ja': '🇯🇵 ជប៉ុន',
    'ko': '🇰🇷 កូរ៉េ',
    'hi': '🇮🇳 ឥណ្ឌា',
    'zh-CN': '🇨🇳 ចិន',  # <--- កែទៅជាអក្សរធំ
    'fr': '🇫🇷 បារាំង',
}

# ==========================================
# ៣. ផ្នែក DASHBOARD MENU
# ==========================================
def get_main_dashboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_translate = types.InlineKeyboardButton("🔤 បកប្រែអក្សរ", callback_data='menu_translate')
    btn_info = types.InlineKeyboardButton("ℹ️ អំពី Bot", callback_data='menu_info')
    markup.add(btn_translate, btn_info)
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
# ៤. HANDLERS (ដំណើរការ)
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
        bot.answer_callback_query(call.id, f"ប្តូរទៅជា {LANGUAGES_MAP.get(code, code)}")
        bot.send_message(chat_id, f"✅ បានកំណត់ភាសា **{LANGUAGES_MAP.get(code, code)}**\n\nសូមផ្ញើសារមក ខ្ញុំនឹងបកប្រែ និងអានជូន។ 👇", parse_mode='Markdown')
    elif call.data == 'menu_info':
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🤖 **Bot Info**\nCreate by: Sinan", reply_markup=get_back_home_btn(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    dest_lang = user_preferences.get(chat_id, 'km')
    
    try:
        # បង្ហាញថា Bot កំពុងធ្វើការ (Typing...)
        bot.send_chat_action(chat_id, 'typing')

        # 1. បកប្រែ
        # ប្រើ GoogleTranslator ជាមួយ source='auto'
        translated_text = GoogleTranslator(source='auto', target=dest_lang).translate(message.text)
        
        reply_text = f"🔤 **បកប្រែ ({LANGUAGES_MAP.get(dest_lang, dest_lang)}):**\n{translated_text}"
        bot.reply_to(message, reply_text, parse_mode='Markdown')

        # 2. បង្កើតសំឡេង (Voice)
        # ដាក់លក្ខខណ្ឌ៖ បើភាសាខ្មែរ (km) ឬ ចិន (zh-CN) អាចនឹងមានបញ្ហា TTS ខ្លះ
        # ប៉ុន្តែយើងសាកល្បងទាំងអស់
        if dest_lang != 'km': 
            try:
                bot.send_chat_action(chat_id, 'record_audio')
                tts_lang = dest_lang
                if dest_lang == 'zh-CN': tts_lang = 'zh' # gTTS ប្រើ 'zh' សម្រាប់ចិន

                tts = gTTS(text=translated_text, lang=tts_lang)
                filename = f"voice_{chat_id}.mp3"
                tts.save(filename)
                
                with open(filename, 'rb') as audio:
                    bot.send_voice(chat_id, audio)
                
                os.remove(filename)
            except Exception as e_voice:
                print(f"Voice Error: {e_voice}")
                # មិនបាច់ប្រាប់ user ទេ បើសំឡេងខូច គ្រាន់តែមិនផ្ញើសំឡេង

    except Exception as e:
        # បង្ហាញ Error ជាក់លាក់ទៅកាន់ User ដើម្បីងាយស្រួលដោះស្រាយ
        error_msg = str(e)
        bot.reply_to(message, f"⚠️ **មានបញ្ហា៖**\n`{error_msg}`\n\nសូមព្យាយាមប្តូរភាសា ឬសាកល្បងម្តងទៀត។", parse_mode='Markdown')
        print(f"Translation Error: {e}")

# ==========================================
# ៥. RUN
# ==========================================
keep_alive()
bot.infinity_polling()
