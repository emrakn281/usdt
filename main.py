import requests
from flask import Flask
from bs4 import BeautifulSoup
import websocket
import json

binance_price = None
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

# Global değişken: Fiyatı saklamak için
# WebSocket URL'si
binance_ws_url = "wss://stream.binance.com:9443/ws/usdttry@trade"

# WebSocket callback fonksiyonu
def on_message(ws, message):
    global binance_price  # Global değişkeni güncelle
    data = json.loads(message)
    binance_price = float(data['p'])
    print(f"Canlı USDT/TRY Fiyatı: {binance_price} ₺")
    
    # Veriyi aldıktan sonra WebSocket bağlantısını kapatıyoruz
    ws.close()

def on_error(ws, error):
    print(f"WebSocket Hatası: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket bağlantısı kapandı")

def on_open(ws):
    print("WebSocket bağlantısı açıldı")

# WebSocket bağlantısını başlatıp fiyatı döndüren fonksiyon
def get_binance_price():
    ws = websocket.WebSocketApp(binance_ws_url, 
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.on_open = on_open
    ws.run_forever()

    return binance_price  # Fiyatı döndür

# Fiyatı al

# Binance USDT/TRY fiyatını çekme fonksiyonu (Selenium yok)


# USD/TRY kurunu çekme fonksiyonu
def get_google_usd_try():
    url = "https://yandex.com.tr/finance/convert?from=USD&to=TRY&source=main"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Döviz kuru verisini almak için doğru HTML elementini bulmamız lazım
        try:
            price_element = soup.find("span", class_="PriceValue")
            if price_element:
                price = float(price_element.text.replace(",", ".").strip())
                send_telegram_message(price)
                return price
        except Exception as e:
            send_telegram_message("Hata oluştu:", e)
    
    return None

# Fiyatları al, oranı hesapla ve Telegram'a gönder
import time

def calculate_and_send():
    while True:
        try:
            binance_price = get_binance_price()

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
