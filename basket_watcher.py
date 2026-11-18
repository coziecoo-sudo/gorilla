import ccxt, pandas as pd, urllib.request
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
wd, hr = now.weekday(), now.hour
today_start_ts = int(datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp() * 1000)

print(f"[{now.strftime('%Y-%m-%d %H:%M UTC')}] Daily Watcher Active...")

# Weekend Lock: Friday 22:00 UTC to Sunday 22:00 UTC
if (wd == 5) or (wd == 4 and hr >= 22) or (wd == 6 and hr < 22):
    print("WEEKEND LOCK ACTIVE: Forex is closed. Sleeping.")
    exit()

ex = ccxt.kraken()
pairs = ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY']
NTFY = "cozie-btc-alerts"
daily_losses = 0
alerts = []

for p in pairs:
    try:
        bars = ex.fetch_ohlcv(p, '1h', limit=50)
        df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
        df['m'] = df['c'].rolling(30).mean()
        df['s'] = df['c'].rolling(30).std()
        df['z'] = (df['c'] - df['m']) / df['s']
        df['atr'] = (df['h'] - df['l']).rolling(14).mean()

        # Audit only trades that happened TODAY (since 00:00 UTC)
        for i in range(30, len(df) - 2):
            if df['t'].iloc[i] >= today_start_ts:
                if df['z'].iloc[i-1] < -2.1 and df['z'].iloc[i] >= -2.1:
                    sp = df['c'].iloc[i] - (df['atr'].iloc[i] * 1.5)
                    tp = df['m'].iloc[i]
                    for k in range(i + 1, min(i + 9, len(df))):
                        if df['l'].iloc[k] <= sp:
                            daily_losses += 1
                            break
                        if df['h'].iloc[k] >= tp:
                            break

        pz, cz = round(df['z'].iloc[-2], 2), round(df['z'].iloc[-1], 2)
        if pz < -2.1 and cz >= -2.1:
            cp = df['c'].iloc[-1]
            dec = 3 if 'JPY' in p else 5
            tp = round(df['m'].iloc[-1], dec)
            sl = round(cp - (df['atr'].iloc[-1] * 1.5), dec)
            dist = abs(cp - sl)
            rl = (dist * 100000) / cp if p.startswith('USD') else (dist * 100000)
            lot = max(0.01, min(round(250.0 / rl, 2), 5.0)) if rl > 0 else 0.1
            alerts.append(f"9694 GORILLA [{p}]: BUY @ {cp} | LOT: {lot} | SL: {sl} | TP: {tp}")
        else:
            print(f"  {p:7} | Prev Z: {pz:5.2f} -> Curr Z: {cz:5.2f} | Standby")
    except Exception as e:
        print(f"  {p:7} | Feed warning: {e}")

if daily_losses >= 3:
    print(f"CIRCUIT BREAKER: {daily_losses} losses today. Paused until midnight UTC.")
else:
    print(f"Circuit Breaker Safe: {daily_losses}/3 losses today.")
    for msg in alerts:
        print(f"*** SENDING ALERT: {msg} ***")
        urllib.request.urlopen(f"https://ntfy.sh/{NTFY}", data=msg.encode('utf-8'))
