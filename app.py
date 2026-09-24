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

st.title("🧪 OSRS Crush Profit Tracker")

qty = st.number_input("Jumlah item", min_value=1, value=4432)
threshold = st.slider("Profit threshold (gp)", min_value=0, max_value=1000000, value=100000)

# Session state untuk history
if "history" not in st.session_state:
    st.session_state["history"] = pd.DataFrame(columns=["time", "item", "profit_total"])

# Ambil harga teleport Nardah dari API (selalu update)
def get_teleport_cost():
    try:
        resp = requests.get(API_URL, headers={"User-Agent": "callista-osrs-bot/1.0"})
        if resp.status_code != 200:
            return 12300
        data = resp.json().get("data", {})
        # contoh: pakai law rune sebagai proxy (2 law rune per teleport)
        return data.get("law rune", {}).get("high", 615) * 2
    except:
        return 12300  # fallback default

def get_prices():
    try:
        resp = requests.get(API_URL, headers={"User-Agent": "callista-osrs-bot/1.0"})
        if resp.status_code != 200:
            return {}
        return resp.json().get("data", {})
    except:
        return {}

# Tombol refresh manual
if st.button("🔄 Refresh Data"):
    data = get_prices()
    teleport_cost = get_teleport_cost()
    now = datetime.now()

    table_rows = []

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

            table_rows.append({
                "Item Before": before,
                "Item After": after,
                "Buy Price": buy_price,
                "Sell Price": sell_price,
                "Profit/Item": round(profit_per_item, 2),
                "Total Profit": round(total_profit, 0)
            })

            # Simpan ke history
            new_row = pd.DataFrame({
                "time": [now],
                "item": [before],
                "profit_total": [total_profit]
            })
            st.session_state["history"] = pd.concat(
                [st.session_state["history"], new_row], ignore_index=True
            )

    # Tampilkan tabel semua item
    st.subheader("📊 Profit Table")
    if table_rows:
        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True)

        # Status threshold per item
        for row in table_rows:
            if row["Total Profit"] >= threshold:
                st.success(f"✅ {row['Item Before']} → {row['Item After']} profitable! Target tercapai.")
            else:
                st.warning(f"⚠️ {row['Item Before']} → {row['Item After']} belum worth, profit di bawah threshold.")
    else:
        st.info("Tidak ada data item yang tersedia dari API.")

    # Tampilkan grafik tren profit
    if not st.session_state["history"].empty:
        st.subheader("📈 Profit History")
        st.line_chart(
            st.session_state["history"].pivot(index="time", columns="item", values="profit_total")
        )
