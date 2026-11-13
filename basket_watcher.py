import ccxt, pandas as pd, urllib.request
from datetime import datetime

ex = ccxt.kraken()
pairs = ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY']
NTFY_TOPIC = "cozie-btc-alerts"

def log(msg):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] {msg}")

def scan_basket():
    log("=== LIVE SCAN: 9694 BASKET ENGINE (EUR/USD, GBP/USD, USD/CAD, USD/JPY) ===")
    
    for p in pairs:
        try:
            bars = ex.fetch_ohlcv(p, '1h', limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','close','v'])
            
            # Exact Math from basket_audit.py ($9,694 test)
            df['mean'] = df['close'].rolling(30).mean()
            df['std'] = df['close'].rolling(30).std()
            df['z'] = (df['close'] - df['mean']) / df['std']
            df['atr'] = (df['h'] - df['l']).rolling(14).mean()
            
            curr_price = df['close'].iloc[-1]
            prev_z = round(df['z'].iloc[-2], 2)
            curr_z = round(df['z'].iloc[-1], 2)
            
            # The -2.1 Sigma Hook Trigger
            if prev_z < -2.1 and curr_z >= -2.1:
                tp = round(df['mean'].iloc[-1], 5)
                sl = round(curr_price - (df['atr'].iloc[-1] * 1.5), 5)
                
                # Risk formula: 0.5% risk ($250) on $50,000 account
                risk_distance = abs(curr_price - sl)
                lot_size = round(250.00 / (risk_distance * 100000), 2) if risk_distance > 0 else 0.1
                
                alert_msg = f"9694 GORILLA SIGNAL [{p}]: BUY @ {curr_price} | LOT: {lot_size} | SL: {sl} | TP: {tp}"
                log(f"*** TRIGGER DETECTED: {alert_msg} ***")
                
                # Push directly to your phone via ntfy
                urllib.request.urlopen(f"https://ntfy.sh/{NTFY_TOPIC}", data=alert_msg.encode('utf-8'))
            else:
                log(f"  {p:7} | Prev Z: {prev_z:5.2f} -> Curr Z: {curr_z:5.2f} | Status: Standby")
        except Exception as e:
            log(f"  {p:7} | Feed sync error: {str(e)}")

    log("=== SCAN COMPLETE: Standing by for next hourly candle ===")

if __name__ == "__main__":
    scan_basket()
