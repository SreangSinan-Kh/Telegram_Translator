import os
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from docx import Document
from pypdf import PdfReader
from deep_translator import GoogleTranslator
from gtts import gTTS
from flask import Flask, request

# ⚠️ ដាក់ Token របស់បងនៅទីនេះ
BOT_TOKEN = '8223217940:AAH1tHD72PojpV0f4VIkzTnUwePpyxuL9Og'
bot = telebot.TeleBot(BOT_TOKEN)

# Flask App សម្រាប់ឱ្យ Render ស្គាល់ថាមាន Web Service ដំណើរការ
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running happy! 🚀"

def run_web_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# --- Logic របស់ Bot ---

user_preferences = {}

LANGUAGES = {
    'km': {'name': 'ខ្មែរ 🇰🇭', 'code': 'km'},
    'en': {'name': 'English 🇺🇸', 'code': 'en'},
    'zh-CN': {'name': 'Chinese 🇨🇳', 'code': 'zh-CN'},
    'th': {'name': 'Thai 🇹🇭', 'code': 'th'},
    'fr': {'name': 'French 🇫🇷', 'code': 'fr'}
}

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btns = [KeyboardButton(val['name']) for val in LANGUAGES.values()]
    markup.add(*btns)
    return markup

def get_target_lang_code(user_id):
    lang_name = user_preferences.get(user_id, 'ខ្មែរ 🇰🇭')
    for key, val in LANGUAGES.items():
        if val['name'] == lang_name:
            return val['code']
    return 'km'

def smart_translate(text, target_lang):
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        if len(text) < 4500:
            return translator.translate(text)
        chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
        return " ".join([translator.translate(chunk) for chunk in chunks])
    except Exception as e:
        return f"Translation Error: {e}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
                 "👋 **សួស្តី!**\nសូមជ្រើសរើសភាសាគោលដៅដែលបងចង់បកប្រែទៅ៖",
                 parse_mode='Markdown',
                 reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: message.text in [val['name'] for val in LANGUAGES.values()])
def set_language(message):
    user_preferences[message.from_user.id] = message.text
    bot.reply_to(message, f"✅ បានកំណត់យក៖ **{message.text}**\nឥឡូវផ្ញើអក្សរមកចុះ!", parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'): return
    
    target_code = get_target_lang_code(message.from_user.id)
    target_name = user_preferences.get(message.from_user.id, 'ខ្មែរ 🇰🇭')
    
    bot.send_chat_action(message.chat.id, 'typing')
    translated = smart_translate(message.text, target_code)
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔊 ស្តាប់សំឡេង", callback_data=f"tts_{target_code}"))
    
    bot.reply_to(message, f"🎯 **{target_name}:**\n\n{translated}", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('tts_'))
def callback_tts(call):
    try:
        lang_code = call.data.split('_')[1]
        text = call.message.text.split('\n\n', 1)[-1]
        bot.answer_callback_query(call.id, "កំពុងដំណើរការសំឡេង...")
        bot.send_chat_action(call.message.chat.id, 'upload_voice')
        tts = gTTS(text=text, lang=lang_code)
        filename = f"voice_{call.from_user.id}.mp3"
        tts.save(filename)
        with open(filename, 'rb') as audio:
            bot.send_voice(call.message.chat.id, audio)
        os.remove(filename)
    except Exception as e:
        print(e)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        bot.reply_to(message, "📂 កំពុងអានឯកសារ...")
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        temp = f"temp_{message.document.file_name}"
        with open(temp, 'wb') as f: f.write(downloaded)
        
        ext = os.path.splitext(temp)[1].lower()
        text = ""
        if ext == '.docx': text = "\n".join([p.text for p in Document(temp).paragraphs])
        elif ext == '.pdf': 
            try: text = "".join([p.extract_text() for p in PdfReader(temp).pages])
            except: pass
        elif ext == '.txt':
            with open(temp, 'r', encoding='utf-8') as f: text = f.read()

        if text.strip():
            bot.reply_to(message, "🔄 កំពុងបកប្រែ...")
            target = get_target_lang_code(message.from_user.id)
            translated = smart_translate(text, target)
            out_file = f"Translated_{message.document.file_name}.txt"
            with open(out_file, 'w', encoding='utf-8') as f: f.write(translated)
            with open(out_file, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ រួចរាល់!")
            os.remove(out_file)
        else:
            bot.reply_to(message, "❌ អានអក្សរមិនបាន។")
        if os.path.exists(temp): os.remove(temp)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

if __name__ == "__main__":
    t = threading.Thread(target=run_web_server)
    t.start()
    bot.infinity_polling()
