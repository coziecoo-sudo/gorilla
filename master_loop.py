import ccxt, pandas as pd, urllib.request, time
from datetime import datetime

ex = ccxt.kraken()
pairs = ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY']
NTFY_TOPIC = "cozie-btc-alerts"

def log(msg):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] {msg}")

def run_loop():
    log("PRO ENGINE INITIALIZED: 24/7 Continuous Loop Active.")
    last_checked_hour = -1
    
    while True:
        try:
            # Get current UTC hour
            current_hour = datetime.utcnow().hour
            
            # Run only once per new hour candle
            if current_hour != last_checked_hour:
                log("New candle detected. Scanning 4-Currency Basket...")
                
                for p in pairs:
                    bars = ex.fetch_ohlcv(p, '1h', limit=50)
                    df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
                    
                    m = df['c'].rolling(20).mean()
                    s = df['c'].rolling(20).std()
                    z = (df['c'] - m) / s
                    
                    curr_p = df['c'].iloc[-1]
                    prev_z = round(z.iloc[-2], 2)
                    curr_z = round(z.iloc[-1], 2)
                    
                    if prev_z < -2.0 and curr_z >= -2.0:
                        tp = round(m.iloc[-1], 5)
                        sl = round(curr_p - (s.iloc[-1] * 1.5), 5)
                        alert_text = f"PRO GORILLA SIGNAL [{p}]: BUY @ {curr_p} | SL: {sl} | TP: {tp}"
                        log(f"*** TRIGGER: {alert_text} ***")
                        urllib.request.urlopen(f"https://ntfy.sh/{NTFY_TOPIC}", data=alert_text.encode('utf-8'))
                    else:
                        log(f"  {p:7} | Z: {curr_z:5.2f} | Status: Standby")
                
                last_checked_hour = current_hour
            
            # Sleep for 30 seconds before checking the clock again
            time.sleep(30)
            
        except Exception as e:
            log(f"Error in loop: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    run_loop()
