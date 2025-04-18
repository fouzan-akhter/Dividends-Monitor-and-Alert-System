import os
import smtplib
import json
import yfinance as yf
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

# Configuration
STOCKS_FILE = "stocks.txt"
DIVIDEND_DATA_FILE = "dividend_data.json"
ALERT_THRESHOLD = 0.2  # 20% change threshold

# Email setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def load_stocks():
    """Load stocks from text file"""
    with open(STOCKS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def load_dividend_data():
    """Load previous dividend data from JSON file"""
    if not Path(DIVIDEND_DATA_FILE).exists():
        return {}
    with open(DIVIDEND_DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_dividend_data(data):
    """Save dividend data to JSON file"""
    with open(DIVIDEND_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_dividend_info(symbol):
    """Fetch dividend info including dates from Yahoo Finance"""
    stock = yf.Ticker(symbol)
    try:
        dividend_history = stock.dividends
        if not dividend_history.empty:
            last_date = dividend_history.index[-1]
            last_amount = dividend_history.iloc[-1]
            return {
                "amount": float(last_amount),
                "date": last_date.strftime('%Y-%m-%d'),
                "last_updated": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error getting dividend history for {symbol}: {str(e)}")
    
    # Fallback
    info = stock.info
    return {
        "amount": float(info.get("dividendRate", 0)),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "last_updated": datetime.now().isoformat()
    }

def send_alert(symbol, current_amount, current_date, prev_amount, prev_date):
    """Send email alert about new dividend"""
    msg = MIMEMultipart()
    msg['From'] = os.getenv("GMAIL_ADDRESS")
    msg['To'] = os.getenv("RECIPIENT_EMAIL")
    msg['Subject'] = f"New Dividend: {symbol}"
    
    # Calculate percentage change
    change_info = ""
    if prev_amount > 0:
        change = (current_amount - prev_amount) / prev_amount
        change_percent = abs(change) * 100
        direction = "increased" if change > 0 else "decreased"
        if abs(change) >= ALERT_THRESHOLD:
            change_info = f"⚠️ Significant change: {direction} by {change_percent:.1f}%"
        else:
            change_info = f"ℹ️ Moderate change: {direction} by {change_percent:.1f}%"
    else:
        change_info = "ℹ️ First dividend recorded"
    
    body = f"""
Stock: {symbol}
New dividend: ${current_amount:.2f} (on {current_date})
{change_info}
Previous: ${prev_amount:.2f} (on {prev_date})
"""
    msg.attach(MIMEText(body))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"))
            server.send_message(msg)
        print(f"✅ Email sent for {symbol}")
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")

def check_dividends():
    """Main monitoring function"""
    dividend_data = load_dividend_data()
    stocks = load_stocks()
    updated_data = dividend_data.copy()  # Preserve existing data

    for symbol in stocks:
        try:
            current_info = get_dividend_info(symbol)
            current_amount = current_info["amount"]
            current_date = current_info["date"]

            if current_amount == 0:
                continue  # Skip if no dividend

            prev_info = dividend_data.get(symbol, {"amount": 0, "date": ""})
            prev_amount = float(prev_info.get("amount", 0))
            prev_date = prev_info.get("date", "")

            # Check if this is a new dividend (new date)
            if current_date != prev_date:
                send_alert(symbol, current_amount, current_date, prev_amount, prev_date)

            # Update data for saving
            updated_data[symbol] = {
                "amount": current_amount,
                "date": current_date,
                "last_updated": current_info["last_updated"]
            }

        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")

    save_dividend_data(updated_data)

if __name__ == "__main__":
    check_dividends()
