import requests
import streamlit as st
import pandas as pd
from datetime import datetime

API_URL = "https://prices.runescape.wiki/api/v1/osrs/latest"
MAP_URL = "https://prices.runescape.wiki/api/v1/osrs/mapping"

# Ambil mapping item → id
@st.cache_data
def get_mapping():
    resp = requests.get(MAP_URL, headers={"User-Agent": "callista-osrs-bot/1.0"})
    if resp.status_code == 200:
        return {item["name"]: item["id"] for item in resp.json()}
    return {}

mapping = get_mapping()

# Item pairs dengan nama sesuai mapping
ITEMS = {
    "Bird nest (empty)": "Crushed nest",
    "Unicorn horn": "Unicorn horn dust",
    "Dragon scale": "Dragon scale dust",
    "Goat horn": "Goat horn dust",
    "Kebbit teeth": "Kebbit teeth dust",
    "Nihil shard": "Nihil dust"
}

st.title("🧪 OSRS Crush Profit Calculator")

selected_item = st.selectbox("Pilih item yang mau dihitung:", list(ITEMS.keys()))
qty = st.number_input("Jumlah item dibeli", min_value=1, value=4432)
threshold = st.slider("Profit threshold (gp)", min_value=0, max_value=1000000, value=100000)
target_profit = st.number_input("Target minimal profit (gp)", min_value=0, value=100000)

if "history" not in st.session_state:
    st.session_state["history"] = pd.DataFrame(columns=["time", "item", "profit_total"])

def get_prices():
    resp = requests.get(API_URL, headers={"User-Agent": "callista-osrs-bot/1.0"})
    if resp.status_code == 200:
        return resp.json().get("data", {})
    return {}

def get_teleport_cost():
    resp = requests.get(API_URL, headers={"User-Agent": "callista-osrs-bot/1.0"})
    if resp.status_code == 200:
        data = resp.json().get("data", {})
        return data.get("law rune", {}).get("high", 615) * 2
    return 12300

if st.button("🔄 Hitung Profit"):
    data = get_prices()
    teleport_cost = get_teleport_cost()
    now = datetime.now()

    after_item = ITEMS[selected_item]

    before_id = mapping.get(selected_item)
    after_id = mapping.get(after_item)

    if before_id and after_id and str(before_id) in data and str(after_id) in data:
        buy_price = data[str(before_id)]["low"]
        sell_price = data[str(after_id)]["high"]

        crush_cost = 50
        teleport_per_item = teleport_cost / qty
        tax_rate = 0.02

        cost_per_item = buy_price + crush_cost + teleport_per_item
        revenue_per_item = sell_price * (1 - tax_rate)
        profit_per_item = revenue_per_item - cost_per_item
        total_profit = profit_per_item * qty

        # Hitung batas harga beli agar profit ≥ target_profit
        required_margin = target_profit / qty
        max_buy_price = revenue_per_item - crush_cost - teleport_per_item - required_margin

        st.subheader(f"Hasil: {selected_item} → {after_item}")
        st.write(f"📉 Buy price: {buy_price} gp")
        st.write(f"📈 Sell price: {sell_price} gp")
        st.write(f"🪙 Biaya crush Wesley: {crush_cost} gp/item")
        st.write(f"🌀 Biaya teleport Nardah: {teleport_cost} gp total (≈ {teleport_per_item:.2f} gp/item)")
        st.write(f"💸 Pajak GE: {tax_rate*100:.0f}%")
        st.write(f"💰 Profit per item: {profit_per_item:.2f} gp")
        st.write(f"💵 Total profit ({qty}): {total_profit:,.0f} gp")
        st.write(f"📊 Batas harga beli agar profit ≥ {target_profit:,} gp: ≤ {max_buy_price:.0f} gp per item")

        if total_profit >= threshold:
            st.success("✅ Profitable! Target tercapai.")
        else:
            st.warning("⚠️ Belum worth, profit di bawah threshold.")

        new_row = pd.DataFrame({
            "time": [now],
            "item": [selected_item],
            "profit_total": [total_profit]
        })
        st.session_state["history"] = pd.concat(
            [st.session_state["history"], new_row], ignore_index=True
        )
    else:
        st.error("Item tidak ditemukan di mapping API. Coba cek nama item di OSRS Wiki.")

    if not st.session_state["history"].empty:
        st.subheader("📈 Profit History")
        st.line_chart(
            st.session_state["history"].pivot(index="time", columns="item", values="profit_total")
        )
