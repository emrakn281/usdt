import requests
from bs4 import BeautifulSoup
from flask import Flask

import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)

# Telegram Bot Token ve Chat ID
TOKEN = "7996664982:AAEmhzaXiE1rL2Dj0pBiJhzjiw6JwkHK59w"
CHAT_ID = "-4761304742"

# Son mesajı saklayacak değişken
last_message = "Henüz veri çekilmedi."

# Telegram mesaj gönderme fonksiyonu
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# Binance USDT/TRY fiyatı çekme fonksiyonu
def get_binance_usdt_try():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    url_binance = "https://www.binance.com/en-TR/trade/USDT_TRY?type=spot"
    driver.get(url_binance)
    try:
        element_binance = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.showPrice"))
        )
        price_binance = float(element_binance.text.replace(',', '').replace('$', '').strip())
        driver.quit()
        return price_binance
    except Exception as e:
        driver.quit()
        print("Error fetching data from Binance:", e)
        return None

# Google USD/TRY fiyatı çekme fonksiyonu
def get_google_usd_try():
    url_google = "https://www.google.com/finance/quote/USD-TRY"
    response_google = requests.get(url_google)
    soup_google = BeautifulSoup(response_google.text, 'html.parser')
    price_element_google = soup_google.find('div', class_='YMlKec fxKbKc')
    if price_element_google:
        price_google = float(price_element_google.text.replace(',', '').replace('$', '').strip())
        return price_google
    else:
        return None

# Oran hesaplama ve mesaj güncelleme fonksiyonu
def calculate_and_update():
    global last_message
    try:
        binance_price = get_binance_usdt_try()
        google_price = get_google_usd_try()

        if binance_price is None or google_price is None:
            raise ValueError("Veri çekme işlemi başarısız oldu. Binance veya Google fiyatı alınamadı.")

        # Oran hesaplama
        difference = ((google_price - binance_price) / google_price) * 100
        last_message = (
            f"📢 **Fiyat Güncellemesi** 📢\n"
            f"🔹 **Binance USDT/TRY**: {binance_price} ₺\n"
            f"🔹 **Google USD/TRY**: {google_price} ₺\n"
            f"🔹 **Fark**: %{difference:.2f}\n"
        )

        send_telegram_message(last_message)
        print("Mesaj güncellendi:", last_message)

    except Exception as e:
        last_message = f"Hata oluştu: {e}"
        send_telegram_message(last_message)
        print("Hata:", e)

# Flask ana sayfası, en son mesajı gösterir ve UptimeRobot için bir HTTP yanıtı döndürür
@app.route('/')
def home():
    return f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="60">
        <title>Fiyat Güncellemesi</title>
    </head>
    <body>
        <h2>{last_message.replace('📢', '').replace('🔹', '<br>🔹')}</h2>
        <p>UptimeRobot için ping sayfası çalışıyor.</p>
    </body>
    </html>
    """

# UptimeRobot’un pingleyebileceği ekstra bir endpoint
@app.route('/ping')
def ping():
    return "OK", 200  # HTTP 200 yanıtı döndürür, bu sayede UptimeRobot Replit’in çalıştığını anlar.

# Flask'ı arka planda çalıştır
def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# Döngü her 15 dakikada bir güncellenir
while True:
    calculate_and_update()
    time.sleep(900)
