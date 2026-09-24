import requests
import streamlit as st
import pandas as pd
from datetime import datetime

API_URL = "https://prices.runescape.wiki/api/v1/osrs/latest"

# Item pairs: (before, after)
ITEMS = {
    "Bird nest": "Crushed nest",
    "Unicorn horn": "Unicorn horn dust",
    "Red dragon scale": "Dragon scale dust",
    "Goat horn": "Goat horn dust",
    "Kebbit teeth": "Kebbit teeth dust",
    "Nihil shard": "Nihil dust"
}

st.title("🧪 OSRS Crush Profit Calculator")

# Pilih item dulu
selected_item = st.selectbox("Pilih item yang mau dihitung:", list(ITEMS.keys()))

# Input jumlah beli
qty = st.number_input("Jumlah item dibeli", min_value=1, value=4432)
threshold = st.slider("Profit threshold (gp)", min_value=0, max_value=1000000, value=100000)

# Session state untuk history
if "history" not in st.session_state:
    st.session_state["history"] = pd.DataFrame(columns=["time", "item", "profit_total"])

def get_prices():
    try:
        resp = requests.get(API_URL, headers={"User-Agent": "callista-osrs-bot/1.0"})
        if resp.status_code != 200:
            return {}
        return resp.json().get("data", {})
    except:
        return {}

def get_teleport_cost():
    try:
        resp = requests.get(API_URL, headers={"User-Agent": "callista-osrs-bot/1.0"})
        if resp.status_code != 200:
            return 12300
        data = resp.json().get("data", {})
        # contoh: pakai law rune sebagai proxy (2 law rune per teleport)
        return data.get("law rune", {}).get("high", 615) * 2
    except:
        return 12300

# Tombol refresh manual
if st.button("🔄 Hitung Profit"):
    data = get_prices()
    teleport_cost = get_teleport_cost()
    now = datetime.now()

    after_item = ITEMS[selected_item]

    if selected_item in data and after_item in data:
        buy_price = data[selected_item]["low"]
        sell_price = data[after_item]["high"]

        crush_cost = 50
        teleport_per_item = teleport_cost / qty
        cost_per_item = buy_price + crush_cost + teleport_per_item
        revenue_per_item = sell_price * 0.98
        profit_per_item = revenue_per_item - cost_per_item
        total_profit = profit_per_item * qty

        # Tampilkan hasil
        st.subheader(f"Hasil: {selected_item} → {after_item}")
        st.write(f"📉 Buy price: {buy_price} gp")
        st.write(f"📈 Sell price: {sell_price} gp")
        st.write(f"💰 Profit per item: {profit_per_item:.2f} gp")
        st.write(f"💵 Total profit ({qty}): {total_profit:,.0f} gp")

        if total_profit >= threshold:
            st.success("✅ Profitable! Target tercapai.")
        else:
            st.warning("⚠️ Belum worth, profit di bawah threshold.")

        # Simpan ke history
        new_row = pd.DataFrame({
            "time": [now],
            "item": [selected_item],
            "profit_total": [total_profit]
        })
        st.session_state["history"] = pd.concat(
            [st.session_state["history"], new_row], ignore_index=True
        )

    else:
        st.error("Data item tidak ditemukan di API.")

    # Grafik tren profit
    if not st.session_state["history"].empty:
        st.subheader("📈 Profit History")
        st.line_chart(
            st.session_state["history"].pivot(index="time", columns="item", values="profit_total")
        )
