import ccxt, pandas as pd

ex = ccxt.kraken()
bars = ex.fetch_ohlcv('EUR/USD', '1h', limit=500)
df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])

df['m'] = df['c'].rolling(20).mean()
df['s'] = df['c'].rolling(20).std()
df['z'] = (df['c'] - df['m']) / df['s']

df['entry'] = (df['z'].shift(1) < -2.0) & (df['z'] >= -2.0)
df['frozen_target'] = df['m']
df['frozen_stop'] = df['c'] - (df['s'] * 1.5)

df['f_high'] = df['h'].shift(-1).rolling(6).max().shift(-5)
df['f_low'] = df['l'].shift(-1).rolling(6).min().shift(-5)

df['is_win'] = df['entry'] & (df['f_high'] >= df['frozen_target'])
df['is_loss'] = df['entry'] & (df['f_low'] <= df['frozen_stop']) & (~df['is_win'])

w = int(df['is_win'].sum())
l = int(df['is_loss'].sum())
tot = w + l
rate = round((w / tot) * 100, 1) if tot > 0 else 0
net = (w * 400) - (l * 200) - (tot * 2.0)

print("=========================================")
print("=== CLOUD ENGINE AUDIT: EUR/USD       ===")
print("=========================================")
print(f"Total Completed Trades: {tot}")
print(f"Wins:                   {w}")
print(f"Losses:                 {l}")
print(f"Win Rate:               {rate}%")
print(f"Net Profit ($):         ${net}")
print("=========================================")
