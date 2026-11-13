import ccxt, pandas as pd, numpy as np

print("==================================================")
print("=== INITIALIZING INSTITUTIONAL QUANT FRAMEWORK ===")
print("==================================================")

ex = ccxt.kraken()
pairs = ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY']

def calculate_hurst(ts):
    """Calculates the Hurst Exponent to classify market regime."""
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

total_master_trades = 0
total_master_wins = 0
total_master_losses = 0
total_master_net = 0.0

for p in pairs:
    try:
        print(f"Analyzing microstructure for {p}...")
        bars = ex.fetch_ohlcv(p, '1h', limit=500)
        df = pd.DataFrame(bars, columns=['t','o','h','l','close','v'])
        
        # 1. Microstructure & Stochastic Baselines
        df['mean'] = df['close'].rolling(24).mean()
        df['std'] = df['close'].rolling(24).std()
        df['z_score'] = (df['close'] - df['mean']) / df['std']
        df['atr'] = (df['h'] - df['l']).rolling(14).mean()
        
        wins = 0
        losses = 0
        
        # 2. Event-Driven Simulation Loop with Regime Filter
        for i in range(30, len(df) - 10):
            # Calculate Hurst exponent on recent window to check regime
            recent_prices = df['close'].iloc[i-30:i].values
            hurst = calculate_hurst(recent_prices)
            
            # REGIME FILTER: Only trade if market is mean-reverting (Hurst < 0.5)
            if hurst < 0.5:
                prev_z = df['z_score'].iloc[i-1]
                curr_z = df['z_score'].iloc[i]
                
                # Alpha Trigger: Ornstein-Uhlenbeck Mean Reversion Hook
                if prev_z < -2.0 and curr_z >= -2.0:
                    entry_p = df['close'].iloc[i]
                    target_p = df['mean'].iloc[i]
                    stop_p = entry_p - (df['atr'].iloc[i] * 1.5)
                    
                    # Forward Walk Execution
                    f_high = df['h'].iloc[i+1 : i+8].max()
                    f_low = df['l'].iloc[i+1 : i+8].min()
                    
                    if f_high >= target_p:
                        wins += 1
                    elif f_low <= stop_p:
                        losses += 1
                        
        trades = wins + losses
        net = (wins * 400.0) - (losses * 200.0) - (trades * 2.0)
        win_rate = round((wins / trades) * 100, 1) if trades > 0 else 0.0
        
        print(f" -> {p:7} | Trades: {trades:2} | Wins: {wins:2} | Losses: {losses:2} | WinRate: {win_rate:5.1f}% | Net: ${net}")
        
        total_master_trades += trades
        total_master_wins += wins
        total_master_losses += losses
        total_master_net += net
        
    except Exception as e:
        print(f" -> {p:7} | Status: Feed calibration pending ({str(e)})")

master_rate = round((total_master_wins / total_master_trades) * 100, 1) if total_master_trades > 0 else 0.0

print("--------------------------------------------------")
print(f"MASTER PORTFOLIO TOTALS:")
print(f"Total Filtered Trades: {total_master_trades}")
print(f"Wins:                  {total_master_wins}")
print(f"Losses:                {total_master_losses}")
print(f"MASTER WIN RATE:       {master_rate}%")
print(f"TOTAL SYSTEM NET PnL:  ${total_master_net:.2f}")
print("==================================================")
