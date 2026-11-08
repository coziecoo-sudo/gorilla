import ccxt, pandas as pd, urllib.request, time
from datetime import datetime

ex = ccxt.kraken()
pairs = ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY']
NTFY_TOPIC = "cozie-btc-alerts"

def log(msg):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] {msg}")

def check_market():
    log("Scanning 4-Currency Basket for Institutional Hooks...")
    for p in pairs:
        try:
            bars = ex.fetch_ohlcv(p, '1h', limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
            
            m = df['c'].rolling(20).mean()
            s = df['c'].rolling(20).std()
            z = (df['c'] - m) / s
            
            curr_p = df['c'].iloc[-1]
            prev_z = round(z.iloc[-2], 2)
            curr_z = round(z.iloc[-1], 2)
            
            # The Verified Z-Score Hook
            if prev_z < -2.0 and curr_z >= -2.0:
                tp = round(m.iloc[-1], 5)
                sl = round(curr_p - (s.iloc[-1] * 1.5), 5)
                
                alert_text = f"GORILLA SIGNAL [{p}]: BUY @ {curr_p} | SL: {sl} | TP: {tp}"
                log(f"*** TRIGGER: {alert_text} ***")
                
                # Fire push notification to your phone
                urllib.request.urlopen(f"https://ntfy.sh/{NTFY_TOPIC}", data=alert_text.encode('utf-8'))
            else:
                log(f"  {p:7} | Z: {curr_z:5.2f} | Status: Standby")
        except Exception as e:
            log(f"  {p:7} | Error: Feed sync pending market open.")

if __name__ == "__main__":
    log("Gorilla Institutional Watcher Initialized.")
    check_market()
