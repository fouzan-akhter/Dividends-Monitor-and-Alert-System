# Dividend Monitoring & Alert System

<div align="center" style="margin: 20px 0;">
  <div class="wave" style="font-size: 3rem; display: inline-block; animation: wave 2s infinite;"></div>
</div>

**An intelligent, automated system for real-time dividend monitoring — built for portfolio managers, analysts, and finance professionals.**

---

## Core Features

- <strong>Threshold Alerts</strong>  
  Instantly detects significant changes in quarterly dividends, which is triggered by both +20% and -20% changes, and notified via email.

- <strong>Custom Configuration</strong>  
  Set your own alert thresholds and tailor your watchlist to focus on key holdings

---

## Technical Architecture

```
Stock Watchlist
     ↓
Daily Dividend Scan
     ↓
Check for Change ≥ ±20%
     |
     ├── Yes → Trigger Alert → Send Email Notification
     |
     └── No  → Log the Data in SUPABASE Database
```

- **Language:** Python 3.9  
- **Data Source:** Yahoo Finance API  
- **Automation:** GitHub Actions  
- **Storage:** Supabase  

---
