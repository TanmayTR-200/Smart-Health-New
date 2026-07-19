# Backtest Results: Prophet vs Moving Average

Holdout period: last 30 days of synthetic data.
PHC-Medicine pairs tested: 36

## Summary

| Metric | Prophet | Moving Average | Winner |
|---|---|---|---|
| Average MAE | 362.88 | 264.94 | Moving Average |
| Average RMSE | 410.85 | 298.15 | Moving Average |
| Prophet win rate (MAE) | 33.3% | - | - |
| Prophet win rate (RMSE) | 27.8% | - | - |

## Per-Pair Results

| PHC | Medicine | Train Days | Prophet MAE | Prophet RMSE | MA MAE | MA RMSE | Winner (MAE) |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 336 | 813.27 | 981.77 | 914.08 | 1025.35 | Prophet |
| 1 | 2 | 336 | 606.55 | 690.22 | 128.36 | 154.29 | Moving Average |
| 1 | 3 | 336 | 86.23 | 105.38 | 76.47 | 92.14 | Moving Average |
| 1 | 4 | 336 | 758.89 | 842.57 | 458.76 | 513.51 | Moving Average |
| 1 | 5 | 336 | 170.31 | 186.95 | 169.89 | 185.74 | Moving Average |
| 1 | 6 | 336 | 422.93 | 485.59 | 345.7 | 383.51 | Moving Average |
| 2 | 1 | 336 | 497.47 | 555.35 | 516.91 | 581.61 | Prophet |
| 2 | 2 | 336 | 488.51 | 518.84 | 260.48 | 287.62 | Moving Average |
| 2 | 3 | 336 | 88.65 | 110.82 | 94.13 | 115.22 | Prophet |
| 2 | 4 | 336 | 132.07 | 210.06 | 189.19 | 220.54 | Prophet |
| 2 | 5 | 336 | 194.76 | 247.61 | 384.5 | 395.89 | Prophet |
| 2 | 6 | 336 | 405.09 | 412.87 | 189.19 | 208.83 | Moving Average |
| 3 | 1 | 336 | 1180.23 | 1280.49 | 423.84 | 476.89 | Moving Average |
| 3 | 2 | 336 | 199.12 | 255.31 | 185.67 | 208.18 | Moving Average |
| 3 | 3 | 336 | 119.18 | 135.78 | 110.54 | 132.78 | Moving Average |
| 3 | 4 | 336 | 258.35 | 291.13 | 359.22 | 406.42 | Prophet |
| 3 | 5 | 336 | 433.0 | 446.95 | 134.6 | 148.92 | Moving Average |
| 3 | 6 | 336 | 301.15 | 305.31 | 161.62 | 179.93 | Moving Average |
| 4 | 1 | 336 | 645.56 | 661.3 | 532.89 | 606.39 | Moving Average |
| 4 | 2 | 336 | 234.24 | 272.44 | 216.01 | 250.55 | Moving Average |
| 4 | 3 | 336 | 108.04 | 132.69 | 89.57 | 103.16 | Moving Average |
| 4 | 4 | 336 | 521.48 | 562.05 | 236.45 | 264.13 | Moving Average |
| 4 | 5 | 336 | 375.95 | 427.81 | 163.04 | 178.48 | Moving Average |
| 4 | 6 | 336 | 358.57 | 414.6 | 393.0 | 430.52 | Prophet |
| 5 | 1 | 336 | 293.02 | 336.04 | 418.1 | 496.72 | Prophet |
| 5 | 2 | 336 | 146.73 | 165.93 | 125.62 | 150.94 | Moving Average |
| 5 | 3 | 336 | 106.76 | 129.11 | 76.88 | 93.28 | Moving Average |
| 5 | 4 | 336 | 173.78 | 246.84 | 192.18 | 219.63 | Prophet |
| 5 | 5 | 336 | 81.27 | 101.34 | 153.8 | 170.2 | Prophet |
| 5 | 6 | 336 | 368.98 | 457.08 | 190.65 | 204.14 | Moving Average |
| 6 | 1 | 336 | 1342.81 | 1371.71 | 550.41 | 611.0 | Moving Average |
| 6 | 2 | 336 | 345.37 | 357.47 | 257.15 | 280.19 | Moving Average |
| 6 | 3 | 336 | 102.37 | 126.32 | 78.52 | 100.09 | Moving Average |
| 6 | 4 | 336 | 239.24 | 340.15 | 327.3 | 358.05 | Prophet |
| 6 | 5 | 336 | 284.83 | 339.55 | 197.06 | 219.32 | Moving Average |
| 6 | 6 | 336 | 178.96 | 285.12 | 236.18 | 279.34 | Prophet |
