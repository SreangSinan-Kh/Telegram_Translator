import telebot
from telebot import types
from googletrans import Translator

# ==========================================
# ១. ការកំណត់ (CONFIGURATION)
# ==========================================
API_TOKEN = '8223217940:AAH1tHD72PojpV0f4VIkzTnUwePpyxuL9Og'  # <--- ដាក់ Token របស់អ្នកនៅទីនេះ
bot = telebot.TeleBot(API_TOKEN)
translator = Translator()

# ផ្ទុកទិន្នន័យអ្នកប្រើប្រាស់បណ្តោះអាសន្ន (សន្មតថាអ្នកប្រើចង់បកប្រែទៅភាសាខ្មែរជាគោល)
user_preferences = {} 

# បញ្ជីភាសាដែលបានកែសម្រួល (ដកថៃ, បន្ថែម ជប៉ុន កូរ៉េ ឥណ្ឌា)
LANGUAGES_MAP = {
    'km': '🇰🇭 ខ្មែរ',
    'en': '🇬🇧 អង់គ្លេស',
    'ja': '🇯🇵 ជប៉ុន',   # បន្ថែម
    'ko': '🇰🇷 កូរ៉េ',    # បន្ថែម
    'hi': '🇮🇳 ឥណ្ឌា',   # បន្ថែម (Hindi)
    'zh-cn': '🇨🇳 ចិន',
    'fr': '🇫🇷 បារាំង',
    # 'th': '🇹🇭 ថៃ'     <-- បានដកចេញ
}

# ==========================================
# ២. ផ្នែករចនា MENU / DASHBOARD
# ==========================================

def get_main_dashboard():
    """បង្កើតផ្ទាំង Dashboard ដើម"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # បង្កើតប៊ូតុង
    btn_translate = types.InlineKeyboardButton("🔤 បកប្រែអក្សរ", callback_data='menu_translate')
    btn_photo = types.InlineKeyboardButton("📸 បកប្រែរូបភាព", callback_data='menu_photo')
    btn_voice = types.InlineKeyboardButton("🎙️ បកប្រែសំឡេង", callback_data='menu_voice')
    btn_info = types.InlineKeyboardButton("ℹ️ អំពី Bot", callback_data='menu_info')
    
    # ដាក់ប៊ូតុងចូល
    markup.add(btn_translate, btn_photo, btn_voice, btn_info)
    return markup

def get_language_keyboard():
    """បង្កើតផ្ទាំងជ្រើសរើសភាសាគោលដៅ"""
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for code, name in LANGUAGES_MAP.items():
        buttons.append(types.InlineKeyboardButton(name, callback_data=f'set_lang_{code}'))
    
    markup.add(*buttons)
    # ប៊ូតុងត្រឡប់ក្រោយ
    markup.add(types.InlineKeyboardButton("🔙 ត្រឡប់ទៅ Dashboard", callback_data='back_home'))
    return markup

def get_back_home_btn():
    """ប៊ូតុងត្រឡប់ទៅដើម"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 ត្រឡប់ទៅ Dashboard", callback_data='back_home'))
    return markup

# ==========================================
# ៣. ដំណើរការ COMMANDS & HANDLERS
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    # កំណត់ភាសាដើមជា ខ្មែរ សម្រាប់អ្នកប្រើថ្មី
    if message.chat.id not in user_preferences:
        user_preferences[message.chat.id] = 'km'

    text = (
        f"សួស្តី **{user_name}**! 👋\n\n"
        "សូមស្វាគមន៍មកកាន់ **AI Dashboard Bot**។\n"
        "សូមជ្រើសរើសមុខងារដែលអ្នកចង់ប្រើប្រាស់ខាងក្រោម៖"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=get_main_dashboard())

# ទទួលការចុចលើប៊ូតុង (Callback Query)
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    
    # 1. ត្រឡប់ទៅផ្ទាំងដើម (Dashboard)
    if call.data == 'back_home':
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="🏠 **ផ្ទាំងដើម (Dashboard)**\nសូមជ្រើសរើសមុខងារ៖",
            parse_mode='Markdown',
            reply_markup=get_main_dashboard()
        )

    # 2. ចូលទៅម៉ឺនុយបកប្រែ (Translate Menu)
    elif call.data == 'menu_translate':
        current_lang = user_preferences.get(chat_id, 'km')
        lang_name = LANGUAGES_MAP.get(current_lang, current_lang)
        
        text = (
            f"🔤 **មុខងារបកប្រែអក្សរ**\n\n"
            f"ភាសាគោលដៅបច្ចុប្បន្នគឺ៖ **{lang_name}**\n"
            "សូមជ្រើសរើសភាសាដែលអ្នកចង់បកប្រែទៅ៖"
        )
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=get_language_keyboard()
        )

    # 3. ការកំណត់ភាសា (Set Language)
    elif call.data.startswith('set_lang_'):
        lang_code = call.data.split('_')[2]
        user_preferences[chat_id] = lang_code # រក្សាទុកភាសាដែលបានរើស
        lang_name = LANGUAGES_MAP.get(lang_code)
        
        bot.answer_callback_query(call.id, f"បានប្តូរទៅជាភាសា {lang_name}")
        bot.send_message(
            chat_id, 
            f"✅ បានកំណត់បកប្រែទៅជា៖ **{lang_name}**\n\nសូមផ្ញើសារ ឬអត្ថបទមក ខ្ញុំនឹងបកប្រែជូនភ្លាមៗ។ 👇",
            parse_mode='Markdown'
        )

    # 4. មុខងារផ្សេងៗ (Placeholder)
    elif call.data in ['menu_photo', 'menu_voice']:
        bot.answer_callback_query(call.id, "មុខងារនេះកំពុងអភិវឌ្ឍន៍", show_alert=True)
    
    elif call.data == 'menu_info':
        info_text = "🤖 **អំពី Bot**\n\nBot នេះបង្កើតឡើងដើម្បីជួយសម្រួលការងារបកប្រែ និងការងាររដ្ឋបាលផ្សេងៗ។\nCreate by: Sinan"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=info_text,
            parse_mode='Markdown',
            reply_markup=get_back_home_btn()
        )

# ទទួលសារជាអក្សរ និងធ្វើការបកប្រែ
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    dest_lang = user_preferences.get(chat_id, 'km') # យកភាសាដែលបានកំណត់ (default: km)
    
    try:
        # បង្ហាញ status ថា "typing..."
        bot.send_chat_action(chat_id, 'typing')
        
        # ធ្វើការបកប្រែ
        translated = translator.translate(message.text, dest=dest_lang)
        
        reply_text = (
            f"🔤 **លទ្ធផលបកប្រែ ({LANGUAGES_MAP.get(dest_lang, dest_lang)}):**\n"
            f"-------------------\n"
            f"{translated.text}"
        )
        
        # បង្ហាញប៊ូតុងសម្រាប់ប្តូរភាសាវិញនៅខាងក្រោមសារ
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 ប្តូរភាសា", callback_data='menu_translate'))
        
        bot.reply_to(message, reply_text, parse_mode='Markdown', reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, "សូមអភ័យទោស មានបញ្ហាក្នុងការបកប្រែ។ សូមព្យាយាមម្តងទៀត។")
        print(f"Error: {e}")

# ==========================================
# ៤. ចាប់ផ្តើម BOT
# ==========================================
print("Bot is running...")
bot.infinity_polling()
