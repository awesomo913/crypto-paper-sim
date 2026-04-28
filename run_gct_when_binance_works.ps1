# GoCryptoTrader backtests (requires outbound HTTPS to api.binance.com).
# Use FORWARD SLASHES in -singlerunstrategypath or quoted full path — backslashes break Go flags (\u etc.).
$base = "c:/Users/default.LAPTOP-S2O9G7EP/Desktop/AI2/gocryptotrader/backtester"
Set-Location $base
go run . "-singlerunstrategypath=$base/config/user-sim/01-aggressive-rsi-5m-30d.strat" -generatereport=true "-outputpath=$base/results/aggressive-30d"
go run . "-singlerunstrategypath=$base/config/user-sim/02-longterm-dca-daily-30d.strat" -generatereport=true "-outputpath=$base/results/longterm-30d"
