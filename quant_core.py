import ccxt
import pandas as pd
import numpy as np

print("=== QUANT ENGINE INITIALIZED ===")

ex = ccxt.kraken()
bars = ex.fetch_ohlcv('EUR/USD', '1h', limit=1000)
df = pd.DataFrame(bars, columns=['t','o','h','l','close','v'])

df['mean'] = df['close'].rolling(30).mean()
df['std'] = df['close'].rolling(30).std()
df['z'] = (df['close'] - df['mean']) / df['std']
df['atr'] = (df['h'] - df['l']).rolling(14).mean()

wins = 0
losses = 0

for i in range(40, len(df) - 10):
    c_high = df['h'].iloc[i]
    c_low = df['l'].iloc[i]
    c_close = df['close'].iloc[i]
    
    prev_z = df['z'].iloc[i-1]
    curr_z = df['z'].iloc[i]
    
    if prev_z < -2.1 and curr_z >= -2.1:
        target_p = df['mean'].iloc[i]
        stop_p = c_close - (df['atr'].iloc[i] * 1.5)
        
        f_high = df['h'].iloc[i+1 : i+8].max()
        f_low = df['l'].iloc[i+1 : i+8].min()
        
        if f_high >= target_p:
            wins += 1
        elif f_low <= stop_p:
            losses += 1

total = wins + losses
rate = round((wins / total) * 100, 1) if total > 0 else 0
net = (wins * 400) - (losses * 200) - (total * 2)

print("=== AUDIT RESULTS ===")
print("Trades:", total)
print("Wins:", wins)
print("Losses:", losses)
print("Win Rate:", str(rate) + "%")
print("Net Profit ($):", "$" + str(net))
print("=====================")
