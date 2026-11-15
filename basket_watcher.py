import ccxt, pandas as pd, urllib.request
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
wd, hr = now.weekday(), now.hour
print(f"[{now.strftime('%Y-%m-%d %H:%M UTC')}] Checking...")
if (wd == 5) or (wd == 4 and hr >= 22) or (wd == 6 and hr < 22):
    print("WEEKEND LOCK ACTIVE: Forex is closed. Sleeping.")
    exit()

ex = ccxt.kraken()
pairs = ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY']
NTFY = "cozie-btc-alerts"
def count_losses(df):
    c = 0
    for i in range(30, len(df) - 2):
        if df['z'].iloc[i-1] < -2.1 and df['z'].iloc[i] >= -2.1:
            sp = df['c'].iloc[i] - (df['atr'].iloc[i] * 1.5)
            tp = df['m'].iloc[i]
            for k in range(i + 1, min(i + 9, len(df))):
                if df['l'].iloc[k] <= sp: c += 1; break
                if df['h'].iloc[k] >= tp: break
    return c
def calc_lot(p, cp, sl):
    d = abs(cp - sl)
    rl = (d * 100000) / cp if p.startswith('USD') else (d * 100000)
    return max(0.01, min(round(250.0 / rl, 2), 5.0)) if rl > 0 else 0.1
def check_pair(p):
    b = ex.fetch_ohlcv(p, '1h', limit=60)
    df = pd.DataFrame(b, columns=['t','o','h','l','c','v'])
    df['m'] = df['c'].rolling(30).mean()
    df['s'] = df['c'].rolling(30).std()
    df['z'] = (df['c'] - df['m']) / df['s']
    df['atr'] = (df['h'] - df['l']).rolling(14).mean()
    loss = count_losses(df)
    pz, cz = round(df['z'].iloc[-2], 2), round(df['z'].iloc[-1], 2)
    if pz < -2.1 and cz >= -2.1:
        cp, dec = df['c'].iloc[-1], (3 if 'JPY' in p else 5)
        tp = round(df['m'].iloc[-1], dec)
        sl = round(cp - (df['atr'].iloc[-1] * 1.5), dec)
        lot = calc_lot(p, cp, sl)
        return loss, f"9694 GORILLA [{p}]: BUY @ {cp} | LOT: {lot} | SL: {sl} | TP: {tp}"
    print(f"  {p:7} | Prev Z: {pz:5.2f} -> Curr Z: {cz:5.2f} | Standby")
    return loss, None
losses, alerts = 0, []
for p in pairs:
    try:
        lc, sig = check_pair(p)
        losses += lc
        if sig: alerts.append(sig)
    except Exception as e:
        print(f"  {p:7} | Feed warning: {e}")

if losses >= 3:
    print(f"CIRCUIT BREAKER TRIPPED ({losses} losses). Locked.")
else:
    print(f"Circuit Breaker Safe ({losses}/3 recent losses).")
    for m in alerts:
        print(f"*** SENDING: {m} ***")
        urllib.request.urlopen(f"https://ntfy.sh/{NTFY}", data=m.encode('utf-8'))
