import requests
from flask import Flask

# Flask uygulaması oluştur
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Flask'i arka planda çalıştırmak için thread kullan
import threading
def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# Telegram Bot Bilgileri
TOKEN = "7996664982:AAEmhzaXiE1rL2Dj0pBiJhzjiw6JwkHK59w"
CHAT_ID = "-4761304742"

# Telegram'a mesaj gönderme fonksiyonu
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# Binance USDT/TRY fiyatını çekme fonksiyonu (Selenium yok)
def get_binance_usdt_try():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=USDTTRY"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return float(data["price"])
    return None

# USD/TRY kurunu çekme fonksiyonu
def get_google_usd_try():
    url = "https://api.exchangerate.host/latest?base=USD&symbols=TRY"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return float(data["rates"]["TRY"])
    return None

# Fiyatları al, oranı hesapla ve Telegram'a gönder
import time

def calculate_and_send():
    while True:
        try:
            binance_price = get_binance_usdt_try()
            google_price = get_google_usd_try()

            print(f"Binance USDT/TRY: {binance_price}")
            print(f"Google USD/TRY: {google_price}")

            if binance_price is None or google_price is None:
                raise ValueError("Fiyat bilgileri alınamadı!")

            # Farkı hesapla
            difference = ((google_price - binance_price) / google_price) * 100
            message = (
                f"📢 **Fiyat Güncellemesi** 📢\n"
                f"🔹 **Binance USDT/TRY**: {binance_price} ₺\n"
                f"🔹 **Google USD/TRY**: {google_price} ₺\n"
                f"🔹 **Fark**: %{difference:.2f}\n"
            )

            send_telegram_message(message)
            print("Mesaj gönderildi:", message)

        except Exception as e:
            send_telegram_message(f"Hata oluştu: {e}")
            print("Hata:", e)

        # 1 dakika bekle (60 saniye)
        time.sleep(60)

# Hesaplama fonksiyonunu çalıştır
calculate_and_send()
