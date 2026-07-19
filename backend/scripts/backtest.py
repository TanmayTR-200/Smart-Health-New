"""
Backtest: Prophet vs moving average for stockout prediction.

This script holds out the last 30 days of data and compares forecast accuracy
(MAE, RMSE) between Prophet and the 7-day moving average fallback across all
PHC-medicine pairs with sufficient history (>= 60 days).

IMPORTANT: This must be run locally where Prophet is installed.
It will NOT work on Render's free tier (Prophet OOMs during pip install)
and is NOT run in CI.

Usage:
    cd backend
    python scripts/backtest.py

Output:
    Prints a summary table to stdout and saves it to docs/backtest_results.md.
"""
import sys
import os
from datetime import timedelta
import pandas as pd
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import engine
from app.models.ml_models import PROPHET_AVAILABLE

if not PROPHET_AVAILABLE:
    print("ERROR: Prophet is not installed. Install it locally first:")
    print("  pip install prophet==1.1.5 cmdstanpy>=1.0.4,<1.3")
    sys.exit(1)

from prophet import Prophet


def load_stock_data():
    """Load all stock data from the database."""
    df = pd.read_sql("SELECT * FROM stocks ORDER BY phc_id, medicine_id, date", engine)
    df['date'] = pd.to_datetime(df['date'])
    return df


def prophet_forecast(train_df, periods=30):
    """Fit Prophet on training data and forecast `periods` days ahead."""
    prophet_df = pd.DataFrame({
        'ds': train_df['date'],
        'y': train_df['quantity']
    })
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05
    )
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    return forecast['yhat'].tail(periods).values


def moving_average_forecast(train_df, periods=30):
    """Simple 7-day moving average forecast (projects the last 7-day mean forward)."""
    recent_mean = train_df['quantity'].tail(7).mean()
    return np.full(periods, recent_mean)


def calculate_metrics(actual, predicted):
    """Calculate MAE and RMSE."""
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    return mae, rmse


def run_backtest():
    """Run the full backtest and return results."""
    df = load_stock_data()
    holdout_days = 30
    min_history = 60  # Need at least 60 days to have 30 train + 30 test

    pairs = df.groupby(['phc_id', 'medicine_id']).size().reset_index(name='count')
    pairs = pairs[pairs['count'] >= min_history]

    results = []

    for _, row in pairs.iterrows():
        phc_id = row['phc_id']
        medicine_id = row['medicine_id']

        pair_data = df[
            (df['phc_id'] == phc_id) &
            (df['medicine_id'] == medicine_id)
        ].sort_values('date').reset_index(drop=True)

        # Split into train (all but last 30) and test (last 30)
        train = pair_data.iloc[:-holdout_days]
        test = pair_data.iloc[-holdout_days:]

        actual = test['quantity'].values

        # Prophet forecast
        try:
            prophet_pred = prophet_forecast(train, holdout_days)
            prophet_mae, prophet_rmse = calculate_metrics(actual, prophet_pred)
        except Exception as e:
            print(f"  Prophet failed for PHC {phc_id} med {medicine_id}: {e}")
            prophet_mae, prophet_rmse = float('nan'), float('nan')

        # Moving average forecast
        ma_pred = moving_average_forecast(train, holdout_days)
        ma_mae, ma_rmse = calculate_metrics(actual, ma_pred)

        results.append({
            'phc_id': phc_id,
            'medicine_id': medicine_id,
            'train_days': len(train),
            'prophet_mae': round(prophet_mae, 2),
            'prophet_rmse': round(prophet_rmse, 2),
            'ma_mae': round(ma_mae, 2),
            'ma_rmse': round(ma_rmse, 2),
            'prophet_wins_mae': prophet_mae < ma_mae,
            'prophet_wins_rmse': prophet_rmse < ma_rmse,
        })

    return results


def print_and_save_results(results):
    """Print summary table and save to docs/backtest_results.md."""
    results_df = pd.DataFrame(results)

    # Summary stats
    prophet_avg_mae = results_df['prophet_mae'].mean()
    prophet_avg_rmse = results_df['prophet_rmse'].mean()
    ma_avg_mae = results_df['ma_mae'].mean()
    ma_avg_rmse = results_df['ma_rmse'].mean()
    prophet_win_rate_mae = results_df['prophet_wins_mae'].mean() * 100
    prophet_win_rate_rmse = results_df['prophet_wins_rmse'].mean() * 100

    # Print to stdout
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS: Prophet vs Moving Average (30-day holdout)")
    print("=" * 80)
    print(f"\nPHC-Medicine pairs tested: {len(results_df)}")
    print(f"\n{'Metric':<25} {'Prophet':>12} {'Moving Avg':>12} {'Winner':>10}")
    print("-" * 60)
    print(f"{'Avg MAE':<25} {prophet_avg_mae:>12.2f} {ma_avg_mae:>12.2f} {'Prophet' if prophet_avg_mae < ma_avg_mae else 'Moving Avg':>10}")
    print(f"{'Avg RMSE':<25} {prophet_avg_rmse:>12.2f} {ma_avg_rmse:>12.2f} {'Prophet' if prophet_avg_rmse < ma_avg_rmse else 'Moving Avg':>10}")
    print(f"{'Prophet win rate (MAE)':<25} {prophet_win_rate_mae:>11.1f}% {'':>12}")
    print(f"{'Prophet win rate (RMSE)':<25} {prophet_win_rate_rmse:>11.1f}% {'':>12}")
    print()

    # Per-pair table
    print(f"{'PHC':>4} {'Med':>4} {'Train':>6} {'P_MAE':>8} {'P_RMSE':>8} {'MA_MAE':>8} {'MA_RMSE':>8} {'Winner':>10}")
    print("-" * 65)
    for _, r in results_df.iterrows():
        winner = "Prophet" if r['prophet_mae'] < r['ma_mae'] else "Moving Avg"
        print(f"{r['phc_id']:>4} {r['medicine_id']:>4} {r['train_days']:>6} {r['prophet_mae']:>8.2f} {r['prophet_rmse']:>8.2f} {r['ma_mae']:>8.2f} {r['ma_rmse']:>8.2f} {winner:>10}")

    # Save to docs/backtest_results.md
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    output_path = os.path.join(docs_dir, 'backtest_results.md')

    with open(output_path, 'w') as f:
        f.write("# Backtest Results: Prophet vs Moving Average\n\n")
        f.write("Holdout period: last 30 days of synthetic data.\n")
        f.write(f"PHC-Medicine pairs tested: {len(results_df)}\n\n")
        f.write("## Summary\n\n")
        f.write("| Metric | Prophet | Moving Average | Winner |\n")
        f.write("|---|---|---|---|\n")
        winner_mae = "Prophet" if prophet_avg_mae < ma_avg_mae else "Moving Average"
        winner_rmse = "Prophet" if prophet_avg_rmse < ma_avg_rmse else "Moving Average"
        f.write(f"| Average MAE | {prophet_avg_mae:.2f} | {ma_avg_mae:.2f} | {winner_mae} |\n")
        f.write(f"| Average RMSE | {prophet_avg_rmse:.2f} | {ma_avg_rmse:.2f} | {winner_rmse} |\n")
        f.write(f"| Prophet win rate (MAE) | {prophet_win_rate_mae:.1f}% | - | - |\n")
        f.write(f"| Prophet win rate (RMSE) | {prophet_win_rate_rmse:.1f}% | - | - |\n\n")
        f.write("## Per-Pair Results\n\n")
        f.write("| PHC | Medicine | Train Days | Prophet MAE | Prophet RMSE | MA MAE | MA RMSE | Winner (MAE) |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for _, r in results_df.iterrows():
            winner = "Prophet" if r['prophet_mae'] < r['ma_mae'] else "Moving Average"
            f.write(f"| {r['phc_id']} | {r['medicine_id']} | {r['train_days']} | {r['prophet_mae']} | {r['prophet_rmse']} | {r['ma_mae']} | {r['ma_rmse']} | {winner} |\n")

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    results = run_backtest()
    print_and_save_results(results)
