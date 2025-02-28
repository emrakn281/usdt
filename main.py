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
show_time = None
status=""
oran=""
USDTTRY= None
USDTRY= None
altinoran=""
mynets1= None
gramaltin = None
last_chart_update = None
price_history = []
altin_history = []
last_message_time = None  # Son mesajın gönderildiği zaman



def update_price_history(timestamp, binance, yandex, difference):
    if len(price_history) >= 100:
        price_history.pop(0)
    price_history.append({
        "time": timestamp,
        "binance": binance,
        "yandex": yandex,
        "difference": difference
    })

def update_altin_history(timestamp, gram, s1, difference):
    if len(altin_history) >= 100:
        altin_history.pop(0)
    altin_history.append({
        "time": timestamp,
        "gram": gram,
        "s1": s1,
        "fark": difference
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
<title>USD ve ALTIN BOTU</title>
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
<h1>📊 ALTIN BOT DURUMU 📊</h1>
<p class="price">💰 Mynet Gram Altın: <strong>{{ gramaltin }}</strong> ₺</p>
<p class="price">💰 Mynet S1 (x100): <strong>{{ mynets1 }}</strong> ₺</p>
<p class="price">📉 Fark: <strong>%{{ altinoran }}</strong></p>
<canvas id="goldDifferenceChart"></canvas>
<canvas id="goldChart"></canvas>

</div>

<script>
    const ctx3 = document.getElementById('goldChart').getContext('2d');
    const goldChart = new Chart(ctx3, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Gram Altın', data: [], borderColor: '#FFD700', fill: true },
                { label: 'S1 (x100)', data: [], borderColor: '#FFA500', fill: true }
            ]
        }
    });
    const ctx4 = document.getElementById('goldDifferenceChart').getContext('2d');
    const goldDifferenceChart = new Chart(ctx4, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Altın - S1 Fark (%)', data: [], borderColor: '#FF4444', fill: true }
            ]
        }
    });
</script>

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

       // Altın ve s1 için fiyat grafiği
       goldChart.data.labels = data.goldLabels;
       goldChart.data.datasets[0].data = data.gramPrices;
       goldChart.data.datasets[1].data = data.s1Prices;
       goldChart.update();

       // Altın ve s1 için fark grafiği
       goldDifferenceChart.data.labels = data.goldLabels;
       goldDifferenceChart.data.datasets[0].data = data.goldDifferences;
       goldDifferenceChart.update();
       
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
""", l_action=status, l_time=show_time, binance=USDTTRY, yandex=USDTRY, oran=oran, gramaltin=gramaltin, mynets1=mynets1,altinoran=altinoran )
@app.route('/chart-data')
def chart_data():
    return jsonify({
        "labels": [entry["time"] for entry in price_history],
        "binancePrices": [entry["binance"] for entry in price_history],
        "yandexPrices": [entry["yandex"] for entry in price_history],
        "differences": [entry["difference"] for entry in price_history],
        "goldLabels": [entry["time"] for entry in altin_history],
        "gramPrices": [entry["gram"] for entry in altin_history],
        "s1Prices": [entry["s1"] for entry in altin_history],
        "goldDifferences": [entry["fark"] for entry in altin_history]
    })


# Flask'i arka planda çalıştırmak için thread kullan
import threading
def run_flask():
    app.run(host='0.0.0.0', port=3000)

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

# Binance USDT/TRY fiyatını çekme fonksiyonu 


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

def get_s1_price():
    url = "https://finans.mynet.com/borsa/hisseler/altins1-darphane-altin-sertifikasi/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        price_div = soup.find('div', {'class': 'data-value'})
        if price_div:

            price = price_div.text.strip().replace(".", "")  # Virgülü noktaya çevir
            price = price.replace(",", ".")  # Virgülü noktaya çevir
            return float(price) * 100  # S1 fiyatını 100 ile çarp
    return None

def get_gold_price():
    url = "https://finans.mynet.com/altin/xgld-spot-altin-tl-gr/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        price_span = soup.find('span', {'class': 'dynamic-price-GAUTRY'})
        if price_span:
            
            price = price_span.text.strip().replace(".", "")  # Virgülü noktaya çevir
            price = price.replace(",", ".")  # Virgülü noktaya çevir
            return float(price)
    return None

# Fiyatları al, oranı hesapla ve Telegram'a gönder
import time

def calculate_and_send():
    global last_action, last_action_time, show_time, status, oran, USDTTRY, USDTRY, gramaltin, mynets1
    global last_message, last_message_time, altinoran
    while True:
        try:
            # Binance ve Yandex fiyatlarını al
            USDTTRY = get_binance_price()
            USDTRY = get_google_usd_try()
            # Altın ve S1 fiyatlarını al
            gold_price = get_gold_price()
            gramaltin = str(gold_price)[:7]
            s1_price = get_s1_price()
            mynets1=str(s1_price)[:7]

            # Fiyatlar alındı mı kontrol et
            if None in [USDTTRY, USDTRY, gold_price, s1_price]:
                raise ValueError("Fiyat bilgileri alınamadı!")
            # USDT/TRY - USD/TRY farkı hesapla
            difference_usdt = ((USDTRY - USDTTRY) / USDTRY) * 100
            oran = str(difference_usdt)[:4]
            # Altın - S1 farkını hesapla
            difference_gold = ((s1_price - gold_price) / s1_price) * 100
            altinoran = str(difference_gold)[:4]
            timestamp = (datetime.now() + timedelta(hours=3)).strftime("%d-%m-%Y %H:%M:%S")
            # Grafik verilerini güncelle (Her 15 dakikada bir)
            update_price_history(timestamp, USDTTRY, USDTRY, difference_usdt)
            update_altin_history(timestamp, gold_price, s1_price, difference_gold)
            
            # **Dolar ve USDT için AL/SAT BEKLE kararı**
            action_usdt = "BEKLE"
            if difference_usdt < -1.95:
                action_usdt = "SAT"
            elif difference_usdt > 0:
                action_usdt = "AL"
            # **Altın ve S1 için AL/SAT BEKLE kararı**
            action_gold = "BEKLE"
            if difference_gold > 0:
                action_gold = "SAT"
            elif difference_gold < -1.95:
                action_gold = "AL"
            # Telegram mesajı oluştur
            message = (
                f"📢 **{action_usdt}** 📢\n"
                f"🔹 **Binance USDT/TRY**: {USDTTRY} ₺\n"
                f"🔹 **Yandex USD/TRY**: {USDTRY} ₺\n"
                f"🔹 **Fark (USDT)**: %{difference_usdt:.2f}\n"
                "----------------------------------\n"
                f"📢 **{action_gold}** 📢\n"
                f"🔸 **Gram Altın**: {gramaltin} ₺\n"
                f"🔸 **S1 (x100)**: {mynets1} ₺\n"
                f"🔸 **Fark (Altın vs S1)**: %{difference_gold:.2f}"
            )
            # **Telegram mesajı gönderme mantığı**
            suan = datetime.now() + timedelta(hours=3)
            if last_message_time is None or (datetime.now() - last_message_time) >= timedelta(hours=2):
                last_message_time = datetime.now()
                send_telegram_message(message)
                last_action_time = suan
                show_time = last_action_time.strftime("%Y-%m-%d %H:%M:%S")
                last_action = f"{action_usdt} - {action_gold}"

            last_message = message
        except Exception as e:
            print("Hata:", e)
            last_message = str(e)
        time.sleep(900)  # 15 dakika bekle
# Hesaplama fonksiyonunu çalıştır
calculate_and_send()
