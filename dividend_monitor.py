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
ALERT_THRESHOLD = 0.2  # 20% change threshold for notification

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
    
    # Get dividend history (returns DataFrame with Date and Dividend columns)
    try:
        dividend_history = stock.dividends
        if not dividend_history.empty:
            last_dividend = dividend_history.iloc[-1]
            return {
                "amount": last_dividend.Dividend,
                "date": last_dividend.name.strftime('%Y-%m-%d'),  # Convert Timestamp to string
                "last_updated": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error getting dividend history for {symbol}: {str(e)}")
    
    # Fallback to basic info if history fails
    info = stock.info
    return {
        "amount": info.get("dividendRate", 0),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "last_updated": datetime.now().isoformat()
    }

def send_alert(symbol, current_amount, current_date, prev_amount, prev_date):
    """Send email alert about new dividend"""
    msg = MIMEMultipart()
    msg['From'] = os.getenv("GMAIL_ADDRESS")
    msg['To'] = os.getenv("RECIPIENT_EMAIL")
    msg['Subject'] = f"New Dividend Announcement: {symbol}"
    
    # Calculate percentage change if previous amount exists and > 0
    change_info = ""
    if prev_amount > 0:
        change = (current_amount - prev_amount) / prev_amount
        change_percent = abs(change) * 100
        direction = "increased" if change > 0 else "decreased"
        
        if abs(change) >= ALERT_THRESHOLD:
            change_info = (
                f"\n\n⚠️ Significant change: Dividend {direction} by {change_percent:.1f}%\n"
                f"Previous amount: ${prev_amount:.2f} (on {prev_date})\n"
                f"New amount: ${current_amount:.2f}"
            )
        else:
            change_info = (
                f"\n\nℹ️ Moderate change: Dividend {direction} by {change_percent:.1f}%\n"
                f"Previous amount: ${prev_amount:.2f} (on {prev_date})\n"
                f"New amount: ${current_amount:.2f}"
            )
    else:
        change_info = "\n\nℹ️ This is the first dividend being recorded for this stock."
    
    message = (
        f"Stock: {symbol}\n"
        f"New dividend announced on: {current_date}\n"
        f"Amount: ${current_amount:.2f}\n"
        f"{change_info}\n"
        f"Time detected: {datetime.now()}"
    )
    
    msg.attach(MIMEText(message))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD"))
            server.send_message(msg)
        print(f"✅ Alert sent for {symbol}")
    except Exception as e:
        print(f"❌ Failed to send alert: {str(e)}")

def check_dividends():
    """Main monitoring function"""
    dividend_data = load_dividend_data()
    stocks = load_stocks()
    updated_data = {}
    alerts_sent = False

    for symbol in stocks:
        try:
            current_info = get_dividend_info(symbol)
            current_amount = float(current_info["amount"])
            current_date = current_info["date"]
            
            # Skip if dividend amount is zero
            if current_amount == 0:
                continue
            
            # Initialize if symbol not in data
            if symbol not in dividend_data:
                dividend_data[symbol] = {
                    "amount": 0,
                    "date": "",
                    "last_updated": datetime.min.isoformat()
                }
            
            prev_info = dividend_data[symbol]
            prev_amount = float(prev_info["amount"])
            prev_date = prev_info["date"]
            
            # Check if this is a new dividend (new date)
            if current_date != prev_date:
                send_alert(symbol, current_amount, current_date, prev_amount, prev_date)
                alerts_sent = True
            
            # Update data for saving (always update to get latest amount/date)
            updated_data[symbol] = {
                "amount": current_amount,
                "date": current_date,
                "last_updated": current_info["last_updated"]
            }
            
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")
            # Keep previous data if error occurs
            if symbol in dividend_data:
                updated_data[symbol] = dividend_data[symbol]
    
    # Save the updated data
    save_dividend_data(updated_data)
    
    if not alerts_sent:
        print("✅ No new dividend announcements detected")

if __name__ == "__main__":
    check_dividends()
