import os
import telebot
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

# Token Render muhit o'zgaruvchilaridan (Environment Variables) olinadi
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN muhit o'zgaruvchisi topilmadi!")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Salom! 👋\n\nMenga istalgan veb-sahifa havolasini yuboring, men o'sha sahidadagi barcha rasmlarni topib sizga yuboraman."
    )

@bot.message_handler(func=lambda message: True)
def handle_url(message):
    url = message.text.strip()
    
    # Havola to'g'riligini tekshirish
    if not url.startswith('http://') and not url.startswith('https://'):
        bot.reply_to(message, "❌ Iltimos, to'g'ri havola (URL) yuboring (masalan: https://example.com)")
        return
    
    processing_msg = bot.reply_to(message, "⏳ Havola tekshirilmoqda va rasmlar qidirilmoqda...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            bot.edit_message_text("❌ Kechirasiz, bu sahifaga ulanib bo'lmadi yoki sayt kirishni cheklagan.", message.chat.id, processing_msg.message_id)
            return
        
        # HTML sahifani tahlil qilish
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')
        
        image_urls = []
        for img in img_tags:
            img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if img_url:
                # Nisbiy havolalarni to'liq manzilga aylantirish
                full_url = urljoin(url, img_url)
                if full_url.startswith('http://') or full_url.startswith('https://'):
                    image_urls.append(full_url)
        
        # Takrorlangan rasmlarni olib tashlash
        image_urls = list(set(image_urls))
        
        if not image_urls:
            bot.edit_message_text("❌ Bu havoladan hech qanday rasm topilmadi.", message.chat.id, processing_msg.message_id)
            return
        
        bot.edit_message_text(f"✅ Topildi: {len(image_urls)} ta rasm. Ularni yuborishni boshlayman...", message.chat.id, processing_msg.message_id)
        
        sent_count = 0
        # Telegram limiti uchun ko'pi bilan 20 ta rasmni yuboramiz
        for img_url in image_urls[:20]:
            try:
                bot.send_photo(message.chat.id, img_url)
                sent_count += 1
            except Exception:
                continue
                
        bot.send_message(message.chat.id, f"🎉 Jami {sent_count} ta rasm muvaffaqiyatli yuborildi!")
        
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}", message.chat.id, processing_msg.message_id)

if __name__ == '__main__':
    print("Bot ishga tushdi...")
    bot.infinity_polling()
