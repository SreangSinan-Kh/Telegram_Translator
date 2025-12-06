import telebot
from telebot import types
from deep_translator import GoogleTranslator
from gtts import gTTS
from flask import Flask
from threading import Thread
import os
import io
import PyPDF2
import docx

# ==========================================
# ១. ផ្នែក KEEP ALIVE (Server)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running with Dashboard & File Support!"

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

# ដាក់ Link រូបភាពសម្រាប់ Dashboard (បងអាចប្តូរ Link នេះតាមចិត្ត)
BANNER_IMAGE_URL = "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?q=80&w=1470&auto=format&fit=crop"

user_preferences = {} 

LANGUAGES_MAP = {
    'km': '🇰🇭 ខ្មែរ',
    'en': '🇬🇧 អង់គ្លេស',
    'ja': '🇯🇵 ជប៉ុន',
    'ko': '🇰🇷 កូរ៉េ',
    'hi': '🇮🇳 ឥណ្ឌា',
    'zh-CN': '🇨🇳 ចិន',
    'fr': '🇫🇷 បារាំង',
}

# ==========================================
# ៣. ផ្នែក DASHBOARD MENU (DESIGN ថ្មី)
# ==========================================
def get_main_dashboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    # ប៊ូតុងរៀបជាជួរស្អាត
    btn_translate = types.InlineKeyboardButton("🔤 បកប្រែអក្សរ", callback_data='menu_translate')
    btn_file = types.InlineKeyboardButton("📂 បកប្រែឯកសារ", callback_data='menu_file')
    btn_voice = types.InlineKeyboardButton("🗣️ សំឡេង", callback_data='menu_voice')
    btn_info = types.InlineKeyboardButton("ℹ️ អំពី Bot", callback_data='menu_info')
    
    markup.add(btn_translate, btn_file, btn_voice, btn_info)
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
# ៤. មុខងារជំនួយ (HELPER FUNCTIONS)
# ==========================================
def split_message(text, limit=4000):
    """កាត់អក្សរវែងៗជាកង់ៗ ដើម្បីផ្ញើតាម Telegram កុំឱ្យ Error"""
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def translate_and_reply(message, text_to_translate):
    chat_id = message.chat.id
    dest_lang = user_preferences.get(chat_id, 'km')
    
    try:
        translated = GoogleTranslator(source='auto', target=dest_lang).translate(text_to_translate)
        
        # បើអក្សរវែងពេក ត្រូវកាត់ផ្ញើម្ដងមួយៗ
        chunks = split_message(translated)
        bot.reply_to(message, f"✅ **លទ្ធផលបកប្រែ ({LANGUAGES_MAP.get(dest_lang)}):**", parse_mode='Markdown')
        
        for chunk in chunks:
            bot.send_message(chat_id, chunk)
            
        # (Option) បង្កើតសំឡេង
        if dest_lang != 'km' and len(translated) < 500: # កុំអានបើវែងពេក
            tts = gTTS(text=translated, lang=(dest_lang if dest_lang != 'zh-CN' else 'zh'))
            filename = f"voice_{chat_id}.mp3"
            tts.save(filename)
            with open(filename, 'rb') as audio:
                bot.send_voice(chat_id, audio)
            os.remove(filename)
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ បញ្ហា៖ {e}")

# ==========================================
# ៥. HANDLERS (ដំណើរការ)
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id not in user_preferences:
        user_preferences[message.chat.id] = 'km'
    
    caption_text = (
        f"សួស្តី **{message.from_user.first_name}**! 👋\n\n"
        "សូមស្វាគមន៍មកកាន់ **Smart Translator Bot ដែលបង្កើតដោយលោក ស៊ីណាន** 🚀\n"
        "ខ្ញុំអាចជួយអ្នកបកប្រែអក្សរ រូបភាព និងឯកសារ (Word/PDF) បានយ៉ាងងាយស្រួល។\n\n"
        "👇 **សូមជ្រើសរើសមុខងារខាងក្រោម៖**"
    )
    
    # ផ្ញើរូបភាព Banner មុននឹងបង្ហាញ Menu
    bot.send_photo(
        message.chat.id, 
        BANNER_IMAGE_URL, 
        caption=caption_text, 
        parse_mode='Markdown', 
        reply_markup=get_main_dashboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    
    if call.data == 'back_home':
        # ពេលត្រឡប់ក្រោយ យើងលុបសារចាស់ចោល ហើយផ្ញើផ្ទាំងថ្មីដែលមានរូប
        bot.delete_message(chat_id, call.message.message_id)
        send_welcome(call.message) # ហៅមុខងារ start មកវិញ
        
    elif call.data == 'menu_translate':
        current = LANGUAGES_MAP.get(user_preferences.get(chat_id, 'km'))
        bot.send_message(chat_id, f"🔤 **បកប្រែអក្សរ**\nភាសាបច្ចុប្បន្ន៖ **{current}**\n\nសូមជ្រើសរើសភាសាគោលដៅ៖", reply_markup=get_language_keyboard(), parse_mode='Markdown')
        
    elif call.data == 'menu_file':
        bot.send_message(chat_id, "📂 **បកប្រែឯកសារ**\n\nសូមផ្ញើ File **Word (.docx)** ឬ **PDF** មកខ្ញុំ។\nខ្ញុំនឹងអានអក្សរខាងក្នុង ហើយបកប្រែជូនភ្លាមៗ!", reply_markup=get_back_home_btn(), parse_mode='Markdown')
        
    elif call.data == 'menu_voice':
         bot.send_message(chat_id, "🎙️ **មុខងារសំឡេង**\n\nគ្រាន់តែផ្ញើអក្សរមក ខ្ញុំនឹងបកប្រែ និងអានជូន។ (ភាសាខ្មែរមិនទាន់មានសំឡេងទេ)", reply_markup=get_back_home_btn())

    elif call.data.startswith('set_lang_'):
        code = call.data.split('_')[2]
        user_preferences[chat_id] = code
        bot.answer_callback_query(call.id, f"ប្តូរទៅជា {LANGUAGES_MAP.get(code)}")
        bot.send_message(chat_id, f"✅ បានកំណត់ភាសា **{LANGUAGES_MAP.get(code)}** រួចរាល់!", parse_mode='Markdown')

    elif call.data == 'menu_info':
        bot.send_message(chat_id, "🤖 **Bot Info**\nVersion: 2.0 (Pro)\nFeatures: Text, Voice, PDF, Word\nDev: Sinan", reply_markup=get_back_home_btn())

# --- ផ្នែកទទួលសារអក្សរ ---
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    translate_and_reply(message, message.text)

# --- ផ្នែកទទួលឯកសារ (WORD & PDF) ---
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = message.chat.id
    try:
        file_info = bot.get_file(message.document.file_id)
        file_extension = os.path.splitext(message.document.file_name)[1].lower()

        if file_extension not in ['.pdf', '.docx']:
            bot.reply_to(message, "⚠️ សូមអភ័យទោស! ខ្ញុំស្គាល់តែ File **.pdf** និង **.docx** (Word) ប៉ុណ្ណោះ។")
            return

        bot.send_chat_action(chat_id, 'upload_document')
        bot.reply_to(message, "⏳ កំពុងទាញយក និងអានឯកសារ...")

        # ទាញយកឯកសារ
        downloaded_file = bot.download_file(file_info.file_path)
        extracted_text = ""

        # ១. បើជា PDF
        if file_extension == '.pdf':
            with io.BytesIO(downloaded_file) as open_pdf_file:
                read_pdf = PyPDF2.PdfReader(open_pdf_file)
                for page in read_pdf.pages:
                    extracted_text += page.extract_text() + "\n"
        
        # ២. បើជា Word (.docx)
        elif file_extension == '.docx':
            with io.BytesIO(downloaded_file) as open_docx_file:
                doc = docx.Document(open_docx_file)
                for para in doc.paragraphs:
                    extracted_text += para.text + "\n"

        # ពិនិត្យមើលថាមានអក្សរទេ?
        if len(extracted_text.strip()) == 0:
            bot.reply_to(message, "⚠️ ឯកសារនេះមិនមានអក្សរដែលខ្ញុំអាចអានបានទេ។ (ប្រហែលជាវាជារូបភាព scan?)")
            return

        # ចាប់ផ្តើមបកប្រែ
        bot.reply_to(message, "✅ បានអានរួចរាល់! កំពុងបកប្រែ...")
        translate_and_reply(message, extracted_text)

    except Exception as e:
        bot.reply_to(message, f"❌ មានបញ្ហាក្នុងការអានឯកសារ៖ {e}")

# ==========================================
# ៦. RUN
# ==========================================
keep_alive()
try:
    bot.infinity_polling()
except:
    pass

