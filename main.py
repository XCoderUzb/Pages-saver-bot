import os
import time
import requests
import telebot
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from flask import Flask
import threading

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN muhit o'zgaruvchisi topilmadi!")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Render port talabini qondirish uchun oddiy sahifa
@app.route('/')
def home():
    print("Ping olindi, bot ishlayapti!")
    return "Telegram Bot is running smoothly!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Salom! 👋\n\nMenga istalgan veb-sahifa havolasini yuboring, men o'sha sahidadagi barcha rasmlarni yuboraman."
    )

@bot.message_handler(func=lambda message: True)
def handle_url(message):
    url = message.text.strip()
    
    if not url.startswith('http://') and not url.startswith('https://'):
        bot.reply_to(message, "❌ Iltimos, to'g'ri havola (URL) yuboring (masalan: https://example.com)")
        return
    
    processing_msg = bot.reply_to(message, "⏳ Sahifa tahlil qilinmoqda va rasmlar yig'ilmoqda...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            bot.edit_message_text("❌ Kechirasiz, sayt kirishni chekladi yoki sahifa topilmadi.", message.chat.id, processing_msg.message_id)
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')
        
        image_urls = []
        for img in img_tags:
            img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
            if img_url:
                full_url = urljoin(url, img_url)
                if full_url.startswith('http://') or full_url.startswith('https://'):
                    image_urls.append(full_url)
        
        unique_images = list(dict.fromkeys(image_urls))
        
        if not unique_images:
            bot.edit_message_text("❌ Bu havoladan hech qanday rasm topilmadi.", message.chat.id, processing_msg.message_id)
            return
        
        total_count = len(unique_images)
        bot.edit_message_text(f"✅ Topildi: {total_count} ta rasm. Telegram chekloviga tushmasligi uchun sekin-asta yuborilmoqda...", message.chat.id, processing_msg.message_id)
        
        sent_count = 0
        for idx, img_url in enumerate(unique_images, start=1):
            try:
                img_data = requests.get(img_url, headers=headers, timeout=10).content
                bot.send_photo(message.chat.id, img_data, caption=f"Rasm {idx}/{total_count}")
                sent_count += 1
                # Telegram spamlardan saqlash va rate-limit'ga tushmaslik uchun tanaffus
                time.sleep(1.2)
            except Exception:
                continue
                
        bot.send_message(message.chat.id, f"🎉 Muvaffaqiyatli yuklandi: {sent_count} / {total_count} ta rasm!")
        
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}", message.chat.id, processing_msg.message_id)

def run_bot():
    print("Telegram bot polling boshlandi...")
    bot.infinity_polling(none_stop=True)

if __name__ == '__main__':
    # Telegram botni alohida oqimda (background thread) ishga tushiramiz
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Render taqdim etadigan PORT orqali Flask veb-serverini ishga tushiramiz (port ochish uchun)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
