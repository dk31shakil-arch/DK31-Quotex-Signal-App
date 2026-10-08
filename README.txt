DK31 EARNING KNOWLEDGE — Android Signal App
============================================

WHAT THIS APP DOES
- Shows CALL / UP, PUT / DOWN, or WAIT.
- Uses EMA 9/21 + RSI(14) + basic candlestick confirmation.
- Refreshes every ~20 seconds while running.
- Optional Telegram alerts.
- Includes the DK31 logo.
- Signal-only: it does NOT log into Quotex and does NOT place trades.

DATA LIMITATION
The current build uses Binance public 1-minute BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT candles.
It does not read Quotex OTC prices. The 30-second button is intentionally disabled because
a true sub-minute feed is required for a genuine 30-second signal.

BUILD APK (recommended)
Kivy recommends Buildozer as the easiest way to package a full Android APK.
Buildozer runs on Linux/macOS (Windows users can use WSL).

Commands:
  sudo apt update
  sudo apt install -y python3-pip git zip unzip openjdk-17-jdk
  pip3 install --user buildozer
  cd DK31_Quotex_Signal_App
  buildozer android debug

The APK will normally appear in the bin/ directory.

TELEGRAM
1. Create a bot with BotFather in Telegram.
2. Put the bot token in the app.
3. Put the destination chat ID in the app.
4. Start signals.
The app sends alerts only when CALL/PUT changes to a new signal.

IMPORTANT
This is an educational signal assistant, not a profit guarantee or financial advice.
Test with demo/paper trading first. Binary options can involve substantial risk.
