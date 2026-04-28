# GoCryptoTrader: 12 wall-clock hours of LIVE candle paper trading (real-orders=false).
# Uses real Binance klines; no real orders — safe to fine-tune.
#
# Windows: backslashes in -singlerunstrategypath break flags — use forward slashes.
$ErrorActionPreference = "Stop"
$bt = "c:/Users/default.LAPTOP-S2O9G7EP/Desktop/AI2/gocryptotrader/backtester"
$strat = "$bt/config/user-sim/03-live-aggressive-rsi-1m-paper.strat"
$out  = "$bt/results/live-12h-paper"
$secs = 12 * 3600

New-Item -ItemType Directory -Force -Path $out | Out-Null
Set-Location $bt
Write-Host "Starting live PAPER backtester (stops in 12h). Press Ctrl+C to end sooner."
Write-Host "Strategy: $strat"
Write-Host "Reports:  $out"
Write-Host ""

$args = @(
  "run", ".",
  "-singlerunstrategypath=$strat",
  "-generatereport=true",
  "-outputpath=$out"
)
$proc = Start-Process -FilePath "go" -ArgumentList $args -WorkingDirectory $bt -PassThru -NoNewWindow
if (-not $proc) { throw "Failed to start go run" }
Start-Sleep -Seconds $secs
try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
Get-Process -Name "go","backtester" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" } | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "12h window elapsed (or process ended). Check $out for report output if generated."
