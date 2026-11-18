import ccxt, pandas as pd, urllib.request
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
wd, hr = now.weekday(), now.hour

print(f"[{now.strftime('%Y-%m-%d %H:%M UTC')}] Gorilla Scanner Active...")

if (wd == 5) or (wd == 4 and hr >= 22) or (wd == 6 and hr < 22):
    print("WEEKEND LOCK ACTIVE: Forex is closed. Sleeping.")
    exit()

ex = ccxt.kraken()
pairs = ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY']
NTFY = "cozie-btc-alerts"

for p in pairs:
    try:
        bars = ex.fetch_ohlcv(p, '1h', limit=50)
        df = pd.DataFrame(bars, columns=['t','o','h','l','close','v'])
        df['m'] = df['close'].rolling(30).mean()
        df['s'] = df['close'].rolling(30).std()
        df['z'] = (df['close'] - df['m']) / df['s']
        df['atr'] = (df['h'] - df['l']).rolling(14).mean()

        pz = round(df['z'].iloc[-2], 2)
        cz = round(df['z'].iloc[-1], 2)

        # 9694 Hook Trigger
        if pz < -2.1 and cz >= -2.1:
            cp = df['close'].iloc[-1]
            dec = 3 if 'JPY' in p else 5
            atr = df['atr'].iloc[-1]
            
            # FIXED TARGETS: TP is strictly ABOVE entry (1.5x ATR), SL is BELOW entry (1.5x ATR)
            tp = round(cp + (atr * 1.5), dec)
            sl = round(cp - (atr * 1.5), dec)
            
            dist = abs(cp - sl)
            rl = (dist * 100000) / cp if p.startswith('USD') else (dist * 100000)
            lot = max(0.01, min(round(250.0 / rl, 2), 5.0)) if rl > 0 else 0.1
            
            alert_msg = f"9694 GORILLA [{p}]: BUY @ {cp} | LOT: {lot} | SL: {sl} | TP: {tp}"
            print(f"*** LIVE TRIGGER: {alert_msg} ***")
            urllib.request.urlopen(f"https://ntfy.sh/{NTFY}", data=alert_msg.encode('utf-8'))
        else:
            print(f"  {p:7} | Prev Z: {pz:5.2f} -> Curr Z: {cz:5.2f} | Standby")
    except Exception as e:
        print(f"  {p:7} | Feed warning: {e}")

print("=== SCAN COMPLETE ===")
