import requests
from flask import Flask, render_template_string
from bs4 import BeautifulSoup
import websocket
import json
from datetime import datetime, timedelta

binance_price = None
# Flask uygulaması oluştur
app = Flask(__name__)

last_message = ""
last_action = ""
last_action_time = None
status=""

@app.route('/')
def home():
    # Web sitesinde gösterilecek mesaj
    return render_template_string("""
        <!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>USDT BOT LIVE</title>
<style>
               body {
                   font-family: Arial, sans-serif;
                   background-color: #121212;
                   color: #ffffff;
                   text-align: center;
                   padding: 20px;
               }
               .container {
                   max-width: 600px;
                   margin: auto;
                   background: #1e1e1e;
                   padding: 20px;
                   border-radius: 10px;
                   box-shadow: 0px 0px 15px rgba(255, 255, 255, 0.2);
               }
               h1 {
                   color: #00ffcc;
                   text-shadow: 2px 2px 5px rgba(0, 255, 204, 0.5);
               }
               .price {
                   font-size: 24px;
                   font-weight: bold;
                   color: #ffcc00;
               }
               .status {
                   font-size: 20px;
                   font-weight: bold;
                   padding: 10px;
                   border-radius: 5px;
                   display: inline-block;
               }
               .buy { background-color: #009900; color: white; }
               .sell { background-color: #cc0000; color: white; }
               .wait { background-color: #666666; color: white; }
               .time {
                   font-size: 16px;
                   margin-top: 10px;
                   color: #bbbbbb;
               }
</style>
</head>
<body>
<div class="container">
<h1>📊 USDT BOT DURUMU 📊</h1>

<p class="status {{ 'buy' if l_action == 'AL' else 'sell' if l_action == 'SAT' else 'wait' }}">
                   🔔 Durum: <strong>{{ l_action if l_action else 'BEKLE' }}</strong>
</p>
<p class="price">💰 Binance USDT/TRY: <strong>{{ message }}</strong></p>
<p class="price">💱 Google USD/TRY: <strong>{{ l_action }}</strong></p>

<p class="time">🕒 Son Mesaj Gönderimi: {{ l_time }}</p>
</div>
</body>
</html>
   """, message=last_message, l_action=status, l_time=last_action_time)

# Flask'i arka planda çalıştırmak için thread kullan
import threading
def run_flask():
    app.run(host='0.0.0.0', port=5080)

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
                return price
        except Exception as e:
            last_message = e
    
    return None

# Fiyatları al, oranı hesapla ve Telegram'a gönder
import time

def calculate_and_send():
    global last_message  # Global değişkeni güncelleyeceğiz
    global last_action
    global last_action_time
    global status
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

            # eğer fark 0,2 den büyükse sat 0 dan küçükse al eğer başka bir şey ise bekle

            action = "BEKLE"
            if difference < -1.95:
                action = "SAT"
                status ="SAT"
            elif difference > 0:
                action = "AL"
                status ="AL"
            else:
                action = "BEKLE"
                status ="BEKLE"
                last_action=""

            message = (
                f"📢 **{action}** 📢\n"
                f"🔹 **Binance USDT/TRY**: {binance_price} ₺\n"
                f"🔹 **Yandex USD/TRY**: {google_price} ₺\n"
                f"🔹 **Fark**: %{difference:.2f}\n"
            )
            html_message = (
                f"📢 **{action}** 📢\n<br>"
                f"🔹 **Binance USDT/TRY**: {binance_price} ₺\n<br>"
                f"🔹 **Yandex USD/TRY**: {google_price} ₺\n<br>"
                f"🔹 **Fark**: %{difference:.2f}\n<br>"
            )
            
            
            suan = datetime.now()
            if last_action_time is None:  # Eğer 'son' değişkeni daha önce atanmadıysa, şu anki zamana eşitle
                last_action_time = suan
            if action != "BEKLE":
                if last_action != action:
                    send_telegram_message(message)
                    last_action_time = suan
                    last_action=action
                    print("Mesaj gönderildi:", message)
                else:
                    fark = suan - last_action_time
                    if fark>= timedelta(minutes=10):
                        send_telegram_message(message)
                        last_action_time = suan
                        last_action=action
                        print("Mesaj gönderildi:", message)
            last_message = html_message

        except Exception as e:
            print("Hata:", e)
            last_message = e

        # 1 dakika bekle (60 saniye)
        time.sleep(60)

# Hesaplama fonksiyonunu çalıştır
calculate_and_send() 
