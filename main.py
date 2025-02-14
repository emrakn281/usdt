import requests
from flask import Flask, render_template_string, jsonify
from bs4 import BeautifulSoup
import websocket
import json
import threading
import time
from datetime import datetime, timedelta
app = Flask(__name__)
binance_price = None
last_message = ""
last_action = ""
last_action_time = None
status = ""
oran = ""
USDTTRY = None
USDTRY = None
# Fiyat geçmişini saklamak için liste
price_history = []
def update_price_history(timestamp, price):
   if len(price_history) >= 50:  # Maksimum 50 veri noktası tut
       price_history.pop(0)
   price_history.append({"time": timestamp, "price": price})
@app.route('/')
def home():
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
<canvas id="priceChart"></canvas>
</div>
<script>
   async function updateChart() {
       const response = await fetch('/chart-data');
       const data = await response.json();
       priceChart.data.labels = data.labels;
       priceChart.data.datasets[0].data = data.values;
       priceChart.update();
   }
   const ctx = document.getElementById('priceChart').getContext('2d');
   const priceChart = new Chart(ctx, {
       type: 'line',
       data: {
           labels: [],
           datasets: [{
               label: 'USDT/TRY Fiyatı',
               data: [],
               borderColor: '#ffcc00',
               backgroundColor: 'rgba(255, 204, 0, 0.2)',
               borderWidth: 2,
               fill: true
           }]
       },
       options: {
           scales: {
               x: { display: true },
               y: { display: true }
           }
       }
   });
   setInterval(updateChart, 60000);
</script>
</body>
</html>
""", l_action=status, l_time=last_action_time, binance=USDTTRY, yandex=USDTRY, oran=oran)
@app.route('/chart-data')
def chart_data():
   return jsonify({
       "labels": [entry["time"] for entry in price_history],
       "values": [entry["price"] for entry in price_history]
   })
def run_flask():
   app.run(host='0.0.0.0', port=5080)
threading.Thread(target=run_flask, daemon=True).start()
def get_binance_price():
   global binance_price
   ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/usdttry@trade",
                                on_message=lambda ws, msg: set_price(json.loads(msg)['p']))
   ws.run_forever()
   return binance_price
def set_price(price):
   global binance_price
   binance_price = float(price)
def get_google_usd_try():
   url = "https://yandex.com.tr/finance/convert?from=USD&to=TRY&source=main"
   response = requests.get(url)
   if response.status_code == 200:
       soup = BeautifulSoup(response.text, 'html.parser')
       try:
           price_element = soup.find("span", class_="PriceValue")
           if price_element:
               return float(price_element.text.replace(",", ".").strip())
       except Exception as e:
           print("Hata:", e)
   return None
def calculate_and_send():
   global last_message, last_action, last_action_time, status, oran, USDTTRY, USDTRY
   while True:
       try:
           binance_price = get_binance_price()
           USDTTRY = binance_price
           google_price = get_google_usd_try()
           USDTRY = google_price
           if binance_price is None or google_price is None:
               raise ValueError("Fiyat bilgileri alınamadı!")
           difference = ((google_price - binance_price) / google_price) * 100
           oran = str(difference)[:4]
           action = "BEKLE"
           if difference < -1.95:
               action = "SAT"
               status = "SAT"
           elif difference > 0:
               action = "AL"
               status = "AL"
           timestamp = datetime.now().strftime("%H:%M:%S")
           update_price_history(timestamp, difference)
           message = f"📢 {action} 📢\n🔹 Binance: {binance_price} ₺\n🔹 Yandex: {google_price} ₺\n🔹 Fark: %{difference:.2f}"
           if action != "BEKLE" and last_action != action:
               print("Mesaj gönderildi:", message)
               last_action = action
               last_action_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           last_message = message
       except Exception as e:
           print("Hata:", e)
           last_message = str(e)
       time.sleep(60)
calculate_and_send()
