import requests
import streamlit as st
import time
import pandas as pd

API_URL = "https://prices.runescape.wiki/api/v1/osrs/latest"

# Item pairs: (before, after)
ITEMS = {
    "Unicorn horn": "Unicorn horn dust",
    "Crushed nest": "Crushed nest",  # sudah crushed, tampilkan harga saja
    "Red dragon scale": "Dragon scale dust",
    "Goat horn": "Goat horn dust",
    "Kebbit teeth": "Kebbit teeth dust",
    "Nihil shard": "Nihil dust"
}

st.title("🧪 OSRS Crush Profit Tracker")

qty = st.number_input("Jumlah item", min_value=1, value=4432)
threshold = st.slider("Profit threshold (gp)", min_value=0, max_value=1000000, value=100000)

# Ambil harga teleport Nardah dari API (selalu update)
def get_teleport_cost():
    try:
        resp = requests.get(API_URL)
        data = resp.json()["data"]
        # contoh: pakai law rune sebagai proxy (2 law rune per teleport)
        return data["law rune"]["high"] * 2
    except:
        return 12300  # fallback default

def get_prices():
    try:
        resp = requests.get(API_URL)
        return resp.json()["data"]
    except Exception as e:
        st.error(f"Error ambil data: {e}")
        return {}

# DataFrame untuk history
history = pd.DataFrame(columns=["time", "item", "profit_total"])

placeholder = st.empty()
chart_placeholder = st.empty()

while True:
    data = get_prices()
    teleport_cost = get_teleport_cost()
    now = pd.Timestamp.now()

    with placeholder.container():
        for before, after in ITEMS.items():
            if before in data and after in data:
                buy_price = data[before]["low"]
                sell_price = data[after]["high"]

                crush_cost = 50
                teleport_per_item = teleport_cost / qty
                cost_per_item = buy_price + crush_cost + teleport_per_item
                revenue_per_item = sell_price * 0.98
                profit_per_item = revenue_per_item - cost_per_item
                total_profit = profit_per_item * qty

                st.subheader(f"{before} → {after}")
                st.write(f"📉 Buy price: {buy_price} gp")
                st.write(f"📈 Sell price: {sell_price} gp")
                st.write(f"💰 Profit per item: {profit_per_item:.2f} gp")
                st.write(f"💵 Total profit ({qty}): {total_profit:,.0f} gp")

                if total_profit >= threshold:
                    st.success("✅ Profitable! Target tercapai.")
                else:
                    st.warning("⚠️ Belum worth, profit di bawah threshold.")

                # Simpan ke history
                history = pd.concat([
                    history,
                    pd.DataFrame({"time": [now], "item": [before], "profit_total": [total_profit]})
                ])

    # Tampilkan grafik tren profit
    if not history.empty:
        chart_placeholder.line_chart(
            history.pivot(index="time", columns="item", values="profit_total")
        )

    time.sleep(60)
