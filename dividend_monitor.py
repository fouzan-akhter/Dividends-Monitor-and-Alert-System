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
    """Main monitoring function that checks for:
    1. Quarterly dividend changes ≥20%
    2. Special dividend announcements"""
    
    # Initialize Supabase client if using database
    if os.getenv("SUPABASE_URL"):
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    
    for symbol in load_stocks():
        try:
            data = get_dividend_data(symbol)
            current_dividend = float(data["dividend"])
            current_special = float(data["special"])
            
            # Get previous dividend from database or initialize
            if os.getenv("SUPABASE_URL"):
                prev_data = supabase.table("dividends").select("*").eq("symbol", symbol).execute()
                prev_dividend = prev_data.data[0]["dividend"] if prev_data.data else current_dividend
            else:
                prev_dividend = current_dividend  # First run behavior
            
            # Check for significant dividend change (≥20%)
            if prev_dividend != 0:  # Avoid division by zero
                change = (current_dividend - prev_dividend) / prev_dividend
                
                if abs(change) >= ALERT_THRESHOLD:
                    direction = "increased" if change > 0 else "decreased"
                    send_alert(
                        symbol, 
                        f"Quarterly dividend {direction} by {abs(change)*100:.1f}%\n"
                        f"Old: ${prev_dividend:.2f}\nNew: ${current_dividend:.2f}"
                    )
            
            # Check for special dividend
            if current_special > 0:
                send_alert(
                    symbol,
                    f"Special dividend announced!\n"
                    f"Amount: ${current_special:.2f}"
                )
            
            # Update database with current data
            if os.getenv("SUPABASE_URL"):
                supabase.table("dividends").upsert({
                    "symbol": symbol,
                    "dividend": current_dividend,
                    "special": current_special,
                    "updated_at": datetime.now().isoformat()
                }).execute()
                
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")

if __name__ == "__main__":
    check_dividends()
