import requests
from flask import Flask, render_template_string, jsonify
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
oran=""
USDTTRY= None
USDTRY= None
# Fiyat geçmişini saklamak için liste
price_history = []
def update_price_history(timestamp, binance, yandex, difference):
    if len(price_history) >= 1000:
        price_history.pop(0)
    price_history.append({
        "time": timestamp,
        "binance": binance,
        "yandex": yandex,
        "difference": difference
    })

@app.route('/')
def home():
    # Web sitesinde gösterilecek mesaj
    return render_template_string("""
       <!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>USDT/USD BOTU</title>
<style>
   body {
       font-family: Arial, sans-serif;
       background-color: #121212;
       color: #ffffff;
       text-align: center;
       padding: 20px;
   }
   .container {
       max-width: 500px;
       margin: auto;
       background: #1e1e1e;
       padding: 20px;
       border-radius: 10px;
       box-shadow: 0px 0px 15px rgba(255, 255, 255, 0.2);
   }
   h1 {
       color: #00ffcc;
       text-shadow: 2px 2px 5px rgba(0, 255, 204, 0.5);
       font-size: 24px;
   }
   .price {
       font-size: 22px;
       font-weight: bold;
       color: #ffcc00;
       margin: 10px 0;
   }
   .status {
       font-size: 22px;
       font-weight: bold;
       padding: 10px;
       border-radius: 5px;
       display: inline-block;
       width: 100%;
       margin: 15px 0;
   }
   .buy {
       background-color: #28a745;
       color: white;
   }
   .sell {
       background-color: #dc3545;
       color: white;
   }
   .wait {
       background-color: #ffc107;
       color: black;
   }
   .time {
       font-size: 16px;
       margin-top: 10px;
       color: #bbbbbb;
   }
   .divider {
       height: 2px;
       background: #444;
       margin: 15px 0;
   }
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
<div class="container">
<h1>📊 USDT BOT DURUMU 📊</h1>
<p class="status {{ 'buy' if l_action == 'AL' else 'sell' if l_action == 'SAT' else 'wait' }}">
       🔔 Durum: <strong>{{ l_action if l_action else 'BEKLE' }}</strong>
</p>
<div class="divider"></div>
<p class="price">💰 Binance USDT/TRY: <strong>{{ binance }}</strong> ₺</p>
<p class="price">💱 Yandex USD/TRY: <strong>{{ yandex }}</strong> ₺</p>
<p class="price">📉 Fark: <strong>%{{ oran }}</strong></p>
<div class="divider"></div>
<p class="time">🕒 Son Mesaj Gönderimi: {{ l_time }}</p>

<canvas id="differenceChart"></canvas>
<canvas id="priceChart"></canvas>

</div>

<script>
   async function updateCharts() {
       const response = await fetch('/chart-data');
       const data = await response.json();

       // Binance ve Yandex için fiyat grafiği
       priceChart.data.labels = data.labels;
       priceChart.data.datasets[0].data = data.binancePrices;
       priceChart.data.datasets[1].data = data.yandexPrices;
       priceChart.update();

       // Oran (Fark) grafiği
       differenceChart.data.labels = data.labels;
       differenceChart.data.datasets[0].data = data.differences;
       differenceChart.update();
   }

   const ctx1 = document.getElementById('priceChart').getContext('2d');
   const priceChart = new Chart(ctx1, {
       type: 'line',
       data: {
           labels: [],
           datasets: [
               {
                   label: 'Binance USDT/TRY',
                   data: [],
                   borderColor: '#ffcc00',
                   backgroundColor: 'rgba(255, 204, 0, 0.2)',
                   borderWidth: 2,
                   fill: true
               },
               {
                   label: 'Yandex USD/TRY',
                   data: [],
                   borderColor: '#00ccff',
                   backgroundColor: 'rgba(0, 204, 255, 0.2)',
                   borderWidth: 2,
                   fill: true
               }
           ]
       },
       options: {
           scales: {
               x: { ticks: { display: false } },
               y: { display: true }
           },
           plugins: {
               tooltip: { enabled: true }
           }
       }
   });

   const ctx2 = document.getElementById('differenceChart').getContext('2d');
   const differenceChart = new Chart(ctx2, {
       type: 'line',
       data: {
           labels: [],
           datasets: [
               {
                   label: 'Fark (%)',
                   data: [],
                   borderColor: '#ff4444',
                   backgroundColor: 'rgba(255, 68, 68, 0.2)',
                   borderWidth: 2,
                   fill: true
               }
           ]
       },
       options: {
           scales: {
               x: { ticks: { display: false } },
               y: { display: true }
           },
           plugins: {
               tooltip: { enabled: true }
           }
       }
   });

updateCharts();
</script>

</body>
</html>
""", l_action=status, l_time=last_action_time, binance=USDTTRY, yandex=USDTRY, oran=oran)
@app.route('/chart-data')
def chart_data():
    return jsonify({
        "labels": [entry["time"] for entry in price_history],
        "binancePrices": [entry["binance"] for entry in price_history],
        "yandexPrices": [entry["yandex"] for entry in price_history],
        "differences": [entry["difference"] for entry in price_history]
    })


# Flask'i arka planda çalıştırmak için thread kullan
import threading
def run_flask():
    app.run(host='0.0.0.0', port=000)

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
    global oran
    global USDTTRY
    global USDTRY
    
    while True:
        try:
            binance_price = get_binance_price()
            USDTTRY = binance_price

            google_price = get_google_usd_try()
            USDTRY = google_price
            print(f"Binance USDT/TRY: {binance_price}")
            print(f"Yandex USD/TRY: {google_price}")
            if binance_price is None or google_price is None:
                raise ValueError("Fiyat bilgileri alınamadı!")

            # Farkı hesapla
            difference = ((google_price - binance_price) / google_price) * 100
            oran = str(difference)[:4]
            timestamp = (datetime.now()+timedelta(hours=3)).strftime("%d-%m-%Y %H:%M:%S")
            update_price_history(timestamp,binance_price, google_price, difference)
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
            
            
            suan = datetime.now()+timedelta(hours=3)
            if last_action_time is None:  # Eğer 'son' değişkeni daha önce atanmadıysa, şu anki zamana eşitle
                last_action_time = suan
            if action != "BEKLE":
                print(7)
                if last_action != action:
                    send_telegram_message(message)
                    last_action_time = suan
                    last_action_time = last_action_time.strftime("%Y-%m-%d %H:%M:%S")
                    last_action=action
                    print("Mesaj gönderildi:", message)
                else:
                    fark = suan - last_action_time
                    if fark>= timedelta(minutes=10):
                        send_telegram_message(message)
                        last_action_time = suan
                        last_action_time = last_action_time.strftime("%Y-%m-%d %H:%M:%S")
                        last_action=action
                        print("Mesaj gönderildi:", message)
            last_message = message

        except Exception as e:
            print("Hata:", e)
            last_message = e

        # 1 dakika bekle (60 saniye)
        time.sleep(60)

# Hesaplama fonksiyonunu çalıştır
calculate_and_send()
