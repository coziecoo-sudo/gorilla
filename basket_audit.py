import ccxt, pandas as pd
import numpy as np

print("==========================================================")
print("=== INSTITUTIONAL 4-ASSET MULTI-CURRENCY BASKET AUDIT   ===")
print("==========================================================")

ex = ccxt.kraken()
pairs = ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY']

grand_total_trades = 0
grand_wins = 0
grand_losses = 0
grand_net = 0.0

for p in pairs:
    try:
        print(f"[{p}] Pulling clean historical feed...")
        bars = ex.fetch_ohlcv(p, '1h', limit=1000)
        df = pd.DataFrame(bars, columns=['t','o','h','l','close','v'])
        
        df['mean'] = df['close'].rolling(30).mean()
        df['std'] = df['close'].rolling(30).std()
        df['z'] = (df['close'] - df['mean']) / df['std']
        df['atr'] = (df['h'] - df['l']).rolling(14).mean()
        
        wins = 0
        losses = 0
        in_position = False
        entry_p = 0.0
        target_p = 0.0
        stop_p = 0.0
        
        for i in range(40, len(df) - 10):
            c_high = df['h'].iloc[i]
            c_low = df['l'].iloc[i]
            c_close = df['close'].iloc[i]
            
            if in_position:
                if c_low <= stop_p:
                    losses += 1
                    in_position = False
                elif c_high >= target_p:
                    wins += 1
                    in_position = False
            
            if not in_position:
                prev_z = df['z'].iloc[i-1]
                curr_z = df['z'].iloc[i]
                
                # Z-Score Hook Anomaly Trigger
                if prev_z < -2.1 and curr_z >= -2.1:
                    in_position = True
                    entry_p = c_close
                    target_p = round(df['mean'].iloc[i], 5)
                    stop_p = round(entry_p - (df['atr'].iloc[i] * 1.5), 5)

        total_t = wins + losses
        rate = round((wins / total_t) * 100, 1) if total_t > 0 else 0.0
        net_pnl = (wins * 400.0) - (losses * 200.0) - (total_t * 2.0)
        
        print(f" -> {p:7} | Trades: {total_t:2} | Wins: {wins:2} | Losses: {losses:2} | WinRate: {rate:5.1f}% | Net: ${net_pnl}")
        
        grand_total_trades += total_t
        grand_wins += wins
        grand_losses += losses
        grand_net += net_pnl
        
    except Exception as e:
        print(f" -> {p:7} | Status: Feed pending ({str(e)})")

portfolio_rate = round((grand_wins / grand_total_trades) * 100, 1) if grand_total_trades > 0 else 0.0

print("----------------------------------------------------------")
print(f"PORTFOLIO BASKET TOTALS:")
print(f"Total Filtered Trades: {grand_total_trades}")
print(f"Total Wins:            {grand_wins}")
print(f"Total Losses:          {grand_losses}")
print(f"BASKET WIN RATE:       {portfolio_rate}%")
print(f"TOTAL BASKET NET PnL:  ${grand_net:.2f}")
print("==========================================================")
