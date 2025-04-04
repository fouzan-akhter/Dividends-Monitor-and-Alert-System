import os
import smtplib
import yfinance as yf
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client, Client

# Configuration
STOCKS_FILE = "stocks.txt"
ALERT_THRESHOLD = 0.2  # 20% change triggers alert

# Email setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def load_stocks():
    """Load stocks from text file"""
    with open(STOCKS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_dividend_data(symbol):
    """Fetch dividend data from Yahoo Finance"""
    stock = yf.Ticker(symbol)
    info = stock.info
    return {
        "dividend": info.get("dividendRate", 0),
        "special": info.get("trailingAnnualDividendRate", 0)
    }

def send_alert(symbol, message):
    """Send email alert"""
    msg = MIMEMultipart()
    msg['From'] = os.getenv("GMAIL_ADDRESS")
    msg['To'] = os.getenv("RECIPIENT_EMAIL")
    msg['Subject'] = f"Dividend Alert: {symbol}"
    msg.attach(MIMEText(f"Stock: {symbol}\nAlert: {message}\nTime: {datetime.now()}"))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"))
            server.send_message(msg)
        print(f"✅ Alert sent for {symbol}")
    except Exception as e:
        print(f"❌ Failed to send alert: {str(e)}")

def check_dividends():
    """Main monitoring function"""
    for symbol in load_stocks():
        try:
            data = get_dividend_data(symbol)
            current_dividend = float(data["dividend"])
            current_special = float(data["special"])

            # Your dividend change logic here
            # Example: if change > ALERT_THRESHOLD:
            #     send_alert(symbol, "Dividend changed!")

        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")

if __name__ == "__main__":
    check_dividends()
