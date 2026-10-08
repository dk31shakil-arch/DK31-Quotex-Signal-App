import threading
from datetime import datetime
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

Window.size = (420, 760)

API = "https://api.binance.com/api/v3/klines"

def ema(values, period):
    if len(values) < period:
        return None
    k = 2 / (period + 1)
    e = sum(values[:period]) / period
    for v in values[period:]:
        e = (v * k) + (e * (1-k))
    return e

def rsi(values, period=14):
    if len(values) <= period:
        return None
    gains, losses = [], []
    for i in range(1, len(values)):
        d = values[i] - values[i-1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag*(period-1) + gains[i]) / period
        al = (al*(period-1) + losses[i]) / period
    if al == 0:
        return 100.0
    rs = ag/al
    return 100 - (100/(1+rs))

def get_signal(symbol="BTCUSDT"):
    params = {"symbol": symbol, "interval": "1m", "limit": 120}
    data = requests.get(API, params=params, timeout=10).json()
    closes = [float(x[4]) for x in data]
    opens = [float(x[1]) for x in data]
    highs = [float(x[2]) for x in data]
    lows = [float(x[3]) for x in data]

    price = closes[-1]
    e9 = ema(closes, 9)
    e21 = ema(closes, 21)
    rv = rsi(closes, 14)

    body = abs(closes[-1]-opens[-1])
    rng = max(highs[-1]-lows[-1], 1e-12)
    bullish = closes[-1] > opens[-1] and body/rng >= 0.35
    bearish = closes[-1] < opens[-1] and body/rng >= 0.35

    signal = "WAIT"
    reason = "No strong confirmation"
    score = 0

    if e9 and e21 and rv is not None:
        if e9 > e21:
            score += 1
        elif e9 < e21:
            score -= 1

        if rv >= 55:
            score += 1
        elif rv <= 45:
            score -= 1

        if bullish:
            score += 1
        elif bearish:
            score -= 1

        if score >= 2:
            signal = "CALL / UP"
            reason = "EMA9>EMA21 + RSI/candle confirmation"
        elif score <= -2:
            signal = "PUT / DOWN"
            reason = "EMA9<EMA21 + RSI/candle confirmation"

    return {
        "price": price, "ema9": e9, "ema21": e21, "rsi": rv,
        "signal": signal, "reason": reason,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

class DK31App(App):
    title = "DK31 EARNING KNOWLEDGE"

    def build(self):
        self.running = False
        self.last_signal = None
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        header = BoxLayout(size_hint_y=None, height=dp(100), spacing=dp(10))
        header.add_widget(Image(source="logo.jpg", size_hint_x=None, width=dp(95)))
        title_box = BoxLayout(orientation="vertical")
        title_box.add_widget(Label(text="[b]DK31 EARNING KNOWLEDGE[/b]", markup=True,
                                   font_size=dp(20), halign="left"))
        title_box.add_widget(Label(text="QUOTEX SIGNAL ASSISTANT", font_size=dp(13)))
        header.add_widget(title_box)
        root.add_widget(header)

        controls = GridLayout(cols=2, size_hint_y=None, height=dp(100), spacing=dp(6))
        controls.add_widget(Label(text="Market"))
        self.symbol = Spinner(text="BTCUSDT", values=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"))
        controls.add_widget(self.symbol)
        controls.add_widget(Label(text="Timeframe"))
        self.tf = Spinner(text="1 Minute", values=("1 Minute","30 Seconds (not available)"))
        controls.add_widget(self.tf)
        root.add_widget(controls)

        self.status = Label(text="● STOPPED", size_hint_y=None, height=dp(35), font_size=dp(16))
        root.add_widget(self.status)

        self.signal_label = Label(text="WAIT", font_size=dp(34), size_hint_y=None, height=dp(70),
                                  bold=True)
        root.add_widget(self.signal_label)

        info = GridLayout(cols=2, size_hint_y=None, height=dp(160), spacing=dp(4))
        self.price_l = Label(text="Price: --", halign="left")
        self.ema_l = Label(text="EMA 9/21: -- / --", halign="left")
        self.rsi_l = Label(text="RSI(14): --", halign="left")
        self.time_l = Label(text="Updated: --", halign="left")
        self.reason_l = Label(text="Reason: --", halign="left")
        for w in (self.price_l,self.ema_l,self.rsi_l,self.time_l,self.reason_l):
            info.add_widget(w)
            if w is self.reason_l:
                info.add_widget(Label(text=""))
            else:
                info.add_widget(Label(text=""))
        root.add_widget(info)

        btns = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(8))
        start = Button(text="START SIGNALS")
        stop = Button(text="STOP")
        start.bind(on_release=lambda *_: self.start())
        stop.bind(on_release=lambda *_: self.stop())
        btns.add_widget(start); btns.add_widget(stop)
        root.add_widget(btns)

        tg_title = Label(text="[b]Telegram (optional)[/b]", markup=True, size_hint_y=None, height=dp(30))
        root.add_widget(tg_title)
        self.bot_token = TextInput(hint_text="Telegram Bot Token", password=True,
                                   multiline=False, size_hint_y=None, height=dp(42))
        self.chat_id = TextInput(hint_text="Telegram Chat ID", multiline=False,
                                 size_hint_y=None, height=dp(42))
        root.add_widget(self.bot_token)
        root.add_widget(self.chat_id)

        note = Label(
            text="Signal-only • No Quotex login • No automatic trade\n"
                 "Data source: Binance public 1-minute candles\n"
                 "30-second mode needs a true sub-minute data feed.",
            font_size=dp(11), size_hint_y=None, height=dp(55)
        )
        root.add_widget(note)

        return root

    def start(self):
        if self.running:
            return
        self.running = True
        self.status.text = "● RUNNING"
        self.update()
        self.event = Clock.schedule_interval(lambda dt: self.update(), 20)

    def stop(self):
        self.running = False
        self.status.text = "● STOPPED"
        if hasattr(self, "event"):
            self.event.cancel()

    def update(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            if self.tf.text.startswith("30"):
                result = {"error": "30-second data is not available from the current public 1-minute feed."}
            else:
                result = get_signal(self.symbol.text)
        except Exception as e:
            result = {"error": str(e)}
        Clock.schedule_once(lambda dt: self._show(result), 0)

    def _show(self, r):
        if "error" in r:
            self.signal_label.text = "ERROR"
            self.reason_l.text = "Reason: " + r["error"][:80]
            return

        self.price_l.text = f"Price: {r['price']:.2f}"
        self.ema_l.text = f"EMA 9/21: {r['ema9']:.2f} / {r['ema21']:.2f}"
        self.rsi_l.text = f"RSI(14): {r['rsi']:.2f}"
        self.time_l.text = "Updated: " + r["time"]
        self.reason_l.text = "Reason: " + r["reason"]
        self.signal_label.text = r["signal"]

        # Telegram only when signal changes to CALL/PUT
        if r["signal"] in ("CALL / UP", "PUT / DOWN") and r["signal"] != self.last_signal:
            self.send_telegram(r)
        self.last_signal = r["signal"]

    def send_telegram(self, r):
        token = self.bot_token.text.strip()
        chat_id = self.chat_id.text.strip()
        if not token or not chat_id:
            return
        msg = (
            "DK31 EARNING KNOWLEDGE\\n"
            "SIGNAL ALERT\\n"
            f"Symbol: {self.symbol.text}\\n"
            f"Timeframe: 1m\\n"
            f"Signal: {r['signal']}\\n"
            f"Price: {r['price']:.2f}\\n"
            f"RSI: {r['rsi']:.2f}\\n"
            f"EMA9: {r['ema9']:.2f}\\n"
            f"EMA21: {r['ema21']:.2f}\\n"
            f"Time: {r['time']}\\n"
            "Signal only — not financial advice."
        )
        def worker():
            try:
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": chat_id, "text": msg}, timeout=10
                )
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    DK31App().run()
