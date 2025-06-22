import telebot
from telebot import types
import os
import base64
import time

API_TOKEN = '7967640262:AAFKCefly9fEBLVTUXm1BeOPQ1GPLKd_bkE'
CHANNEL_USERNAME = '@vxwwo'  

bot = telebot.TeleBot(API_TOKEN)

# Caching cases 
user_states = {}
user_files = {}
user_encrypt_type = {}

# Subscription verification 
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
    
    if chat_member.status in ['member', 'administrator', 'creator']:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn = types.KeyboardButton('encryption/')
        markup.add(btn)
        bot.send_message(user_id, '*Welcome to Primex Core Encryption Bot!*\nClick "encryption/" to continue.', parse_mode='Markdown', reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('🔒 Join Channel', url=f'https://t.me/{CHANNEL_USERNAME[1:]}')
        markup.add(btn)
        bot.send_message(user_id, '*Please join our channel first to use this bot.*', parse_mode='Markdown', reply_markup=markup)

# استقبال "encryption/"
@bot.message_handler(func=lambda m: m.text.lower() == 'encryption/')
def ask_encryption_type(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Base64', callback_data='base64')
    btn2 = types.InlineKeyboardButton('Marshal', callback_data='marshal')
    btn3 = types.InlineKeyboardButton('Zlib+Base64', callback_data='zlib')
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, '*Select encryption type:*', parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['base64', 'marshal', 'zlib'])
def encryption_type_chosen(call):
    user_id = call.from_user.id
    user_encrypt_type[user_id] = call.data
    user_states[user_id] = 'awaiting_file'
    bot.send_message(user_id, '*Ok. Now send the file you want to encrypt (make sure it\'s in .py format).*', parse_mode='Markdown')

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    if user_states.get(user_id) == 'awaiting_file':
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name

        if not file_name.endswith('.py'):
            bot.send_message(user_id, '*Only .py files are supported.*', parse_mode='Markdown')
            return

        file_path = file_info.file_path
        downloaded_file = bot.download_file(file_path)
        user_files[user_id] = downloaded_file.decode()
        user_states[user_id] = 'awaiting_filename'

        bot.send_message(user_id, '*Checking...\nNow send the file name you want to encrypt.*', parse_mode='Markdown')

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'awaiting_filename')
def handle_filename(message):
    user_id = message.from_user.id
    file_content = user_files.get(user_id)
    encrypt_type = user_encrypt_type.get(user_id)
    filename = message.text.strip()

    bot.send_message(user_id, '*Please wait, your file is being encrypted...*', parse_mode='Markdown')

    if encrypt_type == 'base64':
        encrypted = base64.b64encode(file_content.encode()).decode()
    elif encrypt_type == 'marshal':
        import marshal
        encrypted = marshal.dumps(compile(file_content, '', 'exec'))
        encrypted = base64.b64encode(encrypted).decode()
    elif encrypt_type == 'zlib':
        import zlib
        compressed = zlib.compress(file_content.encode())
        encrypted = base64.b64encode(compressed).decode()
    else:
        encrypted = file_content

    final_code = f"#Encrypted by primex\nexec(__import__('base64').b64decode('{encrypted}'))"

    with open(filename + '.py', 'w') as f:
        f.write(final_code)

    with open(filename + '.py', 'rb') as f:
        bot.send_document(user_id, f, caption='*Encryption is complete. Thank you for waiting.*', parse_mode='Markdown')

    os.remove(filename + '.py')
    user_states.pop(user_id, None)
    user_files.pop(user_id, None)
    user_encrypt_type.pop(user_id, None)

bot.polling(non_stop=True)